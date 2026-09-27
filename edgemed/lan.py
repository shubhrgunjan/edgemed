"""Explicit, short-lived TLS configuration for the synthetic hospital LAN demo."""

import datetime as dt
import ipaddress
import json
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from .security import private_write


PRIVATE_NETWORKS = tuple(
    ipaddress.ip_network(cidr) for cidr in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
)


def private_lan_ip(value):
    address = ipaddress.ip_address(value)
    if address.version != 4 or not any(address in net for net in PRIVATE_NETWORKS):
        raise ValueError("Use a private IPv4 address assigned to this computer's hospital/demo LAN")
    return address


def configure(root: Path, address: str, port: int):
    ip = private_lan_ip(address)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    now = dt.datetime.now(dt.timezone.utc)
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "EdgeMed demo LAN CA")])
    ca = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - dt.timedelta(minutes=5))
        .not_valid_after(now + dt.timedelta(days=30))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(
            x509.KeyUsage(True, False, False, False, False, True, True, False, False), critical=True
        )
        .sign(ca_key, hashes.SHA256())
    )
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    server = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "EdgeMed demo server")]))
        .issuer_name(ca_name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - dt.timedelta(minutes=5))
        .not_valid_after(now + dt.timedelta(days=7))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ip)]), critical=False)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .sign(ca_key, hashes.SHA256())
    )
    private_write(root / "lan-ca.pem", ca.public_bytes(serialization.Encoding.PEM).decode())
    private_write(
        root / "lan-ca.key",
        ca_key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
        ).decode(),
    )
    private_write(root / "lan-server.pem", server.public_bytes(serialization.Encoding.PEM).decode())
    private_write(
        root / "lan-server.key",
        key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
        ).decode(),
    )
    private_write(root / "lan.json", json.dumps({"ip": str(ip), "port": port}))
    return {"origin": f"https://{ip}:{port}", "ca_fingerprint_sha256": ca.fingerprint(hashes.SHA256()).hex()}


def load(root: Path, port: int):
    settings = json.loads((root / "lan.json").read_text())
    ip = private_lan_ip(settings["ip"])
    if settings["port"] != port:
        raise RuntimeError("LAN certificate port differs from this runtime; reconfigure LAN")
    ca = x509.load_pem_x509_certificate((root / "lan-ca.pem").read_bytes())
    cert = x509.load_pem_x509_certificate((root / "lan-server.pem").read_bytes())
    now = dt.datetime.now(dt.timezone.utc)
    key = serialization.load_pem_private_key((root / "lan-server.key").read_bytes(), password=None)
    if key.public_key().public_numbers() != cert.public_key().public_numbers():
        raise RuntimeError("LAN TLS key and certificate do not match")
    try:
        ca.public_key().verify(
            cert.signature, cert.tbs_certificate_bytes, padding.PKCS1v15(), cert.signature_hash_algorithm
        )
    except Exception as exc:
        raise RuntimeError("LAN certificate is not signed by the configured CA") from exc
    if (
        now < cert.not_valid_before_utc
        or now >= cert.not_valid_after_utc
        or now < ca.not_valid_before_utc
        or now >= ca.not_valid_after_utc
    ):
        raise RuntimeError("LAN certificate expired; reconfigure LAN and redistribute the new CA")
    if ip not in cert.extensions.get_extension_for_class(
        x509.SubjectAlternativeName
    ).value.get_values_for_type(x509.IPAddress):
        raise RuntimeError("LAN certificate does not cover the configured IP")
    return {
        "origin": f"https://{ip}:{port}",
        "bind": str(ip),
        "tls_cert": str(root / "lan-server.pem"),
        "tls_key": str(root / "lan-server.key"),
        "tls_ca": str(root / "lan-ca.pem"),
    }
