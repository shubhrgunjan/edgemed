"""Read-only preflight and cold encrypted-container backup; no plaintext key export."""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from .platforms import target


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def tree_manifest(root):
    return {str(p.relative_to(root)): file_hash(p) for p in sorted(root.rglob("*")) if p.is_file()}


def preflight(project):
    from .cli import verify_vault, config
    from .security import load_secret

    verify_vault()
    manifest = json.loads((project / "assets-manifest.json").read_text())
    for relative, expected in manifest["files"].items():
        path = project / relative
        if not path.is_file() or file_hash(path) != expected:
            raise RuntimeError(f"Asset missing or checksum mismatch: {relative}")
    binary = project / ".tools/qdrant"
    expected_binary = manifest["qdrant_binaries"][target()]["binary_sha256"]
    if not binary.is_file() or file_hash(binary) != expected_binary:
        raise RuntimeError("Pinned Qdrant binary missing or checksum mismatch for this platform")
    if not (project / "frontend/dist/index.html").is_file():
        raise RuntimeError("Build frontend before starting")
    for profile in ("edge-a", "edge-b", "central"):
        cfg, secret = config(profile), load_secret(profile)
        if not secret.get("db_key") or not Path(cfg["cert"]).is_file() or not Path(cfg["key"]).is_file():
            raise RuntimeError("Profile key material incomplete")
    return {
        "vault": "encrypted and mounted",
        "profiles": 3,
        "asset_hashes": len(manifest["files"]) + 1,
        "frontend": "built",
        "network_access": "not required",
        "platform": target(),
    }


def cold_backup(image, destination):
    if sys.platform != "darwin":
        raise RuntimeError("Linux backup needs an offline LUKS volume snapshot; this command supports macOS only")
    import plistlib

    info = plistlib.loads(subprocess.check_output(["hdiutil", "info", "-plist"]))
    if any(Path(i.get("image-path", "")).resolve() == image.resolve() for i in info.get("images", [])):
        raise RuntimeError("Unmount the encrypted image before backup")
    if not image.is_dir() or destination.exists():
        raise RuntimeError("A source image and a new destination directory are required")
    destination.mkdir(parents=True, mode=0o700)
    target = destination / "data.sparsebundle"
    shutil.copytree(image, target, symlinks=False)
    hashes = tree_manifest(image)
    if tree_manifest(target) != hashes:
        raise RuntimeError("Backup verification failed; do not use this copy")
    (destination / "checksums.json").write_text(json.dumps(hashes, indent=2) + "\n")
    return {
        "verified_files": len(hashes),
        "format": "encrypted sparsebundle",
        "key_recovery": "Requires original protected Keychain material; keys are not exported",
    }
