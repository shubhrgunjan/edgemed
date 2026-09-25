# Edge Architecture Specification

- **Document Version:** 1.0.0
- **Status:** Complete
- **Date:** 2026-09-26

---

## 1. Edge Node Hardware Profile & Constraints

The edge node architecture is specifically engineered to operate on resource-constrained commodity portable hardware:
- **Reference Platform:** AMD Ryzen 5 5500U Mobile Processor (6 Cores / 12 Threads, 2.1 GHz Base, 4.0 GHz Boost)
- **Host Memory:** 8.0 GB DDR4 System RAM
- **Storage:** NVMe / SSD local storage (Fast POSIX read/write)
- **Graphics / Acceleration:** Integrated AMD Radeon Vega 7 (No dedicated VRAM, CPU-only inference execution)
- **Network Interface:** Wi-Fi 802.11ac / Ethernet with frequent hardware-level disconnects.

---

## 2. In-Process Edge Engine Lifecycle

EdgeMed avoids running separate client/server processes on the edge device. The FastAPI backend, Qdrant Edge engine (`EdgeShard`), FastEmbed ONNX runtime, and SQLite storage all reside within a **single operating system process**:

```
+--------------------------------------------------------------------------+
| Linux Operating System (x86_64)                                          |
|                                                                          |
|   +------------------------------------------------------------------+   |
|   | EdgeMed Host Process (Python 3.11 / Uvicorn / Asyncio)           |   |
|   |                                                                  |   |
|   |  [ FastAPI Endpoints ] <---> [ Context Fusion & Memory Governor] |   |
|   |                                       |                          |   |
|   |  +------------------------+  +--------+--------+  +------------+ |   |
|   |  | FastEmbed ONNX Runtime |  | Qdrant Edge Shard|  | SQLite C   | |   |
|   |  | (Quantized bge-small)  |  | (Rust Core / Py)|  | (WAL Mode) | |   |
|   |  +-----------+------------+  +--------+--------+  +-----+------+ |   |
|   +--------------|------------------------|-----------------|--------+   |
|                  |                        |                 |            |
|                  v                        v                 v            |
|       [ Model Weights File ]     [ Shard Directory ]  [ .sqlite DB ]     |
|       ./models/bge-small.onnx    ./data/qdrant_edge/  ./data/meta.db     |
+--------------------------------------------------------------------------+
```

### Advantages of In-Process Execution on Edge:
1. **Zero IPC / Network Overhead:** Querying the vector store involves direct memory function calls via C-bindings rather than TCP sockets or HTTP serialization.
2. **Deterministic Shutdown:** Shards and WAL files are flushed and locked synchronously during application shutdown hooks.
3. **Low Working Memory:** Elimination of multiple daemon processes prevents redundant runtime overhead, keeping the entire memory engine under **450 MB RAM**.
