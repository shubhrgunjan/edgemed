# Technical Glossary and Domain Terminology

- **Document Version:** 1.0.0
- **Status:** Complete
- **Date:** 2026-09-26

---

## Terms and Definitions

- **Edge Shard (`EdgeShard`):** The primary storage abstraction in Qdrant Edge. A self-contained directory managing vector segments, payload indexes, and point storage that operates in-process without network daemons.
- **Mutable Shard:** A local Edge Shard configured without heavy HNSW indexing for rapid, low-overhead write operations directly on the edge device.
- **Immutable Shard:** A replicated Edge Shard restored from a central Qdrant Server snapshot containing pre-built HNSW graph indices for global clinical knowledge.
- **Reciprocal Rank Fusion (RRF):** An algorithmic method for combining multiple ranked search result lists (e.g., dense vector matches and sparse BM25 keyword matches) into a single unified score without requiring score calibration.
- **Memory Governor:** The EdgeMed component that evaluates the importance, confidence, recurrence, freshness, and privacy level of local memories to assign retention states (`LOCAL`, `SYNC_CANDIDATE`, `EXPIRE`).
- **Privacy Firewall:** The security gatekeeper that inspects payload fields prior to network synchronization, redacting identifiers or completely blocking sensitive clinical notes based on classification tiers (`PUBLIC`, `INTERNAL`, `SENSITIVE`, `HIGHLY_SENSITIVE`).
- **Tripartite Memory:** The cooperative architecture uniting vector semantic retrieval (Qdrant Edge), explicit relational knowledge graphs (SQLite entities and edges), and temporal event progressions (longitudinal event logs).
- **Contradiction Lifecycle:** The state machine governing conflicting medical assertions, transitioning through `CONFIRMED`, `CONFLICTING`, `OUTDATED`, `SUPERSEDED`, and `REQUIRES_REVIEW` states without silent data loss.
- **Memory Consolidation:** The background process of clustering repeated observations over time to synthesize high-confidence summary records while preserving complete provenance links back to raw constituent records.
- **Provenance DAG:** A Directed Acyclic Graph tracking the lineage of every memory record, including creation device, capturing user, source document hash, contributing memories, and modification history.
- **Offline-First:** An architectural paradigm where all application workflows execute locally against embedded storage by default, treating network synchronization as an opportunistic background enhancement.
