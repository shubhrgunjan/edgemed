# Screen Specification: Obsidian-Style Knowledge Graph View

- **Document Version:** 1.0.0
- **Status:** Complete / Design Specification
- **Date:** 2026-09-26
- **Lead UX Architect:** Team LEX (Code Cubicle 6.0 — PS03)

---

## 1. Purpose
The **Knowledge Graph View** provides an Obsidian-style interactive 2D canvas visualizing explicit ontological relationships between clinical entities. It allows clinicians to inspect drug contraindications, patient disease histories, symptom timelines, and active contradictions topologically.

> [!IMPORTANT]
> **Strict Semantic Boundary:**
> Graph edges represent explicit, verified clinical relationships (`HAS_CONDITION`, `TREATED_WITH`, `CONTRADICTS`, `SUPERSEDES`). Vector similarity scores are NEVER rendered as graph edges.

---

## 2. Screen Specifications

- **Layout:** Full-viewport interactive Cytoscape.js canvas with floating HUD controls (Layout Selector, Node Type Filters, Search Filter, Mini-Map).
- **Components:**
  - `GraphCanvas`: Hardware-accelerated canvas utilizing physics-based force layout (CoSE / Cola algorithm).
  - `NodeTypeFilterBar`: Toggle chips for node types (`Patient`, `Condition`, `Medication`, `Procedure`, `Observation`, `Event`, `Document`).
  - `EdgeLegend`: Color-coded line styles:
    - `HAS_CONDITION`: Solid Cyan
    - `TREATED_WITH`: Solid Emerald
    - `CONTRADICTS`: Pulsing Red / Dashed
    - `SUPERSEDES`: Amber Arrow
    - `HAS_EVENT`: Dotted Violet
    - `MENTIONS`: Subtle Grey
    - `DERIVED_FROM`: Faint Dotted Grey
  - `NodeDetailInspector`: Slide-over card when a node is clicked, showing its properties and connected edges.
- **Data Displayed:**
  - Nodes categorized by icon and color.
  - Directional arrows with edge labels.
  - Highlighting of contradiction clusters in red.
- **User Actions:**
  - Pan / Zoom / Drag nodes.
  - Hover node -> Dim unconnected nodes; highlight immediate 1-hop neighborhood.
  - Click node -> Opens properties drawer with link to full Memory Inspector.
  - Switch layout -> Physics force-directed, hierarchical tree, or circular.
- **Backend Requirements:**
  - `GET /api/graph?patient_id=...&max_depth=2`: Exports Cytoscape-formatted JSON elements (`nodes` and `edges`).
- **Loading States:** Centered progress spinner while SQLite executes recursive CTE and initializes physics simulation.
- **Error States:** Fallback notification if graph exceeds 2,500 nodes (prompts user to filter by specific patient).
- **Offline Behavior:** 100% operational offline. Graph renders entirely from local SQLite tables in `<50ms`.
