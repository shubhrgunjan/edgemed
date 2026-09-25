# Screen Specification: Memory Explorer

- **Document Version:** 1.0.0
- **Status:** Complete / Design Specification
- **Date:** 2026-09-26

---

## 1. Purpose
The **Memory Explorer** provides a structured, paginated, and filterable table view of all memory points stored across local Qdrant Edge shards and SQLite tables.

---

## 2. Screen Specifications

- **Layout:** Filter header rail on top, central responsive data table with sortable columns, pagination controls at the footer, and a collapsible detail drawer on the right.
- **Components:**
  - `FilterToolbar`: Multi-select dropdowns for Category, Privacy Tier, Lifecycle State, and Sync Status; free-text keyword filter.
  - `MemoryTable`: Columns for `ID`, `Timestamp`, `Category`, `Content Snippet`, `Confidence`, `Importance`, `Privacy`, `Status`.
  - `PaginationControls`: Page size selector (10, 25, 50, 100), previous/next buttons, total count indicator.
- **Data Displayed:** Complete list of memory points, formatted timestamps, colored badges for privacy tiers (`PUBLIC`, `INTERNAL`, `SENSITIVE`, `HIGHLY_SENSITIVE`), and sync states (`COMMITTED`, `PENDING`).
- **User Actions:**
  - Click row -> Opens Memory Inspector in side drawer.
  - Filter by Category or Privacy Tier -> Re-queries local database.
  - Export filtered set -> Downloads local JSON snapshot.
- **Backend Requirements:**
  - `GET /api/memories?page=1&limit=25&category=...&privacy=...`
- **Loading States:** Shimmer rows in table body during pagination transitions.
- **Error States:** Empty-state illustration when filters match zero records; error modal on database read failures.
- **Offline Behavior:** 100% operational offline. All queries execute against local SQLite and Qdrant Edge in `<10ms`.
