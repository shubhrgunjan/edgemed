# Requirements Traceability Matrix (RTM)

- **Document Version:** 1.0.0
- **Status:** Complete / Authoritative Matrix
- **Date:** 2026-09-26
- **Lead Systems Engineer:** Team LEX (Code Cubicle 6.0 — PS03)

---

## 1. Overview and Purpose

This Requirements Traceability Matrix guarantees complete end-to-end alignment between the primary hackathon requirements established in **Code Cubicle 6.0 Problem Statement 03 (PS03)**, our system specifications, architectural components, planned implementation modules, acceptance tests, and future live demonstration evidence.

---

## 2. Master Traceability Matrix

| PS03 Core Requirement | System Requirement ID | Architecture Component | Planned Implementation Module | Acceptance Test | Live Demo Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Searchable semantic memory on edge device** | `REQ-EDGE-001` | Local Vector Engine | `app.memory.vector_store.EdgeVectorStore` wrapping `qdrant-edge-py` | `TEST-001`, `TEST-003` | Operator searches medical concepts via UI and receives ranked results in <1ms without internet. |
| **Low-latency vector/hybrid search without network access** | `REQ-EDGE-002`, `REQ-PERF-001` | In-Process EdgeShard & FastEmbed | `app.search.hybrid_search.HybridSearchEngine` (Dense + BM25 RRF) | `TEST-004`, `TEST-015` | Live search execution with real-time latency timer displaying <5ms search and zero network packets. |
| **Intermittent connectivity & continued offline operation** | `REQ-EDGE-003`, `REQ-SYNC-001` | Connectivity Manager & Local SQLite WAL | `app.sync.connectivity.ConnectivityManager` & `app.storage.sqlite_store` | `TEST-004`, `TEST-005` | Sever Ethernet/Wi-Fi connection; interface confirms offline state; all ingest and retrieval features remain functional. |
| **Dynamic decisions: local vs. synchronized info** | `REQ-GOV-001`, `REQ-PRIV-001` | Memory Governor & Privacy Firewall | `app.intelligence.governor.MemoryGovernor` & `app.intelligence.firewall.PrivacyFirewall` | `TEST-007`, `TEST-008` | Governor assigns `LOCAL`, `SYNC_CANDIDATE`, or `EXPIRE`; Privacy Firewall redacts or blocks PHI. |
| **Synchronization between edge and central Qdrant Server** | `REQ-SYNC-002`, `REQ-SYNC-003` | Sync Queue & Snapshot Engine | `app.sync.replicator.QdrantServerReplicator` (dual-write + snapshots) | `TEST-006`, `TEST-007`, `TEST-012` | Re-enable network; outbound queue drains; central server confirms ingestion; snapshot diffs propagate. |
| **Evolving local memory, updates, & conflicting information** | `REQ-MEM-003`, `REQ-MEM-004` | Contradiction State Machine & Consolidation | `app.memory.contradiction.ContradictionEngine` & `app.memory.consolidation.ConsolidationWorker` | `TEST-009`, `TEST-010`, `TEST-014` | Ingest conflicting clinical statements; system marks `CONFLICTING` without overwriting; visual review in UI. |
| **User-facing inspection of memory & provenance** | `REQ-UI-002`, `REQ-UI-005` | Memory Explorer & Provenance DAG | `frontend.components.MemoryExplorer` & `frontend.components.ProvenanceViewer` | `TEST-011` | Click any memory card to view origin device, timestamp, actor, parent links, and content hash. |
| **User-facing inspection of search results & explainability**| `REQ-UI-003`, `REQ-EXPL-001` | Search HUD & Score Breakdown | `frontend.components.SemanticSearch` & `frontend.components.ScoreBreakdown` | `TEST-015` | Search view displays dense score, sparse BM25 score, RRF rank, and entity matches with highlight chips. |
| **User-facing synchronization status** | `REQ-UI-006`, `REQ-SYNC-004` | Sync Monitor & Network HUD | `frontend.components.SyncMonitor` & WebSocket status feed | `TEST-006`, `TEST-012` | Real-time status indicator showing queue depth, transfer rate, last sync timestamp, and server health. |
| **Meaningful edge-to-cloud AI workflow** | `REQ-ARCH-001`, `REQ-ROUT-001` | Adaptive Query Router & Cross-Device Sync | `app.intelligence.router.QueryRouter` & multi-device snapshot loop | `TEST-013`, `TEST-015` | Edge captures observation; cloud builds HNSW index; second edge receives updated guidance shard. |

---

## 3. Verification and Audit Strategy

Every pull request during the upcoming implementation phases must link to at least one Requirement ID from this matrix. CI workflows will enforce that all Acceptance Tests specified above pass before any implementation milestone is deemed complete.
