# Privacy Firewall Specification: Inspection, Redaction, and Local Pinning

- **Document Version:** 1.0.0
- **Status:** Complete / Authoritative Specification
- **Date:** 2026-09-26
- **Lead Security Architect:** Team LEX (Code Cubicle 6.0 — PS03)

---

## 1. Architectural Purpose and Pipeline

The **Privacy Firewall** acts as an impassable data boundary between the local edge storage engine and the outbound cloud synchronization queue. It prevents confidential patient data, local credentials, or identifiable narratives from leaking over the network.

```
       RAW LOCAL MEMORY
              │
              ▼
    SENSITIVITY ANALYSIS (Regex PHI Detectors + Clinical Category Rules)
              │
              ▼
        PRIVACY POLICY (Evaluation against Classification Tiers)
              │
              ▼
      REDACTION / BLOCKING (Transform Payload or Reject Sync)
              │
              ▼
   SYNCHRONIZATION DECISION (Permit to Queue or Pin Locally)
```

---

## 2. Privacy Classification Tiers and System Actions

| Privacy Level | Definition & Clinical Scope | System Action on Synchronization |
| :--- | :--- | :--- |
| **`PUBLIC`** | General medical protocols, published clinical guidelines, drug interaction reference tables, textbook diagnostic criteria. | **Transmit Unchanged:** Permitted to synchronize freely with central Qdrant Server; accessible across all edge devices. |
| **`INTERNAL`** | Operational hospital telemetry, facility equipment statuses, non-patient ward inventories, shift handoff metadata. | **Transmit to Encrypted Facility Partition:** Replicated only to authorized institutional shards. |
| **`SENSITIVE`** | Patient observations containing clinical measurements and findings (vitals, symptoms, lab values) but with direct identifiers scrubbed. | **Redact Identifiers & Transmit:** Automated scrubber removes patient names, room numbers, and specific dates of birth; assigns anonymous hash ID; transmits de-identified finding for global clinical learning. |
| **`HIGHLY_SENSITIVE`** | Free-text psychiatric notes, identifiable demographic narratives, raw genetic markers, stigmatizing diagnostic entries. | **HARD PIN TO LOCAL STORAGE (BLOCK):** Strictly forbidden from entering the sync queue. Remains 100% on the local physical edge device. Attempted sync generates an audit rejection event. |

---

## 3. The Local-Only Clinical Default Rule

> [!CRITICAL]
> **DEFAULT-TO-LOCAL MANDATE:**
> Every newly created synthetic patient observation defaults to **`SENSITIVE`** or **`HIGHLY_SENSITIVE`**.
> No clinical memory record will ever be replicated to the central Qdrant Server without explicitly passing the Privacy Firewall's de-identification and redaction filter.
