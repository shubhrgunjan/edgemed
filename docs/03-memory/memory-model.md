# The Tripartite Memory Model: Vector, Graph, and Temporal Cooperativity

- **Document Version:** 1.0.0
- **Status:** Complete / Core Architectural Specification
- **Date:** 2026-09-26
- **Lead System Designer:** Team LEX (Code Cubicle 6.0 — PS03)

---

## 1. The Core Dilemma of Single-Model Memory

Traditional vector-only memory systems (standard RAG) treat clinical data as flat points in a high-dimensional vector space. In clinical environments, this causes three critical failure modes:
1. **Semantic Ambiguity with Medical Negation:** A query for "contraindications for hypertensive patient with asthma" retrieves mentions of beta-blockers because of strong textual co-occurrence, even though the text explicitly states the drug is *strictly prohibited*.
2. **Loss of Strict Multi-Hop Topology:** Vectors cannot enforce transitive ontological paths (e.g., `Patient -> HasCondition(SevereAsthma) -> Contraindicates(Propranolol)`).
3. **Chronological Flattening:** A vector space cannot distinguish between an observation recorded 10 minutes ago during acute shock and a baseline observation recorded 3 years ago.

---

## 2. The Tripartite Memory Solution

EdgeMed models clinical reality across three distinct, cooperating memory pillars:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      THE TRIPARTITE MEMORY ENGINE                      │
├───────────────────┬──────────────────────────┬─────────────────────────┤
│ 1. VECTOR MEMORY  │ 2. KNOWLEDGE GRAPH       │ 3. TEMPORAL MEMORY      │
│    (Qdrant Edge)  │    (SQLite Relational)   │    (Event Progression)  │
├───────────────────┼──────────────────────────┼─────────────────────────┤
│ • Fuzzy semantic  │ • Explicit ontology      │ • Chronological timeline│
│   similarity      │ • Strict multi-hop paths │ • Symptom progression   │
│ • Natural-language│ • Invariant clinical     │ • Recency decay         │
│   triage notes    │   rules & contradictions │ • Causal chaining       │
│ • Dense + BM25    │ • Entity relationships   │ • Event intervals       │
└─────────┬─────────┴────────────┬─────────────┴────────────┬────────────┘
          │                      │                          │
          └──────────────────────┼──────────────────────────┘
                                 ▼
                     ┌───────────────────────┐
                     │ CONTEXT FUSION ENGINE │
                     └───────────────────────┘
```

---

## 3. How the Three Representations Cooperate (Clinical Example)

Consider an incoming clinical scenario:
> *"Patient exhibiting wheezing, respiratory distress, and tachycardia. Initial suspicion: acute asthma exacerbation."*

1. **Vector Memory (Qdrant Edge):**
   - Natural language search finds semantically related clinical protocol guidelines: `"Management of acute bronchospasm and tachycardia in respiratory distress"`.
   - Returns candidate memories with high cosine similarity (>0.82).

2. **Knowledge Graph (SQLite):**
   - Queries explicit relations for the patient entity:
     - `Patient_402` -> `HAS_CONDITION` -> `SevereAsthma`
     - `Drug_Propranolol` -> `CONTRAINDICATED_WITH` -> `SevereAsthma`
   - **Intersection Filter:** Automatically removes or flags Propranolol from the retrieved candidate treatments, regardless of how high its semantic similarity was.

3. **Temporal Memory (Event Stream):**
   - Retrieves the longitudinal timeline for `Patient_402`:
     - `T-12h`: Routine vitals normal (HR 72, SpO2 98%).
     - `T-2h`: Onset of mild dyspnea recorded.
     - `T-15m`: Acute respiratory distress (HR 125, SpO2 88%).
   - Calculates the rate of deterioration (temporal slope), prompting the Context Fusion engine to prioritize high-acuity interventions over routine management.

---

## 4. Context Fusion Strategy

The Context Fusion engine combines the three pillars via weighted scoring:

$$\text{FinalScore} = \left(\alpha \cdot \text{RRF}_{\text{Vector}} + \beta \cdot \text{GraphRelevance}\right) \times \text{TemporalDecay}(t)$$

Where:
- $\text{RRF}_{\text{Vector}}$ fuses dense cosine similarity and sparse BM25 keyword rankings.
- $\text{GraphRelevance}$ applies binary masks (1.0 for valid ontological paths, 0.0 for contraindicated or refuted paths).
- $\text{TemporalDecay}(t) = e^{-\lambda \Delta t}$ applies recency weighting to acute observations while holding chronic diagnoses at constant weight.
