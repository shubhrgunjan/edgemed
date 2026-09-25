# API Specification: Knowledge Graph Endpoints

- **Document Version:** 1.0.0
- **Status:** Complete / Contract Specification
- **Date:** 2026-09-26

---

## 1. `GET /api/graph`
- **Method:** `GET`
- **Path:** `/api/graph`
- **Purpose:** Retrieve entities and explicit relationship edges formatted for Cytoscape.js rendering.
- **Request Parameters (Query):**
  - `patient_id` (string, optional: filter graph around a specific subject)
  - `max_depth` (integer, default: 2, range: 1..4)
  - `node_types` (string array, optional: filter specific entity types)
- **Response (200 OK):**
  ```json
  {
    "nodes": [
      {
        "data": {
          "id": "node_patient_104",
          "label": "Patient #104",
          "type": "Patient",
          "properties": {"gender": "F", "age": 42}
        }
      },
      {
        "data": {
          "id": "node_cond_asthma",
          "label": "Severe Asthma",
          "type": "Condition",
          "properties": {"severity": "HIGH", "icd10": "J45.5"}
        }
      }
    ],
    "edges": [
      {
        "data": {
          "id": "edge_104_asthma",
          "source": "node_patient_104",
          "target": "node_cond_asthma",
          "label": "HAS_CONDITION",
          "weight": 1.0
        }
      }
    ]
  }
  ```
- **Errors:** 400 Bad Request (Invalid depth parameter).
- **Offline Behavior:** 100% operational offline. Resolves directly from local SQLite database in `<20ms`.
