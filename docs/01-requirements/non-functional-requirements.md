# Non-Functional Requirements Specification

- **Document Version:** 1.0.0
- **Status:** Complete / Authoritative Matrix
- **Date:** 2026-09-26
- **Lead Systems Engineer:** Team LEX (Code Cubicle 6.0 — PS03)

---

## 1. Non-Functional Requirements Matrix

| ID | Requirement Description | Source | Priority | Component | Acceptance Test | Target Metric |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-PERF-001** | Local vector query latency must be sub-millisecond for up to 10,000 points. | PS03 | Critical | Qdrant Edge | `TEST-004` | `< 5.0 ms` response time (TARGET) |
| **REQ-PERF-002** | Local text embedding generation must execute efficiently on consumer CPU. | Hardware Constraint | High | FastEmbed ONNX | `TEST-001` | `< 18.0 ms` per text snippet on AMD Ryzen 5 5500U (TARGET) |
| **REQ-PERF-003** | Total resident working set memory must remain under strict edge device limits. | Hardware Constraint | Critical | Edge Runtime | Profiling Suite | `< 450 MB` RAM total working set (TARGET) |
| **REQ-RELY-001** | Local state must survive ungraceful process termination without data corruption. | Architecture | Critical | SQLite WAL & Qdrant Edge | `TEST-002`, `TEST-003` | Kill `-9` during write; verify DB opens cleanly with zero point loss. |
| **REQ-SECU-001** | All outbound synchronization network traffic must be encrypted in transit. | Security Baseline | Critical | Replicator Client | `TEST-007` | Enforce TLS 1.3 / mTLS on sync endpoints. |
| **REQ-USAB-001** | Interface must provide clear visual indication of connectivity state within 500ms of link change. | PS03 | Medium | Frontend Status HUD | `TEST-004`, `TEST-006` | Sever network; verify UI displays "OFFLINE MODE" banner in <500ms. |
| **REQ-SCAL-001** | Edge device must support storing and searching at least 50,000 clinical memory points locally without disk overflow. | Capacity Planning | High | Storage Engine | Stress Suite | Storage footprint `< 250 MB` on disk for 50k points (TARGET). |
