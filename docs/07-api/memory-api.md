# API Specification: Memory Endpoints

- **Document Version:** 1.0.0
- **Status:** Complete / Contract Specification
- **Date:** 2026-09-26

---

## 1. `GET /api/memories`
- **Method:** `GET`
- **Path:** `/api/memories`
- **Purpose:** Retrieve a paginated, filtered list of memory points.
- **Request Parameters (Query):**
  - `page` (integer, default: 1)
  - `limit` (integer, default: 25)
  - `category` (string, optional)
  - `privacy_level` (string, optional)
  - `patient_id` (string, optional)
- **Response (200 OK):**
  ```json
  {
    "items": [
      {
        "id": "mem_01h8x9j2k3",
        "content": "Patient reports severe shortness of breath on exertion.",
        "category": "SYMPTOM",
        "timestamp": "2026-09-26T12:00:00Z",
        "confidence": 0.88,
        "importance": 0.75,
        "privacy_level": "SENSITIVE",
        "lifecycle_state": "LOCAL",
        "sync_state": "PENDING",
        "version": 1
      }
    ],
    "total": 1,
    "page": 1,
    "pages": 1
  }
  ```
- **Errors:** 400 Bad Request (Invalid parameters).
- **Authentication:** Local Session / None required.
- **Offline Behavior:** 100% operational offline.

---

## 2. `GET /api/memories/{id}`
- **Method:** `GET`
- **Path:** `/api/memories/{id}`
- **Purpose:** Retrieve full tripartite details, provenance DAG, and governance factors for a specific memory.
- **Request Parameters:** `id` (path, string).
- **Response (200 OK):** Full Memory Record schema (see `schemas/memory.schema.json`).
- **Errors:** 404 Not Found (Record does not exist).
- **Offline Behavior:** 100% operational offline.

---

## 3. `POST /api/memories`
- **Method:** `POST`
- **Path:** `/api/memories`
- **Purpose:** Ingest a new clinical observation, compute embeddings, persist to Qdrant Edge & SQLite, evaluate governance, and optionally enqueue for sync.
- **Request Body:**
  ```json
  {
    "content": "Blood pressure elevated at 148/92 mmHg, repeat confirmed.",
    "category": "VITAL_SIGN",
    "patient_id": "patient_synthetic_104",
    "importance": 0.70,
    "confidence": 0.95,
    "privacy_level": "SENSITIVE",
    "source": "CLINICIAN_ENTRY"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "id": "mem_01h8x9j2k3",
    "content": "Blood pressure elevated at 148/92 mmHg, repeat confirmed.",
    "lifecycle_state": "LOCAL",
    "sync_state": "PENDING",
    "governance_decision": "LOCAL",
    "created_at": "2026-09-26T12:05:00Z"
  }
  ```
- **Errors:** 422 Unprocessable Entity (Schema violation).
- **Offline Behavior:** 100% operational offline. Point written to local mutable shard immediately.

---

## 4. `DELETE /api/memories/{id}`
- **Method:** `DELETE`
- **Path:** `/api/memories/{id}`
- **Purpose:** Archive or remove a memory point from local retrieval; enqueues a tombstone if synchronized.
- **Request Parameters:** `id` (path, string).
- **Response (200 OK):**
  ```json
  {
    "id": "mem_01h8x9j2k3",
    "status": "archived",
    "tombstone_enqueued": true
  }
  ```
- **Errors:** 404 Not Found.
- **Offline Behavior:** 100% operational offline.
