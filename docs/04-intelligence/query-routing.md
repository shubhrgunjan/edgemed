# Adaptive Query Routing Specification

- **Document Version:** 1.0.0
- **Status:** Complete / Proposed Algorithm
- **Date:** 2026-09-26
- **Lead Software Architect:** Team LEX (Code Cubicle 6.0 — PS03)

---

## 1. Architectural Purpose

In a distributed edge-cloud deployment, search queries cannot simply execute against a single static target. Forcing every query to the cloud wastes cellular bandwidth and fails offline; restricting every query to the local edge prevents the clinician from benefiting from global hospital updates or centralized medical literature.

The **Adaptive Query Router** evaluates query intent, network health, latency targets, and privacy classifications to dynamically select one of three execution modes:
1. **`EDGE` Mode:** Query resolves strictly against local in-process Qdrant Edge shards and local SQLite tables. Zero network packets emitted.
2. **`CLOUD` Mode:** Query dispatches to the central Qdrant Server (used only for explicit global medical research queries containing no local patient identifiers).
3. **`HYBRID` Mode:** Query executes concurrently against both local Edge shards and the central server; results are merged, deduplicated, and ranked via Reciprocal Rank Fusion.

---

## 2. Decision Factors and Evaluation Hierarchy

```mermaid
flowchart TD
    QUERY["Incoming Search Query"] --> NET{"Is Network Active?"}
    
    NET -->|NO (Offline)| ROUTE_EDGE["ROUTE: EDGE (100% Local)"]
    
    NET -->|YES (Online)| PRIV{"Query Contains Identifiable Patient PHI?"}
    
    PRIV -->|YES (Sensitive)| ROUTE_EDGE
    
    PRIV -->|NO (De-identified/General)| LAT{"Strict Latency Budget < 20ms?"}
    
    LAT -->|YES| ROUTE_EDGE
    
    LAT -->|NO| CONF{"Local Retrieval Confidence >= Threshold?"}
    
    CONF -->|YES (High Confidence)| ROUTE_EDGE
    CONF -->|NO (Low Local Confidence)| ROUTE_HYBRID["ROUTE: HYBRID (Edge + Cloud Fusion)"]
```

---

## 3. Proposed Query Routing Algorithm (Pseudocode)

```python
# PROPOSED ALGORITHM: Query Routing Decision Logic
# Note: Specification only. Do not implement in Phase 0.

def route_clinical_query(
    query_text: str,
    patient_id: Optional[str],
    network_state: NetworkState,
    latency_budget_ms: float,
    local_confidence_threshold: float = 0.72
) -> RouteDecision:
    """
    Evaluates runtime signals to determine optimal execution target.
    """
    # 1. Hard Invariant: If offline, route strictly to local edge
    if network_state.status in ("STATE_OFFLINE", "STATE_DEGRADED"):
        return RouteDecision(
            mode=ExecutionMode.EDGE,
            reason="Network offline or degraded. Enforcing local autonomy."
        )

    # 2. Hard Invariant: If query references specific patient records, preserve privacy
    if patient_id is not None or contains_phi_markers(query_text):
        return RouteDecision(
            mode=ExecutionMode.EDGE,
            reason="Query touches patient-specific privacy perimeter."
        )

    # 3. Latency Constraint: Acute emergency queries require sub-5ms local response
    if latency_budget_ms < 25.0:
        return RouteDecision(
            mode=ExecutionMode.EDGE,
            reason="Strict latency budget (<25ms) mandates in-process edge retrieval."
        )

    # 4. Probe Local Confidence
    local_probe_score = probe_local_top_similarity(query_text)
    
    # 5. If local confidence is sufficient, avoid unnecessary cloud round-trips
    if local_probe_score >= local_confidence_threshold:
        return RouteDecision(
            mode=ExecutionMode.EDGE,
            reason=f"High local confidence ({local_probe_score:.2f} >= {local_confidence_threshold})."
        )

    # 6. Default to Hybrid Fusion when online and local knowledge is sparse
    return RouteDecision(
        mode=ExecutionMode.HYBRID,
        reason=f"Low local confidence ({local_probe_score:.2f}). Augmenting with global server index."
    )
```
