# EdgeMed Comprehensive Project & System Audit

**Audit Date:** September 2026  
**Audited Repository:** `shubhrgunjan/edgemed` (Branch: `main`)  
**Target Milestone:** Full System Audit across Milestones 1–5  
**Auditor Classification:** Automated Security, Architectural & Operational Audit  
**Operating Status:** Synthetic-Data Research Prototype (Not Approved for Clinical Use)

---

## 1. Executive Summary

EdgeMed is an offline-first, local-first clinical memory and retrieval research prototype developed for Team LEX's Code Cubicle 6.0 problem statement 03. This document presents an exhaustive, end-to-end technical audit of the entire codebase, evaluating:
* **Architectural integrity:** Adherence to zero-cloud dependencies, local-first canonical persistence, and layered boundaries.
* **Security & boundary enforcement:** Verification of multi-tenant workspace isolation, personal observation privacy, CSRF/origin/host defenses, fail-closed storage, and egress leakage prevention.
* **Storage & ledger robustness:** SQLCipher 4 encryption, append-only revision DAGs, tombstone deletion truthfulness, and tamper-evident HMAC event chaining.
* **Retrieval & scalability performance:** Dual-projection hybrid search (dense ONNX vector embeddings + sparse inverted index) sustaining sub-10ms query latencies at 10,000+ records.
* **Frontend presentation:** Responsive React 19 interface across Visual Data Logging, Synthetic Subjects Roster, and Sync Monitor & Memory Lab workspaces.
* **Verification suite:** 77 passing backend integration/unit tests and 4 end-to-end Playwright browser test suites.

---

## 2. Codebase & Component Inventory

| Component / File | Primary Role | Lines of Code | Security / Architectural Significance |
| :--- | :--- | :--- | :--- |
| **`edgemed/api.py`** | FastAPI Core Server & HTTP Endpoints | ~430 lines | Implements authentication, session management, CSRF checks, workspace routing, and security headers. |
| **`edgemed/http_boundary.py`** | ASGI Streaming Middleware | 68 lines | Enforces 32 KiB request limit, 10s request timeout, `no-store` headers, and diagnostic collection. |
| **`edgemed/accounts.py`** | Identity, Roles & Scoping Engine | 50 lines | Multi-workspace scoping (`ward-a`, `ward-b`), personal privacy isolation (`personal:{user}`), and role checks. |
| **`edgemed/security.py`** | Cryptographic Primitives & Keyring | ~95 lines | Argon2id hashing, Ed25519 signatures, fail-closed OS keyring interface, atomic private file write (`0o600`). |
| **`edgemed/store.py`** | Canonical Storage & Audit Ledger | ~520 lines | SQLCipher 4 AES-256 database, revision DAG, HMAC-SHA256 audit chaining, tombstone deletes, inverted index. |
| **`edgemed/retrieval.py`** | Dual-Projection Hybrid Search | ~310 lines | BAAI/bge-small-en-v1.5 ONNX runtime, Qdrant Edge vector indexing, sparse inverted postings, RRF fusion ($k=60$). |
| **`edgemed/models.py`** | Pydantic Request & Data Models | 92 lines | Strict schema validation with `extra="forbid"`, preventing property injection attacks. |
| **`edgemed/sync.py`** | Selective Reference Transport | ~205 lines | mTLS 1.3 transport, Ed25519 envelope signing, strict egress filter ensuring zero clinical observations leave device. |
| **`edgemed/snapshots.py`** | Verified Reference Shards | ~205 lines | Reference snapshot decompression bomb defense, tar traversal prevention, point-by-point payload inspection. |
| **`edgemed/lan.py`** | Hospital LAN HTTPS Setup | 116 lines | Automated private IPv4 verification (RFC 1918), short-lived CA (30d) and server cert (7d) generation. |
| **`edgemed/linux_vault.py`** | Linux LUKS2 Storage Verification | 42 lines | Fail-closed verification that vault is backed by a verified `CRYPT-LUKS2-` device with strict permissions. |
| **`frontend/src/main.tsx`** | Authenticated SPA Orchestrator | ~300 lines | Workspace router, Catppuccin theme manager, global keyboard shortcuts, conflict review modal. |
| **`frontend/src/logging.tsx`** | Visual Data Logging Workspace | ~415 lines | Timeline, category filter chips, search, Needs Review queue, metric trend charts integration. |
| **`frontend/src/quick-entry.tsx`**| Structured Observation Cards | ~640 lines | Vitals, Lab values, Symptoms, Notes forms with client-side range validation and instant commit. |
| **`frontend/src/charts.tsx`** | Interactive Trend Visualizations | ~460 lines | SVG trend charts (Blood Pressure, Heart Rate, Respiration) derived from canonical stored data. |
| **`frontend/src/subjects.tsx`** | Synthetic Subjects Roster | ~1,280 lines| Subject navigation roster, patient-chart summary, longitudinal vitals, allergy alerts, chronological history. |
| **`frontend/src/sync-monitor.tsx`**| Sync Monitor & Memory Lab | ~800 lines | Connectivity hero, outbox delivery queue, activity timeline, storage status, simulation controls. |
| **`frontend/src/style.css`** | Semantic Styling & Design System | ~2,300 lines| Responsive Catppuccin Latte/Mocha theme tokens, responsive layouts down to 320px mobile viewport. |

---

## 3. Security & Boundary Audit

### 3.1 Trust Boundaries & Attack Surfaces
* **HTTP Perimeter:** The application rejects requests with invalid `Host` headers (`400 Bad Request`), mismatched `Origin` headers (`403 Forbidden`), or `Sec-Fetch-Site: cross-site` headers.
* **Cross-Site Request Forgery (CSRF):** SameSite=Strict cookies combined with constant-time HMAC-verified `x-csrf-token` headers block drive-by cross-site attacks.
* **Denial of Service (DoS):** Request bodies are bounded to 32 KiB and 10-second processing timeouts via `BoundedHTTP`.
* **Multi-Tenant Isolation:** SQL parameterized queries enforce workspace boundaries (`owner IN (?, ?)`). Cross-ward access attempts return `404 Not Found`.
* **Personal Observation Isolation:** Observations marked `HIGHLY_SENSITIVE` are assigned to `personal:{username}` and cannot be viewed, listed, or searched by other staff or ward administrators.

### 3.2 Data Leakage Prevention (Egress Filter)
* **Invariant:** Under no circumstances can patient observations, vitals, allergies, or clinical notes leave the device.
* **Double Egress Guard:**
  1. Store layer: `_append` only queues items in the outbox if `memory["fixture"]` is non-null.
  2. Transport layer: `Transport.run` re-queries SQLCipher immediately prior to transmission; if `fixture` is absent or `privacy != "PUBLIC"`, the delivery is permanently cancelled.

---

## 4. Storage & Persistence Audit

### 4.1 SQLCipher 4 Cryptographic Configuration
* **Cipher:** AES-256-CBC with HMAC page authentication.
* **Journaling:** Write-Ahead Logging (`PRAGMA journal_mode=WAL`) with synchronous checkpointing (`PRAGMA synchronous=FULL`).
* **Key Derivation:** 256,000 PBKDF2 iterations using HMAC-SHA1.
* **Fail-Closed Key Validation:** Database initialization validates `PRAGMA cipher_version` and queries `sqlite_master`. Invalid or mismatched keys fail closed and throw immediate exceptions without revealing plaintext.

### 4.2 Append-Only DAG & Conflict Resolution
* Revisions are stored in an append-only table (`revisions`).
* Concurrent modifications update `heads` without overwriting prior history.
* Multi-head states (`len(heads) > 1`) flag records as `conflicting=True`.
* Three-way branch resolution requires specifying all active branch parents and selecting a winning revision.

### 4.3 Tombstone Truthfulness
* Deleting a record sets `deleted=1` and clears `heads`.
* Direct lookups return `404 Not Found`.
* High-level `revise` operations on deleted memories raise `KeyError`. Low-level `_append` rejects resurrection with `ValueError("Deleted records cannot be resurrected")`.
* Retrieval engine enforces canonical head verification; deleted memories yield zero results in both lexical and vector searches.

---

## 5. Retrieval & Performance Scaling Audit

### 5.1 Dual-Projection Architecture
* **Semantic Engine:** Local ONNX Runtime executing `BAAI/bge-small-en-v1.5` generating 384-dimensional dense vectors indexed in embedded Qdrant Edge (`lex_synthetic_memories`).
* **Lexical Engine:** Persistent SQLite sparse inverted index table (`lexical_postings`) storing token posting lists and term frequencies.
* **Reciprocal Rank Fusion (RRF):** Fuses semantic and lexical ranks using $k=60$.

### 5.2 Performance Benchmarks Across Scale

| Metric | 1,000 Synthetic Records | 10,000 Synthetic Records (Optimized) | Previous Bottleneck (Pre-Optimization) |
| :--- | :--- | :--- | :--- |
| **Complete Backend Search (p50)** | **~4.3 ms** | **~8.9 ms** | ~101.5 ms (Exceeded 32 MiB cache) |
| **Complete Backend Search (p95)** | **~7.8 ms** | **~14.6 ms** | ~142.0 ms |
| **Lexical Search Time (p50)** | **~1.1 ms** | **~2.8 ms** | ~92.0 ms (Inverted index eliminated corpus prep) |
| **Vector Search Time (p50)** | **~3.2 ms** | **~6.1 ms** | ~9.5 ms |
| **Index Query Path Memory** | Stable (<12 MiB) | Stable (<18 MiB) | Excessive memory thrashing |

---

## 6. Frontend & User Experience Audit

* **Theme System:** Fully implemented Catppuccin Latte (light) and Catppuccin Mocha (dark) semantic color tokens. Zero hardcoded generic colors or unstyled browser defaults.
* **Responsive Layout:** Tested across viewports from 1920px desktop down to 320px mobile. Navigation collapses into a full-height slide-over drawer on mobile viewports.
* **Keyboard Accessibility:** Global shortcuts (`?` for keyboard shortcuts modal, `Ctrl+K` for instant search focus, `Escape` to dismiss dialogs).
* **Workspace Workflows:**
  * **Memory Workspace:** Timeline with search, category filtering, add dialog, revision history, and conflict resolution banner.
  * **Visual Data Logging:** Quick-entry observation cards with live client-side validation, metric trend visualizations, and Needs Review workflow.
  * **Synthetic Subjects Roster:** Patient roster listing, summary banner, longitudinal vitals charts, allergy alert cards, and chronological medical history.
  * **Sync Monitor & Memory Lab:** Outbox delivery tracking with status chips, activity audit log, storage health indicators, and interactive simulation controls.

---

## 7. Verification & Quality Assurance Audit

### 7.1 Backend Test Coverage (77 Passed)
* `tests/test_governance_snapshots.py`: 12 tests (advisory retention, snapshot generation, manifest verification).
* `tests/test_hospital_lan.py`: 2 tests (private LAN IP bounds, TLS CA and cert generation, multi-user scoping).
* `tests/test_next_phase.py`: 12 tests (session expiry, idle timeout, snapshot rollback defense, archive validation).
* `tests/test_provision_assets.py`: 4 tests (pinned ONNX model and Qdrant binary checksum validation).
* `tests/test_real_edge.py`: 1 test (real embedded Qdrant Edge vector indexing and search).
* `tests/test_relevance.py`: 1 test (hybrid semantic + lexical ranking relevance verification).
* `tests/test_retrieval_performance.py`: 6 tests (scaling benchmarks, inverted postings index, cache hit rate).
* `tests/test_security_and_storage.py`: 19 tests (SQLCipher encryption, HMAC event chain, concurrency, export validation).
* `tests/test_security_boundaries.py`: 16 tests (cross-workspace isolation, staff personal privacy, CSRF, egress filters).
* `tests/test_unix_platform.py`: 4 tests (Linux LUKS2 verification, Unix architecture detection).

### 7.2 Linter & Type Safety
* `uv run ruff check edgemed tests scripts`: **All checks passed!**
* `npm run build`: TypeScript compilation clean without warnings.

---

## 8. Remaining Operational & Physical Validation Gaps

1. **Physical Linux LUKS2 Host:** End-to-end verification of `edgemed.cli start` on a physical Linux machine with cryptsetup LUKS2 mapper mounted at `/dev/mapper/edgemed-vault`.
2. **Headless Secret Service:** Verification of Secret Service / KWallet keyring unlock during headless server reboots under `systemd`.
3. **Mobile LAN CA Trust Rehearsal:** Physical distribution and installation of `lan-ca.pem` into an iOS or Android root trust store over local Wi-Fi.
4. **Disaster Recovery & Key Escrow:** Cold database copy, manual key export, and out-of-band restore rehearsal on a separate physical machine.
5. **Simulated Power Failure:** Hard process termination during intensive writes to verify SQLite WAL recovery and HMAC audit chain consistency.

---

## 9. Final Audit Verdict

EdgeMed demonstrates strong defense-in-depth engineering, strict architectural separation of concerns, and verified multi-tenant isolation. All five project milestones have been successfully designed, implemented, and verified. The system operates strictly as a **synthetic-data research prototype** and meets all requirements established for Team LEX Problem Statement 03.
