# Synchronization Architecture Specification

- **Document Version:** 1.0.0
- **Status:** Complete
- **Date:** 2026-09-26

---

## 1. The Complete End-to-End Synchronization Lifecycle

```
    LOCAL CREATION (Clinician enters observation)
          ↓
    LOCAL VALIDATION (Pydantic Schema & Type Checks)
          ↓
    LOCAL STORAGE (Qdrant Edge Mutable Shard + SQLite Graph/Events)
          ↓
    GOVERNANCE (Memory Governor assigns LOCAL / SYNC_CANDIDATE / EXPIRE)
          ↓
    SYNC QUEUE (Enqueued in SQLite persistent queue if SYNC_CANDIDATE)
          ↓
    PRIVACY CHECK (Privacy Firewall redacts PII/PHI or blocks HIGHLY_SENSITIVE)
          ↓
    CLOUD SYNCHRONIZATION (Asynchronous batch upsert to central Qdrant Server)
          ↓
    SERVER VALIDATION (Server validates schema, updates global index & HNSW)
          ↓
    OTHER EDGE DEVICES (Peer devices receive updates via partial snapshot recovery)
```

---

## 2. Upstream Qdrant vs. EdgeMed Architectural Responsibilities

To maintain engineering clarity, the boundary between native Qdrant functionality and EdgeMed application logic is strictly defined:

```
┌────────────────────────────────────────────────────────────────────────┐
│ WHAT QDRANT PROVIDES (Native Engine)                                   │
├────────────────────────────────────────────────────────────────────────┤
│ • In-process EdgeShard storage and reading                             │
│ • Shard snapshot unpacking (`EdgeShard.unpack_snapshot`)               │
│ • Manifest generation (`EdgeShard.snapshot_manifest`)                  │
│ • Differential partial snapshot recovery (`recover_partial_snapshot`)  │
│ • Server REST/gRPC endpoint for point upserts                          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Orchestrated by
┌───────────────────────────────────▼────────────────────────────────────┐
│ WHAT EDGEMED BUILDS (Application Platform)                             │
├────────────────────────────────────────────────────────────────────────┤
│ • Persistent SQLite Sync Queue with retry backoff & state tracking     │
│ • Connectivity Manager (heartbeat, latency probing, link listener)     │
│ • Privacy Firewall (classification, scrubbing, and local pinning)      │
│ • Contradiction State Machine & Multi-master Conflict Resolution       │
│ • Cross-device snapshot scheduling and background pollers              │
│ • Real-time WebSocket status broadcasts to user interface             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Asynchronous Batch Synchronization Mechanics

1. **Persistent Enqueuing:** When a memory receives a `SYNC_CANDIDATE` verdict from the Memory Governor and passes the Privacy Firewall, it is committed to SQLite table `sync_queue` in the same transaction as local metadata.
2. **Batch Poller:** A dedicated async worker queries `SELECT * FROM sync_queue WHERE status = 'PENDING' LIMIT 10`.
3. **Idempotent Upsert:** The worker executes `qdrant_client.upsert(collection_name, points)`. Because IDs are deterministic UUIDs, duplicate transmission creates no side effects.
4. **Acknowledgment:** Upon receiving HTTP 200 from the server, the queue status transitions to `'COMMITTED'`.
5. **Partial Snapshot Pull:** Every N minutes (or on manual trigger), the edge device calls `server.snapshot_manifest()`, computes the delta against local segments, downloads the minimal `.snapshot` archive, and applies it via `edge_shard.update_from_snapshot()`.
