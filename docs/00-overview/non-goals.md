# Project Non-Goals

- **Document Version:** 1.0.0
- **Status:** Complete
- **Date:** 2026-09-26

---

## 1. Explicit Non-Goals

To maintain rigorous architectural focus and eliminate scope creep, the following areas are designated as **out of scope**:

1. **Certified Diagnostic System:** EdgeMed is **NOT** a certified medical diagnostic device. It will never output primary clinical diagnoses, treatment authorizations, or drug prescriptions. It is strictly an experimental decision-support and memory retrieval prototype.
2. **Real Protected Health Information (PHI) Ingestion:** Ingesting real patient records, actual hospital EHR exports, or genuine clinical telemetry is strictly prohibited. The system exclusively uses synthetic, procedurally generated data fixtures.
3. **Heavy On-Device LLM Fine-Tuning or Massive Model Execution:** Running 70B parameter models or performing local backpropagation fine-tuning on edge CPUs is out of scope. The platform is optimized for fast CPU embeddings (FastEmbed) and lightweight vector-graph retrieval.
4. **General-Purpose File Synchronization Engine:** EdgeMed is not a generic file-syncing daemon (like Dropbox or rsync). It synchronizes structured semantic memory points and partial shard snapshots specifically for vector and graph state.
5. **Direct Replacement of Full Hospital Information Systems (HIS / EHR):** EdgeMed does not aim to replace hospital billing, appointment scheduling, or enterprise HL7/FHIR servers. It serves as a specialized edge-memory layer for field operations.
