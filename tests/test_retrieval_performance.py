"""Regression and performance tests for optimized local retrieval pipeline.

Verifies:
- Mathematical equivalence between inverted-index BM25 and baseline linear scan.
- Accurate memory estimation and successful caching of 10,000+ records.
- Qdrant eligibility filter precomputation and reuse.
- Multi-subject cache separation.
- On-disk lexical cache persistence and cold-start recovery.
- Backward compatibility with legacy tuple unpacking and _corpus property.
"""

import json
import math
import secrets
from collections import Counter
from uuid import uuid4

import numpy as np

from edgemed.fixtures import NOTES
from edgemed.models import CreateMemory
from edgemed.retrieval import LexicalCorpus, Retrieval, tokens
from edgemed.store import Store


class MockEmbedder:
    """Deterministic fast embedder for testing retrieval pipeline logic."""

    def embed(self, texts):
        for _ in texts:
            yield np.array([1.0] + [0.0] * 383)

    query_embed = embed


def make_store(path):
    return Store(path, secrets.token_hex(32))


def test_inverted_index_bm25_matches_baseline_exactly():
    """Verify inverted index scores are mathematically identical to baseline formula."""
    records = {}
    revisions = {}
    sample_texts = [
        "Patient has high fever and persistent dry cough.",
        "Penicillin rash allergic reaction on upper arms.",
        "Blood pressure recorded at 135/85 mmHg.",
        "Follow up for fever, cough resolved, mild fatigue.",
        "Patient reported severe cough after allergy to penicillin.",
    ]

    for i, text in enumerate(sample_texts):
        mid, rid = str(uuid4()), str(uuid4())
        records[mid] = {"id": mid, "title": f"Note {i}", "content": text, "active": [{"id": rid, "content": text}]}
        revisions[rid] = (mid, {"id": rid, "content": text})

    corpus = LexicalCorpus(records, revisions)

    # Baseline calculation
    docs = {rid: Counter(tokens(rev["content"])) for rid, (_, rev) in revisions.items()}
    df = Counter(t for counts in docs.values() for t in counts)
    lengths = {rid: sum(counts.values()) for rid, counts in docs.items()}
    avg = sum(lengths.values()) / max(1, len(docs))

    query = "fever and cough with penicillin allergy"
    terms = set(tokens(query))

    # Baseline score calculation
    baseline_scores = {}
    for rid, counts in docs.items():
        score = 0.0
        for t in terms:
            tf = counts[t]
            if tf:
                idf = math.log(1 + (len(docs) - df[t] + 0.5) / (df[t] + 0.5))
                score += idf * tf * 2.5 / (tf + 1.5 * (0.25 + 0.75 * lengths[rid] / max(avg, 1)))
        if score:
            baseline_scores[rid] = score

    # Inverted index score calculation
    inverted_scores = {}
    num_docs, avg_len = corpus.num_docs, max(corpus.avg_len, 1)
    for t in terms:
        plist = corpus.postings.get(t)
        if not plist:
            continue
        df_t = len(plist)
        idf = math.log(1 + (num_docs - df_t + 0.5) / (df_t + 0.5))
        for rid, tf in plist.items():
            score = idf * tf * 2.5 / (tf + 1.5 * (0.25 + 0.75 * corpus.lengths[rid] / avg_len))
            inverted_scores[rid] = inverted_scores.get(rid, 0.0) + score

    assert set(baseline_scores.keys()) == set(inverted_scores.keys())
    for rid in baseline_scores:
        assert math.isclose(baseline_scores[rid], inverted_scores[rid], rel_tol=1e-9)


def test_ten_thousand_records_cached_without_rejection(tmp_path):
    """Verify that a 10,000-record dataset is successfully cached within memory limits."""
    store = make_store(tmp_path)
    with store.transaction():
        for i in range(10000):
            mid, rid = str(uuid4()), str(uuid4())
            content = f"Synthetic observation {i} fever cough temperature {i % 100}"
            store.db.execute(
                "INSERT INTO memories VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (mid, "operator", f"Note {i}", f"SYN-{(i % 50):04d}", "NOTE", "SENSITIVE", 0.5, None, json.dumps([rid]), 0, i),
            )
            store.db.execute(
                "INSERT INTO revisions VALUES(?,?,?,?,?,?,?,?)",
                (rid, mid, "[]", content, "edge-a", 0, 0, i),
            )
            store.db.execute("INSERT INTO jobs(revision_id) VALUES(?)", (rid,))

    retrieval = Retrieval(store, tmp_path, embedder=MockEmbedder())

    # First load builds corpus
    corpus1 = retrieval._load_corpus("operator", None)
    assert isinstance(corpus1, LexicalCorpus)
    assert corpus1.num_docs == 10000
    assert corpus1.estimate_bytes() < 100 * 1024 * 1024  # Well under 256 MiB

    # Second load must return exact same cached object (no DB queries or re-tokenization)
    corpus2 = retrieval._load_corpus("operator", None)
    assert corpus1 is corpus2

    # Eligibility filter is precomputed once
    assert corpus1.eligible is not None

    retrieval.close()
    store.close()


def test_cache_invalidation_on_mutation(tmp_path):
    """Ensure corpus cache invalidates when generation advances on store mutation."""
    store = make_store(tmp_path)
    m = store.create(CreateMemory(title="Original", content="fever cough"))
    retrieval = Retrieval(store, tmp_path, embedder=MockEmbedder())

    corpus1 = retrieval._load_corpus("operator", None)
    assert m["id"] in corpus1.records

    # Mutate store -> advances store.generation
    store.revise(m["id"], m["heads"], content="updated allergy rash")

    # Next load should produce new corpus reflecting update
    corpus2 = retrieval._load_corpus("operator", None)
    assert corpus2 is not corpus1
    active_rev = store.current_records()[m["id"]]["active"][0]["id"]
    assert active_rev in corpus2.revisions

    retrieval.close()
    store.close()


def test_multi_subject_cache_isolation(tmp_path):
    """Verify that querying different subjects does not evict general owner corpus."""
    store = make_store(tmp_path)
    for i in range(20):
        sub = f"SYN-{i % 3:03d}"
        store.create(CreateMemory(title=f"Note {i}", content="observation data", subject=sub))

    retrieval = Retrieval(store, tmp_path, embedder=MockEmbedder())

    # Load general owner
    c_gen = retrieval._load_corpus("operator", None)
    # Load subject SYN-000
    c_s0 = retrieval._load_corpus("operator", "SYN-000")
    # Load subject SYN-001
    c_s1 = retrieval._load_corpus("operator", "SYN-001")

    # General owner corpus should still be cached
    assert retrieval._load_corpus("operator", None) is c_gen
    assert retrieval._load_corpus("operator", "SYN-000") is c_s0
    assert retrieval._load_corpus("operator", "SYN-001") is c_s1

    retrieval.close()
    store.close()


def test_persistent_lexical_cache_disk_recovery(tmp_path):
    """Verify that on-disk lexical cache enables instant cold-start recovery."""
    store = make_store(tmp_path)
    for note in NOTES:
        store.create(CreateMemory(**note))

    retrieval1 = Retrieval(store, tmp_path, embedder=MockEmbedder())
    c1 = retrieval1._load_corpus("operator", None)
    cache_path = store.root / "lexical_operator.cache"
    assert cache_path.is_file()
    retrieval1.close()

    # Simulate fresh process restart (new Retrieval instance)
    retrieval2 = Retrieval(store, tmp_path, embedder=MockEmbedder())
    c2 = retrieval2._load_corpus("operator", None)

    assert c2.num_docs == c1.num_docs
    assert c2.total_tokens == c1.total_tokens
    assert set(c2.postings.keys()) == set(c1.postings.keys())
    assert c2.lengths == c1.lengths

    retrieval2.close()
    store.close()


def test_backward_compatibility_interfaces(tmp_path):
    """Verify tuple unpacking, clear_cache, and _corpus property compatibility."""
    store = make_store(tmp_path)
    store.create(CreateMemory(title="Test", content="fever symptom"))
    retrieval = Retrieval(store, tmp_path, embedder=MockEmbedder())

    corpus = retrieval._load_corpus("operator", None)

    # Tuple unpacking test
    records, revisions, docs, lengths, df, avg = corpus
    assert len(records) == 1
    assert len(revisions) == 1
    assert isinstance(docs, dict)
    assert isinstance(lengths, dict)
    assert isinstance(df, Counter)
    assert isinstance(avg, float)

    # _corpus property test
    assert retrieval._corpus is not None
    k, v = retrieval._corpus
    assert k == ("operator", None, store.generation)
    assert v is corpus

    # Setter test
    retrieval._corpus = None
    assert retrieval._corpus is None

    retrieval.clear_cache()
    assert retrieval._corpus is None

    retrieval.close()
    store.close()
