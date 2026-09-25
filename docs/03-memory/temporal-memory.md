# Temporal Memory Specification: Longitudinal Event Progression

- **Document Version:** 1.0.0
- **Status:** Complete / Technical Architecture
- **Date:** 2026-09-26
- **Lead System Designer:** Team LEX (Code Cubicle 6.0 — PS03)

---

## 1. Purpose and Clinical Motivation

Medical care is inherently chronological and causal. Clinical diagnoses are not static snapshots; they are hypotheses that evolve as treatments are administered and responses are observed:

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   OBSERVATION   │  ──►  │    FOLLOW-UP    │  ──►  │    TREATMENT    │  ──►  │     OUTCOME     │
│                 │       │                 │       │                 │       │                 │
│ Initial Triage: │       │ Confirmatory:   │       │ Intervention:   │       │ Evaluation:     │
│ Dyspnea & SpO2  │       │ Chest X-Ray     │       │ Nebulized       │       │ SpO2 Normalizes │
│ 88% on room air │       │ demonstrates    │       │ Albuterol + IV  │       │ to 97%; patient │
│                 │       │ hyperinflation  │       │ Corticosteroids │       │ stabilizes      │
└─────────────────┘       └─────────────────┘       └─────────────────┘       └─────────────────┘
         │                         │                         │                         │
         └─────────────────────────┼─────────────────────────┴─────────────────────────┘
                                   ▼
                       Longitudinal Care Timeline
```

A memory system that treats all observations as an unranked bag of vectors cannot determine whether a patient is improving, deteriorating, or experiencing a delayed drug reaction.

---

## 2. Event Evolution Data Model

Each temporal event is captured in an append-only journal in SQLite (`temporal_events` table) with causal linkages:

```
{
  "event_id": "evt_7f8a9b2c-3d4e",
  "patient_id": "patient_synthetic_104",
  "event_sequence": 3,
  "stage": "TREATMENT",
  "timestamp": "2026-09-26T14:30:00Z",
  "prior_event_id": "evt_1a2b3c4d-5e6f",
  "clinical_acuity_delta": -0.4,
  "description": "Administered 5mg Nebulized Albuterol",
  "vitals_snapshot": {
    "hr": 110,
    "spo2": 93,
    "bp": "125/80"
  },
  "linked_memory_ids": ["mem_001", "mem_002"]
}
```

---

## 3. Dynamic Temporal Decay Function

To ensure retrieval relevancy without evicting critical medical history, the system applies asymmetric category-aware temporal decay curves:

$$w_{\text{temporal}}(\Delta t) = \begin{cases}
1.0 & \text{if Category} \in \{\text{ALLERGY}, \text{CHRONIC\_CONDITION}\} \\
e^{-\lambda_{\text{acute}} \Delta t} & \text{if Category} \in \{\text{VITAL\_SIGN}, \text{ACUTE\_SYMPTOM}\} \\
e^{-\lambda_{\text{subacute}} \Delta t} & \text{if Category} \in \{\text{TREATMENT\_RESPONSE}, \text{LAB\_TEST}\}
\end{cases}$$

- **Zero Decay (Chronic / Allergies):** A severe penicillin anaphylaxis recorded 10 years ago retains a weight of $1.0$ permanently.
- **Fast Decay (Acute Vitals):** An SpO2 measurement from 6 hours ago decays rapidly as new vitals arrive, preventing old transient numbers from polluting current clinical decisions.
- **Moderate Decay (Lab Results):** Blood cultures and electrolyte panels decay over 24–48 hour half-lives until superseded by new lab draws.
