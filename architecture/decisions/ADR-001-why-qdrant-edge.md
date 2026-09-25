# ADR-001: Selection of Qdrant Edge as Embedded Vector Engine

- **Status:** Proposed / Architectural Baseline (Requires Empirical Shard Validation in Phase 1)
- **Date:** 2026-09-26
- **Author:** Team LEX (Code Cubicle 6.0 — PS03)

## Context
EdgeMed requires a low-latency, embedded semantic search capability that operates autonomously on edge hardware without continuous internet access or heavy cloud background services.

## Problem
Traditional vector databases (e.g., Pinecone, Milvus, Weaviate) are client-server architectures that assume reliable high-bandwidth network connectivity and multi-node clusters. Embedded options like Chroma or DuckDB either lack native Rust-level performance or lack first-class differential snapshot synchronization with an upstream central vector server.

## Options Considered
1. **Cloud-only Vector Database:** Fails immediately under PS03 requirements due to zero offline functionality and privacy leakage.
2. **SQLite-VSS / SQLite-Vec:** Lightweight and single-file, but lacks advanced HNSW tuning, payload indexing flexibility, and native snapshot replication pipelines.
3. **Qdrant Edge (`qdrant-edge-py`):** In-process, Rust-backed embedded vector search engine sharing core engine internals with Qdrant Server, supporting snapshot-based partial segment replication.

## Decision
Adopt **Qdrant Edge** as the embedded semantic vector storage engine. Decouple write operations using the Dual-Shard design pattern (local unindexed mutable shard for instant ingestion; server-replicated immutable shard for HNSW structures).

## Consequences
- **Positive:** True in-process vector retrieval (<1ms latency); zero external daemon overhead; memory-mapped file I/O fits 8 GB RAM machines; snapshot synchronization compatibility with central Qdrant Server.
- **Negative:** Qdrant Edge is officially in Beta; APIs may evolve; it does not provide knowledge graph relations, temporal progressions, or automatic bidirectional conflict handling, requiring EdgeMed to construct these layers.
