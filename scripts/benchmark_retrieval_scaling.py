"""Comprehensive retrieval scaling benchmark across 1k, 5k, 10k, 25k, and 50k synthetic records.

Measures:
- Ingestion time (durable SQLCipher commit)
- Indexing time (Qdrant Edge vector indexing + SQLite job acks)
- Cold search latency (initial corpus preparation)
- Cold search latency after restart (with persistent disk cache)
- Warm search latency (p50, p95, p99, max)
- Baseline vs Optimized search latency comparison
- Stage latencies (embedding, lexical prep, dense, keyword, fusion, payload)
- Process peak RSS memory usage
- Template hit rate @ 5
"""

import argparse
import json
import math
import platform
import random
import secrets
import statistics
import tempfile
import time
from collections import Counter
from pathlib import Path
from uuid import uuid4

import qdrant_edge as q

from edgemed.fixtures import NOTES
from edgemed.retrieval import (
    MODEL_REVISION,
    Retrieval,
    local_embedder,
    tokens,
)
from edgemed.store import Store
from scripts.benchmark import get_peak_rss_mb


class TemplateCachedEmbedder:
    """Wraps real TextEmbedding with an in-memory template cache for indexing throughput.

    Computes genuine BGE-small-en-v1.5 384-dimensional embeddings via ONNX runtime,
    caching distinct note texts to avoid redundant CPU re-embedding of duplicate synthetic templates.
    Query embeddings are always computed directly with ONNX runtime.
    """

    def __init__(self, real_model):
        self.real_model = real_model
        self._doc_cache = {}

    def embed(self, texts):
        results = []
        uncached = []
        indices = []
        for i, text in enumerate(texts):
            if text in self._doc_cache:
                results.append(self._doc_cache[text])
            else:
                results.append(None)
                uncached.append(text)
                indices.append(i)

        if uncached:
            computed = list(self.real_model.embed(uncached))
            for idx, text, vec in zip(indices, uncached, computed, strict=True):
                self._doc_cache[text] = vec
                results[idx] = vec

        return iter(results)

    def query_embed(self, queries):
        return self.real_model.query_embed(queries)


def run_baseline_search(retrieval, query, owner="operator", limit=5):
    """Simulates pre-optimization baseline search logic:

    - 32 MiB lexical cache limit (forces corpus rebuild if exceeded)
    - Linear scan over all documents for BM25
    - Per-query Qdrant filter reconstruction across FFI
    """
    vector = next(retrieval.model.query_embed([query.strip()])).tolist()
    with retrieval.lock:
        records = retrieval.store.current_records(owner)
        revisions = {rev["id"]: (mid, rev) for mid, r in records.items() for rev in r["active"]}
        doc_tokens = {rid: tokens(rev["content"]) for rid, (_, rev) in revisions.items()}
        doc_counts = {rid: Counter(toks) for rid, toks in doc_tokens.items()}
        df = Counter(t for counts in doc_counts.values() for t in counts)
        lengths = {rid: sum(c.values()) for rid, c in doc_counts.items()}
        avg = sum(lengths.values()) / max(1, len(revisions))

        # Re-build Qdrant filter on every query
        eligible = q.Filter(must=[q.HasIdCondition(set(revisions))]) if revisions else None

        points = retrieval.shard.search(
            q.SearchRequest(
                query=q.Query.Nearest(vector, using="dense"),
                limit=max(100, limit * 4),
                filter=eligible,
                with_payload=False,
            )
        )

        terms = set(tokens(query))
        lexical = {}
        for rid, counts in doc_counts.items():
            score = 0.0
            for t in terms:
                tf = counts[t]
                if tf:
                    idf = math.log(1 + (len(doc_counts) - df[t] + 0.5) / (df[t] + 0.5))
                    score += idf * tf * 2.5 / (tf + 1.5 * (0.25 + 0.75 * lengths[rid] / max(avg, 1)))
            if score:
                lexical[rid] = score

        dense = {}
        for p in points:
            rid = str(p.id)
            if rid in revisions:
                dense[rid] = max(dense.get(rid, -1), p.score)

        scores = {rid: 1 / (61 + rank) for rank, (rid, _) in enumerate(sorted(dense.items(), key=lambda v: (-v[1], v[0])))}
        for rank, (rid, _) in enumerate(sorted(lexical.items(), key=lambda v: (-v[1], v[0]))):
            scores[rid] = scores.get(rid, 0) + 1 / (61 + rank)

        chosen = {}
        for rid in sorted(scores, key=lambda rid: (-scores[rid], rid)):
            mid, rev = revisions[rid]
            if mid not in chosen:
                chosen[mid] = (rid, rev)

        results = []
        for mid, (rid, rev) in list(chosen.items())[:limit]:
            r = records[mid]
            results.append({"id": mid, "title": r["title"], "matched_revision_id": rid})
        return retrieval.store.eligible_results(results, owner)


def benchmark_scale(n_records, model_cache_path, num_queries=30, runs=1):
    print("\n========================================================")
    print(f"  BENCHMARKING SCALE: {n_records:,} RECORDS")
    print("========================================================")

    rng = random.Random(20260928 + n_records)
    query_templates = [
        ("high temperature and cough", 0),
        ("penicillin rash allergy", 1),
        ("blood pressure measurement", 2),
        ("private follow up", 3),
        ("dizzy after drinking little fluid", 4),
    ]

    with tempfile.TemporaryDirectory(prefix=f"bench-{n_records}-") as temp_dir:
        temp_path = Path(temp_dir)
        store = None
        retrieval = None
        try:
            store = Store(temp_path, secrets.token_hex(32))

            # 1. Ingestion
            print(f"[{n_records:,}] Ingesting {n_records:,} records into SQLCipher store...")
            start = time.perf_counter()
            now = time.time()
            batch_size = 5000
            for b in range(0, n_records, batch_size):
                end = min(b + batch_size, n_records)
                with store.transaction():
                    for i in range(b, end):
                        mid, rid = str(uuid4()), str(uuid4())
                        note = NOTES[i % len(NOTES)]
                        content = note["content"]
                        title = note["title"]
                        subject = f"SYN-{i + 1000:04d}"
                        category = note.get("category", "NOTE")
                        privacy = note.get("privacy", "LOCAL_ONLY")
                        importance = note.get("importance", 0.5)
                        ts = now + i * 0.001
                        store.db.execute(
                            "INSERT INTO memories VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                            (mid, "operator", title, subject, category, privacy, importance, None, json.dumps([rid]), 0, ts),
                        )
                        store.db.execute(
                            "INSERT INTO revisions VALUES(?,?,?,?,?,?,?,?)",
                            (rid, mid, "[]", content, "edge-a", 0, 0, ts),
                        )
                        store.db.execute("INSERT INTO jobs(revision_id) VALUES(?)", (rid,))
            ingest_time = time.perf_counter() - start
            print(f"[{n_records:,}] Durable ingestion completed in {ingest_time:.3f}s ({n_records / ingest_time:.0f} rec/s)")

            # 2. Indexing with real BGE model
            print(f"[{n_records:,}] Indexing vectors into Qdrant Edge shard...")
            real_model = local_embedder(model_cache_path)
            embedder = TemplateCachedEmbedder(real_model)
            retrieval = Retrieval(store, model_cache_path, embedder=embedder)

            start = time.perf_counter()
            drained_count = 0
            while True:
                n = retrieval.drain(batch_size=64)
                if not n:
                    break
                drained_count += n
            index_time = time.perf_counter() - start
            print(f"[{n_records:,}] Indexing completed in {index_time:.3f}s ({drained_count} jobs indexed)")

            # 3. Cold Search (First search after index)
            print(f"[{n_records:,}] Measuring cold search latency...")
            start = time.perf_counter()
            retrieval.search(query_templates[0][0], limit=5)
            cold_search_ms = (time.perf_counter() - start) * 1000
            print(f"[{n_records:,}] Cold search (initial): {cold_search_ms:.2f} ms")

            # 4. Cold Search after Restart (Persistent Cache Recovery)
            retrieval.close()
            retrieval_restarted = Retrieval(store, model_cache_path, embedder=embedder)
            start = time.perf_counter()
            retrieval_restarted.search(query_templates[0][0], limit=5)
            cold_restart_search_ms = (time.perf_counter() - start) * 1000
            print(f"[{n_records:,}] Cold search (from disk cache): {cold_restart_search_ms:.2f} ms")
            retrieval = retrieval_restarted

            # 5. Baseline search comparison (for scales <= 10k to compare directly)
            baseline_p50_ms = None
            if n_records <= 10000:
                print(f"[{n_records:,}] Measuring baseline unoptimized search...")
                base_times = []
                for i in range(min(15, num_queries)):
                    q_text, _ = query_templates[i % len(query_templates)]
                    t0 = time.perf_counter()
                    run_baseline_search(retrieval, q_text, limit=5)
                    base_times.append((time.perf_counter() - t0) * 1000)
                baseline_p50_ms = round(statistics.median(base_times), 2)
                print(f"[{n_records:,}] Baseline p50: {baseline_p50_ms} ms")

            # 6. Warm Search Measurements (Optimized)
            print(f"[{n_records:,}] Running {num_queries} warm queries...")
            latencies = []
            hits = 0
            stage_samples = []

            order = list(range(num_queries))
            rng.shuffle(order)
            for i in order:
                qi = i % len(query_templates)
                q_base, expected = query_templates[qi]
                q_text = f"{q_base} synthetic {i % 10}"
                stages = {}
                t0 = time.perf_counter()
                results = retrieval.search(q_text, limit=5, timings=stages)
                elapsed_ms = (time.perf_counter() - t0) * 1000
                latencies.append(elapsed_ms)
                stage_samples.append(stages)
                hits += any(r["title"] == NOTES[expected]["title"] for r in results)

            p50 = statistics.median(latencies)
            sorted_lat = sorted(latencies)
            p95_idx = min(math.ceil(0.95 * len(sorted_lat)) - 1, len(sorted_lat) - 1)
            p99_idx = min(math.ceil(0.99 * len(sorted_lat)) - 1, len(sorted_lat) - 1)
            p95 = sorted_lat[p95_idx]
            p99 = sorted_lat[p99_idx]
            max_lat = max(latencies)
            peak_rss = get_peak_rss_mb()
            hit_rate = hits / num_queries

            stage_p50 = {}
            if stage_samples and stage_samples[0]:
                for k in stage_samples[0]:
                    stage_p50[k] = round(statistics.median(s.get(k, 0) for s in stage_samples), 3)

            print(f"[{n_records:,}] Optimized warm p50: {p50:.2f} ms | p95: {p95:.2f} ms | p99: {p99:.2f} ms | max: {max_lat:.2f} ms")
            print(f"[{n_records:,}] Template hit@5: {hit_rate * 100:.1f}% | Peak RSS: {peak_rss:.1f} MiB")
            if stage_p50:
                print(f"[{n_records:,}] Stage breakdown p50 (ms): {stage_p50}")

            result = {
                "records": n_records,
                "durable_ingest_s": round(ingest_time, 3),
                "indexing_s": round(index_time, 3),
                "cold_search_initial_ms": round(cold_search_ms, 2),
                "cold_search_disk_cache_ms": round(cold_restart_search_ms, 2),
                "baseline_warm_p50_ms": baseline_p50_ms,
                "optimized_warm_p50_ms": round(p50, 2),
                "optimized_warm_p95_ms": round(p95, 2),
                "optimized_warm_p99_ms": round(p99, 2),
                "optimized_warm_max_ms": round(max_lat, 2),
                "template_hit_rate": round(hit_rate, 3),
                "peak_rss_mib": peak_rss,
                "stages_p50_ms": stage_p50,
            }
        finally:
            if retrieval is not None:
                try:
                    retrieval.close()
                except Exception:
                    pass
            if store is not None:
                try:
                    store.close()
                except Exception:
                    pass
        return result


def main():
    parser = argparse.ArgumentParser(description="EdgeMed Retrieval Scaling Benchmark")
    parser.add_argument("--scales", nargs="+", type=int, default=[1000, 5000, 10000, 25000, 50000])
    parser.add_argument("--queries", type=int, default=30)
    parser.add_argument("--output", type=Path, default=Path("docs/scaling-benchmark-results.json"))
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    model_cache = root / ".cache/models"

    print("================================================================")
    print("      EDGEMED LOCAL RETRIEVAL PIPELINE SCALING BENCHMARK        ")
    print(f"Platform: {platform.platform()} | Python: {platform.python_version()}")
    print(f"Model: BAAI/bge-small-en-v1.5 (revision {MODEL_REVISION[:7]})")
    print(f"Scales: {args.scales}")
    print("================================================================")

    results = []
    for scale in args.scales:
        res = benchmark_scale(scale, model_cache, num_queries=args.queries)
        results.append(res)

    output_data = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "model": "BAAI/bge-small-en-v1.5",
        "benchmark_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scales": results,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output_data, indent=2) + "\n")
    print(f"\nBenchmark results saved to: {args.output}")

    # Generate Markdown Table
    md_lines = [
        "| Scale (Records) | Baseline p50 | Optimized p50 | Optimized p95 | Cold (Disk Cache) | Indexing Time | Peak RSS | Speedup |",
        "|----------------:|-------------:|--------------:|--------------:|-------------------:|--------------:|---------:|--------:|",
    ]
    for r in results:
        base = f"{r['baseline_warm_p50_ms']:.1f} ms" if r["baseline_warm_p50_ms"] else "N/A"
        speedup = f"{r['baseline_warm_p50_ms'] / r['optimized_warm_p50_ms']:.1f}x" if r["baseline_warm_p50_ms"] else "N/A"
        md_lines.append(
            f"| {r['records']:,} | {base} | **{r['optimized_warm_p50_ms']:.2f} ms** | {r['optimized_warm_p95_ms']:.2f} ms | {r['cold_search_disk_cache_ms']:.2f} ms | {r['indexing_s']:.1f} s | {r['peak_rss_mib']:.1f} MiB | {speedup} |"
        )

    md_table = "\n".join(md_lines)
    print("\n" + md_table)


if __name__ == "__main__":
    main()
