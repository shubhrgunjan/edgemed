"""Authenticated real-loopback request measurements; outputs timing only."""

import json
import statistics
import time
from pathlib import Path

import httpx

from edgemed.cli import config
from edgemed.security import load_secret
from profile_search import summary


def main():
    cfg = config("edge-a")
    with httpx.Client(base_url=cfg["origin"], timeout=10, trust_env=False) as client:
        response = client.post(
            "/api/login", json={"username": "operator", "password": load_secret("edge-a")["initial_password"]}
        )
        response.raise_for_status()
        client.headers["x-csrf-token"] = response.json()["csrf"]
        times = []
        for i in range(220):
            start = time.perf_counter()
            response = client.post("/api/search", json={"query": f"fever cough synthetic case {i % 200}"})
            response.raise_for_status()
            if i >= 20:
                times.append((time.perf_counter() - start) * 1000)
        diagnostics = client.get("/api/diagnostics")
        diagnostics.raise_for_status()
        data = diagnostics.json()
        report = {
            "transport": "real authenticated HTTP loopback",
            "workload": "isolated demo records, not 1k corpus",
            "latency": summary(times),
            "stage_p50_ms": {
                k: statistics.median(s.get(k, 0) for s in data["searches"][-200:])
                for k in data["searches"][-1]
            },
            "server_request_p50_ms": statistics.median(s["total_ms"] for s in data["requests"][-200:]),
        }
        client.post("/api/logout").raise_for_status()
    Path("docs/http-profile.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
