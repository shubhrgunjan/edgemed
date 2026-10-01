# EdgeMed Threat Model & Security Boundary Validation

**Document Status:** Evaluated Research Prototype (Synthetic Data Only)  
**Target Milestone:** Security Boundary & Operational Validation  
**Last Updated:** September 2026  
**Repository:** `shubhrgunjan/edgemed`  
**Applicability:** EdgeMed Local Node (`edge-a`), Hospital LAN Deployment, Central Demo Gateway, and Projection Pipelines.

> [!CAUTION]
> **Prototype & Synthetic Data Notice**  
> EdgeMed is an experimental, offline-first clinical memory and retrieval research prototype developed for synthetic-data demonstrations (Team LEX, Code Cubicle 6.0, Problem Statement 03). It has **not** undergone clinical safety certification (e.g., FDA, CE-MDR), formal HIPAA/GDPR regulatory audits, or external penetration testing. **No real patient data, clinical notes, or production hospital credentials may be ingested, stored, or processed by this system.**

---

## 1. System Overview & Architectural Invariants

EdgeMed is a local-first memory store designed for environments with intermittent or zero internet connectivity. The local node runs as a 64-bit native server accessed via modern browsers.

```
                      +-------------------------------------------------------+
                      |                 TRUST BOUNDARY: BROWSER               |
                      |  [Staff Device Browser: Phone / Tablet / Desktop]     |
                      |  - Session Cookie: HttpOnly, SameSite=Strict, Secure  |
                      |  - Request Headers: x-csrf-token, exact Host & Origin |
                      +---------------------------+---------------------------+
                                                  |
                                                  | TLS 1.3 / Private LAN
                                                  v
+---------------------------------------------------------------------------------------------------+
| TRUST BOUNDARY: HOST OS & EDGEMED LOCAL NODE (edge-a)                                              |
|                                                                                                   |
|  +---------------------------------------------------------------------------------------------+  |
|  | HTTP / APPLICATION PERIMETER (edgemed/api.py, http_boundary.py)                             |  |
|  | - BoundedHTTP: 32 KiB request limit, 10s timeout, no-store headers, nosniff, CSP             |  |
|  | - Host & Origin verification, Sec-Fetch-Site filtering, CSRF HMAC verification              |  |
|  | - Argon2id authentication, rate-limiting (8 attempts / 5 min), 30m session / 5m idle         |  |
|  +----------------------------------------------+----------------------------------------------+  |
|                                                 |                                                 |
|                                                 v                                                 |
|  +---------------------------------------------------------------------------------------------+  |
|  | WORKSPACE & SCOPE AUTHORIZATION (edgemed/accounts.py)                                       |  |
|  | - Clinician: scoped to assigned ward (e.g. ward-a)                                          |  |
|  | - HIGHLY_SENSITIVE notes: strictly isolated to personal:{username}                          |  |
|  | - Admin: scoped to ward; Operator: master administrative access                             |  |
|  +----------------------------------------------+----------------------------------------------+  |
|                                                 |                                                 |
|                        +------------------------+------------------------+                        |
|                        |                                                 |                        |
|                        v                                                 v                        |
|  +--------------------------------------------+  +---------------------------------------------+  |
|  | CANONICAL STORE (edgemed/store.py)          |  | PROJECTIONS & RETRIEVAL (retrieval.py)      |  |
|  | - SQLCipher (AES-256-CBC, PBKDF2 HMAC SHA1)|  | - Local Qdrant Edge (vectors)               |  |
|  | - Append-only Revisions DAG & Heads        |  | - Sparse Lexical Posting Index              |  |
|  | - Tamper-evident HMAC-SHA256 Event Chain   |  | - FastEmbed ONNX (BAAI/bge-small-en-v1.5)   |  |
|  | - Deleted tombstones fail closed           |  | - SQL-guaranteed Current-Head filtering     |  |
|  +---------------------+----------------------+  +---------------------------------------------+  |
|                        |                                                                          |
|                        | Outbox Queue (fixtures only)                                             |
|                        v                                                                          |
|  +--------------------------------------------+                                                   |
|  | SYNCHRONIZATION EGRESS (edgemed/sync.py)   |                                                   |
|  | - Strict Egress Policy: fixture != NULL    |                                                   |
|  |   AND privacy == 'PUBLIC'                  |                                                   |
|  | - Zero patient notes enter outbox          |                                                   |
|  | - Ed25519 payload signing                  |                                                   |
|  +---------------------+----------------------+                                                   |
+------------------------|--------------------------------------------------------------------------+
                         |
                         | mTLS 1.3 / Signed Envelopes
                         v
+---------------------------------------------------------------------------------------------------+
| TRUST BOUNDARY: CENTRAL DEMO INFRASTRUCTURE                                                       |
|  - Demo Gateway (:9443): Verifies Ed25519 signatures, checks device revocation, issues receipts   |
|  - Central Qdrant (:6333): Stores global synthetic reference embeddings                           |
|  - Snapshot Publisher: Packages signed, content-checked reference shards                          |
+---------------------------------------------------------------------------------------------------+
```

### Core Architectural Invariants

1. **SQLCipher as Canonical Source of Truth:** All patient notes, observations, staff metadata, revisions, and outbox intents reside in SQLCipher. Vector shards (Qdrant Edge) and sparse lexical indices are ephemeral, subordinate projections that are re-indexed from SQLCipher and strictly filtered against current canonical heads upon retrieval.
2. **Local-Only Clinical Observations:** Clinical observations (`OBSERVATION`, `ALLERGY`, `VITAL_SIGN`, `NOTE`) are strictly `LOCAL_ONLY`. Under no circumstance can a non-fixture memory be exported to the outbound synchronization queue.
3. **Fail-Closed Storage Verification:** The server refuses to initialize if native platform encryption requirements are not met (unlocked Secret Service/KWallet on Linux, Keychain on macOS, verified LUKS2 block device on Linux). Plaintext secret storage is disabled.

---

## 2. Asset Inventory & Classification

| Asset | Description | Sensitivity | Integrity Requirement | Primary Storage Location |
| :--- | :--- | :--- | :--- | :--- |
| **Clinical Synthetic Notes** | Observations, vitals, allergies, free-text clinical summaries | **Critical** (High Confidentiality) | Tamper-evident append-only DAG | SQLCipher (`memory.db` inside encrypted vault) |
| **Database Encryption Key** | 256-bit hexadecimal key (`db_key`) | **Critical** | Confidential, zero-leakage | OS Keyring (macOS Keychain / Linux Secret Service) |
| **Device Ed25519 Private Key**| Private signing key (`sign_private`) | **High** | Authenticity of outbound payloads | OS Keyring |
| **Staff Passwords & Hashes** | User credentials; Argon2id hashes | **High** | Pre-image resistance, brute-force defense | OS Keyring (`operators` dictionary) |
| **Session & CSRF Tokens** | In-memory 256-bit random tokens | **High** | High entropy, constant-time verification | Memory (`sessions` dict, SHA-256 hashed keys) |
| **Audit Event MAC Chain** | Hash-chained HMAC-SHA256 audit log | **Medium** | Append-only, detect truncation/alteration | SQLCipher (`events` table) |
| **Vector & Lexical Projections**| Derived ONNX embeddings & index | **Medium** | Re-derivable from SQLCipher, filtered | Local file system (`vault/vectors/`) |
| **Approved Reference Data** | Public clinical guidance templates | **Low** (Public) | Authenticity via Gateway signature | SQLCipher / Qdrant Edge |

---

## 3. Trust Boundaries

### 3.1 Host & Operating System Boundary
* **Assumption:** The host operating system kernel and the execution environment of the EdgeMed user are secure.
* **Mechanism:**
  * macOS: APFS AES-256 encrypted sparse bundle; keys held in macOS Keychain.
  * Linux: Dedicated LUKS2 block device (`/dev/mapper/edgemed-vault`) verified via `_mapper_uuid` starting with `CRYPT-LUKS2-` and mounted with mode `0o700` owned by `os.geteuid()`. Keys stored in SecretService/KWallet. Plaintext fallback is disabled.
* **Threat:** Malicious local processes running under the same OS user can inspect mounted files or memory. Physical theft of a powered-on, unlocked device bypasses at-rest encryption.

### 3.2 Network Perimeter & LAN Boundary
* **Assumption:** Local Wi-Fi or hospital LAN may contain untrusted devices, network eavesdroppers, or rogue access points.
* **Mechanism:**
  * Standalone mode: Binds exclusively to loopback interface `127.0.0.1:8765`.
  * LAN mode: Binds **only Edge A** to an explicit, verified private IPv4 address (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) over HTTPS.
  * TLS Certificates: Self-signed demo CA (RSA-3072, 30-day validity) and server certificate (RSA-2048, 7-day validity) generated with SAN matching the exact private IP.
* **Threat:** Man-in-the-middle attacks on the LAN if clients ignore TLS certificate verification or accept unverified CAs.

### 3.3 HTTP Application Perimeter
* **Assumption:** Browsers accessing EdgeMed may execute arbitrary untrusted web content in adjacent tabs.
* **Mechanism:**
  * Strict `Host` header check matching configured server host; returns `400 Bad Request` on mismatch (DNS rebinding defense).
  * Strict `Origin` check matching configured origin; returns `403 Forbidden` on mismatch.
  * Explicit `Sec-Fetch-Site: cross-site` rejection; returns `403 Forbidden`.
  * `BoundedHTTP` middleware enforcing a 32 KiB request payload cap and 10-second timeout.
  * Strict response security headers: `Cache-Control: no-store`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, and restrictive `Content-Security-Policy`.
  * State-changing requests (`POST`, `DELETE`) require a valid `x-csrf-token` verified via constant-time comparison (`hmac.compare_digest`).

### 3.4 Identity & Multi-Workspace Isolation Boundary
* **Assumption:** Staff members from different wards (e.g., `ward-a` vs. `ward-b`) share the same physical server.
* **Mechanism:**
  * Every authenticated user session has an associated identity containing `username`, `owner` (ward), and `role` (`clinician` or `admin`).
  * SQL queries execute with parameterized scope clauses (`owner IN (?, ?)`).
  * `HIGHLY_SENSITIVE` observations are forced into `personal:{username}` scope upon creation (`edgemed/accounts.py:record_owner`). Colleague clinicians and ward admins cannot read, list, search, or revise another user's personal notes.
  * Operator scope (`owner == "operator"`) is reserved for administrative tasks. Staff accounts cannot target or query the `operator` scope.

### 3.5 Synchronization & Central Demonstration Boundary
* **Assumption:** Central demonstration servers or network paths could be malicious, compromised, or misconfigured.
* **Mechanism:**
  * Mutual TLS (mTLS) with TLS 1.3 minimum.
  * Application-layer Ed25519 signing of all request and response envelopes (`sign()`, `verify()`).
  * Outbound filter: Egress code checks `if not memory["fixture"] or memory["privacy"] != "PUBLIC": delivery("cancelled")`.
  * Inbound filter: Central gateway and local node verify that `memory_id == fixture_id(fixture)`. Arbitrary clinical notes or vectors cannot be received from central.

---

## 4. Threat Actor Profiles

| Threat Actor | Motivation | Capabilities & Access | Attack Vectors |
| :--- | :--- | :--- | :--- |
| **Untrusted Web Origin (Malicious Tab)** | Data exfiltration, unauthorized modification | Can lure staff to malicious site while EdgeMed is active | CSRF, DNS rebinding, cross-origin fetch, timing attacks |
| **Rogue LAN Neighbor** | Eavesdropping, network tampering | Positioned on same hospital Wi-Fi/Ethernet | ARP spoofing, TLS stripping, port scanning, traffic analysis |
| **Malicious Staff / Insider** | Accessing records outside authorized ward; snooping on personal notes | Valid clinician or ward-admin credentials | Cross-workspace enumeration, direct ID probing, parameter tampering |
| **Compromised Central Gateway** | Infiltrating local edge nodes | Controls central sync gateway and Qdrant server | Malicious snapshot archives (zip slip/tar bomb), malicious sync pushes |
| **Physical Device Interceptor** | Full physical access to stolen laptop/server | Physical possession of device (powered off or sleep) | Disk extraction, offline password cracking, cold boot attacks |

---

## 5. Security Boundary Validations & Controls

### 5.1 Authentication & Session Management
- **Password Hashing:** Argon2id (`time_cost=3`, `memory_cost=65536` KiB, `parallelism=2`).
- **Session Tokens:** 256-bit cryptographically secure pseudorandom tokens (`secrets.token_urlsafe(32)`).
- **Session Storage:** Tokens are SHA-256 hashed before storage in memory to mitigate token leakage via memory dump.
- **Session Lifetime:** 30 minutes absolute session expiry; 5 minutes idle timeout (configured via `idle_seconds`).
- **Cookies:** `HttpOnly`, `SameSite=Strict`, `Secure` (when HTTPS configured), `max_age=1800`.
- **Brute-Force Protection:** IP-based sliding window rate limiter: maximum 8 failed login attempts within 300 seconds per remote IP; returns `429 Too Many Requests`.

### 5.2 Workspace & Scope Authorization
- **Role Hierarchy:**
  - `clinician`: Can create and read notes in their ward; can revise ward notes; can manage their own personal notes; cannot delete ward notes.
  - `admin`: Can create, read, revise, and delete ward notes; can resolve branch conflicts; cannot access another staff member's `personal:*` notes.
  - `operator`: Bootstrap identity with access to the master administrative scope.
- **Enforcement:** Enforced in Python backend (`edgemed/api.py`, `edgemed/store.py`). Frontend UI controls are purely decorative and carry no security authority.

### 5.3 Request Boundary & CSRF Defenses
- **Bounded Ingestion:** `BoundedHTTP` streaming middleware reads at most 32,768 bytes before raising HTTP 413. Protects against memory exhaustion and slowloris attacks.
- **CSRF Token:** Embedded in response body upon successful authentication. Required in `x-csrf-token` header for all state-modifying requests (`POST`, `DELETE`, `PUT`). Verification uses `hmac.compare_digest`.
- **Cross-Origin Defense:** Direct validation of `Host`, `Origin`, and `Sec-Fetch-Site`. Unmatched requests fail with 400 or 403.

### 5.4 Encrypted Storage & Audit Trail
- **Encryption:** SQLCipher 4 with AES-256-CBC and HMAC page authentication. Default page size 4096 bytes with 256,000 PBKDF2 iterations.
- **Tamper-Evident Audit Trail:** Every revision, deletion, and sync state transition inserts an event into `events` table. Each event links to the preceding event's MAC using `HMAC-SHA256(db_key, previous_mac + canonical(payload))`. Any database manipulation breaks chain verification (`store.verify_audit()`).

### 5.5 Retrieval Pipeline & Search Truthfulness
- **Stale Projection & Deletion Defense:** Vector and lexical indices store revision IDs. When a search query completes, `store.eligible_results()` performs a mandatory SQL check ensuring:
  1. The memory's `owner` is currently authorized for the requesting user.
  2. The memory is not marked `deleted == 1`.
  3. The matched revision ID is an active current head in `memories.heads`.
- **Tombstones:** Deleted memories have their heads cleared and deleted flag set. Deleted records return 404 and are filtered out of all lexical, vector, and hybrid search results.

### 5.6 Synchronization Egress & Ingress Boundary
- **Egress Filter:** Only records where `fixture` is non-null and `privacy == "PUBLIC"` are permitted in the outbox. The outbox payload (`Export` model) contains only metadata: `fixture` name, `variant` integer (0, 1, or 2), `operation_id`, `memory_id`, `revision_id`, `parents`, and `deleted` flag. No clinical text, embeddings, or patient identifiers can be serialized.
- **Double Invariant Check:** The transport runner (`edgemed/sync.py:Transport.run`) re-queries canonical SQLCipher immediately before network egress; if `fixture` is absent or privacy is not `PUBLIC`, the operation is permanently cancelled.
- **Ingress Filter:** Central sync payloads (`/sync/pull`) only accept `Export` models matching known `REFERENCES` fixtures. Arbitrary text injection via sync is impossible.

### 5.7 Snapshot Verification & Ingestion
- **Cryptographic Verification:** Snapshot archives must include an Ed25519-signed manifest.
- **Decompression Bomb Defense:** Archive unpacker strictly limits archive members ($\le 10,000$), total expanded bytes ($\le 512\text{ MiB}$), and member depth ($\le 3$).
- **Path Traversal Defense:** Member paths are inspected using `PurePosixPath`; any absolute path, backslash, or `..` component raises a fatal `ValueError`.
- **Payload Integrity:** Every vector point in the unpacked Qdrant shard is scrolled and validated: payload must match approved `REFERENCES` fixture IDs, and corresponding metadata must already exist in local SQLCipher.
- **Rollback Prevention:** The manifest generation must be greater than or equal to the current snapshot generation.

---

## 6. Threat Analysis & Boundary Matrix

| Threat / Attack Vector | Target Boundary | Architectural Mitigation | Automated Test Coverage |
| :--- | :--- | :--- | :--- |
| **Cross-Ward Data Leakage** | Workspace Scoping | SQL query parameterization via `_scope_clause(owner)` | `test_cross_workspace_isolation_blocks_read_and_search` |
| **Staff Personal Note Snooping** | Identity Boundary | `HIGHLY_SENSITIVE` notes routed to `personal:{user}` | `test_staff_personal_observations_isolated_from_colleagues` |
| **Exfiltration of Clinical Notes via Sync** | Egress Boundary | Egress whitelist enforces `fixture` non-null and `PUBLIC` | `test_clinical_observations_cannot_enter_outbox` |
| **Tampered Export Payload Ingestion** | Ingress Boundary | Strict schema validation; `variant` must be in {0,1,2} | `test_tampered_export_injection_fails` |
| **Cross-Site Request Forgery (CSRF)** | HTTP Perimeter | `SameSite=Strict`, `x-csrf-token` header, HMAC comparison | `test_csrf_token_required_on_mutations` |
| **DNS Rebinding & Host Header Poisoning** | HTTP Perimeter | Exact `Host` header matching in middleware | `test_host_header_poisoning_rejected` |
| **Cross-Origin Information Leakage** | HTTP Perimeter | Origin header matching; `Sec-Fetch-Site: cross-site` block | `test_cross_origin_and_fetch_site_rejected` |
| **Zombie Search Hits (Deleted Records)** | Retrieval Boundary| Canonical head & deletion verification in `eligible_results` | `test_deleted_memory_tombstone_purges_search_results` |
| **Tombstone Resurrection Attack** | Canonical Storage | `_append` forbids adding revisions to deleted memories | `test_deleted_record_resurrection_prevented` |
| **Privilege Escalation via Frontend Tampering**| API Boundary | Server-side role checks (`admin`, `system_admin`) | `test_clinician_cannot_execute_admin_endpoints` |
| **Replay of Stale Sync Changes** | Sync Boundary | Idempotent inbox tracking via SHA-256 payload hash | `test_idempotency_and_payload_reuse` |
| **Archive Traversal / Zip Slip via Snapshot** | Storage / Snapshot | Strict `validate_archive` rejecting `..`, absolute paths | `test_snapshot_archive_rejects_path_traversal` |
| **Snapshot Rollback Attack** | Snapshot Boundary| Manifest generation verification against prior state | `test_snapshot_rollback_rejected` |
| **Plaintext Keyring Fallback** | Key Storage | Linux SecretService verification; fails closed | `test_protected_keyring_fails_closed_without_secret_service` |
| **Unencrypted SQLCipher Key Bypass** | Storage Boundary | SQLCipher fail-closed key validation | `test_encryption_and_wrong_key` |

---

## 7. Residual Risks & Operational Limitations

1. **Host-Level Compromise:** If an attacker gains root or the execution privileges of the local OS user while the vault is mounted, they can dump process memory, inspect the decrypted SQLite database, or extract ONNX model weights.
2. **Whole-Volume Rollback:** While the internal HMAC event chain prevents undetectable intra-database tampering, an attacker with filesystem access could replace the entire `memory.db` file with an older valid backup.
3. **Single Node Availability:** The system currently relies on a single host. Hardware failure, power loss, or local disk corruption will cause downtime.
4. **No Hardware Security Module (HSM) / Secure Enclave Binding:** Keyring storage delegates to OS software secret services (e.g., freedesktop Secret Service or macOS Keychain) without mandatory TPM/Secure Enclave hardware sealing.
5. **Cold Backup Recovery:** Backing up `memory.db` while active can capture inconsistent WAL states. Backups must be performed when the database is idle or unmounted. Restoring requires out-of-band recovery of the 256-bit database key.

---

## 8. Physical & Operational Validation Requirements

The following operational aspects cannot be fully verified via mock/synthetic unit tests and require physical or manual rehearsal:

| Area | Validation Requirement | Environment / Equipment | Operational Procedure |
| :--- | :--- | :--- | :--- |
| **Linux LUKS2 Verification** | Live verification of mapper UUID, permissions, and mount source | Physical Linux x86-64 / ARM64 workstation | Verify cryptsetup format with LUKS2, mount to target directory, execute `edgemed.cli start`, confirm `verify_luks_mount` succeeds. |
| **Keyring Headless Startup** | Unlocked Secret Service without graphical desktop session | Headless Linux server (systemd) | Validate DB key retrieval via `dbus-run-session` or secret-tool without prompting on headless restarts. |
| **Disaster Recovery & Key Escrow** | Cold backup creation, transfer, key restore, and database unlock | Secondary test machine | Perform cold database copy, import key into clean keyring, start server, verify HMAC audit chain integrity. |
| **Hospital LAN CA Rehearsal** | Private CA installation and certificate trust on mobile browser | Physical iOS / Android smartphone on Wi-Fi | Distribute `lan-ca.pem`, install into mobile trust store, connect to `https://<ip>:8765`, verify zero browser security warnings. |
| **Power Failure & WAL Recovery** | Abrupt power interruption during indexing / revision write | Physical workstation | Simulate hard kill (`kill -9` or power drop) during write stress test; reboot and verify SQLite WAL recovery and event chain consistency. |

---

## 9. Conclusion & Security Gate Statement

EdgeMed has defense-in-depth controls across the HTTP boundary, workspace scoping, cryptographic storage, and synchronization egress. Automated tests exercise the intended exclusion of staff observations from sync, cross-workspace access checks, and deletion from active search. They do not prove the absence of all vulnerabilities or authorize handling real patient data.

However, EdgeMed remains a **research prototype**. Before any progression toward production or handling of identifiable patient data, EdgeMed must undergo:
1. An independent, third-party penetration test and code audit.
2. Formal integration with enterprise hospital identity providers (OIDC/SAML/LDAP).
3. Implementation of hardware-backed key management (TPM 2.0 / Apple Secure Enclave).
4. Regulatory compliance reviews under applicable healthcare data standards.
