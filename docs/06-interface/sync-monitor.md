# Screen Specification: Synchronization Monitor & Queue Telemetry

- **Document Version:** 1.0.0
- **Status:** Complete / Design Specification
- **Date:** 2026-09-26

---

## 1. Purpose
The **Sync Monitor** provides real-time transparency into edge-to-cloud replication, displaying the status of the SQLite outbound queue, network connection quality, recent sync transactions, and partial snapshot updates.

---

## 2. Screen Specifications

- **Layout:** Two-tier dashboard (Top: Real-time network telemetry gauges and queue status pills; Bottom: Tabbed log of outgoing point uploads and incoming snapshot syncs).
- **Components:**
  - `NetworkHealthHUD`: Latency meter (RTT ms), jitter gauge, packet loss indicator, and connection status badge (`ONLINE`, `OFFLINE`, `DEGRADED`).
  - `QueueSummaryMetrics`: Counters for `Pending`, `Syncing`, `Committed`, and `Failed (Retrying)` items.
  - `SyncLogTable`: Stream of point uploads showing Memory ID, Privacy Tier, Destination Server, Status, and Timestamp.
  - `ManualSyncControls`: Buttons to "Force Queue Flush", "Check Server Manifest", or "Simulate Network Drop".
- **Data Displayed:**
  - Live queue depth, bytes transmitted, server handshake confirmation, last sync timestamp.
- **User Actions:**
  - Click "Force Sync" -> Immediately attempts to drain pending queue items if online.
  - Click "Retry Failed" -> Resets retry counters on failed queue items.
  - Click a sync item -> Inspects raw JSON payload transmitted to the server.
- **Backend Requirements:**
  - `GET /api/sync/status`: Aggregated queue stats.
  - `POST /api/sync`: Manually triggers synchronization drain.
  - `GET /api/ws/status`: WebSocket stream pushing updates every 1s.
- **Loading States:** Shimmer pulse over status pills during initial WebSocket connection.
- **Error States:** Red warning box if cloud endpoint returns 401 Unauthorized or 503 Service Unavailable.
- **Offline Behavior:** 100% operational offline. Displays queue depth accumulating in local SQLite; confirms network requests are safely paused.
