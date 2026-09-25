# Privacy Requirements Specification

- **Document Version:** 1.0.0
- **Status:** Complete / Authoritative Matrix
- **Date:** 2026-09-26
- **Lead Security Architect:** Team LEX (Code Cubicle 6.0 — PS03)

---

## 1. Privacy Requirements Matrix

| ID | Requirement Description | Source | Priority | Component | Acceptance Test | Target / Verification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-PRIV-001** | The system must classify every memory record into one of four privacy tiers (`PUBLIC`, `INTERNAL`, `SENSITIVE`, `HIGHLY_SENSITIVE`). | PS03 | Critical | Privacy Classifier | `TEST-008` | Assign classification tag to payload; verify tag persistence and validation. |
| **REQ-PRIV-002** | Records marked `HIGHLY_SENSITIVE` must be permanently restricted to local device storage and forbidden from synchronization. | PS03 | Critical | Privacy Firewall | `TEST-008` | Trigger sync; verify `HIGHLY_SENSITIVE` record is excluded from outbound queue and server. |
| **REQ-PRIV-003** | Records marked `SENSITIVE` must undergo automated scrubbing of synthetic patient identifiers prior to synchronization. | PS03 | High | Redaction Engine | `TEST-007` | Sync `SENSITIVE` record; verify patient name, DOB, and device ID are sanitized in cloud payload. |
| **REQ-PRIV-004** | The system must default all patient-specific synthetic records to local-only behavior unless explicitly cleared. | Healthcare Best Practice | Critical | Memory Governor | `TEST-008` | Create clinical observation without explicit policy; verify default state is `LOCAL`. |
| **REQ-PRIV-005** | Memory provenance logs must preserve the redaction history and policy decision ID for auditing. | Audit Requirement | High | Provenance Tracker | `TEST-011` | Query provenance of synced record; verify redaction transform record is attached. |
