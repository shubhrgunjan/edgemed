# Offline Testing Specifications

- **Document Version:** 1.0.0
- **Status:** Complete
- **Date:** 2026-09-26

---

## 1. Scope of Offline Tests

Offline tests verify system autonomy under simulated network blackouts:
- `test_zero_network_search`: Executes search suite with mock socket connections disabled; asserts zero network errors and latency $<5\text{ ms}$.
- `test_offline_queue_accumulation`: Creates 50 memories while offline; asserts that all 50 items enter SQLite table `sync_queue` with status `PENDING`.
- `test_unclean_kill_recovery`: Simulates power failure (`os._exit(1)` mid-write); reboots app; verifies SQLite WAL and Qdrant Edge shard recover cleanly without corrupt segments.
