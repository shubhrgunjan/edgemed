"""Verify an encrypted cold backup on this Mac without exporting its keys."""

import json
import argparse
import subprocess
from pathlib import Path

import keyring
from sqlcipher3 import dbapi2 as sqlite

from edgemed.cli import RUNTIME, VAULT, SERVICE
from edgemed.security import load_secret


def read(root, profile):
    path = root / profile / "data/memory.db"
    db = sqlite.connect(path.as_uri() + ("?mode=ro" if root == VAULT else "?mode=ro&immutable=1"), uri=True)
    key = load_secret(profile)["db_key"]
    db.execute(f'''PRAGMA key = "x'{key}'"''')
    try:
        return {
            table: sorted(map(tuple, db.execute("SELECT * FROM " + table)))
            for table in ("memories", "revisions", "outbox", "inbox", "events")
        }
    finally:
        db.close()


def main():
    if SERVICE == "org.lex.edgemed.local":
        raise RuntimeError("Recovery rehearsal requires an isolated runtime")
    parser = argparse.ArgumentParser()
    parser.add_argument("--backup", type=Path, default=RUNTIME / "backup-check")
    image = parser.parse_args().backup / "data.sparsebundle"
    mount = RUNTIME / "restore-check"
    mount.mkdir(exist_ok=True, mode=0o700)
    password = keyring.get_password(SERVICE, "vault")
    if password is None:
        raise RuntimeError("Vault key unavailable")
    expected = {profile: read(VAULT, profile) for profile in ("edge-a", "edge-b", "central")}
    subprocess.run(
        ["hdiutil", "attach", "-readonly", "-nobrowse", "-mountpoint", str(mount), "-stdinpass", str(image)],
        input=password.encode(),
        capture_output=True,
        check=True,
    )
    try:
        actual = {profile: read(mount, profile) for profile in expected}
        assert actual == expected, "Restored records, revisions, queues or audit history differ"
        report = {
            "encrypted_restore": "passed",
            "scope": "same Mac with original Keychain material",
            "profiles": {
                profile: {table: len(rows) for table, rows in data.items()}
                for profile, data in actual.items()
            },
        }
        Path("docs/recovery-results.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
    finally:
        subprocess.run(["hdiutil", "detach", str(mount)], capture_output=True, check=True)


if __name__ == "__main__":
    main()
