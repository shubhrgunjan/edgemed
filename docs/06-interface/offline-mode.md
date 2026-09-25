# Screen Specification: Offline Mode Experience & System Edge Inspector

- **Document Version:** 1.0.0
- **Status:** Complete / Design Specification
- **Date:** 2026-09-26

---

## 1. Purpose
The **Offline Mode Experience** specifies how the entire UI behaves during network loss. The **System / Edge Inspector** provides hardware-level telemetry regarding local Qdrant Edge shard directories, memory usage, and SQLite WAL health.

---

## 2. Global Offline UI States and Banners

When the Connectivity Manager reports `STATE_OFFLINE`:
- **Top Global Banner:** Displays a non-dismissible indigo badge: `[● OFFLINE MODE: 100% Autonomous — Local Qdrant Edge Active]`.
- **Search HUD:** Search inputs update subtitle to: `"Searching local shard directly (0ms network round-trip)"`.
- **Sync Badge:** Pulsing grey pill: `"Sync Paused — X items queued in SQLite"`.
- **Zero Blocking Modals:** No warning modals or connection error alerts interrupt the clinician. All operations commit locally and optimistically.

---

## 3. System / Edge Inspector View Specifications

- **Layout:** Two-column diagnostic dashboard.
- **Components:**
  - `ShardFileSystemTree`: Visual directory inspector showing `./data/qdrant_edge/` segments, manifest files, and byte sizes.
  - `DatabaseHealthCard`: SQLite WAL size, page count, and transaction log statistics.
  - `HardwareResourceMonitor`: Real-time CPU core activity, system RAM allocation (<450 MB working set), and disk space headroom.
- **Data Displayed:** Shard segment IDs, vector point counts (mutable vs. immutable shard), disk bytes used, RAM working set.
- **User Actions:**
  - Click "Flush Shard to Disk" -> Calls `edge_shard.flush()`.
  - Click "Optimize WAL" -> Runs SQLite `PRAGMA wal_checkpoint(TRUNCATE)`.
- **Backend Requirements:**
  - `GET /api/system`: Returns hardware and storage diagnostics.
- **Loading / Error States:** Instant local read; zero network latency.
- **Offline Behavior:** 100% operational offline.
