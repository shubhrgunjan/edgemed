# Vector Memory Specification: Qdrant Edge Shard Engine

- **Document Version:** 1.0.0
- **Status:** Complete / Technical Architecture
- **Date:** 2026-09-26
- **Lead Research Engineer:** Team LEX (Code Cubicle 6.0 — PS03)

---

## 1. Engine Configuration and Vector Topology

Vector memory is powered directly by in-process **Qdrant Edge** (`qdrant-edge-py`). It executes dense and sparse vector queries locally against memory-mapped filesystem segments.

### Shard Configuration Blueprint
- **Collection / Shard Name:** `clinical_memories`
- **Dense Vector Name:** `clinical_dense`
  - **Dimension:** `384` (Matches `BAAI/bge-small-en-v1.5`)
  - **Distance Metric:** `Cosine`
  - **Storage:** On-disk mmap with scalar quantization (`int8`)
- **Sparse Vector Name:** `clinical_sparse` (BM25 token weights)
  - **Distance Metric:** `Dot`
  - **Storage:** On-disk inverted index
- **Payload Indexing:**
  - `patient_id` (Keyword index)
  - `category` (Keyword index)
  - `privacy_level` (Keyword index)
  - `timestamp` (Integer index for range queries)
  - `confidence` (Float index)

---

## 2. The Dual-Shard Mechanics

```
  WRITE PATH (Local Ingestion)          READ PATH (Search Query)
               │                                   │
               ▼                                   ▼
      ┌─────────────────┐                 ┌─────────────────┐
      │  MUTABLE SHARD  │◄────────────────┤   DUAL QUERY    │
      │   (Unindexed /  │                 │    EXECUTOR     │
      │   Flat Buffer)  │                 └────────┬────────┘
      └─────────────────┘                          │
               │ Server Sync                       │
               ▼                                   ▼
      ┌─────────────────┐                 ┌─────────────────┐
      │ IMMUTABLE SHARD │◄────────────────┤  MERGE & FUSION │
      │  (HNSW Indexed  │                 │   (RRF Engine)  │
      │  from Server)   │                 └─────────────────┘
      └─────────────────┘
```

1. **Mutable Shard (Unindexed / Flat Buffer):**
   - Receives all local writes and updates created on the edge device.
   - Bypasses HNSW graph building on the edge CPU, ensuring writes complete in `<5ms`.
   - Searched via exact flat scan (negligible overhead for local working sets `<10,000` points).
2. **Immutable Shard (Server Mirror):**
   - Replicated from the central Qdrant Server via differential partial snapshots.
   - Contains pre-built HNSW graph indices and compressed quantization structures.
3. **Dual Query Execution:**
   - Searches are dispatched concurrently to both shards; candidate points are merged using Reciprocal Rank Fusion (RRF) and deduplicated.
