import hashlib
import io
import secrets
import tarfile
import time

import pytest

from edgemed.governance import evaluate
from edgemed.security import new_identity, sign
from edgemed.snapshots import install, validate_archive
from edgemed.store import Store


@pytest.mark.parametrize(
    "category,importance,conflicting", [("ALLERGY", 0.1, False), ("NOTE", 0.9, False), ("NOTE", 0.1, True)]
)
def test_retention_pin_overrides_age(category, importance, conflicting):
    m = {
        "created": time.time() - 86400 * 1000,
        "category": category,
        "importance": importance,
        "conflicting": conflicting,
        "release": "LOCAL_ONLY",
        "reason": "private",
    }
    decision = evaluate(m)
    assert decision["pinned"] and decision["retention"] == "RETAIN"
    assert decision["release"] == "LOCAL_ONLY" and not decision["automatic_deletion"]


@pytest.mark.parametrize(
    "name,link", [("../escape", False), ("/absolute", False), ("safe", True), ("a\\b", False)]
)
def test_malicious_archive_rejected(tmp_path, name, link):
    p = tmp_path / "bad.tar"
    with tarfile.open(p, "w") as t:
        entry = tarfile.TarInfo(name)
        if link:
            entry.type = tarfile.SYMTYPE
            entry.linkname = "/private/tmp/escape"
        else:
            entry.size = 1
        t.addfile(entry, io.BytesIO(b"x"))
    with pytest.raises(ValueError, match="Unsafe"):
        validate_archive(p)


@pytest.mark.parametrize("failure", ["signature", "digest", "scope", "rollback", "metadata"])
def test_snapshot_manifest_fails_closed(tmp_path, failure):
    key, pub = new_identity()
    s = Store(tmp_path / "db", secrets.token_hex(32))
    s.set_setting("cursor", 3)
    s.set_setting("reference_snapshot", {"generation": 2, "path": "unchanged"})
    p = tmp_path / "payload.gz"
    p.write_bytes(b"not-an-archive")
    m = {
        "scope": "public-synthetic-references",
        "schema_version": 1,
        "model": "BAAI/bge-small-en-v1.5",
        "nonce": "request",
        "generation": 3,
        "bytes": p.stat().st_size,
        "expanded_bytes": 10,
        "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
    }
    if failure == "digest":
        m["sha256"] = "0" * 64
    if failure == "scope":
        m["scope"] = "private-patients"
    if failure == "rollback":
        m["generation"] = 1
    if failure == "metadata":
        m["generation"] = 4
    envelope = {"payload": m, "signature": sign(m, key)}
    if failure == "signature":
        envelope["signature"] = "bad"
    with pytest.raises(ValueError):
        install(s, p, envelope, pub, "request")
    assert s.get_setting("reference_snapshot")["path"] == "unchanged"
    s.close()
