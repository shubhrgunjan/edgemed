# ADR-009: Privacy-Aware Synchronization and Privacy Firewall

- **Status:** Approved / Core Architectural Boundary
- **Date:** 2026-09-26
- **Author:** Team LEX (Code Cubicle 6.0 — PS03)

## Context
When synchronizing edge clinical memories with a centralized Qdrant Server or peer edge devices, patient identifiers and highly sensitive observations must not leak beyond authorized administrative or physical boundaries.

## Problem
Naively replicating local vector payloads to a centralized cloud vector database exposes sensitive patient notes, local device IDs, and identifiable clinical narratives to cloud breaches or unauthorized external access.

## Options Considered
1. **Unrestricted Dual-Write Replication:** Immediately copies every local point to the server. Completely unacceptable for medical privacy.
2. **Encrypted Payload Sync without Field Inspection:** The cloud stores encrypted blobs, but this prevents central semantic querying over anonymized medical knowledge and cross-device learning.
3. **Four-Tier Privacy Firewall:** Implements an inline inspection barrier between local memory and the outbound sync queue. Classifies records into `PUBLIC`, `INTERNAL`, `SENSITIVE`, and `HIGHLY_SENSITIVE`. Only sanitized/redacted data transitions to cloud sync; `HIGHLY_SENSITIVE` records are permanently pinned to local device storage.

## Decision
Adopt the **Privacy Firewall** with explicit privacy classifications. In clinical mode, all patient-specific synthetic records default to local-only behavior (`SENSITIVE` or `HIGHLY_SENSITIVE`) unless explicitly transformed, anonymized, or approved for synchronization.

## Consequences
- **Positive:** Guarantees data sovereignty on edge devices; prevents accidental leakage of identifiable information; provides verifiable privacy logs.
- **Negative:** Introduces classification and redaction overhead in the synchronization pipeline; requires user confirmation or policy definitions for borderline records.
