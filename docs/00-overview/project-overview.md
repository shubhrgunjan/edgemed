# Project Overview: EdgeMed Memory Lab

- **Document Version:** 1.0.0
- **Status:** Complete / Authoritative Document
- **Date:** 2026-09-26
- **Lead Architect:** Team LEX (Code Cubicle 6.0 — PS03)

---

## 1. Vision and Mission

**EdgeMed** is an intelligent, edge-native clinical decision-support memory platform engineered for decentralized, offline-first medical operations.

The system addresses the fundamental dilemma of modern AI in healthcare: while high-parameter models and centralized data warehouses offer immense reasoning capabilities, they are completely paralyzed when network connectivity is severed or bandwidth is constrained. In rural field clinics, forward operating bases, emergency transport vehicles, and humanitarian disaster zones, medical staff cannot rely on cloud APIs for patient history recall or clinical guidance.

EdgeMed embeds autonomous semantic intelligence directly onto the edge device. By orchestrating **Qdrant Edge** for in-process vector retrieval, **SQLite** for explicit relational knowledge graphs and temporal event logging, and an intelligent **Memory Governor** for lifecycle and privacy management, EdgeMed transforms resource-constrained laptops and embedded hardware into resilient clinical memory companions.

---

## 2. Core Value Propositions

1. **Sub-Millisecond Offline Recall:** Zero cloud round-trips. Local hybrid vector and keyword search queries resolve in <5ms directly on-device.
2. **Tripartite Memory Cooperativity:** Combines the fuzzy associative strengths of dense embeddings with the exact relational guarantees of knowledge graphs and the chronological progression of clinical event timelines.
3. **Principled Data Sovereignty:** A four-tier Privacy Firewall inspects all clinical assertions before queueing for cloud synchronization, ensuring identifiable patient data never leaves physical hardware without explicit authorization.
4. **Resilient Synchronization Lifecycle:** Operates asynchronously across intermittent network links, utilizing partial segment snapshots and persistent queues to ensure eventual consistency without data loss or silent overwriting.

---

## 3. High-Level System Context

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │                              FIELD CLINIC                              │
 │                                                                        │
 │  ┌──────────────────────────────────────────────────────────────────┐  │
 │  │                 EDGE DEVICE (AMD Ryzen 5 / 8GB)                  │  │
 │  │                                                                  │  │
 │  │  ┌───────────────┐     ┌──────────────────────────────────────┐  │  │
 │  │  │ Operator UI   │◄───►│ EdgeMed Core Engine (FastAPI)        │  │  │
 │  │  │ (React/Vite)  │     │                                      │  │  │
 │  │  └───────────────┘     │  - Memory Governor & Privacy Filter  │  │  │
 │  │                        │  - Context Fusion (Hybrid Engine)    │  │  │
 │  │                        │  - Contradiction & Consolidation     │  │  │
 │  │                        └──────────┬───────────────────────────┘  │  │
 │  │                                   │                              │  │
 │  │                        ┌──────────┴───────────┐                  │  │
 │  │                        ▼                      ▼                  │  │
 │  │                ┌──────────────┐       ┌──────────────┐           │  │
 │  │                │ Qdrant Edge  │       │ SQLite (WAL) │           │  │
 │  │                │ Vector Store │       │ Graph & Sync │           │  │
 │  │                └──────────────┘       └──────────────┘           │  │
 │  └───────────────────────────────────┬──────────────────────────────┘  │
 └──────────────────────────────────────┼─────────────────────────────────┘
                                        │ Intermittent Uplink (mTLS)
                                        ▼
                         ┌─────────────────────────────┐
                         │   CENTRAL HOSPITAL CLOUD    │
                         │   Qdrant Server Cluster     │
                         │   Central Knowledge Base    │
                         └─────────────────────────────┘
```
