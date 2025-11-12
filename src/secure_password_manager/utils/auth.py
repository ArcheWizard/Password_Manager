"""Authentication utilities for Password Manager."""

import hashlib
import json
import os

from secure_password_manager.utils.paths import get_auth_json_path


def _get_auth_file() -> str:
    """Get the auth file path."""
    return str(get_auth_json_path())


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(stored_hash: str, provided_password: str) -> bool:
    """Verify a password against its stored hash."""
    return stored_hash == hash_password(provided_password)


def set_master_password(password: str) -> None:
    """Set or update the master password."""
    hashed = hash_password(password)
    auth_file = _get_auth_file()
    with open(auth_file, "w") as f:
        json.dump({"master_hash": hashed}, f)


def authenticate(password: str) -> bool:
    """Authenticate with the master password."""
    auth_file = _get_auth_file()
    if not os.path.exists(auth_file):
        return False

    with open(auth_file, "r") as f:
        auth_data = json.load(f)

    return verify_password(auth_data["master_hash"], password)
