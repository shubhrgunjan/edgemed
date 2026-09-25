# Data Flow Architecture

- **Document Version:** 1.0.0
- **Status:** Complete
- **Date:** 2026-09-26

---

## 1. End-to-End Clinical Data Flow

The following sequence details how a newly captured clinical observation flows through the EdgeMed system, from operator entry to persistent storage, governance evaluation, and optional cloud synchronization:

```mermaid
sequenceDiagram
    autonumber
    actor Clinician as Clinician / Operator
    participant UI as Operator UI / Memory Lab
    participant API as FastAPI Ingestion Endpoint
    participant FastEmbed as FastEmbed (CPU ONNX)
    participant Engine as EdgeMed Memory Engine
    participant QdrantEdge as Qdrant Edge Shard
    participant SQLite as SQLite Storage (WAL)
    participant Governor as Memory Governor
    participant Firewall as Privacy Firewall
    participant SyncQueue as Persistent Sync Queue
    participant Server as Central Qdrant Server

    Clinician->>UI: Enter Clinical Observation
    UI->>API: POST /api/memories (JSON Payload)
    API->>FastEmbed: Generate 384-d Vector & Sparse BM25
    FastEmbed-->>API: Dense & Sparse Embeddings
    API->>Engine: Ingest Observation Record
    
    par Store in Local Memory Engine
        Engine->>QdrantEdge: Upsert Vector + Payload (Mutable Shard)
        Engine->>SQLite: Insert Entity Nodes & Edges
        Engine->>SQLite: Append Event to Timeline Journal
        Engine->>SQLite: Record Provenance Node (SHA-256 Hash)
    end

    Engine->>Governor: Evaluate Memory Retention Score
    Governor-->>Engine: Decision: SYNC_CANDIDATE (Score: 0.84)

    Engine->>Firewall: Inspect Payload Privacy Tier
    alt Privacy Tier == HIGHLY_SENSITIVE
        Firewall-->>Engine: Rule: Local Pin Only (Blocked from Sync)
    else Privacy Tier == SENSITIVE
        Firewall->>Firewall: Redact Synthetic Identifiers
        Firewall->>SyncQueue: Enqueue Sanitized Point (PENDING)
    else Privacy Tier == PUBLIC or INTERNAL
        Firewall->>SyncQueue: Enqueue Full Point (PENDING)
    end

    opt Network Connection Active
        SyncQueue->>Server: Batch Upsert Points (mTLS)
        Server-->>SyncQueue: Acknowledge Success (HTTP 200)
        SyncQueue->>SQLite: Mark Queue Item COMMITTED
    end

    API-->>UI: HTTP 201 Created (Memory ID, Scores, Provenance)
    UI-->>Clinician: Render Observation in Memory Explorer
```

---

## 2. Ingestion Stages

1. **Validation & Normalization:** The input JSON is validated against `MemoryCreateRequest` schema; clinical entities are extracted.
2. **On-Device Embedding:** FastEmbed generates 384-dimensional dense vectors and BM25 sparse token frequencies in-process.
3. **Tripartite Persistence:** Points are stored in the Qdrant Edge mutable shard, relational entities in SQLite, and longitudinal events in the timeline journal.
4. **Governance Evaluation:** The Memory Governor calculates relevance, importance, and confidence scores.
5. **Privacy Inspection:** The Privacy Firewall checks sensitivity classifications, drops local-only records, scrubs identifiers, and passes approved payloads to the SQLite outbound queue.
6. **Replication Drain:** An asynchronous background worker transmits queued points to the central Qdrant Server whenever verified network connectivity exists.
