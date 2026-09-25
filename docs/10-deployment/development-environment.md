# Development Environment Specification

- **Document Version:** 1.0.0
- **Status:** Complete / Developer Setup Guide
- **Date:** 2026-09-26

---

## 1. Prerequisites and Toolchain

To prepare the development environment for EdgeMed on Linux (specifically tested on Ubuntu / Debian / Fedora with AMD hardware):
- **Python:** 3.11 or 3.12 (managed via `uv` or `pyenv`)
- **Package Manager:** `uv` recommended for fast dependency resolution
- **Node.js:** 18+ LTS (for React/TypeScript UI builds)
- **Container Engine:** Docker or Podman (for running the central test Qdrant Server container)
- **C/C++ Build Essentials:** GCC/Clang, Make (for native ONNX and SQLite extensions if required)

---

## 2. Directory Layout & Workspace Setup

```bash
# Clone the repository
git clone https://github.com/shubhrgunjan/edgemed.git
cd edgemed

# Create isolated Python virtual environment using uv
uv venv .venv
source .venv/bin/activate

# Install project specifications & future runtime dependencies
# (Implementation phase dependencies will include: fastapi, uvicorn, qdrant-edge-py, fastembed, pydantic)
```

---

## 3. Local Test Infrastructure (Qdrant Server Node)

For testing edge-to-cloud synchronization locally, spin up a lightweight Qdrant Server instance via Docker:
```bash
docker run -d --name qdrant-test-server \
  -p 6333:6333 \
  -p 6334:6334 \
  -v $(pwd)/qdrant_server_data:/qdrant/storage \
  qdrant/qdrant:latest
```
