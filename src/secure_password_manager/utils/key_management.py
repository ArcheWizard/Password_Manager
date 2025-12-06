"""Key management helpers for switching encryption modes."""

from __future__ import annotations

import hashlib
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List

from cryptography.fernet import Fernet

from secure_password_manager.utils import config
from secure_password_manager.utils.auth import authenticate, set_master_password
from secure_password_manager.utils.config import KEY_MODE_FILE, KEY_MODE_PASSWORD
from secure_password_manager.utils.crypto import (
    decrypt_password,
    derive_key_from_password,
    encrypt_password,
    generate_key,
    is_key_protected,
    load_kdf_params,
    protect_key_with_master_password,
    save_kdf_params,
    unprotect_key,
)
from secure_password_manager.utils.paths import (
    get_database_path,
    get_secret_key_enc_path,
    get_secret_key_path,
)


class KeyManagementError(RuntimeError):
    """Raised when key management operations fail."""


def get_key_mode() -> str:
    """Return the active key management mode."""
    return config.get_setting("key_management.mode", KEY_MODE_FILE)


def is_password_mode() -> bool:
    """Return ``True`` when master-password-derived mode is active."""
    return get_key_mode() == KEY_MODE_PASSWORD


def _delete_file(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        return
    except OSError:
        # As a fallback, overwrite with zero bytes and remove
        try:
            path.write_bytes(b"")
            path.unlink()
        except Exception:
            pass


def _cleanup_secret_keys() -> None:
    for path in (get_secret_key_path(), get_secret_key_enc_path()):
        _delete_file(path)


def _reencrypt_vault(
    source_mode: str,
    target_mode: str,
    master_password: str,
) -> int:
    db_path = str(get_database_path())
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, password FROM passwords")
    rows = cursor.fetchall()

    updated = 0
    try:
        for entry_id, encrypted in rows:
            plaintext = decrypt_password(
                encrypted,
                master_password=(
                    master_password if source_mode == KEY_MODE_PASSWORD else None
                ),
                force_mode=source_mode,
            )
            ciphertext = encrypt_password(
                plaintext,
                master_password=(
                    master_password if target_mode == KEY_MODE_PASSWORD else None
                ),
                force_mode=target_mode,
            )
            cursor.execute(
                "UPDATE passwords SET password = ?, updated_at = ? WHERE id = ?",
                (ciphertext, int(time.time()), entry_id),
            )
            updated += 1
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return updated


def _reencrypt_password_mode_vault(
    master_password: str,
    old_salt: bytes,
    old_iterations: int,
    new_salt: bytes,
    new_iterations: int,
) -> int:
    old_key = derive_key_from_password(
        master_password, salt=old_salt, iterations=old_iterations
    )
    new_key = derive_key_from_password(
        master_password, salt=new_salt, iterations=new_iterations
    )
    old_cipher = Fernet(old_key)
    new_cipher = Fernet(new_key)

    db_path = str(get_database_path())
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, password FROM passwords")
    rows = cursor.fetchall()
    updated = 0
    try:
        for entry_id, encrypted in rows:
            plaintext = old_cipher.decrypt(encrypted)
            ciphertext = new_cipher.encrypt(plaintext)
            cursor.execute(
                "UPDATE passwords SET password = ?, updated_at = ? WHERE id = ?",
                (ciphertext, int(time.time()), entry_id),
            )
            updated += 1
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return updated


def switch_key_mode(target_mode: str, master_password: str) -> Dict[str, str | int]:
    """Switch between file-key and password-derived modes, re-encrypting the vault."""
    if target_mode not in (KEY_MODE_FILE, KEY_MODE_PASSWORD):
        raise KeyManagementError(f"Unsupported key mode: {target_mode}")

    current_mode = get_key_mode()
    if current_mode == target_mode:
        return {"mode": target_mode, "entries_reencrypted": 0}

    if not master_password:
        raise KeyManagementError("Master password is required to change key mode")

    if target_mode == KEY_MODE_FILE:
        _cleanup_secret_keys()
        generate_key()
    try:
        updated = _reencrypt_vault(current_mode, target_mode, master_password)
    except Exception as exc:  # pragma: no cover - re-raised with context
        raise KeyManagementError("Failed to re-encrypt vault") from exc

    if target_mode == KEY_MODE_PASSWORD:
        _cleanup_secret_keys()

    config.update_settings({"key_management": {"mode": target_mode}})
    return {"mode": target_mode, "entries_reencrypted": updated}


def benchmark_kdf(
    target_ms: int = 350, max_iterations: int = 2_000_000
) -> Dict[str, Any]:
    """Benchmark PBKDF2-HMAC-SHA256 and recommend iterations for the target runtime."""
    if target_ms < 50:
        raise KeyManagementError("Target runtime must be at least 50 ms")

    password = os.urandom(32)
    salt = os.urandom(16)
    iterations = 100_000
    samples: List[Dict[str, float | int]] = []

    while iterations <= max_iterations:
        start = time.perf_counter()
        hashlib.pbkdf2_hmac("sha256", password, salt, iterations, dklen=32)
        duration_ms = (time.perf_counter() - start) * 1000
        samples.append({"iterations": iterations, "duration_ms": duration_ms})
        if duration_ms >= target_ms * 0.9 or iterations == max_iterations:
            break
        scale = target_ms / max(duration_ms, 1.0)
        next_iterations = int(iterations * scale)
        iterations = min(max_iterations, max(iterations + 10_000, next_iterations))

    result = samples[-1] if samples else {"iterations": iterations, "duration_ms": 0.0}
    return {
        "target_ms": target_ms,
        "samples": samples,
        "recommended_iterations": int(result["iterations"]),
        "estimated_duration_ms": float(result["duration_ms"]),
    }


def apply_kdf_parameters(
    master_password: str,
    iterations: int,
    salt_bytes: int = 16,
) -> Dict[str, Any]:
    """Apply new PBKDF2 parameters across auth storage and encryption context."""
    if iterations < 100_000:
        raise KeyManagementError("KDF iterations must be at least 100,000")
    if salt_bytes < 16:
        raise KeyManagementError("Salt size must be at least 16 bytes")
    if not master_password:
        raise KeyManagementError("Master password is required")
    if not authenticate(master_password):
        raise KeyManagementError("Master password verification failed")

    old_salt, old_iterations, version = load_kdf_params()
    password_mode_active = is_password_mode()
    key_was_protected = is_key_protected()
    reencrypted_entries = 0
    new_salt = os.urandom(salt_bytes)

    try:
        if key_was_protected:
            unprotect_key(master_password)

        if password_mode_active:
            reencrypted_entries = _reencrypt_password_mode_vault(
                master_password,
                old_salt,
                old_iterations,
                new_salt,
                iterations,
            )

        save_kdf_params(new_salt, iterations, version)
        config.update_settings({"key_management": {"kdf_iterations": iterations}})
        set_master_password(master_password)

        if key_was_protected:
            protect_key_with_master_password(master_password)

    except Exception as exc:
        # Attempt best-effort recovery if possible
        if password_mode_active and reencrypted_entries:
            try:
                _reencrypt_password_mode_vault(
                    master_password,
                    new_salt,
                    iterations,
                    old_salt,
                    old_iterations,
                )
            except Exception:
                pass
        if key_was_protected:
            try:
                protect_key_with_master_password(master_password)
            except Exception:
                pass
        raise KeyManagementError("Failed to apply KDF parameters") from exc

    return {
        "iterations": iterations,
        "salt_bytes": salt_bytes,
        "entries_reencrypted": reencrypted_entries,
        "password_mode": password_mode_active,
    }
