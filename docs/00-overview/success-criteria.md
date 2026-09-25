# Success Criteria and Evaluation Metrics

- **Document Version:** 1.0.0
- **Status:** Complete
- **Date:** 2026-09-26

---

## 1. Quantitative Target Metrics

The following metrics represent engineering targets designed for the AMD Ryzen 5 5500U, 8 GB RAM platform:

| Metric Category | Target Indicator | Engineering Benchmark | Target Status |
| :--- | :--- | :--- | :--- |
| **Local Search Latency** | In-process vector query (dense + BM25) | `< 5.0 ms` for 10k points | **TARGET** |
| **Local Embedding Latency** | FastEmbed `bge-small-en-v1.5` on CPU | `< 18.0 ms` per clinical text snippet | **TARGET** |
| **Memory Ingestion Latency** | Embed + Qdrant Edge write + SQLite write | `< 30.0 ms` total pipeline | **TARGET** |
| **Working Memory Footprint** | Combined runtime RAM (FastAPI + Qdrant + Embed) | `< 450 MB` total resident memory | **TARGET** |
| **Application Startup Time** | Cold boot to ready state with 10k points | `< 2.5 seconds` | **TARGET** |
| **Offline Recovery Time** | Network reconnect to queue drain initiation | `< 1.0 second` | **TARGET** |
| **Sync Throughput** | Batch point upsert over local Wi-Fi | `> 250 points/second` | **TARGET** |

---

## 2. Qualitative Acceptance Criteria

1. **Uninterrupted Offline Functionality:** A user can sever the network connection, create new patient observations, execute hybrid semantic searches, traverse the knowledge graph, and evaluate memory governance with zero error modals or degraded UI states.
2. **Transparent Provenance:** For every memory retrieved, the user interface can display the full provenance audit path (creator device, timestamp, source hash, parent records, transformation chain).
3. **Verified Privacy Boundary:** Ingesting a record flagged as `HIGHLY_SENSITIVE` results in verified local persistence while remaining completely absent from the outbound synchronization queue and central server index.
4. **Contradiction Visibility:** Ingesting contradictory statements results in an explicit visual indicator in the UI displaying both records in a `CONFLICTING` state, with neither record erased.
