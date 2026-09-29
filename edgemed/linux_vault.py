"""Fail-closed verification of an operator-mounted Linux LUKS volume."""

import os
import re
import subprocess
from pathlib import Path


def _mount_source(vault):
    return subprocess.run(
        ["findmnt", "-n", "-o", "SOURCE", "--mountpoint", str(vault)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _mapper_uuid(device):
    metadata = os.stat(device)
    path = Path(f"/sys/dev/block/{os.major(metadata.st_rdev)}:{os.minor(metadata.st_rdev)}/dm/uuid")
    return path.read_text().strip() if path.is_file() else ""


def verify_luks_mount(vault: Path):
    mapper = os.environ.get("EDGEMED_LUKS_MAPPER", "edgemed-vault")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", mapper):
        raise RuntimeError("Invalid EDGEMED_LUKS_MAPPER")
    if vault.is_symlink() or not vault.is_mount():
        raise RuntimeError("Linux vault is not an independently mounted LUKS volume")
    mount = _mount_source(vault)
    expected = Path("/dev/mapper") / mapper
    if not mount.startswith("/dev/") or Path(mount).resolve() != expected.resolve():
        raise RuntimeError("Vault mount is not backed by the configured LUKS mapper")
    if not _mapper_uuid(expected).startswith("CRYPT-LUKS2-"):
        raise RuntimeError("Vault device is not a verifiable LUKS2 mapper")
    metadata = vault.stat()
    euid = getattr(os, "geteuid", lambda: metadata.st_uid)()
    mode_leak = (metadata.st_mode & 0o077) if hasattr(os, "geteuid") else 0
    if metadata.st_uid != euid or mode_leak:
        raise RuntimeError("Vault mount must be owned by this user and accessible only to this user")
    return True
