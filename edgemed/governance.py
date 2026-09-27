import math
import time


def evaluate(memory):
    """Deterministic advisory retention; export authorization is a separate hard rule."""
    age_days = max(0, (time.time() - memory["created"]) / 86400)
    freshness = math.exp(-age_days / 30)
    score = round(0.7 * memory["importance"] + 0.3 * freshness, 3)
    pinned = memory["category"] == "ALLERGY" or memory["importance"] >= 0.85 or memory["conflicting"]
    decision = "RETAIN" if pinned or score >= 0.25 else "ARCHIVE_CANDIDATE"
    return {
        "rule_version": "retention-v1",
        "retention": decision,
        "score": score,
        "pinned": pinned,
        "release": memory["release"],
        "reason": memory["reason"],
        "factors": {"importance": memory["importance"], "freshness": round(freshness, 3)},
        "automatic_deletion": False,
    }
