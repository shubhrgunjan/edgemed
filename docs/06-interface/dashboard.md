# Screen Specification: Clinical Triage Dashboard

- **Document Version:** 1.0.0
- **Status:** Complete / Design Specification
- **Date:** 2026-09-26

---

## 1. Purpose
The **Dashboard** serves as the clinician's home view, offering an immediate operational summary of patient volume, active clinical contradictions, recent triage observations, system resource usage, and connectivity status.

---

## 2. Screen Specifications

- **Layout:** Three-column grid layout (Top Summary Metric Cards, Center Triage Activity Stream, Right Sidebar System & Sync Health).
- **Components:**
  - `MetricCardGrid`: 4 key indicators (Total Local Memories, Active Patients, Conflicting Records, Outbound Queue Size).
  - `RecentActivityFeed`: Chronological list of recently ingested clinical observations with category badges.
  - `ContradictionAlertBanner`: Prominent amber/red card notifying operator if any records are in `REQUIRES_REVIEW` status.
  - `HardwareGauge`: Mini-charts showing CPU load, RAM usage (out of 8 GB), and disk usage.
- **Data Displayed:**
  - Real-time memory count, patient count, queue depth.
  - Snippets of recent observations with timestamps, category tags, and provenance links.
  - Immediate alert details for conflicting medical assertions.
- **User Actions:**
  - Click "Review Contradiction" -> Navigates to Memory Inspector with conflict diff.
  - Click "New Observation" -> Opens quick-entry modal.
  - Click any recent memory card -> Opens Memory Inspector.
- **Backend Requirements:**
  - `GET /api/stats`: Aggregate system and memory statistics.
  - `GET /api/memories?limit=10&sort=desc`: Recent observation stream.
- **Loading States:** Skeleton shimmer blocks on metric cards and activity stream.
- **Error States:** Fallback warning toast if `/api/stats` fails to respond; retry button displayed.
- **Offline Behavior:** 100% operational offline. Displays cached local statistics and updates instantaneously as new local observations are added.
