# Edge Deployment Architecture

- **Document Version:** 1.0.0
- **Status:** Complete
- **Date:** 2026-09-26

---

## 1. Deployment Models

EdgeMed is engineered for two primary deployment topologies:
1. **Standalone Portable Edge Device:** A single laptop or ruggedized tablet carried by a triage team, running the entire stack (FastAPI backend + in-process Qdrant Edge + SQLite + React UI in kiosk mode).
2. **Field Clinic Hub:** A central local edge micro-server (e.g., mini-PC or rugged laptop) serving multiple clinician tablets over a local offline Wi-Fi access point, synchronizing upward to the hospital cloud via intermittent satellite or cellular uplink.

---

## 2. Process Supervision

On Linux edge devices, the backend process is managed via `systemd`:
```ini
[Unit]
Description=EdgeMed Clinical Memory Engine
After=network.target

[Service]
Type=simple
User=edgemed
WorkingDirectory=/opt/edgemed
ExecStart=/opt/edgemed/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```
