"""Cryptographic utilities for Password Manager."""

import base64
import hmac
import json
import os
import time
from typing import Dict, Optional, Tuple

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from secure_password_manager.utils.paths import (
    get_crypto_salt_path,
    get_secret_key_enc_path,
    get_secret_key_path,
)

# Constants
CURRENT_KDF_VERSION = 1
DEFAULT_ITERATIONS = 100_000

# In-memory context for master password (set at login)
_MASTER_PW_CONTEXT: Optional[str] = None


def _now_ts() -> int:
    return int(time.time())


def _get_key_file() -> str:
    """Get the secret key file path."""
    return str(get_secret_key_path())


def _get_enc_key_file() -> str:
    """Get the encrypted secret key file path."""
    return str(get_secret_key_enc_path())


def _get_salt_file() -> str:
    """Get the salt file path."""
    return str(get_crypto_salt_path())


def generate_salt() -> bytes:
    """Generate and save a salt for key derivation (with versioned metadata)."""
    salt = os.urandom(16)
    data = {
        "kdf": "PBKDF2HMAC",
        "version": CURRENT_KDF_VERSION,
        "iterations": DEFAULT_ITERATIONS,
        "salt": base64.b64encode(salt).decode("ascii"),
        "updated_at": _now_ts(),
    }
    # Store JSON for forward compatibility
    with open(_get_salt_file(), "w") as salt_file:
        json.dump(data, salt_file)
    return salt


def load_kdf_params() -> Tuple[bytes, int, int]:
    """Load KDF salt, iterations, and version. Accepts legacy raw salt file."""
    salt_file = _get_salt_file()
    if not os.path.exists(salt_file):
        salt = generate_salt()
        return salt, DEFAULT_ITERATIONS, CURRENT_KDF_VERSION

    # Try JSON format first
    try:
        with open(salt_file) as f:
            data = json.load(f)
        salt_b = base64.b64decode(data["salt"])
        iterations = int(data.get("iterations", DEFAULT_ITERATIONS))
        version = int(data.get("version", CURRENT_KDF_VERSION))
        return salt_b, iterations, version
    except Exception:
        # Legacy: raw salt bytes
        with open(salt_file, "rb") as f:
            salt_b = f.read()
        # Migrate to JSON without changing the salt value
        data = {
            "kdf": "PBKDF2HMAC",
            "version": CURRENT_KDF_VERSION,
            "iterations": DEFAULT_ITERATIONS,
            "salt": base64.b64encode(salt_b).decode("ascii"),
            "updated_at": _now_ts(),
        }
        try:
            with open(salt_file, "w") as wf:
                json.dump(data, wf)
        except Exception:
            # Non-fatal; continue with legacy params
            pass
        return salt_b, DEFAULT_ITERATIONS, CURRENT_KDF_VERSION


def derive_key_from_password(password: str) -> bytes:
    """Derive a Fernet key (urlsafe base64) from the master password using PBKDF2.

    Backward compatible wrapper that uses current KDF params.
    """
    salt, iterations, _ = load_kdf_params()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
    return key


def derive_keys_from_password(password: str) -> Tuple[bytes, bytes, Dict]:
    """Derive separate encryption (Fernet) and HMAC keys from password.

    Returns (fernet_key_b64, hmac_key_bytes, kdf_meta_dict)
    """
    salt, iterations, version = load_kdf_params()
    # Derive 64 bytes and split into two 32-byte keys
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=64,
        salt=salt,
        iterations=iterations,
    )
    key_material = kdf.derive(password.encode("utf-8"))
    enc_key = base64.urlsafe_b64encode(key_material[:32])
    mac_key = key_material[32:]
    meta = {
        "kdf": "PBKDF2HMAC",
        "version": version,
        "iterations": iterations,
        "salt": base64.b64encode(salt).decode("ascii"),
    }
    return enc_key, mac_key, meta


def set_master_password_context(password: Optional[str]) -> None:
    """Set or clear the in-memory master password context (used to unwrap key)."""
    global _MASTER_PW_CONTEXT
    _MASTER_PW_CONTEXT = password


def is_key_protected() -> bool:
    """Return True if the encryption key is stored in protected form."""
    return os.path.exists(_get_enc_key_file())


def generate_key() -> None:
    """Generate and save a plaintext encryption key (legacy/default)."""
    key = Fernet.generate_key()
    with open(_get_key_file(), "wb") as key_file:
        key_file.write(key)


def protect_key_with_master_password(master_password: Optional[str] = None) -> bool:
    """Protect the secret.key by wrapping it with a KEK derived from the master password.

    Creates ENC_KEY_FILE and removes/backs up KEY_FILE. Returns True on success.
    """
    pw = master_password or _MASTER_PW_CONTEXT
    if not pw:
        raise ValueError("Master password context not set")

    key_file = _get_key_file()
    enc_key_file = _get_enc_key_file()

    # Load or generate the plaintext key
    if not os.path.exists(key_file):
        generate_key()
    with open(key_file, "rb") as f:
        key_bytes = f.read()

    enc_key, mac_key, kdf_meta = derive_keys_from_password(pw)
    token = Fernet(enc_key).encrypt(key_bytes)

    # Build envelope with HMAC for integrity
    mac = hmac.new(mac_key, token, digestmod="sha256").hexdigest()
    envelope = {
        "format": "spm-key",
        "version": "1.0",
        "kdf": kdf_meta,
        "ciphertext": base64.b64encode(token).decode("ascii"),
        "hmac": mac,
        "hmac_alg": "HMAC-SHA256",
    }

    tmp_path = enc_key_file + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(envelope, f)
    os.replace(tmp_path, enc_key_file)

    # Backup and remove plaintext key
    try:
        os.replace(key_file, f"{key_file}.bak{_now_ts()}")
    except Exception:
        # If replace fails, try to remove
        try:
            os.remove(key_file)
        except Exception:
            pass
    return True


def unprotect_key(master_password: Optional[str] = None) -> bool:
    """Unwrap the protected key and write back to KEY_FILE (plaintext)."""
    pw = master_password or _MASTER_PW_CONTEXT
    if not pw:
        raise ValueError("Master password context not set")

    enc_key_file = _get_enc_key_file()
    key_file = _get_key_file()

    if not os.path.exists(enc_key_file):
        return True  # Nothing to do

    with open(enc_key_file) as f:
        envelope = json.load(f)

    enc_key, mac_key, _ = derive_keys_from_password(pw)
    token = base64.b64decode(envelope["ciphertext"])
    expected_mac = envelope.get("hmac")
    mac = hmac.new(mac_key, token, digestmod="sha256").hexdigest()
    if not hmac.compare_digest(mac, expected_mac):
        raise ValueError("Protected key integrity check failed")

    key_bytes = Fernet(enc_key).decrypt(token)

    tmp = key_file + ".tmp"
    with open(tmp, "wb") as f:
        f.write(key_bytes)
    os.replace(tmp, key_file)

    # Optionally keep ENC file as backup
    return True


def load_key() -> bytes:
    """Load the encryption key from file or protected envelope.

    If ENC_KEY_FILE exists, requires the master password context to be set.
    """
    enc_key_file = _get_enc_key_file()
    key_file = _get_key_file()

    if os.path.exists(enc_key_file):
        if not _MASTER_PW_CONTEXT:
            raise ValueError(
                "Encrypted key present. Set master password context before loading key."
            )
        with open(enc_key_file) as f:
            envelope = json.load(f)
        token = base64.b64decode(envelope["ciphertext"])
        enc_key, mac_key, _ = derive_keys_from_password(_MASTER_PW_CONTEXT)
        mac = hmac.new(mac_key, token, digestmod="sha256").hexdigest()
        if not hmac.compare_digest(mac, envelope.get("hmac", "")):
            raise ValueError("Key integrity verification failed")
        return Fernet(enc_key).decrypt(token)

    # Fallback to plaintext key
    if not os.path.exists(key_file):
        generate_key()
    with open(key_file, "rb") as key_file_obj:
        return key_file_obj.read()


# Encryption/Decryption for vault (file key) or with a provided master password for exports


def encrypt_password(password: str, master_password: Optional[str] = None) -> bytes:
    """
    Encrypt a password string to bytes.

    Args:
        password: The password to encrypt
        master_password: If provided, use password-derived key (for exports); else use file key
    """
    if master_password:
        key = derive_key_from_password(master_password)
    else:
        key = load_key()
    f = Fernet(key)
    return f.encrypt(password.encode("utf-8"))


def decrypt_password(
    encrypted_password: bytes, master_password: Optional[str] = None
) -> str:
    """
    Decrypt an encrypted password bytes to string.

    Args:
        encrypted_password: The encrypted password to decrypt
        master_password: If provided, use password-derived key (for exports); else use file key
    """
    try:
        if master_password:
            key = derive_key_from_password(master_password)
        else:
            key = load_key()
        f = Fernet(key)
        return f.decrypt(encrypted_password).decode("utf-8")
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")


# Envelope helpers for export/import with integrity HMAC


def encrypt_with_password_envelope(plaintext: str, password: str) -> bytes:
    """Encrypt plaintext with Fernet using a password-derived key and wrap with HMAC envelope.

    Returns bytes containing a JSON envelope.
    """
    enc_key, mac_key, kdf_meta = derive_keys_from_password(password)
    token = Fernet(enc_key).encrypt(plaintext.encode("utf-8"))
    mac = hmac.new(mac_key, token, digestmod="sha256").hexdigest()
    envelope = {
        "format": "spm-export",
        "version": "2.1",
        "kdf": kdf_meta,
        "ciphertext": base64.b64encode(token).decode("ascii"),
        "hmac": mac,
        "hmac_alg": "HMAC-SHA256",
    }
    return json.dumps(envelope).encode("utf-8")


def decrypt_with_password_envelope(blob: bytes, password: str) -> str:
    """Decrypt either a raw Fernet token (legacy) or a JSON envelope.

    Verifies HMAC when envelope is present.
    """
    # Try parse as JSON envelope
    integrity_error = False
    try:
        data = json.loads(blob.decode("utf-8"))
        if isinstance(data, dict) and data.get("format") == "spm-export":
            token = base64.b64decode(data["ciphertext"])  # bytes
            enc_key, mac_key, _ = derive_keys_from_password(password)
            mac = hmac.new(mac_key, token, digestmod="sha256").hexdigest()
            if not hmac.compare_digest(mac, data.get("hmac", "")):
                # Mark as integrity error to re-raise later
                integrity_error = True
                raise ValueError("Backup integrity verification failed")
            plaintext = Fernet(enc_key).decrypt(token).decode("utf-8")
            return plaintext
    except Exception as e:
        # Re-raise if it's an integrity verification failure
        if integrity_error:
            raise
        # Not an envelope; fall back to legacy raw token
        pass

    # Legacy format: blob is a raw Fernet token
    return decrypt_password(blob, master_password=password)
