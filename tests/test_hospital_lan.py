"""Real retrieval and HTTP checks for LAN staff isolation and TLS configuration."""

import json
import secrets
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from edgemed.accounts import add, disable
from edgemed.api import create_app
from edgemed.lan import configure, load, private_lan_ip
from edgemed.models import CreateMemory
from edgemed.security import PASSWORDS


def test_lan_certificate_is_explicit_private_and_bound_to_one_ip(tmp_path):
    with pytest.raises(ValueError):
        private_lan_ip("8.8.8.8")
    with pytest.raises(ValueError):
        private_lan_ip("127.0.0.1")
    data = configure(tmp_path, "192.168.40.10", 8765)
    assert data["origin"] == "https://192.168.40.10:8765"
    assert len(data["ca_fingerprint_sha256"]) == 64
    assert load(tmp_path, 8765)["bind"] == "192.168.40.10"
    assert (tmp_path / "lan-server.key").stat().st_mode & 0o077 == 0
    settings = json.loads((tmp_path / "lan.json").read_text())
    settings["ip"] = "192.168.40.11"
    (tmp_path / "lan.json").write_text(json.dumps(settings))
    with pytest.raises(RuntimeError, match="does not cover"):
        load(tmp_path, 8765)


def test_staff_accounts_and_real_retrieval_are_scoped(tmp_path):
    secret = {
        "db_key": secrets.token_hex(32),
        "operators": {
            "operator": {
                "password_hash": PASSWORDS.hash("admin-secret"),
                "owner": "operator",
                "role": "admin",
            }
        },
    }
    passwords = {
        "alice": add(secret, "alice", "ward-a"),
        "bob": add(secret, "bob", "ward-a"),
        "carol": add(secret, "carol", "ward-b"),
        "wardadmin": add(secret, "wardadmin", "ward-a", "admin"),
    }
    with pytest.raises(ValueError):
        add(secret, "wardevil", "operator")
    app = create_app(
        {
            "data_path": str(tmp_path / "data"),
            "device_id": "edge-a",
            "origin": "https://192.168.40.10:8765",
            "lan_mode": True,
        },
        secret,
        Path(__file__).resolve().parents[1] / ".cache/models",
    )

    def sign_in(client, username):
        response = client.post("/api/login", json={"username": username, "password": passwords[username]})
        assert response.status_code == 200
        assert "secure" in response.headers["set-cookie"].lower()
        client.headers["x-csrf-token"] = response.json()["csrf"]
        return client

    # Clients have distinct cookie jars; the same backend/shard serves all four sessions.
    with TestClient(app, base_url="https://192.168.40.10:8765") as alice:
        bob = TestClient(app, base_url="https://192.168.40.10:8765")
        carol = TestClient(app, base_url="https://192.168.40.10:8765")
        admin = TestClient(app, base_url="https://192.168.40.10:8765")
        sign_in(alice, "alice")
        sign_in(bob, "bob")
        sign_in(carol, "carol")
        sign_in(admin, "wardadmin")
        shared = alice.post(
            "/api/memories",
            json=CreateMemory(
                title="Shared handoff", content="synthetic ward handoff canary", privacy="SENSITIVE"
            ).model_dump(),
        ).json()
        personal = alice.post(
            "/api/memories",
            json=CreateMemory(
                title="Personal note", content="private-only canary", privacy="HIGHLY_SENSITIVE"
            ).model_dump(),
        ).json()
        while app.state.retrieval.drain():
            pass
        assert alice.get("/api/status").json()["total"] == 2
        assert bob.get("/api/status").json()["total"] == 1
        assert carol.get("/api/status").json()["total"] == 0
        other_ward = carol.post(
            "/api/memories",
            json=CreateMemory(title="Other ward", content="separate synthetic canary").model_dump(),
        ).json()
        assert all(event["memory_id"] != other_ward["id"] for event in admin.get("/api/activity").json())
        assert {m["id"] for m in bob.get("/api/memories").json()} == {shared["id"]}
        assert bob.get("/api/memories/" + personal["id"]).status_code == 404
        assert carol.get("/api/memories/" + shared["id"]).status_code == 404
        assert bob.get("/api/memories/" + personal["id"] + "/governance").status_code == 404
        assert personal["id"] not in {
            r["id"] for r in bob.post("/api/search", json={"query": "private-only canary"}).json()["results"]
        }
        assert shared["id"] not in {
            r["id"]
            for r in carol.post("/api/search", json={"query": "synthetic ward handoff canary"}).json()[
                "results"
            ]
        }
        assert {
            r["id"]
            for r in alice.post("/api/search", json={"query": "private-only canary"}).json()["results"]
        } >= {personal["id"]}
        assert (
            bob.post(
                "/api/memories/" + personal["id"] + "/revisions",
                json={"parent": personal["heads"][0], "content": "attack"},
            ).status_code
            == 404
        )
        assert bob.delete("/api/memories/" + shared["id"]).status_code == 403
        assert alice.delete("/api/memories/" + personal["id"]).status_code == 200
        assert admin.delete("/api/memories/" + shared["id"]).status_code == 200
        assert bob.get("/api/sync/status").status_code == 403
        assert admin.get("/api/sync/status").status_code == 403
        assert bob.post("/api/demo/seed").status_code == 403
        assert alice.get("/api/health", headers={"host": "attacker.example"}).status_code == 400
        assert (
            alice.post(
                "/api/memories",
                json={"title": "cross-site", "content": "x"},
                headers={"Origin": "https://evil.example"},
            ).status_code
            == 403
        )
        disable(secret, "bob")
        later = TestClient(app, base_url="https://192.168.40.10:8765")
        assert (
            later.post("/api/login", json={"username": "bob", "password": passwords["bob"]}).status_code
            == 401
        )
