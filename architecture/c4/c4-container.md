# C4 Model: Container Architecture Specification

- **Document Version:** 1.0.0
- **Status:** Complete / Architecture Reference
- **Date:** 2026-09-26

---

## 1. Container Diagram

```mermaid
flowchart TB
    actor Clinician as "Clinician / Field Operator"

    subgraph EDGE_DEVICE["Edge Device Boundary (Laptop / Embedded Node)"]
        SPA["Single Page Application<br/>[Container: React 18 / TypeScript]<br/>Interactive UI, Cytoscape graph canvas, triage HUD"]
        
        subgraph BACKEND_PROCESS["Single In-Process Host (Python 3.11 / Uvicorn)"]
            API["API Gateway & Service Layer<br/>[Container: FastAPI]<br/>Async REST endpoints & WebSocket state broadcast"]
            
            ENGINE["EdgeMed Memory Core<br/>[Component: Python Core]<br/>Governor, Privacy Firewall, Query Router, RRF Fusion"]
            
            FASTEMBED["FastEmbed Runtime<br/>[Component: ONNX / C++]<br/>CPU embeddings (bge-small-en-v1.5)"]
            
            QE["Qdrant Edge Engine<br/>[Container: qdrant-edge-py / Rust]<br/>In-process dual-shard vector memory"]
            
            SQLITE["Relational & Sync Storage<br/>[Container: SQLite 3 WAL]<br/>Entities, relations, event journal, sync queue, provenance"]
        end
    end

    subgraph CLOUD_NODE["Central Hospital Cloud"]
        QS["Central Qdrant Server<br/>[Container: Docker / Qdrant Server]<br/>Global vector index & snapshot engine"]
    end

    Clinician -->|"HTTPS / WebSocket"| SPA
    SPA -->|"JSON API (localhost:8000)"| API
    API --> ENGINE
    ENGINE --> FASTEMBED
    ENGINE --> QE
    ENGINE --> SQLITE
    
    ENGINE == "Asynchronous Idempotent Sync (mTLS)" ==> QS
    QS -. "Differential Snapshot Recovery" .-> QE
```

---

## 2. Container Descriptions

| Container Name | Technology | Description |
| :--- | :--- | :--- |
| **Single Page Application** | React 18 / TypeScript / Vite | Renders the operator UI, Cytoscape graph canvas, Search HUD, and Memory Lab controls. |
| **API Gateway Layer** | FastAPI / Uvicorn | Exposes REST and WebSocket contracts; handles asynchronous request dispatching. |
| **EdgeMed Memory Core** | Python 3.11+ Core | Implements Memory Governor scoring, Privacy Firewall filtering, Query Routing, and Contradiction detection. |
| **FastEmbed Runtime** | ONNX Runtime (CPU) | High-speed, low-memory dense vector and BM25 token generator (`bge-small-en-v1.5`). |
| **Qdrant Edge Engine** | `qdrant-edge-py` / Rust Core | In-process embedded vector database managing mutable and immutable shards. |
| **Relational Storage** | SQLite 3 (WAL Mode) | Embedded ACID store for Knowledge Graph entities, edges, temporal events, sync queues, and provenance logs. |
| **Central Qdrant Server** | Docker / Qdrant Server | Central cloud vector store handling cross-device replication and global HNSW indexing. |
