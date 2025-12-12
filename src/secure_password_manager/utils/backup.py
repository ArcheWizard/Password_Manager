"""Backup and restore utilities.

This module provides safe, atomic operations for:
- Exporting passwords to encrypted files
- Importing passwords from encrypted files
- Creating full system backups
- Restoring from backups

Key design principles:
1. One database connection per operation
2. Explicit transaction boundaries
3. Proper resource cleanup via context managers
4. Validation before mutation
5. Atomic operations with rollback on failure
"""

import contextlib
import json
import os
import shutil
import sqlite3
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from secure_password_manager.utils.crypto import (
    decrypt_password,
    decrypt_with_password_envelope,
    encrypt_password,
    encrypt_with_password_envelope,
)
from secure_password_manager.utils.database import add_category, get_categories, get_passwords
from secure_password_manager.utils.logger import log_error, log_info, log_warning
from secure_password_manager.utils.paths import (
    get_auth_json_path,
    get_crypto_salt_path,
    get_database_path,
    get_secret_key_path,
)


# Constants
EXPORT_VERSION = "2.0"
BACKUP_VERSION = "2.0"
DEFAULT_TIMEOUT = 30.0  # seconds


class BackupError(Exception):
    """Base exception for backup operations."""
    pass


class ImportError(Exception):
    """Base exception for import operations."""
    pass


# ============================================================================
# EXPORT OPERATIONS
# ============================================================================

def export_passwords(
    filename: str,
    master_password: str,
    include_notes: bool = True
) -> bool:
    """Export passwords to an encrypted file.

    Args:
        filename: Path to export file (will add .dat extension if missing)
        master_password: Password to encrypt the export
        include_notes: Whether to include notes field

    Returns:
        True if export succeeded, False otherwise

    Raises:
        BackupError: If export fails critically
    """
    try:
        # Ensure .dat extension
        if not filename.endswith('.dat'):
            filename = f"{filename}.dat"

        # Fetch all passwords (single query, one connection)
        passwords = get_passwords()

        if not passwords:
            log_warning("Export aborted: vault is empty")
            return False

        # Build export structure
        export_data = _build_export_data(passwords, include_notes)

        # Encrypt and write atomically
        _write_encrypted_export(filename, export_data, master_password)

        log_info(f"Exported {len(passwords)} passwords to {filename}")
        return True

    except Exception as e:
        log_error(f"Export failed: {e}")
        # Clean up partial file
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except OSError:
                pass
        return False


def _build_export_data(
    passwords: List[Tuple],
    include_notes: bool
) -> Dict:
    """Build the export data structure."""
    entries = []

    for entry in passwords:
        (
            entry_id,
            website,
            username,
            encrypted,
            category,
            notes,
            created_at,
            updated_at,
            expiry,
            favorite,
        ) = entry

        # Decrypt password
        password = decrypt_password(encrypted)

        # Build entry dict
        entry_data = {
            "website": website,
            "username": username,
            "password": password,
            "category": category,
            "created_at": created_at,
            "updated_at": updated_at,
            "favorite": bool(favorite),
        }

        if include_notes:
            entry_data["notes"] = notes or ""

        if expiry:
            entry_data["expiry_date"] = expiry

        entries.append(entry_data)

    # Get categories
    categories = get_categories()

    # Build final structure
    return {
        "metadata": {
            "version": EXPORT_VERSION,
            "exported_at": int(time.time()),
            "entry_count": len(entries),
        },
        "categories": [
            {"name": name, "color": color}
            for name, color in categories
        ],
        "entries": entries,
    }


def _write_encrypted_export(
    filename: str,
    data: Dict,
    master_password: str
) -> None:
    """Write encrypted export to file atomically."""
    # Serialize to JSON
    json_data = json.dumps(data, separators=(',', ':'))

    # Encrypt with envelope (includes HMAC)
    blob = encrypt_with_password_envelope(json_data, master_password)

    # Write atomically (write to temp, then move)
    temp_path = f"{filename}.tmp"
    try:
        with open(temp_path, 'wb') as f:
            f.write(blob)
        # Atomic move
        os.replace(temp_path, filename)
    except Exception as e:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise BackupError(f"Failed to write export: {e}") from e


# ============================================================================
# IMPORT OPERATIONS
# ============================================================================

def import_passwords(filename: str, master_password: str) -> int:
    """Import passwords from an encrypted file.

    Args:
        filename: Path to import file
        master_password: Password to decrypt the import

    Returns:
        Number of passwords successfully imported

    Raises:
        ImportError: If import fails critically
    """
    if not os.path.exists(filename):
        log_error(f"Import failed: file not found: {filename}")
        return 0

    try:
        # Read and decrypt file
        import_data = _read_encrypted_import(filename, master_password)

        # Validate structure
        entries, categories = _validate_import_data(import_data)

        if not entries:
            log_warning("Import file contains no entries")
            return 0

        # Import categories first
        _import_categories(categories)

        # Import passwords in single transaction
        imported_count = _import_entries(entries)

        # Get version from metadata if available (modern format)
        if isinstance(import_data, dict):
            version = import_data.get("metadata", {}).get("version", "1.0")
        else:
            version = "legacy"

        log_info(f"Imported {imported_count} passwords from {filename} (v{version})")

        return imported_count

    except Exception as e:
        log_error(f"Import failed: {e}")
        return 0


def _read_encrypted_import(filename: str, master_password: str) -> Dict:
    """Read and decrypt import file."""
    try:
        with open(filename, 'rb') as f:
            blob = f.read()

        json_data = decrypt_with_password_envelope(blob, master_password)
        return json.loads(json_data)

    except Exception as e:
        raise ImportError(f"Failed to decrypt import file: {e}") from e


def _validate_import_data(data: Dict) -> Tuple[List[Dict], List[Dict]]:
    """Validate import data structure and extract entries/categories.

    Returns:
        (entries, categories) tuple
    """
    # Handle legacy format (list of entries)
    if isinstance(data, list):
        return data, []

    # Modern format with metadata
    if "entries" not in data:
        if isinstance(data, dict) and any(k in data for k in ["website", "username", "password"]):
            # Single entry wrapped in dict
            return [data], []
        raise ImportError("Invalid backup format: missing 'entries' key")

    entries = data["entries"]
    categories = data.get("categories", [])

    # Validate entries are list
    if not isinstance(entries, list):
        raise ImportError("Invalid backup format: 'entries' must be a list")

    return entries, categories


def _import_categories(categories: List[Dict]) -> None:
    """Import categories (best-effort, ignore duplicates)."""
    for category in categories:
        try:
            add_category(category["name"], category.get("color", "blue"))
        except Exception:
            # Category likely already exists, skip
            pass


def _import_entries(entries: List[Dict]) -> int:
    """Import password entries in a single transaction.

    Returns:
        Number of entries successfully imported
    """
    db_path = str(get_database_path())

    # Single connection for entire import
    conn = sqlite3.connect(db_path, timeout=DEFAULT_TIMEOUT)
    conn.execute("PRAGMA busy_timeout = 30000")

    try:
        cursor = conn.cursor()
        now = int(time.time())

        # Prepare batch insert
        rows = []
        for item in entries:
            try:
                row = _prepare_entry_row(item, now)
                rows.append(row)
            except Exception as e:
                log_warning(f"Skipping invalid entry: {e}")
                continue

        # Batch insert in single transaction
        cursor.executemany(
            """
            INSERT INTO passwords (
                website, username, password, category, notes,
                created_at, updated_at, expiry_date, favorite
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows
        )

        conn.commit()
        return len(rows)

    except sqlite3.Error as e:
        conn.rollback()
        raise ImportError(f"Database import failed: {e}") from e

    finally:
        conn.close()


def _prepare_entry_row(item: Dict, default_time: int) -> Tuple:
    """Prepare a single entry for insertion."""
    # Required fields
    website = item["website"]
    username = item["username"]
    password = item["password"]

    # Optional fields with defaults
    category = item.get("category", "General")
    notes = item.get("notes", "")
    created_at = item.get("created_at", default_time)
    updated_at = item.get("updated_at", default_time)
    expiry_date = item.get("expiry_date")
    favorite = int(item.get("favorite", False))

    # Validate expiry is int or None
    if expiry_date is not None and not isinstance(expiry_date, int):
        expiry_date = None

    # Encrypt password
    encrypted = encrypt_password(password)

    return (
        website,
        username,
        encrypted,
        category,
        notes,
        created_at,
        updated_at,
        expiry_date,
        favorite,
    )


# ============================================================================
# FULL BACKUP OPERATIONS
# ============================================================================

def create_full_backup(backup_dir: str, master_password: str) -> Optional[str]:
    """Create a complete backup including database, keys, and config.

    Args:
        backup_dir: Directory to store backup
        master_password: Password to encrypt the password export

    Returns:
        Path to backup zip file, or None if failed
    """
    try:
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = int(time.time())
        backup_filename = f"password_manager_backup_{timestamp}.zip"
        backup_path = os.path.join(backup_dir, backup_filename)

        # Create backup in temp dir, then move to final location
        with tempfile.TemporaryDirectory() as temp_dir:
            # Export passwords
            export_path = os.path.join(temp_dir, "passwords_export.dat")
            if not export_passwords(export_path, master_password):
                log_error("Failed to export passwords for backup")
                return None

            # Create backup zip
            _create_backup_zip(backup_path, export_path, timestamp)

        log_info(f"Created full backup at {backup_path}")
        return backup_path

    except Exception as e:
        log_error(f"Full backup failed: {e}")
        return None


def _create_backup_zip(zip_path: str, export_path: str, timestamp: int) -> None:
    """Create backup zip with all necessary files."""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
        # Add password export
        backup_zip.write(export_path, "passwords_export.dat")

        # Add system files
        _add_file_to_zip(backup_zip, get_database_path(), "passwords.db")
        _add_file_to_zip(backup_zip, get_secret_key_path(), "secret.key")
        _add_file_to_zip(backup_zip, get_auth_json_path(), "auth.json")
        _add_file_to_zip(backup_zip, get_crypto_salt_path(), "crypto.salt")

        # Add metadata
        metadata = {
            "version": BACKUP_VERSION,
            "timestamp": timestamp,
            "description": "Full password manager backup",
        }
        backup_zip.writestr("metadata.json", json.dumps(metadata, indent=2))


def _add_file_to_zip(zip_file: zipfile.ZipFile, source_path: Path, archive_name: str) -> None:
    """Add file to zip if it exists."""
    if source_path.exists():
        zip_file.write(str(source_path), archive_name)


# ============================================================================
# RESTORE OPERATIONS
# ============================================================================

def restore_from_backup(backup_path: str, master_password: str) -> bool:
    """Restore from a full backup.

    Args:
        backup_path: Path to backup zip file
        master_password: Password to decrypt password export

    Returns:
        True if restore succeeded, False otherwise
    """
    if not os.path.exists(backup_path):
        log_error(f"Restore failed: backup not found: {backup_path}")
        return False

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract backup
            with zipfile.ZipFile(backup_path, 'r') as backup_zip:
                backup_zip.extractall(temp_dir)

            # Validate backup
            export_path = os.path.join(temp_dir, "passwords_export.dat")
            if not os.path.exists(export_path):
                log_error("Invalid backup: missing password export")
                return False

            # Create timestamped backups of current files
            backup_suffix = int(time.time())
            _backup_current_files(backup_suffix)

            # Restore files
            _restore_files_from_temp(temp_dir)

        log_info(f"Successfully restored from {backup_path}")
        return True

    except Exception as e:
        log_error(f"Restore failed: {e}")
        return False


def _backup_current_files(suffix: int) -> None:
    """Create backups of current files before restore."""
    files_to_backup = [
        get_database_path(),
        get_secret_key_path(),
        get_auth_json_path(),
        get_crypto_salt_path(),
    ]

    for file_path in files_to_backup:
        if file_path.exists():
            backup_path = Path(f"{file_path}.bak{suffix}")
            try:
                shutil.copy(str(file_path), str(backup_path))
            except Exception as e:
                log_warning(f"Failed to backup {file_path}: {e}")


def _restore_files_from_temp(temp_dir: str) -> None:
    """Restore files from temporary extraction directory."""
    file_mappings = {
        "passwords.db": get_database_path(),
        "secret.key": get_secret_key_path(),
        "auth.json": get_auth_json_path(),
        "crypto.salt": get_crypto_salt_path(),
    }

    for filename, dest_path in file_mappings.items():
        source_path = os.path.join(temp_dir, filename)
        if os.path.exists(source_path):
            shutil.copy(source_path, str(dest_path))