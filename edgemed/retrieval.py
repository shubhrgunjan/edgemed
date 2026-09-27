import math
import os
import re
import threading
from collections import Counter
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["DO_NOT_TRACK"] = "1"
import onnxruntime as ort

ort.disable_telemetry_events()
from fastembed import TextEmbedding  # noqa: E402 - offline/telemetry policy precedes runtime imports
import qdrant_edge as q  # noqa: E402

MODEL = "BAAI/bge-small-en-v1.5"


def tokens(text):
    return re.findall(r"[a-z0-9]+", text.lower())


MODEL_REVISION = "aa8f8b060edb00e03bfdd08813a2949946c8ba55"


def local_embedder(cache, threads=2):
    path = Path(cache) / "models--Qdrant--bge-small-en-v1.5-onnx-Q" / "snapshots" / MODEL_REVISION
    if not (path / "model_optimized.onnx").is_file():
        raise RuntimeError("Pinned local embedding model is missing; provision verified assets first")
    return TextEmbedding(
        MODEL, cache_dir=str(cache), local_files_only=True, threads=threads, specific_model_path=str(path)
    )


class Retrieval:
    def __init__(self, store, cache: Path, embedder=None):
        self.store, self.lock = store, threading.RLock()
        self.model_lock, self.drain_lock = threading.Lock(), threading.Lock()
        self.model = embedder or local_embedder(cache)
        self._corpus = None
        path = store.root / "vectors"
        path.mkdir(mode=0o700, exist_ok=True)
        if any(path.iterdir()):
            self.shard = q.EdgeShard.load(str(path))
        else:
            self.shard = q.EdgeShard.create(
                str(path),
                q.EdgeConfig(
                    vectors={"dense": q.EdgeVectorParams(size=384, distance=q.Distance.Cosine)},
                    max_search_threads=2,
                ),
            )
            with store.lock:
                store.db.execute("UPDATE jobs SET state='pending',generation=generation+1")
        self.reference = None
        self.reference_path = None
        self.reload_reference()

    def reload_reference(self):
        # Open before swapping so a corrupt replacement never closes the working shard.
        state = self.store.get_setting("reference_snapshot")
        path = state["path"] if state else None
        if path == self.reference_path:
            return
        replacement = q.EdgeShard.load(path) if state else None
        with self.lock:
            old, self.reference = self.reference, replacement
            self.reference_path = path
            if old:
                old.close()

    def clear_cache(self):
        with self.lock:
            self._corpus = None

    def drain(self):
        with self.drain_lock:
            jobs = self.store.pending_jobs()[:4]
            live = [j for j in jobs if not j["memory_deleted"]]
            with self.model_lock:
                vectors = list(self.model.embed([j["content"] for j in live])) if live else []
            embedded = {j["id"]: v.tolist() for j, v in zip(live, vectors, strict=True)}
            # Lock order: shard then canonical. No network or model work under either.
            with self.lock, self.store.lock:
                accepted = []
                for job in jobs:
                    if not self.store.job_current(job):
                        continue
                    if job["memory_deleted"]:
                        self.shard.update(q.UpdateOperation.delete_points([job["id"]]))
                    else:
                        self.shard.update(
                            q.UpdateOperation.upsert_points(
                                [
                                    q.Point(
                                        id=job["id"],
                                        vector={"dense": embedded[job["id"]]},
                                        payload={"owner": job["owner"], "memory_id": job["memory_id"]},
                                    )
                                ]
                            )
                        )
                    accepted.append(job)
                if accepted:
                    self.shard.flush()
                for job in accepted:
                    self.store.mark_indexed(job["id"], job["generation"])
            return len(jobs)

    def _load_corpus(self, owner, subject):
        # One bounded in-memory corpus, invalidated by every canonical transaction.
        with self.store.lock:
            key = (owner, subject, self.store.generation)
            if self._corpus and self._corpus[0] == key:
                return self._corpus[1]
            records = self.store.current_records(owner, subject)
        revisions = {rev["id"]: (mid, rev) for mid, r in records.items() for rev in r["active"]}
        docs = {rid: Counter(tokens(rev["content"])) for rid, (_, rev) in revisions.items()}
        lengths = {rid: sum(c.values()) for rid, c in docs.items()}
        df = Counter(t for counts in docs.values() for t in counts)
        corpus = (records, revisions, docs, lengths, df, sum(lengths.values()) / max(1, len(docs)))
        # Conservative estimate; oversized corpora stay uncached, never silently truncated.
        estimate = sum(
            len(rev["content"].encode()) * 4 + len(docs[rid]) * 200 + 2048
            for rid, (_, rev) in revisions.items()
        )
        self._corpus = (key, corpus) if estimate <= 32 * 1024 * 1024 else None
        return corpus

    def search(
        self, query, owner="operator", limit=10, mode="hybrid", subject=None, timings=None, vector=None
    ):
        from .metrics import span

        with span(timings, "normalize"):
            query = query.strip()
        if vector is None:
            with span(timings, "embedding"):
                with self.model_lock:
                    vector = next(self.model.query_embed([query])).tolist()
        with span(timings, "lock_wait"):
            self.lock.acquire()
        try:
            with span(timings, "canonical_and_lexical_prepare"):
                records, revisions, docs, lengths, df, avg = self._load_corpus(owner, subject)
            if not revisions:
                return []
            # Apply canonical eligibility before top-k to prevent stale/foreign heads crowding hits.
            eligible = q.Filter(must=[q.HasIdCondition(set(revisions))])
            with span(timings, "dense_local"):
                points = self.shard.search(
                    q.SearchRequest(
                        query=q.Query.Nearest(vector, using="dense"),
                        limit=max(100, limit * 4),
                        filter=eligible,
                        with_payload=False,
                    )
                )
            with span(timings, "dense_reference"):
                if self.reference:
                    points += self.reference.search(
                        q.SearchRequest(
                            query=q.Query.Nearest(vector),
                            limit=max(100, limit * 4),
                            filter=eligible,
                            with_payload=False,
                        )
                    )
            with span(timings, "keyword"):
                lexical = {}
                if mode == "hybrid":
                    terms = set(tokens(query))
                    for rid, counts in docs.items():
                        score = 0.0
                        for t in terms:
                            tf = counts[t]
                            if tf:
                                idf = math.log(1 + (len(docs) - df[t] + 0.5) / (df[t] + 0.5))
                                score += (
                                    idf * tf * 2.5 / (tf + 1.5 * (0.25 + 0.75 * lengths[rid] / max(avg, 1)))
                                )
                        if score:
                            lexical[rid] = score
            with span(timings, "fusion"):
                dense = {}
                for p in points:
                    rid = str(p.id)
                    if rid in revisions:
                        dense[rid] = max(dense.get(rid, -1), p.score)
                scores = {
                    rid: 1 / (61 + rank)
                    for rank, (rid, _) in enumerate(sorted(dense.items(), key=lambda v: (-v[1], v[0])))
                }
                for rank, (rid, _) in enumerate(sorted(lexical.items(), key=lambda v: (-v[1], v[0]))):
                    scores[rid] = scores.get(rid, 0) + 1 / (61 + rank)
                chosen = {}
                for rid in sorted(scores, key=lambda rid: (-scores[rid], rid)):
                    mid, rev = revisions[rid]
                    if mid not in chosen:
                        chosen[mid] = (rid, rev)
                results = []
            with span(timings, "payload"):
                for mid, (rid, rev) in list(chosen.items())[:limit]:
                    r = records[mid]
                    results.append(
                        {
                            k: r[k]
                            for k in (
                                "id",
                                "title",
                                "subject",
                                "category",
                                "privacy",
                                "release",
                                "heads",
                                "fixture",
                                "conflicting",
                                "index_state",
                                "created",
                            )
                        }
                    )
                    results[-1].update(
                        content=rev["content"][:500],
                        matched_revision_id=rid,
                        score=scores[rid],
                        semantic_score=dense.get(rid),
                        keyword_score=lexical.get(rid, 0),
                    )
                return self.store.eligible_results(results, owner, subject)
        finally:
            self.lock.release()

    def close(self):
        with self.drain_lock, self.model_lock, self.lock:
            self._corpus = None
            if self.reference:
                self.reference.close()
            self.shard.close()
