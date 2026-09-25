# Screen Specification: Semantic Search & Retrieval HUD

- **Document Version:** 1.0.0
- **Status:** Complete / Design Specification
- **Date:** 2026-09-26

---

## 1. Purpose
The **Semantic Search** view allows clinicians to perform natural-language queries over all clinical knowledge, triage observations, and medical guidelines, displaying transparent score attribution and explainability chips.

---

## 2. Screen Specifications

- **Layout:** Centered search input box with suggestion chips, filter toggle bar, followed by ranked search result cards with interactive score breakdown tabs.
- **Components:**
  - `SearchInputBar`: Natural-language search box with hotkey support (`/`), clear button, and search mode indicator (`EDGE`, `CLOUD`, `HYBRID`).
  - `SuggestionChips`: Quick test queries (e.g., *"acute bronchospasm"*, *"penicillin contraindications"*, *"hypotension with bradycardia"*).
  - `ResultCardList`: Ranked cards displaying match score, excerpt with keyword highlighting, category tag, patient ID, and freshness badge.
  - `ScoreAttributionDrawer`: Expandable panel displaying dense cosine similarity, sparse BM25 score, RRF rank, and graph ontology boost.
- **Data Displayed:** Ranked list of retrieved memories, composite score, dense vs. sparse breakdown, matched graph entities, and elapsed latency in milliseconds.
- **User Actions:**
  - Type query & hit Enter -> Executes hybrid search in `<5ms`.
  - Click result card -> Opens Memory Inspector.
  - Click "Explain Score" -> Expands attribution drawer showing RRF calculations.
- **Backend Requirements:**
  - `POST /api/search` with payload `{"query": "...", "limit": 10, "mode": "AUTO"}`.
- **Loading States:** Real-time millisecond stopwatch counter active while search is processing.
- **Error States:** Informative notice if no semantic matches exceed the minimum confidence threshold (`0.40`).
- **Offline Behavior:** 100% operational offline. Displays `"EXECUTION TARGET: LOCAL IN-PROCESS (0ms network)"` banner.
