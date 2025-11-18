"""Authentication utilities for Password Manager."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict, Optional

from secure_password_manager.utils.config import get_setting
from secure_password_manager.utils.paths import get_auth_json_path


DEFAULT_AUTH_ITERATIONS = 390_000


def _get_auth_file() -> str:
    """Get the auth file path."""
    return str(get_auth_json_path())


def _pbkdf2(password: str, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )


def _load_auth_data() -> Optional[Dict[str, Any]]:
    auth_file = _get_auth_file()
    if not os.path.exists(auth_file):
        return None
    try:
        with open(auth_file, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _write_auth_data(data: Dict[str, Any]) -> None:
    auth_file = _get_auth_file()
    with open(auth_file, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)


def _upgrade_legacy_hash(password: str, legacy_hash: str) -> bool:
    """Upgrade SHA-256 legacy hashes to PBKDF2 after verifying password."""
    if hashlib.sha256(password.encode("utf-8")).hexdigest() != legacy_hash:
        return False
    # Re-write file using PBKDF2 parameters
    set_master_password(password)
    return True


def set_master_password(password: str) -> None:
    """Set or update the master password using PBKDF2."""
    iterations = int(
        get_setting("key_management.kdf_iterations", DEFAULT_AUTH_ITERATIONS)
    )
    salt = os.urandom(16)
    derived = _pbkdf2(password, salt, iterations)

    record = {
        "version": 2,
        "kdf": {
            "algorithm": "PBKDF2-HMAC-SHA256",
            "iterations": iterations,
            "salt": base64.b64encode(salt).decode("ascii"),
        },
        "hash": base64.b64encode(derived).decode("ascii"),
        "updated_at": int(time.time()),
    }
    _write_auth_data(record)


def _verify_pbkdf2(record: Dict[str, Any], password: str) -> bool:
    kdf = record.get("kdf", {})
    try:
        iterations = int(kdf.get("iterations"))
        salt = base64.b64decode(kdf["salt"])
        expected = base64.b64decode(record["hash"])
    except (KeyError, ValueError, TypeError, base64.binascii.Error):
        return False

    computed = _pbkdf2(password, salt, iterations)
    return hmac.compare_digest(computed, expected)


def authenticate(password: str) -> bool:
    """Authenticate with the master password."""
    record = _load_auth_data()
    if not record:
        return False

    if "hash" in record and "kdf" in record:
        return _verify_pbkdf2(record, password)

    # Legacy SHA-256 hash support
    legacy_hash = record.get("master_hash")
    if isinstance(legacy_hash, str):
        return _upgrade_legacy_hash(password, legacy_hash)
    return False
