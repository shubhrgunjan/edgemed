# Project Goals

- **Document Version:** 1.0.0
- **Status:** Complete
- **Date:** 2026-09-26

---

## 1. Primary Product Goals

1. **Sub-Millisecond In-Process Vector Search:** Embed Qdrant Edge in-process to achieve local semantic search latency under 5 milliseconds on consumer CPU hardware.
2. **Deterministic Offline Autonomy:** Guarantee that all primary user actions—memory creation, semantic search, knowledge graph exploration, and governance evaluations—execute completely without network access.
3. **Tripartite Memory Cooperativity:** Construct clean interfaces connecting Qdrant Edge vector similarity, SQLite-backed relational knowledge graphs, and temporal event progression.
4. **Intelligent Memory Governance:** Implement a multi-signal Memory Governor capable of scoring memories and determining whether they remain `LOCAL`, become `SYNC_CANDIDATE`, or `EXPIRE`.
5. **Privacy-Preserving Replication:** Deploy a four-tier Privacy Firewall between the local memory engine and the outbound sync queue to block or redact sensitive patient information.
6. **Non-Destructive Conflict Resolution:** Preserve medical audit trails by establishing an explicit Contradiction State Machine that flags opposing clinical facts rather than silently overwriting records.
7. **Comprehensive Inspection UI (Memory Lab):** Provide rich, interactive user-facing views for inspecting memory records, understanding hybrid search rankings, exploring graph topologies, and monitoring synchronization health.
