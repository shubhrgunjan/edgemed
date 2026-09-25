# Screen Specification: Memory Inspector & Provenance Viewer

- **Document Version:** 1.0.0
- **Status:** Complete / Design Specification
- **Date:** 2026-09-26

---

## 1. Purpose
The **Memory Inspector** is the deep-dive diagnostic interface for any individual memory point. It renders all 18 conceptual memory attributes, displays its exact provenance DAG, shows governance scoring factors, and exposes contradiction resolution actions.

---

## 2. Screen Specifications

- **Layout:** Two-pane detail view (Left: Memory Attributes & Content; Right: Interactive Provenance DAG & Governance Scorecard).
- **Components:**
  - `HeaderBanner`: Memory UUID, Category badge, Lifecycle State, Privacy Tier.
  - `ContentBox`: Full verbatim observation text with syntax-highlighted medical entities.
  - `AttributeGrid`: Key-value grid for confidence, importance, recurrence, freshness, version, device ID.
  - `GovernanceScorecard`: Visual progress bars showing multi-factor scores ($I, C, R, F, D$) and the Memory Governor's verdict explanation.
  - `ProvenanceDAGViewer`: Visual tree showing source document, extraction model, parent memories, and modification timeline.
  - `ConflictAdjudicationCard` (Rendered only if state is `CONFLICTING` / `REQUIRES_REVIEW`): Side-by-side comparison of conflicting records with "Accept", "Supersede", or "Incorporate" buttons.
- **Data Displayed:**
  - Complete JSON representation of the memory.
  - Full cryptographic audit path (SHA-256 hashes).
  - Outbound sync status (`PENDING`, `COMMITTED`).
- **User Actions:**
  - Click "Evaluate Governance" -> Manually re-runs Memory Governor scoring.
  - Click "Adjudicate Conflict" -> Submits clinician resolution decision.
  - Click "Export Provenance" -> Downloads cryptographic audit certificate.
- **Backend Requirements:**
  - `GET /api/memories/{id}`: Retrieves full tripartite record with provenance object.
  - `POST /api/governance/evaluate/{id}`: Triggers manual re-scoring.
- **Loading States:** Skeleton cards during ID fetch.
- **Error States:** 404 Not Found error card if memory ID does not exist in local shard.
- **Offline Behavior:** 100% operational offline.
