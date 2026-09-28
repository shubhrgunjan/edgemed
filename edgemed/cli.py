import argparse
import datetime as dt
import ipaddress
import json
import os
import signal
import ssl
import subprocess
import sys
import time
from pathlib import Path

import portalocker
import uvicorn
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID

from .security import SERVICE, PASSWORDS, load_secret, save_secret, new_identity, private_write
from .platforms import target

PROJECT = Path(__file__).resolve().parent.parent
DEFAULT_RUNTIME = (
    Path.home() / "Library/Application Support/EdgeMed Local"
    if sys.platform == "darwin"
    else Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "edgemed"
)
RUNTIME = (
    Path(os.environ.get("EDGEMED_RUNTIME", DEFAULT_RUNTIME))
    .expanduser()
    .resolve()
)
PORT_OFFSET = int(os.environ.get("EDGEMED_PORT_OFFSET", "0"))
if not 0 <= PORT_OFFSET <= 50000:
    raise ValueError("Invalid local port offset")
if "EDGEMED_RUNTIME" in os.environ and SERVICE == "org.lex.edgemed.local":
    raise RuntimeError("An isolated runtime requires a distinct EDGEMED_KEYCHAIN_SERVICE")
VAULT = RUNTIME / "vault"


def mount_vault():
    target()
    if sys.platform == "linux":
        verify_vault()
        return
    import keyring
    import secrets

    if sys.platform != "darwin":
        raise RuntimeError(
            "This verified launcher supports macOS; configure a reviewed encrypted Linux volume separately."
        )
    RUNTIME.mkdir(parents=True, exist_ok=True, mode=0o700)
    password = keyring.get_password(SERVICE, "vault")
    image = RUNTIME / "data.sparsebundle"
    if password is None:
        if image.exists():
            raise RuntimeError("Existing vault key unavailable; refusing to replace it")
        password = secrets.token_hex(32)
        keyring.set_password(SERVICE, "vault", password)
    if not image.exists():
        subprocess.run(
            [
                "hdiutil",
                "create",
                "-size",
                "4g",
                "-type",
                "SPARSEBUNDLE",
                "-fs",
                "APFS",
                "-volname",
                "EdgeMed Private",
                "-encryption",
                "AES-256",
                "-stdinpass",
                str(image),
            ],
            input=password.encode(),
            capture_output=True,
            check=True,
        )
    if not VAULT.is_mount():
        VAULT.mkdir(exist_ok=True)
        subprocess.run(
            ["hdiutil", "attach", "-nobrowse", "-mountpoint", str(VAULT), "-stdinpass", str(image)],
            input=password.encode(),
            capture_output=True,
            check=True,
        )
    verify_vault()


def verify_vault():
    target()
    if sys.platform == "linux":
        from .linux_vault import verify_luks_mount

        return verify_luks_mount(VAULT)
    if sys.platform != "darwin":
        raise RuntimeError("Only macOS and Linux 64-bit launchers are supported")
    import plistlib

    info = plistlib.loads(subprocess.check_output(["hdiutil", "info", "-plist"]))
    for image in info.get("images", []):
        if (
            image.get("image-path") == str(RUNTIME / "data.sparsebundle")
            and image.get("image-encrypted") is True
        ):
            if any(e.get("mount-point") == str(VAULT) for e in image.get("system-entities", [])):
                return True
    raise RuntimeError("Expected encrypted data image is not mounted; refusing to write data")


def make_pki(root):
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if (root / "ca.pem").exists():
        return
    now = dt.datetime.now(dt.timezone.utc)
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "EdgeMed local development CA")])
    ca = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - dt.timedelta(minutes=5))
        .not_valid_after(now + dt.timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .sign(ca_key, hashes.SHA256())
    )
    private_write(root / "ca.pem", ca.public_bytes(serialization.Encoding.PEM).decode())
    private_write(
        root / "ca.key",
        ca_key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
        ).decode(),
    )
    for name in ("edge-a", "edge-b", "central"):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cert = (
            x509.CertificateBuilder()
            .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)]))
            .issuer_name(ca_name)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - dt.timedelta(minutes=5))
            .not_valid_after(now + dt.timedelta(days=90))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(
                x509.SubjectAlternativeName(
                    [x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]
                ),
                critical=False,
            )
            .add_extension(
                x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH, ExtendedKeyUsageOID.SERVER_AUTH]),
                critical=False,
            )
            .sign(ca_key, hashes.SHA256())
        )
        private_write(root / f"{name}.pem", cert.public_bytes(serialization.Encoding.PEM).decode())
        private_write(
            root / f"{name}.key",
            key.private_bytes(
                serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
            ).decode(),
        )


def setup():
    import secrets

    mount_vault()
    pki = VAULT / "pki"
    make_pki(pki)
    identities = {}
    for name in ("edge-a", "edge-b", "central"):
        try:
            secret = load_secret(name)
        except RuntimeError:
            if (VAULT / name / "data" / "memory.db").exists():
                raise RuntimeError("Existing profile keys unavailable; refusing to replace them") from None
            priv, pub = new_identity()
            password = secrets.token_urlsafe(18)
            secret = {
                "db_key": secrets.token_hex(32),
                "sign_private": priv,
                "sign_public": pub,
                "initial_password": password,
                "qdrant_api_key": secrets.token_urlsafe(32),
                "operators": {
                    "operator": {
                        "password_hash": PASSWORDS.hash(password),
                        "owner": "operator",
                        "role": "admin",
                    }
                },
            }
            save_secret(name, secret)
        identities[name] = secret
    for name, port in (("edge-a", 8765), ("edge-b", 8766), ("central", 9443)):
        port += PORT_OFFSET
        root = VAULT / name
        root.mkdir(exist_ok=True, mode=0o700)
        cfg = {
            "device_id": name,
            "data_path": str(root / "data"),
            "origin": f"http://127.0.0.1:{port}",
            "port": port,
            "vault_verified": True,
            "ca": str(pki / "ca.pem"),
            "cert": str(pki / f"{name}.pem"),
            "key": str(pki / f"{name}.key"),
            "gateway": f"https://127.0.0.1:{9443 + PORT_OFFSET}",
            "gateway_public": identities["central"]["sign_public"],
            "qdrant": f"https://127.0.0.1:{6333 + PORT_OFFSET}",
            "devices": {
                n: {"public": identities[n]["sign_public"], "revoked": False} for n in ("edge-a", "edge-b")
            },
        }
        if not (root / "config.json").exists():
            private_write(root / "config.json", json.dumps(cfg, indent=2))
    # Config is inside the encrypted vault and never committed.
    server_config = {
        "log_level": "WARN",
        "telemetry_disabled": True,
        "storage": {
            "storage_path": str(VAULT / "qdrant-storage"),
            "snapshots_path": str(VAULT / "qdrant-snapshots"),
        },
        "service": {
            "host": "127.0.0.1",
            "http_port": 6333 + PORT_OFFSET,
            "grpc_port": None,
            "enable_tls": True,
            "api_key": identities["central"]["qdrant_api_key"],
        },
        "tls": {"cert": str(pki / "central.pem"), "key": str(pki / "central.key")},
    }
    import yaml

    private_write(VAULT / "qdrant.yaml", yaml.safe_dump(server_config))
    print(
        "Encrypted profiles provisioned. Username: operator. "
        "Retrieve your password with: uv run python -m edgemed.cli credentials edge-a"
    )


def config(profile):
    verify_vault()
    value = json.loads((VAULT / profile / "config.json").read_text())
    value["profiling"] = os.environ.get("EDGEMED_PROFILE") == "1"
    if profile == "edge-a" and os.environ.get("EDGEMED_LAN") == "1":
        from .lan import load

        value.update(load(VAULT / "pki", value["port"]))
        value["lan_mode"] = True
    return value


def serve(profile):
    cfg, secret = config(profile), load_secret(profile)
    # OS-level process lock prevents concurrent owners of an embedded shard.
    with portalocker.Lock(str(VAULT / profile / "process.lock"), timeout=0):
        if profile == "central":
            from .gateway import create_gateway

            app = create_gateway(cfg, secret, PROJECT / ".cache/models")
            uvicorn.run(
                app,
                host="127.0.0.1",
                port=cfg["port"],
                access_log=False,
                log_level="warning",
                ssl_keyfile=cfg["key"],
                ssl_certfile=cfg["cert"],
                ssl_ca_certs=cfg["ca"],
                ssl_cert_reqs=ssl.CERT_REQUIRED,
            )
        else:
            from .api import create_app

            app = create_app(cfg, secret, PROJECT / ".cache/models", PROJECT / "frontend/dist")
            uvicorn.run(
                app,
                host=cfg.get("bind", "127.0.0.1"),
                port=cfg["port"],
                access_log=False,
                log_level="warning",
                ssl_certfile=cfg.get("tls_cert"),
                ssl_keyfile=cfg.get("tls_key"),
            )


def alive(pid):
    try:
        os.kill(pid, 0)
        state = subprocess.check_output(["ps", "-p", str(pid), "-o", "stat="], text=True).strip()
        return bool(state) and not state.startswith("Z")
    except ProcessLookupError:
        return False


def start(lan=False):
    mount_vault()
    from .operations import preflight

    preflight(PROJECT)
    if lan:
        from .lan import load

        load(VAULT / "pki", 8765 + PORT_OFFSET)
    pidfile = RUNTIME / "processes.json"
    pids = json.loads(pidfile.read_text()) if pidfile.exists() else {}
    mode = "lan" if lan else "local"
    mode_file = RUNTIME / "start-mode"
    if (
        any(alive(pid) for pid in pids.values())
        and (mode_file.read_text() if mode_file.is_file() else "local") != mode
    ):
        raise RuntimeError("Services are already running in another mode; stop them before switching")
    commands = {
        "qdrant": [str(PROJECT / ".tools/qdrant"), "--config-path", str(VAULT / "qdrant.yaml")],
        **{p: [sys.executable, "-m", "edgemed.cli", "serve", p] for p in ("central", "edge-a", "edge-b")},
    }
    for name, command in commands.items():
        if name in pids and alive(pids[name]):
            continue
        log = open(VAULT / f"{name}.log", "ab", buffering=0)
        environment = {**os.environ, "EDGEMED_LAN": "1" if lan and name == "edge-a" else "0"}
        proc = subprocess.Popen(
            command,
            cwd=PROJECT,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            start_new_session=True,
            env=environment,
        )
        log.close()
        pids[name] = proc.pid
        private_write(pidfile, json.dumps(pids))
        private_write(mode_file, mode)
        time.sleep(2 if name == "qdrant" else 1)
    import httpx

    for profile in ("edge-a", "edge-b"):
        cfg = config(profile)
        if lan and profile == "edge-a":
            from .lan import load

            cfg.update(load(VAULT / "pki", cfg["port"]))
        url = cfg["origin"]
        for _ in range(60):
            try:
                if (
                    httpx.get(
                        url + "/api/health", timeout=1, trust_env=False, verify=cfg.get("tls_ca", True)
                    ).status_code
                    == 200
                ):
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.5)
        else:
            raise RuntimeError(f"{profile} did not become ready; inspect protected runtime logs")
        print(f"{profile}: {url}")


def stop():
    path = RUNTIME / "processes.json"
    if not path.exists():
        return
    pids = json.loads(path.read_text())
    for name in ("edge-a", "edge-b", "central", "qdrant"):
        pid = pids.get(name)
        if pid and alive(pid):
            command = subprocess.check_output(["ps", "-p", str(pid), "-o", "command="], text=True).strip()
            if ("edgemed.cli serve " + name) in command or (
                name == "qdrant" and str(PROJECT / ".tools/qdrant") in command
            ):
                os.kill(pid, signal.SIGTERM)
    for _ in range(50):
        if not any(alive(pid) for pid in pids.values()):
            path.unlink(missing_ok=True)
            (RUNTIME / "start-mode").unlink(missing_ok=True)
            return
        time.sleep(0.2)
    raise RuntimeError("Some services have not stopped; vault remains mounted")


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description="EdgeMed encrypted local demo")
    parser.add_argument(
        "command",
        choices=[
            "setup",
            "start",
            "stop",
            "lock",
            "credentials",
            "serve",
            "preflight",
            "backup",
            "lan-configure",
            "staff-add",
            "staff-disable",
            "staff-list",
        ],
    )
    parser.add_argument("profile", nargs="?", choices=["edge-a", "edge-b", "central"], default="edge-a")
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--lan", action="store_true", help="Serve edge-a over verified HTTPS on its configured private LAN IP"
    )
    parser.add_argument("--lan-ip", help="Private IPv4 address currently assigned to this computer")
    parser.add_argument("--username")
    parser.add_argument("--workspace")
    parser.add_argument("--role", choices=["clinician", "admin"], default="clinician")
    args = parser.parse_args()
    if args.command == "setup":
        setup()
    elif args.command == "serve":
        serve(args.profile)
    elif args.command == "start":
        start(lan=args.lan)
    elif args.command == "stop":
        stop()
    elif args.command == "lock":
        if sys.platform != "darwin":
            parser.error("On Linux, stop EdgeMed and unmount the LUKS vault using your system tooling")
        stop()
        subprocess.run(["hdiutil", "detach", str(VAULT)], check=True)
        print("Services stopped and encrypted vault unmounted.")
    elif args.command == "preflight":
        from .operations import preflight

        print(json.dumps(preflight(PROJECT), indent=2))
    elif args.command == "backup":
        from .operations import cold_backup

        if not args.output:
            parser.error("backup requires --output (a new directory)")
        if sys.platform != "darwin":
            parser.error("Linux backup requires an offline LUKS volume snapshot; see installation guide")
        stop()
        if VAULT.is_mount():
            subprocess.run(["hdiutil", "detach", str(VAULT)], check=True)
        print(json.dumps(cold_backup(RUNTIME / "data.sparsebundle", args.output), indent=2))
    elif args.command == "lan-configure":
        if not args.lan_ip:
            parser.error("lan-configure requires --lan-ip")
        from .lan import configure, private_lan_ip

        private_lan_ip(args.lan_ip)
        stop()
        mount_vault()
        result = configure(VAULT / "pki", args.lan_ip, 8765 + PORT_OFFSET)
        print(json.dumps({**result, "ca_path": str(VAULT / "pki/lan-ca.pem")}, indent=2))
    elif args.command == "staff-add":
        if not args.username or not args.workspace:
            parser.error("staff-add requires --username and --workspace")
        from .accounts import add

        staff = load_secret("edge-a")
        password = add(staff, args.username, args.workspace, args.role)
        stop()
        save_secret("edge-a", staff)
        print("Staff account added. Username:", args.username, "Password (shown once):", password)
    elif args.command == "staff-disable":
        if not args.username:
            parser.error("staff-disable requires --username")
        from .accounts import disable

        staff = load_secret("edge-a")
        disable(staff, args.username)
        stop()
        save_secret("edge-a", staff)
        print("Staff account disabled; restart services to resume with fresh sessions.")
    elif args.command == "staff-list":
        staff = load_secret("edge-a")
        print(
            json.dumps(
                [
                    {
                        "username": name,
                        "workspace": data["owner"],
                        "role": data["role"],
                        "disabled": data.get("disabled", False),
                    }
                    for name, data in sorted(staff["operators"].items())
                ],
                indent=2,
            )
        )
    elif args.command == "credentials":
        print("Username: operator\nPassword:", load_secret(args.profile)["initial_password"])


if __name__ == "__main__":
    main()
