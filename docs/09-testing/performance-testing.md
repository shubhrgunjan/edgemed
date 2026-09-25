# Performance and Benchmark Testing Specifications

- **Document Version:** 1.0.0
- **Status:** Complete / Target Benchmarks
- **Date:** 2026-09-26

---

## 1. Benchmarking Targets on Reference Hardware

> [!NOTE]
> All metrics listed below represent **TARGETS**, not measured achievements. They will be formally validated during Phase 13 using automated pytest-benchmark scripts.
> Reference Platform: AMD Ryzen 5 5500U, 8 GB RAM, Linux.

| Benchmark Suite | Workload Description | Target Benchmark Metric | Status |
| :--- | :--- | :--- | :--- |
| **`BENCH-01: In-Process Search`** | Dense + BM25 RRF query over 10,000 local points | `< 5.0 ms` response time | **TARGET** |
| **`BENCH-02: CPU Embedding`** | FastEmbed single-string encoding (128 tokens) | `< 18.0 ms` encoding latency | **TARGET** |
| **`BENCH-03: Batch Ingestion`** | Ingest 500 clinical observations in a single loop | `> 50 points/second` | **TARGET** |
| **`BENCH-04: Working Memory`** | Resident Set Size (RSS) under 20,000 points | `< 450 MB` total RAM | **TARGET** |
| **`BENCH-05: Cold Start`** | App launch to HTTP 200 ready state | `< 2.5 seconds` | **TARGET** |
| **`BENCH-06: Graph Traversal`** | 3-hop recursive neighborhood CTE query in SQLite | `< 2.0 ms` query execution | **TARGET** |
