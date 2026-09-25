# Retrieval Explainability and Score Attribution Specification

- **Document Version:** 1.0.0
- **Status:** Complete
- **Date:** 2026-09-26

---

## 1. The Requirement for Explainable Retrieval in Healthcare

Clinicians cannot trust black-box relevance scores. When the system retrieves a treatment suggestion or prior finding, the operator must know *why* this memory was surfaced:
- Was it because of strong semantic similarity in free text?
- Was it because an exact drug name matched a BM25 keyword query?
- Was it boosted by an active condition in the Knowledge Graph?
- Did recent vital signs alter the ranking?

---

## 2. Score Decomposition Model

Every search result returned by `/api/search` includes a comprehensive `attribution` object breaking down the composite score:

```json
{
  "memory_id": "mem_9b8a7c6d",
  "composite_score": 0.884,
  "attribution": {
    "dense_cosine_score": 0.842,
    "dense_rank": 2,
    "sparse_bm25_score": 14.28,
    "sparse_rank": 1,
    "rrf_score": 0.0328,
    "graph_boost_factor": 1.25,
    "matched_graph_entities": [
      {"id": "entity_asthma", "type": "Condition", "matched_field": "diagnosis"}
    ],
    "temporal_decay_factor": 0.94,
    "elapsed_time_hours": 1.2
  },
  "highlight_snippets": [
    "Patient presenting with acute <mark>bronchospasm</mark> and elevated heart rate."
  ]
}
```

This decomposition powers the **Search HUD** in the UI, rendering visual badge chips representing dense match strength, keyword hits, and active ontological affirmations.
