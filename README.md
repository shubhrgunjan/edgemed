# EdgeMed — Protected Memory Across Local Care Networks

<p align="center">
  <img src="assets/edgemed-hero.png" alt="EdgeMed Hero" width="800" />
</p>

<p align="center">
  <em>A local-first, offline-first memory and hybrid search engine for protected synthetic clinical notes.</em>
</p>

<p align="center">
  <a href="https://farhanakhtar0x66.github.io/edgemed-synthetic-demo/"><img src="https://img.shields.io/badge/Live%20Demo-Browser%20Sample-40a02b?style=flat-square&logo=googlechrome&logoColor=white" alt="Live Demo" /></a>
  <a href="https://www.youtube.com/watch?v=-EHztt86J2c"><img src="https://img.shields.io/badge/Demo%20Video-YouTube-ff0000?style=flat-square&logo=youtube&logoColor=white" alt="Demo Video" /></a>
  <a href="https://github.com/shubhrgunjan/edgemed"><img src="https://img.shields.io/badge/GitHub-shubhrgunjan%2Fedgemed-181825?style=flat-square&logo=github&logoColor=white" alt="GitHub" /></a>
  <img src="https://img.shields.io/badge/Version-0.1.0-89b4fa?style=flat-square" alt="Version 0.1.0" />
  <img src="https://img.shields.io/badge/Python-3.12-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/FastAPI-0.141.1-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Tests-77%20passed-a6e3a1?style=flat-square&logo=pytest&logoColor=white" alt="Tests 77 Passed" />
  <img src="https://img.shields.io/badge/Storage-SQLCipher%20(AES--256)-fab387?style=flat-square&logo=sqlite&logoColor=white" alt="SQLCipher" />
  <img src="https://img.shields.io/badge/Vector%20Engine-Qdrant%20Edge%20(384--d)-cba6f7?style=flat-square&logo=qdrant&logoColor=white" alt="Qdrant Edge" />
  <img src="https://img.shields.io/badge/Embeddings-FastEmbed%20ONNX-f38ba8?style=flat-square&logo=onnx&logoColor=white" alt="FastEmbed ONNX" />
  <img src="https://img.shields.io/badge/License-Apache--2.0-b4befe?style=flat-square" alt="License" />
</p>

---

> [!CAUTION]
> **Synthetic Data Notice:** EdgeMed is a research prototype developed for Team LEX Problem Statement 03. It is **not approved for clinical use or real patient records**. All notes and entities must remain synthetic.

---

> [!TIP]
> 📺 **Video Walkthrough & Architecture Demo:** Watch the complete 3-minute architectural and live demo walkthrough on YouTube: [EdgeMed — Offline-First Clinical Memory | Demo](https://www.youtube.com/watch?v=-EHztt86J2c)

---

## System Architecture Blueprint & Layer Flow

Local capture and search do not require an external cloud service. The optional reference-sharing path uses a separately configured local gateway and Qdrant Server. SQLCipher remains the canonical store, with vector and lexical search projections:

```mermaid
flowchart TB
    subgraph Layer1["1. Clients & Presentation Boundary"]
        SPA["EdgeMed SPA (React 19 / TypeScript / Vanilla CSS Tokens)"]
        Log["Visual Data Logging Workspace"]
        Roster["Synthetic Subjects Roster"]
        Monitor["Sync Monitor & Memory Lab"]
        Demo["Public Static Demo (Browser-Only / No Backend)"]
    end

    subgraph Layer2["2. Transport, Security & Origin Boundary"]
        Bound["BoundedHTTP (32 KiB Limit / 10s Timeout)"]
        SecHeaders["Security Headers (CSP, no-store, nosniff, no-referrer)"]
        HostOrigin["Host, Origin & Sec-Fetch-Site Guards"]
        AuthCSRF["Argon2id Session + Timing-Safe CSRF Verification"]
        ASGI["FastAPI ASGI Core Engine (127.0.0.1:8765 / Private LAN HTTPS)"]
    end

    subgraph Layer3["3. Identity & Workspace Scoping Boundary"]
        Scopes["Workspace Scoping (ward-a, ward-b)"]
        Personal["Personal Privacy Isolation: personal:{username}"]
        Gov["Advisory Governance & Retention Evaluator"]
    end

    subgraph Layer4["4. Canonical Storage & Audit Ledger (Single Source of Truth)"]
        SQL["SQLCipher 4 Database (memory.db / AES-256-CBC)"]
        DAG["Append-Only Revision DAG (memories, revisions, heads)"]
        Audit["Tamper-Evident HMAC-SHA256 Event Chain"]
        Tombstone["Tombstone Deletion & Resurrection Guards"]
    end

    subgraph Layer5["5. Dual-Projection Search & Retrieval Engines"]
        direction LR
        ONNX["FastEmbed ONNX (BAAI/bge-small-en-v1.5)"]
        Qdrant["Embedded Qdrant Edge (384-d Cosine)"]
        Inverted["SQLite Inverted Index (lexical_postings)"]
        RRF["Reciprocal Rank Fusion (RRF k=60)"]
        Eligible["Canonical Head & Deletion Gate"]
    end

    subgraph Layer6["6. Synchronization & Verified Ingestion"]
        Egress["Strict Egress Filter (fixture != NULL AND privacy == 'PUBLIC')"]
        mTLS["mTLS 1.3 Transport + Ed25519 Payload Signing"]
        Snapshots["Verified Reference Snapshots (Tarbomb & Rollback Defense)"]
    end

    Layer1 -->|"HTTP Requests / Cookies"| Layer2
    Bound --> SecHeaders --> HostOrigin --> AuthCSRF --> ASGI
    ASGI -->|"Authenticated Context"| Layer3
    Layer3 -->|"Scoped Queries & Mutations"| Layer4
    Layer4 -->|"Async Indexing Jobs"| Layer5
    ONNX --> Qdrant --> RRF
    Inverted --> RRF
    RRF --> Eligible -.->|"Verified Current Heads Only"| ASGI
    Layer4 -->|"Selective Reference Export"| Layer6
    Egress --> mTLS
    Snapshots --> Qdrant
```

---

## Core Application Workspaces

| Workspace | Description | Key Capabilities | Deep Dive |
| :--- | :--- | :--- | :--- |
| **Visual Data Logging** | Rapid structured clinical observation and vitals entry | Quick-entry cards (Vitals, Labs, Symptoms, Notes), live timeline, Needs Review queue, pure SVG trend charts | [Features Guide](docs/FEATURES_GUIDE.md#2-workspace-1-visual-data-logging--monitoring) |
| **Synthetic Subjects Roster** | Consolidated patient chart interface for synthetic subjects | Searchable roster sidebar, longitudinal vitals tracking, allergy & risk alerts, chronological observation history | [Features Guide](docs/FEATURES_GUIDE.md#3-workspace-2-synthetic-subjects--patient-roster) |
| **Sync Monitor & Memory Lab** | Operational monitoring, transport inspection & network simulation | Connectivity hero status, outbox queue inspector, HMAC event log, vault diagnostics, interactive simulation controls | [Features Guide](docs/FEATURES_GUIDE.md#4-workspace-3-sync-monitor--memory-lab) |
| **Memory & Hybrid Search** | Local hybrid search across synthetic notes | FastEmbed ONNX semantic search, sparse inverted BM25 search, RRF fusion, multi-head conflict resolution | [Features Guide](docs/FEATURES_GUIDE.md#5-workspace-4-memory--hybrid-search-engine) |

---

## Synthetic retrieval measurements

The committed [scaling benchmark](docs/scaling-benchmark-results.json) used synthetic records on Windows 11 with Python 3.12.14. These are warm **complete backend search** timings, including query embedding; they are not browser round-trip times, cold starts, clinical-quality results, or guarantees on other machines.

| Synthetic records | Warm p50 | Warm p95 |
| :--- | ---: | ---: |
| 1,000 | 8.46 ms | 21.49 ms |
| 5,000 | 34.08 ms | 39.50 ms |
| 10,000 | 63.98 ms | 73.81 ms |

The new inverted index removed the earlier full-corpus lexical rebuild, but latency still grows with corpus size. An older [macOS 10,000-record run](docs/search-10k.json) measured 101.48 ms p50 under different conditions, so it is not a same-machine before/after comparison.

---

## Quickstart & Local Installation

### Prerequisites
* **OS:** macOS (Apple Silicon or Intel) or Linux (x86-64 / ARM64).
* **Tools:** Python 3.12, [`uv`](https://docs.astral.sh/uv/), Node.js 22+, and SQLCipher. Follow the [macOS installation guide](docs/installation.md) or [Linux LUKS2 guide](docs/linux-installation.md) for prerequisites and encryption setup before running these commands. The full app is for synthetic data on a local server or trusted private LAN, not public-internet hosting.

```sh
# 1. Clone repository
git clone https://github.com/shubhrgunjan/edgemed.git
cd edgemed

# 2. Install dependencies & build frontend
uv sync --frozen
(cd frontend && npm ci && npm run build)

# 3. Provision pinned verified model & Qdrant assets
uv run python scripts/provision_assets.py

# 4. Initialize encrypted vault & start local server
uv run python -m edgemed.cli setup
uv run python -m edgemed.cli start
```

Open **http://127.0.0.1:8765** in your browser.

* For staff credentials: `uv run python -m edgemed.cli credentials edge-a`
* For private hospital LAN HTTPS setup: see [Hospital LAN Guide](docs/installation.md#2-configure-https-on-a-private-lan)
* For encrypted Linux LUKS2 setup: see [Linux Setup Guide](docs/linux-installation.md)

---

## Verification & Testing

EdgeMed maintains comprehensive automated test suites across backend boundaries and frontend UI:

```sh
# Run linter
uv run ruff check edgemed tests scripts

# Run all 77 backend integration & security tests
uv run pytest -q

# Build both frontend targets (browser tests need a running app or static test servers)
(cd frontend && npm ci && npm run build && npm run build:demo)
```

---

## Technical Documentation Directory

* **[Video Walkthrough & Architecture Demo](https://www.youtube.com/watch?v=-EHztt86J2c):** Complete 3-minute recording demonstrating offline-first clinical memory, sub-10ms hybrid search benchmarks, and the local care workspace.
* **[Comprehensive Project Audit](docs/PROJECT_AUDIT.md):** Full component inventory, security audit, storage audit, and validation matrix.
* **[System Architecture Blueprint](docs/SYSTEM_ARCHITECTURE.md):** Multi-tier architecture, layer flow, data flow sequence diagrams, and intended boundaries.
* **[Features & Workspace Guide](docs/FEATURES_GUIDE.md):** Comprehensive visual walkthrough of all 4 application workspaces and themes.
* **[Threat Model & Security Validation](THREAT_MODEL.md):** Formal threat model, asset classification, trust boundaries, and regression suite.
* **[Security Boundary Statement](SECURITY.md):** Concise statement of security boundaries and data restrictions.
* **[Development Roadmap](TODO.md):** Prioritized roadmap across foundations (P0), product (P1), and scale (P2).

---

## License & Safety Notice

Licensed under [Apache-2.0](LICENSE). This software is intended for research demonstrations with synthetic care notes. It carries no clinical certifications and must not be used with identifiable patient information.
