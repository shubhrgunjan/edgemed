# ADR-003: Tripartite Hybrid Memory Model (Vector + Graph + Temporal)

- **Status:** Approved / Core Architectural Tenet
- **Date:** 2026-09-26
- **Author:** Team LEX (Code Cubicle 6.0 — PS03)

## Context
Clinical decision-support and medical data management require more than generic similarity matching. Medical understanding demands precise relational topology (contraindications, drug-condition relationships) and causal progression (symptoms evolving over time).

## Problem
Relying solely on vector embeddings loses critical relational structure and chronological evolution:
1. Vectors struggle with medical negation and strict multi-hop relationships.
2. Flat vector indexes treat a diagnosis from 5 years ago identically to a finding recorded 10 minutes ago unless manually post-filtered.
3. Pure knowledge graphs lack fuzzy semantic recall and natural-language tolerance.

## Options Considered
1. **Vector-Only Memory (Qdrant Edge alone):** High semantic flexibility, but severe topological blindness and hallucination risks.
2. **Graph-Only Memory (Neo4j / NetworkX alone):** High topological rigor, but poor handling of unstructured notes, fuzzy clinical phrasing, and semantic discovery.
3. **Tripartite Model (Vector + Graph + Temporal):**
   - **Vector Memory (Qdrant Edge):** Fuzzy similarity, semantic concept matching, and unstructured note retrieval.
   - **Knowledge Graph (SQLite Relational Edges):** Explicit clinical ontology (`Patient`, `Condition`, `Medication`, `Procedure`, `Observation`) with validated edges (`HAS_CONDITION`, `TREATED_WITH`, `CONTRADICTS`).
   - **Temporal Memory (Event Timeline):** Longitudinal state progression (`Observation → Follow-up → Treatment → Clinical Outcome`).

## Decision
Adopt the **Tripartite Memory Model**, fusing Qdrant Edge vector similarity, SQLite-backed relational knowledge graphs, and event-based temporal decay.

## Consequences
- **Positive:** Robust clinical decision-support with both semantic discoverability and rigorous relationship enforcement; prevents semantic confusion between contradictory treatments.
- **Negative:** Increased schema complexity; requires synchronization across vector IDs, graph node IDs, and temporal event records.
