"""Authentication utilities for Password Manager."""

import hashlib
import json
import os

AUTH_FILE = "auth.json"


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    salt = os.urandom(32)  # 32-byte salt
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100000,  # Number of iterations
    )
    # Store salt and key together
    return salt.hex() + ":" + key.hex()


def verify_password(stored_hash: str, provided_password: str) -> bool:
    """Verify a password against its stored hash."""
    salt_hex, key_hex = stored_hash.split(":")
    salt = bytes.fromhex(salt_hex)
    stored_key = bytes.fromhex(key_hex)

    # Hash the provided password with the same salt
    key = hashlib.pbkdf2_hmac(
        "sha256",
        provided_password.encode("utf-8"),
        salt,
        100000,  # Same number of iterations
    )

    # Compare in constant time to prevent timing attacks
    return key == stored_key


def set_master_password(password: str) -> None:
    """Set or update the master password."""
    password_hash = hash_password(password)
    with open(AUTH_FILE, "w") as f:
        json.dump({"master_hash": password_hash}, f)


def authenticate(password: str) -> bool:
    """Authenticate with the master password."""
    if not os.path.exists(AUTH_FILE):
        # First time setup
        set_master_password(password)
        return True

    with open(AUTH_FILE, "r") as f:
        auth_data = json.load(f)

    return verify_password(auth_data["master_hash"], password)
