# Integration Testing Specifications

- **Document Version:** 1.0.0
- **Status:** Complete
- **Date:** 2026-09-26

---

## 1. Scope of Integration Tests

Integration tests validate multi-module execution flows against temporary disk directories:
- `test_ingest_and_query_flow`: Ingests a clinical note through FastAPI endpoint; confirms vector point is stored in Qdrant Edge mutable shard and query returns it within top-1 candidate.
- `test_sqlite_wal_persistence`: Tests transactional commits across `kg_nodes`, `temporal_events`, and `sync_queue` under concurrent async requests.
- `test_shard_snapshot_roundtrip`: Exports a shard snapshot via `EdgeShard.unpack_snapshot()`, re-mounts it in an isolated directory, and validates point count and search parity.
- `test_contradiction_graph_edge`: Ingests two conflicting notes; asserts that SQLite `kg_edges` contains a directed `CONTRADICTS` relation.
