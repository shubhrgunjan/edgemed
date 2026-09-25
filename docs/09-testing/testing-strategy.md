# Testing Strategy & Verification Blueprint

- **Document Version:** 1.0.0
- **Status:** Complete / Authoritative Test Strategy
- **Date:** 2026-09-26
- **Lead Quality Engineer:** Team LEX (Code Cubicle 6.0 — PS03)

---

## 1. Testing Philosophy: Verify Before Implementation

In accordance with leading software engineering practices, EdgeMed specifies all critical test cases, fixtures, assertions, and acceptance gates **prior to the implementation phase**.

The test suite is structured into four distinct test categories:
1. **Unit Tests (`tests/unit`):** Validate isolated algorithmic logic (Memory Governor scoring, FastEmbed dimension checks, Privacy Firewall regex filters, Contradiction state transitions).
2. **Integration Tests (`tests/integration`):** Validate multi-component pipelines (FastAPI -> Qdrant Edge in-process shard write -> SQLite WAL commit).
3. **Offline & Network Resiliency Tests (`tests/offline`):** Validate mock network cuts, queue accumulation, and link recovery.
4. **End-to-End System Tests (`tests/e2e`):** Validate full user scenarios mimicking the Code Cubicle 6.0 hackathon demo.

---

## 2. Master Test Suite Matrix (TEST-001 through TEST-015)

| Test ID | Test Scenario | Category | Preconditions | Input / Stimulus | Expected Assertion & Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`TEST-001`** | **Insert Memory** | Unit / Int | Shard loaded | POST `/api/memories` with valid note | HTTP 201; 384-d vector stored in Qdrant Edge mutable shard; SQLite rows created. |
| **`TEST-002`** | **Restart Application** | Int / System | 100 memories stored | Execute `kill -9`; re-invoke FastAPI app | Shard re-mounts without error; WAL journal recovers in `< 2.5s`. |
| **`TEST-003`** | **Retrieve Memory Post-Restart** | Int / System | App restarted | GET `/api/memories/{id}` for pre-restart point | HTTP 200; verbatim content and vector match pre-restart state. |
| **`TEST-004`** | **Search While Completely Offline** | Offline | Physical network disabled | POST `/api/search` with natural-language query | Resolves in `< 5ms`; returns ranked candidates with zero network packets. |
| **`TEST-005`** | **Create Memory While Offline** | Offline | Physical network disabled | POST `/api/memories` with new triage observation | Point immediately searchable locally; item placed in SQLite `sync_queue` (PENDING). |
| **`TEST-006`** | **Reconnect to Network** | Sync / Resil | 5 offline queue items | Re-enable network gate | Heartbeat probe verifies cloud health; background worker initiates queue drain. |
| **`TEST-007`** | **Synchronize Permitted Memory** | Sync | Device online | Queue item with privacy tier `PUBLIC` | Transmits to Qdrant Server; receives HTTP 200; queue status transitions to `COMMITTED`. |
| **`TEST-008`** | **Block Sensitive Memory** | Privacy | Device online | Ingest note with privacy tier `HIGHLY_SENSITIVE` | Stored in local Qdrant Edge shard; NOT added to `sync_queue`; zero cloud bytes. |
| **`TEST-009`** | **Detect Conflicting Memories** | Memory Logic | Patient has confirmed allergy | Ingest order for contraindicated antibiotic | Both records transition to `CONFLICTING`; linked by `CONTRADICTS` edge; alert raised. |
| **`TEST-010`** | **Consolidate Repeated Memories**| Memory Logic | 4 similar vitals in 2h window | Trigger POST `/api/memories/consolidate` | Creates 1 consolidated summary record; parent IDs linked; constituent points archived. |
| **`TEST-011`** | **Preserve Provenance** | Audit / Memory| Memory created & modified | GET `/api/memories/{id}` | Provenance DAG contains creator device ID, UTC timestamps, source hash, parent IDs. |
| **`TEST-012`** | **Handle Failed Synchronization** | Sync / Resil | Server returns 500 error | Queue worker attempts upload | Item status remains `PENDING`; retry counter increments; exponential backoff applied. |
| **`TEST-013`** | **Handle Duplicate Synchronization**| Sync / Idemp | Point already on server | Worker replays same sync item | Server acknowledges idempotently; no duplicate points or version collisions occur. |
| **`TEST-014`** | **Handle Stale Information** | Conflict | Local record has version 3 | Server sends snapshot with version 1 | Server update rejected as stale; local version remains authoritative. |
| **`TEST-015`** | **Run Hybrid Query** | Search / AI | Online connection | POST `/api/search` with `mode: "AUTO"` | Query dispatches locally and upstream; RRF merges candidates; attribution chips returned. |
