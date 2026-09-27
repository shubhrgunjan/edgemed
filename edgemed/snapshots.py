"""Verified full reference snapshots. Private mutable shards are never exported or replaced."""

import base64
import gzip
import hashlib
import json
import os
import shutil
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from uuid import uuid4

import httpx
import qdrant_edge as q

from .fixtures import REFERENCES, fixture_id
from .security import sign, verify
from .sync import tls_context

MAX_COMPRESSED = 16 * 1024 * 1024
MAX_EXPANDED = 512 * 1024 * 1024


def validate_archive(path):
    """Bound archive expansion and reject links, special files and traversal, including nested tars."""
    budget = [0, 0]

    def inspect(fileobj, depth=0):
        if depth > 3:
            raise ValueError("Nested archive depth exceeded")
        with tarfile.open(fileobj=fileobj, mode="r:*") as archive:
            for entry in archive:
                budget[0] += 1
                budget[1] += entry.size
                name = PurePosixPath(entry.name)
                if (
                    name.is_absolute()
                    or ".." in name.parts
                    or "\\" in entry.name
                    or not (entry.isfile() or entry.isdir())
                ):
                    raise ValueError("Unsafe snapshot archive member")
                if budget[0] > 10000 or budget[1] > MAX_EXPANDED * 2 or entry.size > MAX_EXPANDED:
                    raise ValueError("Snapshot expansion limit exceeded")
                if entry.isfile() and entry.name.endswith(".tar"):
                    with archive.extractfile(entry) as member:
                        inspect(member, depth + 1)

    with open(path, "rb") as stream:
        inspect(stream)


def produce(store, config, secret, nonce):
    import ssl

    root = store.root / "snapshot-exports"
    root.mkdir(exist_ok=True, mode=0o700)
    path = root / (str(uuid4()) + ".snapshot.gz")
    with store.lock:
        if store.db.execute("SELECT count(*) FROM jobs WHERE state!='indexed'").fetchone()[0]:
            raise ValueError("Wait for central indexing before requesting a snapshot")
        generation = store.db.execute("SELECT coalesce(max(seq),0) FROM changes").fetchone()[0]
        ctx = ssl.create_default_context(cafile=config["ca"])
        size = 0
        try:
            with httpx.Client(verify=ctx, trust_env=False, timeout=60, follow_redirects=False) as client:
                with client.stream(
                    "GET",
                    config["qdrant"] + "/collections/lex_synthetic_references/shards/0/snapshot",
                    headers={"api-key": secret["qdrant_api_key"]},
                ) as response:
                    response.raise_for_status()
                    with gzip.open(path, "wb", compresslevel=3) as output:
                        for chunk in response.iter_bytes(65536):
                            size += len(chunk)
                            if size > MAX_EXPANDED:
                                raise ValueError("Server snapshot exceeds size limit")
                            output.write(chunk)
            if path.stat().st_size > MAX_COMPRESSED:
                raise ValueError("Compressed snapshot exceeds size limit")
            manifest = {
                "scope": "public-synthetic-references",
                "generation": generation,
                "schema_version": 1,
                "model": "BAAI/bge-small-en-v1.5",
                "nonce": nonce,
                "bytes": path.stat().st_size,
                "expanded_bytes": size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            envelope = {"payload": manifest, "signature": sign(manifest, secret["sign_private"])}
            return path, base64.b64encode(json.dumps(envelope).encode()).decode()
        except BaseException:
            path.unlink(missing_ok=True)
            raise


def install(store, compressed, envelope, public_key, nonce):
    manifest = envelope["payload"]
    verify(manifest, envelope["signature"], public_key)
    if (
        manifest["scope"] != "public-synthetic-references"
        or manifest["schema_version"] != 1
        or manifest["model"] != "BAAI/bge-small-en-v1.5"
        or manifest["nonce"] != nonce
    ):
        raise ValueError("Snapshot manifest scope, model or request mismatch")
    if (
        manifest["bytes"] > MAX_COMPRESSED
        or manifest["expanded_bytes"] > MAX_EXPANDED
        or compressed.stat().st_size != manifest["bytes"]
    ):
        raise ValueError("Snapshot size mismatch")
    if hashlib.sha256(compressed.read_bytes()).hexdigest() != manifest["sha256"]:
        raise ValueError("Snapshot digest mismatch")
    prior = store.get_setting("reference_snapshot", {"generation": -1})
    if manifest["generation"] < prior["generation"]:
        raise ValueError("Snapshot rollback rejected")
    if manifest["generation"] > store.get_setting("cursor", 0):
        raise ValueError("Synchronize reference metadata before activating snapshot")
    if manifest["generation"] == prior["generation"]:
        return prior
    if shutil.disk_usage(store.root).free < MAX_EXPANDED * 3:
        raise ValueError("Insufficient free vault space for staged snapshot")
    root = store.root / "reference-snapshots"
    root.mkdir(exist_ok=True, mode=0o700)
    with tempfile.TemporaryDirectory(dir=root, prefix="staging-") as temp:
        stage = Path(temp)
        raw = stage / "shard.snapshot"
        total = 0
        with gzip.open(compressed, "rb") as source, raw.open("wb") as output:
            while chunk := source.read(65536):
                total += len(chunk)
                if total > MAX_EXPANDED:
                    raise ValueError("Snapshot expansion limit exceeded")
                output.write(chunk)
        if total != manifest["expanded_bytes"]:
            raise ValueError("Expanded snapshot size mismatch")
        validate_archive(raw)
        shard_path = stage / "shard"
        q.EdgeShard.unpack_snapshot(str(raw), str(shard_path))
        shard = q.EdgeShard.load(str(shard_path))
        try:
            points, offset = shard.scroll(q.ScrollRequest(limit=1000, with_payload=True))
            if offset is not None:
                raise ValueError("Reference snapshot exceeds demo record limit")
            allowed = {fixture_id(f) for f in REFERENCES}
            for point in points:
                if (
                    set(point.payload) != {"memory_id", "schema_version"}
                    or point.payload["memory_id"] not in allowed
                    or point.payload["schema_version"] != 1
                ):
                    raise ValueError("Snapshot contains unapproved payload")
                with store.lock:
                    if not store.db.execute(
                        "SELECT 1 FROM revisions WHERE id=? AND memory_id=?",
                        (str(point.id), point.payload["memory_id"]),
                    ).fetchone():
                        raise ValueError("Snapshot revision lacks synchronized metadata")
        finally:
            shard.close()
        final = root / ("generation-" + str(manifest["generation"]) + "-" + str(uuid4()))
        os.replace(shard_path, final)
        state = {
            "generation": manifest["generation"],
            "path": str(final),
            "points": len(points),
            "bytes": manifest["bytes"],
            "sha256": manifest["sha256"],
        }
        store.set_setting("reference_snapshot", state)
        return state


def fetch(transport):
    store, cfg = transport.store, transport.config
    if not store.get_setting("transport", False):
        raise ValueError("Enable transport before downloading shared references")
    with transport.lock:
        request = {"device_id": store.device, "cursor": store.get_setting("cursor", 0), "nonce": str(uuid4())}
        signed = {**request, "signature": sign(request, transport.secret["sign_private"])}
        with tempfile.TemporaryDirectory(dir=store.root, prefix="snapshot-download-") as temp:
            path = Path(temp) / "reference.gz"
            with httpx.Client(
                verify=tls_context(cfg), trust_env=False, timeout=90, follow_redirects=False
            ) as client:
                with client.stream(
                    "POST", cfg["gateway"] + "/sync/reference-snapshot", json=signed
                ) as response:
                    response.raise_for_status()
                    header = response.headers.get("x-edgemed-manifest", "")
                    if len(header) > 8192:
                        raise ValueError("Oversized snapshot manifest")
                    envelope = json.loads(base64.b64decode(header, validate=True))
                    verify(envelope["payload"], envelope["signature"], cfg["gateway_public"])
                    size = 0
                    with path.open("wb") as output:
                        for chunk in response.iter_bytes(65536):
                            size += len(chunk)
                            if size > MAX_COMPRESSED:
                                raise ValueError("Snapshot download limit exceeded")
                            output.write(chunk)
            return install(store, path, envelope, cfg["gateway_public"], request["nonce"])
