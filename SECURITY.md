# Security Policy and Threat Model

- **Document Version:** 1.0.0
- **Status:** Complete / Active Security Baseline
- **Date:** 2026-09-26
- **Lead Security Architect:** Team LEX (Code Cubicle 6.0 — PS03)

---

## 1. Safety and Clinical Status Disclaimer

> [!CAUTION]
> **EdgeMed is a TECHNICAL DEMONSTRATION / DECISION-SUPPORT RESEARCH PROTOTYPE.**
> It is strictly designed for technical evaluation and hackathon judging under Code Cubicle 6.0 (Problem Statement 03). It is **not** a certified medical device (FDA 510(k), CE mark, or HIPAA-certified software).
> All test fixtures and sample data are 100% synthetic. Real clinical Protected Health Information (PHI) or Personally Identifiable Information (PII) must never be loaded into this prototype.

---

## 2. Threat Model

Edge devices deployed in decentralized environments (e.g., field clinics, ambulances, remote triage stations) operate outside physically secure data centers. Consequently, the threat surface includes both traditional network vectors and physical hardware tampering.

```
                                THREAT MODEL BOUNDARY
 ┌─────────────────────────────────────────────────────────────────────────────────┐
 │                                EDGE DEVICE                                      │
 │                                                                                 │
 │  ┌───────────────────────┐   Local IPC    ┌──────────────────────────────────┐  │
 │  │      Operator UI      │◄──────────────►│    EdgeMed Backend (FastAPI)     │  │
 │  └───────────────────────┘                └─────────────────┬────────────────┘  │
 │                                                             │                   │
 │           [ Threat: Compromised Device / Storage Dump ]     │                   │
 │                                                             ▼                   │
 │                   ┌──────────────────────────────────────────────────┐          │
 │                   │  Local Encrypted Storage (Qdrant Edge + SQLite)  │          │
 │                   └──────────────────────────────────────────────────┘          │
 │                                                             │                   │
 │                                                             ▼                   │
 │                                            ┌─────────────────────────────────┐  │
 │                                            │   PRIVACY FIREWALL & GOVERNOR   │  │
 │                                            └────────────────┬────────────────┘  │
 └─────────────────────────────────────────────────────────────┼───────────────────┘
                                                               │
                          [ Threat: Man-in-the-Middle Link ]   │  mTLS Encrypted Sync
                          [ Threat: Malicious Sync Payload ]   │
                                                               ▼
                                              ┌─────────────────────────────────┐
                                              │      CENTRAL QDRANT SERVER      │
                                              └─────────────────────────────────┘
```

### Detailed Threat Analysis and Mitigations

| Threat ID | Threat Vector | Impact | Planned Mitigation in Architecture |
| :--- | :--- | :--- | :--- |
| **THREAT-01** | **Physical Device Compromise / Lost Hardware** | Unauthorized extraction of local vector embeddings and SQLite clinical notes from disk. | Local storage directory encryption via LUKS / SQLCipher; sensitive vector payloads stored as non-reversible embeddings with separate keyed pseudonymization tables. |
| **THREAT-02** | **Data Leakage during Cloud Sync** | Accidental broadcast of identifiable patient notes across public hospital networks. | **Privacy Firewall**: Strict four-tier classification (`PUBLIC`, `INTERNAL`, `SENSITIVE`, `HIGHLY_SENSITIVE`). `HIGHLY_SENSITIVE` records are blocked from sync; `SENSITIVE` records are stripped of identifiers before entering the outbound sync queue. |
| **THREAT-03** | **Malicious Synchronization Payload** | An attacker injects corrupted clinical guidelines, false contraindications, or poisoned embeddings via the central server sync stream. | Cryptographic signature verification on incoming snapshots; strict Pydantic schema validation; point provenance verification before merging into local knowledge graph. |
| **THREAT-04** | **Prompt Injection via Ingested Documents** | Adversarial text embedded in imported medical notes attempts to hijack downstream local LLM or extraction pipelines. | Context isolation; structured schema parsing before LLM handoff; prompt boundaries with delimited text blocks; strict prohibition of raw executable eval. |
| **THREAT-05** | **Memory Tampering & Historical Alteration** | Malicious or accidental modification of past clinical findings to hide medical malpractice or diagnostic error. | **Cryptographic Provenance DAG**: Append-only event journaling in SQLite; content hashing (SHA-256) of observation records; changes create new superseding nodes rather than overwriting historical records. |
| **THREAT-06** | **Stale Information Propagation** | An edge device disconnected for months reconnects and pushes outdated clinical protocols that overwrite recent hospital findings. | Vector-clock and timestamped versioning in `SyncRecord`; Memory Governor rejects stale lower-version updates; conflicts trigger `REQUIRES_REVIEW` state. |
| **THREAT-07** | **Conflicting Medical Updates** | Divergent clinical observations from multiple edge devices create clinical ambiguity (e.g., conflicting drug dosages). | **Contradiction Lifecycle State Machine**: System detects opposing assertions, creates explicit `CONTRADICTS` graph edges, and presents both records side-by-side in the Memory Lab for clinician adjudication. |

---

## 3. Vulnerability Reporting Procedure

If you discover a security vulnerability or privacy boundary defect within this repository:
1. **Do not create a public GitHub issue.**
2. Send a detailed vulnerability report to Team LEX security leads via encrypted channel or contact team maintainers directly.
3. Include reproduction steps, affected schemas/endpoints, and potential impact assessment.
4. The team will acknowledge receipt within 48 hours and coordinate remediation before disclosure.
