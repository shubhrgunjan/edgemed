# C4 Model: System Context Specification

- **Document Version:** 1.0.0
- **Status:** Complete / Architecture Reference
- **Date:** 2026-09-26

---

## 1. System Context Diagram

```mermaid
flowchart TB
    CLINICIAN["Clinician / Field Operator<br/>[Person]<br/>Triage nurse, emergency doctor, or field medic"]
    
    subgraph EDGEMED_SYSTEM["EdgeMed Platform [System Context Boundary]"]
        EDGEMED["EdgeMed Memory Lab<br/>[Software System]<br/>Autonomous edge-intelligence & tripartite memory platform"]
    end

    HOSPITAL_CLOUD["Central Hospital Cloud<br/>[External System]<br/>Authoritative medical databases, EHR, and global guidelines"]
    QDRANT_CLUSTER["Central Qdrant Server Cluster<br/>[External System]<br/>High-capacity vector index and global knowledge repository"]

    CLINICIAN -->|"Inputs observations, runs hybrid queries, reviews conflicts"| EDGEMED
    EDGEMED -->|"Replicates scrubbed points & pulls differential snapshots (mTLS)"| QDRANT_CLUSTER
    QDRANT_CLUSTER -->|"Provides global protocol updates"| EDGEMED
    EDGEMED -.->|"Optional future export of clinical summaries (FHIR)"| HOSPITAL_CLOUD
```

---

## 2. Elements Description

- **User (Clinician / Field Operator):** Uses the EdgeMed interface on portable edge hardware to record triage findings, search medical knowledge, and review clinical contradictions during active field operations.
- **EdgeMed Platform (System):** The complete software system running autonomously on the edge device, providing tripartite memory, memory governance, and synchronization capabilities.
- **Central Qdrant Server Cluster (External System):** High-capacity vector database infrastructure hosted in a central hospital data center, responsible for multi-device snapshot coordination and global vector indexing.
- **Central Hospital Cloud (External System):** Enterprise EHR/HIS infrastructure storing long-term patient records and administrative histories.
