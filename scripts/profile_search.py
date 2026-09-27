"""Isolated synthetic search benchmark. Compare the same script against two source roots."""

import argparse
import json
import math
import os
import platform
import random
import resource
import secrets
import statistics
import tempfile
import time
from pathlib import Path

from edgemed.fixtures import NOTES
from edgemed.models import CreateMemory
from edgemed.retrieval import Retrieval
from edgemed.store import Store


def summary(values):
    a = sorted(values)
    return {
        "samples": len(a),
        "p50_ms": round(statistics.median(a), 3),
        "p95_ms": round(a[math.ceil(0.95 * len(a)) - 1], 3),
        "p99_ms": round(a[math.ceil(0.99 * len(a)) - 1], 3),
        "max_ms": round(max(a), 3),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=int, default=1000)
    parser.add_argument("--queries", type=int, default=1000)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True, help="Verified encrypted test directory")
    args = parser.parse_args()
    rng = random.Random(20260928)
    queries = [
        "high temperature and cough",
        "penicillin rash allergy",
        "blood pressure measurement",
        "private follow up",
        "dizzy after drinking little fluid",
    ]
    report = {
        "platform": platform.platform(),
        "records": args.records,
        "query_templates": 5,
        "unique_queries": 200,
        "application_query_cache": "disabled",
        "runs": [],
        "quality_note": "Synthetic template retrieval; not held-out clinical quality",
        "pid": os.getpid(),
    }
    with tempfile.TemporaryDirectory(dir=args.root, prefix="profile-") as temp:
        store = Store(Path(temp), secrets.token_hex(32))
        for i in range(args.records):
            record = store.create(CreateMemory(**{**NOTES[i % len(NOTES)], "subject": f"SYN-{i + 1000:04d}"}))
            if i % 10 == 0:
                store.revise(
                    record["id"], record["heads"], record["content"] + " Synthetic reviewed follow-up."
                )
        start = time.perf_counter()
        retrieval = Retrieval(store, args.cache)
        report["model_shard_load_seconds"] = round(time.perf_counter() - start, 3)
        start = time.perf_counter()
        while retrieval.drain():
            pass
        report["index_seconds"] = round(time.perf_counter() - start, 3)
        start = time.perf_counter()
        retrieval.search(queries[0])
        report["first_search_after_index_ms"] = round((time.perf_counter() - start) * 1000, 3)
        for i in range(20):
            retrieval.search(queries[i % 5])
        tracing = "timings" in __import__("inspect").signature(retrieval.search).parameters
        samples = []
        hits = 0
        for run in range(args.runs):
            times = []
            order = list(range(args.queries))
            rng.shuffle(order)
            for i in order:
                qi = i % 5
                query = queries[qi] + f" synthetic case {i % 200}"
                stages = {}
                start = time.perf_counter()
                result = retrieval.search(query, limit=5, **({"timings": stages} if tracing else {}))
                elapsed = (time.perf_counter() - start) * 1000
                times.append(elapsed)
                hits += any(r["title"] == NOTES[qi]["title"] for r in result)
                samples.append({"run": run, "query_id": i % 200, "total_ms": elapsed, "stages_ms": stages})
            report["runs"].append(summary(times))
        report["template_hit_at_5"] = hits / (args.runs * args.queries)
        report["stage_p50_ms"] = {
            k: round(statistics.median(s["stages_ms"].get(k, 0) for s in samples), 3)
            for k in samples[0]["stages_ms"]
        }
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        report["peak_rss_mib"] = round(peak / (1048576 if platform.system() == "Darwin" else 1024), 2)
        retrieval.close()
        store.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    args.output.with_suffix(".jsonl").write_text("".join(json.dumps(s) + "\n" for s in samples))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
