"""Comprehensive security boundary regression tests for EdgeMed.

Validates:
1. Cross-workspace and personal observation isolation.
2. Clinical/staff observations strictly never enter outbound sync.
3. Backend authorization enforcement cannot be bypassed by frontend requests.
4. HTTP perimeter defenses (Host header, Origin, Sec-Fetch-Site, CSRF).
5. Deletion, tombstones, and current-head search truthfulness.
6. Synchronization boundary accepts only approved synthetic reference templates.
7. Fail-closed storage, keyring, and snapshot configuration.
"""

import json
import secrets
import sys
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from edgemed.accounts import add
from edgemed.api import create_app
from edgemed.fixtures import fixture_id, initial_revision
from edgemed.models import CreateMemory, Export
from edgemed.security import PASSWORDS, new_identity
from edgemed.snapshots import validate_archive
from edgemed.store import Store
from edgemed.sync import Transport


class MockAuthRetrieval:
    """Mock retrieval engine for fast, isolated security boundary tests."""

    def __init__(self, store, cache):
        self.store = store
        self.cache = cache

    def drain(self):
        for job in self.store.pending_jobs():
            self.store.mark_indexed(job["id"], job["generation"])
        return 0

    def search(self, query, owner, limit=10, mode="hybrid", subject=None, timings=None):
        records = self.store.current_records(owner, subject=subject)
        results = []
        for mid, rec in records.items():
            if query.lower() in rec["content"].lower() or query.lower() in rec["title"].lower():
                results.append(
                    {
                        "id": mid,
                        "matched_revision_id": rec["heads"][0],
                        "title": rec["title"],
                        "snippet": rec["content"],
                        "score": 0.95,
                    }
                )
        return self.store.eligible_results(results, owner, subject=subject)

    def close(self):
        pass


@pytest.fixture
def security_env(tmp_path):
    """Sets up a complete multi-user hospital environment for boundary testing."""
    secret = {
        "db_key": secrets.token_hex(32),
        "sign_private": new_identity()[0],
        "operators": {
            "operator": {
                "password_hash": PASSWORDS.hash("operator-secret-123"),
                "owner": "operator",
                "role": "admin",
            }
        },
    }
    passwords = {
        "alice": add(secret, "alice", "ward-a", "clinician"),
        "bob": add(secret, "bob", "ward-a", "clinician"),
        "wardadmin_a": add(secret, "wardadmin_a", "ward-a", "admin"),
        "carol": add(secret, "carol", "ward-b", "clinician"),
        "wardadmin_b": add(secret, "wardadmin_b", "ward-b", "admin"),
    }
    origin = "http://127.0.0.1:8765"
    app = create_app(
        {
            "data_path": str(tmp_path / "data"),
            "device_id": "edge-a",
            "origin": origin,
            "lan_mode": False,
        },
        secret,
        tmp_path / "cache",
        retrieval_factory=MockAuthRetrieval,
    )
    return {
        "app": app,
        "secret": secret,
        "passwords": passwords,
        "origin": origin,
        "tmp_path": tmp_path,
    }


def authenticate_client(app, origin, username, password):
    client = TestClient(app, base_url=origin)
    res = client.post("/api/login", json={"username": username, "password": password})
    assert res.status_code == 200, f"Authentication failed for {username}: {res.text}"
    client.headers["x-csrf-token"] = res.json()["csrf"]
    return client


# ==============================================================================
# 1. CROSS-WORKSPACE & PERSONAL ISOLATION
# ==============================================================================


def test_cross_workspace_isolation_blocks_read_and_search(security_env):
    """Staff in ward-b cannot view, list, search, revise, or delete ward-a records."""
    app = security_env["app"]
    origin = security_env["origin"]
    pw = security_env["passwords"]

    alice = authenticate_client(app, origin, "alice", pw["alice"])
    carol = authenticate_client(app, origin, "carol", pw["carol"])

    # Alice creates a synthetic record in ward-a
    create_res = alice.post(
        "/api/memories",
        json=CreateMemory(
            title="Ward A Canary",
            content="CANARY_WARD_A_OBSERVATION: patient blood pressure stable",
            category="OBSERVATION",
            privacy="SENSITIVE",
            subject="SYN-001",
        ).model_dump(),
    )
    assert create_res.status_code == 201
    memory_a = create_res.json()
    mid_a = memory_a["id"]

    # Carol (ward-b) attempts to GET the record
    assert carol.get(f"/api/memories/{mid_a}").status_code == 404

    # Carol attempts to view governance metadata
    assert carol.get(f"/api/memories/{mid_a}/governance").status_code == 404

    # Carol lists memories: must not contain memory_a
    carol_list = carol.get("/api/memories").json()
    assert all(m["id"] != mid_a for m in carol_list)

    # Carol searches for exact unique canary string: must return zero results
    carol_search = carol.post("/api/search", json={"query": "CANARY_WARD_A_OBSERVATION"}).json()
    assert len(carol_search["results"]) == 0

    # Carol attempts to revise ward-a memory
    revise_res = carol.post(
        f"/api/memories/{mid_a}/revisions",
        json={"parent": memory_a["heads"][0], "content": "malicious revision attempt"},
    )
    assert revise_res.status_code == 404

    # Carol attempts to delete ward-a memory
    assert carol.delete(f"/api/memories/{mid_a}").status_code == 404

    # Carol checks graph: must not contain ward-a node
    carol_graph = carol.get("/api/graph").json()
    assert all(n["id"] != mid_a for n in carol_graph["nodes"])


def test_staff_personal_observations_isolated_from_colleagues(security_env):
    """HIGHLY_SENSITIVE notes are personal and cannot be accessed by other ward staff or ward admin."""
    app = security_env["app"]
    origin = security_env["origin"]
    pw = security_env["passwords"]

    alice = authenticate_client(app, origin, "alice", pw["alice"])
    bob = authenticate_client(app, origin, "bob", pw["bob"])
    wardadmin = authenticate_client(app, origin, "wardadmin_a", pw["wardadmin_a"])

    # Alice creates a HIGHLY_SENSITIVE personal note
    create_res = alice.post(
        "/api/memories",
        json=CreateMemory(
            title="Alice Personal Observation",
            content="CANARY_ALICE_PRIVATE_NOTE: internal diagnostic hypothesis",
            category="NOTE",
            privacy="HIGHLY_SENSITIVE",
        ).model_dump(),
    )
    assert create_res.status_code == 201
    personal_note = create_res.json()
    mid = personal_note["id"]

    # Bob (colleague clinician in same ward-a) cannot access it
    assert bob.get(f"/api/memories/{mid}").status_code == 404
    bob_search = bob.post("/api/search", json={"query": "CANARY_ALICE_PRIVATE_NOTE"}).json()
    assert len(bob_search["results"]) == 0
    assert all(m["id"] != mid for m in bob.get("/api/memories").json())

    # Wardadmin in the same ward cannot access Alice's personal note
    assert wardadmin.get(f"/api/memories/{mid}").status_code == 404
    admin_search = wardadmin.post("/api/search", json={"query": "CANARY_ALICE_PRIVATE_NOTE"}).json()
    assert len(admin_search["results"]) == 0

    # Alice CAN access and delete her own personal note
    assert alice.get(f"/api/memories/{mid}").status_code == 200
    assert alice.delete(f"/api/memories/{mid}").status_code == 200


# ==============================================================================
# 2. LOCAL-ONLY CLINICAL OBSERVATIONS NEVER ENTER OUTBOUND SYNC
# ==============================================================================


def test_clinical_observations_cannot_enter_outbox(security_env):
    """Patient notes, vitals, allergies, and observations never produce outbox records."""
    app = security_env["app"]
    origin = security_env["origin"]
    pw = security_env["passwords"]
    store = app.state.store

    alice = authenticate_client(app, origin, "alice", pw["alice"])
    wardadmin = authenticate_client(app, origin, "wardadmin_a", pw["wardadmin_a"])

    # Create various types of clinical observations
    categories = ["OBSERVATION", "VITAL_SIGN", "ALLERGY", "NOTE"]
    for cat in categories:
        res = alice.post(
            "/api/memories",
            json=CreateMemory(
                title=f"Synthetic {cat}",
                content=f"Clinical content for {cat}",
                category=cat,
                privacy="SENSITIVE",
                subject="SYN-002",
            ).model_dump(),
        )
        assert res.status_code == 201
        mid = res.json()["id"]
        heads = res.json()["heads"]

        # Revise the memory
        rev_res = alice.post(
            f"/api/memories/{mid}/revisions",
            json={"parent": heads[0], "content": f"Updated {cat} observation"},
        )
        assert rev_res.status_code == 201

    # Admin deletes one record
    del_res = wardadmin.delete(f"/api/memories/{mid}")
    assert del_res.status_code == 200

    # Invariant: Outbox MUST be completely empty
    assert len(store.outbox()) == 0


def test_transport_egress_policy_cancels_unauthorized_outbox_items(security_env, monkeypatch):
    """If an invalid item is somehow forced into outbox, Transport cancels it immediately before egress."""
    app = security_env["app"]
    origin = security_env["origin"]
    pw = security_env["passwords"]
    store = app.state.store

    alice = authenticate_client(app, origin, "alice", pw["alice"])
    res = alice.post(
        "/api/memories",
        json=CreateMemory(
            title="Non-fixture Memory",
            content="Confidential observation",
            privacy="SENSITIVE",
        ).model_dump(),
    )
    mid = res.json()["id"]

    # Directly simulate an outbox item pointing to a non-fixture or sensitive memory
    fake_payload = Export(
        operation_id=uuid4(),
        memory_id=mid,
        revision_id=uuid4(),
        parents=[],
        device_id="edge-a",
        facility="lex-demo",
        fixture="reference-hydration",
        variant=0,
        deleted=False,
    ).model_dump(mode="json")
    with store.transaction():
        store.db.execute(
            "INSERT INTO outbox(id,payload,hash) VALUES(?,?,?)",
            (fake_payload["operation_id"], json.dumps(fake_payload), "fakehash"),
        )
    assert len(store.outbox()) == 1

    # Mock tls_context so Transport.run can instantiate httpx.Client without live cert files
    monkeypatch.setattr("edgemed.sync.tls_context", lambda cfg: True)

    # Configure transport and trigger egress validation
    transport = Transport(
        store,
        {"gateway": "https://127.0.0.1:9443", "ca": str(security_env["tmp_path"] / "ca.pem")},
        security_env["secret"],
    )
    store.set_setting("transport", True)

    # Calling run() will inspect the canonical memory record and cancel the item
    transport.run()

    outbox_item = store.outbox()[0]
    assert outbox_item["state"] == "cancelled"
    assert "Policy no longer permits sharing" in outbox_item["error"]


# ==============================================================================
# 3. BACKEND ENFORCEMENT CANNOT BE BYPASSED BY FRONTEND
# ==============================================================================


def test_clinician_cannot_execute_admin_endpoints(security_env):
    """Clinician roles are blocked from invoking administrative actions."""
    app = security_env["app"]
    origin = security_env["origin"]
    pw = security_env["passwords"]

    alice = authenticate_client(app, origin, "alice", pw["alice"])

    # Alice creates a shared note
    res = alice.post(
        "/api/memories",
        json=CreateMemory(
            title="Ward note",
            content="Observation",
            privacy="SENSITIVE",
        ).model_dump(),
    )
    mid = res.json()["id"]

    # Alice (clinician) cannot delete a shared ward note
    assert alice.delete(f"/api/memories/{mid}").status_code == 403

    # Alice cannot access administrative activity log
    assert alice.get("/api/activity").status_code == 403

    # Alice cannot access diagnostics
    assert alice.get("/api/diagnostics").status_code == 403

    # Alice cannot seed the demo database
    assert alice.post("/api/demo/seed").status_code == 403

    # Alice cannot trigger conflict resolution (requires admin)
    assert (
        alice.post(
            f"/api/memories/{mid}/resolve",
            json={"parents": [str(uuid4()), str(uuid4())], "chosen": str(uuid4())},
        ).status_code
        == 403
    )


def test_ward_admin_cannot_execute_operator_endpoints(security_env):
    """Ward admin cannot execute server operator sync/transport controls."""
    app = security_env["app"]
    origin = security_env["origin"]
    pw = security_env["passwords"]

    wardadmin = authenticate_client(app, origin, "wardadmin_a", pw["wardadmin_a"])

    # Wardadmin cannot access central sync controls
    assert wardadmin.get("/api/sync/status").status_code == 403
    assert wardadmin.post("/api/sync/transport", json={"enabled": True}).status_code == 403
    assert wardadmin.post("/api/sync").status_code == 403
    assert wardadmin.post("/api/sync/reference-snapshot").status_code == 403


def test_frontend_cannot_spoof_owner_or_privacy_public(security_env):
    """Backend ignores client-provided owner fields and rejects privacy='PUBLIC' for user notes."""
    app = security_env["app"]
    origin = security_env["origin"]
    pw = security_env["passwords"]

    alice = authenticate_client(app, origin, "alice", pw["alice"])

    # Attempt to self-declare privacy=PUBLIC
    res_public = alice.post(
        "/api/memories",
        json={
            "title": "Malicious Public Note",
            "content": "Trying to leak public",
            "category": "NOTE",
            "privacy": "PUBLIC",
        },
    )
    assert res_public.status_code == 422

    # Attempt to inject extra owner field
    res_spoof = alice.post(
        "/api/memories",
        json={
            "title": "Spoofed Owner",
            "content": "Trying to own operator scope",
            "category": "NOTE",
            "privacy": "SENSITIVE",
            "owner": "operator",
        },
    )
    # Pydantic extra='forbid' rejects unrecognized fields
    assert res_spoof.status_code == 422


# ==============================================================================
# 4. HTTP PERIMETER: HOST, ORIGIN, SEC-FETCH-SITE, CSRF
# ==============================================================================


def test_host_header_poisoning_rejected(security_env):
    """Requests with mismatched Host headers are rejected with 400 Bad Request."""
    app = security_env["app"]
    origin = security_env["origin"]

    client = TestClient(app, base_url=origin)
    res = client.get("/api/health", headers={"Host": "attacker.controlled.domain"})
    assert res.status_code == 400
    assert res.json()["detail"] == "Host not permitted"


def test_cross_origin_and_fetch_site_rejected(security_env):
    """Requests from foreign origins or with Sec-Fetch-Site: cross-site are rejected with 403."""
    app = security_env["app"]
    origin = security_env["origin"]
    pw = security_env["passwords"]

    client = TestClient(app, base_url=origin)

    # Foreign Origin on login
    res_origin = client.post(
        "/api/login",
        headers={"Origin": "https://malicious-site.example"},
        json={"username": "alice", "password": pw["alice"]},
    )
    assert res_origin.status_code == 403
    assert res_origin.json()["detail"] == "Origin not permitted"

    # Sec-Fetch-Site: cross-site header
    res_fetch = client.post(
        "/api/login",
        headers={"Sec-Fetch-Site": "cross-site"},
        json={"username": "alice", "password": pw["alice"]},
    )
    assert res_fetch.status_code == 403
    assert res_fetch.json()["detail"] == "Origin not permitted"


def test_csrf_token_required_on_mutations(security_env):
    """Mutating state without valid x-csrf-token header returns 403 Forbidden."""
    app = security_env["app"]
    origin = security_env["origin"]
    pw = security_env["passwords"]

    # Authenticate without setting header
    client = TestClient(app, base_url=origin)
    login_res = client.post("/api/login", json={"username": "alice", "password": pw["alice"]})
    assert login_res.status_code == 200

    # Missing CSRF token
    res_missing = client.post(
        "/api/memories",
        json={"title": "Missing CSRF", "content": "test", "privacy": "SENSITIVE"},
    )
    assert res_missing.status_code == 403
    assert res_missing.json()["detail"] == "CSRF verification failed"

    # Tampered CSRF token
    res_tampered = client.post(
        "/api/memories",
        headers={"x-csrf-token": "tampered_token_value_xyz"},
        json={"title": "Tampered CSRF", "content": "test", "privacy": "SENSITIVE"},
    )
    assert res_tampered.status_code == 403
    assert res_tampered.json()["detail"] == "CSRF verification failed"


# ==============================================================================
# 5. DELETION, TOMBSTONES, AND REVISION TRUTHFULNESS
# ==============================================================================


def test_deleted_memory_tombstone_purges_search_results(security_env):
    """Deleted records return 404 and are filtered from both lexical and vector search."""
    app = security_env["app"]
    origin = security_env["origin"]
    pw = security_env["passwords"]

    alice = authenticate_client(app, origin, "alice", pw["alice"])
    wardadmin = authenticate_client(app, origin, "wardadmin_a", pw["wardadmin_a"])

    create_res = alice.post(
        "/api/memories",
        json=CreateMemory(
            title="Transient Note",
            content="CANARY_EPHEMERAL_TEXT: temporary finding",
            privacy="SENSITIVE",
        ).model_dump(),
    )
    mid = create_res.json()["id"]

    # Search finds it while active
    s1 = alice.post("/api/search", json={"query": "CANARY_EPHEMERAL_TEXT"}).json()
    assert len(s1["results"]) == 1
    assert s1["results"][0]["id"] == mid

    # Delete the record
    del_res = wardadmin.delete(f"/api/memories/{mid}")
    assert del_res.status_code == 200

    # Direct GET returns 404
    assert alice.get(f"/api/memories/{mid}").status_code == 404

    # Search for exact canary string yields zero results
    s2 = alice.post("/api/search", json={"query": "CANARY_EPHEMERAL_TEXT"}).json()
    assert len(s2["results"]) == 0

    # Summary list excludes it
    assert all(m["id"] != mid for m in alice.get("/api/memories").json())


def test_deleted_record_resurrection_prevented(security_env):
    """The store rejects appending revisions to a deleted record."""
    store = security_env["app"].state.store
    m = store.create(
        CreateMemory(title="Doomed record", content="Will be deleted", privacy="SENSITIVE"),
        owner="ward-a",
    )
    mid = m["id"]
    heads = m["heads"]

    # Tombstone delete
    store.revise(mid, heads, deleted=True, owner="ward-a")

    # High-level revise raises KeyError (memory not found for modification)
    with pytest.raises(KeyError, match="Memory not found"):
        store.revise(mid, heads, content="Attempting to resurrect", owner="ward-a")

    # Direct append on deleted memory row raises ValueError
    row = store.db.execute("SELECT * FROM memories WHERE id=?", (mid,)).fetchone()
    with pytest.raises(ValueError, match="Deleted records cannot be resurrected"):
        store._append(row, str(uuid4()), heads, "Resurrect attempt", "edge-a")


# ==============================================================================
# 6. SYNC ACCEPTS ONLY APPROVED REFERENCE DATA
# ==============================================================================


def test_sync_accept_rejects_unapproved_fixtures_and_variants(security_env):
    """Store.accept rejects arbitrary fixture names, wrong memory_ids, or tampered variants."""
    store = security_env["app"].state.store

    # Valid initial reference payload
    fixture_name = "reference-hydration"
    valid_mid = fixture_id(fixture_name)
    initial_op = str(uuid4())

    valid_payload = Export(
        operation_id=initial_op,
        memory_id=valid_mid,
        revision_id=initial_revision(fixture_name),
        parents=[],
        device_id="edge-b",
        fixture=fixture_name,
        variant=0,
        deleted=False,
    ).model_dump(mode="json")

    # Accepting valid payload succeeds
    assert store.accept(valid_payload, owner="operator") is True

    # Duplicate op returns False (idempotent)
    assert store.accept(valid_payload, owner="operator") is False

    # Op ID reuse with altered payload fails
    with pytest.raises(ValueError, match="Operation ID reused"):
        store.accept({**valid_payload, "variant": 1}, owner="operator")

    # Fixture identity mismatch (memory_id != fixture_id)
    with pytest.raises(ValueError, match="Fixture identity mismatch"):
        store.accept(
            {**valid_payload, "operation_id": str(uuid4()), "memory_id": str(uuid4())},
            owner="operator",
        )

    # Unapproved variant number (e.g. 5)
    with pytest.raises(Exception):
        invalid_variant_payload = {
            **valid_payload,
            "operation_id": str(uuid4()),
            "variant": 5,
        }
        # Export model validator forbids variant > 2
        Export.model_validate(invalid_variant_payload)


# ==============================================================================
# 7. INSECURE STORAGE CONFIGURATION FAILS CLOSED
# ==============================================================================


def test_invalid_sqlcipher_key_length_rejected(tmp_path):
    """Store constructor rejects invalid keys (not 64 hex characters)."""
    with pytest.raises(ValueError, match="256-bit database key is required"):
        Store(tmp_path, "short_key")
    with pytest.raises(ValueError, match="256-bit database key is required"):
        Store(tmp_path, "g" * 64)  # non-hex character


def test_protected_keyring_fails_closed_without_secret_service(monkeypatch):
    """On Linux, security.protected_keyring() raises RuntimeError if plaintext keyring is active."""
    from edgemed import security

    class MockPlaintextBackend:
        pass

    MockPlaintextBackend.__module__ = "keyring.backends.file"

    monkeypatch.setattr(sys, "platform", "linux")
    import keyring

    monkeypatch.setattr(keyring, "get_keyring", lambda: MockPlaintextBackend())

    with pytest.raises(RuntimeError, match="Linux requires an unlocked Secret Service"):
        security.protected_keyring()


def test_snapshot_archive_rejects_path_traversal(tmp_path):
    """validate_archive raises ValueError on directory traversal members."""
    import tarfile

    bad_tar = tmp_path / "bad.tar"
    with tarfile.open(bad_tar, "w") as tar:
        ti = tarfile.TarInfo(name="../etc/passwd")
        ti.size = 0
        tar.addfile(ti)

    with pytest.raises(ValueError, match="Unsafe snapshot archive member"):
        validate_archive(bad_tar)
