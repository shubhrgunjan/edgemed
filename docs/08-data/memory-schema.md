# Data Schema: Memory, Governance, and Provenance Models

- **Document Version:** 1.0.0
- **Status:** Complete / Formal Schema Definition
- **Date:** 2026-09-26

---

## 1. Unified Memory Record Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "MemoryRecord",
  "type": "object",
  "required": [
    "id", "content", "timestamp", "source", "device_id",
    "category", "confidence", "importance", "privacy_level",
    "lifecycle_state", "sync_state", "version", "provenance"
  ],
  "properties": {
    "id": {"type": "string", "format": "uuid"},
    "content": {"type": "string"},
    "embedding": {
      "type": "array",
      "items": {"type": "number"},
      "minItems": 384,
      "maxItems": 384
    },
    "timestamp": {"type": "string", "format": "date-time"},
    "source": {
      "type": "string",
      "enum": ["CLINICIAN_ENTRY", "TRIAGE_VITALS", "LAB_REPORT", "IMAGING_REPORT", "SYSTEM_CONSOLIDATED"]
    },
    "device_id": {"type": "string"},
    "category": {
      "type": "string",
      "enum": ["SYMPTOM", "DIAGNOSIS", "MEDICATION", "ALLERGY", "PROCEDURE", "VITAL_SIGN", "PROTOCOL"]
    },
    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    "importance": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    "recurrence": {"type": "integer", "minimum": 1},
    "freshness": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    "privacy_level": {
      "type": "string",
      "enum": ["PUBLIC", "INTERNAL", "SENSITIVE", "HIGHLY_SENSITIVE"]
    },
    "provenance": {"$ref": "#/$defs/ProvenanceRecord"},
    "entities": {
      "type": "array",
      "items": {"type": "string"}
    },
    "relations": {
      "type": "array",
      "items": {"type": "object"}
    },
    "lifecycle_state": {
      "type": "string",
      "enum": ["LOCAL", "SYNC_CANDIDATE", "EXPIRED", "CONSOLIDATED_ARCHIVED", "CONFLICTING"]
    },
    "sync_state": {
      "type": "string",
      "enum": ["PENDING", "SYNCING", "COMMITTED", "FAILED"]
    },
    "version": {"type": "integer", "minimum": 1}
  },
  "$defs": {
    "ProvenanceRecord": {
      "type": "object",
      "required": ["origin_device_id", "created_at", "generator_modality"],
      "properties": {
        "origin_device_id": {"type": "string"},
        "created_at": {"type": "string", "format": "date-time"},
        "generator_modality": {"type": "string"},
        "parent_memory_ids": {"type": "array", "items": {"type": "string"}},
        "source_document_hash": {"type": "string"},
        "revision_count": {"type": "integer"}
      }
    }
  }
}
```
