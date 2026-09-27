import secrets
import socket
import time
from pathlib import Path

import pytest

from edgemed.fixtures import NOTES
from edgemed.models import CreateMemory
from edgemed.retrieval import Retrieval
from edgemed.store import Store

CACHE = Path(__file__).resolve().parents[1] / ".cache/models"


@pytest.mark.integration
def test_real_edge_offline_retrieval_restart_and_delete(tmp_path, monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("Unexpected network access during offline operation")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    monkeypatch.setattr(socket, "create_connection", no_network)
    key = secrets.token_hex(32)
    store = Store(tmp_path, key)
    for data in NOTES:
        store.create(CreateMemory(**data))
    hidden = store.create(
        CreateMemory(title="Secret other operator", content="penicillin allergy hidden"), owner="other"
    )
    retrieval = Retrieval(store, CACHE)
    while retrieval.drain():
        pass
    start = time.perf_counter()
    found = retrieval.search("high temperature with coughing")
    assert found and found[0]["title"] == "Persistent cough and fever"
    assert (time.perf_counter() - start) < 5
    exact = retrieval.search("penicillin")
    assert exact[0]["title"] == "Penicillin allergy reported"
    assert all(m["id"] != hidden["id"] for m in exact)
    target = exact[0]
    retrieval.close()
    store.close()
    # A new store and a newly loaded real shard use the same encrypted canonical data.
    store = Store(tmp_path, key)
    retrieval = Retrieval(store, CACHE)
    assert retrieval.search("penicillin")[0]["id"] == target["id"]
    store.revise(target["id"], target["heads"], deleted=True)
    assert all(r["id"] != target["id"] for r in retrieval.search("penicillin"))
    while retrieval.drain():
        pass
    assert retrieval.shard.retrieve(target["heads"], with_payload=True, with_vector=False) == []
    retrieval.close()
    store.close()
