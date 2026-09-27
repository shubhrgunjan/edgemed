# Next-phase implementation and validation

Date: 28 September 2026. Baseline: `c813223`. Environment: macOS 27 ARM64, Python 3.12, pinned Qdrant Edge 0.8.0 / Qdrant Server 1.19.1 / FastEmbed model assets. All generated records and tests are synthetic. Source implementation is in the commits accompanying this report.

## Performance comparison

Same harness, 1,000 records with 10% additional revisions, 20 warm-ups, 200 distinct query strings derived from five templates, three runs of 1,000 complete backend queries. Query embeddings and query results are not cached. The new bounded canonical/lexical corpus is cached and invalidated by canonical/index state changes.

| Metric | Baseline | Revised |
|---|---:|---:|
| Run 1 p50 / p95 / p99 | 17.523 / 25.329 / 31.165 ms | 4.381 / 6.315 / 8.502 ms |
| Run 2 p50 / p95 / p99 | 17.858 / 25.463 / 31.425 ms | 4.339 / 4.634 / 7.552 ms |
| Run 3 p50 / p95 / p99 | 17.866 / 25.368 / 27.420 ms | 4.329 / 4.644 / 7.595 ms |
| Indexing, including flushes | 52.520 s | 17.914 s |
| Peak process RSS | 242.64 MiB | 269.09 MiB |
| Template category hit@5 | 1.0 | 1.0 |

The experimental ≤5 ms warm complete-backend median was reached for this workload on this Mac. This includes query embedding and canonical checks; it excludes HTTP/browser overhead. It does not imply ≤5 ms for every corpus, device, cold query or tail latency. Main improvements: replace N+1 full-history hydration, cache bounded current-corpus lexical statistics, prefilter active authorized revision IDs, and batch indexing with short shard critical sections.

The revised median embedding span was 2.249 ms, dense-local search 0.164 ms, keyword scoring 0.607 ms, fusion 0.435 ms and payload/canonical result checking 0.110 ms. Spans are diagnostic; independent medians are not additive. Corpus preparation is effectively zero on a valid warm corpus cache. See [baseline](search-baseline.json) and [revised measurements](search-next.json).

A real authenticated HTTP-loopback sample over the small isolated demo corpus measured p50 2.848 ms, p95 2.976 ms and p99 3.057 ms across 200 timed requests. This has a different corpus and is not directly comparable with the 1,000-record benchmark. Response serialization and complete request timing are included in the separate [HTTP report](http-profile.json). The UI labels backend and round-trip timings separately.

The 10,000-record stress sample (200 timed queries, one run) measured p50 101.478 ms, p95 105.671 ms, p99 112.964 ms, indexing 183.464 s and peak RSS 257.34 MiB. Its estimated corpus size exceeded the 32 MiB cache allowance, so corpus preparation returned to the query path (median 71.975 ms). This is an explicit performance limit, not a 5 ms result. All records remained eligible; no 10k truncation was used. See [stress results](search-10k.json). Tail estimates from 200 requests are provisional.

Five store/model/shard reloads within a single process measured 61–89 ms initialization and 2.49–3.87 ms first queries with uncontrolled OS caches. During concurrent indexing, 54 foreground searches had p95 48.836 ms; see [lifecycle profile](lifecycle-profile.json). A 30-second idle sample found each isolated process below 0.24% of one logical CPU. Edge A RSS was 420.17 MiB, Edge B 260.05 MiB; the full central-plus-two-device runtime occupied approximately 1.06 GiB of logical file space. These are not a five-minute idle test, a single-device disk budget result, or browser-inclusive memory figures. See [resource profile](resource-profile.json).

## Verified behavior

- 45 backend tests passed, including actual Edge/ONNX retrieval, 50 separate synthetic paraphrase cases, schema-1 migration, deletion-during-embedding, stale central acknowledgement, final scope/current-head filtering, >10k eligibility, session expiry/activity, bounded gateway input and cooperative worker shutdown.
- Ruff passed and TypeScript/Vite production build passed.
- Three Playwright tests passed using the locked dependencies and matching Chromium: capture/search/inspect/delete/sharing, mobile keyboard focus, and delayed search after sign-out. Desktop and mobile screenshots were inspected locally.
- Three live isolated two-device rehearsals passed. Each covered actual gateway outage, local capture/search, queued approved edits, conflict convergence/resolution, private-record exclusion, deletion visibility, mTLS rejection, invalid-signature rejection, real central Qdrant projection and signed snapshot activation. See [latest rehearsal](local-integration-results.json).
- Two real retrieval tests passed inside a macOS sandbox denying network access. This is stronger than Python socket monkeypatching and is still limited to that test process and those tests.
- Full isolated vault stop/unmount/start passed. A cold encrypted sparsebundle backup was checksummed and mounted read-only; all three profiles' memories, revisions, outbox, inbox and audit history matched. See [recovery results](recovery-results.json).
- Python and npm dependency audits reported no known vulnerabilities at the time of verification. This is not an independent security audit.
- GitHub checks must pass on the final PR before merge. CI covers static/backend security regression, frontend build, and existing documentation/schema validation; live macOS vault and browser rehearsal remain local checks.

## Scope and limitations

P0 correctness, security, performance and interface work is implemented, with selected P1 improvements: bounded lexical corpus caching, 10k stress testing and snapshot download outside the search lock. The plan's explicitly deferred post-hackathon items are not represented as completed.

The Snapdragon 720G/8 GB device is assumed to be Android and is not attached to this environment. Physical slow-device backend validation, native Android packaging, a protected Linux runtime adapter, portable key recovery/rotation, OS-lock integration, an independent security review, and whole-volume rollback protection remain pending. Phone-browser access to a Mac would not satisfy on-device execution.

The benchmark's five category templates and the separate synthetic paraphrase tests do not establish clinical accuracy. No diverse external held-out clinical dataset was used. Model/shard reload measurements are not a flushed OS-cache boot test. No 30-minute device-offline or one-hour soak claim is made. Index/cache bounds and longer-lived queues need larger, more varied operational evaluation before any real-data use.

The source remains an informational synthetic prototype, not an autonomous diagnostic product. Private observations and embeddings stay local; only reviewed synthetic reference variants can synchronize. The original user's vault and records were not used by mutation/rehearsal tests.
