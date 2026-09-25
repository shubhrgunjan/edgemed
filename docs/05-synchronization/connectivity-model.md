# Connectivity Model Specification: Heartbeat, Probing, and Network State

- **Document Version:** 1.0.0
- **Status:** Complete
- **Date:** 2026-09-26

---

## 1. Network Probe and Health Architecture

The **Connectivity Manager** is an asynchronous background loop running within the edge application process that monitors network link quality without imposing heavy bandwidth overhead.

### Probing Strategy:
1. **Physical Interface State:** Listens to OS network socket state changes (carrier up/down).
2. **Lightweight Heartbeat (`/healthz`):** When the physical carrier is up, transmits a periodic HTTP `HEAD` or small `GET` request (<100 bytes) to the central Qdrant Server every 10 seconds.
3. **Latency and Jitter Tracking:** Measures Round-Trip Time (RTT) across the last 5 probes. If RTT $> 1500\text{ ms}$ or packet loss $> 30\%$, the manager marks the connection as `STATE_DEGRADED`.

---

## 2. Dynamic Operational Adaptation Table

| Monitored Link Condition | Inferred Network State | Search Router Action | Sync Worker Action |
| :--- | :--- | :--- | :--- |
| Carrier Down / No Route | `STATE_OFFLINE` | Strict `EDGE` in-process search | Halt all HTTP requests; accumulate queue |
| RTT > 1500ms or Loss > 30% | `STATE_DEGRADED` | Strict `EDGE` in-process search | Reduce batch size to 2; increase backoff |
| RTT < 300ms, Loss < 2% | `STATE_ONLINE` | Enable `HYBRID` broad queries | Drain sync queue (batch size: 10 points) |
