# Linux 64-bit synthetic demo setup

This is a **synthetic-data prototype**, not a clinical deployment guide. The Unix launcher supports Linux x86-64 and ARM64 with Python 3.12. A desktop Linux session with an unlocked Secret Service or KWallet is required for the current key store. The backend remains local to the host by default; the optional LAN mode uses the same private-IP HTTPS workflow as macOS. A headless hospital service, tested restore procedure, and real-data approval remain future work.

## Protected storage comes first

Before running `setup`, have an administrator prepare a **dedicated, already initialized LUKS2** volume with a filesystem. Do not format a device containing any existing data. The EdgeMed process must run as an ordinary user; only mounting and unlocking the volume require administrator privileges. The app verifies an exact mount at `~/.local/share/edgemed/vault`, backed by `/dev/mapper/edgemed-vault` (or the name in `EDGEMED_LUKS_MAPPER`), whose kernel mapper UUID identifies it as LUKS2. It refuses a plain directory, bind mount, different mapper, or world-accessible mount.

For a previously prepared LUKS2 device, adapt this example to the real device UUID:

```sh
install -d -m 700 "$HOME/.local/share/edgemed/vault"
sudo cryptsetup open --type luks2 /dev/disk/by-uuid/YOUR-LUKS-UUID edgemed-vault
sudo mount /dev/mapper/edgemed-vault "$HOME/.local/share/edgemed/vault"
sudo chown "$USER" "$HOME/.local/share/edgemed/vault"
chmod 700 "$HOME/.local/share/edgemed/vault"
findmnt --mountpoint "$HOME/.local/share/edgemed/vault"
```

Use your organization’s backup and recovery procedure for the LUKS device and its header. A lost LUKS passphrase/header or lost keyring material can make the data unrecoverable. The EdgeMed `backup` and `lock` commands currently support macOS only; on Linux, stop EdgeMed, unmount the vault, and close the mapper using your system’s approved tooling. Never copy a live mounted database as a recovery backup.

## Install dependencies and verified assets

On Ubuntu/Mint, install Python 3.12, `uv`, Node.js 22+, build tools, `libsqlcipher-dev`, `pkg-config`, `util-linux`, `cryptsetup`, and a configured GNOME Secret Service or KWallet session. Follow your distribution’s trusted package sources. `uv` must be run in the same unlocked keyring session that will run EdgeMed. The app rejects plaintext or unavailable keyring backends. On headless Linux, [keyring’s Secret Service instructions](https://keyring.readthedocs.io/en/stable/#using-keyring-on-headless-linux-systems) explain the D-Bus requirement; keep that session available to the services.

From a fresh clone:

```sh
git clone https://github.com/shubhrgunjan/edgemed.git
cd edgemed
export CFLAGS=-I/usr/include/sqlcipher
export LDFLAGS=-lsqlcipher
uv sync --frozen
(cd frontend && npm ci && npm run build)
uv run python scripts/provision_assets.py
uv run ruff check edgemed tests scripts
uv run pytest -q
uv run python -m edgemed.cli setup
uv run python -m edgemed.cli preflight
uv run python -m edgemed.cli start
```

Open `http://127.0.0.1:8765` on that host. The one-time provisioning step downloads the same pinned ONNX model on every host and a Qdrant 1.19.1 binary chosen for the current 64-bit OS/CPU. Both archive and extracted executable are checked against SHA-256 values in `assets-manifest.json`. Runtime capture and search do not download assets. If a hash does not match, the installer stops without replacing a verified executable.

To stop, run `uv run python -m edgemed.cli stop`. Then, after confirming services stopped, use your approved unmount and `cryptsetup close edgemed-vault` procedure. Do not close the mapper while files are in use. For private-LAN staff access, follow the account and certificate steps in the [installation guide](installation.md); apply a host firewall that admits only the trusted LAN to Edge A.

The full Linux launcher has not yet been rehearsed on a physical LUKS2 host. CI checks Python behavior, native asset provisioning, and retrieval on x86-64 and ARM64; an actual encrypted-host outage and restore rehearsal is still required before treating Linux as an operational deployment.
