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


_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokens(text):
    return _TOKEN_RE.findall(text.lower())


MODEL_REVISION = "aa8f8b060edb00e03bfdd08813a2949946c8ba55"
MAX_LEXICAL_CACHE_BYTES = int(os.environ.get("EDGEMED_MAX_LEXICAL_CACHE_MB", "256")) * 1024 * 1024


class LexicalCorpus:
    """Precomputed sparse lexical index, forward mappings, and canonical eligibility."""

    def __init__(self, records, revisions):
        self.records = records
        self.revisions = revisions
        self.num_docs = len(revisions)

        # Inverted index: token -> dict[rid, tf]
        self.postings = {}
        self.lengths = {}
        total_tokens = 0
        for rid, (_, rev) in revisions.items():
            toks = tokens(rev["content"])
            counts = Counter(toks)
            length = sum(counts.values())
            self.lengths[rid] = length
            total_tokens += length
            for t, tf in counts.items():
                if t not in self.postings:
                    self.postings[t] = {}
                self.postings[t][rid] = tf

        self.total_tokens = total_tokens
        self.avg_len = total_tokens / max(1, self.num_docs)

        # Precompute Qdrant eligibility filter once per generation/corpus
        try:
            self.eligible = q.Filter(must=[q.HasIdCondition(set(revisions))]) if revisions else None
        except Exception:
            self.eligible = None

    def estimate_bytes(self):
        postings_bytes = sum(len(p) * 32 + 128 for p in self.postings.values())
        lengths_bytes = len(self.lengths) * 32
        revisions_bytes = len(self.revisions) * 128
        records_bytes = sum(len(r.get("content", "").encode()) + 512 for r in self.records.values())
        return postings_bytes + lengths_bytes + revisions_bytes + records_bytes

    def __iter__(self):
        """Backward compatibility: allows unpacking as (records, revisions, docs, lengths, df, avg)."""
        docs = {rid: Counter(tokens(rev["content"])) for rid, (_, rev) in self.revisions.items()}
        df = Counter(t for counts in docs.values() for t in counts)
        return iter((self.records, self.revisions, docs, self.lengths, df, self.avg_len))


def local_embedder(cache, threads=2):
    path = Path(cache) / "models--Qdrant--bge-small-en-v1.5-onnx-Q" / "snapshots" / MODEL_REVISION
    if not (path / "model_optimized.onnx").is_file():
        raise RuntimeError(
            "Pinned local embedding model is missing. From the repository root, provision it online with: "
            "uv run python scripts/provision_assets.py --model-only. Runtime will not download it."
        )
    return TextEmbedding(
        MODEL, cache_dir=str(cache), local_files_only=True, threads=threads, specific_model_path=str(path)
    )


class Retrieval:
    def __init__(self, store, cache: Path, embedder=None):
        self.store, self.lock = store, threading.RLock()
        self.model_lock, self.drain_lock = threading.Lock(), threading.Lock()
        self.model = embedder or local_embedder(cache)
        self._corpora = {}
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

    @property
    def _corpus(self):
        if not self._corpora:
            return None
        k, v = next(iter(self._corpora.items()))
        return (k, v)

    @_corpus.setter
    def _corpus(self, val):
        self._corpora.clear()
        if val is not None:
            self._corpora[val[0]] = val[1]

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
            self._corpora.clear()

    def drain(self, batch_size=32):
        with self.drain_lock:
            jobs = self.store.pending_jobs()[:batch_size]
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
        with self.store.lock:
            # Purge any stale generation corpora
            current_gen = self.store.generation
            stale = [k for k in self._corpora if k[2] != current_gen]
            for k in stale:
                del self._corpora[k]

            key = (owner, subject, current_gen)
            if key in self._corpora:
                return self._corpora[key]

            # Fast persistent cache recovery for general owner corpus on cold starts / restarts
            if subject is None:
                cache_file = self.store.root / f"lexical_{owner}.cache"
                if cache_file.is_file():
                    try:
                        import pickle
                        data = pickle.loads(cache_file.read_bytes())
                        if data.get("generation") == current_gen and data.get("owner") == owner:
                            corpus = LexicalCorpus.__new__(LexicalCorpus)
                            corpus.records = data["records"]
                            corpus.revisions = data["revisions"]
                            corpus.num_docs = len(corpus.revisions)
                            corpus.postings = data["postings"]
                            corpus.lengths = data["lengths"]
                            corpus.total_tokens = data["total_tokens"]
                            corpus.avg_len = data["total_tokens"] / max(1, corpus.num_docs)
                            try:
                                corpus.eligible = (
                                    q.Filter(must=[q.HasIdCondition(set(corpus.revisions))])
                                    if corpus.revisions
                                    else None
                                )
                            except Exception:
                                corpus.eligible = None
                            if corpus.estimate_bytes() <= MAX_LEXICAL_CACHE_BYTES:
                                self._corpora[key] = corpus
                            return corpus
                    except Exception:
                        pass

            records = self.store.current_records(owner, subject)

        revisions = {rev["id"]: (mid, rev) for mid, r in records.items() for rev in r["active"]}
        corpus = LexicalCorpus(records, revisions)

        estimate = corpus.estimate_bytes()
        if estimate <= MAX_LEXICAL_CACHE_BYTES:
            if len(self._corpora) >= 8:
                self._corpora.pop(next(iter(self._corpora)), None)
            self._corpora[key] = corpus

            # Persist general owner corpus for cold start acceleration
            if subject is None:
                try:
                    import pickle
                    cache_file = self.store.root / f"lexical_{owner}.cache"
                    cache_data = {
                        "generation": current_gen,
                        "owner": owner,
                        "records": corpus.records,
                        "revisions": corpus.revisions,
                        "postings": corpus.postings,
                        "lengths": corpus.lengths,
                        "total_tokens": corpus.total_tokens,
                    }
                    cache_file.write_bytes(pickle.dumps(cache_data, protocol=5))
                except Exception:
                    pass

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
                corpus = self._load_corpus(owner, subject)
                if isinstance(corpus, LexicalCorpus):
                    records, revisions = corpus.records, corpus.revisions
                    eligible = corpus.eligible
                else:
                    records, revisions, docs, lengths, df, avg = corpus
                    eligible = q.Filter(must=[q.HasIdCondition(set(revisions))]) if revisions else None

            if not revisions:
                return []

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
                    if isinstance(corpus, LexicalCorpus):
                        num_docs, avg_len = corpus.num_docs, max(corpus.avg_len, 1)
                        for t in terms:
                            plist = corpus.postings.get(t)
                            if not plist:
                                continue
                            df_t = len(plist)
                            idf = math.log(1 + (num_docs - df_t + 0.5) / (df_t + 0.5))
                            for rid, tf in plist.items():
                                score = (
                                    idf
                                    * tf
                                    * 2.5
                                    / (tf + 1.5 * (0.25 + 0.75 * corpus.lengths[rid] / avg_len))
                                )
                                lexical[rid] = lexical.get(rid, 0.0) + score
                    else:
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
                        if len(chosen) >= limit:
                            break
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
            self._corpora.clear()
            if self.reference:
                self.reference.close()
            self.shard.close()
