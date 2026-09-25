# Functional Requirements Specification

- **Document Version:** 1.0.0
- **Status:** Complete / Authoritative Matrix
- **Date:** 2026-09-26
- **Lead Systems Engineer:** Team LEX (Code Cubicle 6.0 — PS03)

---

## 1. Functional Requirements Matrix

| ID | Requirement Description | Source | Priority | Component | Acceptance Test | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-FUNC-001** | Ingest structured and unstructured synthetic clinical notes and convert them to vector embeddings. | PS03 | Critical | Ingestion Pipeline | `TEST-001` | Ingest note, verify 384-d vector generation and payload storage. |
| **REQ-FUNC-002** | Execute hybrid semantic and keyword search across local memory records. | PS03 | Critical | Hybrid Search Engine | `TEST-004`, `TEST-015` | Query with natural language; verify dense cosine + BM25 RRF score fusion. |
| **REQ-FUNC-003** | Construct explicit knowledge graph entities (`Patient`, `Condition`, `Medication`, `Procedure`, `Observation`) from ingested notes. | Architecture | High | Knowledge Graph Engine | `TEST-001`, `TEST-011` | Ingest clinical record; verify entity nodes and relationship edges created in SQLite. |
| **REQ-FUNC-004** | Record longitudinal temporal event sequences (`Observation → Follow-up → Treatment → Outcome`). | Architecture | High | Temporal Memory Engine | `TEST-001`, `TEST-010` | Verify event timeline persistence and chronological ordering. |
| **REQ-FUNC-005** | Evaluate incoming memories using multi-factor scoring to determine retention state (`LOCAL`, `SYNC_CANDIDATE`, `EXPIRE`). | PS03 | Critical | Memory Governor | `TEST-007`, `TEST-008` | Submit memory; verify calculated score and assigned lifecycle state. |
| **REQ-FUNC-006** | Inspect outbound payloads against privacy classification tiers (`PUBLIC`, `INTERNAL`, `SENSITIVE`, `HIGHLY_SENSITIVE`) and apply redactions. | PS03 | Critical | Privacy Firewall | `TEST-008` | Attempt to sync `HIGHLY_SENSITIVE` record; verify transmission is blocked. |
| **REQ-FUNC-007** | Detect conflicting medical assertions and transition records to a `CONFLICTING` state without data destruction. | PS03 | High | Contradiction Engine | `TEST-009` | Ingest contradictory diagnosis; verify both records exist with `CONTRADICTS` relation. |
| **REQ-FUNC-008** | Consolidate repeated observations into higher-confidence summary records while preserving lineage links. | PS03 | Medium | Consolidation Worker | `TEST-010` | Ingest 5 repeated vitals; verify single consolidated record with 5 parent references. |
| **REQ-FUNC-009** | Maintain an immutable cryptographic provenance log for all memory transformations. | PS03 | High | Provenance Tracker | `TEST-011` | Query memory provenance; verify parent hashes, device ID, and timestamp lineage. |
| **REQ-FUNC-010** | Provide real-time sync status monitoring via WebSocket. | PS03 | Medium | Sync Monitor Service | `TEST-006`, `TEST-012` | Stream connection status, queue depth, and throughput to client UI. |
