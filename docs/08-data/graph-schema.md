# Data Schema: Knowledge Graph Entities and Relations

- **Document Version:** 1.0.0
- **Status:** Complete / Formal Schema Definition
- **Date:** 2026-09-26

---

## 1. Graph Entity (Node) Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "GraphEntityNode",
  "type": "object",
  "required": ["id", "type", "label", "properties"],
  "properties": {
    "id": {"type": "string"},
    "type": {
      "type": "string",
      "enum": ["Patient", "Condition", "Medication", "Procedure", "Observation", "Event", "Document"]
    },
    "label": {"type": "string"},
    "properties": {"type": "object"},
    "created_at": {"type": "string", "format": "date-time"}
  }
}
```

---

## 2. Graph Relation (Edge) Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "GraphRelationEdge",
  "type": "object",
  "required": ["id", "source_id", "target_id", "relation_type", "weight"],
  "properties": {
    "id": {"type": "string"},
    "source_id": {"type": "string"},
    "target_id": {"type": "string"},
    "relation_type": {
      "type": "string",
      "enum": [
        "HAS_CONDITION", "TREATED_WITH", "HAS_EVENT",
        "MENTIONS", "DERIVED_FROM", "CONTRADICTS", "SUPERSEDES"
      ]
    },
    "weight": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    "properties": {"type": "object"},
    "created_at": {"type": "string", "format": "date-time"}
  }
}
```
