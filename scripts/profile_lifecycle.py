"""Cold-process-equivalent model reloads and search while indexing; synthetic only."""

import json
import secrets
import tempfile
import threading
import time
from pathlib import Path

from edgemed.cli import VAULT, verify_vault
from edgemed.fixtures import NOTES
from edgemed.models import CreateMemory
from edgemed.retrieval import Retrieval
from edgemed.store import Store
from profile_search import summary


def main():
    verify_vault()
    cache = Path(__file__).resolve().parents[1] / ".cache/models"
    with tempfile.TemporaryDirectory(dir=VAULT, prefix="lifecycle-") as root:
        key = secrets.token_hex(32)
        store = Store(Path(root), key)
        for note in NOTES:
            store.create(CreateMemory(**note))
        retrieval = Retrieval(store, cache)
        while retrieval.drain():
            pass
        retrieval.close()
        store.close()
        reloads, first_queries = [], []
        for _ in range(5):
            start = time.perf_counter()
            store = Store(Path(root), key)
            retrieval = Retrieval(store, cache)
            reloads.append((time.perf_counter() - start) * 1000)
            start = time.perf_counter()
            assert retrieval.search("fever and coughing")
            first_queries.append((time.perf_counter() - start) * 1000)
            retrieval.close()
            store.close()
        store = Store(Path(root), key)
        retrieval = Retrieval(store, cache)
        for i in range(40):
            store.create(CreateMemory(title=f"Background {i}", content="Synthetic cough and fever"))
        errors = []

        def index():
            try:
                while retrieval.drain():
                    time.sleep(0.01)
            except Exception as exc:
                errors.append(type(exc).__name__)

        thread = threading.Thread(target=index)
        thread.start()
        times = []
        while thread.is_alive():
            start = time.perf_counter()
            assert retrieval.search("fever and cough")
            times.append((time.perf_counter() - start) * 1000)
        thread.join()
        assert not errors and not store.pending_jobs()
        retrieval.close()
        store.close()
    report = {
        "restart_scope": "five store/model/shard reloads within one process; OS cache uncontrolled",
        "model_and_store_start_ms": reloads,
        "first_query_ms": first_queries,
        "search_during_indexing": summary(times),
    }
    Path("docs/lifecycle-profile.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
