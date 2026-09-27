# EdgeMed: AI-Powered Edge Memory & Intelligence Platform

> **Local prototype:** See [implementation status, local operation, validation, and remaining work](docs/local-prototype.md). The architecture documents below remain design references.
### *EdgeMed Memory Lab — Technical Repository Specification*

[![Hackathon](https://img.shields.io/badge/Hackathon-Code%20Cubicle%206.0-blue.svg)](https://codecibicle6.devpost.com)
[![Team](https://img.shields.io/badge/Team-LEX-orange.svg)]()
[![Problem Statement](https://img.shields.io/badge/Problem%20Statement-PS03-green.svg)]()
[![Status](https://img.shields.io/badge/Status-Architecture%20%2F%20Documentation%20Phase-yellow.svg)]()
[![Implementation](https://img.shields.io/badge/Implementation-NOT%20IMPLEMENTED%20YET-lightgrey.svg)]()
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

> **One-Line Description:** An autonomous, offline-first clinical decision-support memory platform that separates vector semantic recall, relational knowledge graphs, and temporal event progressions on resource-constrained edge devices with privacy-governed cloud synchronization.

 ### Built Under Team LEX:
 - Aryan Vishwakarma (Leader)
 - Farhan Akhtar
 - Shubhr Gunjan

---

> [!IMPORTANT]
> ### CURRENT STATUS: ARCHITECTURE & SPECIFICATION PHASE ONLY
> **Implementation Status: NOT IMPLEMENTED YET.**
> This repository currently represents the authoritative, complete technical specification, architectural blueprints, data schemas, API contracts, threat models, and research validations for Code Cubicle 6.0 (Problem Statement 03).
> **No production application code, mock APIs, fake implementations, or UI code have been implemented in this phase.**

> [!CAUTION]
> ### MEDICAL SAFETY DISCLAIMER
> **EdgeMed is a TECHNICAL DEMONSTRATION / DECISION-SUPPORT RESEARCH PROTOTYPE.**
> - It utilizes **100% synthetic, procedurally generated medical data**.
> - It is **NOT** a certified medical device and must **NOT** be used as a primary diagnostic or therapeutic tool.
> - All clinical decisions must be validated by licensed medical professionals.

---

## Table of Contents
- [1. Problem Formulation](#1-problem-formulation)
- [2. Why Edge AI & Why Clinical Memory?](#2-why-edge-ai--why-clinical-memory)
- [3. Core High-Level Architecture](#3-core-high-level-architecture)
- [4. The Tripartite Hybrid Memory Model](#4-the-tripartite-hybrid-memory-model)
- [5. Key Architectural Features](#5-key-architectural-features)
- [6. Technology Stack & Hardware Feasibility](#6-technology-stack--hardware-feasibility)
- [7. Repository Structure](#7-repository-structure)
- [8. Implementation Roadmap](#8-implementation-roadmap)
- [9. Planned Hackathon Demonstration](#9-planned-hackathon-demonstration)
- [10. Research References](#10-research-references)

---

## 1. Problem Formulation

**Code Cubicle 6.0 — Problem Statement 03 (PS03)** challenges developers to construct an **AI-Powered Edge Memory & Intelligence Platform**. In decentralized, mission-critical environments—such as disaster relief zones, rural field clinics, military forward operating bases, and maritime vessels—connectivity is intermittent or non-existent.

When clinical staff treat patients in such environments:
- **Cloud-Dependent AI Fails:** Latency spikes, packet drops, or complete severed links leave clinicians without retrieval or decision support.
- **Data Sovereignty is Critical:** Patient records cannot be broadcast over unencrypted, public wireless links or stored indiscriminately in commercial clouds.
- **Flat Vector Search is Insufficient:** Semantic similarity alone cannot capture contraindications, drug-drug interactions, causal event progressions, or detect clinical contradictions.

EdgeMed solves this by engineering an **intelligent edge-memory platform** that maintains autonomous local recall, reconciles evolving facts, governs data lifecycles, and synchronizes selectively when connectivity returns.

---

## 2. Why Edge AI & Why Clinical Memory?

### Why Edge AI?
1. **Zero-Latency In-Process Retrieval:** In acute clinical triage, sub-millisecond query response is non-negotiable.
2. **Deterministic Offline Autonomy:** Edge devices must operate continuously through days or weeks of network blackout.
3. **Physical Data Containment:** Medical data remains on physical hardware under clinician supervision until explicitly vetted for upstream replication.

### Why Clinical Memory?
Memory is not simply caching text strings. Clinical memory must maintain:
- **Provenance:** Who observed this? What device recorded it? What evidence supports it?
- **Temporality:** How did the patient's symptoms evolve over the past 48 hours?
- **Topological Integrity:** What medications directly contraindicate this diagnosed condition?
- **Contradiction Awareness:** When a new lab test invalidates an earlier assumption, both records must be reconciled, not silently overwritten.

---

## 3. Core High-Level Architecture

EdgeMed strictly adheres to the principle: **Do not make Qdrant responsible for everything.** The architecture decouples vector search, relational graph topology, event chronologies, data governance, and cloud replication.

```
                         ┌─────────────────────┐
                         │    QDRANT SERVER    │
                         │                     │
                         │ Global Knowledge    │
                         │ Shared Memory       │
                         │ Central Index       │
                         └──────────┬──────────┘
                                    │
                              Synchronization
                                    │
                         ┌──────────▼──────────┐
                         │   MEMORY GOVERNOR   │
                         │                     │
                         │ Privacy             │
                         │ Relevance           │
                         │ Confidence          │
                         │ Freshness           │
                         │ Importance          │
                         │ Recurrence          │
                         │ Device specificity  │
                         └──────────┬──────────┘
                                    │
                  ┌─────────────────┼─────────────────┐
                  │                 │                 │
                  ▼                 ▼                 ▼
               LOCAL             SYNC             EXPIRE
                  │                 │
                  ▼                 ▼
          ┌──────────────┐    Qdrant Server
          │ Qdrant Edge  │
          └──────┬───────┘
                 │
       ┌─────────┼─────────┐
       ▼         ▼         ▼
    Vector     Graph    Timeline
    Memory     Memory   Memory
       │         │         │
       └─────────┼─────────┘
                 ▼
          Context Fusion
                 │
                 ▼
             Local AI
                 │
                 ▼
                UI
```

---

## 4. The Tripartite Hybrid Memory Model

Rather than flattening all clinical data into a single vector space, EdgeMed models memory across three interconnected dimensions:

```
                  ┌─────────────────────────────────────────┐
                  │       TRIPARTITE CLINICAL MEMORY        │
                  └────────────────────┬────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
┌──────────────────┐          ┌──────────────────┐          ┌──────────────────┐
│  VECTOR MEMORY   │          │ KNOWLEDGE GRAPH  │          │ TEMPORAL MEMORY  │
│  (Qdrant Edge)   │          │     (SQLite)     │          │  (Event Journal) │
├──────────────────┤          ├──────────────────┤          ├──────────────────┤
│ • Unstructured   │          │ • Explicit       │          │ • Longitudinal   │
│   clinical notes │          │   Ontology       │          │   Causality      │
│ • Fuzzy symptoms │          │ • Patient, Drug, │          │ • Observation →  │
│ • Semantic match │          │   Condition      │          │   Follow-up →    │
│ • In-process ANN │          │ • Strict multi-  │          │   Treatment →    │
│   retrieval      │          │   hop edges      │          │   Outcome        │
└────────┬─────────┘          └────────┬─────────┘          └────────┬─────────┘
         │                             │                             │
         └─────────────────────────────┼─────────────────────────────┘
                                       ▼
                       ┌───────────────────────────────┐
                       │     CONTEXT FUSION ENGINE     │
                       │ Reciprocal Rank Fusion (RRF)  │
                       │      + Relational Filters     │
                       │     + Temporal Recency Decay  │
                       └───────────────────────────────┘
```

1. **Vector Memory (Qdrant Edge):** In-process storage of dense embeddings (FastEmbed `bge-small-en-v1.5`) and sparse BM25 vectors for semantic recall over natural-language clinical narratives.
2. **Knowledge Graph (SQLite Relational Edges):** Formal medical ontology connecting entities (`Patient`, `Condition`, `Medication`, `Procedure`, `Observation`) via explicit directed relationships (`HAS_CONDITION`, `TREATED_WITH`, `CONTRADICTS`, `SUPERSEDES`).
3. **Temporal Memory (Event Journal):** Longitudinal event tracking modeling clinical progression across time windows, applying decay curves to transient observations while preserving chronic baselines.

---

## 5. Key Architectural Features

- **Offline-First Resilience:** Ingest, search, graph traverse, and govern with zero network interfaces active.
- **Dual-Shard Storage Pattern:** Instant unindexed writes to a local mutable shard; offloaded server-side HNSW index construction pulled via partial snapshots.
- **Multi-Signal Memory Governor:** Governs memory retention (`LOCAL`, `SYNC_CANDIDATE`, `EXPIRE`) using a multi-factor score (relevance, confidence, importance, freshness, recurrence, device specificity).
- **Four-Tier Privacy Firewall:** Inspects and sanitizes payloads before network transmission (`PUBLIC`, `INTERNAL`, `SENSITIVE`, `HIGHLY_SENSITIVE`).
- **Contradiction Lifecycle State Machine:** Prevents dangerous silent overwrites by explicitly flagging opposing clinical statements (`CONFIRMED`, `CONFLICTING`, `SUPERSEDED`, `REQUIRES_REVIEW`).
- **Memory Consolidation Worker:** Automatically clusters repeated observations, compressing storage while linking back to full provenance audit records.
- **Cryptographic Provenance DAG:** Every memory point records origin device, actor, source document hash, contributing memories, and transformation lineage.

---

## 6. Technology Stack & Hardware Feasibility

Designed and budgeted specifically for resource-constrained laptops and edge nodes:
- **Target Hardware:** AMD Ryzen 5 5500U (6C/12T), 8.0 GB RAM, Integrated Radeon Graphics, Linux OS.
- **Local Vector Engine:** Qdrant Edge (`qdrant-edge-py`, in-process Rust core).
- **Local Embedding Engine:** FastEmbed with ONNX Runtime (`BAAI/bge-small-en-v1.5`, 384-d, INT8/FP16 quantized).
- **Structured State & Graph:** SQLite 3 with Write-Ahead Logging (WAL).
- **Application Backend:** Python 3.11+ / FastAPI (Async ASGI).
- **Frontend / Memory Lab:** React 18 / TypeScript with Vite, Cytoscape.js for interactive knowledge graphs.
- **Central Vector Node:** Qdrant Server (Containerized / Cloud instance for snapshot testing).

*Working RAM Allocation:* Total platform runtime footprint is budgeted at **<450 MB RAM**, leaving over 7 GB of memory headroom.

---

## 7. Repository Structure

```
.
├── README.md                          # Single source of truth overview
├── LICENSE                            # Apache 2.0 open-source license
├── CONTRIBUTING.md                     # Contributor guidelines & code of conduct
├── SECURITY.md                        # Threat model, vulnerability reporting & disclosures
├── .gitignore                         # Environment, storage, and build exclusions
│
├── docs/                              # Comprehensive engineering specifications
│   ├── 00-overview/                   # Vision, problem statement, goals, non-goals, glossary
│   ├── 01-requirements/               # Functional, edge, sync, privacy requirements & acceptance
│   ├── 02-architecture/               # System, component, data flow, edge, cloud, offline, security
│   ├── 03-memory/                     # Tripartite model, provenance, consolidation, contradiction
│   ├── 04-intelligence/               # Embeddings, query router, context fusion, governor, firewall
│   ├── 05-synchronization/            # Synchronization queues, conflict resolution, connectivity model
│   ├── 06-interface/                  # UX overview, dashboard, memory explorer, graph UI, memory lab
│   ├── 07-api/                        # Complete REST & WebSocket API endpoint contracts
│   ├── 08-data/                       # Data schemas, database models, and payload representations
│   ├── 09-testing/                    # Testing strategy, offline scenarios, performance benchmarks
│   ├── 10-deployment/                 # Dev environment setup, edge hardware configuration
│   ├── 11-roadmap/                    # Phases 0-14, milestones, deliverables, future horizons
│   ├── research/                      # Authoritative Qdrant Edge research & technology tradeoffs
│   ├── requirements-traceability.md   # Full traceability matrix (PS03 -> Acceptance Tests)
│   └── PROJECT_STATUS.md              # Authoritative phase tracking & open questions
│
├── architecture/                      # Architectural assets
│   ├── decisions/                     # Architecture Decision Records (ADR-001 through ADR-010)
│   ├── diagrams/                      # Standalone Mermaid diagrams for all subsystems
│   └── c4/                            # C4 Model Context and Container specifications
│
├── api/
│   └── openapi/
│       └── openapi.yaml               # Formal OpenAPI 3.1.0 contract for all endpoints
│
├── schemas/                           # Formal JSON Schema specifications
│   ├── memory.schema.json             # Core Memory Record JSON Schema
│   ├── entity.schema.json             # Knowledge Graph Entity Schema
│   ├── relation.schema.json           # Knowledge Graph Relation Schema
│   ├── event.schema.json              # Temporal Event Progression Schema
│   ├── sync-record.schema.json        # Synchronization Queue Item Schema
│   ├── governance-decision.schema.json# Memory Governor Evaluation Schema
│   ├── search-result.schema.json      # Hybrid Search Result & Explainability Schema
│   └── provenance-record.schema.json  # Audit Provenance Record Schema
│
├── examples/                          # Synthetic test fixtures and scenarios
│   ├── synthetic-patient-data.json    # Synthetic patient clinical profiles
│   ├── sample-memories.json           # Sample vector and payload memories
│   ├── sample-knowledge-graph.json    # Clinical entity-relationship graph export
│   ├── sample-sync-payload.json       # Partial snapshot sync queue payloads
│   └── sample-governance-eval.json    # Memory Governor sample inputs and decisions
│
└── .github/                           # GitHub engineering governance
    ├── ISSUE_TEMPLATE/                # ADR, Feature, Bug, Research, Docs issue templates
    ├── pull_request_template.md       # Pull request checklist and safety criteria
    └── workflows/
        └── docs-validation.yml        # CI workflow verifying markdown, schemas, and links
```

---

## 8. Implementation Roadmap

| Phase | Milestone | Focus Area | Deliverables | Status |
| :---: | :--- | :--- | :--- | :---: |
| **0** | **Architecture & Specs** | System Design & Single Source of Truth | Complete technical specifications, schemas, ADRs | **CURRENT** |
| **1** | **Qdrant Edge Spike** | In-Process Embedded Engine | Shard lifecycle, local vector upsert & search validation | Upcoming |
| **2** | **Local Embeddings** | FastEmbed Integration | CPU ONNX pipeline, tokenization, batch encoding | Upcoming |
| **3** | **Persistent Memory API** | FastAPI + SQLite Core | CRUD memory endpoints, WAL journal, schema validation | Upcoming |
| **4** | **Semantic Search** | Hybrid Dense + Sparse Retrieval | RRF search, payload filtering, latency benchmarks | Upcoming |
| **5** | **Knowledge Graph** | Relational Entity Topology | SQLite adjacency graph, graph traversal, cyto export | Upcoming |
| **6** | **Temporal Progression** | Event Chronology Engine | Longitudinal timeline, recency decay, causal chaining | Upcoming |
| **7** | **Memory Governor** | Retention & Lifecycle Rules | Multi-factor scoring, LOCAL/SYNC/EXPIRE routing | Upcoming |
| **8** | **Privacy Firewall** | Redaction & Security Policy | Sensitivity classification, PHI scrubbing, local pinning | Upcoming |
| **9** | **Offline/Online State** | Connectivity Manager | Link detection, heartbeat, offline queue transition | Upcoming |
| **10**| **Server Synchronization**| Qdrant Server Replication | Dual-write queue, partial snapshot recovery | Upcoming |
| **11**| **Conflict Resolution** | Contradiction State Machine | Branching versions, human review flags, deduplication | Upcoming |
| **12**| **UI & Memory Lab** | Interactive Exploration Suite | Dashboard, Cytoscape graph, inspector, simulation HUD | Upcoming |
| **13**| **Benchmarking & Testing**| Quality & Stress Testing | Offline failover tests, memory leaks, latency suite | Upcoming |
| **14**| **Demo Hardening** | Code Cubicle 6.0 Delivery | Polished presentation walkthrough, demo scripts | Upcoming |

---

## 9. Planned Hackathon Demonstration

The planned demonstration for the Code Cubicle 6.0 judging panel showcases an end-to-end clinical workflow across fluctuating network states:
1. **Online Baseline:** Device connects to central hospital node, populates shared medical knowledge and snapshot shards.
2. **Network Severance:** Network connection is severed (simulated flight mode). Edge device transitions seamlessly to autonomous state.
3. **Offline Semantic Search:** Clinician searches for complex clinical presentations; Qdrant Edge answers in <1ms without internet.
4. **Offline Observation Ingestion:** Clinician records new vital signs and an updated patient symptom. Local mutable shard stores points instantly.
5. **Memory Governor Evaluation:** Governor marks patient notes as `SENSITIVE` and pins raw observations locally, queuing sanitized medical statistics for synchronization.
6. **Network Re-establishment:** Network returns. Privacy Firewall scrubs identifiers; approved records stream to central Qdrant Server.
7. **Cross-Device Knowledge Propagation:** Central server optimizes HNSW graph; a second edge device receives updated clinical guidance via partial snapshot.
8. **Interactive Visual Proof:** Clinician opens the **Memory Lab** and inspects the Cytoscape knowledge graph, verifies provenance audit trails, and inspects the contradiction resolution log.

---

## 10. Research References

1. **Qdrant Edge Official Documentation:** https://qdrant.tech/documentation/edge/
2. **Qdrant Edge vs. Qdrant Cluster:** https://qdrant.tech/documentation/edge/edge-vs-qdrant-cluster/
3. **Qdrant Edge Data Synchronization Patterns:** https://qdrant.tech/documentation/edge/edge-data-synchronization-patterns/
4. **Qdrant Edge Smart Glasses Reference Demo:** https://github.com/qdrant/qdrant-edge-demo
5. **Qdrant Edge Mission Control Robot Memory:** https://github.com/qdrant-labs/edge-mission-control
6. **FastEmbed Python Documentation:** https://qdrant.github.io/fastembed/
7. **SQLite Write-Ahead Logging Design:** https://www.sqlite.org/wal.html

---

*Authored by Team LEX for Code Cubicle 6.0 — Problem Statement 03.*
