# Conflict and Contradiction Testing Specifications

- **Document Version:** 1.0.0
- **Status:** Complete
- **Date:** 2026-09-26

---

## 1. Scope of Conflict Tests

- `test_contradictory_clinical_assertions`:
  - Step 1: Ingest "Patient has active diagnosis: Bacterial Pneumonia".
  - Step 2: Ingest "Sputum culture confirms Viral Bronchitis, no bacterial pathology".
  - Assert: Both records remain in storage; both records marked `CONFLICTING`; relation `CONTRADICTS` established; zero silent overwrites.
- `test_stale_server_version_rejection`:
  - Step 1: Local record updated to `version: 3`.
  - Step 2: Inbound server sync payload carries `version: 2`.
  - Assert: Inbound payload rejected; audit event logged; local version 3 remains untouched.
- `test_clinician_adjudication_flow`:
  - Step 1: Query conflicting pair via API.
  - Step 2: POST adjudication payload resolving in favor of Record B.
  - Assert: Record B transitions to `CONFIRMED`; Record A transitions to `SUPERSEDED`.
