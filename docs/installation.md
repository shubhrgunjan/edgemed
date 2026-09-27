# Installation and hospital LAN demo

This guide is for a **synthetic-data demonstration** on one macOS ARM64 server and browsers on the same private LAN. EdgeMed can keep serving when the internet is down, provided the local server, LAN and power remain available. Do not import real patient data.

## 1. Install and verify the server

Use Python 3.12, `uv`, Node.js 22+, Xcode command-line tools and Homebrew SQLCipher on the Mac. From a fresh clone:

```sh
brew install sqlcipher uv node
export CFLAGS="-I$(brew --prefix sqlcipher)/include/sqlcipher"
export LDFLAGS="-L$(brew --prefix sqlcipher)/lib -lsqlcipher"
uv sync --frozen
(cd frontend && npm ci && npm run build)
uv run python scripts/provision_assets.py
uv run ruff check edgemed tests scripts
uv run pytest -q
uv run python -m edgemed.cli setup
uv run python -m edgemed.cli preflight
```

`provision_assets.py` downloads pinned public ONNX model files and a macOS Qdrant binary once, and checks each SHA-256 hash against `assets-manifest.json`. It needs internet during installation. The model and server binary are ignored by Git. `setup` creates an AES-256 encrypted sparsebundle and stores keys in the macOS Keychain. Keep both the encrypted container and protected Keychain material; losing the keys makes the container unrecoverable. For the operator password, run `uv run python -m edgemed.cli credentials edge-a` privately. Do not paste credentials into logs or tickets.

For server-only use:

```sh
uv run python -m edgemed.cli start
```

Open `http://127.0.0.1:8765` on that Mac. `stop` stops processes; `lock` also unmounts the encrypted vault. Do not point testing tools at a vault containing important records; the [runbook](next-phase-runbook.md) explains isolated namespaces.

## 2. Configure HTTPS on a private LAN

Assign the Mac a stable private IPv4 address on the demo network, such as a DHCP reservation. Find the address in macOS Network settings; `ipconfig getifaddr en0` is useful when Wi-Fi uses `en0`. Replace the example below with the address assigned to **this Mac**:

```sh
uv run python -m edgemed.cli lan-configure --lan-ip 192.168.1.50
```

This stops running EdgeMed services, leaves the vault mounted, and generates a separate seven-day server certificate for exactly that IP, signed by a separate 30-day demo LAN CA. The command prints the HTTPS URL, public CA path and SHA-256 fingerprint. The CA private key and server private key remain in the encrypted vault. If the Mac's IP changes or the certificate expires, rerun `lan-configure`; client devices must trust the newly issued public CA again.

Move **only** the public `lan-ca.pem` shown by the command to each demonstration device using a trusted channel. Verify its SHA-256 fingerprint against the Mac before installing it in that device's trust store. On iOS, adding a profile alone does not enable full trust; enable trust in Certificate Trust Settings as described by [Apple](https://support.apple.com/en-au/102390). On Android, follow the device/browser policy for a user-installed CA and test that browser before the demo. Do not copy `lan-ca.key`, `lan-server.key`, the sparsebundle, or Keychain credentials. A browser certificate warning means trust is incomplete; fix the certificate path rather than bypassing the warning. Remove the demo CA from client trust stores after the event.

Allow the Edge A port (default TCP 8765) only from the trusted demonstration LAN. Do not forward it from the router or expose it to the public internet. Edge B (8766), the gateway (9443) and Qdrant (6333) remain loopback-bound on the Mac. Connect browsers to the printed `https://<server-ip>:8765` URL. A browser using `http://`, a different IP, a DNS alias, or a reverse proxy will fail origin or certificate checks.

## 3. Add staff and start LAN mode

Each staff member gets a separate account. A workspace name groups staff who may read and edit shared synthetic observations. Use the **same** workspace name for colleagues in one ward; use another for isolation. `operator` and `personal` are reserved workspaces.

```sh
uv run python -m edgemed.cli staff-add --username alice --workspace ward-a --role clinician
uv run python -m edgemed.cli staff-add --username bob --workspace ward-a --role clinician
uv run python -m edgemed.cli staff-add --username wardadmin --workspace ward-a --role admin
uv run python -m edgemed.cli staff-list
uv run python -m edgemed.cli start --lan
```

Each `staff-add` stops services before changing Keychain material and prints a generated password **once**. Give it only to that staff member through a private channel. Do not save it in the repository. Starting with `--lan` binds Edge A only to the configured private IP and serves it over HTTPS; the other services stay local to the Mac. `start` without `--lan` retains the server-only loopback mode. Stop before changing modes. Run `uv run python -m edgemed.cli staff-disable --username alice` to disable an account; the command stops services and clears active sessions. Start again afterwards.

Staff roles and record rules:

| Account/record | Access |
| --- | --- |
| Clinician, `SENSITIVE` | Create/read/search/revise in the named workspace; workspace admin removes shared records. |
| Clinician, `HIGHLY_SENSITIVE` | Create/read/search/revise/remove only their own personal observations. |
| Workspace admin | Same workspace access plus shared-record removal, conflict review and synthetic fixture loading. No access to another user's personal observations or server-wide sync controls. |
| Other workspace | Cannot list, search, read or edit these records. |

The original `operator` account keeps its original workspace and existing data. Hospital staff do not inherit access to it. “Personal” in this demo means personal to one staff account on the server; it is not a copy stored on their phone. Sign-out ends the browser session, while `lock` is an operator action on the Mac. The certificate authority is for this demo only; use a hospital-managed certificate and identity system in any later deployment.

## 4. Rehearse without internet

With the Mac and two browsers connected to the same LAN, sign in as `alice` and `bob`. Alice saves one **Shared with workspace** observation and one **Personal · only me** observation. Bob should see the shared entry but not Alice's personal entry in listing, search or direct detail URLs. Sign in from a different workspace to verify neither record is visible. The workspace admin can remove the shared entry; Alice can remove her own personal entry.

Disconnect the LAN from the internet while keeping local Wi-Fi and the Mac running. Capture and search a synthetic observation from both browsers. Then restart EdgeMed and confirm the notes persist. If the Mac or LAN goes down, browsers cannot save or search until it returns. Run the [isolated verification and backup checks](next-phase-runbook.md) before the demo. A cold backup is made with `uv run python -m edgemed.cli backup --output /path/to/new-directory`; it stops services, unmounts the vault, copies and checksums only the encrypted image, and still requires the original Keychain keys.

Linux users can run the retrieval suite by provisioning only the model with `uv run python scripts/provision_assets.py --model-only` and then `uv run pytest -q`; Linux hospital-server deployment is not included here.
