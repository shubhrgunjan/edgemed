# Data Schemas Master Catalog

- **Document Version:** 1.0.0
- **Status:** Complete / Authoritative Data Catalog
- **Date:** 2026-09-26
- **Lead Data Architect:** Team LEX (Code Cubicle 6.0 — PS03)

---

## 1. Overview of Data Models

EdgeMed enforces strict JSON Schema definitions and Pydantic v2 data models across all storage and communication boundaries. The core models are organized into the following specifications:

| Model Name | Document Specification | Formal JSON Schema File | Key Purpose |
| :--- | :--- | :--- | :--- |
| **Memory** | [memory-schema.md](memory-schema.md) | `schemas/memory.schema.json` | The unified 18-attribute clinical memory representation. |
| **Entity** | [graph-schema.md](graph-schema.md) | `schemas/entity.schema.json` | Clinical subject node in the Knowledge Graph. |
| **Relation** | [graph-schema.md](graph-schema.md) | `schemas/relation.schema.json` | Explicit typed directed edge between entities. |
| **Event** | [event-schema.md](event-schema.md) | `schemas/event.schema.json` | Longitudinal event entry in the temporal journal. |
| **SyncRecord** | [sync-schema.md](sync-schema.md) | `schemas/sync-record.schema.json` | Outbound synchronization queue transaction item. |
| **GovernanceDecision**| [memory-schema.md](memory-schema.md) | `schemas/governance-decision.schema.json`| Scoring factor breakdown and retention verdict. |
| **SearchResult** | [memory-schema.md](memory-schema.md) | `schemas/search-result.schema.json` | Scored hybrid search candidate with score attribution. |
| **ProvenanceRecord** | [memory-schema.md](memory-schema.md) | `schemas/provenance-record.schema.json` | Cryptographic audit trail and transformation history. |
