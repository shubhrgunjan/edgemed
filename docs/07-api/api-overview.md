# API Overview and Contract Guidelines

- **Document Version:** 1.0.0
- **Status:** Complete / Contract Specification (No Implementation in Phase 0)
- **Date:** 2026-09-26
- **Lead API Architect:** Team LEX (Code Cubicle 6.0 — PS03)

---

## 1. Design Standards and Protocols

The EdgeMed API provides the communication contract between the local browser interface (Memory Lab) and the underlying Python edge runtime.
- **Protocol:** HTTP/1.1 and HTTP/2 over local loopback (`http://127.0.0.1:8000`), with WebSocket support on `/api/ws/status`.
- **Data Exchange Format:** Strict JSON (`application/json`) adhering to OpenAPI 3.1.0 specifications.
- **Contract Enforcement:** All request and response structures are mapped 1-to-1 with Pydantic v2 schemas.
- **Offline Autonomy Invariant:** Every endpoint documented herein functions 100% locally when disconnected from the cloud, with the exception of explicit cloud-forwarded sync calls which return clear status indicators.

---

## 2. Global Status Endpoints

### 2.1 `GET /api/status`
- **Purpose:** Quick health check returning system uptime, version, and connectivity state.
- **Method / Path:** `GET /api/status`
- **Authentication:** None (Local Loopback).
- **Request:** None.
- **Response (200 OK):**
  ```json
  {
    "status": "healthy",
    "version": "1.0.0",
    "phase": "PHASE_0_ARCHITECTURE",
    "network_state": "STATE_OFFLINE",
    "uptime_seconds": 3600.4
  }
  ```
- **Errors:** 500 Internal Server Error (Engine failure).
- **Offline Behavior:** Fully functional offline.

### 2.2 `GET /api/stats`
- **Purpose:** High-level metrics for dashboard cards.
- **Method / Path:** `GET /api/stats`
- **Request:** None.
- **Response (200 OK):**
  ```json
  {
    "total_memories": 1240,
    "active_patients": 48,
    "conflicting_memories": 3,
    "pending_sync_items": 14,
    "shard_point_count": 1240,
    "graph_node_count": 860,
    "graph_edge_count": 1420
  }
  ```
- **Errors:** 500 Internal Server Error.
- **Offline Behavior:** Fully functional offline.

### 2.3 `GET /api/system`
- **Purpose:** Hardware and storage diagnostics for the Edge Inspector.
- **Method / Path:** `GET /api/system`
- **Request:** None.
- **Response (200 OK):**
  ```json
  {
    "cpu_usage_percent": 12.4,
    "memory_working_set_mb": 348.2,
    "memory_system_total_mb": 8192.0,
    "disk_free_gb": 42.6,
    "qdrant_edge_shards": {
      "mutable_shard_points": 42,
      "immutable_shard_points": 1198,
      "directory_size_mb": 18.4
    },
    "sqlite_database": {
      "wal_size_mb": 2.1,
      "db_size_mb": 14.8
    }
  }
  ```
- **Errors:** 500 Internal Server Error.
- **Offline Behavior:** Fully functional offline.
