"""Native platform and encrypted-vault checks must fail closed."""

import hashlib
import json
from pathlib import Path

import pytest

from edgemed import linux_vault, security
from edgemed.operations import preflight


def test_linux_vault_rejects_an_unmounted_directory(tmp_path):
    with pytest.raises(RuntimeError, match="independently mounted"):
        linux_vault.verify_luks_mount(tmp_path)


def test_linux_vault_requires_exact_luks2_mapper_and_private_mount(tmp_path, monkeypatch):
    original_mount = Path.is_mount
    monkeypatch.setattr(Path, "is_mount", lambda self: self == tmp_path or original_mount(self))
    monkeypatch.setattr(linux_vault, "_mount_source", lambda _: "/dev/mapper/edgemed-vault")
    monkeypatch.setattr(linux_vault, "_mapper_uuid", lambda _: "CRYPT-LUKS2-test-edgemed-vault")
    assert linux_vault.verify_luks_mount(tmp_path)
    monkeypatch.setattr(linux_vault, "_mapper_uuid", lambda _: "CRYPT-PLAIN-test")
    with pytest.raises(RuntimeError, match="LUKS2"):
        linux_vault.verify_luks_mount(tmp_path)
    monkeypatch.setattr(linux_vault, "_mapper_uuid", lambda _: "CRYPT-LUKS2-test-edgemed-vault")
    monkeypatch.setattr(linux_vault, "_mount_source", lambda _: "/dev/mapper/other")
    with pytest.raises(RuntimeError, match="configured LUKS mapper"):
        linux_vault.verify_luks_mount(tmp_path)


def test_linux_rejects_non_system_keyring(monkeypatch):
    import keyring

    class PlaintextBackend:
        pass

    monkeypatch.setattr(security.sys, "platform", "linux")
    monkeypatch.setattr(keyring, "get_keyring", lambda: PlaintextBackend())
    with pytest.raises(RuntimeError, match="plaintext fallback is disabled"):
        security.protected_keyring()


def test_preflight_checks_native_binary_for_current_target(tmp_path, monkeypatch):
    import edgemed.cli as cli
    import edgemed.operations as operations

    monkeypatch.setattr(cli, "verify_vault", lambda: True)
    monkeypatch.setattr(operations, "target", lambda: "macos-x86_64")
    model = tmp_path / "model.onnx"
    model.write_bytes(b"synthetic model")
    binary = tmp_path / ".tools/qdrant"
    binary.parent.mkdir()
    binary.write_bytes(b"wrong binary")
    (tmp_path / "assets-manifest.json").write_text(
        json.dumps(
            {
                "files": {"model.onnx": hashlib.sha256(model.read_bytes()).hexdigest()},
                "qdrant_binaries": {"macos-x86_64": {"binary_sha256": "0" * 64}},
            }
        )
    )
    with pytest.raises(RuntimeError, match="Qdrant binary missing or checksum mismatch"):
        preflight(tmp_path)
