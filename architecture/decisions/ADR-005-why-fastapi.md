# ADR-005: Selection of FastAPI for Edge Gateway and Local Services

- **Status:** Approved / Core Framework Selection
- **Date:** 2026-09-26
- **Author:** Team LEX (Code Cubicle 6.0 — PS03)

## Context
EdgeMed requires a local HTTP and WebSocket service layer running on the edge device to interface between the storage engine (Qdrant Edge, SQLite), the governance layer, and the operator UI.

## Problem
The backend must support async concurrent requests, automatic OpenAPI contract generation, low resource consumption, and seamless interoperability with Python-based AI bindings (`qdrant-edge-py`, `fastembed`, `onnxruntime`).

## Options Considered
1. **Flask:** Synchronous by default, lacks native async concurrency for streaming sync events, manual OpenAPI generation.
2. **Rust / Axum:** Maximum performance and lowest footprint, but Python AI binding ecosystem (`fastembed`, `pydantic`, `qdrant-edge-py`) is significantly faster to develop and maintain in Python.
3. **FastAPI with Pydantic v2:** Built on Starlette/Uvicorn; native async I/O; Pydantic v2 compiled in Rust for high validation speed; automatic interactive OpenAPI documentation.

## Decision
Adopt **FastAPI** as the application server framework.

## Consequences
- **Positive:** Rapid development; native async handling of WebSocket sync status updates; automatic OpenAPI/JSON-Schema export; seamless bridge to Python AI libraries.
- **Negative:** Requires careful async/await isolation when calling blocking CPU tasks (such as embedding computation, which must be run in thread pools via `run_in_threadpool` or `asyncio.to_thread`).
