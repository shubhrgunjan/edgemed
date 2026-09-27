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


class Retrieval:
    def __init__(self, store, cache: Path, embedder=None):
        self.store, self.lock = store, threading.RLock()
        self.model = embedder or TextEmbedding(MODEL, cache_dir=str(cache), local_files_only=True, threads=2)
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
                store.db.execute("UPDATE jobs SET state='pending'")
        self.reference = None
        self.reload_reference()

    def reload_reference(self):
        if self.reference:
            self.reference.close()
        state = self.store.get_setting("reference_snapshot")
        self.reference = q.EdgeShard.load(state["path"]) if state else None

    def drain(self):
        with self.lock:
            jobs = self.store.pending_jobs()
            for job in jobs:
                if job["memory_deleted"]:
                    self.shard.update(q.UpdateOperation.delete_points([job["id"]]))
                else:
                    vector = next(self.model.embed([job["content"]])).tolist()
                    self.shard.update(
                        q.UpdateOperation.upsert_points(
                            [
                                q.Point(
                                    id=job["id"],
                                    vector={"dense": vector},
                                    payload={"owner": job["owner"], "memory_id": job["memory_id"]},
                                )
                            ]
                        )
                    )
                self.shard.flush()
                self.store.mark_indexed(job["id"])
            return len(jobs)

    def search(self, query, owner="operator", limit=10, mode="hybrid", subject=None):
        with self.lock:
            vector = next(self.model.query_embed([query])).tolist()
            points = self.shard.search(
                q.SearchRequest(
                    query=q.Query.Nearest(vector, using="dense"),
                    limit=100,
                    filter=q.Filter(must=[q.FieldCondition("owner", match=q.MatchValue(owner))]),
                    with_payload=True,
                )
            )
            if self.reference:
                points += self.reference.search(
                    q.SearchRequest(query=q.Query.Nearest(vector), limit=100, with_payload=True)
                )
                points.sort(key=lambda p: -p.score)
            records = self.store.list(owner, limit=10000)
            allowed = {r["id"]: r for r in records if subject is None or r["subject"] == subject}
            scores, dense, lexical = {}, {}, {}
            for rank, point in enumerate(points):
                mid = point.payload["memory_id"]
                if mid not in allowed or str(point.id) not in allowed[mid]["heads"]:
                    continue
                scores[mid] = max(scores.get(mid, 0), 1 / (60 + rank + 1))
                dense[mid] = max(dense.get(mid, -1), point.score)
            # BM25 is computed locally over authorized canonical text; no keyword representation leaves.
            docs = {mid: tokens(r["content"]) for mid, r in allowed.items()}
            avg = sum(map(len, docs.values())) / max(1, len(docs))
            terms = set(tokens(query))
            df = {t: sum(t in doc for doc in docs.values()) for t in terms}
            for mid, doc in docs.items():
                counts = Counter(doc)
                score = 0.0
                for t in terms:
                    tf = counts[t]
                    idf = math.log(1 + (len(docs) - df[t] + 0.5) / (df[t] + 0.5))
                    score += idf * tf * 2.5 / (tf + 1.5 * (0.25 + 0.75 * len(doc) / max(avg, 1)))
                if score:
                    lexical[mid] = score
            if mode == "hybrid":
                for rank, (mid, _) in enumerate(sorted(lexical.items(), key=lambda x: -x[1])):
                    scores[mid] = scores.get(mid, 0) + 1 / (61 + rank)
            results = []
            for mid, score in sorted(scores.items(), key=lambda x: -x[1])[:limit]:
                results.append(
                    {
                        **allowed[mid],
                        "score": score,
                        "semantic_score": dense.get(mid),
                        "keyword_score": lexical.get(mid, 0),
                    }
                )
            return results

    def close(self):
        with self.lock:
            if self.reference:
                self.reference.close()
            self.shard.close()
