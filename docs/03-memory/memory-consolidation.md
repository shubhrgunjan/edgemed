# Memory Consolidation Architecture: Repetition and Pattern Clustering

- **Document Version:** 1.0.0
- **Status:** Complete / Authoritative Specification
- **Date:** 2026-09-26
- **Lead System Designer:** Team LEX (Code Cubicle 6.0 — PS03)

---

## 1. Architectural Purpose

In hospital and triage settings, identical or semantically redundant observations occur continuously (e.g., blood pressure checks every 15 minutes, repeated reports of persistent cough). Unbounded storage of these redundant records causes:
1. **Vector Memory Inflation:** Unnecessary memory-mapped file growth on the edge device.
2. **Search Result Dilution:** Top-k nearest-neighbor queries become flooded with repetitive variations of the same observation, crowding out distinct clinical findings.
3. **Bandwidth Waste:** Replicating 50 identical readings upstream exhausts low-bandwidth edge connections.

---

## 2. Consolidation Pipeline Architecture

```
    RAW MEMORY STREAM
    [ Obs 1: BP 142/90, T-60m ]
    [ Obs 2: BP 145/92, T-45m ]
    [ Obs 3: BP 140/88, T-30m ]
    [ Obs 4: BP 144/91, T-15m ]
                │
                ▼
      TEMPORAL GROUPING (Window: 2 hours, Patient: P_104)
                │
                ▼
      SEMANTIC SIMILARITY & DUPLICATE CHECK (Cosine Similarity > 0.92)
                │
                ▼
      PATTERN RECOGNITION (Consistent Stage 1 Hypertension Pattern)
                │
                ▼
      CONFIDENCE AGGREGATION (Bayesian / Weighted Mean Confidence)
                │
                ▼
      CONSOLIDATED MEMORY CREATION
      [ Summary: "Sustained Stage 1 Systolic Hypertension (Mean BP: 143/90, n=4)" ]
      [ Category: VITAL_SUMMARY | Importance: 0.72 | Recurrence: 4 ]
      [ Provenance: Linked to parent IDs [Obs 1, Obs 2, Obs 3, Obs 4] ]
```

---

## 3. The 5 Core Consolidation Pillars

### 3.1 Duplicate Detection & Semantic Similarity
The consolidation worker executes periodically in the background (or when local shard memory exceeds 80% working limit):
- Queries memories belonging to the same `patient_id` within a sliding temporal window ($\Delta T \le 4\text{ hours}$).
- Computes pairwise cosine similarity between embeddings:
  $$\text{Sim}(M_i, M_j) = \frac{\mathbf{v}_i \cdot \mathbf{v}_j}{\|\mathbf{v}_i\| \|\mathbf{v}_j\|}$$
- Pairs with $\text{Sim} \ge 0.90$ and matching clinical categories are identified as consolidation candidates.

### 3.2 Temporal Grouping
Memories separated by large chronological intervals (e.g., an observation from last week vs. today) are excluded from consolidation, as they represent distinct clinical episodes rather than a repeated pattern.

### 3.3 Confidence Aggregation
Individual observation confidences ($c_1, c_2, \dots, c_n$) are aggregated asymptotically to reflect reinforced observational certainty:

$$c_{\text{consolidated}} = 1 - \prod_{i=1}^n (1 - c_i)$$

*(Capped at 0.99 to preserve non-absolute epistemic uncertainty).*

### 3.4 Provenance Preservation
The constituent raw memories are not deleted immediately; their lifecycle states are updated to `CONSOLIDATED_ARCHIVED`. The newly created consolidated memory stores the explicit list of constituent IDs in its `provenance.parent_memory_ids`, ensuring complete traceability during clinical audits.
