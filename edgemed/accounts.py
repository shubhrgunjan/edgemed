"""Local staff accounts and workspace identities for the synthetic LAN demo."""

import re
import secrets

from .security import PASSWORDS

NAME = re.compile(r"^[a-z][a-z0-9_-]{2,31}$")


def add(secret, username, workspace, role="clinician"):
    if not NAME.fullmatch(username) or username == "operator":
        raise ValueError("Username must be 3-32 lowercase letters, digits, _ or - and cannot be operator")
    if not NAME.fullmatch(workspace) or workspace == "operator" or workspace.startswith("personal"):
        raise ValueError("Use a named workspace such as ward-a; operator and personal are reserved")
    if role not in ("clinician", "admin"):
        raise ValueError("Role must be clinician or admin")
    if username in secret["operators"]:
        raise ValueError("Staff username already exists")
    password = secrets.token_urlsafe(24)
    secret["operators"][username] = {
        "password_hash": PASSWORDS.hash(password),
        "owner": workspace,
        "role": role,
        "disabled": False,
    }
    return password


def disable(secret, username):
    if username == "operator":
        raise ValueError("The bootstrap operator cannot be disabled by this demo command")
    if username not in secret["operators"]:
        raise ValueError("Unknown staff username")
    secret["operators"][username]["disabled"] = True


def scopes(identity):
    workspace = identity["owner"]
    username = identity["username"]
    if workspace == "operator" and username == "operator":
        return (workspace,)
    return (workspace, f"personal:{username}")


def record_owner(identity, privacy):
    if privacy == "HIGHLY_SENSITIVE" and identity["username"] != "operator":
        return f"personal:{identity['username']}"
    return identity["owner"]
