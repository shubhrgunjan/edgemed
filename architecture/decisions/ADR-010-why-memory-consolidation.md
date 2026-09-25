# ADR-010: Memory Consolidation and Contradiction Resolution

- **Status:** Proposed / Architectural Blueprint (Requires Pipeline Tuning in Phase 6 & 11)
- **Date:** 2026-09-26
- **Author:** Team LEX (Code Cubicle 6.0 — PS03)

## Context
In continuous clinical workflows, redundant observations accumulate rapidly (e.g., vital sign checks every 30 minutes, repeated symptom complaints). Conversely, clinical updates often conflict directly with previous data (e.g., "Allergic to Penicillin" vs. "Penicillin allergy test negative, tolerated well").

## Problem
1. **Redundancy Inflation:** Storing 50 near-identical observations clutters retrieval results, degrades reciprocal rank fusion, and exhausts vector memory.
2. **Silent Overwrite Hazard:** Standard databases silently overwrite records when an update occurs. In clinical contexts, overwriting a previous finding destroys the temporal progression and provenance of the patient's care history.

## Options Considered
1. **Append-Only without Consolidation or Conflict Tracking:** Creates massive redundancy; queries return confusing duplicates; contradictory memories coexist without clear precedence.
2. **Last-Write-Wins Overwrite:** Erases historical diagnostic context; destroys medical audit trails.
3. **Consolidation Worker + Contradiction State Machine:**
   - **Consolidation:** Groups semantically similar observations within a temporal window into a single higher-confidence summary memory while preserving pointers to parent records.
   - **Contradiction Lifecycle:** When an opposing fact is detected, neither memory is erased. Both are marked with relational states (`CONFIRMED`, `CONFLICTING`, `SUPERSEDED`, `REQUIRES_REVIEW`), exposing explicit provenance for human clinician verification.

## Decision
Adopt **Memory Consolidation** and an explicit **Contradiction Lifecycle State Machine**. Repeated observations are consolidated, and contradictory assertions are flagged with explicit relations in the knowledge graph rather than silently deleted or overwritten.

## Consequences
- **Positive:** Reduces vector memory bloat; maintains clinical provenance integrity; highlights dangerous clinical contradictions explicitly to the user.
- **Negative:** Requires semantic clustering logic and contradiction heuristics; requires UI support for human review of conflicting memories.
