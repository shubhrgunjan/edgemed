# EdgeMed

![EdgeMed: protected memory across a local care network](assets/edgemed-hero.png)

**A local-first memory and search prototype for synthetic care notes.** Capture observations in an encrypted vault, search them using an on-device model, and optionally share reviewed synthetic references between local servers. EdgeMed is a research demo, not a clinical system.

[Try the public browser demo](https://farhanakhtar0x66.github.io/edgemed-synthetic-demo/) · [Install the local app](docs/installation.md) · [Development roadmap](TODO.md) · [Security boundaries](SECURITY.md)

The public link opens a **synthetic, browser-only sample**: keyword search, capture, inspection, deletion, and Latte/Mocha themes. It has no account, API, persistent note storage, encrypted vault, or semantic search. Notes added there exist only in the tab and disappear on refresh. **Never enter patient information.** The installable app below runs the actual local backend.

## What works today

| Area | Current prototype |
| --- | --- |
| Local operation | macOS ARM64 has a live synthetic-data rehearsal. macOS Intel and Linux x86-64/ARM64 have experimental launcher paths that still need physical encrypted-host rehearsals. Any host needs power and a working local network for browser clients. |
| Protected storage | macOS uses an encrypted sparsebundle and Keychain. Linux requires an operator-mounted LUKS2 volume and an unlocked Secret Service/KWallet keyring; no plaintext fallback. |
| Search | Pinned local embeddings, lexical retrieval, and workspace-aware access checks. Model assets are downloaded and hash-verified during setup, never fetched by runtime search. |
| Staff demo | Separate synthetic-data accounts, shared workspace notes, creator-only personal notes, private-IP HTTPS, and server-side authorization. |
| Optional sharing | Only reviewed synthetic reference variants enter the demo synchronization path. Staff observations do not. |
| Interface | Responsive browser UI with Catppuccin Latte and Mocha themes and a persistent theme switch. |

The architecture is a **local server plus browsers**. A phone on the same trusted LAN can use the interface, but the backend does not run on the phone. A native Android backend and app remain on the [roadmap](TODO.md).

## Next development path

- [ ] Complete independent security and privacy reviews before any real-data pilot.
- [ ] Package and harden a hospital-local server with managed identity, backups, monitoring, and failover.
- [ ] Test a physical Android device as a secure LAN browser client.
- [ ] Build a native Android app and decide whether it also needs an encrypted on-device backend for LAN outages.
- [ ] Validate retrieval quality and clinical workflows with appropriately governed data and expert review.

The [full task list](TODO.md) separates security gates, Android work, and scale testing.

## Install the full local app

For the macOS launcher, use **Apple Silicon or Intel**, Python 3.12, `uv`, Node.js 22+, Xcode command-line tools, and Homebrew SQLCipher. Start with a fresh clone:

```sh
git clone https://github.com/shubhrgunjan/edgemed.git
cd edgemed
brew install sqlcipher uv node
export CFLAGS="-I$(brew --prefix sqlcipher)/include/sqlcipher"
export LDFLAGS="-L$(brew --prefix sqlcipher)/lib -lsqlcipher"
uv sync --frozen
(cd frontend && npm ci && npm run build)
uv run python scripts/provision_assets.py
uv run python -m edgemed.cli setup
uv run python -m edgemed.cli start
```

Open **http://127.0.0.1:8765** on that Mac. `setup` provisions the encrypted vault and local operator account. The asset provisioning step needs internet once; normal local capture and search do not. For passwords, staff accounts, private-LAN certificates, firewall boundaries, and backups, follow the [macOS installation guide](docs/installation.md). For **Linux x86-64 or ARM64**, follow the separate [encrypted Linux setup](docs/linux-installation.md); it needs a pre-mounted LUKS2 volume and protected system keyring. Do not expose the local server to the public internet.

The lockfile selects ONNX Runtime 1.23.2 on macOS Intel because newer pinned releases lack an Intel wheel, and 1.30.0 on Apple Silicon and 64-bit Linux. CI runs real offline retrieval on all four targets; encrypted-vault setup still needs a physical-host rehearsal on the new targets.

32-bit x86 and ARM are **not supported** by this runtime: the pinned [Qdrant Edge](https://pypi.org/project/qdrant-edge-py/0.8.0/#files) and [ONNX Runtime](https://pypi.org/project/onnxruntime/1.23.2/#files) releases do not publish the required 32-bit native wheels. A browser on a 32-bit device can still access a 64-bit LAN server if its browser supports the interface. The Linux launcher and macOS Intel path need physical-host end-to-end rehearsal before operational use.

## Verify and explore

```sh
uv run ruff check edgemed tests scripts
uv run pytest -q
(cd frontend && npm run build && npm run build:demo)
```

For Linux retrieval tests without the server, run `uv run python scripts/provision_assets.py --model-only` first. A full 64-bit install provisions the verified native Qdrant binary as well. The public demo can be built from `frontend` with `npm run build:demo`; its output is `frontend/dist-demo/` and contains only static assets. The measured results and limitations are recorded in [next-phase validation](docs/next-phase-results.md) and [hospital LAN verification](docs/hospital-lan-results.md).

## Safety and project state

This repository uses synthetic examples only. It has no independent security audit, clinical validation, hospital identity-provider integration, high-availability deployment, or approval to handle real patient records. A browser-visible public sample cannot be treated as the encrypted local app. See [SECURITY.md](SECURITY.md), the [current status](docs/PROJECT_STATUS.md), and the [next steps](TODO.md) before extending it.

Licensed under [Apache-2.0](LICENSE). The illustrations in `assets/` were generated for this project and contain no patient data.
