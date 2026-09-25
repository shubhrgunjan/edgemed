# Global Acceptance Criteria and Verification Standards

- **Document Version:** 1.0.0
- **Status:** Complete / Authoritative Acceptance Baseline
- **Date:** 2026-09-26
- **Lead Quality Engineer:** Team LEX (Code Cubicle 6.0 — PS03)

---

## 1. Hackathon Acceptance Gate Definition

The EdgeMed platform will be judged complete and ready for the Code Cubicle 6.0 demonstration only when all of the following sixteen acceptance gates are validated:

1. **Gate 1 (Zero-Network Search):** The device can be booted in airplane mode and successfully execute natural-language queries against local clinical notes with `< 5ms` latency.
2. **Gate 2 (Cold Boot Persistence):** Memories created on the edge persist through cold restarts without requiring cloud rehydration.
3. **Gate 3 (Tripartite Synthesis):** Search results return vector similarity scores, linked graph entities, and chronological event progressions simultaneously.
4. **Gate 4 (Privacy Pinning):** `HIGHLY_SENSITIVE` observations remain strictly local; cloud audits confirm zero byte leakage.
5. **Gate 5 (Intermittent Reconnect):** Unplugging and reconnecting network links does not trigger unhandled exceptions, memory leaks, or duplicate writes.
6. **Gate 6 (Non-Destructive Contradiction):** Conflicting clinical assertions remain co-present in the system, flagged as `CONFLICTING` for clinician adjudication.
7. **Gate 7 (Memory Consolidation):** High-frequency vitals cluster into consolidated summary records with preserved provenance trees.
8. **Gate 8 (Complete Provenance):** Clicking any retrieved memory in the UI renders its full origin device, author, hash, and transformation history.
9. **Gate 9 (Differential Replication):** Server snapshot updates transfer only changed segments via manifest diffs.
10. **Gate 10 (Interactive Graph UI):** The Cytoscape knowledge graph renders at 60 FPS and supports interactive node filtering and neighborhood exploration.
11. **Gate 11 (Memory Lab Controls):** The testing HUD allows judges to simulate network disconnects, trigger reconciliations, and force governance evaluations interactively.
12. **Gate 12 (RAM Enveloping):** System memory footprint stays under 450 MB working set throughout sustained operation.
13. **Gate 13 (OpenAPI Conformance):** All REST and WebSocket endpoints match the formal OpenAPI 3.1.0 specification.
14. **Gate 14 (Schema Validation):** All payloads strictly conform to the published JSON Schema models.
15. **Gate 15 (Zero Real PHI):** 100% of demo fixtures are certified synthetic.
16. **Gate 16 (Full Traceability):** Every PS03 requirement is traceable to verified acceptance tests.
