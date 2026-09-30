# EdgeMed System Architecture Blueprint & Layer Flow

**Specification Version:** 1.0.0 (Research Prototype)  
**Security Status:** Synthetic Data Only · Not for Clinical Use  
**Canonical Storage Engine:** SQLCipher 4 (AES-256-CBC)  
**Vector & Lexical Engines:** Qdrant Edge (384-d Cosine) & SQLite Sparse Postings (BM25-style)  

---

## 1. High-Level Architectural Blueprint

EdgeMed is architected around strict separation of concerns, zero-cloud dependency, local-first canonical persistence, append-only revision DAGs, and dual-projection retrieval engines.

```mermaid
flowchart TB
    %% Subgraphs representing architectural tiers
    subgraph Tier1["1. Clients & Presentation Boundary (Browser & Responsive SPA)"]
        direction LR
        UI_SPA["EdgeMed SPA (React 19 / TypeScript / Vite / Vanilla CSS Tokens)"]
        UI_Log["Visual Logging & Vitals Entry"]
        UI_Sub["Synthetic Subjects / Patient Chart Roster"]
        UI_Sync["Sync Monitor & Memory Lab"]
        UI_CLI["Operator CLI (edgemed/cli.py)"]
        UI_Demo["Public Static Demo (Static HTML / No Backend)"]
    end

    subgraph Tier2["2. Transport, Security & Origin Boundary"]
        direction TB
        HTTP_Gate["BoundedHTTP Middleware (32 KiB Bound / 10s Timeout)"]
        SEC_Headers["Security Headers (CSP, no-store, nosniff, no-referrer)"]
        SEC_HostOrigin["Host, Origin & Sec-Fetch-Site Cross-Origin Guards"]
        AUTH_Session["Argon2id Auth & Sliding Session (SameSite=Strict, HttpOnly)"]
        CSRF_Gate["HMAC Constant-Time CSRF Verification (x-csrf-token)"]
        ASGI_Core["FastAPI Core Engine (Uvicorn 127.0.0.1:8765 / Private LAN HTTPS)"]
    end

    subgraph Tier3["3. Identity, Scoping & Business Rules Engine"]
        direction TB
        SCOPE_Mgr["Workspace & Identity Scoping (edgemed/accounts.py)"]
        SCOPE_Ward["Ward Scoping: Clinician / Admin (e.g., ward-a, ward-b)"]
        SCOPE_Personal["Personal Isolation: personal:{username} (HIGHLY_SENSITIVE)"]
        GOV_Engine["Clinical Governance Rules & Retention Evaluator (edgemed/governance.py)"]
    end

    subgraph Tier4["4. Canonical Storage & Audit Ledger (Single Source of Truth)"]
        direction TB
        SQL_Core["SQLCipher 4 Database (memory.db / AES-256-CBC / WAL Mode)"]
        DAG_Revs["Append-Only Revision DAG (memories, revisions, heads)"]
        AUDIT_Mac["Tamper-Evident HMAC-SHA256 Event Chain (events table)"]
        TOMB_Guard["Tombstone Deletion & Resurrection Guard (deleted=1)"]
        OUT_Queue["Selective Reference Outbox (PUBLIC fixtures only)"]
    end

    subgraph Tier5["5. Ephemeral Derived Projections & Search Engines"]
        direction LR
        subgraph SemanticBranch["Semantic Vector Engine"]
            ONNX_Model["FastEmbed / ONNX Runtime (BAAI/bge-small-en-v1.5 / 384-d)"]
            QDRANT_Edge["Local Qdrant Edge (Embedded Rust / HNSW Cosine Index)"]
        end
        subgraph LexicalBranch["Lexical Inverted Engine"]
            INV_Index["SQLite Sparse Inverted Index (lexical_postings / BM25)"]
            POST_Cache["Precomputed Corpus & Token Posting Cache (<10ms at 10k)"]
        end
        RRF_Fusion["Reciprocal Rank Fusion (RRF k=60)"]
        CANON_Filter["Canonical Head & Deletion Gate (eligible_results)"]
    end

    subgraph Tier6["6. Synchronization & Verified Ingestion Boundary"]
        direction TB
        SYNC_Egress["Outbound Egress Guard (fixture != NULL AND privacy == 'PUBLIC')"]
        MTLS_Transport["TLS 1.3 Transport + Ed25519 Payload Signing"]
        GATEWAY_Demo["Central Demo Gateway (:9443) & Qdrant Server (:6333)"]
        SNAP_Verify["Reference Snapshot Ingestion & Tarbomb Verification (edgemed/snapshots.py)"]
    end

    %% Flow connections
    Tier1 -->|"HTTP Requests / Cookies / Headers"| Tier2
    HTTP_Gate --> SEC_Headers --> SEC_HostOrigin --> CSRF_Gate --> AUTH_Session --> ASGI_Core
    ASGI_Core -->|"Authenticated Context (Identity, Role, Owner)"| Tier3
    Tier3 -->|"Scoped Reads / Validated Mutations"| Tier4
    
    %% Storage to Projections
    DAG_Revs -->|"Background Job Queue (jobs table)"| Tier5
    ONNX_Model --> QDRANT_Edge
    INV_Index --> POST_Cache
    QDRANT_Edge --> RRF_Fusion
    POST_Cache --> RRF_Fusion
    RRF_Fusion --> CANON_Filter
    CANON_Filter -.->|"Guaranteed Current Head Only"| ASGI_Core

    %% Storage to Sync
    OUT_Queue -->|"Double-Checked Egress"| SYNC_Egress
    SYNC_Egress --> MTLS_Transport --> GATEWAY_Demo
    GATEWAY_Demo -.->|"Signed Shard Manifest"| SNAP_Verify
    SNAP_Verify -->|"Verified References"| QDRANT_Edge

    %% Styling
    classDef clientStyle fill:#1e1e2e,stroke:#89b4fa,stroke-width:2px,color:#cdd6f4;
    classDef transportStyle fill:#181825,stroke:#f38ba8,stroke-width:2px,color:#cdd6f4;
    classDef scopeStyle fill:#181825,stroke:#fab387,stroke-width:2px,color:#cdd6f4;
    classDef storeStyle fill:#11111b,stroke:#a6e3a1,stroke-width:2px,color:#cdd6f4;
    classDef projStyle fill:#181825,stroke:#cba6f7,stroke-width:2px,color:#cdd6f4;
    classDef syncStyle fill:#1e1e2e,stroke:#94e2d5,stroke-width:2px,color:#cdd6f4;

    class UI_SPA,UI_Log,UI_Sub,UI_Sync,UI_CLI,UI_Demo clientStyle;
    class HTTP_Gate,SEC_Headers,SEC_HostOrigin,AUTH_Session,CSRF_Gate,ASGI_Core transportStyle;
    class SCOPE_Mgr,SCOPE_Ward,SCOPE_Personal,GOV_Engine scopeStyle;
    class SQL_Core,DAG_Revs,AUDIT_Mac,TOMB_Guard,OUT_Queue storeStyle;
    class ONNX_Model,QDRANT_Edge,INV_Index,POST_Cache,RRF_Fusion,CANON_Filter projStyle;
    class SYNC_Egress,MTLS_Transport,GATEWAY_Demo,SNAP_Verify syncStyle;
```

---

## 2. Detailed Layer Specifications

### Layer 1: Presentation & Client Boundary
The client layer consists of two distinct components:
1. **EdgeMed Authenticated SPA:** Built with React 19, TypeScript, Vite, and semantic vanilla CSS tokens (Catppuccin Latte/Mocha themes). Zero external CDN dependencies; all scripts, fonts, and assets are hosted locally on the EdgeMed ASGI server.
   * **Visual Data Logging Workspace (`logging.tsx`):** Quick-entry cards for vitals, observations, lab values, and clinical notes; interactive SVG trend charts; Needs Review queue.
   * **Synthetic Subjects Roster (`subjects.tsx`):** Patient-chart interface with roster navigation, longitudinal vitals graphs, allergy badge alerts, and chronological history.
   * **Sync Monitor & Memory Lab (`sync-monitor.tsx`):** Connectivity hero status, outbox inspection, audit event timeline, storage diagnostics, and simulation controls.
2. **Public Static Demonstration (`demo.tsx`):** A lightweight standalone sample compiled to static HTML/CSS. It has **no backend, no API, no persistent storage, and no vault**. Notes entered exist strictly in browser tab memory.

### Layer 2: Transport & HTTP Security Boundary
* **Bounded Request Ingestion (`http_boundary.py`):** The `BoundedHTTP` middleware intercepts raw ASGI streams, strictly rejecting payloads exceeding 32,768 bytes (`413 Request Too Large`) and requests taking longer than 10 seconds (`408 Request Timeout`).
* **Origin & Host Protection:** Evaluates incoming `Host` and `Origin` headers against the server's configured origin (`127.0.0.1:8765` or explicit private LAN IP). Drops cross-site requests (`Sec-Fetch-Site: cross-site`) with `403 Forbidden`.
* **State & CSRF Verification:** Issues high-entropy, cryptographically random session tokens (`secrets.token_urlsafe(32)`). Sets `SameSite=Strict`, `HttpOnly`, `Secure` (over HTTPS) cookies. State-modifying HTTP verbs (`POST`, `DELETE`, `PUT`) require a matching `x-csrf-token` verified via `hmac.compare_digest`.
* **Strict Security Headers:** Injects `Cache-Control: no-store`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, and a hardened `Content-Security-Policy` (`frame-ancestors 'none'`, `default-src 'self'`).

### Layer 3: Identity & Multi-Workspace Scoping Boundary
* **Identity Management (`accounts.py`):** Local user accounts are secured with Argon2id password hashing (`time_cost=3`, `memory_cost=65536` KiB, `parallelism=2`). Brute-force rate limiting blocks IPs after 8 failed attempts in 5 minutes.
* **Workspace Isolation:** Every record is tagged with an `owner`. Clinicians and ward admins query data through SQL scope clauses (`owner IN (?, ?)`).
* **Personal Clinical Notes Isolation:** Observations marked `HIGHLY_SENSITIVE` are dynamically reassigned to `personal:{username}`. Colleague staff members and ward admins in the same ward cannot view, search, revise, or delete these records.

### Layer 4: Canonical SQLCipher Storage & Ledger
* **Canonical Persistence (`store.py`):** SQLCipher 4 full-database encryption using AES-256-CBC with HMAC page validation. Plaintext fallback is completely disabled.
* **Revision Directed Acyclic Graph (DAG):** Edits do not overwrite prior state. Every change creates a new revision referencing one or more parents. Concurrent edits on separate devices or tabs create branching heads (`conflicting=True`), requiring explicit three-way branch resolution.
* **Tombstone Semantics:** Deletions set `deleted=1` and clear current heads. Deleted records return 404, are purged from lexical/vector search results, and cannot be resurrected by subsequent revisions.
* **Tamper-Evident Event Chain:** System events are recorded in an append-only table (`events`) where each row calculates an HMAC-SHA256 linking to the previous row's MAC. Any database file tampering is detected via `store.verify_audit()`.

### Layer 5: Ephemeral Projections & Retrieval Pipeline
* **Dual-Projection Architecture:** Vector embeddings and sparse inverted index records are ephemeral projections derived from SQLCipher:
  1. **Dense Semantic Branch:** Pinned ONNX Runtime (`BAAI/bge-small-en-v1.5`, 384 dimensions) generating embeddings stored in local embedded Qdrant Edge collection.
  2. **Sparse Lexical Branch:** SQLite-backed inverted index table (`lexical_postings`) with cached document frequencies and token posting lists, eliminating corpus preparation overhead on the query path.
* **Reciprocal Rank Fusion (RRF):** Merges semantic and lexical result sets using $RRF(d) = \sum_{m} \frac{1}{60 + rank_m(d)}$.
* **Canonical Verification (`store.eligible_results`):** Candidate results from search projections are re-validated against SQLCipher to verify that the requesting user is authorized for the record, the matched revision is an active current head, and the memory has not been tombstoned.

### Layer 6: Synchronization & Verified Snapshot Ingestion
* **Selective Synchronization (`sync.py`):** Patient observations (`OBSERVATION`, `ALLERGY`, `VITAL_SIGN`, `NOTE`) are strictly `LOCAL_ONLY`. Only reviewed reference templates (`fixture != NULL` and `privacy == "PUBLIC"`) can be queued for synchronization.
* **Double-Check Egress Guard:** Immediately before network transmission, the transport runner re-queries SQLCipher; if a memory lacks a valid fixture ID or has non-public privacy, delivery is permanently cancelled.
* **Cryptographic Envelopes:** All sync payloads and receipts are signed with Ed25519 keypairs. Central demonstration gateway verifies signatures against registered, non-revoked device certificates.
* **Snapshot Tarbomb & Ingestion Defense (`snapshots.py`):** Downloaded reference snapshots are strictly bounded ($\le 16\text{ MiB}$ compressed, $\le 512\text{ MiB}$ expanded, $\le 10,000$ members). Member filenames are parsed with `PurePosixPath` to reject directory traversal (`../`) or absolute paths. Every point in the unpacked shard is inspected for schema compliance and local metadata reconciliation before activation.

---

## 3. Data Flow Diagrams

### Data Flow A: Local Clinical Observation Ingestion

```mermaid
sequenceDiagram
    autonumber
    actor Clinician as Staff Clinician (Browser)
    participant API as FastAPI Boundary (BoundedHTTP)
    participant Auth as Identity & Scoping Engine
    participant Store as SQLCipher Canonical Store
    participant Worker as Indexing Background Worker
    participant Proj as Dual Projections (Qdrant & Inverted Index)

    Clinician->>API: POST /api/memories (title, content, category, privacy, subject)
    API->>API: Validate BoundedHTTP (<32 KiB) & CSRF Token
    API->>Auth: Evaluate user session & derive scope
    Auth-->>API: Scope: 'ward-a' (or 'personal:alice' if HIGHLY_SENSITIVE)
    API->>Store: store.create(data, owner=scope)
    Store->>Store: INSERT INTO memories & revisions (Heads=[rid])
    Store->>Store: Record HMAC-SHA256 audit event
    Store->>Store: Enqueue job in jobs table (state='pending')
    Store-->>API: Return canonical memory object
    API-->>Clinician: 201 Created (Memory DTO)

    Note over Worker,Proj: Asynchronous Background Projection Pipeline
    Worker->>Store: store.pending_jobs()
    Store-->>Worker: Return batch of pending revisions
    Worker->>Proj: Generate FastEmbed ONNX embedding & insert Qdrant point
    Worker->>Proj: Tokenize content & update lexical_postings inverted index
    Worker->>Store: store.mark_indexed(rid, generation)
```

### Data Flow B: Hybrid Search Query Execution

```mermaid
sequenceDiagram
    autonumber
    actor Staff as Authenticated Staff
    participant API as FastAPI Query Handler
    participant Ret as Retrieval Engine (edgemed/retrieval.py)
    participant Lex as Sparse Inverted Index
    participant Vec as Qdrant Edge Vector Store
    participant Store as SQLCipher Canonical Verification

    Staff->>API: POST /api/search (query, mode="hybrid", limit=10, subject=null)
    API->>API: Verify session, origin, and rate limits
    API->>Ret: retrieval.search(query, owner=scopes, limit=10)
    
    par Lexical Search
        Ret->>Lex: Search token posting lists & compute BM25 scores
        Lex-->>Ret: Top lexical candidate IDs & scores
    and Semantic Search
        Ret->>Ret: Encode query via FastEmbed ONNX (384-d vector)
        Ret->>Vec: Query Qdrant Edge collection (HNSW cosine similarity)
        Vec-->>Ret: Top vector candidate revision IDs & scores
    end

    Ret->>Ret: Apply Reciprocal Rank Fusion (RRF k=60)
    Ret->>Store: store.eligible_results(candidates, owner=scopes)
    Store->>Store: Verify owner in scopes, deleted=0, and rid in current heads
    Store-->>Ret: Filtered, verified results only
    Ret-->>API: Final authorized results + latency timings
    API-->>Staff: 200 OK (Results JSON, route="LOCAL", elapsed_ms)
```

---

## 4. Architectural Guarantees & Non-Functional Boundaries

| Guarantee | Boundary / Mechanism | Verification Method |
| :--- | :--- | :--- |
| **Zero External Data Leakage** | All patient notes are marked `LOCAL_ONLY`. Egress filter cancels outbox items if `fixture IS NULL`. | Automated regression test: `test_clinical_observations_cannot_enter_outbox` |
| **Strict Multi-Tenant Scoping** | SQL query parametrization enforces `owner IN (?, ?)`. Direct ID lookup for cross-ward memory returns 404. | Automated regression test: `test_cross_workspace_isolation_blocks_read_and_search` |
| **Personal Note Privacy** | `HIGHLY_SENSITIVE` notes routed to `personal:{username}`, inaccessible even to ward admins. | Automated regression test: `test_staff_personal_observations_isolated_from_colleagues` |
| **Search Truthfulness** | Projections subordinate to canonical store. Deleted records return 404 and disappear from search. | Automated regression test: `test_deleted_memory_tombstone_purges_search_results` |
| **Fail-Closed Storage** | Server refuses startup without valid 256-bit DB key or with insecure plaintext keyring fallback. | Automated regression test: `test_invalid_sqlcipher_key_length_rejected` |
| **10k Record Search Scalability** | Precomputed inverted postings index sustains sub-10ms queries at 10,000 synthetic records. | Benchmark test: `tests/test_retrieval_performance.py` |
