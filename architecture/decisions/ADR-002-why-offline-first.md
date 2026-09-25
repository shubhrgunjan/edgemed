# ADR-002: Offline-First Architectural Paradigm

- **Status:** Approved / Foundation Principle
- **Date:** 2026-09-26
- **Author:** Team LEX (Code Cubicle 6.0 — PS03)

## Context
EdgeMed operates in medical, field-clinic, and disaster-response environments where network infrastructure is intermittent, congested, or non-existent.

## Problem
Many "hybrid" architectures treat offline mode as an exception handler or fallback state. This leads to broken user experiences, unhandled timeout cascades, blocking network calls, and data loss when connectivity fluctuates.

## Options Considered
1. **Cloud-First with Offline Cache:** Requests are sent to the cloud by default; local cache is consulted only on network timeout. Results in severe UI latency (seconds waiting for timeouts) and fragile offline transitions.
2. **Offline-First:** All read and write operations execute locally against on-device storage (Qdrant Edge and SQLite). Synchronization is an asynchronous, opportunistic background daemon that activates only when verified connectivity exists.

## Decision
Adopt a strict **Offline-First** architecture. Local storage is the primary source of truth for the local operator. The system guarantees 100% feature availability for local ingestion, search, graph navigation, and governance without a network interface active.

## Consequences
- **Positive:** Zero latency penalty when offline; deterministic sub-millisecond retrieval; resilient to intermittent connectivity; complete privacy boundary while disconnected.
- **Negative:** Requires sophisticated local conflict detection, persistent synchronization queues, and reconciliation logic when reconnecting.
