# Screen Specification: Memory Laboratory Demonstration Suite

- **Document Version:** 1.0.0
- **Status:** Complete / Authoritative Design Specification
- **Date:** 2026-09-26
- **Lead UX Architect:** Team LEX (Code Cubicle 6.0 — PS03)

---

## 1. Purpose and Role for Hackathon Judging

The **Memory Laboratory** is the flagship demonstration interface for Code Cubicle 6.0 judges and developers. It serves as an interactive simulator and diagnostic command center, enabling users to trigger, manipulate, observe, and verify every dynamic behavior of the EdgeMed platform without relying on external network conditions.

---

## 2. Interactive Control Matrix

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 MEMORY LABORATORY HUD                                  │
├────────────────────────────────┬───────────────────────────────┬───────────────────────┤
│ MEMORY MANIPULATION CONTROLS   │ NETWORK SIMULATION CONTROLS   │ GOVERNANCE & AI TESTS │
├────────────────────────────────┼───────────────────────────────┼───────────────────────┤
│ [➕ Create Synthetic Memory]   │ [🔌 Simulate Network Sever]   │ [⚖️ Evaluate Governor] │
│ [✏️ Modify Observation]        │ [📶 Simulate Reconnection]    │ [🧹 Consolidate Memories]
│ [❌ Delete Memory]             │ [🚀 Trigger Sync Queue Drain] │ [🔍 Inspect Provenance]
│ [⚡ Inject Contradiction]      │ [🌐 Force Server Manifest]    │ [🛡️ Test Privacy Block]
└────────────────────────────────┴───────────────────────────────┴───────────────────────┘
```

### Detailed Functional Controls:

1. **`Create Memory`:** Opens an interactive form to inject synthetic clinical notes, vitals, or diagnoses with selectable category and privacy levels.
2. **`Delete Memory`:** Deletes or soft-archives a memory, verifying immediate removal from local search and propagation to the tombstone sync queue.
3. **`Modify Memory`:** Edits an existing observation, creating an incremented `version` and appending a delta entry in the provenance DAG.
4. **`Create Conflict (Inject Contradiction):`** Injects a clinical finding that directly opposes an existing confirmed record (e.g., adding an amoxicillin prescription for a patient with a confirmed penicillin allergy). Verifies that both records transition to `CONFLICTING` without data loss.
5. **`Simulate Offline (Sever Network):`** Toggles a software network gate in the Connectivity Manager, simulating complete physical link loss. Verifies zero search downtime and confirms outbound items accumulate in the SQLite sync queue.
6. **`Simulate Reconnect:`** Re-enables the network gate, triggering an automatic heartbeat, queue flush, and partial snapshot pull.
7. **`Trigger Synchronization:`** Manually initiates an immediate queue drain and displays the live batch payload transmitted to the server.
8. **`Inspect Provenance:`** Opens the provenance DAG for the selected memory, revealing origin device ID, capturing user, and content hash.
9. **`Evaluate Governance:`** Submits a memory to the Memory Governor scoring model and displays the live factor scorecard ($I, C, R, F, D$) and verdict (`LOCAL`, `SYNC_CANDIDATE`, `EXPIRE`).
10. **`Consolidate Memories:`** Triggers the Consolidation Worker, clustering repeated vitals into a single summary record with preserved parent links.

---

## 3. Screen Specifications

- **Layout:** Three-panel master-detail layout:
  - Left Panel: Action Command Toolbar & Simulation Triggers.
  - Center Panel: Interactive Execution Log & State Inspector.
  - Right Panel: Real-Time Event Telemetry Stream (WebSocket feed).
- **Backend Requirements:**
  - `POST /api/governance/evaluate/{id}`: Manual governor evaluation.
  - `POST /api/memories/consolidate`: Triggers clustering pass.
  - `POST /api/sync`: Forces queue drain.
  - `POST /api/system/simulate-network`: Toggles network simulation states.
- **Offline Behavior:** 100% operational offline.
