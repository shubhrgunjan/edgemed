import base64
import hashlib
import hmac
import json
import os
import secrets
import sys
import time
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

PASSWORDS = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
SERVICE = os.environ.get("EDGEMED_KEYCHAIN_SERVICE", "org.lex.edgemed.local")


def protected_keyring():
    import keyring

    if sys.platform == "linux":
        backend = keyring.get_keyring()
        module = type(backend).__module__
        if module not in {"keyring.backends.SecretService", "keyring.backends.kwallet"}:
            raise RuntimeError("Linux requires an unlocked Secret Service or KWallet keyring; plaintext fallback is disabled")
    return keyring


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sign(value, private_hex):
    key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_hex))
    return base64.b64encode(key.sign(canonical(value))).decode()


def verify(value, signature, public_hex):
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_hex)).verify(
            base64.b64decode(signature, validate=True), canonical(value)
        )
    except Exception as exc:
        raise ValueError("Invalid signature") from exc


def new_identity():
    key = Ed25519PrivateKey.generate()
    return key.private_bytes_raw().hex(), key.public_key().public_bytes_raw().hex()


def load_secret(profile):
    keyring = protected_keyring()
    value = keyring.get_password(SERVICE, profile)
    if value is None:
        raise RuntimeError("Keychain material unavailable. Run setup; plaintext fallback is disabled.")
    return json.loads(value)


def save_secret(profile, data):
    keyring = protected_keyring()
    keyring.set_password(SERVICE, profile, json.dumps(data))


def private_write(path: Path, data: str):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = __import__("os").open(
        path, __import__("os").O_WRONLY | __import__("os").O_CREAT | __import__("os").O_TRUNC, 0o600
    )
    if hasattr(os, "fchmod"):
        os.fchmod(fd, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(data)


def password_valid(encoded, password):
    try:
        return PASSWORDS.verify(encoded, password)
    except VerificationError:
        return False


def issue_session():
    return secrets.token_urlsafe(32), secrets.token_urlsafe(32), time.time() + 1800


def audit_mac(key, previous, payload):
    return hmac.new(bytes.fromhex(key), previous.encode() + canonical(payload), hashlib.sha256).hexdigest()
