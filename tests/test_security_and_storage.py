import json
import secrets
import sqlite3
import threading
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from edgemed.api import create_app
from edgemed.gateway import create_gateway
from edgemed.models import CreateMemory, Export
from edgemed.security import PASSWORDS, new_identity, sign, verify
from edgemed.store import Store


@pytest.fixture
def store(tmp_path):
    s = Store(tmp_path, secrets.token_hex(32))
    yield s
    s.close()


def note(**kwargs):
    return CreateMemory(
        title="Private synthetic note", content="PRIVATE_CANARY_8392 fever and cough", **kwargs
    )


def test_encryption_and_wrong_key(tmp_path):
    key = secrets.token_hex(32)
    s = Store(tmp_path, key)
    s.create(note())
    s.close()
    assert not (tmp_path / "memory.db").read_bytes().startswith(b"SQLite format")
    assert b"PRIVATE_CANARY_8392" not in (tmp_path / "memory.db").read_bytes()
    with pytest.raises(Exception):
        sqlite3.connect(tmp_path / "memory.db").execute("select * from memories").fetchall()
    with pytest.raises(Exception):
        Store(tmp_path, secrets.token_hex(32))
    reopened = Store(tmp_path, key)
    assert reopened.list()[0]["content"].startswith("PRIVATE_CANARY")
    reopened.close()


def test_canonical_commit_survives_index_failure(store):
    m = store.create(note())
    assert store.get(m["id"])["content"] == note().content
    assert len(store.pending_jobs()) == 1
    assert m["index_state"] == "pending"
    assert store.outbox() == []


def test_private_and_highly_sensitive_never_queue(store):
    for privacy in ["SENSITIVE", "HIGHLY_SENSITIVE"]:
        m = store.create(note(privacy=privacy))
        store.revise(m["id"], m["heads"], "Private changed content")
    assert store.outbox() == []


def test_public_cannot_be_self_declared():
    with pytest.raises(ValueError):
        note(privacy="PUBLIC")
    with pytest.raises(ValueError):
        CreateMemory(title="x", content="y", owner="victim")


def test_scope_isolation(store):
    m = store.create(note(), owner="a")
    with pytest.raises(KeyError):
        store.get(m["id"], "b")
    with pytest.raises(KeyError):
        store.revise(m["id"], m["heads"], "attack", owner="b")
    assert store.list("b") == []
    assert store.graph("b") == {"nodes": [], "edges": []}


def test_concurrent_edits_preserved_and_resolved(store):
    m = store.create(note())
    a = store.revise(m["id"], m["heads"], "Branch A")
    b = store.revise(m["id"], m["heads"], "Branch B")
    assert b["conflicting"] and len(b["heads"]) == 2
    assert {r["content"] for r in b["revisions"]} == {note().content, "Branch A", "Branch B"}
    with pytest.raises(ValueError):
        store.resolve(m["id"], a["heads"], a["heads"][0])
    resolved = store.resolve(m["id"], b["heads"], a["heads"][0])
    assert not resolved["conflicting"] and resolved["content"] == "Branch A"
    assert len(resolved["revisions"]) == 4


def test_tombstone_blocks_resurrection_and_purges_jobs(store):
    m = store.create(note())
    store.mark_indexed(m["heads"][0])
    store.revise(m["id"], m["heads"], deleted=True)
    with pytest.raises(KeyError):
        store.get(m["id"])
    assert len(store.pending_jobs()) == 2
    assert store.list() == []


def test_audit_tampering_detected(store):
    store.create(note())
    store.verify_audit()
    store.db.execute("UPDATE events SET payload='{}' WHERE seq=1")
    with pytest.raises(RuntimeError, match="Audit"):
        store.verify_audit()


def test_logs_exclude_private_text(store):
    store.create(note())
    assert "PRIVATE_CANARY" not in json.dumps(store.activity())


def test_transaction_rolls_back_all_intent(store):
    m = store.create(note())
    with pytest.raises(ValueError):
        store.revise(m["id"], [str(uuid4())], "invalid ancestry")
    assert len(store.get(m["id"])["revisions"]) == 1
    assert len(store.pending_jobs()) == 1


def test_export_rejects_extra_fields(store):
    store.seed_reference("reference-hydration")
    p = json.loads(store.outbox()[0]["payload"])
    for field in ("content", "embedding", "patient_id", "query"):
        with pytest.raises(ValueError):
            Export.model_validate({**p, field: "PRIVATE_CANARY"})
    assert set(p) == {
        "schema_version",
        "policy_version",
        "operation_id",
        "memory_id",
        "revision_id",
        "parents",
        "device_id",
        "facility",
        "fixture",
        "variant",
        "deleted",
    }


def test_idempotency_and_payload_reuse(store, tmp_path):
    store.seed_reference("reference-hydration")
    p = json.loads(store.outbox()[0]["payload"])
    receiver = Store(tmp_path / "receiver", secrets.token_hex(32), "edge-b")
    assert receiver.accept(p)
    assert not receiver.accept(p)
    with pytest.raises(ValueError):
        receiver.accept({**p, "variant": 2})
    assert len(receiver.list()[0]["revisions"]) == 1
    receiver.close()


def test_two_device_conflict_and_delete_replay(store, tmp_path):
    b = Store(tmp_path / "device-b", secrets.token_hex(32), "edge-b")
    m = store.seed_reference("reference-hydration")
    initial = json.loads(store.outbox()[0]["payload"])
    b.accept(initial)
    store.revise(m["id"], m["heads"], variant=1)
    b.revise(m["id"], m["heads"], variant=2)
    pa = json.loads(store.outbox()[-1]["payload"])
    pb = json.loads(b.outbox()[-1]["payload"])
    store.accept(pb)
    b.accept(pa)
    assert set(store.get(m["id"])["heads"]) == set(b.get(m["id"])["heads"])
    assert b.get(m["id"])["conflicting"]
    store.revise(m["id"], store.get(m["id"])["heads"], variant=0, deleted=True)
    b.accept(json.loads(store.outbox()[-1]["payload"]))
    b.accept({**initial, "operation_id": str(uuid4())})
    assert b.list() == []
    b.close()


class AuthOnlyRetrieval:
    """Unit-test isolation only; actual Edge/ONNX covered in the integration suite."""

    def __init__(self, store, cache):
        self.lock = threading.RLock()

    def drain(self):
        return 0

    def close(self):
        pass


@pytest.fixture
def api(tmp_path):
    secret = {
        "db_key": secrets.token_hex(32),
        "operators": {
            "operator": {
                "password_hash": PASSWORDS.hash("correct-local-password"),
                "owner": "operator",
                "role": "admin",
            }
        },
    }
    app = create_app(
        {"data_path": str(tmp_path), "device_id": "edge-a"},
        secret,
        tmp_path,
        retrieval_factory=AuthOnlyRetrieval,
    )
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        yield client, app


def login(client):
    r = client.post("/api/login", json={"username": "operator", "password": "correct-local-password"})
    assert r.status_code == 200
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie
    client.headers["x-csrf-token"] = r.json()["csrf"]


def test_api_auth_csrf_host_origin_and_logout(api):
    client, _ = api
    assert client.get("/api/memories").status_code == 401
    assert client.get("/api/health", headers={"Host": "attacker.example"}).status_code == 400
    assert (
        client.post(
            "/api/login",
            headers={"Origin": "https://evil.example"},
            json={"username": "operator", "password": "correct-local-password"},
        ).status_code
        == 403
    )
    login(client)
    assert (
        client.post("/api/memories", json=note().model_dump(), headers={"x-csrf-token": "wrong"}).status_code
        == 403
    )
    m = client.post("/api/memories", json=note().model_dump())
    assert m.status_code == 201
    assert client.get("/api/memories").headers["cache-control"] == "no-store"
    assert "frame-ancestors" in client.get("/api/memories").headers["content-security-policy"]
    assert client.post("/api/logout").status_code == 200
    assert client.get("/api/memories").status_code == 401


def test_api_limits_unknown_fields_and_safe_validation(api):
    client, _ = api
    login(client)
    assert client.post("/api/memories", json={**note().model_dump(), "privacy": "PUBLIC"}).status_code == 422
    assert client.post("/api/memories", content=b"x" * 40000).status_code == 413
    response = client.post("/api/memories", json={**note().model_dump(), "extra": "PRIVATE_CANARY"})
    assert response.status_code == 422
    assert "PRIVATE_CANARY" not in response.text
    assert client.get("/api/memories?limit=99999").status_code == 422


def test_login_rate_limit(api):
    client, _ = api
    for _ in range(8):
        assert (
            client.post("/api/login", json={"username": "operator", "password": "wrong"}).status_code == 401
        )
    assert client.post("/api/login", json={"username": "operator", "password": "wrong"}).status_code == 429


def test_api_cross_scope_and_no_forced_private_sync(api):
    client, app = api
    hidden = app.state.store.create(note(), "other-operator")
    login(client)
    assert client.get("/api/memories/" + hidden["id"]).status_code == 404
    assert client.get("/api/status").json()["total"] == 0
    assert client.get("/api/graph").json()["nodes"] == []
    m = client.post("/api/memories", json=note().model_dump()).json()
    assert (
        client.post(
            "/api/memories/" + m["id"] + "/reference-variant", json={"parent": m["heads"][0], "variant": 1}
        ).status_code
        == 409
    )
    assert app.state.store.outbox() == []


def test_signatures():
    private, public = new_identity()
    signature = sign({"value": 1}, private)
    verify({"value": 1}, signature, public)
    with pytest.raises(ValueError):
        verify({"value": 2}, signature, public)


def test_gateway_auth_atomic_receipt_and_wrong_scope(tmp_path):
    private, public = new_identity()
    central_private, _ = new_identity()
    cfg = {"data_path": tmp_path / "central", "devices": {"edge-a": {"public": public, "revoked": False}}}
    app = create_gateway(cfg, {"db_key": secrets.token_hex(32), "sign_private": central_private}, tmp_path)
    sender = Store(tmp_path / "sender", secrets.token_hex(32))
    sender.seed_reference("reference-hydration")
    p = json.loads(sender.outbox()[0]["payload"])
    client = TestClient(app)
    assert client.post("/sync/push", json={"payload": p, "signature": "bad"}).status_code == 403
    good = {"payload": p, "signature": sign(p, private)}
    assert client.post("/sync/push", json=good).json()["payload"]["accepted"]
    assert client.post("/sync/push", json=good).json()["payload"]["duplicate"]
    assert app.state.store.db.execute("SELECT count(*) FROM changes").fetchone()[0] == 1
    changed = {**p, "facility": "another-facility"}
    assert (
        client.post("/sync/push", json={"payload": changed, "signature": sign(changed, private)}).status_code
        == 422
    )
    cfg["devices"]["edge-a"]["revoked"] = True
    assert client.post("/sync/push", json=good).status_code == 403
    sender.close()
    app.state.store.close()
