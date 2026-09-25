# Contributing to EdgeMed

Thank you for your interest in contributing to **EdgeMed**! This document provides guidelines for contributors, architects, and developers working on Code Cubicle 6.0 (Problem Statement 03).

---

## 1. Project Phase Notice

> [!IMPORTANT]
> The repository is currently in **PHASE 0: ARCHITECTURE & SPECIFICATION**.
> During this phase:
> - **DO NOT implement production code, frontend apps, or mock APIs.**
> - Contributions must focus on refining documentation, data schemas, OpenAPI contracts, ADRs, test specifications, and architectural diagrams.

---

## 2. Architectural Principles to Uphold

Every pull request and proposal must adhere to our core architectural principles:
1. **Never Make Qdrant Responsible for Everything:** Keep semantic vector search, explicit knowledge graph topology, temporal events, and data governance cleanly decoupled.
2. **Offline-First:** All local operations (retrieval, storage, graph queries) must execute with 100% autonomy without internet.
3. **Synthetic Data Only:** Never commit real clinical records or PHI. All test fixtures must be procedurally generated synthetic data.
4. **Research-Backed Claims:** Do not claim upstream Qdrant capabilities unless documented in official Qdrant documentation. Distinguish native features from custom EdgeMed components.

---

## 3. How to Contribute

### 3.1 Proposing Architecture Changes
1. Open an issue using the `Architecture Decision` template.
2. Draft an ADR following our standard format in `architecture/decisions/` (`Context`, `Problem`, `Options Considered`, `Decision`, `Consequences`, `Status`).
3. Ensure diagrams are written in valid Mermaid syntax under `architecture/diagrams/`.

### 3.2 Updating Schemas or API Contracts
1. Modify the relevant JSON Schema under `schemas/`.
2. Update the OpenAPI 3.1 contract in `api/openapi/openapi.yaml`.
3. Provide or update corresponding test fixtures in `examples/`.

### 3.3 Pull Request Process
1. Use the PR template in `.github/pull_request_template.md`.
2. Ensure internal links in Markdown files are valid.
3. Confirm no production implementation code has been introduced prematurely.
4. Obtain review from Team LEX architectural leads.
