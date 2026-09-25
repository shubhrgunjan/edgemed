# Synchronization Protocol Specification

- **Document Version:** 1.0.0
- **Status:** Complete / Authoritative Protocol Specification
- **Date:** 2026-09-26
- **Lead Distributed Systems Engineer:** Team LEX (Code Cubicle 6.0 — PS03)

---

## 1. Protocol Architecture and Upstream Boundaries

The synchronization protocol coordinates state between disconnected edge devices and the central hospital Qdrant Server cluster.

### Clear Technology Division of Labor:
- **Upstream Qdrant Primitives:**
  - `EdgeShard.unpack_snapshot(path, dir)`: Restores a server snapshot into local disk structures.
  - `EdgeShard.snapshot_manifest()`: Generates local segment manifest hashes for differential comparison.
  - `EdgeShard.recover_partial_snapshot(...)`: Ingests differential segment delta files.
  - `qdrant_client.upsert(...)`: Transmits point vectors and payloads to server collections.
- **EdgeMed Application Layer (Our Code):**
  - Persistent SQLite transaction queue with retry backoff.
  - Network state monitor and heartbeat probe.
  - Multi-master conflict detection and contradiction state engine.
  - Differential snapshot scheduling and segment file integrity checking.
  - Privacy Firewall integration.

---

## 2. Bidirectional Synchronization Mechanics

```mermaid
sequenceDiagram
    autonumber
    participant EdgeApp as EdgeMed Host
    participant EdgeQueue as SQLite Sync Queue
    participant EdgeShard as Local Qdrant Edge Shard
    participant Server as Central Qdrant Server

    Note over EdgeApp,Server: 1. UPLINK: Edge to Central Server (Points Upload)
    EdgeApp->>EdgeQueue: Read batch of PENDING records (Limit: 10)
    EdgeQueue-->>EdgeApp: Return 10 PointStruct items
    EdgeApp->>Server: POST /collections/{name}/points (mTLS)
    alt Upload Succeeded (HTTP 200)
        Server-->>EdgeApp: Acknowledge Points Written
        EdgeApp->>EdgeQueue: UPDATE status = 'COMMITTED'
    else Network Lost or Timeout
        EdgeApp->>EdgeQueue: Increment retry_count, status = 'PENDING'
        Note over EdgeApp: Apply exponential backoff with jitter
    end

    Note over EdgeApp,Server: 2. DOWNLINK: Server to Edge (Differential Snapshot)
    EdgeApp->>EdgeShard: Get current snapshot manifest
    EdgeShard-->>EdgeApp: Return local manifest JSON
    EdgeApp->>Server: POST /collections/{name}/shards/{id}/snapshot/partial/create
    Server-->>EdgeApp: Stream partial.snapshot (Changed segments only)
    EdgeApp->>EdgeShard: EdgeShard.recover_partial_snapshot(...)
    EdgeShard-->>EdgeApp: Updated Shard Ready for Queries
```

---

## 3. Protocol Invariants: Idempotency and Versioning

1. **Idempotency Guarantee:** All point IDs are deterministic UUIDv5 hashes derived from namespace and origin content. Re-uploading the same point $N$ times produces the identical vector and payload state on the server without duplicate accumulation.
2. **Monotonic Versioning:** Every memory record maintains an integer `version` field. When an update is pushed, the version is incremented. The server and peer devices reject incoming updates whose version is less than or equal to the currently stored version, preventing stale re-writes.
3. **Partial Snapshot Efficiency:** Downlink replication downloads only the modified binary segments rather than the full multi-gigabyte collection snapshot, cutting transfer sizes by over 90% across bandwidth-constrained field links.
