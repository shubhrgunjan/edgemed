# Comprehensive Implementation Roadmap: Phases 0 through 14

- **Document Version:** 1.0.0
- **Status:** Complete / Implementation Plan
- **Date:** 2026-09-26
- **Lead Software Architect:** Team LEX (Code Cubicle 6.0 — PS03)

---

## 1. Roadmap Overview

The implementation roadmap divides development into fifteen sequential, test-driven phases. Each phase establishes explicit inputs, deliverables, dependencies, acceptance gates, and risk mitigations.

---

## 2. Detailed Phase Breakdown

### PHASE 0: Architecture & Documentation (CURRENT)
- **Goal:** Establish the complete technical specification, schemas, contracts, research baselines, and ADRs as the single source of truth before writing application code.
- **Inputs:** PS03 Problem Statement, Qdrant Edge documentation, hardware profile.
- **Deliverables:** Complete Markdown documentation suite, formal JSON schemas, OpenAPI contracts, ADR-001 through ADR-010, GitHub issue/PR templates.
- **Dependencies:** None.
- **Acceptance Criteria:** 100% of documentation files created; zero fake implementations; all Mermaid diagrams pass syntax validation; status marked `NOT IMPLEMENTED YET`.
- **Risks:** Scope creep in planning; mitigated by establishing explicit non-goals.

### PHASE 1: Minimal Qdrant Edge Experiment (Spike)
- **Goal:** Verify `qdrant-edge-py` in-process shard instantiation, vector insertion, and query mechanics in an isolated Python script.
- **Inputs:** Phase 0 research document (`docs/research/qdrant-edge.md`).
- **Deliverables:** `scripts/spike_qdrant_edge.py`, benchmark log of memory footprint and read/write latency.
- **Dependencies:** Phase 0.
- **Acceptance Criteria:** Inserts 1,000 synthetic 384-d vectors; executes nearest-neighbor query; measures `<1ms` search latency on AMD Ryzen 5 5500U.
- **Risks:** Upstream beta bugs in Python bindings; mitigated by pinning tested version.

### PHASE 2: Local Embeddings
- **Goal:** Integrate FastEmbed with quantized ONNX models (`bge-small-en-v1.5`) for fast CPU encoding.
- **Inputs:** Phase 1 spike, FastEmbed docs.
- **Deliverables:** `app/intelligence/embedding.py` module, unit tests asserting 384-d output.
- **Dependencies:** Phase 1.
- **Acceptance Criteria:** Single-text encoding completes in `<18ms`; total RAM overhead `<150MB`.
- **Risks:** Memory spikes during batch tokenization; mitigated by enforcing batch limits.

### PHASE 3: Persistent Memory API
- **Goal:** Construct core FastAPI application with SQLite WAL metadata storage and Pydantic v2 validation.
- **Inputs:** `schemas/memory.schema.json`, `api/openapi/openapi.yaml`.
- **Deliverables:** CRUD endpoints `/api/memories`, `/api/memories/{id}`, `/api/status`.
- **Dependencies:** Phase 2.
- **Acceptance Criteria:** Ingestion persists vector to Qdrant Edge and metadata to SQLite in a single transaction; passes `TEST-001` and `TEST-002`.
- **Risks:** SQLite concurrency lock contention; mitigated by enforcing WAL mode.

### PHASE 4: Semantic Search Engine
- **Goal:** Implement hybrid dense and sparse BM25 retrieval with Reciprocal Rank Fusion (RRF).
- **Inputs:** Phase 3 persistence engine, `docs/04-intelligence/context-fusion.md`.
- **Deliverables:** `POST /api/search` endpoint, RRF fusion logic, score attribution payload.
- **Dependencies:** Phase 3.
- **Acceptance Criteria:** Hybrid search resolves in `<5ms` offline; returns explainability attribution chips (`TEST-004`, `TEST-015`).
- **Risks:** Disparate score distribution; mitigated by pure rank-based RRF.

### PHASE 5: Knowledge Graph Engine
- **Goal:** Build SQLite-backed explicit relational graph tables and recursive CTE neighborhood queries.
- **Inputs:** `docs/03-memory/knowledge-graph.md`, `schemas/entity.schema.json`, `schemas/relation.schema.json`.
- **Deliverables:** `GET /api/graph` endpoint, graph traversal helper functions.
- **Dependencies:** Phase 3.
- **Acceptance Criteria:** Ingesting notes creates typed nodes and edges; 3-hop traversal resolves in `<2ms`.
- **Risks:** Deep graph traversal performance; mitigated by capping depth at 3.

### PHASE 6: Temporal Memory Engine
- **Goal:** Implement longitudinal event progressions and category-aware temporal decay curves.
- **Inputs:** `docs/03-memory/temporal-memory.md`, `schemas/event.schema.json`.
- **Deliverables:** `app/memory/temporal.py`, timeline query filters.
- **Dependencies:** Phase 5.
- **Acceptance Criteria:** Event sequences chain chronologically; acute vitals decay over time while chronic allergies retain 1.0 weight.
- **Risks:** High clock drift on edge devices; mitigated by UTC normalization.

### PHASE 7: Memory Governor
- **Goal:** Implement the multi-factor scoring model to determine `LOCAL`, `SYNC_CANDIDATE`, and `EXPIRE`.
- **Inputs:** `docs/04-intelligence/memory-governor.md`.
- **Deliverables:** `app/intelligence/governor.py`, `POST /api/governance/evaluate/{id}` endpoint.
- **Dependencies:** Phase 3, Phase 6.
- **Acceptance Criteria:** Evaluates 8 signals; assigns valid verdict; critical records ($I \ge 0.85$) are never expired (`TEST-007`, `TEST-008`).
- **Risks:** Heuristic instability; mitigated by transparent explainability factor logging.

### PHASE 8: Privacy Firewall
- **Goal:** Implement the four-tier privacy classification and automated PII/PHI scrubbing engine.
- **Inputs:** `docs/04-intelligence/privacy-firewall.md`.
- **Deliverables:** `app/intelligence/firewall.py`, scrubbing regexes, classification middleware.
- **Dependencies:** Phase 7.
- **Acceptance Criteria:** `HIGHLY_SENSITIVE` records are blocked from sync; `SENSITIVE` records have identifiers scrubbed (`TEST-008`).
- **Risks:** Unidentified edge-case identifiers; mitigated by default-to-local mandate.

### PHASE 9: Offline / Online State Management
- **Goal:** Implement the asynchronous Connectivity Manager for link probing and state transitions.
- **Inputs:** `docs/02-architecture/offline-architecture.md`.
- **Deliverables:** `app/sync/connectivity.py`, WebSocket status broadcaster `/api/ws/status`.
- **Dependencies:** Phase 3.
- **Acceptance Criteria:** Detects physical network drop in `<500ms`; pushes status update to WebSocket; triggers zero blocking errors (`TEST-004`).
- **Risks:** False positive disconnections during high server load; mitigated by moving-average latency window.

### PHASE 10: Qdrant Server Synchronization
- **Goal:** Implement the SQLite persistent sync queue, dual-write batch upsert, and partial snapshot pull.
- **Inputs:** `docs/05-synchronization/synchronization.md`, `docs/05-synchronization/sync-queue.md`.
- **Deliverables:** `app/sync/replicator.py`, `GET /api/sync/status`, `POST /api/sync`.
- **Dependencies:** Phase 8, Phase 9.
- **Acceptance Criteria:** Drains queue in batches of 10 upon reconnection; verifies idempotent point upserts on central server (`TEST-006`, `TEST-007`).
- **Risks:** Network drop mid-batch; mitigated by atomic SQLite transaction marking.

### PHASE 11: Conflict Resolution & Contradiction Engine
- **Goal:** Implement the Contradiction State Machine and multi-master branching versioning.
- **Inputs:** `docs/03-memory/contradiction-resolution.md`, `docs/05-synchronization/conflict-resolution.md`.
- **Deliverables:** `app/memory/contradiction.py`, contradiction detection rules.
- **Dependencies:** Phase 10.
- **Acceptance Criteria:** Conflicting clinical assertions create a `CONTRADICTS` graph edge and enter `REQUIRES_REVIEW` state without data destruction (`TEST-009`).
- **Risks:** Overly sensitive contradiction triggers; mitigated by requiring exact entity collision and negative polarity.

### PHASE 12: Operator UI & Memory Laboratory
- **Goal:** Construct the React/TypeScript frontend with Cytoscape.js graph and full simulation HUD.
- **Inputs:** Screen specifications in `docs/06-interface/`.
- **Deliverables:** Single-page application with Dashboard, Memory Explorer, Search, Graph, Inspector, Sync Monitor, and Memory Lab.
- **Dependencies:** Phases 4, 5, 7, 10, 11.
- **Acceptance Criteria:** Cytoscape graph renders at 60 FPS; Memory Lab controls allow interactive offline simulation and conflict injection.
- **Risks:** Frontend bundle bloat; mitigated by lightweight Vite packaging.

### PHASE 13: Testing & Benchmarking Suite
- **Goal:** Execute the full automated test suite (`TEST-001` through `TEST-015`) and measure latency targets.
- **Inputs:** `docs/09-testing/testing-strategy.md`.
- **Deliverables:** Automated pytest suite, benchmark reports confirming $<5\text{ms}$ search and $<450\text{MB}$ RAM.
- **Dependencies:** Phase 12.
- **Acceptance Criteria:** 100% test pass rate across offline failover, queue drain, and conflict flows.
- **Risks:** Flaky network simulation tests; mitigated by deterministic local loopback mocking.

### PHASE 14: Hackathon Demo Hardening
- **Goal:** Polish the live demonstration narrative and synthetic clinical scenario walk-through for Code Cubicle 6.0 judges.
- **Inputs:** `examples/synthetic-patient-data.json`, Demo script.
- **Deliverables:** Rehearsed end-to-end walk-through showing online baseline -> network severance -> offline search -> observation ingestion -> reconnect -> privacy scrub -> cross-device sync -> graph visualization.
- **Dependencies:** Phase 13.
- **Acceptance Criteria:** Flawless live execution in under 5 minutes without crashes or unhandled exceptions.
- **Risks:** Live presentation glitches; mitigated by automated demo script fallback.
