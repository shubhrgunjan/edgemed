# Synchronization Queue Specification

- **Document Version:** 1.0.0
- **Status:** Complete / Technical Architecture
- **Date:** 2026-09-26

---

## 1. Persistent Queue Architecture

The outbound sync queue is implemented as a dedicated SQLite table (`sync_queue`) with Write-Ahead Logging (WAL) enabled:
- **Crash Safety:** In the event of battery exhaustion or kernel panics, uncommitted queue items are recovered seamlessly upon reboot.
- **Transactional Consistency:** Enqueuing a sync item occurs in the exact same database transaction as the local memory creation.

---

## 2. Queue Schema and State Transitions

### Database Table DDL:
```sql
CREATE TABLE sync_queue (
    queue_id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id TEXT NOT NULL UNIQUE,
    payload_json TEXT NOT NULL,
    vector_dense_json TEXT NOT NULL,
    vector_sparse_json TEXT,
    privacy_tier TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('PENDING', 'SYNCING', 'COMMITTED', 'FAILED')),
    retry_count INTEGER NOT NULL DEFAULT 0,
    next_retry_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    committed_at TIMESTAMP
);

CREATE INDEX idx_sync_queue_status_retry ON sync_queue (status, next_retry_at);
```

---

## 3. Exponential Backoff and Jitter Strategy

When network timeouts or server 5xx errors occur, the queue worker applies truncated exponential backoff with full jitter to avoid the "thundering herd" problem across edge fleets:

$$T_{\text{wait}} = \min\left(T_{\text{max}}, T_{\text{base}} \cdot 2^{\text{retry\_count}}\right) \times \text{Uniform}(0.5, 1.5)$$

*Parameters:*
- $T_{\text{base}} = 2.0\text{ seconds}$
- $T_{\text{max}} = 300.0\text{ seconds}$ (5 minutes)
- After 10 consecutive failures, the item status transitions to `FAILED` and raises an alert on the Sync Monitor UI, requiring operator inspection.
