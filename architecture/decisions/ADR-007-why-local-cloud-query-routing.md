# ADR-007: Adaptive Local / Cloud Query Routing Architecture

- **Status:** Proposed / Architectural Blueprint (Requires Latency & Confidence Profiling)
- **Date:** 2026-09-26
- **Author:** Team LEX (Code Cubicle 6.0 — PS03)

## Context
When an edge device has intermittent or variable connectivity, an incoming clinical search query should not blindly execute either exclusively on the edge or exclusively in the cloud.

## Problem
A static query strategy fails in field environments:
- Forcing cloud queries causes requests to fail or hang when network is degraded.
- Restricting queries strictly to local edge memory misses global hospital updates, clinical guidelines, and centralized research literature.
- Sending all queries to both edge and cloud simultaneously wastes battery and cellular bandwidth.

## Options Considered
1. **Local-Only Query Execution:** Simple, zero network use, but misses centralized institutional knowledge.
2. **Cloud-First Query Execution:** High latency, fragile under intermittent links, violates offline guarantees.
3. **Adaptive Query Router:** Evaluates query intent, privacy tier, network state, local retrieval confidence, and latency constraints to select `EDGE`, `CLOUD`, or `HYBRID` routing.

## Decision
Adopt an **Adaptive Query Routing** layer. When offline or handling high-sensitivity queries, routing is strictly `EDGE`. When online, low-confidence local queries (<0.72 similarity) or explicit global queries trigger a `HYBRID` search, merging local edge observations with central server knowledge.

## Consequences
- **Positive:** Minimizes network utilization; preserves battery and privacy; ensures graceful degradation to local retrieval whenever connectivity degrades.
- **Negative:** Introduces query routing heuristics and requires score normalization across edge and cloud candidate sets.
