"""Provisioning must be portable for model assets and fail closed on corruption."""

import hashlib
import importlib.util
import io
import json
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
    files[".tools/qdrant"] = "unused platform-specific hash"
    (tmp_path / "assets-manifest.json").write_text(json.dumps({"files": files}))
    monkeypatch.setattr(provisioner, "ROOT", tmp_path)
    monkeypatch.setattr(provisioner.platform, "system", lambda: "Linux")
    monkeypatch.setattr(provisioner.platform, "machine", lambda: "x86_64")
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


def test_linux_full_provisioning_still_requires_reviewed_server(monkeypatch, provisioner):
    monkeypatch.setattr(provisioner.platform, "system", lambda: "Linux")
    with pytest.raises(RuntimeError, match="--model-only"):
        provisioner.main([])


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
