# EdgeMed — next-phase engineering plan

Prepared 28 September 2026. Planning only; implementation requires the user's next explicit command.

Reviewed project: `~/Projects/lex-local-ps3`, branch `codex/local-edgemed-prototype`, commit `c813223327266a79ecdb9538563c0ef44e1728b2`. The working tree was clean when inspected. This document is deliberately outside the repository. No application code, dependencies, runtime records, repository files, or remote branches have been changed for this planning task.

The leader's prompt is input to the plan, not authorization to execute it. The user's latest constraint is **1–2 days**, with a possible group. The available slower device has **Snapdragon 720G and 8 GB RAM**, assumed to be an Android phone/tablet until its model and OS are confirmed. This is not interchangeable with an ARM Linux mini-PC. All targets below are proposed acceptance budgets, not newly measured results. Estimates are engineering hours including focused verification, not guaranteed elapsed delivery times.

## 1. Decision and scope

Keep Python/FastAPI, SQLCipher as the authority, embedded Qdrant Edge, local FastEmbed/ONNX, and React. Keep private observations local. Keep the central gateway and Qdrant Server for approved synthetic reference synchronization. Do not rewrite the stack or add a hosted service.

The next release should tell one reliable story: capture and search on a device while disconnected; show which information stays private; queue approved shared-reference edits; reconnect; receive them on another device; detect and explicitly resolve a conflict. Make status honest and keep user actions responsive while indexing and synchronization run.

The sequence is correctness and security fixes, baseline instrumentation, narrowly justified optimization, usable demo flow, then rehearsal. Profiling can begin before fixes to preserve a baseline, but optimizations must land after correctness tests define the intended behavior.

The ≤5 ms target is a **warm search experiment**. Report separately whether it applies to dense retrieval alone, hybrid retrieval with a precomputed query vector, the complete backend query including embedding, or an exact-repeat cache hit. A claim about complete search must include embedding and canonical authorization. Do not put a retrieval-only number in front of judges as end-to-end application latency.

### Deadline variants

| Available time/team | Deliverable commitment |
|---|---|
| One day, one engineer | Approximately 10–15 hours of selected work: session/data-clearing fix, deletion race fix, basic timing instrumentation, truthful connectivity and sharing labels, one complete offline/conflict rehearsal. Publish the measured result even if no meaningful speedup lands. Defer full benchmark matrix and hardware port. |
| Two days, one engineer | Approximately 16–24 hours of prioritized work: the above, one measured retrieval improvement, focused regression tests, setup preflight, slower-device smoke test if already compatible. Defer broad UI restructuring and platform work. |
| Two days, 2–3 contributors | Target the full P0 package below, about 24–40 total engineering hours plus contingency. Assign backend/correctness, UI/demo, and hardware/verification ownership. Agree contracts before simultaneous edits. |

Reserve the final 3–4 elapsed hours for integrated testing and rehearsal. Stop feature work before that window. If the deadline is one day, defer optimization before deferring privacy or correctness. A full cross-platform security implementation is not a credible 1–2 day commitment.

## 2. Current architecture assessment

### Evidence and boundaries

The assessment is based on source inspection and the existing test/benchmark artifacts, not a new runtime profiling session. Existing reports record 32 passing backend tests, Ruff and production frontend build success, eight earlier live integration checks, a successful signed full snapshot import, and two earlier browser tests. The final browser refinements were not covered by another browser run. This planning pass did not rerun tests that create databases or mutate synthetic demo state.

| Area | Current implementation | Assessment |
|---|---|---|
| Local authority | `edgemed/store.py`: encrypted SQLite records, immutable revisions, current heads, jobs, inbox/outbox, audit events | Keep. Transactions make record creation and indexing/export intent durable. Add small, explicit schema migrations for any new fields. |
| Retrieval | `edgemed/retrieval.py`: one model per Retrieval instance, embedded Edge shard, optional imported reference shard, Python BM25 and RRF | No remote vector request on the normal local search path. Repeated per-query model initialization is not evident. Main avoidable work is canonical hydration, keyword computation, and contention. |
| API | `edgemed/api.py`: synchronous endpoints executed through the framework's worker pool, authenticated session middleware, background indexing/sync | Changing `def` to `async def` would not make CPU inference faster and could block the event loop. Keep blocking operations off that loop. |
| UI | `frontend/src/main.tsx`: one large component, full refresh every three seconds | Functional but excessive polling, fragile detail selection, and ambiguous connectivity. Refactor only the parts needed for correctness and demo flow. |
| Synchronization | `edgemed/sync.py`, `gateway.py`: durable operations, mTLS, Ed25519 signatures, retry, pull cursor, immutable reference revisions | Preserve narrow export policy. Queue acknowledgement means central acceptance; it does not prove another device has received the update. |
| Snapshots | `edgemed/snapshots.py`: signed manifest, size/hash/scope/model/nonce checks, generation checks, archive validation, staged reference shard | Useful existing controls. Download currently holds the retrieval lock; full reference refresh is optional during the demo and should not interrupt search. |
| Runtime security | `edgemed/cli.py`, `security.py`: macOS APFS encrypted sparsebundle, Keychain, SQLCipher, generated credentials | Mac-specific. Vault verification checks expected image/mount association; a configuration boolean is not continuous proof of vault security. Browser sign-out leaves services and volume running. |
| Deployment | Local native processes; manually provisioned model and Qdrant binary | Add preflight and document versions. Do not pretend a fresh clone is immediately runnable. |

Qdrant documents Edge as an embedded, in-process engine and currently labels it beta. Pin the tested API rather than assuming Qdrant Server settings are interchangeable with Edge settings. [Qdrant Edge documentation](https://qdrant.tech/documentation/edge/).

### Important source findings

1. **Canonical reads scale with the corpus on every query.** `retrieval.py:90` calls `Store.list(limit=10000)`. `store.py:242` selects IDs and calls `get()` for each; `get()` performs two selects and hydrates every revision. For N records this is approximately 1 + 2N selects before ranking, excluding unrelated concurrent work. This is a code-derived count, not a measured latency attribution.
2. **Keyword work is rebuilt per query.** `retrieval.py:100–112` tokenizes all allowed content, computes document frequencies, and creates Counters repeatedly. Semantic-only mode still performs this work, although it does not use lexical scores in fusion.
3. **Indexing and search share one long-lived lock.** `drain()` holds it for up to 32 records, embedding and flushing one record at a time. Foreground search can wait behind the whole batch. The separate background worker also runs transport only after indexing finishes.
4. **Deletion can race with indexing.** Jobs capture deletion state before embedding; deletion can then mark jobs pending, followed by the old indexer writing a vector and marking the job indexed. Canonical filtering hides the record, but the derived vector may remain. The central projector needs the same review.
5. **Current limits affect retrieval correctness.** Only the newest 10,000 canonical records are considered. Dense retrieval selects 100 candidates before subject/current-head filtering. Old revisions can crowd out eligible hits. The plan must remove silent corpus truncation or reject unsupported datasets explicitly.
6. **Conflicts need clearer result evidence.** Dense retrieval may match either current branch, while `Store.get()` chooses one branch's text for `content`. A result should identify which active revision matched and flag the conflict rather than imply that one branch is definitive.
7. **Snapshot refresh can block local search.** `api.py:286` holds `retrieval.lock` while downloading/installing the snapshot. Network work should eventually happen before a brief activation lock; until fixed, keep refresh out of the demonstration sequence.
8. **Browser state has security and usability gaps.** Sign-out clears several objects but not query/form/view state; in-flight refresh or search can complete after sign-out and repopulate state. Polling also resets an inspector using only the first 100 listed records, so a valid search result outside that page can disappear.
9. **Transport enabled is not online.** The UI shows a configured switch, not verified gateway reachability. Error text conflates network failure and signature verification failure. The latter should not look like an ordinary offline state.
10. **Some unnecessary background writes exist.** The worker writes `worker_error=None` every cycle, even when unchanged. Status polling also hydrates the whole corpus. Measure CPU, disk activity, and contention before changing polling rates.

## 3. Performance investigation

### What is already measured

`docs/benchmark-results.json` records 1,000 synthetic records, 30 queries from five repeated templates, p50 15.15 ms, p95 23.69 ms, maximum 23.72 ms, indexing 43.349 seconds, and peak process RSS 263.6 MB. The benchmark directly calls `Retrieval.search`; it does not measure full HTTP authentication, response serialization, browser rendering, or the whole two-device process stack. Model construction precedes the query loop and indexing has already exercised the model. These numbers are neither cold-start measurements nor a strong p99 sample.

No stage timings exist. Likely bottlenecks must remain hypotheses until P0-02 measures them. In particular, do not invent an embedding contribution or claim Qdrant itself consumes the current 15 ms.

### Timing boundaries to implement after approval

Use `perf_counter_ns()` and request IDs unrelated to patient identifiers. Keep traces in bounded memory and write aggregate synthetic benchmark artifacts. Never write raw queries, notes, vectors, cookies, signatures, or credentials into traces. Detailed timing must be opt-in and unavailable to unauthenticated clients.

| Span | Exact boundary / purpose |
|---|---|
| API total | Request arrival/body receipt through final response body emission; middleware, authentication, validation, worker dispatch, handler, serialization included |
| Middleware/dispatch | Host/origin/body/session/CSRF work and waiting for an endpoint worker; separate from retrieval lock wait |
| Query normalization | Trim and existing token processing; avoid changing clinical text semantics as a performance shortcut |
| Retrieval lock wait | Before lock acquisition to acquisition; essential for indexing/refresh interference |
| Embedding | Tokenization, ONNX inference, pooling/normalization and Python conversion; split internal subspans only where supported |
| Canonical eligibility | SQL time, select count, rows loaded, current-head/owner/deletion filtering; record lock wait separately |
| Dense local/reference | Each shard search independently, candidate count and filtered count; separate conversion if significant |
| Keyword | Token lookup/tokenization, DF/statistics, BM25 scoring and ranking |
| Fusion | Rank deduplication, RRF, deterministic ties, final truncation |
| Payload hydration | Fetch authorized display fields for final results; full history only for inspector |
| Serialization | Result validation/conversion and JSON encoding, plus response bytes |
| Client round trip | Browser fetch start through body decoding; includes loopback/network and server time |
| Visible result | User submit through committed/rendered results; record separately from network timing |
| Background work | Index queue age, batch duration/size, projection flush, sync attempts and status requests |

Nested spans must not be added twice. Do not subtract independently calculated medians to derive a stage duration. Correlate individual requests; browser-minus-server duration is a residual that includes scheduling and decoding, not pure network time. Capture diagnostic and non-instrumented runs to quantify tracing overhead.

### Reproducible benchmark protocol

1. Freeze baseline commit, Python/package locks, model/tokenizer hashes, dimensions, ONNX provider and thread settings, Edge configuration, OS/CPU/RAM/storage, power mode, and dataset/query seeds. Record whether the browser, central gateway, second device, indexing and sync are running.
2. Use an isolated synthetic dataset on verified encrypted storage. Never benchmark against or reset the existing user's runtime. Preload all assets; disconnect outbound connectivity for offline runs. Do not clear operating-system caches on the user's development machine.
3. Primary corpus: 1,000 varied synthetic observations. Include multiple subjects, 10–15% multi-revision records, conflicts, deletions, another owner, long notes and difficult exact terms. Keep the existing five-template benchmark as a historical comparison, not the quality evaluation.
4. Prepare at least 50 manually reviewed query/relevance cases, including paraphrases, exact terms, misspellings, negation/context, subject filters, conflicts, and no relevant match. Hold these out from optimization tuning. Memory retrieval is informational; the labels do not assess diagnostic safety.
5. A second deterministic workload should supply at least 200 distinct query strings and 1,000 timed requests per run, randomizing order. Use three runs if deadline permits. Report sample count, nearest-rank percentile convention, per-run p50/p95/p99 and maximum. With fewer samples, label tail estimates provisional.
6. Test 100 and 1,000 records for P0. Test 10,000 for P1, or earlier if implementation changes remove the present cap. Never load >10,000 and silently benchmark a truncated subset.
7. Separate process-cold startup, first query after ready, and warm queries. For process-cold, restart only the isolated test app at least five times; label the OS page cache as uncontrolled. Warm with 20 requests, exclude those, then measure. Report model load and shard-open startup separately.
8. Record four modes: dense-only with a precomputed vector; hybrid retrieval with that vector; complete backend query with embedding; browser/API end-to-end. Authentication remains enabled for HTTP/browser runs. Synthetic precomputed-vector tests are diagnostic only.
9. Default optimization comparison has application query/result caches disabled. If caching is tested, publish cold misses, exact repeats, cache hit ratio, eviction behavior and RAM separately. Repeating five queries cannot justify the uncached target.
10. Run normal idle search, search during a bounded indexing batch, search during failed sync/reconnect, and two simultaneous local clients. Include reference shard on/off. Observe thread-pool and lock waits rather than increasing concurrency indiscriminately.
11. Record active/peak RSS per process and process-tree aggregate, CPU with 100% defined as one fully used logical core, disk bytes allocated and logical bytes, database/WAL/vector/model sizes, queue recovery, and result quality.
12. Compare paired workloads before/after each optimization. Security/correctness assertions are hard gates. Report held-out recall@5/nDCG@10 against judged cases and dense approximate recall against an exact-search reference where applicable. Never use timing success to accept wrong-owner, deleted, or obsolete-only hits.

Artifacts proposed after implementation: a versioned benchmark specification, raw JSONL span samples with synthetic query IDs, machine-readable summary, human-readable comparison, and a short command-based runbook. Keep results outside source by default; commit only a reviewed aggregate report without secrets or machine-specific credentials.

### Optimization candidates, in order

Benefit rankings below are hypotheses, not promises. Effort overlaps milestone estimates and must not be counted twice.

| Order | Change | Expected benefit | Effort / complexity | Correctness and RAM impact | Deadline decision |
|---|---|---|---|---|---|
| 1 | Replace N+1 full-history loading with bounded bulk current-head reads; fetch only final result summaries | High CPU/SQL/payload benefit | 3–5 h, moderate | Preserve owner/deletion/revision predicates; reduces transient memory | First performance change if profiling agrees |
| 2 | Skip keyword work in semantic-only mode; avoid unchanged settings writes; make status counts aggregate queries | Low–medium, low-risk waste removal | 1–2 h, low | No query-ranking change for hybrid; less I/O | Include when demonstrated |
| 3 | Short, bounded indexing batches; batch embeddings and flush; versioned acknowledgement | High responsiveness/index throughput | 3–6 h, moderate | Race safety is mandatory; batch size increases peak RAM | Correctness part P0; tune only after timing |
| 4 | Maintain token/TF/DF statistics instead of retokenizing all text | Potentially high corpus-scale benefit | 4–8 h, moderate | Cache invalidation, owner/subject-specific BM25 statistics, extra RAM | P1 unless clearly dominant and time remains |
| 5 | ONNX thread settings 1/2/4, sequential execution baseline, measured idle spinning | Medium, hardware-dependent | 1–3 h experiment | Quality unchanged with same model; too many threads compete with indexing | Time-box P0 experiment |
| 6 | Correct subject/current-head candidate filtering and deduplication, then tune candidate count | Medium speed/recall improvement | 2–4 h, moderate | Candidate reduction can lose recall; sensitive filter metadata stays local | Correctness first, tuning P1 |
| 7 | Bounded in-memory query-embedding cache | High exact-repeat benefit only | 2–4 h, moderate | Query/vector sensitivity and invalidation; reserve ≤8 MiB | P1; no headline cached benchmark |
| 8 | Edge index/search parameters, on-disk settings, supported payload indexes | Unknown until shard profiling | 3–6 h, moderate | Index build cost, RAM, approximation quality | P1 only with exact-search comparison |
| 9 | JSON conversion/serializer changes | Usually small relative to full-record loading | 1–3 h | API compatibility/dependency cost | Only if ≥10% measured hot-path cost |
| 10 | Model change, quantization conversion, reranker, alternative embedding runtime | Potentially large but uncertain | 1–3+ days | Re-embedding, quality drift, snapshot compatibility and supply chain | P2 |

The installed FastEmbed implementation already creates an ONNX session during model initialization, enables graph optimizations, and sets intra/inter-op thread counts from the supplied `threads=2`. Do not spend the deadline “fixing” model recreation that the code does not do. Some ONNX session settings are not exposed by this FastEmbed version; avoid monkeypatching internals in P0. ONNX's own guidance describes latency/CPU tradeoffs in threading and spinning. [ONNX Runtime thread management](https://onnxruntime.ai/docs/performance/tune-performance/threading.html).

#### Selected retrieval design

- Add a compact authorized current-head read path in SQLCipher; keep history available through detail endpoints. Index owner/deleted/subject fields only if query plans justify it. Migrate transactionally and test old databases.
- Define search result DTOs with ID, title, subject, category, sharing status, current-head IDs, matched revision ID, conflict/indexing state, short excerpt and scores. The inspector fetches detail by ID and authorization. A conflict match must show the matched branch and all competing heads.
- Keep canonical authorization authoritative even when Qdrant payloads or a cache disagree. Recheck selected results at response construction under a defined snapshot/generation rule. Deletion tests must demonstrate no result after a completed delete; a concurrent response ordered before deletion is a different case and must be documented.
- Preserve BM25 tokenization and ranking initially. If a lexical cache is warranted, scope it by owner and eligible subject corpus, revision/generation and tokenizer version. Update/invalidate after every create, revision, delete, inbound sync and restore. On mismatch, rebuild or take a bounded correct fallback; never return stale cached content.
- Do not start with result caching. If embedding caching is added, use exact normalized-query bytes plus model/tokenizer/prompt version and session/owner scope. Do not lowercase or remove punctuation merely to increase hits. Keep cache in memory only, with capacity/TTL and explicit session/vault clearing. A hash alone is not a privacy boundary.
- Keep one local app process per device; Edge is already in-process. Do not merge central and device processes to improve a benchmark. On slower hardware, run only one device locally and place the optional central demo services on the Mac.

#### ≤5 ms decision rule

Spend at most 2–3 hours on targeted inference/search tuning after instrumentation and the first structural improvement. If uncached query embedding alone approaches/exceeds 5 ms, complete warm ≤5 ms is not supported by that model/device configuration. Publish the measured lower bound and move the goal to useful responsiveness. Retrieval-only ≤5 ms can remain a separately labeled result. A full query target is never waived by excluding encryption, security checks, filtering, conflicts, or result hydration.

## 4. Security threat model and smallest useful changes

Assets are canonical notes/revisions, query text, embeddings/indexes, operator sessions, vault/database/signing keys, audit history and export policy. Trust boundaries are browser↔loopback API, process↔encrypted storage/Keychain, edge↔gateway, gateway↔Qdrant Server, and downloaded asset/snapshot↔native parsers.

Assume synthetic data for the hackathon. Still test boundaries as if notes were sensitive. A malicious website, another unprivileged user, corrupted files, a replaying peer, and a lost powered-off device are realistic test actors. Root/admin malware or arbitrary execution as the unlocked OS user can read memory and mounted files; app encryption does not defeat that actor. Do not claim it does.

Severity below is impact plus realistic opportunity in this prototype. These are source-review findings and planned tests, not proof of a remotely exploitable vulnerability in every case.

| ID / severity | Finding or threat | Existing defense / remaining gap | Smallest next action |
|---|---|---|---|
| S1 High, P0 | Sensitive UI state after sign-out/session expiry or on an unattended unlocked screen | Absolute 30-minute server expiry exists; no idle policy; in-flight responses can repopulate state | Session epoch and AbortController; clear all record/query/draft state; no stale response after expiry; server inactivity policy plus distinct lock/sign-out behavior |
| S2 High, P0 | Delete-during-indexing and stale derived vectors | Canonical filtering prevents normal deleted-result display; acknowledgement race leaves stale projection | Version jobs and make stale completion unable to mark deletion work complete; equivalent central projection review; deterministic interleaving tests |
| S3 High, P0 rehearsal | Vault shutdown/lifecycle errors | Mac encrypted image and process locks exist; full lock/restart not verified; gateway worker shutdown can outlive cancellation | Explicit quiesce/join/flush/close order, bounded waits, fail visibly on busy unmount; prove wrong/missing key fails closed |
| S4 High impact, P0 operational / P1 product | Lost keys or corrupted data with no proven restore | No validated backup/recovery workflow | Same-machine encrypted cold-backup rehearsal in isolation; portable recovery/key escrow is P1, not a claimed feature |
| S5 Medium–High, P0 bounded review | Malformed or flooding signed sync traffic, unsigned large bodies, resource exhaustion | Strict schemas, mTLS and signatures; gateway lacks local API's streaming body limit | Gateway byte/time/concurrency limits, signature before expensive projection, strict receipt/pull DTOs and max changes; generic errors; adversarial payload tests |
| S6 Medium, P0 tests / P1 workflow | Replay, revocation and identity lifecycle | Operation hash/idempotency, request-bound pull nonce/cursor and configured revocation exist | Test revoked signing identity, altered duplicate operation, reordered changes and fresh request binding; document config reload requirement; rotation UI deferred |
| S7 Medium, P0 behavior / P1 hardening | Corrupt/tampered local vector files | Disk encryption is confidentiality, not full authenticated integrity; canonical records remain authority | Fail closed on unreadable shard, clear recovery state, rebuild disposable projection from canonical data; do not claim detection of every silent vector edit |
| S8 Medium, P0 tests / P1 optimization | Snapshot rollback/corruption or slow refresh blocking search | Signature/hash/nonce/generation/archive checks exist | Test rejection leaves old shard usable, activation failure, wrong model/scope, oversized archive; avoid network I/O under search lock if snapshot remains in P0 demo |
| S9 Medium, P0 review | Logs/traces containing notes/queries/credentials | Access logs disabled, audit events metadata-only; exception and new profiling paths still need review | Allowlists for log fields, redaction tests with unique canaries, bounded retention, no raw request/response dumps |
| S10 Medium, P0 preflight | Missing/substituted model or binary, dependency drift | Locks exist, assets were manually provisioned | Asset hashes and verified origin manifest, frozen installs, offline startup test, current audit review; do not blindly upgrade before demo |
| S11 High impact, limited app control | Unlocked-user malware, secrets in memory, stolen running device | Keychain and encrypted disk do not protect decrypted process memory | OS screen lock, no persistent plaintext credentials, reduce unnecessary copies, process shutdown for full lock; no Python zeroization claim |
| S12 Medium residual, P2 architecture | Whole-volume rollback or audit truncation | Audit HMAC verifies chain links; checkpoint and chain are on same recoverable device | Document limit. Independent signed checkpoint/key separation/rollback-resistant state are later work; no “tamper-proof audit” label |

### Exact P0 security behavior

**Session lifecycle.** Keep 30-minute absolute expiry, add a proposed five-minute idle expiry, and clear client content immediately on sign-out/expiry. Background status polling must not keep a session alive. Track deliberate foreground actions and rate-limited activity notifications; treat this as protection against unattended use, not malicious same-origin script. Use a session generation token so responses from a prior login cannot update a later session. Abort pending requests and clear modals, query, selection, records, results, notices and drafts. Never put notes or credentials into localStorage, URLs, service-worker caches or telemetry. OWASP recommends server-enforced idle and absolute timeouts; adapt the exact idle interval only if the demo usability check requires it. [OWASP session guidance](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html).

**Indexing safety.** A queued job must carry a generation/expected state. Compute embeddings outside the long shard critical section where safe, then validate the canonical generation before committing and acknowledging. A deletion that occurs at any point must leave a pending purge until the corresponding shard deletion is durable. If a crash occurs after vector write but before acknowledgement, retry is idempotent. If a deletion occurs during a central network upsert, a later confirmed delete must remain queued. Do not hold a canonical database lock across network I/O to obtain apparent atomicity. Preserve lock ordering and document it. Test the local and central interleavings with deterministic barriers, not timing sleeps.

**Full vault lock.** Distinguish “Sign out / hide workspace” from the operational CLI action that stops services and unmounts the vault. Stop new work, stop/join worker threads, flush projections, close SQLCipher and shard handles, invalidate sessions, then unmount. On timeout or busy volume, report that the vault remains mounted; never display a locked claim. Do not add an unauthenticated web endpoint that executes shell commands. Automatic OS-lock integration is P1.

**Recovery.** Stop/lock an isolated demo profile, copy only the unmounted encrypted container, verify its checksum, and restore to a separate test location. Ensure compatible keys are available through the protected local store; prove record/revision/tombstone and queue integrity. Do not copy a live database without its consistency protocol or export Keychain secrets to plaintext. This demonstrates recovery on the same machine, not recovery after losing the machine and its keys. Do not reset the user's existing profile to rehearse.

**Authentication and local API.** Preserve Argon2, host/origin/CSRF checks and loopback binding. Test streaming oversized input, wrong owner, unknown properties, content rendered as text, and no-content cache behavior. Scope claims to the single demo facility/operator model. Multi-tenant administration and permission redesign are out of scope.

**Logging and audit.** Record action IDs, states, durations, counts and opaque correlation IDs; exclude tokens and clinical text. HMAC chaining detects covered modifications when the key is protected; it does not independently detect rollback of the complete store. [OWASP logging guidance](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html).

## 5. Slower-device strategy

### Choose existing hardware first

**Hardware update:** the user has a Snapdragon 720G device with 8 GB RAM. RAM alone does not establish compatibility. Assuming Android, the present Python 3.12/FastEmbed/ONNX/SQLCipher/Edge native dependency stack and macOS Keychain/APFS launcher need a separate platform adaptation. Linux ARM64 wheel availability is not Android wheel compatibility: the platform tags distinguish glibc-based manylinux from Android API-level/ABI targets. Python's Android guidance also describes an application-specific embedding/distribution environment. [Python packaging platform compatibility](https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/), [Python on Android](https://docs.python.org/3/using/android.html).

**Decision for this deadline:** do not promise a true on-phone backend in 1–2 days. Do not spend P0 compiling the complete native stack through Termux or a Linux compatibility environment. First ask whether an older desktop/laptop can be borrowed. If none is available, deliver the Mac baseline and a clearly labeled constrained-resource experiment; state that physical slow-device backend validation is pending. This means the original hardware-proof objective remains incomplete, not passed by a substitute test.

The phone can optionally test touch layout and browser responsiveness using a reviewed development tunnel that preserves the local API boundary, after P0. This still executes search on the Mac and depends on that connection. It is not Android on-device search, nor proof that the phone works when disconnected from its backend. Do not expose the current loopback HTTP API to the LAN or weaken origin checks just to show the phone.

Preferred borrowed/refurbished fallback class: a Dell OptiPlex 3060 Micro with i3-8100T, 8 GB RAM and a 128–256 GB SSD, or a comparable older clinic/office laptop. Dell documents the i3-8100T model as a four-core 35 W configuration with Linux support. This is a representative target, not a procurement recommendation or a current-price claim. [Dell hardware specification](https://www.dell.com/support/manuals/en-au/optiplex-3060-micro/optiplex_3060_micro_setup_and_specs/processor?guid=guid-cd1daac8-70ee-4488-918d-58acae5cf479&lang=en-us).

Use a currently supported 64-bit OS. Do not install an obsolete Ubuntu version just because it appears in the original hardware manual. Raspberry Pi-class ARM64 hardware is a secondary option if already available; include cooling, storage and power in its evaluation. Version 0.8.0 of the Qdrant Edge Python package lists Linux x86-64 and ARM64 wheels, but the full pinned stack, CPU instruction compatibility, SQLCipher, secure storage and launcher still require a smoke test. [Pinned package files](https://pypi.org/project/qdrant-edge-py/0.8.0/).

### Hardware decision gate: 30–60 minutes after approval

Confirm the phone's OS/model and whether a desktop-class alternative exists; inventory CPU/architecture, RAM, disk free space, encryption, secure secret-store availability and Python/runtime compatibility. If an alternative machine can run the existing stack with a small reviewed launcher adaptation, use it. If the port needs OS installation, filesystem repartitioning, unsupported wheels or a new key-management system, defer it to P1. Native Android adaptation is P2. Continue a labeled constrained-machine experiment on the Mac/VM if available without setup delays; never claim that emulation proves performance on physical hardware.

The current launcher is macOS-only. A Linux target requires explicit runtime paths, a verified encrypted data volume and supported protected secret storage; missing encryption or keys must fail closed. Do not weaken encryption to meet the deadline. A temporary performance harness using synthetic data alone may be used as a clearly labeled performance-only experiment; it does not validate the production security path or count as the complete application demo.

### Proposed budgets

Workload: one local device process, 1,000 synthetic records with the benchmark revision/query mix, model cached, no central services on the slow device. Measure browser separately and together. These are starting budgets to validate, not guarantees or existing achievements. The second column is for a borrowed older desktop/laptop, not a prediction for the Snapdragon phone.

| Metric | Apple Silicon development Mac | Older 4-core / 8 GB device |
|---|---|---|
| Process start to ready, volume already unlocked | ≤10 s | ≤30 s |
| First complete query after ready | ≤500 ms | ≤1.5 s |
| Warm uncached complete backend query p50 / p95 | ≤20 / 50 ms release budget; ≤5 ms experimental p50 | ≤100 / 250 ms |
| Warm backend p99 | ≤100 ms diagnostic budget | ≤500 ms diagnostic budget |
| Browser submit to visible results p95 | ≤200 ms | ≤600 ms |
| Foreground backend search p95 while indexing | ≤250 ms | ≤750 ms |
| Single edge backend RSS steady / peak | ≤600 / 900 MiB | ≤600 / 900 MiB |
| Edge plus one browser tab total working set | Measure; target ≤1.5 GiB | ≤1.5 GiB |
| Idle CPU, five-minute mean | <2% of one logical core | <2% of one logical core |
| Index 1,000 records | ≤60 s including vector durability | ≤180 s |
| Single new observation becomes semantically searchable, no backlog | ≤2 s | ≤5 s |
| App+model+dependencies, excluding OS | ≤3 GiB | ≤3 GiB |
| Active 1,000-record runtime excluding retained backups | ≤256 MiB initial budget | ≤256 MiB initial budget |
| Free space before snapshot staging | Existing ≥1.5 GiB staging safety check retained | Same, or fail clearly before starting |
| Offline test | 30 min, create/search/restart succeeds, no external requests | Same |

For a later native Android feasibility phase, provisional 1,000-record acceptance budgets are startup ≤30 s, uncached complete-query p50 ≤150 ms / p95 ≤400 ms, foreground result display p95 ≤800 ms, backend peak ≤900 MiB, index 1,000 records ≤5 minutes, idle CPU <2% of one core, package/model/runtime ≤3 GiB, and a 30-minute airplane-mode persistence/search test. These are planning thresholds only, contingent on native dependency feasibility. Measure thermal throttling, battery impact, process eviction and restart recovery; a phone has different background-lifecycle constraints from a desktop.

Report snapshot copies, WAL, database, vector files and logs separately; do not confuse a sparsebundle's virtual 4 GB capacity with physical allocation. If limits are missed, record the cause and proposed revised SLO before changing them. A device with different RAM/CPU needs its own labeled budget. Do not slow down the Mac artificially and call that an equivalent old CPU.

### Test sequence

Install/provision while online, validate hashes, run local health/crypto/model smoke tests, and record idle/startup resource use. Run cache-miss and repeat benchmarks. Disconnect external connectivity while preserving loopback; create and revise synthetic notes, search, restart the local app, verify persistence and zero external access. Restore only the gateway route and verify approved queue recovery. Test low free disk by an isolated bounded test fixture; do not fill the user's disk. Log thermal/power state and throttling during sustained indexing. Add a 10,000-record stress test only after P0 passes and the corpus-cap issue is addressed.

## 6. Product and UI plan

### Main workspace

Keep one obvious search box and one primary “Add observation” button. Use a compact persistent status row: **Device A · Local workspace ready · Shared service connected/unavailable · 3 approved updates pending · 1 conflict**. If the API itself is unavailable, say so; do not show “offline but working” when saving cannot work. Keep the synthetic-only label visible.

Simplify navigation to **Memory**, **Needs review**, and **Sharing & activity**. Keep the graph as an optional secondary view, with no expansion this phase. Technical engine/version information belongs in a small diagnostics panel, not the main workflow.

### States and interactions

| Flow | Planned behavior | Acceptance |
|---|---|---|
| Capture | Title, synthetic subject and note first; optional category/privacy details; clear “stays on this device” explanation; single-submit guard | Successful save shows “Saved on this device”; indexing is a separate state. Network loss does not prevent local save. Draft survives ordinary validation errors in memory, but is erased on lock/logout. |
| Search | Explicit submit; disable duplicate submit; cancel/ignore superseded responses; local-results badge; clear loading/empty/error states | Older searches cannot replace newer results; keyboard submit works; timer label describes what is measured. |
| Inspect | Fetch detail by ID; show matched active revision, source, time, sharing reason, history and conflict warning | Polling cannot close a valid result outside the current list page; escaped content cannot execute HTML/script. |
| Connectivity | Distinct local API readiness, last verified gateway contact, user-paused transport, gateway unreachable, verification error and reconnecting | Status derives from observed transport outcomes and freshness, not just `enabled` or `navigator.onLine`. No third-party internet ping. |
| Queue | Separate waiting/retrying/failed/central-accepted counts, oldest age, last attempt and simple reason | Local-only notes are never counted as pending sharing. Permanent failures remain visible. Central acceptance is not labeled peer delivery. |
| Conflicts | Dedicated list and side-by-side current branches, device/time/source, differences, choose-existing-branch action | Show both branches; one explicit confirmation creates a resolution revision over all current heads. A concurrent new head returns “changed while reviewing”; refresh before resolving. |
| Activity | Plain-language local save/index/sync/conflict events with timestamps; diagnostics disclosure for IDs | No raw payload JSON by default; no notes in operational logs. Full revision history remains in the inspector. |
| Session | Sign out/hide workspace clear client state; idle warning if feasible; full vault lock described separately | Re-login cannot reveal prior user's stale response, query or draft; no false “vault locked” message. |
| Accessibility | Semantic dialog, focus trap/return, Escape handling, visible focus, labeled controls, status text independent of color | Entire primary workflow works by keyboard; 390 px viewport has no horizontal overflow; asynchronous status uses restrained live announcements. |

Keep refresh requests bounded and view-specific. Poll lightweight status at approximately 5 seconds while visible; back off when hidden/unavailable. Fetch list and detail on relevant changes, not full history every three seconds. Separate request cancellation/session epochs from performance caching. Do not add a service worker: offline operation already means a running local server, and caching private API content creates another storage boundary.

### Honest 5–7 minute demonstration

1. Show both device profiles with distinct labels and a verified connected gateway. Explain that central services may also run on the same Mac for the simulation.
2. Add a private synthetic observation on A and search it locally. Show “local only” and no outbound queue increment.
3. Interrupt A's gateway route using a reversible test-specific proxy/process/network boundary, while leaving the local API and browser loopback running. If only the transport switch is used, explicitly label it “sync paused simulation,” not a real network disconnection. Turning off Wi-Fi alone will not interrupt the all-loopback gateway.
4. Add another private note and perform a new semantic query while disconnected. Show saved/indexing/searchable states.
5. Edit an approved synthetic reference on A. Show its pending outbound operation. This supplies the queued sharing example without exporting a patient observation.
6. Make a different approved variant edit on B from the same common ancestor. Keep the operations deterministic and isolated from the user's existing data.
7. Restore connectivity. Show pending→central accepted and then the changed reference on B. Show that A's private note never appears on B.
8. Open the conflict, compare both branches, choose one, and create a new resolution revision. Show convergence on both devices while historical branches remain inspectable.
9. End with the activity trail and an honest performance card: hardware, corpus, sample count, complete-query versus retrieval-only latency, and offline proof.

Automate the rehearsal with isolated synthetic profiles or a clearly scoped test runtime. Never implement a global “reset everything” button that can delete the existing vault. A demo fixture namespace must include its own protected keys, roots, ports and cleanup boundaries.

## 7. P0 work packages and acceptance gates

These estimates total approximately **24–40 engineering hours** if the hardware is already compatible and only one measured structural performance change is selected. They overlap no P1 task estimates. Actual platform adaptation adds time. Work may be divided among people after implementation is authorized; this plan itself spawns no implementation agents.

| ID | Work / proposed files | Effort | Dependencies | Acceptance gate |
|---|---|---|---|---|
| P0-01 | Freeze scope, machine inventory, baseline capture, isolated-runtime and API/result contracts | 1–2 h | User implementation command | Baseline commit and asset versions recorded; no existing runtime modified; device feasibility decision; export policy and target latency definitions agreed in docs |
| P0-02 | Stage timing, isolated benchmark harness, representative synthetic cases (`scripts/benchmark.py`, focused timing helper) | 3–5 h | P0-01 | Full span accounting, lock wait, SQL count, response bytes, cold/warm and uncached/repeat separation; baseline results saved; no private trace fields |
| P0-03 | Index job generation/race fix and shutdown ordering (`store.py`, `retrieval.py`, `sync.py`, `gateway.py`) | 3–5 h | P0-01 | Delete at each deterministic race boundary leaves no active hit and eventually no private shard point; stale acknowledgement cannot clear purge; crash/retry safe; safe closure under active worker |
| P0-04 | Session/browser clearing and bounded ingress (`api.py`, `security.py`, `gateway.py`, frontend API/session code) | 3–5 h | P0-01 | Logout/expiry clears state, late responses ignored, polling does not extend idle life, oversized sync rejected before costly work, prior security tests pass |
| P0-05 | One measured retrieval improvement: bulk current-head reads and lean result hydration; skip demonstrably unused work | 3–5 h | P0-02, P0-03; result contract from P0-01 | Same or corrected authorized/current results; no silent 10k truncation; explain matched conflict branch; paired timings published; no quality regression accepted for speed |
| P0-06 | Clear memory/sharing/conflict UI with honest connectivity and reliable detail fetch | 4–6 h | P0-01 contract; integrate P0-04/05 | Capture/search/detail by keyboard; correct states/counts; no private record sharing; conflict race handled; mobile smoke test passes |
| P0-07 | Preflight, asset manifest, lock/restart and same-machine encrypted backup rehearsal | 2–4 h | P0-03/04 | Missing model/key/invalid vault fails clearly; no download during offline operation; isolated restored data and queue verified; unmount failure is reported honestly |
| P0-08 | Hardware feasibility and, only if a compatible borrowed machine exists, physical slow-device smoke | 2–3 h | P0-01 hardware gate, P0-02 | Snapdragon/Android gap explicitly recorded; either actual desktop-device measurements or a labeled constrained-resource experiment. Android backend proof remains P2; missing physical validation is not a pass |
| P0-09 | Full demo regression, reconnect/conflict script, reviewed result report, release freeze | 3–5 h | P0-03–08 | Three complete isolated rehearsals; no privacy/correctness regressions; local checks and final browser run on exact candidate commit; measured limitations recorded |

The upper bound is 40 hours, before a 20% uncertainty allowance. Do not imply three contributors make all steps parallel: the result contract, correctness fixes, integration and final rehearsal are sequential dependencies. Each contributor should own separate files/areas or use agreed small integration commits.

### Suggested two-day allocation

- First 1–2 hours: scope, contracts, isolated runtime, machine feasibility, baseline measurements.
- Backend contributor: P0-02/03/05; UI contributor: P0-04 client handling and P0-06; verification contributor: P0-07/08 and adversarial cases. Assign one owner for API/session backend integration.
- End of day one: indexing/session fixes integrated; one baseline/after comparison; capture/search/queue states demonstrable. If this gate fails, cut further tuning and optional UI work.
- Day two first half: finish selected work, physical-device run where feasible, integration checks and security regression.
- Final 3–4 hours: P0-09 only, documentation of limitations, freeze. No model upgrades, schema redesign or cosmetic rebuilds.

## 8. P1 — high-value only after P0 is stable

| ID | Task | Estimate | Depends on | Acceptance |
|---|---|---|---|---|
| P1-01 | Incremental lexical statistics with exact scoped invalidation | 4–8 h | P0-02/03/05 | Original tokenization/BM25 equivalence within defined ties; owner/subject isolation; invalidation and RAM cap tests; demonstrated measured benefit |
| P1-02 | Query-embedding cache and small ONNX tuning matrix | 3–6 h | P0-02/04/05 | Separate hit/miss numbers; bounded cache; cleared on session/vault boundary; model change invalidation; quality preserved |
| P1-03 | Desktop Linux slow-device launcher/storage/secret-provider adaptation if needed | 6–12 h | Hardware feasibility, P0-07 | Encrypted storage and key availability verified; no plaintext fallback; restart/offline tests on physical target; reproducible provisioning. This estimate excludes Android |
| P1-04 | Snapshot download outside search lock, safe activation/cleanup | 3–5 h | P0-03 and snapshot integrity tests | Failed download/activation retains previous shard; search remains within load budget; concurrent delete still authoritative; old shards cleaned only after safe swap |
| P1-05 | Supported backup recovery across machines and controlled signing-key rotation/revocation runbook | 6–12 h | P0-07, strict identity tests | Encrypted recovery tested with separately protected key material; old revoked identity rejected; interrupted rotation does not destroy data; no mass key reuse |
| P1-06 | 10k corpus, 1-hour soak, dependency/model supply-chain review | 3–5 h | P0-09 | No hidden cap, resource figures recorded, queues converge, no unbounded logs/shard retention, pinned assets verified |
| P1-07 | OS lock integration, richer accessible conflict diff, compact activity pagination | 4–8 h | P0-04/06 | No accidental session renewal; keyboard/manual usability checks; no full-history polling; useful state without technical clutter |

Do not start every P1 item because individual estimates look small. Select one based on measured impact and remaining time.

## 9. P2 — post-hackathon

| Work | Rough effort | Dependencies / completion definition |
|---|---|---|
| Schema/API/ADR reconciliation and platform packaging | 3–5 engineer-days | Stable prototype behavior; contracts match implementation; migration/install/upgrade rollback tested |
| Independent security assessment, stronger local integrity/rollback design and separated audit keys | 5–10+ engineer-days | Explicit operational threat model and recovery design; attack tests and documented residual risks |
| Complete key lifecycle, protected cross-device recovery and administrative roles | 5–10+ engineer-days | Provision/revoke/rotate/recover tested across interruptions; no broadening of data sharing without a new policy decision |
| Larger corpus/device evaluation and optional model changes | 3–7+ engineer-days | Held-out relevance cases and physical hardware; model/version compatibility and re-index plan |
| Native Snapdragon/Android feasibility and prototype | 1–2 days feasibility; tentatively 5–15+ further engineer-days if viable | Confirm Android/API/ABI, native Edge/ONNX/SQLCipher builds, model compatibility, protected application storage and Android-specific key/lifecycle design. All create/embed/search must execute on the phone with airplane mode enabled; browser-to-Mac execution does not satisfy this gate. Re-estimate after feasibility |
| Differential snapshots, richer graph and governance/consolidation | 5–10+ engineer-days | Demonstrated need, versioned contracts, deletion/provenance correctness; no autonomous destructive retention |
| Any move beyond synthetic informational memory | Separate scoped project | Privacy, clinical, operational and legal requirements established with appropriate experts; no compliance claim inherited from this prototype |

Do not build before the hackathon: diagnosis/treatment agents, a generative chatbot, EHR/FHIR integration, cloud AI calls, a custom graph database, Redis, Kafka, Kubernetes, microservices, native mobile apps, a model rewrite, automatic clinical-note sharing, custom cryptography, automatic deletion/consolidation, a polished key-management UI, or distributed anti-rollback infrastructure. Avoid dependency upgrades unless a verified issue requires one.

## 10. Implementation guardrails and verification matrix

After the user approves implementation, inspect the then-current working tree and remote state first. Work on a new `codex/` branch based on the actual current code; do not overwrite other contributors' work. This plan is not advance authorization to merge, deploy, purchase hardware, repartition disks, or delete runtime data.

Keep migrations small and versioned. Back up the isolated test database before migration; test migration from schema 1, wrong keys, interruption, and restart. For a canonical-compatible retrieval-only change, prefer rebuildable projections over a new persistent data format. A failed migration must stop without silently creating an empty workspace. Rollback uses the prior code plus its compatible encrypted backup, not an untested reverse migration.

| Category | Required tests |
|---|---|
| Authorization/privacy | Wrong owner, deleted/current-head filtering, subject scope, private/highly-sensitive queue exclusion, strict export schema, session/CSRF/host/origin behavior |
| Lifecycle/concurrency | Deletion at embedding/upsert/ack boundaries, revision while searching, resolution with stale parents, shutdown during indexing/network work, idempotent restart |
| Synchronization | Offline durable queue, retry/backoff, duplicate and altered operations, revoked identity, invalid signature, missing client cert, pull nonce/cursor mismatch, reconnect and both-device convergence |
| Snapshot | Wrong signer/model/scope/nonce, stale generation, oversized/compressed/path traversal input, failed install keeps old shard, canonical tombstones respected |
| Browser | Capture→search→inspect, keyboard/focus/mobile, sign-out/expiry with delayed responses, no script execution, truthful queue/connectivity, conflict choice, detail outside first list page |
| Performance | Before/after identical fixtures, cache labels, cold/warm, representative payloads, indexing interference, sample counts/tails, per-process and total resources |
| Operational | Missing assets/keys, preflight offline, full lock/restart, encrypted backup restore, resource failure in isolation, no sensitive content in artifacts/logs |

Use meaningful targeted tests for changed security/concurrency behavior, then run existing backend, Ruff, TypeScript/build and browser suites. Do not replace real Edge/ONNX integration with mocks for the final proof. Mocks/barriers are appropriate for deterministic race and malformed transport tests. Disable external network at the OS/test-boundary level for the final offline proof; the existing Python socket monkeypatch alone is insufficient to observe all native-library traffic.

Define release gates before implementation: no critical privacy/correctness failures, all applicable local checks pass on the final commit, three rehearsals succeed, measured performance report names its hardware/workload, and unavailable hardware or unfinished platform security is explicitly disclosed. A green unit suite alone does not make the complete roadmap done.

## 11. Deliverables after approval

1. Small implementation commits with focused tests and the minimum necessary schema migration.
2. A reproducible performance harness and a measured before/after report, including an explicit conclusion about the 5 ms target.
3. A readable main workspace with capture, local search, reliable inspection, real connectivity/queue states and explicit conflict resolution.
4. A short threat-model/status document identifying fixed controls, verified behavior and accepted prototype limitations.
5. A preflight and offline demo runbook, asset manifest, isolated synthetic rehearsal, and local recovery evidence.
6. A physical slow-device report if the available hardware passes the feasibility gate; otherwise a precise blocker and a clearly labeled substitute experiment.
7. A final checklist naming the exact tested commit, checks, known issues and deferred P1/P2 work. Publishing or updating a PR can follow the user's implementation instructions; no automatic merge.

## 12. Pending information and decisions

- Exact model and OS of the Snapdragon 720G / 8 GB device; whether a borrowed older Windows/Linux laptop or mini-PC is also available. CPU and RAM are already supplied; do not ask for them again.
- Whether there are actually one, two or three contributors available for the next 1–2 days.
- Exact demo time determines whether the one-day cut or two-day P0 package is realistic.

No answer is needed to review this plan. Once implementation is authorized, use the smallest deadline variant supported by the known team and hardware. The next action now is user review; implementation remains paused until the user explicitly says to start.
