"""Explicit online provisioning of pinned public assets. Runtime never downloads models."""

import hashlib
import json
import os
import platform
import tarfile
import tempfile
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
REVISION = "aa8f8b060edb00e03bfdd08813a2949946c8ba55"
ARCHIVE_HASH = "e060209dfefc9d977ddcec48521349f505f8fd1ce21f2a3db444140870522fe4"


def download(url, path, expected):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected:
        return
    stage = path.with_suffix(path.suffix + ".download")
    try:
        with urlopen(url, timeout=60) as source, stage.open("wb") as target:
            total = 0
            while chunk := source.read(1024 * 1024):
                total += len(chunk)
                if total > 256 * 1024 * 1024:
                    raise RuntimeError("Asset exceeds provisioning size limit")
                target.write(chunk)
        if hashlib.sha256(stage.read_bytes()).hexdigest() != expected:
            raise RuntimeError("Asset checksum mismatch")
        os.replace(stage, path)
    finally:
        stage.unlink(missing_ok=True)


def main():
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise RuntimeError(
            "This asset manifest is verified for macOS ARM64; review a platform-specific manifest first"
        )
    manifest = json.loads((ROOT / "assets-manifest.json").read_text())
    for name, digest in manifest["files"].items():
        if "/snapshots/" in name:
            filename = Path(name).name
            download(
                f"https://huggingface.co/Qdrant/bge-small-en-v1.5-onnx-Q/resolve/{REVISION}/{filename}",
                ROOT / name,
                digest,
            )
    tools = ROOT / ".tools"
    tools.mkdir(exist_ok=True)
    binary = tools / "qdrant"
    if (
        not binary.exists()
        or hashlib.sha256(binary.read_bytes()).hexdigest() != manifest["files"][".tools/qdrant"]
    ):
        with tempfile.TemporaryDirectory(dir=tools) as temp:
            archive = Path(temp) / "qdrant.tar.gz"
            download(
                "https://github.com/qdrant/qdrant/releases/download/v1.19.1/qdrant-aarch64-apple-darwin.tar.gz",
                archive,
                ARCHIVE_HASH,
            )
            with tarfile.open(archive) as tar:
                members = [m for m in tar.getmembers() if m.isfile() and Path(m.name).name == "qdrant"]
                if len(members) != 1 or members[0].size > 256 * 1024 * 1024:
                    raise RuntimeError("Unexpected release archive")
                data = tar.extractfile(members[0]).read()
            if hashlib.sha256(data).hexdigest() != manifest["files"][".tools/qdrant"]:
                raise RuntimeError("Qdrant binary checksum mismatch")
            binary.write_bytes(data)
            binary.chmod(0o755)
    print("Pinned model and Qdrant assets verified; no runtime records or keys were changed.")


if __name__ == "__main__":
    main()
