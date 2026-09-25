# Related Projects and Prior Art Analysis

- **Document Version:** 1.0.0
- **Status:** Complete / Reference Document
- **Date:** 2026-09-26
- **Lead System Designer:** Team LEX (Code Cubicle 6.0 — PS03)

---

## 1. Executive Summary

This document evaluates relevant open-source systems, architectural patterns, and academic concepts in edge computing, vector retrieval, and long-term memory architectures. The goal is to extract proven patterns, identify failure modes, and ensure **EdgeMed** builds upon established best practices without duplicating structural flaws.

---

## 2. Comparative Systems Analysis

| Project / Pattern | Core Architecture | Key Strengths | Critical Gaps Addressed by EdgeMed |
| :--- | :--- | :--- | :--- |
| **Qdrant Edge Smart Glasses Demo** (`qdrant/qdrant-edge-demo`) | Dual-shard architecture (mutable local shard + immutable indexed shard) + SQLite sync queue. | Highly efficient pattern for decoupling on-device capture from server-side HNSW index construction. | Purely image/vision focused. Lacks clinical entity graphs, temporal reasoning, memory governance, and privacy filtering. |
| **Edge Mission Control** (`qdrant-labs/edge-mission-control`) | Single-process embedded Python pipeline running FastEmbed/SigLIP2, sparse BM25, and Qdrant Edge in-process. | Demonstrates sub-millisecond local hybrid search (dense + sparse RRF) with zero external daemon dependencies. | Designed for single-device robot patrol. No cloud sync, no multi-device coordination, and no contradiction detection. |
| **MemGPT / Letta** | Hierarchical memory tiers (Working Context, Recall Storage, Archival Storage) managed via LLM function calling. | Elegant abstraction of human-like multi-tiered memory and paging mechanisms. | Cloud-dependent; assumes constant access to high-parameter LLMs for memory management. Infeasible for constrained offline edge devices. |
| **Zep / Mem0** | Graph-augmented vector memory engines for agentic conversations. | Merges vector retrieval with knowledge graphs for relationship extraction. | Server-centric architecture requiring containerized Neo4j/Postgres backends. Unsuitable for embedded offline edge runtimes. |
| **SQLite with `sqlite-vss` / `sqlite-vec`** | Relational database with vector search virtual table extensions. | Single-file zero-configuration simplicity and ACID transaction guarantees. | Limited vector indexing flexibility; primitive ANN algorithms compared to Qdrant's dedicated Rust segment architecture. |

---

## 3. Deep Architectural Lessons

### 3.1 Lesson 1: The Trap of "Vector-Only" Memory
Traditional Retrieval-Augmented Generation (RAG) systems assume that representing all knowledge as flat vector embeddings is sufficient. In clinical and medical workflows, this fails catastrophically:
- **Loss of Negation:** Semantic embeddings often map "Patient has diabetes" and "Patient does not have diabetes" to very high cosine similarity scores (>0.88).
- **Loss of Topology:** A vector cannot explicitly represent transitive relationships (e.g., `Patient -> HasCondition(Hypertension) -> TreatedWith(Lisinopril) -> ContraindicatedWith(PotassiumSpares)`).
- **Loss of Temporality:** An observation from 3 years ago and an observation from 10 minutes ago look semantically identical to a vector similarity query.

**EdgeMed Solution:** We institute the **Tripartite Memory Model**—coupling Qdrant Edge vector retrieval with an explicit relational knowledge graph and an event timeline progression engine.

### 3.2 Lesson 2: Asymmetric Edge-Cloud Workloads
Mobile and embedded edge CPUs experience severe power draw and thermal throttling when executing heavy approximate nearest neighbor (ANN) graph construction over thousands of items.

**EdgeMed Solution:** We leverage the **Dual-Shard Pattern** validated in `qdrant-edge-demo`. Write operations on the edge commit to a flat, unindexed mutable shard. Complex HNSW graph optimization is performed on the central Qdrant Server, and returned as compressed, memory-mapped immutable segments.

### 3.3 Lesson 3: The Danger of Autonomous Sync without Governance
In medical environments, directly mirroring all edge writes to a central cloud server introduces severe privacy violations (HIPAA/GDPR breaches) and distributes corrupted or conflicting local observations across hospital fleets.

**EdgeMed Solution:** EdgeMed introduces the **Memory Governor** and **Privacy Firewall** between the local storage engine and the outbound sync queue. Information is classified and filtered prior to cloud replication.
