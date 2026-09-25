# Synchronization Testing Specifications

- **Document Version:** 1.0.0
- **Status:** Complete
- **Date:** 2026-09-26

---

## 1. Scope of Synchronization Tests

Validates replication pipelines against a local test container of Qdrant Server:
- `test_reconnect_queue_drain`: Queues 10 items offline; enables mock connection; asserts queue drains and items transition to `COMMITTED`.
- `test_differential_snapshot_sync`: Simulates server-side point additions; verifies edge node calls `recover_partial_snapshot` and downloads only delta segment files.
- `test_idempotent_batch_retry`: Forces mock network drop on 9th point of 10-point batch; replays batch; asserts server collection contains exactly 10 points (no duplicates).
