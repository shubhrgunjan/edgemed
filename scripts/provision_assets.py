"""Explicit online provisioning of pinned public assets. Runtime never downloads models."""

import argparse
import hashlib
import json
import os
import sys
import tarfile
import tempfile
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from edgemed.platforms import target  # noqa: E402

REVISION = "aa8f8b060edb00e03bfdd08813a2949946c8ba55"


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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model-only",
        action="store_true",
        help="Provision the pinned ONNX model without a native Qdrant server binary",
    )
    args = parser.parse_args(argv)
    manifest = json.loads((ROOT / "assets-manifest.json").read_text())
    binary_spec = None if args.model_only else manifest["qdrant_binaries"].get(target())
    if not args.model_only and binary_spec is None:
        raise RuntimeError("No verified Qdrant binary for this platform; use --model-only")
    for name, digest in manifest["files"].items():
        if "/snapshots/" in name:
            filename = Path(name).name
            download(
                f"https://huggingface.co/Qdrant/bge-small-en-v1.5-onnx-Q/resolve/{REVISION}/{filename}",
                ROOT / name,
                digest,
            )
    if args.model_only:
        print("Pinned model assets verified; runtime records, keys and server binaries were not changed.")
        return
    tools = ROOT / ".tools"
    tools.mkdir(exist_ok=True)
    binary = tools / "qdrant"
    if not binary.is_file() or hashlib.sha256(binary.read_bytes()).hexdigest() != binary_spec["binary_sha256"]:
        with tempfile.TemporaryDirectory(dir=tools) as temp:
            archive = Path(temp) / "qdrant.tar.gz"
            download(
                f"https://github.com/qdrant/qdrant/releases/download/v{manifest['qdrant_server']}/"
                + binary_spec["archive"],
                archive,
                binary_spec["archive_sha256"],
            )
            with tarfile.open(archive) as tar:
                members = [m for m in tar.getmembers() if m.isfile() and Path(m.name).name == "qdrant"]
                if len(members) != 1 or members[0].size > 256 * 1024 * 1024:
                    raise RuntimeError("Unexpected release archive")
                data = tar.extractfile(members[0]).read()
            if hashlib.sha256(data).hexdigest() != binary_spec["binary_sha256"]:
                raise RuntimeError("Qdrant binary checksum mismatch")
            staged = Path(temp) / "qdrant"
            staged.write_bytes(data)
            staged.chmod(0o755)
            os.replace(staged, binary)
    print("Pinned model and Qdrant assets verified; no runtime records or keys were changed.")


if __name__ == "__main__":
    main()
