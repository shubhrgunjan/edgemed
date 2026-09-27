"""Reproducible synthetic benchmark; no performance values are fabricated."""

import json
import platform
import resource
import secrets
import statistics
import tempfile
import time
from pathlib import Path

from edgemed.cli import VAULT, verify_vault
from edgemed.fixtures import NOTES
from edgemed.models import CreateMemory
from edgemed.retrieval import Retrieval
from edgemed.store import Store

verify_vault()
root = Path(__file__).resolve().parents[1]
queries = [
    ("high temperature and cough", 0),
    ("penicillin rash allergy", 1),
    ("blood pressure measurement", 2),
    ("private follow up", 3),
    ("dizzy after drinking little fluid", 4),
]
with tempfile.TemporaryDirectory(dir=VAULT, prefix="benchmark-") as temp:
    store = Store(Path(temp), secrets.token_hex(32))
    start = time.perf_counter()
    for i in range(1000):
        data = {**NOTES[i % len(NOTES)], "subject": f"SYN-{i + 1000:04d}"}
        store.create(CreateMemory(**data))
    ingest = time.perf_counter() - start
    retrieval = Retrieval(store, root / ".cache/models")
    start = time.perf_counter()
    while retrieval.drain():
        pass
    index = time.perf_counter() - start
    latencies = []
    hits = 0
    for i in range(30):
        query, expected = queries[i % len(queries)]
        t = time.perf_counter()
        result = retrieval.search(query, limit=5)
        latencies.append((time.perf_counter() - t) * 1000)
        hits += any(r["title"] == NOTES[expected]["title"] for r in result)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report = {
        "platform": platform.platform(),
        "records": 1000,
        "queries": 30,
        "unique_query_templates": 5,
        "evaluation_note": "Repeated synthetic categories; measures operation and template retrieval, not held-out clinical quality.",
        "durable_ingestion_seconds": round(ingest, 3),
        "indexing_seconds": round(index, 3),
        "search_p50_ms": round(statistics.median(latencies), 2),
        "search_p95_ms": round(sorted(latencies)[28], 2),
        "search_max_ms": round(max(latencies), 2),
        "template_hit_at_5": hits / 30,
        "process_peak_rss_mb": round(peak / (1024 * 1024 if platform.system() == "Darwin" else 1024), 1),
        "network_mode": "local model and Edge only",
        "model": "BAAI/bge-small-en-v1.5",
    }
    retrieval.close()
    store.close()
Path("docs/benchmark-results.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
