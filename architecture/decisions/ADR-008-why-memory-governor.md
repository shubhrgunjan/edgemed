# ADR-008: The Memory Governor Lifecycle & Retention Engine

- **Status:** Proposed / Core Innovation (Requires Heuristic Validation in Phase 7)
- **Date:** 2026-09-26
- **Author:** Team LEX (Code Cubicle 6.0 — PS03)

## Context
Edge storage is finite, while observations and clinical telemetry continuously accumulate. Without active memory management, local edge storage will exhaust disk capacity, degrade retrieval performance, and push noise or transient data upstream.

## Problem
Standard vector databases append data indefinitely until disk exhaustion occurs. Traditional LRU (Least Recently Used) cache eviction is dangerous in medical contexts—a vital allergy or chronic diagnosis recorded months ago might not be accessed frequently, yet evicting it could lead to fatal clinical errors.

## Options Considered
1. **Unbounded Storage Growth:** Causes edge crash when disk fills.
2. **Simple LRU / FIFO Eviction:** Evicts critical, infrequently accessed medical baselines (e.g., severe anaphylactic allergies).
3. **Multi-Signal Memory Governor:** Evaluates clinical importance, confidence, recurrence, freshness, privacy level, and device specificity to govern lifecycle transitions: `LOCAL`, `SYNC_CANDIDATE`, or `EXPIRE`.

## Decision
Design and implement the **Memory Governor**. Every memory record is evaluated by a proposed scoring algorithm that balances clinical importance against storage pressure, protecting high-importance memories from eviction while routing eligible knowledge to cloud sync or expiration.

## Consequences
- **Positive:** Protects vital clinical data from unprincipled eviction; prevents edge disk saturation; prevents uploading transient telemetry noise to the central server.
- **Negative:** The scoring weights are proposed heuristics that must be tuned through empirical simulations in Phase 7.
