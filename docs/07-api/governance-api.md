# API Specification: Governance & Consolidation Endpoints

- **Document Version:** 1.0.0
- **Status:** Complete / Contract Specification
- **Date:** 2026-09-26

---

## 1. `POST /api/governance/evaluate/{id}`
- **Method:** `POST`
- **Path:** `/api/governance/evaluate/{id}`
- **Purpose:** Manually trigger the Memory Governor to evaluate an existing memory, calculate its multi-factor score, and output a retention verdict with transparent explainability factors.
- **Request Parameters:** `id` (path, string).
- **Response (200 OK):**
  ```json
  {
    "memory_id": "mem_01h8x9j2k3",
    "previous_state": "LOCAL",
    "new_state": "SYNC_CANDIDATE",
    "governance_score": 0.785,
    "factors": {
      "importance": 0.85,
      "confidence": 0.95,
      "recurrence": 3,
      "freshness": 0.92,
      "device_specificity": 0.20,
      "access_frequency": 5
    },
    "explanation": "High clinical importance (0.85) and confirmed recurrence (3) qualify this record for cloud synchronization."
  }
  ```
- **Errors:** 404 Not Found (Memory ID does not exist).
- **Offline Behavior:** 100% operational offline.

---

## 2. `POST /api/memories/consolidate`
- **Method:** `POST`
- **Path:** `/api/memories/consolidate`
- **Purpose:** Triggers the Memory Consolidation Worker to identify and cluster repeated observations for a specific patient.
- **Request Body:**
  ```json
  {
    "patient_id": "patient_synthetic_104",
    "window_hours": 4
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "status": "completed",
    "clusters_detected": 1,
    "memories_consolidated": 4,
    "new_consolidated_memory_id": "cons_01h8x9xyz"
  }
  ```
- **Offline Behavior:** 100% operational offline.
