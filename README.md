# EdgeMed

EdgeMed is a **synthetic-data-only** memory and search prototype. A macOS server stores observations in an encrypted local vault, builds a local vector index, and serves a browser interface. It can keep working when the internet is unavailable while the browser can still reach the server over the local network.

The optional hospital LAN demo gives staff separate accounts. Staff in the same workspace see `SENSITIVE` observations together; `HIGHLY_SENSITIVE` observations are visible only to their creator. Workspace administrators can manage shared records and demo sync. All access checks run on the server, including listing, full detail, search and edits. This is a research demonstration, not a clinical system or a substitute for an EHR.

## Install and run

See the [installation guide](docs/installation.md) for macOS prerequisites, verified model and Qdrant assets, encrypted vault setup, staff accounts, LAN TLS certificates and device setup. The shortest local-only path after installing prerequisites is:

```sh
uv sync --frozen
(cd frontend && npm ci && npm run build)
uv run python scripts/provision_assets.py
uv run python -m edgemed.cli setup
uv run python -m edgemed.cli start
```

Open `http://127.0.0.1:8765` on the server. The model and server asset download is an explicit installation step; runtime search never downloads them.

To run the verified retrieval tests on Linux, use `uv run python scripts/provision_assets.py --model-only` followed by `uv run pytest -q`. The encrypted launcher and LAN demo currently require macOS. For full test and recovery instructions, see the [verification runbook](docs/next-phase-runbook.md).

## Current boundaries

- The Mac must remain powered on; browsers need a working local network path to it. A phone does not run the search backend.
- Edge A can be deliberately exposed on one private LAN IP over HTTPS. Edge B, the central sync gateway and Qdrant server stay bound to loopback.
- Separate staff identities, workspace scoping, personal observations, CSRF checks, secure cookies, short sessions and verified encrypted storage support the demo. User provisioning is an operator CLI task that stops services and requires a restart.
- Only reviewed synthetic reference variants enter optional device-to-device sync. Staff observations are not sent to the central sync service. Existing operator data stays in its original workspace.
- There is no high-availability cluster, hospital identity-provider integration, emergency access workflow, independent security audit, clinical validation, or support for real patient data.

The original architecture and planning documents remain under [docs](docs/) and [architecture](architecture/). The measured implementation results and known limits are in [next-phase results](docs/next-phase-results.md) and [hospital LAN verification](docs/hospital-lan-results.md).
