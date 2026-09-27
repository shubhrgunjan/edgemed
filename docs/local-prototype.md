# EdgeMed local prototype

The application now includes the next-phase correctness, security, retrieval and interface changes. It remains a synthetic-data-only informational memory prototype. The original architecture documents are design references, not a statement that every post-hackathon feature is implemented.

## What changed

- Versioned indexing jobs prevent a stale embedding/upsert acknowledgement from clearing a pending deletion. Native worker operations finish before storage closes.
- Search uses bulk current-head reads, a bounded in-memory lexical corpus, canonical prefiltering and a final authorization/revision check. It no longer silently limits the eligible corpus to 10,000 records. Conflicting search results identify the matched revision.
- Five-minute idle expiry and 30-minute absolute expiry protect sessions. Polling does not extend them. Sign-out/expiry cancels data requests and clears query, forms, selections and records; late responses cannot restore a previous session's data.
- Gateway request and response sizes are bounded. Pull pages and acceptance receipts are validated. The interface distinguishes gateway reachability, paused sharing, stale status and verification errors.
- The interface emphasizes capture, local search, review and sharing history. Approved reference operations are visibly separate from private observations. Dialog keyboard focus, responsive layout and delayed-response behavior have browser tests.
- Snapshot download is outside the search lock; replacement is opened before the working shard is closed. Failed activation preserves the previous reference state.
- The launcher supports isolated verification namespaces, verifies encrypted image status, checks pinned asset hashes, waits for readiness and can create a verified cold encrypted-container backup.

## Setup on macOS ARM64

Install Python 3.12, uv, Node.js and SQLCipher build prerequisites. On a development Mac with Homebrew:

```sh
brew install sqlcipher uv node
export CFLAGS="-I$(brew --prefix sqlcipher)/include/sqlcipher"
export LDFLAGS="-L$(brew --prefix sqlcipher)/lib -lsqlcipher"
uv sync --frozen
(cd frontend && npm ci && npm run build)
uv run python scripts/provision_assets.py
uv run python -m edgemed.cli setup
uv run python -m edgemed.cli preflight
uv run python -m edgemed.cli start
```

Provisioning explicitly downloads pinned public model and binary assets and checks their hashes. Runtime model loading uses the pinned local model path and has no download fallback. The committed asset manifest currently supports macOS ARM64 only. Do not substitute a Linux ARM wheel for an Android build.

Device A is at `http://127.0.0.1:8765`, Device B at `http://127.0.0.1:8766`. Retrieve the generated local password privately with `uv run python -m edgemed.cli credentials edge-a`. Do not include that output in logs, screenshots, tickets or commits.

`stop` stops the services; `lock` stops them and unmounts the encrypted vault. Sign-out only hides the browser workspace. `backup --output /path/to/new-directory` stops services, unmounts the vault and copies/checksums its encrypted container. That backup requires the original Keychain material; portable key recovery is not implemented.

## Verification

See [next-phase results](next-phase-results.md) for the measured comparison, completed tests and explicit limitations. Run:

```sh
uv run ruff check edgemed tests scripts
uv run pytest -q
(cd frontend && npm run build)
```

Real model tests require the verified cache. Browser and live synchronization tests require a separately provisioned verification environment; see [runbook](next-phase-runbook.md). They must not reset or mutate the user's original vault.

## Security boundary

SQLCipher is authoritative; Edge stores derived vectors. Private observations and their embeddings stay local. Only predefined reviewed synthetic reference identifiers and variants enter synchronization. TLS, signatures, idempotency, canonical filtering, session controls and encrypted runtime storage support this boundary.

Encryption does not protect decrypted process memory from malware running as the unlocked OS user. HMAC audit chaining does not prove protection against whole-store rollback. Deletion hides/purges derived vectors but intentionally preserves encrypted revision history. No clinical or regulatory compliance claim is made.
