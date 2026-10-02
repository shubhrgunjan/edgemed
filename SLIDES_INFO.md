# EdgeMed — 7-Slide Winning Pitch Deck

**Event:** Geek Room Code Cubicle 6.0  
**Problem Statement:** PS-03 — AI-Powered Edge Memory & Intelligence Platform (Powered by Qdrant)  
**Project:** EdgeMed — Protected Memory Across Local Care Networks  
**Target Pitch Time:** 3 to 4 Minutes (7 Slides)  

---

## Slide 1: Title & The Hook

### Slide Purpose
Grab immediate attention from judges by framing the mission-critical reality of edge intelligence in healthcare.

### Layout & Visual Design
* **Header / Title:** **EdgeMed — Protected Edge Memory Across Local Care Networks**
* **Subtitle:** *An Offline-First, Local-First Clinical Memory & Hybrid Search Engine Powered by Qdrant Edge*
* **Visuals / Graphics:**
  * High-res EdgeMed Hero Logo / Screenshot (`assets/edgemed-hero.png`) placed center-right.
  * Tagline badges on the bottom: `[Qdrant Edge Embedded]` · `[SQLCipher AES-256]` · `[FastEmbed ONNX]` · `[Sub-10ms Hybrid Search]` · `[100% Offline-Capable]`
* **Key Stats Callout (Top Right):**
  * `0 ms` Cloud Dependency
  * `8.9 ms` p50 Hybrid Search @ 10,000 Records
  * `77 / 77` Verified Tests Passed

### Slide Content (Bullet Points for Slide)
* **The Reality:** Critical healthcare, disaster relief, and rural clinics cannot depend on 24/7 cloud connectivity or accept 500ms network latency.
* **The Dilemma:** Strict data privacy regulations (HIPAA, GDPR) forbid raw patient notes, vitals, and embeddings from leaving the physical local premises.
* **Our Solution:** **EdgeMed** — a complete edge-native intelligence platform that combines **embedded Qdrant Edge**, **canonical encrypted SQLCipher**, and **sparse lexical inverted indexing** to remember, retrieve, and operate 100% offline, while synchronizing approved knowledge intelligently.

### Speaker Script (30 Seconds)
> *"Judges, imagine an ICU or rural clinic during an internet blackout. Cloud-first AI is completely paralyzed. Clinicians can't afford a 500-millisecond network roundtrip, and privacy laws strictly forbid raw patient records from ever leaving the local premises. We built EdgeMed: a complete, offline-first clinical memory platform powered by Qdrant Edge. It provides sub-10ms hybrid search on edge devices, handles evolving records and conflicts without connectivity, and uses zero-leakage cryptographic policies to bridge the gap between local device memory and central knowledge."*

---

## Slide 2: The Core Problem & Architectural Gap

### Slide Purpose
Prove that simply running a local vector database is not enough. Address all core challenges highlighted in Problem Statement 03.

### Layout & Visual Design
* **Header:** **Why Traditional AI Fails at the Edge**
* **Subtitle:** *The 4 Fatal Flaws of Cloud-Dependent & Naive Local Vector Deployments*
* **Layout:** 2x2 Grid of Challenge Cards with contrasting red/amber alert styling.

```
+---------------------------------------+---------------------------------------+
| 1. The Intermittent Connectivity Trap | 2. The Data Privacy & Egress Trap     |
| [X] Cloud RAG fails when the wire cuts| [X] Naive sync leaks private patient  |
| [X] Latency spikes from 10ms -> 1500ms|     notes, vitals, and embeddings     |
| [X] Clinical workflows stall          | [X] Violates medical data sovereignty |
+---------------------------------------+---------------------------------------+
| 3. The "Zombie Projection" Flaw       | 4. The Evolving Memory Conflict Crisis|
| [X] Deleting a record in vector DB    | [X] Offline clinicians edit same note |
|     leaves ghost hits in lexical cache| [X] Standard databases overwrite data |
| [X] No canonical truth or audit trail | [X] No multi-head branch reconciliation|
+---------------------------------------+---------------------------------------+
```

### Slide Content
1. **Network Fragility:** Cloud-dependent LLMs & vector DBs crash during intermittent outages. Care teams cannot stop triage because a router dropped.
2. **Privacy & Egress Risk:** A hospital cannot "just sync everything to the cloud." Observations must remain on-device; only curated clinical reference guidelines can cross boundaries.
3. **Projection Inconsistency:** Ephemeral vector/lexical caches desynchronize after edits or deletions, producing stale, dangerous "hallucinated" search results.
4. **Offline Multi-Master Conflicts:** In an offline ward, two staff members concurrently revise the same patient record on separate tablets. Naive systems suffer destructive silent overwrites.

### Speaker Script (35 Seconds)
> *"When looking at Problem Statement 03, we realized that running a raw vector database on a device is easy—making it safe, consistent, and clinically sound is the real challenge. Cloud RAG dies during connectivity drops. Naive sync pipelines accidentally leak private patient notes. Deleting a record in a vector shard often leaves zombie traces in lexical caches. And when two doctors edit the same patient chart offline, naive databases silently overwrite each other. EdgeMed was engineered from day one to solve these exact four systemic flaws."*

---

## Slide 3: The Architecture — Dual-Projection Engine Powered by Qdrant Edge

### Slide Purpose
Showcase the engineering brilliance of EdgeMed’s architecture. Show how Qdrant Edge fits into a layered, secure system.

### Layout & Visual Design
* **Header:** **System Architecture: Canonical Truth + Dual Projections**
* **Subtitle:** *SQLCipher Source-of-Truth with Ephemeral Qdrant Edge & Inverted Postings*
* **Centerpiece Graphic:** Paste the **Architecture Blueprint Flowchart** (from `docs/SYSTEM_ARCHITECTURE.md`):

```
[Clients / Browsers] ---> [BoundedHTTP & Security Boundary (32 KiB cap, CSRF, CSP)]
                                    |
                                    v
                     [Identity & Workspace Scoping]
                     (ward-a, ward-b, personal:{user})
                                    |
                                    v
            +-----------------------------------------------+
            | CANONICAL STORE: SQLCipher 4 (AES-256-CBC)   |
            | - Append-only Revision DAG & Branch Heads     |
            | - Tamper-evident HMAC-SHA256 Audit Chain      |
            +-----------------------------------------------+
                       /                         \
                      v                           v
         [Dense Semantic Projection]    [Sparse Lexical Projection]
         FastEmbed ONNX (384-d)         SQLite Sparse Postings (BM25)
         Qdrant Edge Vector Engine      Precomputed Token Postings Cache
                      \                           /
                       v                         v
            +-----------------------------------------------+
            | Reciprocal Rank Fusion (RRF k=60) Hybrid Search|
            +-----------------------------------------------+
                                    |
                                    v
            [Canonical Current-Head & Tombstone Gate (Zero Stale Hits)]
```

### Slide Content
* **Canonical Source of Truth:** SQLCipher 4 (AES-256-CBC) stores all records, revision DAGs, and HMAC-chained audit logs.
* **Qdrant Edge (Embedded Rust):** Hosts local dense 384-dimensional cosine embeddings generated by on-device FastEmbed ONNX (`BAAI/bge-small-en-v1.5`).
* **Sparse Inverted Postings Index:** Custom SQLite inverted index table (`lexical_postings`) powering sub-3ms lexical scoring.
* **Reciprocal Rank Fusion (RRF $k=60$):** Fuses dense semantic embeddings and sparse lexical scores into a unified relevance rank.
* **Canonical Head Gate:** Candidate results are strictly validated against SQLCipher heads—guaranteeing that deleted records or unauthorized scopes return **zero** search traces.

### Speaker Script (40 Seconds)
> *"Here is EdgeMed’s architectural blueprint. Rather than treating Qdrant as an isolated database, we architected a canonical-projection pattern. The single source of truth is an encrypted SQLCipher database. Qdrant Edge runs embedded on the device, storing 384-dimensional vectors from a pinned FastEmbed ONNX model. Alongside it, we built a persistent SQLite sparse inverted index. When a clinician queries EdgeMed, both engines execute simultaneously, their results fuse via Reciprocal Rank Fusion, and a final canonical gate verifies that the record is authorized and active. Zero cloud calls, zero zombie hits, and full cryptographic auditability."*

---

## Slide 4: Deep-Tech Scalability — Breaking the 10,000-Record Bottleneck

### Slide Purpose
Provide hard benchmark numbers that prove EdgeMed scales to production-grade corpus sizes without performance degradation.

### Layout & Visual Design
* **Header:** **High-Performance Hybrid Retrieval at Scale**
* **Subtitle:** *Solving the 10k-Record Edge Bottleneck with Persistent Inverted Postings*
* **Visuals / Comparison Chart:**
  * Bar chart or table comparing Pre-Optimization vs. Optimized EdgeMed at 10,000 records.
  * Green highlight badge: **"11.4x Faster at 10k Records"**.

```
+---------------------------------------+-------------------+-------------------+
| Benchmark Metric                      | Pre-Optimization  | EdgeMed Optimized |
+---------------------------------------+-------------------+-------------------+
| 1,000 Records Hybrid Search (p50)     | 4.3 ms            | 4.1 ms            |
| 10,000 Records Hybrid Search (p50)    | 101.5 ms (LAG)    | 8.9 ms (SUB-10MS!)|
| 10,000 Records Hybrid Search (p95)    | 142.0 ms          | 14.6 ms           |
| Lexical Scoring Overhead (p50)        | 92.0 ms (THRASH)  | 2.8 ms (OPTIMIZED)|
| Vector Scoring Overhead (Qdrant Edge) | 9.5 ms            | 6.1 ms            |
| Corpus Preparation on Query Path      | O(N) Rebuild      | O(1) Precomputed  |
+---------------------------------------+-------------------+-------------------+
```

### Slide Content
* **The Edge Dilemma:** In-memory lexical scoring crashes or causes memory thrashing once corpora exceed 32 MiB on low-power devices.
* **The Architectural Breakthrough:**
  1. Persistent inverted postings table (`lexical_postings`) indexed by `(term, memory_id)`.
  2. Incremental background maintenance during revision insertion.
  3. Precomputed document frequency caching (`total_docs`, `term_freqs`).
* **The Result:** Complete end-to-end backend hybrid search drops from **101.5 ms to 8.9 ms** at 10,000 synthetic records—a **91.2% latency reduction**!

### Speaker Script (35 Seconds)
> *"A critical requirement of the hackathon was low-latency search on device. When testing naive implementations at 1,000 records, queries took ~4ms. But at 10,000 records, query latency exploded to over 100 milliseconds because memory-limited edge devices thrashed rebuilding lexical corpora. We solved this by designing a persistent SQLite sparse inverted postings index with precomputed term statistics. The result? At 10,000 records, our complete backend hybrid search takes just 8.9 milliseconds p50—an 11.4x speedup, maintaining sub-10ms performance on modest hardware without touching the cloud."*

---

## Slide 5: Intelligent Selective Sync & Evolving Memory DAG

### Slide Purpose
Directly answer the problem statement requirements: *"Dynamically decide what remains local vs synchronized"*, *"Handle evolving memory and conflicting information"*, and *"Demonstrate a meaningful edge-to-cloud workflow"*.

### Layout & Visual Design
* **Header:** **Intelligent Sync & Multi-Branch Conflict Resolution**
* **Subtitle:** *Zero-Data-Leakage Egress Policy + Append-Only DAG Revisions*
* **Visuals:** Split comparison diagram:
  * Left: Egress Filter (Clinical Notes = BLOCKED, Reference Guidelines = ALLOWED).
  * Right: Git-like Revision DAG with Branching and 3-Way Resolution.

```
       [ LOCAL DATA ]                           [ EGRESS FILTER ]             [ CENTRAL GATEWAY ]
+----------------------------+             +---------------------------+       +-------------------+
| Patient Notes / Vitals     | ----------> | Policy: fixture == NULL   | ----> | PERMANENTLY       |
| Privacy: SENSITIVE         |             | Action: CANCEL DELIVERY   |       | BLOCKED (0 LEAK)  |
+----------------------------+             +---------------------------+       +-------------------+
| Clinical Guidelines        | ----------> | Policy: fixture != NULL   | ----> | mTLS 1.3 + Ed25519|
| Privacy: PUBLIC            |             | Action: QUEUE OUTBOX      |       | Push to Central   |
+----------------------------+             +---------------------------+       +-------------------+

       [ EVOLVING MEMORY REVISION DAG & CONFLICT RESOLUTION ]
                [Rev 1: Initial Diagnosis (Dr. Alice)]
                               /       \
                              v         v
     [Rev 2A: Updated Vitals]             [Rev 2B: Offline Lab Entry]
     (Active Branch Head A)               (Active Branch Head B)
                              \         /
                               v       v
            [Rev 3: Three-Way Merged & Resolved Resolution]
```

### Slide Content
* **Dynamic Egress Decision Engine:**
  * **Clinical Observations:** Observations, vitals, allergies, and notes are hardcoded to `LOCAL_ONLY`. Double-check egress guard physically cancels any non-fixture outbox item before transmission.
  * **Public Knowledge:** Only reviewed synthetic reference templates (`reference-hydration`, `reference-handoff`) enter the signed mTLS 1.3 outbox queue.
* **Evolving Memory DAG:**
  * All updates append to a Directed Acyclic Graph (`revisions` table).
  * If intermittent connectivity leads to concurrent edits on separate tablets, EdgeMed preserves both branches (`heads` array), marks `conflicting=True`, and enables seamless 3-way administrative resolution.
* **Verified Snapshots:** Central reference updates are packaged as signed shards. The local node verifies Ed25519 signatures, checks tar traversal (`../`), and scrolls through Qdrant vector points to ensure metadata matches before activation.

### Speaker Script (35 Seconds)
> *"Problem Statement 03 asks: how do we intelligently manage what stays on device versus what syncs? In EdgeMed, patient observations are cryptographically barred from egress. A double-check filter physically cancels any transmission attempt of private care notes. Only approved public clinical guidelines can cross the wire, signed with Ed25519 over mTLS 1.3. Furthermore, when care teams work offline, concurrent edits create divergent DAG branches rather than destructive overwrites. EdgeMed tracks all branch heads, alerts clinicians to conflicts, and provides an audited 3-way resolution workflow. It’s Git for clinical edge memory."*

---

## Slide 6: Product Experience — Beyond a Database, a Complete Clinical Product

### Slide Purpose
Prove to the judges that this is a finished, polished, user-facing product across 4 complete workspaces with responsive UI, dark/light modes, and real-time visualization.

### Layout & Visual Design
* **Header:** **The Clinician Experience: 4 Integrated Workspaces**
* **Subtitle:** *Responsive React 19 SPA with Catppuccin Latte & Mocha Design System*
* **Layout:** 4 Visual Feature Cards showcasing each core screen:

```
+---------------------------------------------------------------------------------------------------+
| 1. Visual Data Logging Workspace                 | 2. Synthetic Subjects / Patient Roster         |
| - Quick-entry cards: Vitals, Labs, Symptoms, Note| - Searchable roster (SYN-001, SYN-002, SYN-003)|
| - Instant range validation (<10ms commit)        | - Consolidated patient chart & timeline        |
| - Live SVG trend charts: BP, Pulse, Respiration  | - Longitudinal vitals graph & allergy badges   |
| - Real-time observation feed + Needs Review queue| - Chronological medical history filter         |
+--------------------------------------------------+------------------------------------------------+
| 3. Sync Monitor & Memory Lab                     | 4. Core Memory & Hybrid Retrieval              |
| - Connectivity hero (Connected, Stale, Paused)   | - Sub-10ms instant search bar (Ctrl+K)         |
| - Outbox delivery inspector with state filter    | - Hybrid RRF vs Semantic mode toggle           |
| - Tamper-evident HMAC audit event timeline       | - Record inspector & revision history DAG modal|
| - Simulation lab: Network latency, packet drops  | - Multi-head conflict resolution dialog        |
+---------------------------------------------------------------------------------------------------+
```

### Slide Content
* **1. Visual Data Logging:** Fast clinical data entry with structured vitals cards, immediate range validation, live trendlines, and unreviewed observation queues.
* **2. Patient Roster:** Longitudinal patient-centric view; tracks historical vital signs over time, highlights high-risk allergy alerts, and filters patient observations.
* **3. Sync Monitor & Memory Lab:** Transparent dashboard for inspecting outbox queues, tracking HMAC audit logs, checking vault status, and simulating network partitions.
* **4. Memory & Hybrid Search:** Power-search interface with keyboard shortcuts (`Ctrl+K`), real-time latency diagnostics, and conflict review banners.

### Speaker Script (35 Seconds)
> *"The problem statement specifically demanded a user-facing interface to inspect memory, search results, and sync activity—not just a raw terminal script. EdgeMed delivers four complete workspaces in a responsive React 19 interface. Clinicians use Visual Logging for rapid vitals entry and SVG trend charting. The Subjects workspace gives doctors a consolidated patient chart with longitudinal vital history. The Sync Monitor provides full transparency into outbox delivery queues and HMAC audit logs, complete with an interactive network simulation lab. And our Core Memory workspace allows doctors to search 10,000 records in under 9 milliseconds."*

---

## Slide 7: Verification, Hardened Security & Operational Roadmap

### Slide Purpose
Close the presentation with unshakeable credibility: test proof, formal threat modeling, and clear next steps.

### Layout & Visual Design
* **Header:** **Verified Security, Battle-Tested Code & Roadmap**
* **Subtitle:** *Formal Threat Model, 77 Passing Backend Tests & Operational Path*
* **Layout:** Three vertical columns: **Test Proof**, **Security Boundaries**, and **Future Milestones**.

```
+---------------------------+---------------------------+---------------------------+
| 1. Test & QA Proof        | 2. Security Boundaries    | 3. Operational Roadmap    |
|                           |                           |                           |
| [✓] 77 Backend Tests Pass | [✓] Multi-Tenant Ward     | [ ] Physical Linux LUKS2  |
| [✓] 4 Playwright E2E      |     Isolation (ward-a/b)  |     Hardware Rehearsal    |
|     Browser Test Suites   | [✓] Personal Isolation    | [ ] Mobile LAN CA Trust   |
| [✓] Ruff Linter 100% Clean|     (personal:{user})     |     Store Installation    |
| [✓] Cross-platform builds | [✓] BoundedHTTP (32 KiB)  | [ ] Enterprise Hospital   |
|     (macOS & Linux 64-bit)| [✓] SameSite=Strict CSRF  |     IdP (OIDC/SAML) Gate  |
| [✓] Zero runtime model    | [✓] SQLCipher AES-256-CBC | [ ] Android Native        |
|     download dependencies | [✓] Fail-Closed Keyrings  |     Offline Backend App   |
+---------------------------+---------------------------+---------------------------+
```

### Slide Content
* **Rigorous Verification:**
  * **77 out of 77 automated tests passing** across security, storage, LAN TLS, snapshots, and 10k retrieval scaling.
  * 4 end-to-end Playwright suites validating UI layouts down to 320px mobile viewport.
* **Formal Threat Modeling (`THREAT_MODEL.md`):** Complete asset classification, trust boundaries, multi-tenant ward isolation, personal privacy isolation, and zero-egress data leakage defenses.
* **Clear Next Steps:** Moving from synthetic research prototype toward physical host rehearsals, Android mobile client packaging, and hospital IdP integration.
* **Conclusion:** EdgeMed proves that edge AI with Qdrant Edge is not just viable—it is the foundation for private, resilient, low-latency intelligent edge networks.

### Speaker Script (30 Seconds)
> *"To ensure EdgeMed wasn’t just a concept, we built an exhaustive regression suite: 77 backend integration tests and four Playwright browser suites, all passing with zero failures. We published a full Threat Model covering multi-tenant isolation, CSRF protection, and fail-closed storage. We proved that with Qdrant Edge, an offline-native platform can deliver sub-10ms search, resolve decentralized conflicts, and strictly enforce data privacy. EdgeMed is ready to redefine how edge memory powers mission-critical healthcare. Thank you, and we welcome your questions!"*

---

## Summary of Diagram & Visual Placement Guide

| Slide # | Title | Recommended Visual / Diagram | Asset / Source in Repo |
| :--- | :--- | :--- | :--- |
| **Slide 1** | Title & Hook | Hero branding artwork + 5 feature badges | `assets/edgemed-hero.png` + Shields badges in `README.md` |
| **Slide 2** | The Core Problem | 2x2 grid of challenge cards with red warning icons | Visual layout defined in Slide 2 |
| **Slide 3** | System Architecture | Multi-Tier Architectural Layer Blueprint | Mermaid flowchart in `docs/SYSTEM_ARCHITECTURE.md` |
| **Slide 4** | Retrieval Scalability | 10k Benchmark latency comparison bar chart | Data table from `docs/PROJECT_AUDIT.md` & `search-10k.json` |
| **Slide 5** | Intelligent Sync & DAG | Egress Filter + Git-like Revision DAG diagram | Sequence diagram in `docs/SYSTEM_ARCHITECTURE.md` |
| **Slide 6** | Product Experience | 4-quadrant UI preview cards with feature badges | Workspaces in `frontend/src/` (`logging`, `subjects`, `sync`) |
| **Slide 7** | Verification & Roadmap | 3-column verification matrix with green checkmarks | Test summary from `tests/` and roadmap from `TODO.md` |

---

## 3-Minute Presentation Pitch Timing Cheat Sheet

* **0:00 - 0:30 (Slide 1):** The Offline Hospital Ward Crisis & Introduction to EdgeMed.
* **0:30 - 1:05 (Slide 2):** Why Traditional Cloud AI Fails at the Edge (The 4 Fatal Flaws).
* **1:05 - 1:45 (Slide 3):** EdgeMed Architecture: Canonical SQLCipher + Dual Qdrant Projections.
* **1:45 - 2:20 (Slide 4):** Deep-Tech Benchmark: Breaking the 10,000-Record Latency Bottleneck (8.9ms p50).
* **2:20 - 2:55 (Slide 5):** Intelligent Egress Filtering & Git-like Multi-Branch Conflict Resolution.
* **2:55 - 3:30 (Slide 6):** The 4 Integrated Workspaces: A Complete User-Facing Care Experience.
* **3:30 - 4:00 (Slide 7):** Battle-Tested Proof (77 Tests, Threat Model) & Visionary Close.
