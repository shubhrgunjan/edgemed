# EdgeMed

![EdgeMed: protected memory across a local care network](assets/edgemed-hero.png)

**A local-first memory and search prototype for synthetic care notes.** Capture observations in an encrypted vault, search them using an on-device model, and optionally share reviewed synthetic references between local servers. EdgeMed is a research demo, not a clinical system.

[Try the public browser demo](https://farhanakhtar0x66.github.io/edgemed-synthetic-demo/) · [Install the local app](docs/installation.md) · [Development roadmap](TODO.md) · [Security boundaries](SECURITY.md)

The public link opens a **synthetic, browser-only sample**: keyword search, capture, inspection, deletion, and Latte/Mocha themes. It has no account, API, persistent note storage, encrypted vault, or semantic search. Notes added there exist only in the tab and disappear on refresh. **Never enter patient information.** The installable app below runs the actual local backend.

## What works today

| Area | Current prototype |
| --- | --- |
| Local operation | A macOS ARM64 server keeps serving over loopback or a private LAN without internet, while its power and LAN remain available. |
| Protected storage | A macOS encrypted sparsebundle holds the SQLCipher database and local Qdrant index. Keys are held in the Keychain. |
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

The supported encrypted launcher and LAN demo currently require **macOS ARM64**, Python 3.12, `uv`, Node.js 22+, Xcode command-line tools, and Homebrew SQLCipher. Start with a fresh clone:

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

Open **http://127.0.0.1:8765** on that Mac. `setup` provisions the encrypted vault and local operator account. The asset provisioning step needs internet once; normal local capture and search do not. For passwords, staff accounts, private-LAN certificates, firewall boundaries, backups, and Linux test-only setup, follow the [installation guide](docs/installation.md). Do not expose the local server to the public internet.

## Verify and explore

```sh
uv run ruff check edgemed tests scripts
uv run pytest -q
(cd frontend && npm run build && npm run build:demo)
```

The full Linux retrieval suite needs `uv run python scripts/provision_assets.py --model-only` first. The public demo can be built from `frontend` with `npm run build:demo`; its output is `frontend/dist-demo/` and contains only static assets. The measured results and limitations are recorded in [next-phase validation](docs/next-phase-results.md) and [hospital LAN verification](docs/hospital-lan-results.md).

## Safety and project state

This repository uses synthetic examples only. It has no independent security audit, clinical validation, hospital identity-provider integration, high-availability deployment, or approval to handle real patient records. A browser-visible public sample cannot be treated as the encrypted local app. See [SECURITY.md](SECURITY.md), the [current status](docs/PROJECT_STATUS.md), and the [next steps](TODO.md) before extending it.

Licensed under [Apache-2.0](LICENSE). The illustrations in `assets/` were generated for this project and contain no patient data.
