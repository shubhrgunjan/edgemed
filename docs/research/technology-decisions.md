# Technology Evaluation and Decision Analysis

- **Document Version:** 1.0.0
- **Status:** Complete / Authoritative Reference
- **Date:** 2026-09-26
- **Lead Architect:** Team LEX (Code Cubicle 6.0 — PS03)

---

## 1. Executive Summary

This document formalizes the evaluation, tradeoffs, and selections for the **EdgeMed** technology stack. The hardware profile of the deployment and development platform serves as the binding constraint:
- **Processor:** AMD Ryzen 5 5500U (6 Cores, 12 Threads, x86_64)
- **Host Memory:** 8.0 GB DDR4 RAM
- **Graphics:** Integrated AMD Radeon Graphics (Shared memory, no dedicated VRAM)
- **Operating System:** Linux (Kernel 6.x)
- **Operational Requirement:** 100% offline autonomy without cloud dependence for core retrieval.

---

## 2. Technology Stack Evaluation Matrix

### 2.1 Backend Core Framework
- **Selected:** **Python 3.11+ / FastAPI with Uvicorn**
- **Alternatives Considered:** Go (Gin), Rust (Axum), Node.js (Express)
- **Analysis:**
  - *FastAPI Advantages:* Native Python ecosystem compatibility with AI runtimes (`qdrant-edge-py`, `fastembed`, `onnxruntime`, `pydantic v2`). Pydantic v2 provides Rust-backed validation speed. Async I/O architecture allows concurrent handling of local vector queries, WebSocket sync status events, and HTTP endpoints.
  - *Disadvantages:* Higher base memory footprint than compiled Go/Rust (~45 MB baseline).
  - *Hardware Impact:* Consumes <60 MB RAM; Ryzen 5 5500U easily handles thousands of req/sec in local loopback.
  - *Decision:* Approved. Developer velocity and seamless integration with `qdrant-edge-py` outweighs raw compiled throughput.

### 2.2 Local Vector Database Engine
- **Selected:** **Qdrant Edge (`qdrant-edge-py`)**
- **Alternatives Considered:** ChromaDB (duckdb/clickhouse backed), SQLite-VSS / SQLite-Vec, Faiss
- **Analysis:**
  - *Qdrant Edge Advantages:* Written in Rust with native Python bindings; zero external daemon processes; operates directly on local filesystem directory; supports dense vector search, sparse BM25 vectors, payload filtering, and snapshot synchronization with central Qdrant Server.
  - *Disadvantages:* Upstream is in Beta; lacks higher-level graph or temporal abstractions (addressed by EdgeMed application layers).
  - *Hardware Impact:* Consumes ~45-75 MB RAM for 50,000 vectors; utilizes memory-mapped files to minimize OS memory duplication.
  - *Decision:* Mandatory selection per PS03 core specifications.

### 2.3 Local Embedding Engine
- **Selected:** **FastEmbed (`BAAI/bge-small-en-v1.5` / `all-MiniLM-L6-v2`) via ONNX Runtime**
- **Alternatives Considered:** Hugging Face `sentence-transformers` with PyTorch, Ollama Nomic-Embed, Cloud Embedding APIs
- **Analysis:**
  - *FastEmbed Advantages:* Completely decouples embeddings from PyTorch (saves ~1.5 GB disk space and ~800 MB runtime RAM). Uses lightweight ONNX Runtime with quantized integer models (INT8/FP16).
  - *Latency Target:* Ryzen 5 5500U CPU encodes a 128-token clinical snippet in **12–16 ms** using multi-threaded CPU inference.
  - *Memory Target:* Model weights consume **~120 MB RAM** on disk and in working set.
  - *Disadvantages:* Limited to supported quantized ONNX checkpoints.
  - *Decision:* Approved. Fastest CPU inference engine with lowest memory footprint.

### 2.4 Local Structured State & Knowledge Graph Storage
- **Selected:** **SQLite 3 with Write-Ahead Logging (WAL)**
- **Alternatives Considered:** Embedded RocksDB, Embedded Neo4j / Kùzu, Flat JSON files
- **Analysis:**
  - *SQLite Advantages:* Universal ACID guarantees; built into Python standard library; zero installation overhead; handles relational entities, explicit graph edge adjacency lists, temporal event journals, sync queues, and cryptographic provenance trails.
  - *Graph Implementation:* Relational adjacency table (`edges` with `source_id`, `target_id`, `relation_type`, `properties_json`, `timestamp`) with recursive Common Table Expressions (CTEs) for multi-hop neighborhood traversal.
  - *Disadvantages:* Not a native graph database; deep graph traversals (>4 hops) can incur SQL join overhead (unnecessary for local clinical decision support).
  - *Hardware Impact:* Single-file database; <15 MB RAM working cache.
  - *Decision:* Approved. Unmatched stability and operational zero-maintenance.

### 2.5 Frontend Visualization & User Interface
- **Selected:** **React 18 / TypeScript with Vite**
- **Alternatives Considered:** Vanilla HTML/JS, Streamlit, Electron
- **Analysis:**
  - *React/TS Advantages:* Strong typing aligns with OpenAPI/JSON schemas; component lifecycle matches reactive WebSocket synchronization streams; rich ecosystem for graph and timeline visualization.
  - *Disadvantages:* Requires Node build toolchain during development.
  - *Hardware Impact:* Browser renders client-side; Vite dev server starts in <300 ms.
  - *Decision:* Approved for the future implementation phase.

### 2.6 Graph Visualization Engine
- **Selected:** **Cytoscape.js (primary) / React Flow (fallback)**
- **Alternatives Considered:** D3.js force-directed graph, Vis.js, Obsidian canvas clone
- **Analysis:**
  - *Cytoscape.js Advantages:* Highly optimized for interactive graph manipulation, compound nodes, edge styling, filtering, and high-performance physics-directed layouts (CoSE/Cola); handles up to 2,000 nodes at 60 FPS in canvas.
  - *Disadvantages:* Imperative canvas API requiring React wrapper component.
  - *Decision:* Approved for knowledge graph and provenance explorer views.

### 2.7 Central Vector Database Server (Cloud Node)
- **Selected:** **Qdrant Server (Containerized via Docker / Cloud Instance)**
- **Alternatives Considered:** Milvus, Weaviate, Pinecone
- **Analysis:**
  - *Qdrant Server Advantages:* Exact API parity and snapshot compatibility with Qdrant Edge; native shard snapshot creation and segment recovery API.
  - *Hardware Impact:* Server instance runs remotely or in a separate lightweight container on the development machine.
  - *Decision:* Approved. Enables native snapshot-based partial segment replication.

---

## 3. Total System Memory Budget on AMD Ryzen 5 5500U (8 GB RAM)

```
┌─────────────────────────────────────────────────────────────┐
│              EDGE HOST MEMORY BUDGET ALLOCATION             │
├────────────────────────────────┬──────────────┬─────────────┤
│ Component                      │ RAM Baseline │ Peak Memory │
├────────────────────────────────┼──────────────┼─────────────┤
│ Linux OS & System Services     │ 1.8 GB       │ 2.2 GB      │
│ EdgeMed Backend (FastAPI)      │ 45 MB        │ 75 MB       │
│ FastEmbed Runtime (bge-small)  │ 120 MB       │ 180 MB      │
│ Qdrant Edge In-Process Shard   │ 50 MB        │ 110 MB      │
│ SQLite WAL Engine              │ 15 MB        │ 30 MB       │
│ Chromium Browser (UI Frontend) │ 450 MB       │ 850 MB      │
├────────────────────────────────┼──────────────┼─────────────┤
│ TOTAL SYSTEM LOAD              │ ~2.5 GB      │ ~3.5 GB     │
│ AVAILABLE HEADROOM             │ 5.5 GB       │ 4.5 GB      │
└────────────────────────────────┴──────────────┴─────────────┘
```

The system operates comfortably within less than 50% of the host machine's physical memory, guaranteeing no swap thrashing or process evictions during sustained offline operation.
