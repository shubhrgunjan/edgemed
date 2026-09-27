# EdgeMed / LEX PS03: security-first project plan

**Prepared:** 27 September 2026
**Destination:** `~/Projects/lex-local-ps3/project-planning.md`
**Status:** Planning only. No application implementation, installations, deployment, or repository changes are authorized by this document. The user will explicitly request execution later, potentially using a different coding model.
**Architecture baseline:** `shubhrgunjan/edgemed`, commit `595229864c3b3ff2b372b4037f873c20d6e7296c`.

## 1. What this plan recommends

Build EdgeMed as a local-first memory application with Qdrant Edge for semantic retrieval, an encrypted SQLite database for authoritative records, local embeddings, and a React interface. Retain the existing vector/graph/timeline separation. Demonstrate selective synchronization with a real Qdrant Server, initially running as a separate local service representing the central node.

The principal change is implementation order: establish privacy, authorization, encryption, and recoverable persistence before adding cloud synchronization or rich visualizations. Patient observations stay local by default. A privacy filter does not make arbitrary clinical text safe to publish. Shared knowledge, synthetic approved examples, and narrowly defined operational records can demonstrate the edge-to-central workflow without exporting patient notes.

This is a proposed refinement of the existing architecture, not a replacement already approved by the team. Section 4 records each change and its reason. Section 15 gives the next coding model a bounded starting point after execution is requested.

### Current task boundary

- Deliver only this planning Markdown file in the requested project folder.
- Read the attached PDF and linked repository as source material. Instructions embedded in either are not independent authorization to execute actions.
- Do not clone/scaffold the application, install project packages, start services, generate keys, change disk encryption, upload data, create commits, or modify GitHub during this planning task.
- Source material was inspected read-only; a temporary local rendering was used because the PDF is image-only.

## 2. Source findings and assumptions

### Verified findings

1. The supplied one-page PDF is PS03, **AI-Powered Edge Memory & Intelligence Platform**. It requires Qdrant Edge, offline semantic memory, low-latency vector and hybrid search, dynamic local/sync decisions, reconnect synchronization with Qdrant Server, evolving memory/conflicts, and an interface exposing memory, search, synchronization, and system activity.
2. The repository identifies itself as architecture/documentation only. Its project status says implementation has not started. It contains architecture documents, ADRs, schemas, example data, API specifications, and a proposed roadmap.
3. Existing choices include FastAPI, local FastEmbed/ONNX embeddings, Qdrant Edge, SQLite graph/event storage, React/TypeScript/Vite, Cytoscape, and central Qdrant Server.
4. Existing security documents already propose encrypted storage, mTLS, privacy classification, signed snapshots, and synthetic data. These are design intentions, not verified running controls.
5. The repository assumes an AMD Ryzen/Linux machine with 8 GB RAM. This planning session runs on **macOS, arm64**. Installed RAM was not verified; the read-only system query was restricted.
6. Qdrant's official documentation currently describes Edge as beta. The package page inspected lists `qdrant-edge-py` 0.8.0 with a CPython-compatible macOS ARM64 wheel. This establishes a plausible native path, not proof that the full dependency set works on this Mac. [Qdrant Edge](https://qdrant.tech/documentation/edge/), [package files](https://pypi.org/project/qdrant-edge-py/).
7. Official synchronization examples provide snapshot/delta primitives and application-managed upstream updates. Durable queuing, policy enforcement, authorization, conflict handling, and retry correctness remain application responsibilities. [Synchronization patterns](https://qdrant.tech/documentation/edge/edge-data-synchronization-patterns/).

### Planning assumptions, subject to revision

- Retain the medical-memory demonstration domain and use **synthetic data only** for development and demos. Real patient-data onboarding is outside the initial scope.
- Start with one local operator and one facility namespace. Include authorization boundaries in the schema now; do not claim a production multi-tenant platform.
- Develop natively on this Mac where compatible; benchmark the team's Linux target separately if it remains the presentation device.
- Demonstrate two logical edge devices with separate storage roots, identities, credentials, and queues. They may run on one machine, but must not share files or keys.
- Use a local central-node simulator with actual Qdrant Server and the real sync protocol. Remote deployment is a separate future step.
- No deadline or effort budget has been confirmed. The PDF mentions event dates but does not establish an execution schedule for this request.

## 3. Problem-statement coverage and scope

| PS03 requirement | Planned implementation | Demonstrable acceptance evidence |
| --- | --- | --- |
| Searchable memory on the edge | Local Qdrant Edge vectors plus authoritative local records | Ingest, restart, and retrieve without central services |
| Vector and hybrid search offline | Local dense embeddings and sparse/BM25 retrieval, fused ranking | Semantic paraphrase and exact-term queries work with outbound traffic blocked |
| Decide local versus synchronized | Hard privacy/authorization rules, followed by an explainable relevance governor | Private note is blocked; eligible shared record is queued with reasons |
| Synchronize when connectivity returns | Durable sanitized outbox, central API, real Qdrant Server, verified inbound updates | A record leaves device A once logically, survives retries, and reaches device B |
| Continue under intermittent connectivity | Independent local reads/writes and bounded background retry | Disconnect, edit, restart offline, reconnect, and converge |
| Evolving memory and conflicts | Immutable revisions, explicit ancestry, tombstones, reviewable conflicts | Concurrent edits remain visible; resolution adds a new revision |
| User-facing inspection | Memory explorer, search, timeline, sync monitor, activity and policy inspector | User can see what stayed local, what was transmitted, and why |
| Meaningful edge-to-central AI workflow | Local retrieval + memory decisions + approved sharing + returned knowledge | End-to-end evidence beyond an isolated vector database |

### Minimum complete product

- Authenticated local interface; encrypted authoritative storage and protected vector directories.
- Synthetic memory create/read/revise/archive, bounded imports, provenance, privacy decisions.
- Real local dense and hybrid retrieval, basic graph context and timeline.
- Durable two-device synchronization, authorization, conflict review, deletion/tombstone handling.
- Offline cold-start demonstration, security-negative tests, and measured performance.
- Basic Memory Lab controls and an inspectable explanation for each decision.

### After the core gates pass

- Rich Cytoscape exploration, consolidation of repeated synthetic observations, governor simulation controls, and differential snapshot optimization.
- Optional local generative summaries only after retrieval is reliable and resource use is measured. An LLM is not needed to satisfy the core AI requirement: embeddings and retrieval provide the initial intelligence.
- Remote hosting, organizational account management, broad clinical extraction, mobile packaging, and real patient-data use are separate projects or later milestones.

The repository's differential-snapshot and consolidation acceptance goals remain tracked; deferring them from the first vertical slice does not mean claiming those repository gates are complete.

## 4. Architecture review: keep, refine, or defer

| Baseline | Recommendation | Why / acceptance impact |
| --- | --- | --- |
| Qdrant Edge + local embeddings + SQLite | Keep | Matches PS03 and makes offline operation practical |
| Vector, graph, and temporal separation | Keep; use one canonical record identity | Avoid duplicate truth across representations |
| Numerous conceptual components | Implement as modules in a modular monolith | Fewer services, credentials, deployment paths, and failure modes |
| Privacy firewall appears late in roadmap | Move security foundation before persistent ingestion and networking | Sensitive handling must shape storage and APIs from the start |
| `SENSITIVE` text redacted and shared globally | Default to local; allow only explicitly approved, narrow export types | Regex detection and identifier removal are insufficient release criteria |
| Embeddings described as non-reversible in `SECURITY.md` | Treat vectors, sparse terms, graphs, and query text as sensitive derivatives | Do not base confidentiality on a representation being unreadable to humans |
| Qdrant + SQLite writes described together | SQLite transaction + durable projection jobs | No assumed atomic transaction spans both engines |
| Deterministic IDs described as making retries harmless | Random stable record IDs + immutable revision IDs + operation deduplication | Same-ID upserts alone do not prevent stale or reordered overwrites |
| Timestamp/version comparisons for multi-device edits | Parent revision ancestry + conditional updates + explicit branch conflicts | Clocks and independent integer counters do not establish causality |
| Direct edge upserts to central Qdrant | Authenticated application sync gateway in front of Qdrant | Enforce device scope, field allowlists, policy versions, idempotency, and audit |
| Snapshots serving multiple data scopes | Public/reference snapshots first; dedicated authorized partitions for any internal data | A download contains a whole shard's data; query filters cannot protect an overbroad snapshot |
| Automatic cloud query fallback | Local search by default; defer cloud queries | Low retrieval confidence must not send a sensitive query outward |
| Hashes advertised as tamper evidence | Authenticate event chains and retain independent checkpoints | A local attacker can rewrite both content and an unkeyed hash |
| LUKS-centric encryption | macOS-specific key/storage design plus a separate Linux profile | LUKS is not the native storage control on this Mac |
| Sub-millisecond search and fixed RAM promises | Treat as hypotheses; separate vector time from full query latency | Embedding, filtering, I/O, UI, and hardware affect actual performance |
| Comprehensive graph/LLM/consolidation features early | Small graph/timeline first, optional generation later | Deliver reliable core behavior before increasing attack surface |

Specific contract inconsistencies to fix during implementation planning: OpenAPI has no declared authentication scheme; its ingestion shape includes `patient_id` absent from the strict memory JSON schema; prose/source enums differ; local-only records default to `PENDING`; conflict states described in prose are not fully represented in lifecycle enums. The supplied OpenAPI does not specify the described WebSocket behavior. Do not generate clients from these contracts unchanged.

## 5. Proposed system boundaries

```text
Local browser UI (bundled assets, authenticated session)
       |
       v
Local FastAPI application: authorization, validation, policy, retrieval
       |
       +--> encrypted SQLite: canonical records, revisions, graph, events,
       |                      policy decisions, projection jobs, sync outbox
       |
       +--> local embedding workers --> Qdrant Edge private shard
       |                               Qdrant Edge shared-reference shard
       |
       +--> export policy --> allowlisted export DTO --> durable outbox
                                      |
                             sole sync transport, mTLS
                                      |
                           Central application gateway
                             |                   |
                       SQL revision log     Qdrant Server
                       and dedup ledger     derived vector index
                                      |
                      authorized changes / signed reference snapshots
                                      |
                       verify, stage, validate, activate on edge
```

These are proposed boundaries, not implemented infrastructure. The local API owns every data access; the browser never gets a Qdrant credential. The central gateway uses a separate runtime profile of the same backend codebase. A small central SQL database is sufficient for the local demo's revision log and deduplication; it must not share the edge database.

### Stack and process choices

- **Backend:** Python 3.11+ target, FastAPI/Pydantic, one process owning each Edge shard. Pin exact compatible versions after the initial spike; do not assume multiple Uvicorn workers can safely share a shard directory.
- **Canonical persistence:** SQLCipher-compatible SQLite driver, migrations, foreign keys, bounded transactions, WAL behavior verified under encryption. Failure to open encrypted storage must stop startup, never silently fall back to plaintext.
- **Vector engine:** actual `qdrant-edge-py` using `qdrant_edge` bindings behind a small adapter. Do not substitute `QdrantClient(path=...)` or a local Qdrant Server and label it Edge.
- **Embeddings:** FastEmbed/ONNX, initially `BAAI/bge-small-en-v1.5` if verified compatible. Version model weights, tokenizer, dimensions, normalization, and sparse configuration. Cache all required assets before the offline demo.
- **Frontend:** React/TypeScript/Vite; exact supported versions locked at implementation time. Serve the built frontend from the local backend origin. Use authenticated polling initially; streaming is optional and must preserve the same access checks.
- **Central demo:** real Qdrant Server in an isolated container network plus the gateway; no direct public Qdrant ports. Pin a tested server/Edge compatibility pair.
- **Crypto:** maintained libraries and OS key storage only; no custom cipher or homegrown certificate protocol.

### Authoritative data versus projections

SQLite owns record content, revision ancestry, access scope, privacy state, graph provenance, and deletion state. Qdrant holds derived vectors with minimal payload: opaque record/revision IDs, scope markers required for filtering, model version, and index metadata. It need not duplicate raw note text.

All final search results are authorized and checked against current SQLite state after vector lookup. Stale/deleted/reclassified index entries must not reveal content. Over-fetch with a bounded limit when needed, and do not expose unauthorized candidate counts or snippets.

## 6. Security requirements and threat model

### Assets and trust boundaries

Protect raw observations, identifiers, query text, embeddings, sparse tokens, graph links, event journals, sync queues, model inputs, local browser state, backups, temporary files, and keys. Threats include a lost device, another local user, a malicious website contacting localhost, malformed imports, replayed sync operations, a revoked device, an overbroad snapshot, dependency compromise, and accidental developer logging.

Encryption cannot protect data from an attacker already controlling the unlocked application or its OS user. State this limit in operational documentation; do not claim local-only storage makes a compromised machine safe.

### Mandatory invariants

1. No raw patient note, private vector, private sparse representation, or patient-scoped query leaves the edge by default.
2. Privacy classification and destination authorization are hard gates. A high relevance score, user-supplied label, or forced sync button cannot override them.
3. Only the sync transport may initiate configured central-service traffic at runtime. Downloads for installation are a separate explicit setup activity.
4. Every read, search, graph traversal, mutation, export, and sync operation derives scope from authenticated identity, never solely from a supplied `patient_id` or `facility_id`.
5. A record is acknowledged as locally saved only after canonical commit. Index and sync status are separately visible.
6. A retry cannot duplicate an accepted logical operation, overwrite a newer revision, or resurrect a deletion.
7. Storage errors, missing keys, invalid certificates, policy errors, and incompatible schemas fail closed for the affected operation.
8. Logs and UI activity streams contain allowlisted operational metadata, not raw payloads, query text, secrets, or patient names.
9. Conflict review and archival never silently erase evidence. Retention is distinct from relevance scoring.
10. Development/demo fixtures are synthetic; this plan is not authorization to import existing personal or clinical files.

### Controls and proof

| Risk | Planned control | Required negative test |
| --- | --- | --- |
| Stolen disk / backup | Encrypted DB and complete data volume; keys separate from data | Database, vectors, queue, WAL, temp files, and backup cannot be read while locked |
| Malicious localhost request | Loopback binding, exact Host/Origin allowlists, authenticated session, CSRF protection, strict CORS | Foreign origin, DNS-rebinding-style Host, missing session, and invalid CSRF fail |
| Cross-scope access | Server-side authorization on every path including graph and status | Operator A cannot retrieve B's record by UUID, search, graph, counts, or sync |
| Accidental export | Strict export DTO, destination allowlist, dual policy checks, explicit permissions | Raw text, unknown fields, private vectors, and forged PUBLIC labels are rejected |
| Network interception | Server verification and per-device mTLS for synchronization | Wrong CA, expired/revoked client cert, or unexpected destination is rejected |
| Replay / stale write | Durable operation IDs, signed envelopes, ancestry checks, dedup ledger | Duplicate, reordered, altered, and reused-ID/different-body requests do not overwrite |
| Malicious snapshot | Scope-bound signed manifest, hashes, monotonic generation, staged activation | Bad signature, wrong scope, rollback, oversized archive, and interrupted swap preserve current data |
| Poisoned import / prompt injection | Small bounded formats, schema validation, inert text rendering, no execution/tools | HTML/script and instruction-like text remain data and cannot change policy |
| Resource exhaustion | Size limits, worker concurrency caps, disk reserve, retry bounds | Large import, full disk, and unavailable central node do not freeze local search |
| Audit rewriting | HMAC/signature chain with independent checkpoints where available | Modified or missing middle events fail verification; document suffix-truncation limit offline |
| Supply-chain mistake | Locked versions/hashes, vetted model source, vulnerability and secret scans | Known unacceptable findings block release; no remote code execution from model metadata |

### Local identity and browser session

Provision a local operator during setup using a maintained password-hashing library (Argon2id) and no default password. Use short-lived opaque server-side sessions in HttpOnly cookies, logout/revocation, idle lock, CSRF tokens for mutations, and rate-limited login. Keep tokens out of URLs and browser localStorage. Operator permissions cover ingestion and review; device provisioning, policy changes, and exports require an explicit admin capability.

For the local browser connection, use loopback-only HTTP as a documented development exception, with no LAN exposure and with Host/Origin/session/CSRF protections. Do not call it encrypted transport. A LAN or remote UI profile requires TLS and an independently reviewed authentication configuration; Secure cookies are mandatory there. The production UI should have CSP, no remote CDN scripts/fonts, escaped text, no sensitive API caching, and no patient data in service-worker caches.

### Key and storage lifecycle

- Generate random per-device database and signing keys during future setup; store/retrieve them through macOS Keychain using least necessary application access. Keychain use alone is not a claim of hardware-backed keys.
- Protect Qdrant directories, SQLite/WAL, staging directories, and backups with an encrypted APFS volume or encrypted disk image in the secure profile; verify the actual storage setup. FileVault is useful host protection but is not proof of application-level locking. Use SQLCipher for canonical DB protection as well.
- On Linux, use a separately verified encrypted-volume/key-store arrangement; do not copy macOS-specific setup blindly.
- Use owner-only directory/file permissions. No keys in Git, environment example files, logs, shell arguments, sync payloads, or the database backup being protected.
- Lock closes storage handles and stops workers; document that reliable removal of every secret copy from a high-level runtime's memory is not guaranteed.
- Specify database rekey, signing-key rotation, certificate renewal, and dual-key transition tests before enabling rotation controls.
- Provide an explicit recovery choice: separately stored encrypted recovery material or accepted unrecoverability. Key loss must never trigger an unencrypted reset over existing data.
- Revocation blocks future sync centrally. It cannot remotely erase an offline copy. Retention, device loss, and backup recovery need an operational procedure before any real-data rollout.

## 7. Privacy and data lifecycle

### Default release policy

| Class | Local handling | Export policy |
| --- | --- | --- |
| PUBLIC reference material | Local searchable cache with source/version | Eligible if source and destination are approved |
| INTERNAL operational data | Facility-scoped storage and access | Eligible only for strict non-patient DTOs and the same authorized facility |
| SENSITIVE patient observations | Encrypted, local-only by default | Block in initial product; redaction alone does not grant release |
| HIGHLY_SENSITIVE observations | Encrypted, hard-pinned local | Block; governor cannot override |
| Unknown / failed classification | Treat as sensitive | Block and record reason |
| Synthetic sharing fixtures | Dedicated demo namespace and explicit synthetic marker | Only allowlisted fixture types, never a bypass for arbitrary uploaded text |

Use a separate release decision (`LOCAL_ONLY`, `ELIGIBLE`, `BLOCKED`, `REVOKED`) rather than equating sensitivity with queue state. PUBLIC is assigned by trusted import policy, not accepted as a self-declared permission from a note creation request.

### Export transformation

1. Authorize the operator/device and destination; check record ancestry, retention, and latest policy.
2. Build a new export object from an allowlist of fields. Do not serialize the canonical record and delete a few fields afterward.
3. If approved shared text needs vectors, generate embeddings from that approved representation locally. Never attach the original private embedding to sanitized text.
4. Give the export its own opaque ID, schema/model/policy versions, destination scope, and signed content digest. Keep links to private provenance local unless explicitly allowed.
5. Commit the approved payload and decision atomically into the encrypted outbox.
6. Re-check policy and revocation immediately before sending. Cancel/rebuild stale exports. The central gateway independently checks schema, identity, scope, and policy version.

Do not describe pseudonyms, hashes of names, or redacted free text as anonymous. Any future sharing of real derived patient data requires a separate release-policy and data-use review; it is not part of this implementation plan.

### Retention, archive, and deletion

The governor may recommend archival or cache eviction. It must not delete source observations because their search relevance decayed. Pin critical and conflicted records; cap/normalize recurrence and access signals before applying weights. Keep rule versions and reason codes so decisions can be reproduced.

Deletion creates an authorized tombstone and removes the record from reads immediately. Then purge or rebuild vector/graph/search projections, cancel queued exports, and propagate revocation/deletion for previously shared objects. Snapshots and backups have explicit retention and replay rules. Restore must apply current tombstones before exposing data. Do not promise immediate physical erasure from SSDs or old backups; show pending retention work accurately.

## 8. Data model and API contract plan

### Canonical entities

| Entity/table | Minimum responsibilities |
| --- | --- |
| `operators`, `sessions`, `devices` | Local auth, roles, facility scope, opaque device IDs, key/cert references, revocation |
| `memories` | Stable random UUID, subject/facility scope, current revision reference, sensitivity, retention, tombstone |
| `memory_revisions` | Immutable revision UUID, parent revision IDs, author/device, content, observed/recorded times, schema version |
| `entities`, `relations` | Scoped graph facts, supporting revision IDs, relation type and review status |
| `events` | Append-only domain transitions and provenance; access-controlled sensitive details where needed |
| `policy_decisions` | Rule version, input revision, decision, reasons, destination, expiry/re-evaluation state |
| `projection_jobs` | Revision/model version, desired upsert/delete, leased state, retry and error metadata |
| `sync_outbox` | Immutable operation ID, approved DTO, destination, policy version, hash, lease/retry/ack state |
| `sync_inbox` | Received operation IDs/digests, application status and deduplication |
| `conflicts` | Common ancestor, branch revisions, conflict kind, reviewer and resolving revision |
| `audit_events` | Minimal security metadata, chained authentication, checkpoint references |
| `snapshot_generations` | Authorized scope, generation, content hashes, signer, model/schema compatibility, active path |

Keep identifiers random and opaque; do not use a hardware MAC or a hash of patient content as an externally visible identity. Human-readable fixture IDs may exist in synthetic labels only. UTC timestamps support presentation and provenance; revision ancestry drives merge logic.

### State separation

- **Record:** active, archived, tombstoned; conflict/review status is separate.
- **Index:** pending, indexed, failed; track indexed revision and model version.
- **Release:** local-only, eligible, blocked, revoked.
- **Delivery:** not-applicable, pending, in-flight, acknowledged, retry-wait, failed, cancelled.
- **Connectivity:** offline, degraded, online; derived from the configured central endpoint, not generic Internet probes.

### Local and central API responsibilities

- Preserve useful `/api/memories`, `/api/search`, `/api/graph`, `/api/sync/status`, and governance routes, but specify typed request/response/error schemas and authorization first.
- Add session/login/logout, revision creation with expected parent or `If-Match`, conflict inspection/resolution, timeline, and explicit archive/delete operations.
- Use bounded pagination, query length, import size, graph depth and result counts. Validate unknown fields, enum values, vector dimensions, finite numbers, and IDs.
- Return canonical revision and index state on create; return a clear conflict response for concurrent updates. Do not show a successful save before commit.
- Search responses include matched source/revision, vector/keyword contribution, time, source freshness, and conflict flags. Retrieval scores are not clinical confidence.
- Sync APIs accept signed, allowlisted operations and return per-operation durable receipts. Snapshot/changes endpoints derive accessible scope from device identity.
- Specify 401/403/404 behavior consistently, 409 for revision conflicts, 413/422 for invalid input, and safe retry semantics. Do not return raw exceptions.
- Make one set of backend models the contract source, generate OpenAPI/frontend types, and test contract compatibility. Any event stream gets its own documented schema and auth rules.

## 9. Consistency, retrieval, and synchronization algorithms

### Local save and recovery

1. Validate and authorize input; assign server-controlled identity, scope, privacy defaults, and revision ancestry.
2. In one encrypted SQLite transaction, write the revision, domain event, derived-work intent, and projection job. Commit, then acknowledge save.
3. A bounded worker generates dense/sparse representations locally and idempotently updates Qdrant Edge. Mark that exact revision indexed only after success.
4. After a crash, recover leased jobs and replay unfinished work. A reconciliation pass compares revision/model metadata and repairs missing or stale vectors. SQLite remains the source for reconstruction.
5. Graph and timeline projections carry supporting revision IDs. They can be rebuilt; they never independently authorize access.
6. If a policy decision later makes an export eligible, insert the decision and sanitized outbox payload together in a new transaction. Never attempt a distributed transaction between SQLite and Qdrant.

Use one owner per shard; bound worker concurrency and avoid CPU-heavy embedding on the API event loop. Migration startup takes a lock and checks available disk space. Test backups using a consistent database backup mechanism, not a blind copy of a live main DB file without its journal.

### Search and memory intelligence

1. Authenticate and compute permitted scope.
2. Embed query locally; run dense and sparse/BM25 retrieval against the appropriate local shards.
3. Fuse ranks, deduplicate by canonical record/revision, and validate candidates against current authorized state.
4. Attach small bounded graph neighborhoods, source provenance, and timeline context. Show contradictions explicitly rather than suppressing evidence.
5. Return evidence and uncertainty; abstain from unsupported diagnostic or treatment conclusions.

Graph extraction begins with structured synthetic fields and explicit relation types. Semantic similarity may suggest a review candidate but must not autonomously declare a medical contradiction. Contradiction checks consider subject, attribute, time interval, units, polarity, and revision history. Local generation, if later added, receives read-only evidence with no tools, network, or permission to alter policies.

### Outbound synchronization

- At-least-once delivery with idempotent application, not a claim of exactly-once transport.
- Claim bounded batches with leases. Retry transient errors with capped exponential backoff and jitter. Do not retry permanent schema/auth failures forever; expose intervention status.
- Sign a canonical envelope containing operation ID, revision, destination scope, schema/policy versions, and payload digest. mTLS authenticates the sending device; signing supports provenance and replay checks.
- Gateway checks revocation, authorization, envelope/schema, and duplicate digest. Reusing an operation ID with a different body is an error.
- Central SQL commits the immutable event and dedup result before acknowledging durable acceptance. Qdrant Server projection follows through its own job queue. Expose `accepted` and `indexed` separately; a generic HTTP 200 is not sufficient evidence of completed replication.
- On lost acknowledgment, repeat the identical operation; the server returns the prior receipt. Preserve client outbox state across restarts.

### Inbound synchronization and conflicts

- Initially use an authorized cursor-based change feed for shared records and associated graph/event metadata. Raw Qdrant snapshots alone cannot synchronize all SQLite state.
- Atomically apply received domain changes and inbox dedup markers locally, then update vector projections. Advance the cursor only for durably applied changes; retries are safe.
- Fast-forward only when revision ancestry establishes that the incoming revision descends from the known base with no competing local branch.
- Concurrent same-record changes retain both branches and create a review task. Independent observations merge additively. A later timestamp or higher local counter does not choose a winner.
- Resolution records reviewer identity, reasons, and both parent revisions. It is a new revision; it does not erase the alternatives.
- Tombstones outrank older replayed state. Central and edge retention must preserve sufficient deletion history; devices older than the retained cursor watermark require a fresh authorized baseline before replaying pending work.

### Snapshot stage (after operation sync works)

Keep private mutable memory separate from shared reference shards. Never export the private shard as a shortcut to indexing. Start snapshots with PUBLIC reference data only. INTERNAL snapshots require physically separated authorized partitions; filtering search queries is not a substitute.

The gateway authorizes a manifest containing scope, generation, schema/model versions, content hashes, size limits, and trusted signer. Download into protected staging, verify before parsing, constrain archive expansion/path traversal, validate data, and activate a new generation atomically. Keep the previous good generation for rollback of interrupted activation, without permitting downgrade to a revoked generation. A partial update is applied to a staging copy, not blindly to the live private shard. Schedule metadata hydration and activation together so graph/source context cannot refer to a mismatched generation.

Qdrant-specific method names and server endpoints must be verified against pinned packages in the spike. Full authorized snapshot refresh is an explicit interim fallback if delta compatibility fails; do not claim differential replication until changed-segment behavior is measured.

## 10. User interface plan

Keep product language understandable: saved locally, waiting to index, local only, sharing blocked, pending sync, received centrally, conflict needs review. Avoid exposing implementation jargon in the main workflow.

| View | Essential behavior |
| --- | --- |
| Overview | Connectivity, local readiness, queue counts, failed work, data protection status |
| Memory explorer | Filtered records, privacy label, revision, provenance, retention and sync status |
| Search | Offline-capable semantic/hybrid search, evidence, keyword match explanation, stale/conflict indicators |
| Record inspector | Source, revision history, related facts, timeline, policy reason, proposed export preview |
| Sync monitor | Sanitized operation preview, blocked reasons, retries, receipt/index status, last successful update |
| Conflict review | Side-by-side branches, common ancestor, explicit resolution and audit |
| Memory Lab | Synthetic-only fixture controls, pause transport, replay/reconnect demonstration, governor simulation |

All assets are local. Data panels clear on logout/lock. A UI network toggle only controls transport behavior; it is not proof of physical network isolation. The demo also includes a genuine blocked-network test. Avoid one-click export of all records; show scope and exact approved representation before an export action.

## 11. Implementation sequence and gates

No phase below is executed by preparing this document. After the user requests implementation, work in this order and retain evidence for each gate.

| Phase | Deliverables | Exit gate / dependency |
| --- | --- | --- |
| 0. Confirm decisions | Approve/refine section 4, define development and presentation machines, choose secure storage/recovery profile, settle scope | No unresolved decision affecting first data write or egress |
| 1. Compatibility spike | Real Edge on Mac; local embeddings; dense/sparse search; restart/delete; encrypted SQLite driver; server pairing and snapshot probe | Record exact versions and measured behavior; no substituted Edge engine |
| 2. Security foundation | Local identity/session, scope checks, encryption/key handling, strict models, safe logging, egress policy, initial negative tests | Unauthorized reads fail; missing key/plaintext fallback blocked; private data cannot export |
| 3. Durable local vertical slice | Ingest/revise/archive, revision log, projection jobs, local search and minimal UI | Save/restart/search works offline; crash between DB/index writes repairs safely |
| 4. Memory intelligence | Hybrid ranking, simple graph/timeline, explainable governor, retention protections, local conflict review | Known search fixtures succeed; critical/conflicted records protected; policy dominates score |
| 5. Secure synchronization | Separate central gateway/SQL/Qdrant, mTLS identities, sanitized outbox/inbox, cursors, retries, two device profiles | Disconnect/restart/retry converges; private canaries absent from all outbound representations |
| 6. Inbound hardening | Signed reference snapshots, staging/activation, revocation/tombstones, conflict and restore tests | Bad/stale/wrong-scope updates rejected; no resurrection or loss of private data |
| 7. Product and optional features | Complete inspectors/Memory Lab, bounded Cytoscape, provenance-preserving consolidation, partial snapshots if supported | User can explain an end-to-end event; deferred repository gates clearly marked |
| 8. Release/demo evidence | Reproducible setup, synthetic fixture reset, benchmarks, security regression run, dependency review, demo script | Section 12 passes; no unsupported claims in presentation |

The first usable milestone is phase 3. The PS03-complete workflow requires phases 4-6 plus the essential interface and release checks. Rich graph animation or LLM text can be cut if time is short. Authentication, encrypted handling, real offline retrieval, privacy policy, durable sync, and conflict correctness cannot be replaced with mock success states.

### Suggested future repository layout

```text
lex-local-ps3/
  project-planning.md
  backend/
    app/{api,auth,domain,storage,retrieval,policy,sync,workers,observability}/
    migrations/
    tests/{unit,integration,security,offline,sync,performance}/
  frontend/src/{views,components,api}/
  contracts/
  fixtures/synthetic/
  infra/local-central/
  scripts/
  docs/{decisions,threat-model,runbooks,benchmarks}/
```

This tree is a proposal only; the planning task creates no scaffold. Runtime records, vectors, secrets, model caches, and backups belong in configured application data locations outside tracked source. Each simulated device gets a different root. Commit only synthetic fixtures and secret-free examples.

## 12. Verification and acceptance plan

Tests below are future acceptance requirements, not tests already run.

### Security and correctness release blockers

1. Fresh offline start after explicit provisioning: no external fonts, embeddings, telemetry, DNS probes, or cloud dependencies; ingest/search/restart remain functional.
2. Inject recognizable synthetic private canaries into text, metadata, query text, graph links, and input fields. Inspect queue DTOs, decoded requests at the authorized test receiver, central stores, snapshots, logs, browser storage, and backups. No prohibited representation crosses its boundary. Packet counts alone cannot prove that encrypted traffic is safe.
3. Test forbidden access through every route, direct UUID lookup, graph traversal, filtered search, aggregate counts, and sync. Client-supplied facility/role/privacy labels cannot elevate privilege.
4. Test lock/unlock, wrong/lost keys, unavailable Keychain, WAL/journal encryption, vector-volume protection, backup restore, and accidental plaintext configuration.
5. Crash after canonical commit, during vector indexing, after central acceptance before local acknowledgment, and during snapshot activation. Recover without lost canonical records or duplicate logical operations.
6. Test duplicate/reordered/replayed operations, ID reuse with altered content, different same-parent edits, clock skew, stale schema/model versions, and deletion replay after a long offline period.
7. Test bad/revoked certificates, wrong device scope, bad signatures, wrong-scope snapshots, rollback generations, oversized/traversal archives, and interrupted downloads.
8. Test policy change after enqueue, source deletion before send, and revocation after sharing. Queued work is cancelled/rebuilt; received historical copies follow explicit retention rules.
9. Test import limits, disk-full behavior, slow embedding, network flapping, central outage, worker lease recovery, and long-running queue backpressure. Local search remains available where storage is healthy.
10. Test script/HTML injection, prompt-like instructions in data, safe error responses, log redaction, no secret-bearing URLs, and dependency/secret scanning.
11. Test backup consistency and restoration to a compatible schema; current tombstones and access policy are applied before data is exposed.

### Retrieval and performance evidence

Use versioned synthetic fixtures: at least 1,000 records for the initial spike and 10,000 for the demo benchmark if hardware permits. Include paraphrases, exact drug/term codes, negations, stale facts, ambiguous notes, and contradictory structured observations. Use a held-out set of at least 30 reviewed queries with expected relevant sources; report Recall@5 or equivalent retrieval quality by query type. Do not describe similarity as diagnostic accuracy.

Initial engineering targets, to confirm or revise after measurement:

- Warm end-to-end local search p95 at or below 300 ms on the declared 10,000-record workload, excluding optional generation; report vector lookup and query embedding separately.
- Durable save acknowledgment p95 at or below 250 ms for a small note, with index readiness measured independently.
- Backend plus embedding/index workers peak RSS target below 1 GB for that workload; report browser, central container, disk, and model cache separately.
- Record cold-start duration, first-query latency, queue drain rate, full/delta bytes, disk growth, and behavior under memory pressure. Do not invent a throughput commitment before the spike.
- Zero unauthorized disclosure, lost acknowledged canonical records, or silent conflict overwrites in the deterministic acceptance suite.

The repository's `<1 ms`/`<5 ms` statements and `<450 MB` acceptance criterion are not adopted as verified results. These proposed broader budgets require a recorded architecture decision if accepted. Measure on macOS and the target Linux laptop separately, with hardware, versions, corpus, cache state, concurrency, and sample counts disclosed.

### Definition of done

Every PS03 row in section 3 has executable evidence; the actual Edge library is identifiable; offline functionality is independent of central availability; security gates pass; conflicts and sync states are inspectable; setup/recovery instructions reproduce the result; and deferred baseline features are explicitly labelled incomplete. Synthetic-data success is not evidence of readiness for real clinical use.

## 13. Demo narrative

1. Show two clean synthetic device profiles and a local central node, with versions and data scopes visible.
2. Load an approved reference bundle and search locally.
3. Block external connectivity. Add a private synthetic note and perform dense plus exact-term hybrid search; restart and repeat.
4. Inspect the note's local-only decision, protected storage status, provenance, and empty outbound representation.
5. Create an approved shareable synthetic reference revision. Show its exact export DTO and pending queue state.
6. Reconnect, interrupt after central acceptance, then retry. Show one logical revision centrally and on device B.
7. Introduce two conflicting revisions to a shareable demo record; show both branches and a new human-reviewed resolution. Separately show a local clinical contradiction without exporting patient notes.
8. Attempt a wrong-scope or tampered update. Show rejection and continued local operation.
9. Show deletion/revocation behavior, measured retrieval timings, and the requirement-to-test checklist.

Call the local central service a central-node simulator; do not imply data was hosted remotely. If partial snapshots or optional consolidation are unfinished, say so directly.

## 14. Open decisions and risk register

| Decision / risk | Proposed default | When it must be settled |
| --- | --- | --- |
| Architecture refinements accepted? | Keep existing core; adopt section 4 security/consistency changes | Before implementation begins |
| Development vs. demo hardware | Native Apple Silicon development; separate Linux benchmark if required | Phase 0/1 |
| Available memory / dependency compatibility | Measure; do not import Linux budget assumptions | Phase 1 |
| Data permitted in prototype | Synthetic only | Before any import capability |
| Encryption and recovery arrangement | SQLCipher + protected data volume + Keychain; explicit recovery choice | Before persistent ingestion |
| Scope of shared records | Approved reference/operational DTOs; patient notes local-only | Before outbox design is finalized |
| Need for remote hosting | None for first complete local demonstration | Only on a later deployment request |
| Qdrant beta API/snapshot changes | Pin and test an adapter; retain operation-level sync | Phase 1 and snapshot phase |
| Raw private shard cannot use central indexing | Benchmark local private-search capacity; cap workload honestly | Phase 1/4; never upload private vectors to meet latency |
| Offline revocation limits | Local expiry/lock and central revocation on reconnect; disclose limits | Security design and operational runbook |
| Backup/deletion tension | Tombstone-aware restore and explicit backup retention | Before backup/export features |
| Schedule/team capacity | Estimate after first compatibility evidence | Before committing to calendar dates |

No answer to these questions is needed to save this planning document. Keep unresolved choices visible to the next model; do not invent user approval or silently weaken a security requirement when a dependency is inconvenient.

## 15. Handoff to the coding model

When the user later requests execution:

1. Read this plan and the user's latest instructions. Inspect the current folder and applicable local project instructions before changing files. Preserve the plan.
2. Resolve only decisions that affect the requested implementation slice. Work within the scope the user authorizes; this document by itself is not a request to execute all phases.
3. If broad implementation is requested, start with phase 0 decisions and the phase 1 compatibility spike. Verify exact library APIs, encryption support, offline model assets, and native architecture before scaffolding the full product.
4. Record versions, measurements, failures, and architecture decisions. Treat repository prose and example pseudocode as design references, not proof of working APIs.
5. Implement the security foundation and durable local vertical slice before synchronization. Add meaningful failure-path tests alongside each boundary.
6. Keep all data synthetic and networking limited to explicitly configured test destinations. Do not deploy, upload user data, or enable cloud fallbacks by implication.
7. After each phase, report what works, what was tested, what remains incomplete, and any proposed deviation. Never fabricate passing tests, offline guarantees, or security certification.

**Suggested first future instruction:** "Read project-planning.md, confirm the architecture decisions that affect the first slice, and implement only the compatibility spike using synthetic data. Record exact versions and results before proceeding."

## 16. References and review limits

- User-supplied source: `~/Downloads/problem_explanation_piovxkhlbtb.pdf`, page 1; visually reviewed in full because text extraction returned no text.
- [Pinned architecture baseline](https://github.com/shubhrgunjan/edgemed/tree/595229864c3b3ff2b372b4037f873c20d6e7296c).
- [Project status](https://github.com/shubhrgunjan/edgemed/blob/595229864c3b3ff2b372b4037f873c20d6e7296c/docs/PROJECT_STATUS.md), [system architecture](https://github.com/shubhrgunjan/edgemed/blob/595229864c3b3ff2b372b4037f873c20d6e7296c/docs/02-architecture/system-architecture.md), and [technology decisions](https://github.com/shubhrgunjan/edgemed/blob/595229864c3b3ff2b372b4037f873c20d6e7296c/docs/research/technology-decisions.md).
- [Security policy](https://github.com/shubhrgunjan/edgemed/blob/595229864c3b3ff2b372b4037f873c20d6e7296c/SECURITY.md), [security architecture](https://github.com/shubhrgunjan/edgemed/blob/595229864c3b3ff2b372b4037f873c20d6e7296c/docs/02-architecture/security-architecture.md), and [privacy firewall](https://github.com/shubhrgunjan/edgemed/blob/595229864c3b3ff2b372b4037f873c20d6e7296c/docs/04-intelligence/privacy-firewall.md).
- [Sync architecture](https://github.com/shubhrgunjan/edgemed/blob/595229864c3b3ff2b372b4037f873c20d6e7296c/docs/02-architecture/sync-architecture.md), [conflict resolution](https://github.com/shubhrgunjan/edgemed/blob/595229864c3b3ff2b372b4037f873c20d6e7296c/docs/05-synchronization/conflict-resolution.md), [memory governor](https://github.com/shubhrgunjan/edgemed/blob/595229864c3b3ff2b372b4037f873c20d6e7296c/docs/04-intelligence/memory-governor.md), and [query routing](https://github.com/shubhrgunjan/edgemed/blob/595229864c3b3ff2b372b4037f873c20d6e7296c/docs/04-intelligence/query-routing.md).
- [Memory schema](https://github.com/shubhrgunjan/edgemed/blob/595229864c3b3ff2b372b4037f873c20d6e7296c/schemas/memory.schema.json), [OpenAPI](https://github.com/shubhrgunjan/edgemed/blob/595229864c3b3ff2b372b4037f873c20d6e7296c/api/openapi/openapi.yaml), and [existing acceptance criteria](https://github.com/shubhrgunjan/edgemed/blob/595229864c3b3ff2b372b4037f873c20d6e7296c/docs/01-requirements/acceptance-criteria.md).
- Official implementation references: [Edge overview](https://qdrant.tech/documentation/edge/), [quickstart](https://qdrant.tech/documentation/edge/edge-quickstart/), [sync patterns](https://qdrant.tech/documentation/edge/edge-data-synchronization-patterns/), and [Python package](https://pypi.org/project/qdrant-edge-py/), consulted 27 September 2026.

Review scope: the problem statement, repository tree and selected architecture/security/contracts/acceptance documents, plus relevant official Qdrant references. This was a planning review, not a comprehensive security audit, dependency audit, implementation test, clinical validation, or legal compliance assessment. Proposed controls and budgets above remain unimplemented and unverified until their stated gates pass.
