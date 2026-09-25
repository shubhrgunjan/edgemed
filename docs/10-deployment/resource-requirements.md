# Resource Requirements Specification

- **Document Version:** 1.0.0
- **Status:** Complete / Hardware Constraint Baseline
- **Date:** 2026-09-26

---

## 1. Minimal and Recommended Hardware

| Resource | Minimum Specification | Target Benchmark Specification (Developer Machine) |
| :--- | :--- | :--- |
| **Processor** | Dual-core x86_64 or ARM64 (e.g. Raspberry Pi 5) | AMD Ryzen 5 5500U (6 Cores / 12 Threads) |
| **System Memory** | 4.0 GB RAM | 8.0 GB DDR4 System RAM |
| **Storage** | 10 GB available SSD space | 20+ GB NVMe SSD space |
| **GPU / VRAM** | None required (100% CPU inference) | Integrated AMD Radeon Graphics |
| **Operating System** | Linux (Ubuntu 22.04+, Debian 12+, Fedora 38+) | Linux (Kernel 6.x) |

---

## 2. Resource Envelopes under Load

```
┌────────────────────────────────────────────────────────┐
│             RESOURCE CONSUMPTION ENVELOPES             │
├───────────────────────┬──────────────┬─────────────────┤
│ Subsystem             │ Working RAM  │ CPU Utilization │
├───────────────────────┼──────────────┼─────────────────┤
│ FastEmbed ONNX        │ ~120 MB      │ 35-50% (1 core) │
│ Qdrant Edge (10k pts) │ ~45 MB       │ <5% (idle/read) │
│ SQLite WAL Engine     │ ~15 MB       │ <2%             │
│ FastAPI Web Backend   │ ~45 MB       │ <5%             │
│ Chromium Browser (UI) │ ~450 MB      │ 10-15% (canvas) │
├───────────────────────┼──────────────┼─────────────────┤
│ TOTAL PLATFORM LOAD   │ ~675 MB RAM  │ <25% CPU Avg    │
└───────────────────────┴──────────────┴─────────────────┘
```
The architecture guarantees that even under simultaneous vector querying, graph traversal, and batch point ingestion, the platform leaves $>6.5\text{ GB}$ of RAM free for the host operating system.
