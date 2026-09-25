# ADR-006: Strict Utilization of Synthetic Clinical Datasets

- **Status:** Approved / Safety & Compliance Mandate
- **Date:** 2026-09-26
- **Author:** Team LEX (Code Cubicle 6.0 — PS03)

## Context
The project demonstrates an edge-memory platform within a clinical / healthcare scenario for Code Cubicle 6.0. Handling real Protected Health Information (PHI) or real Electronic Health Records (EHR) introduces severe legal, ethical, and regulatory hurdles (HIPAA, GDPR, ethical board approvals).

## Problem
Demonstrating realistic medical edge-intelligence, conflict resolution, and privacy redaction requires rich, plausible clinical data without using genuine patient records or presenting the prototype as a diagnostic tool.

## Options Considered
1. **Anonymized Real Clinical Records (e.g., MIMIC-III subset):** Complex licensing restrictions; risk of re-identification; heavy data processing pipeline.
2. **Generic Non-Medical Data (e.g., wiki articles):** Weakens the problem demonstration and fails to showcase high-stakes conflict resolution and privacy constraints.
3. **Structured Synthetic Medical Data (Synthea-inspired / Clinical Guideline scenarios):** Procedurally generated patients, conditions, medications, and clinical observations containing intentional test anomalies (contradictions, updates, privacy tiers).

## Decision
Mandate that **all data ingested, indexed, and synchronized across EdgeMed is 100% synthetic**. EdgeMed is explicitly defined as a **Technical Demonstration / Decision-Support Research Prototype**, not a clinical diagnostic system.

## Consequences
- **Positive:** Zero risk of PHI leakage or regulatory violation; enables repeatable, deterministic unit tests for contradiction detection and privacy firewalls.
- **Negative:** Requires crafting realistic synthetic clinical scenarios for hackathon demonstrations.
