# API Specification: Search Endpoints

- **Document Version:** 1.0.0
- **Status:** Complete / Contract Specification
- **Date:** 2026-09-26

---

## 1. `POST /api/search`
- **Method:** `POST`
- **Path:** `/api/search`
- **Purpose:** Execute hybrid semantic and keyword search across local and/or cloud knowledge with reciprocal rank fusion and score attribution.
- **Authentication:** Local Session / None required.
- **Request Body:**
  ```json
  {
    "query": "management of acute bronchospasm with tachycardia",
    "limit": 10,
    "mode": "AUTO",
    "patient_id": "patient_synthetic_104",
    "min_score": 0.40,
    "filter_categories": ["DIAGNOSIS", "MEDICATION", "PROTOCOL"]
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "query": "management of acute bronchospasm with tachycardia",
    "execution_mode": "EDGE",
    "latency_ms": 3.82,
    "results": [
      {
        "memory_id": "mem_01h8x9j2k3",
        "content": "Emergency protocol for acute bronchospasm: Nebulized albuterol with continuous pulse oximetry monitoring.",
        "category": "PROTOCOL",
        "composite_score": 0.892,
        "attribution": {
          "dense_cosine_score": 0.865,
          "sparse_bm25_score": 12.4,
          "rrf_score": 0.032,
          "graph_boost": 1.25,
          "temporal_decay": 1.0
        },
        "highlight_snippets": [
          "Emergency protocol for <mark>acute bronchospasm</mark>: Nebulized albuterol..."
        ]
      }
    ]
  }
  ```
- **Errors:**
  - 400 Bad Request (Missing query string).
  - 422 Unprocessable Entity (Invalid filter parameter).
- **Offline Behavior:** 100% operational offline. Forces `execution_mode: "EDGE"`; query resolves directly against in-process Qdrant Edge in `<5ms`.
