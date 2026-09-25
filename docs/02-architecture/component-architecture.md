# Component Architecture Specification

- **Document Version:** 1.0.0
- **Status:** Complete
- **Date:** 2026-09-26

---

## 1. Edge Component Topology

The edge platform is structured into distinct, decoupled modular layers within the Python runtime:

```mermaid
graph TD
    subgraph UI_LAYER["Presentation Layer (Browser)"]
        UI_DASH["Dashboard & Triage HUD"]
        UI_MEM["Memory Explorer"]
        UI_SEARCH["Semantic Search View"]
        UI_GRAPH["Cytoscape Graph Viewer"]
        UI_SYNC["Sync Monitor & Net State"]
        UI_LAB["Memory Laboratory"]
    end

    subgraph API_LAYER["API Gateway Layer (FastAPI)"]
        API_MEM["/api/memories"]
        API_SEARCH["/api/search"]
        API_GRAPH["/api/graph"]
        API_GOV["/api/governance"]
        API_SYNC["/api/sync"]
        API_WS["/api/ws/status (WebSocket)"]
    end

    subgraph INTELLIGENCE_LAYER["Intelligence & Governance Layer"]
        GOV["Memory Governor"]
        FIREWALL["Privacy Firewall"]
        ROUTER["Adaptive Query Router"]
        FUSION["Context Fusion Engine"]
        CONTRADICT["Contradiction State Machine"]
        CONSOLIDATE["Memory Consolidation Worker"]
    end

    subgraph EMBED_LAYER["Local Embedding Engine"]
        FASTEMBED["FastEmbed Runtime (ONNX / CPU)"]
    end

    subgraph STORAGE_LAYER["Local Storage Layer"]
        QE_MUT["Qdrant Edge: Mutable Shard (Local Writes)"]
        QE_IMM["Qdrant Edge: Immutable Shard (Server Mirror)"]
        SQLITE_GRAPH["SQLite: Entity & Relation Tables"]
        SQLITE_EVENT["SQLite: Longitudinal Event Journal"]
        SQLITE_QUEUE["SQLite: Persistent Outbound Sync Queue"]
        SQLITE_AUDIT["SQLite: Cryptographic Provenance DAG"]
    end

    UI_LAYER <==>|"REST / WebSocket"| API_LAYER
    API_LAYER --> INTELLIGENCE_LAYER
    INTELLIGENCE_LAYER --> EMBED_LAYER
    INTELLIGENCE_LAYER --> STORAGE_LAYER
```

---

## 2. Component Responsibilities

1. **`EdgeVectorStore` (`qdrant-edge-py` Wrapper):** Handles instantiation, querying, updating, and snapshot management of the dual-shard configuration.
2. **`KnowledgeGraphStore` (SQLite Driver):** Manages entity nodes and relation edges; provides recursive neighborhood queries and path discovery.
3. **`TemporalEventStore` (SQLite Driver):** Records time-stamped clinical events, progression links, and state transitions.
4. **`MemoryGovernor`:** Runs scoring algorithms to classify memories into `LOCAL`, `SYNC_CANDIDATE`, or `EXPIRE`.
5. **`PrivacyFirewall`:** Evaluates payload fields against privacy rules, redacts PII/PHI, and drops unauthorized sync items.
6. **`QueryRouter`:** Analyzes incoming search requests, checking network state, privacy level, and latency budgets to route to `EDGE`, `CLOUD`, or `HYBRID`.
7. **`SyncReplicator`:** Manages the SQLite-backed outbound queue, network link detection, batch upserts to Qdrant Server, and partial snapshot imports.
