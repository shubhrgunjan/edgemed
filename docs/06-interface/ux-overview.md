# User Experience & Interface Overview

- **Document Version:** 1.0.0
- **Status:** Complete / Design Specification (No UI Implementation in Phase 0)
- **Date:** 2026-09-26
- **Lead UX Architect:** Team LEX (Code Cubicle 6.0 — PS03)

---

## 1. Design Philosophy: The High-Acuity Medical HUD

The EdgeMed operator interface is engineered for high-stress, rapid-decision environments (field triage, disaster response, and emergency medicine):
- **Visual Aesthetic:** Dark-mode primary palette (`#0B0F19` background) with high-contrast clinical status accents:
  - Clinical Safe / Confirmed: Teal / Emerald (`#10B981`)
  - Acute / Conflicting / Alert: Crimson / Amber (`#EF4444` / `#F59E0B`)
  - Semantic / Vector Links: Electric Blue (`#3B82F6`)
  - Offline Mode Indicator: Deep Indigo / Violet (`#6366F1`)
- **Zero-Latency Responsiveness:** Instant UI feedback (<50ms interaction response) with local optimistic updates.
- **Unambiguous Connectivity Status:** The global header permanently anchors the current network state (`ONLINE`, `OFFLINE`, or `DEGRADED`) with real-time queue counters.

---

## 2. Navigation Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [EDGEMED LOGO]  [● OFFLINE MODE (AUTONOMOUS)]  [Queue: 3 Pending]  [CPU: 14% | RAM: 380MB]│
├────────────────────────────────────────────────────────────────────────────────────────┤
│ (1) Dashboard | (2) Memory Explorer | (3) Semantic Search | (4) Knowledge Graph        │
│ (5) Memory Inspector | (6) Sync Monitor | (7) Edge Inspector | (8) Memory Laboratory   │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│                                  ACTIVE SCREEN VIEW                                    │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

The application exposes 8 dedicated functional screens:
1. **Dashboard:** High-level clinical triage overview, system metrics, and recent alerts.
2. **Memory Explorer:** Paginated and filtered inventory of all local memories.
3. **Semantic Search:** Hybrid search input with interactive result score attribution chips.
4. **Knowledge Graph:** Obsidian-style interactive Cytoscape.js relational graph.
5. **Memory Inspector:** Deep-dive modal/drawer showing full tripartite attributes and provenance.
6. **Sync Monitor:** Real-time queue telemetry, bandwidth charts, and manual flush controls.
7. **System / Edge Inspector:** Hardware metrics, Qdrant Edge shard stats, and SQLite WAL health.
8. **Memory Laboratory:** Interactive test bench for simulating edge-cloud events, offline modes, and contradictions.
