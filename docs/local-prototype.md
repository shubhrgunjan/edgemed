# Local prototype implementation

This branch adds a working, synthetic-data-only prototype to the existing architecture repository. It is a draft implementation, not a production or clinical deployment. The earlier Phase 0 documents describe the intended architecture; they are preserved as design references. The implementation was explicitly authorized after the planning stage. The complete roadmap in `project-planning.md` is not a completion checklist.

## Implemented

- Python/FastAPI local service with SQLCipher canonical storage, immutable revisions, a durable indexing queue, audit events, ownership filtering, and tombstones.
- Real Qdrant Edge with cached FastEmbed/ONNX dense embeddings, local lexical ranking, and reciprocal-rank fusion.
- React/TypeScript interface for local login, memory search and inspection, observations, revision/conflict review, subject relationships, timeline, and synchronization status.
- Two simulated devices and a central gateway using mutual TLS, signed operations/receipts, durable synchronization queues, idempotency, and explicit conflict resolution.
- Synchronization exports only predefined reviewed synthetic reference identifiers/variants. Arbitrary notes and private embeddings are excluded from the export schema.
- Signed full reference snapshots from Qdrant Server with archive/manifest validation and a separate imported reference shard.
- macOS launcher with an encrypted APFS sparsebundle, Keychain secrets, generated credentials, Argon2 authentication, session cookies, CSRF checks, and loopback host/origin restrictions.

## Local operation

The development environment used Python 3.12, the committed `uv.lock`, the frontend npm lockfile, Qdrant Server 1.19.1, and the locally cached `BAAI/bge-small-en-v1.5` model. The native Qdrant executable is expected at `.tools/qdrant`; the model cache is under `.cache`. Neither is committed. A fresh clone still needs these assets provisioned, SQLCipher build prerequisites, dependency installation, and a frontend build. There is no complete automated fresh-machine installer yet.

On the already provisioned development Mac, run from the repository root:

```sh
.venv/bin/python -m edgemed.cli start
.venv/bin/python -m edgemed.cli credentials edge-a
```

The credentials command displays a local password: keep its output private. Device A is at `http://127.0.0.1:8765` and device B at `http://127.0.0.1:8766`. Use only synthetic data. `stop` stops services; `lock` also attempts to unmount the encrypted vault. Browser sign-out does not unmount it. The full lock/restart cycle has not yet been validated.

Runtime storage is in `~/Library/Application Support/EdgeMed Local`, outside the repository. Database files, keys, certificates, model weights, binaries, build outputs, and browser artifacts are excluded from the commit.

## Validation

Checks rerun before this push:

- Ruff: passed.
- Backend pytest: 32 passed; one Starlette TestClient deprecation warning.
- TypeScript and Vite production build: passed.

Earlier local results included eight real integration checks covering synchronization, conflicts, restricted-data exclusion, deletion visibility, mTLS rejection, signature rejection, and Qdrant projection. See `local-integration-results.json`. A full signed reference snapshot was imported; see `snapshot-results.json`. Two Playwright browser tests passed before the final UI refinements; they were not rerun for this push. Dependency audits reported no known vulnerabilities during implementation, not a guarantee of security.

The recorded benchmark used 1,000 synthetic records and 30 queries from five repeated templates: median 15.15 ms, p95 23.69 ms, peak process RSS 263.6 MB. See `benchmark-results.json`. This is a functional/performance sample, not a held-out clinical accuracy evaluation or a large-scale benchmark.

To repeat available checks in the provisioned environment:

```sh
.venv/bin/ruff check edgemed tests scripts
.venv/bin/pytest -q
(cd frontend && npm run build)
```

Browser tests require running local services, provisioned Keychain credentials, and Chromium. Integration scripts mutate synthetic demo state. Python socket blocking tests do not establish operating-system-level network isolation.

## Work remaining before readiness review

- Resolve the deletion-during-embedding race: canonical filtering hides deleted records, but a derived vector may remain if deletion happens while embedding is running.
- Complete fresh-machine provisioning and the final browser/integration regression run.
- Validate vault lock/restart, backup recovery, device revocation, and key rotation workflows.
- Reconcile the prototype API/schema with the existing design contracts and record architecture decisions for the narrowed scope.
- Add differential snapshot support and deeper graph/consolidation/governance behavior if required. Governance is currently advisory, and the graph is a subject relationship view.
- Complete an independent security review before considering real sensitive data. This prototype makes no compliance or clinical-safety claim.
