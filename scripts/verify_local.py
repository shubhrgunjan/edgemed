"""Exercise the running encrypted demo. Prints checks, never credentials or note bodies."""

import json
import os
import signal
import time
from pathlib import Path
from uuid import uuid4

import httpx

from edgemed.cli import config, RUNTIME, SERVICE, start, alive
from edgemed.fixtures import fixture_id
from edgemed.security import load_secret
from edgemed.sync import tls_context

checks = []


def passed(name):
    checks.append(name)
    print("PASS", name, flush=True)


def client(profile, port):
    c = httpx.Client(base_url=f"http://127.0.0.1:{port}", trust_env=False, timeout=15)
    r = c.post(
        "/api/login", json={"username": "operator", "password": load_secret(profile)["initial_password"]}
    )
    r.raise_for_status()
    c.headers["x-csrf-token"] = r.json()["csrf"]
    return c


def call(c, path, data=None):
    r = c.post(path, json=data)
    r.raise_for_status()
    return r.json()


def settle(a, b, mid, predicate, timeout=90):
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        call(a, "/api/sync")
        call(b, "/api/sync")
        ma, mb = a.get("/api/memories/" + mid).json(), b.get("/api/memories/" + mid).json()
        if predicate(ma, mb):
            return ma, mb
        time.sleep(0.3)
    raise AssertionError("Devices did not converge")


def main():
    if SERVICE == "org.lex.edgemed.local":
        raise RuntimeError("Rehearsal requires an isolated verification runtime; original data is protected")
    a, b = client("edge-a", config("edge-a")["port"]), client("edge-b", config("edge-b")["port"])
    for c in (a, b):
        call(c, "/api/demo/seed")
        call(c, "/api/sync/transport", {"enabled": True})
    mid = fixture_id("reference-hydration")
    settle(a, b, mid, lambda x, y: set(x["heads"]) == set(y["heads"]))
    passed("Live mTLS edge-to-central-to-edge synchronization")
    # Actually stop the isolated gateway; loopback device APIs keep serving.
    pid = json.loads((RUNTIME / "processes.json").read_text())["central"]
    os.kill(pid, signal.SIGTERM)
    for _ in range(100):
        if not alive(pid):
            break
        time.sleep(0.1)
    assert not alive(pid)
    saved = call(
        a, "/api/memories", {"title": "Offline rehearsal", "content": "Synthetic offline fever and cough"}
    )
    found = call(a, "/api/search", {"query": "offline fever cough"})
    assert any(r["id"] == saved["id"] for r in found["results"])
    passed("Actual gateway outage preserves local capture and hybrid search")
    base = a.get("/api/memories/" + mid).json()["heads"][0]
    call(a, "/api/memories/" + mid + "/reference-variant", {"parent": base, "variant": 1})
    call(b, "/api/memories/" + mid + "/reference-variant", {"parent": base, "variant": 2})
    assert any(r["state"] != "acknowledged" for r in a.get("/api/sync/status").json()["items"])
    start()
    ma, mb = settle(
        a, b, mid, lambda x, y: x["conflicting"] and y["conflicting"] and set(x["heads"]) == set(y["heads"])
    )
    passed("Concurrent offline edits survive reconnect on both devices")
    resolved = call(
        a, "/api/memories/" + mid + "/resolve", {"parents": ma["heads"], "chosen": ma["heads"][-1]}
    )
    settle(a, b, mid, lambda x, y: not x["conflicting"] and not y["conflicting"] and x["heads"] == y["heads"])
    passed("Explicit resolution converges without erasing historical revisions")
    canary = "PRIVATE_SYNTHETIC_CANARY_" + str(uuid4())
    private = call(
        a,
        "/api/memories",
        {"title": "Temporary verification record", "content": canary, "privacy": "HIGHLY_SENSITIVE"},
    )
    call(a, "/api/sync")
    assert canary not in json.dumps(a.get("/api/sync/status").json())
    assert b.get("/api/memories/" + private["id"]).status_code == 404
    passed("Highly sensitive record excluded from live queue and peer device")
    r = a.delete("/api/memories/" + private["id"])
    r.raise_for_status()
    assert a.get("/api/memories/" + private["id"]).status_code == 404
    passed("Deletion hides record immediately")
    cfg, secret = config("central"), load_secret("central")
    # Missing client certificate and untrusted server CA must fail at TLS, before application auth.
    for verify_arg in (True, tls_context(cfg, client=False)):
        try:
            with httpx.Client(verify=verify_arg, trust_env=False, timeout=4) as c:
                c.post(cfg["gateway"] + "/sync/pull", json={})
        except httpx.HTTPError:
            continue
        raise AssertionError("TLS admitted a client without its certificate or trusted server CA")
    passed("mTLS rejects missing client certificate and untrusted CA")
    edge = config("edge-a")
    with httpx.Client(verify=tls_context(edge), trust_env=False, timeout=10) as c:
        payload = {"device_id": "edge-a", "cursor": 0, "nonce": str(uuid4())}
        r = c.post(edge["gateway"] + "/sync/pull", json={**payload, "signature": "tampered"})
        assert r.status_code == 403
        passed("Gateway rejects invalid device signature")
    with httpx.Client(
        verify=tls_context(cfg, client=False),
        headers={"api-key": secret["qdrant_api_key"]},
        trust_env=False,
        timeout=10,
    ) as c:
        # Wait for the actual server vector projection, not just a queue receipt.
        for _ in range(30):
            r = c.post(
                cfg["qdrant"] + "/collections/lex_synthetic_references/points",
                json={"ids": resolved["heads"], "with_payload": True},
            )
            r.raise_for_status()
            if r.json()["result"]:
                break
            time.sleep(0.2)
        assert r.json()["result"]
        assert canary not in r.text
        passed("Accepted revision projected into real Qdrant Server 1.19.1")
    for _ in range(20):
        snapshot = a.post("/api/sync/reference-snapshot")
        if snapshot.status_code == 200:
            break
        time.sleep(0.5)
    snapshot.raise_for_status()
    assert snapshot.json()["points"] > 0
    passed("Signed full reference snapshot verified and activated")
    for c in (a, b):
        call(c, "/api/sync/transport", {"enabled": False})
        c.close()
    report = {"checks": checks, "passed": len(checks), "failed": 0, "timestamp": time.time()}
    Path("docs/local-integration-results.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
