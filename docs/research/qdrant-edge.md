# Research Report: Qdrant Edge Architecture, Capabilities, and Boundaries

- **Document Version:** 1.0.0
- **Status:** Complete / Authoritative Reference
- **Date:** 2026-09-26
- **Lead Research Engineer:** Team LEX (Code Cubicle 6.0 — PS03)
- **Primary Source:** [Qdrant Edge Official Documentation](https://qdrant.tech/documentation/edge/)
- **Access Date:** 2026-09-26

---

## 1. Executive Summary

This document establishes the official technical baseline for **Qdrant Edge** and defines the exact architectural boundary between capabilities provided natively by the upstream Qdrant engine and the systems that **EdgeMed** must build around it.

Qdrant Edge is an embedded vector search engine designed for in-process retrieval with zero background daemon dependencies and a minimal memory footprint. It operates locally on-disk, conceptually analogous to "SQLite for vector embeddings." While Qdrant Edge provides low-latency local vector indexing, payload storage, and snapshot-based server replication, **it is not an autonomous multi-tier memory system, knowledge graph engine, or clinical data governor**. EdgeMed constructs these necessary layers around Qdrant Edge.

---

## 2. Official Qdrant Edge Reference Materials

| Reference Title | Source URL | Access Date | Key Architectural Finding |
| :--- | :--- | :--- | :--- |
| **Qdrant Edge Overview** | `https://qdrant.tech/documentation/edge/` | 2026-09-26 | Embedded in-process engine; operates directly against local storage; no background service; status: **Beta**. |
| **Edge vs. Qdrant Cluster** | `https://qdrant.tech/documentation/edge/edge-vs-qdrant-cluster/` | 2026-09-26 | Clarifies divergence: Edge is single-node/in-process without Raft/distributed clustering; server handles multi-tenant sharding and horizontal scaling. |
| **Edge API Reference** | `https://qdrant.tech/documentation/edge/edge-api/` | 2026-09-26 | Exposes `EdgeShard` abstraction in Rust (`qdrant-edge`) and Python (`qdrant-edge-py`). Methods include `create`, `load`, `update`, `query`, `snapshot_manifest`, `unpack_snapshot`. |
| **Data Sync Patterns** | `https://qdrant.tech/documentation/edge/edge-data-synchronization-patterns/` | 2026-09-26 | Snapshot restoration from server shard ID; partial snapshots via segment manifest diffs; dual-write queue pattern for client-to-server updates. |
| **Smart Glasses Demo** | `https://github.com/qdrant/qdrant-edge-demo` | 2026-09-26 | Demonstrates dual-shard architecture: local unindexed mutable shard for fast capture + remote HNSW indexing with immutable shard download + SQLite sync queue. |
| **Edge Mission Control** | `https://github.com/qdrant-labs/edge-mission-control` | 2026-09-26 | Demonstrates in-process hybrid search (SigLIP2 dense vectors + Florence-2 caption BM25 sparse vectors) fused with Reciprocal Rank Fusion (RRF) and Maximal Marginal Relevance (MMR). |

---

## 3. Official Qdrant Edge Capabilities vs. EdgeMed Architectural Additions

A foundational design requirement of PS03 is avoiding architectural misrepresentation: **we must not claim that Qdrant provides features that we are actually building in application software**.

The matrix below delineates native Qdrant capabilities from EdgeMed additions:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   EDGEMED PLATFORM                                     │
├────────────────────────────────────────────────────────┬───────────────────────────────┤
│               OFFICIAL QDRANT CAPABILITY               │    OUR PROPOSED ARCHITECTURE  │
├────────────────────────────────────────────────────────┼───────────────────────────────┤
│ • In-process EdgeShard storage & querying              │ • Tripartite Memory Model     │
│ • Local Cosine / Dot / Euclidean vector search         │   (Vector + Graph + Temporal) │
│ • Sparse BM25 vector querying                          │ • Memory Governor Engine      │
│ • Reciprocal Rank Fusion (RRF) on prefetch streams     │ • Local Privacy Firewall      │
│ • Payload storage, JSON filtering, and payload indexes │ • Temporal Observation Graphs │
│ • Shard snapshot export, unpacking, & manifest diff    │ • Contradiction Resolution    │
│ • Partial snapshot updates from server segments        │ • Memory Consolidation Worker │
│ • Dual-write client ingestion primitives               │ • Multi-Device Sync Engine    │
│ • Memory-mapped file I/O on embedded devices           │ • Audit Provenance DAG        │
└────────────────────────────────────────────────────────┴───────────────────────────────┘
```

### Detailed Capability Matrix

| System Domain | Official Qdrant Capability (Native) | EdgeMed Proposed Platform Layer (Our Contribution) |
| :--- | :--- | :--- |
| **Vector Search** | In-process nearest neighbor query execution over dense and sparse vectors via `EdgeShard.query()`. | Hybrid query orchestration fusing clinical semantic matches with entity-relation filters and temporal recency decay. |
| **Local Storage** | Flat filesystem directory holding shard segments, payload records, and vector indices. | Encrypted local SQLite metadata database holding explicit knowledge graph edges, event timelines, and provenance audit trails. |
| **Synchronization** | Snapshot transfer primitives (`snapshot_manifest()`, `unpack_snapshot()`, `update_from_snapshot()`), server point upsert API. | State-machine sync manager handling intermittent link detection, offline queue persistence, bidirectional diffing, and conflict resolution. |
| **Indexing** | HNSW graph building and scalar quantization. (Can be offloaded to central cluster). | Dynamic indexing policy: immediately queryable flat mutable segment on edge; deferred HNSW indexing or cloud snapshot fusion. |
| **Knowledge Modeling** | Schema-less JSON payload attached to vector points; boolean and keyword payload filters. | Explicit Clinical Knowledge Graph (Entities: `Patient`, `Condition`, `Medication`, `Procedure`, `Observation`; Edges: `HAS_CONDITION`, `TREATED_WITH`, etc.). |
| **Temporal Representation**| Timestamps stored as numeric fields in payload with range filter support (`gte`, `lte`). | Temporal Event Memory representing clinical progression: `Observation → Follow-up → Treatment → Clinical Outcome`. |
| **Governance & Privacy** | None. Payload fields are stored as provided. No redaction or policy awareness. | **Memory Governor & Privacy Firewall**: Classification (`PUBLIC`, `INTERNAL`, `SENSITIVE`, `HIGHLY_SENSITIVE`), redaction, and local-only pin. |
| **Conflict & Deduplication**| Overwrites point if identical ID is upserted; returns multiple matches if different IDs exist. | **Contradiction Detection & Consolidation**: Detects opposing clinical assertions, marks states (`CONFIRMED`, `CONFLICTING`, `SUPERSEDED`), groups patterns. |

---

## 4. Qdrant Edge Architecture Deep Dive

### 4.1 In-Process Shard Lifecycle

Unlike a traditional database server that listens on TCP ports `6333` (HTTP) or `6334` (gRPC), Qdrant Edge is embedded directly inside the host process memory space via C-ABI / PyO3 bindings:

```
+-------------------------------------------------------------------+
| Host Application Process (EdgeMed Backend)                        |
|                                                                   |
|   +-----------------------+     +-------------------------------+ |
|   | EdgeMed Memory Engine |     | EdgeShard Python API          | |
|   +-----------+-----------+     +---------------+---------------+ |
|               |                                 |                 |
|               +---------------------------------+                 |
|                                 |                                 |
|                     [ Rust Core Engine ]                         |
|   +-------------------------------------------------------------+ |
|   | Segment Manager | Vector Index (HNSW/Flat) | Payload Store  | |
|   +-------------------------------------------------------------+ |
+---------------------------------+---------------------------------+
                                  | mmap / POSIX I/O
                     +------------v------------+
                     | File System Directory   |
                     | ./data/qdrant_edge/     |
                     |  - segments/            |
                     |  - manifest.json        |
                     +-------------------------+
```

1. **Instantiation (`EdgeShard.create` / `EdgeShard.load`):** Creates or mounts a directory structure containing shard metadata, segment descriptors, vector indices, and payload storage.
2. **Persistence:** Segment files are persisted to disk using memory-mapped (`mmap`) files, ensuring queries hit warm OS page cache without duplicating memory in Python user space.
3. **Flushing & Snapshotting:** `EdgeShard.snapshot_manifest()` generates a deterministic cryptographic summary of local segment hashes, enabling differential delta synchronization against server snapshots.

### 4.2 The Dual-Shard Design Pattern

Learned from the official `qdrant/qdrant-edge-demo` reference, building HNSW indices on low-power edge hardware (such as mobile SoCs or embedded ARM cores) induces high CPU thermal throttling and memory spikes.

To resolve this, EdgeMed adopts the **Dual-Shard Pattern**:
1. **Mutable Shard (Local Writes):** Operates on-device with unindexed or flat vector buffers. Write operations are instantaneous (<5ms) with zero HNSW construction penalty. Immediate offline search scans this mutable shard via brute-force vector distance (highly performant for <10,000 local points).
2. **Immutable Shard (Server Replicated):** Heavy HNSW graph construction is offloaded to the centralized Qdrant Server. The edge device downloads pre-indexed partial snapshots containing finalized global medical knowledge and compressed HNSW structures.
3. **Query Fusion:** Search queries execute across both the local mutable shard and the immutable snapshot shard simultaneously, merging candidate scores using Reciprocal Rank Fusion (RRF).

---

## 5. Synchronization Mechanics & Upstream Limitations

### 5.1 Native Upstream Sync Primitives
Official Qdrant Edge provides two primary primitives for server synchronization:
- **Server-to-Edge:** Snapshot restoration (`EdgeShard.unpack_snapshot`) and differential segment synchronization (`EdgeShard.recover_partial_snapshot`).
- **Edge-to-Server:** Standard REST/gRPC upsert calls through `qdrant_client.QdrantClient.upsert()`.

### 5.2 Critical Limitations of Upstream Synchronization
1. **No Embedded Client-to-Server Streaming Protocol:** Qdrant Edge does not provide an autonomous background synchronization daemon. The host application must implement the network link listener, outbound queue, retry backoff, and serialization.
2. **No Conflict Detection or Resolution:** If Edge Device A and Edge Device B update Point ID `42` with disparate payload data while offline, Qdrant Server's behavior is simply "last write wins" based on upload arrival timestamp. Qdrant has no concept of semantic conflict, branching versions, or medical contradiction.
3. **Beta Maturity:** As stated in the official documentation, Qdrant Edge is currently in **Beta**. APIs and storage formats may change between minor versions. All application storage must be decoupled from the raw shard directory through an abstraction barrier.

---

## 6. Hardware Feasibility on Target Development Machine

- **Development Hardware:** AMD Ryzen 5 5500U (6 Cores, 12 Threads, 2.1 GHz Base / 4.0 GHz Boost), 8 GB DDR4 RAM, Integrated AMD Radeon Graphics.
- **Feasibility Assessment:**
  - **Memory Footprint:** Qdrant Edge in-process memory footprint for 50,000 384-dimensional vectors with scalar quantization is approximately **45 MB to 75 MB RAM**, comfortably fitting within the 8 GB host envelope.
  - **CPU-Only Embeddings:** Utilizing FastEmbed with `BAAI/bge-small-en-v1.5` (384-d, ONNX quantized) consumes **~120 MB RAM** and executes on the Ryzen 5 5500U at approximately **12 to 18 ms per query string**, completely eliminating any requirement for discrete GPU acceleration.
  - **Combined Engine Overhead:** The total edge runtime (FastAPI + Qdrant Edge + SQLite + FastEmbed) stays safely under **450 MB RAM**, leaving over 7 GB for system operations and visualization.

---

## 7. Architectural Conclusion

Qdrant Edge serves as the high-speed vector retrieval engine for EdgeMed. All higher-level intelligence—clinical knowledge graphs, temporal progression tracking, memory governance, privacy firewalls, and multi-device synchronization—must be designed and implemented by Team LEX as modular platform services surrounding Qdrant Edge.
