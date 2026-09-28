"""Provisioning must be portable for model assets and fail closed on corruption."""

import hashlib
import importlib.util
import io
import json
import tarfile
from pathlib import Path

import pytest


@pytest.fixture
def provisioner():
    path = Path(__file__).resolve().parents[1] / "scripts/provision_assets.py"
    spec = importlib.util.spec_from_file_location("provision_assets", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_linux_model_only_downloads_verified_assets_without_server(tmp_path, monkeypatch, provisioner):
    base = f".cache/models/models--Qdrant--bge-small-en-v1.5-onnx-Q/snapshots/{provisioner.REVISION}"
    bodies = {"model_optimized.onnx": b"synthetic model", "tokenizer.json": b"{}"}
    files = {f"{base}/{name}": hashlib.sha256(data).hexdigest() for name, data in bodies.items()}
    (tmp_path / "assets-manifest.json").write_text(json.dumps({"files": files}))
    monkeypatch.setattr(provisioner, "ROOT", tmp_path)
    urls = []

    def public_asset(url, timeout):
        urls.append(url)
        assert f"/resolve/{provisioner.REVISION}/" in url
        return io.BytesIO(bodies[url.rsplit("/", 1)[1]])

    monkeypatch.setattr(provisioner, "urlopen", public_asset)
    provisioner.main(["--model-only"])
    assert len(urls) == 2
    assert not (tmp_path / ".tools").exists()
    for name, data in bodies.items():
        assert (tmp_path / base / name).read_bytes() == data
    # A repeat invocation verifies the existing cache without making a request.
    provisioner.main(["--model-only"])
    assert len(urls) == 2


def test_linux_full_provisioning_pins_archive_and_binary(tmp_path, monkeypatch, provisioner):
    binary = b"synthetic Qdrant executable"
    archive_file = io.BytesIO()
    with tarfile.open(fileobj=archive_file, mode="w:gz") as archive:
        info = tarfile.TarInfo("qdrant")
        info.size = len(binary)
        archive.addfile(info, io.BytesIO(binary))
    archive_data = archive_file.getvalue()
    spec = {
        "archive": "qdrant-x86_64-unknown-linux-gnu.tar.gz",
        "archive_sha256": hashlib.sha256(archive_data).hexdigest(),
        "binary_sha256": hashlib.sha256(binary).hexdigest(),
    }
    (tmp_path / "assets-manifest.json").write_text(
        json.dumps({"qdrant_server": "1.19.1", "files": {}, "qdrant_binaries": {"linux-x86_64": spec}})
    )
    monkeypatch.setattr(provisioner, "ROOT", tmp_path)
    monkeypatch.setattr(provisioner, "target", lambda: "linux-x86_64")
    requested = []

    def public_asset(url, timeout):
        requested.append(url)
        return io.BytesIO(archive_data)

    monkeypatch.setattr(provisioner, "urlopen", public_asset)
    provisioner.main([])
    assert (tmp_path / ".tools/qdrant").read_bytes() == binary
    assert (tmp_path / ".tools/qdrant").stat().st_mode & 0o111
    assert requested == [
        "https://github.com/qdrant/qdrant/releases/download/v1.19.1/"
        "qdrant-x86_64-unknown-linux-gnu.tar.gz"
    ]
    provisioner.main([])
    assert len(requested) == 1


def test_unsupported_native_architecture_rejected():
    from edgemed.platforms import target

    assert target("Darwin", "x86_64") == "macos-x86_64"
    assert target("Linux", "aarch64") == "linux-arm64"
    with pytest.raises(RuntimeError, match="64-bit"):
        target("Linux", "i686")
    with pytest.raises(RuntimeError, match="64-bit"):
        target("Linux", "armv7l")


def test_checksum_failure_preserves_existing_file(tmp_path, monkeypatch, provisioner):
    destination = tmp_path / "model.onnx"
    destination.write_bytes(b"previous file")
    monkeypatch.setattr(provisioner, "urlopen", lambda *a, **kw: io.BytesIO(b"corrupt download"))
    with pytest.raises(RuntimeError, match="checksum mismatch"):
        provisioner.download(
            "https://example.invalid/model", destination, hashlib.sha256(b"good").hexdigest()
        )
    assert destination.read_bytes() == b"previous file"
    assert not destination.with_suffix(".onnx.download").exists()
