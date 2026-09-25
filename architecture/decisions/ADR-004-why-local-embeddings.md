# ADR-004: Local On-Device Embedding Pipeline via FastEmbed / ONNX

- **Status:** Approved / Validated for Target Hardware
- **Date:** 2026-09-26
- **Author:** Team LEX (Code Cubicle 6.0 — PS03)

## Context
Semantic search on the edge requires converting input text into dense vector representations. The system must operate fully offline without external API calls (e.g., OpenAI or Vertex AI).

## Problem
Standard PyTorch-based embedding libraries (`sentence-transformers`, `torch`) impose enormous binary overhead (>2 GB disk footprint, >1 GB RAM allocation), which risks crashing constrained edge devices and consumes excessive memory on the target 8 GB RAM development machine.

## Options Considered
1. **Cloud Embedding APIs:** Unusable offline; violates patient privacy constraints.
2. **PyTorch + SentenceTransformers:** Heavy dependencies; excessive RAM overhead.
3. **FastEmbed with ONNX Runtime (`BAAI/bge-small-en-v1.5`):** Quantized integer models executing on CPU via ONNX Runtime without PyTorch.

## Decision
Adopt **FastEmbed** with quantized ONNX models (`bge-small-en-v1.5`, 384 dimensions). This provides high-quality semantic representations while consuming only ~120 MB RAM and executing in 12–16 ms on the AMD Ryzen 5 5500U CPU.

## Consequences
- **Positive:** Low latency; zero network requirement; tiny footprint (<150 MB disk, <150 MB RAM); zero discrete GPU requirements.
- **Negative:** Fixed dimension size (384-d); migrating to larger models in the future requires re-embedding local collections.
