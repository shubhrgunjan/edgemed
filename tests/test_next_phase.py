import asyncio
import json
import secrets
import threading
from uuid import uuid4

import numpy as np
from fastapi.testclient import TestClient

from edgemed.models import CreateMemory
from edgemed.retrieval import Retrieval
from edgemed.store import Store
from edgemed.workers import finish, repeat
from test_security_and_storage import api as api, login


class Embedder:
    def __init__(self, callback=None):
        self.callback = callback

    def embed(self, texts):
        for _ in texts:
            if self.callback:
                callback, self.callback = self.callback, None
                callback()
            yield np.array([1.0] + [0.0] * 383)

    query_embed = embed


def make_store(path):
    return Store(path, secrets.token_hex(32))


def test_delete_during_embedding_cannot_acknowledge_purge(tmp_path):
    store = make_store(tmp_path)
    m = store.create(CreateMemory(title="Synthetic", content="fever cough"))
    model = Embedder(lambda: store.revise(m["id"], m["heads"], deleted=True))
    retrieval = Retrieval(store, tmp_path, embedder=model)
    retrieval.drain()
    assert len(store.pending_jobs()) == 2
    while retrieval.drain():
        pass
    assert retrieval.search("fever") == []
    assert retrieval.shard.retrieve(m["heads"], with_payload=True, with_vector=False) == []
    retrieval.close()
    store.close()


def test_central_stale_completion_keeps_delete_pending(tmp_path):
    from edgemed.sync import CentralProjector

    store = make_store(tmp_path)
    m = store.seed_reference("reference-hydration")

    class Client:
        def upsert(self, *args, **kwargs):
            store.revise(m["id"], m["heads"], variant=0, deleted=True)

    projector = CentralProjector.__new__(CentralProjector)
    projector.store, projector.model = store, Embedder()
    projector.client, projector.collection = Client(), "test"
    projector.drain()
    assert len(store.pending_jobs()) == 2
    store.close()


def test_current_head_subject_filter_and_cache_invalidation(tmp_path):
    store = make_store(tmp_path)
    for i in range(110):
        store.create(CreateMemory(title=f"Other {i}", content="fever cough", subject="SYN-002"))
    target = store.create(CreateMemory(title="Target", content="fever cough", subject="SYN-001"))
    hidden = store.create(CreateMemory(title="Hidden", content="fever cough"), owner="other")
    retrieval = Retrieval(store, tmp_path, embedder=Embedder())
    while retrieval.drain():
        pass
    found = retrieval.search("fever", subject="SYN-001")
    assert [r["id"] for r in found] == [target["id"]]
    assert "revisions" not in found[0]
    updated = store.revise(target["id"], target["heads"], "new synthetic follow up")
    retrieval.drain()
    result = retrieval.search("new follow", subject="SYN-001")[0]
    assert result["matched_revision_id"] == updated["heads"][0]
    assert "new synthetic" in result["content"]
    assert all(r["id"] != hidden["id"] for r in retrieval.search("fever"))
    store.revise(target["id"], updated["heads"], deleted=True)
    assert retrieval.search("fever", subject="SYN-001") == []
    retrieval.close()
    store.close()


def test_current_records_has_no_ten_thousand_cap(tmp_path):
    store = make_store(tmp_path)
    with store.transaction():
        for i in range(10001):
            mid, rid = str(uuid4()), str(uuid4())
            store.db.execute(
                "INSERT INTO memories VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (
                    mid,
                    "operator",
                    f"N{i}",
                    "SYN-001",
                    "NOTE",
                    "SENSITIVE",
                    0.5,
                    None,
                    json.dumps([rid]),
                    0,
                    i,
                ),
            )
            store.db.execute(
                "INSERT INTO revisions VALUES(?,?,?,?,?,?,?,?)",
                (rid, mid, "[]", "synthetic", "edge-a", 0, 0, i),
            )
            store.db.execute("INSERT INTO jobs(revision_id) VALUES(?)", (rid,))
    assert len(store.current_records()) == 10001
    assert store.stats("operator")["total"] == 10001
    store.close()


def test_schema_one_migrates_and_stale_job_ack_fails(tmp_path):
    key = secrets.token_hex(32)
    store = Store(tmp_path, key)
    store.set_setting("schema", 1)
    store.db.execute("ALTER TABLE jobs DROP COLUMN generation")
    store.close()
    store = Store(tmp_path, key)
    m = store.create(CreateMemory(title="Synthetic", content="note"))
    job = store.pending_jobs()[0]
    store.revise(m["id"], m["heads"], deleted=True)
    assert not store.mark_indexed(job["id"], job["generation"])
    assert store.get_setting("schema") == 2
    store.close()


def test_idle_expiry_not_extended_by_polling(api):
    client, app = api
    login(client)
    session = next(iter(app.state.sessions.values()))
    stamp = session["last_active"]
    assert client.get("/api/status").status_code == 200
    assert session["last_active"] == stamp
    session["last_active"] -= 301
    assert client.get("/api/session").status_code == 401
    assert app.state.sessions == {}


def test_foreground_activity_and_absolute_expiry(api):
    client, app = api
    login(client)
    session = next(iter(app.state.sessions.values()))
    session["last_active"] -= 200
    old = session["last_active"]
    assert client.post("/api/session/activity").status_code == 200
    assert session["last_active"] > old
    session["expires"] = 0
    assert client.post("/api/session/activity").status_code == 401


def test_gateway_body_limit_and_redacted_validation(tmp_path):
    from edgemed.gateway import create_gateway

    app = create_gateway({"data_path": tmp_path, "devices": {}}, {"db_key": secrets.token_hex(32)}, tmp_path)
    client = TestClient(app)
    response = client.post("/sync/pull", content=b"x" * 40000)
    assert response.status_code == 413
    response = client.post("/sync/pull", json={"CANARY_SECRET": "private"})
    assert response.status_code == 422 and "CANARY_SECRET" not in response.text
    app.state.store.close()


def test_shutdown_joins_running_thread_before_closure():
    entered, release = threading.Event(), threading.Event()

    def work():
        entered.set()
        release.wait(3)

    async def run():
        stop = asyncio.Event()
        task = asyncio.create_task(repeat(stop, work))
        await asyncio.to_thread(entered.wait, 2)
        shutdown = asyncio.create_task(finish(stop, [task]))
        await asyncio.sleep(0.02)
        assert not shutdown.done()
        release.set()
        await shutdown

    asyncio.run(run())


def test_final_filter_drops_stale_and_foreign_results(tmp_path):
    store = make_store(tmp_path)
    m = store.create(CreateMemory(title="Synthetic", content="old"))
    result = {"id": m["id"], "matched_revision_id": m["heads"][0]}
    assert store.eligible_results([result], "other") == []
    store.revise(m["id"], m["heads"], "new")
    assert store.eligible_results([result], "operator") == []
    store.close()


def test_statistics_and_conflict_page_are_authorized(api):
    client, app = api
    login(client)
    m = app.state.store.create(CreateMemory(title="Synthetic", content="one"))
    app.state.store.revise(m["id"], m["heads"], "two")
    app.state.store.revise(m["id"], m["heads"], "three")
    page = client.get("/api/memories?conflicts=true").json()
    assert len(page) == 1 and page[0]["conflicting"]
    assert "revisions" not in page[0]
    assert client.get("/api/status").json()["conflicts"] == 1


def test_snapshot_reload_failure_preserves_working_reference(tmp_path, monkeypatch):
    import qdrant_edge as q

    store = make_store(tmp_path)
    retrieval = Retrieval(store, tmp_path, embedder=Embedder())

    class Reference:
        closed = False

        def close(self):
            self.closed = True

    original = Reference()
    retrieval.reference = original
    store.set_setting("reference_snapshot", {"path": str(tmp_path / "corrupt")})

    def fail(*args):
        raise ValueError("corrupt shard")

    monkeypatch.setattr(q.EdgeShard, "load", fail)
    import pytest

    with pytest.raises(ValueError):
        retrieval.reload_reference()
    assert retrieval.reference is original and not original.closed
    retrieval.close()
    store.close()
