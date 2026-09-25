# Data Schema: Temporal Events

- **Document Version:** 1.0.0
- **Status:** Complete / Formal Schema Definition
- **Date:** 2026-09-26

---

## 1. Temporal Event Progression Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "TemporalEventRecord",
  "type": "object",
  "required": [
    "event_id", "patient_id", "stage", "timestamp", "description"
  ],
  "properties": {
    "event_id": {"type": "string"},
    "patient_id": {"type": "string"},
    "event_sequence": {"type": "integer"},
    "stage": {
      "type": "string",
      "enum": ["OBSERVATION", "FOLLOW_UP", "TREATMENT", "OUTCOME"]
    },
    "timestamp": {"type": "string", "format": "date-time"},
    "prior_event_id": {"type": ["string", "null"]},
    "clinical_acuity_delta": {"type": "number"},
    "description": {"type": "string"},
    "vitals_snapshot": {"type": "object"},
    "linked_memory_ids": {
      "type": "array",
      "items": {"type": "string"}
    }
  }
}
```
