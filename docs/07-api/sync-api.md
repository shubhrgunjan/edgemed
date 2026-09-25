# API Specification: Synchronization Endpoints

- **Document Version:** 1.0.0
- **Status:** Complete / Contract Specification
- **Date:** 2026-09-26

---

## 1. `GET /api/sync/status`
- **Method:** `GET`
- **Path:** `/api/sync/status`
- **Purpose:** Retrieve the current state of the outbound synchronization queue, network link quality, and last successful sync timestamp.
- **Response (200 OK):**
  ```json
  {
    "network_state": "STATE_ONLINE",
    "ping_rtt_ms": 42.5,
    "queue_depth": {
      "pending": 3,
      "syncing": 0,
      "committed": 142,
      "failed": 0
    },
    "last_successful_sync_at": "2026-09-26T12:00:15Z",
    "cloud_server_url": "https://qdrant-central.hospital.internal:6333"
  }
  ```
- **Offline Behavior:** 100% operational offline. Returns `network_state: "STATE_OFFLINE"` and current local queue counters.

---

## 2. `POST /api/sync`
- **Method:** `POST`
- **Path:** `/api/sync`
- **Purpose:** Manually trigger an immediate queue drain and differential snapshot sync pass.
- **Request Body (Optional):**
  ```json
  {
    "force": true,
    "batch_size": 10
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "status": "completed",
    "points_uploaded": 3,
    "points_failed": 0,
    "partial_snapshots_applied": 1,
    "elapsed_seconds": 0.42
  }
  ```
- **Errors:** 503 Service Unavailable (If triggered while strictly offline).
- **Offline Behavior:** Returns HTTP 503 with detail: `"Network is offline. Synchronization queued for automatic retry upon link reconnection."`

---

## 3. `WebSocket /api/ws/status`
- **Protocol:** `WebSocket`
- **Path:** `/api/ws/status`
- **Purpose:** Pushes real-time telemetry (network state, queue depth, CPU/RAM stats) to the browser every 1,000ms.
- **Message Format:** Standard JSON telemetry payload matching `SystemTelemetry` schema.
- **Offline Behavior:** The WebSocket connects over local loopback (`ws://127.0.0.1:8000`), operating flawlessly even when the external physical network is unplugged.
