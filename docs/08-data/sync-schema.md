# Data Schema: Synchronization Records

- **Document Version:** 1.0.0
- **Status:** Complete / Formal Schema Definition
- **Date:** 2026-09-26

---

## 1. Outbound Synchronization Queue Record Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SyncQueueRecord",
  "type": "object",
  "required": [
    "queue_id", "memory_id", "payload", "dense_vector",
    "privacy_tier", "status", "retry_count", "created_at"
  ],
  "properties": {
    "queue_id": {"type": "integer"},
    "memory_id": {"type": "string"},
    "payload": {"type": "object"},
    "dense_vector": {
      "type": "array",
      "items": {"type": "number"},
      "minItems": 384,
      "maxItems": 384
    },
    "sparse_vector": {
      "type": "object",
      "properties": {
        "indices": {"type": "array", "items": {"type": "integer"}},
        "values": {"type": "array", "items": {"type": "number"}}
      }
    },
    "privacy_tier": {
      "type": "string",
      "enum": ["PUBLIC", "INTERNAL", "SENSITIVE"]
    },
    "status": {
      "type": "string",
      "enum": ["PENDING", "SYNCING", "COMMITTED", "FAILED"]
    },
    "retry_count": {"type": "integer", "minimum": 0},
    "next_retry_at": {"type": "string", "format": "date-time"},
    "created_at": {"type": "string", "format": "date-time"},
    "committed_at": {"type": ["string", "null"], "format": "date-time"}
  }
}
```
