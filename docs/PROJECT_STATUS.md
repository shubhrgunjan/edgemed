# Project Status: EdgeMed Memory Lab

- **Repository:** `edgemed`
- **Hackathon:** Code Cubicle 6.0
- **Team:** LEX
- **Problem Statement:** PS03 — AI-Powered Edge Memory & Intelligence Platform
- **Last Updated:** 2026-09-26

---

## Current Status

- **Current Phase:** `PHASE 0 — ARCHITECTURE & DOCUMENTATION`
- **Implementation:** `NOT STARTED` (Strictly prohibited during Phase 0)
- **Documentation:** `COMPLETE` (Authoritative technical baseline established)
- **Repository Readiness:** Ready for formal review and Phase 1 empirical spike initiation

---

## Open Architectural Questions

1. **Dual-Shard Segment Merge Boundary:** What is the optimal frequency or threshold (point count vs. time interval) for merging the local mutable unindexed shard with the incoming server-indexed immutable shard to maintain sub-millisecond retrieval latency without causing write lock contention?
2. **Quantization Precision vs. Medical Embedding Distinctions:** Does int8 scalar quantization in FastEmbed / Qdrant Edge preserve sufficient cosine angular distance to differentiate subtle clinical variations in medical descriptions, or is fp16 the minimum acceptable precision?
3. **Graph Neighborhood Traversal Depth in SQLite:** For local clinical contraindication checks, what is the maximum traversal depth required before recursive CTE queries impact sub-millisecond local response targets? (Initial hypothesis: 2 hops is sufficient for 95% of clinical rule checks).
4. **Contradiction Confidence Thresholds:** What cosine similarity and semantic polarity thresholds should trigger a `CONFLICTING` vs. `SUPERSEDED` state in the contradiction lifecycle engine?

---

## Technology Decisions Requiring Empirical Validation

1. **`qdrant-edge-py` Python Bindings Stability:** Validate in-process memory stability, segment file locking, and crash recovery behaviors across simulated unclean process kills on Linux x86_64.
2. **FastEmbed CPU Encoding Throughput on AMD Ryzen 5 5500U:** Formally benchmark multi-threaded batch embedding latency under simulated continuous clinical note ingestion.
3. **Partial Snapshot Download Payload Size:** Verify network transfer bytes and unpack durations when applying differential server snapshots over simulated 3G/2G throttled connections.
4. **Cytoscape.js Canvas Performance:** Verify that rendering 1,000+ clinical entities with compound nodes maintains 60 FPS on integrated Radeon graphics.

---

## Next Implementation Milestone

- **Next Phase:** `PHASE 1 — MINIMAL QDRANT EDGE EXPERIMENT`
- **Phase 1 Objective:** Construct an isolated Python script spike to instantiate an `EdgeShard`, insert 1,000 synthetic vector points with payloads, execute in-process ANN queries, verify disk directory layout, and test snapshot export/import mechanics.
