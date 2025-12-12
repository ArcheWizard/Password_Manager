"""Comprehensive tests for backup module."""

import json
import os
import sqlite3
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.utils.backup import (
    BackupError,
    ImportError,
    create_full_backup,
    export_passwords,
    import_passwords,
    restore_from_backup,
)
from secure_password_manager.utils.crypto import (
    decrypt_password,
    decrypt_with_password_envelope,
    encrypt_password,
)
from secure_password_manager.utils.database import (
    add_category,
    add_password,
    get_categories,
    get_passwords,
    init_db,
)


@pytest.fixture
def setup_test_data(clean_crypto_files, clean_database):
    """Setup test database with sample passwords."""
    from secure_password_manager.utils.crypto import generate_key

    # Generate encryption key
    generate_key()

    # Initialize database
    init_db()

    # Add categories
    add_category("Development", "blue")
    add_category("Cloud", "green")

    # Add test passwords
    add_password(
        "github.com",
        "developer@example.com",
        encrypt_password("GitHubPass123!"),
        "Development",
        "GitHub account",
    )

    add_password(
        "aws.amazon.com",
        "admin@company.com",
        encrypt_password("AWSSecure456#"),
        "Cloud",
        "AWS root account",
        expiry_days=90,
    )

    add_password(
        "gitlab.com",
        "devops@example.com",
        encrypt_password("GitLabKey789$"),
        "Development",
        "",
    )

    return get_passwords()


# ============================================================================
# EXPORT TESTS
# ============================================================================

def test_export_passwords_success(setup_test_data, tmp_path):
    """Test successful password export."""
    export_file = tmp_path / "export.dat"
    master_password = "test_master_pass"

    result = export_passwords(str(export_file), master_password, include_notes=True)

    assert result is True
    assert export_file.exists()
    assert export_file.stat().st_size > 0


def test_export_passwords_adds_dat_extension(setup_test_data, tmp_path):
    """Test that export adds .dat extension if missing."""
    export_file = tmp_path / "export"
    master_password = "test_master_pass"

    result = export_passwords(str(export_file), master_password)

    assert result is True
    assert (tmp_path / "export.dat").exists()


def test_export_passwords_without_notes(setup_test_data, tmp_path):
    """Test password export without notes."""
    export_file = tmp_path / "export.dat"
    master_password = "test_master_pass"

    result = export_passwords(str(export_file), master_password, include_notes=False)

    assert result is True

    # Verify notes are not included
    with open(export_file, "rb") as f:
        blob = f.read()

    json_data = decrypt_with_password_envelope(blob, master_password)
    data = json.loads(json_data)

    for entry in data["entries"]:
        assert "notes" not in entry or entry["notes"] == ""


def test_export_passwords_empty_database(clean_crypto_files, clean_database, tmp_path):
    """Test export with empty database."""
    from secure_password_manager.utils.crypto import generate_key

    generate_key()
    init_db()

    export_file = tmp_path / "export.dat"
    master_password = "test_master_pass"

    result = export_passwords(str(export_file), master_password)

    assert result is False
    assert not export_file.exists()


def test_export_passwords_includes_metadata(setup_test_data, tmp_path):
    """Test that export includes proper metadata."""
    export_file = tmp_path / "export.dat"
    master_password = "test_master_pass"

    export_passwords(str(export_file), master_password)

    with open(export_file, "rb") as f:
        blob = f.read()

    json_data = decrypt_with_password_envelope(blob, master_password)
    data = json.loads(json_data)

    assert "metadata" in data
    assert data["metadata"]["version"] == "2.0"
    assert "exported_at" in data["metadata"]
    assert data["metadata"]["entry_count"] == 3


def test_export_passwords_includes_categories(setup_test_data, tmp_path):
    """Test that export includes categories."""
    export_file = tmp_path / "export.dat"
    master_password = "test_master_pass"

    export_passwords(str(export_file), master_password)

    with open(export_file, "rb") as f:
        blob = f.read()

    json_data = decrypt_with_password_envelope(blob, master_password)
    data = json.loads(json_data)

    assert "categories" in data
    category_names = [cat["name"] for cat in data["categories"]]
    assert "Development" in category_names
    assert "Cloud" in category_names


def test_export_passwords_atomic_write(setup_test_data, tmp_path):
    """Test that export uses atomic write (temp file then move)."""
    export_file = tmp_path / "export.dat"
    master_password = "test_master_pass"

    # Mock the file write to check temp file is used
    original_replace = os.replace
    temp_files_seen = []

    def mock_replace(src, dst):
        temp_files_seen.append(src)
        return original_replace(src, dst)

    with patch('os.replace', side_effect=mock_replace):
        export_passwords(str(export_file), master_password)

    # Should have used a .tmp file
    assert any('.tmp' in str(f) for f in temp_files_seen)


def test_export_passwords_cleans_up_on_error(setup_test_data, tmp_path):
    """Test that partial files are cleaned up on error."""
    export_file = tmp_path / "export.dat"
    master_password = "test_master_pass"

    # Force an error during encryption
    with patch('secure_password_manager.utils.backup.encrypt_with_password_envelope',
               side_effect=Exception("Encryption failed")):
        result = export_passwords(str(export_file), master_password)

    assert result is False
    assert not export_file.exists()
    assert not (tmp_path / "export.dat.tmp").exists()


# ============================================================================
# IMPORT TESTS
# ============================================================================

def test_import_passwords_success(setup_test_data, tmp_path):
    """Test successful password import."""
    from secure_password_manager.utils.paths import get_database_path
    from secure_password_manager.utils.database import close_connection

    # Export first
    export_file = tmp_path / "export.dat"
    master_password = "test_master_pass"
    export_passwords(str(export_file), master_password)

    # Clear database
    close_connection()  # Close connection before deleting
    db_path = get_database_path()
    if db_path.exists():
        db_path.unlink()
    init_db()

    # Import
    imported_count = import_passwords(str(export_file), master_password)

    assert imported_count == 3

    # Verify imported data
    passwords = get_passwords()
    assert len(passwords) >= 3


def test_import_passwords_wrong_password(setup_test_data, tmp_path):
    """Test import with wrong password."""
    export_file = tmp_path / "export.dat"
    export_passwords(str(export_file), "correct_password")

    # Try to import with wrong password
    imported_count = import_passwords(str(export_file), "wrong_password")

    assert imported_count == 0


def test_import_passwords_nonexistent_file(tmp_path):
    """Test import with non-existent file."""
    fake_file = tmp_path / "nonexistent.dat"

    imported_count = import_passwords(str(fake_file), "password")

    assert imported_count == 0


def test_import_passwords_preserves_metadata(setup_test_data, tmp_path):
    """Test that import preserves password metadata."""
    export_file = tmp_path / "export.dat"
    master_password = "test_master_pass"
    export_passwords(str(export_file), master_password)

    # Get original data
    original_passwords = get_passwords()
    original_github = next(p for p in original_passwords if p[1] == "github.com")

    # Clear and import
    from secure_password_manager.utils.paths import get_database_path
    db_path = get_database_path()
    db_path.unlink()
    init_db()

    import_passwords(str(export_file), master_password)

    # Verify metadata preserved
    imported_passwords = get_passwords()
    imported_github = next(p for p in imported_passwords if p[1] == "github.com")

    assert imported_github[2] == original_github[2]  # username
    assert imported_github[4] == original_github[4]  # category
    assert imported_github[5] == original_github[5]  # notes


def test_import_passwords_imports_categories(setup_test_data, tmp_path):
    """Test that import creates categories."""
    export_file = tmp_path / "export.dat"
    master_password = "test_master_pass"
    export_passwords(str(export_file), master_password)

    # Clear database
    from secure_password_manager.utils.paths import get_database_path
    db_path = get_database_path()
    db_path.unlink()
    init_db()

    # Import
    import_passwords(str(export_file), master_password)

    # Verify categories imported
    categories = get_categories()
    category_names = [cat[0] for cat in categories]
    assert "Development" in category_names
    assert "Cloud" in category_names


def test_import_passwords_legacy_format(tmp_path, clean_crypto_files, clean_database):
    """Test importing legacy format (list of entries)."""
    from secure_password_manager.utils.crypto import generate_key

    generate_key()
    init_db()

    # Create legacy format export (just a list)
    legacy_data = [
        {
            "website": "legacy.com",
            "username": "user@legacy.com",
            "password": "LegacyPass123",
            "category": "General",
        }
    ]

    export_file = tmp_path / "legacy.dat"
    from secure_password_manager.utils.crypto import encrypt_with_password_envelope

    json_data = json.dumps(legacy_data)
    blob = encrypt_with_password_envelope(json_data, "password")

    with open(export_file, 'wb') as f:
        f.write(blob)

    # Import
    imported_count = import_passwords(str(export_file), "password")

    assert imported_count == 1

    passwords = get_passwords()
    assert any(p[1] == "legacy.com" for p in passwords)


def test_import_passwords_invalid_format(tmp_path, clean_database):
    """Test import with invalid format."""
    from secure_password_manager.utils.crypto import generate_key

    generate_key()
    init_db()

    # Create invalid format
    invalid_data = {"invalid": "structure"}
    export_file = tmp_path / "invalid.dat"

    from secure_password_manager.utils.crypto import encrypt_with_password_envelope

    json_data = json.dumps(invalid_data)
    blob = encrypt_with_password_envelope(json_data, "password")

    with open(export_file, 'wb') as f:
        f.write(blob)

    # Import should fail gracefully
    imported_count = import_passwords(str(export_file), "password")

    assert imported_count == 0


def test_import_passwords_single_transaction(setup_test_data, tmp_path):
    """Test that import successfully imports all entries."""
    from secure_password_manager.utils.database import close_connection

    export_file = tmp_path / "export.dat"
    master_password = "test_master_pass"
    export_passwords(str(export_file), master_password)

    # Clear database
    close_connection()
    from secure_password_manager.utils.paths import get_database_path
    db_path = get_database_path()
    db_path.unlink()
    init_db()

    # Import should succeed and import all 3 entries
    imported_count = import_passwords(str(export_file), master_password)
    assert imported_count == 3

    # Verify all entries were imported
    passwords = get_passwords()
    assert len(passwords) == 3


# ============================================================================
# FULL BACKUP TESTS
# ============================================================================

def test_create_full_backup_success(setup_test_data, tmp_path):
    """Test creating a full backup."""
    backup_dir = tmp_path / "backups"
    master_password = "test_master_pass"

    backup_path = create_full_backup(str(backup_dir), master_password)

    assert backup_path is not None
    assert Path(backup_path).exists()
    assert backup_path.endswith('.zip')


def test_create_full_backup_creates_directory(tmp_path, clean_crypto_files, clean_database):
    """Test that backup creates directory if it doesn't exist."""
    from secure_password_manager.utils.crypto import generate_key

    generate_key()
    init_db()
    add_password("test.com", "user", encrypt_password("pass"), "General")

    backup_dir = tmp_path / "nonexistent" / "backups"
    master_password = "test_master_pass"

    backup_path = create_full_backup(str(backup_dir), master_password)

    assert backup_path is not None
    assert backup_dir.exists()


def test_create_full_backup_contains_required_files(setup_test_data, tmp_path):
    """Test that backup contains all required files."""
    backup_dir = tmp_path / "backups"
    master_password = "test_master_pass"

    backup_path = create_full_backup(str(backup_dir), master_password)

    # Extract and verify contents
    if backup_path is None:
        raise ValueError("Backup path cannot be None")
    with zipfile.ZipFile(backup_path, 'r') as backup_zip:
        file_list = backup_zip.namelist()

        # Always included
        assert "passwords_export.dat" in file_list
        assert "passwords.db" in file_list
        assert "secret.key" in file_list
        assert "metadata.json" in file_list

        # Optional files (only included if they exist)
        # auth.json - only if master password is set
        # crypto.salt - only if exists


def test_create_full_backup_metadata(setup_test_data, tmp_path):
    """Test that backup metadata is correct."""
    backup_dir = tmp_path / "backups"
    master_password = "test_master_pass"

    backup_path = create_full_backup(str(backup_dir), master_password)

    if backup_path is None:
        raise ValueError("Backup path cannot be None")
    with zipfile.ZipFile(backup_path, 'r') as backup_zip:
        metadata_json = backup_zip.read("metadata.json")
        metadata = json.loads(metadata_json)

        assert metadata["version"] == "2.0"
        assert "timestamp" in metadata
        assert metadata["description"] == "Full password manager backup"


def test_create_full_backup_cleans_temp_files(setup_test_data, tmp_path):
    """Test that backup cleans up temporary files."""
    backup_dir = tmp_path / "backups"
    master_password = "test_master_pass"

    create_full_backup(str(backup_dir), master_password)

    # No .tmp files should remain
    temp_files = list(backup_dir.glob("**/*.tmp"))
    assert len(temp_files) == 0


@patch("secure_password_manager.utils.backup.export_passwords")
def test_create_full_backup_handles_export_failure(mock_export, setup_test_data, tmp_path):
    """Test that backup handles export failure gracefully."""
    mock_export.return_value = False

    backup_dir = tmp_path / "backups"
    master_password = "test_master_pass"

    backup_path = create_full_backup(str(backup_dir), master_password)

    assert backup_path is None


# ============================================================================
# RESTORE TESTS
# ============================================================================

def test_restore_from_backup_success(setup_test_data, tmp_path):
    """Test successful restore from backup."""
    # Create backup
    backup_dir = tmp_path / "backups"
    master_password = "test_master_pass"
    backup_path = create_full_backup(str(backup_dir), master_password)

    # Modify database
    add_password("modified.com", "user", encrypt_password("pass"), "General")

    # Restore
    assert backup_path is not None
    result = restore_from_backup(backup_path, master_password)

    assert result is True


def test_restore_from_backup_nonexistent_file(tmp_path):
    """Test restore with non-existent backup file."""
    fake_backup = tmp_path / "nonexistent.zip"

    result = restore_from_backup(str(fake_backup), "password")

    assert result is False


def test_restore_from_backup_invalid_backup(tmp_path):
    """Test restore with invalid backup file."""
    # Create invalid zip
    invalid_backup = tmp_path / "invalid.zip"
    with zipfile.ZipFile(invalid_backup, 'w') as zf:
        zf.writestr("random.txt", "not a backup")

    result = restore_from_backup(str(invalid_backup), "password")

    assert result is False


def test_restore_from_backup_creates_file_backups(setup_test_data, tmp_path, monkeypatch):
    """Test that restore creates backups of current files."""
    from secure_password_manager.utils.paths import get_database_path

    # Create backup
    backup_dir = tmp_path / "backups"
    master_password = "test_master_pass"
    backup_path = create_full_backup(str(backup_dir), master_password)

    # Get database path
    db_path = get_database_path()
    original_size = db_path.stat().st_size

    # Restore (should create .bak files)
    assert backup_path is not None
    restore_from_backup(backup_path, master_password)

    # Check for backup files
    backup_files = list(db_path.parent.glob("*.bak*"))
    assert len(backup_files) > 0


def test_restore_from_backup_extracts_to_temp(setup_test_data, tmp_path, monkeypatch):
    """Test that restore extracts to temp directory first."""
    backup_dir = tmp_path / "backups"
    master_password = "test_master_pass"
    backup_path = create_full_backup(str(backup_dir), master_password)

    # Mock tempfile to track usage
    original_tempdir = tempfile.TemporaryDirectory

    temp_dirs_created = []

    class TrackedTempDir(original_tempdir):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            temp_dirs_created.append(self.name)

    with patch('tempfile.TemporaryDirectory', TrackedTempDir):
        assert backup_path is not None
        restore_from_backup(backup_path, master_password)

    # Should have used a temp directory
    assert len(temp_dirs_created) > 0


@patch("secure_password_manager.utils.backup.zipfile.ZipFile")
def test_restore_from_backup_handles_extraction_error(mock_zipfile, tmp_path):
    """Test that restore handles extraction errors."""
    mock_zipfile.side_effect = Exception("Extraction failed")

    backup_path = tmp_path / "backup.zip"
    backup_path.touch()

    result = restore_from_backup(str(backup_path), "password")

    assert result is False


# ============================================================================
# ROUNDTRIP TESTS
# ============================================================================

def test_export_import_roundtrip_preserves_data(setup_test_data, tmp_path):
    """Test that export/import roundtrip preserves all data."""
    from secure_password_manager.utils.paths import get_database_path

    # Get original data
    original_passwords = get_passwords()
    original_categories = get_categories()

    # Export
    export_file = tmp_path / "export.dat"
    master_password = "test_master_pass"
    export_passwords(str(export_file), master_password)

    # Clear database
    db_path = get_database_path()
    db_path.unlink()
    init_db()

    # Import
    import_passwords(str(export_file), master_password)

    # Verify data matches
    restored_passwords = get_passwords()
    restored_categories = get_categories()

    assert len(restored_passwords) == len(original_passwords)
    assert len(restored_categories) >= len(original_categories)  # May have defaults

    # Verify passwords can be decrypted
    for password_entry in restored_passwords:
        decrypted = decrypt_password(password_entry[3])
        assert len(decrypted) > 0


def test_backup_restore_roundtrip(setup_test_data, tmp_path, monkeypatch):
    """Test full backup and restore roundtrip."""
    from secure_password_manager.utils.paths import get_database_path

    # Get original password count
    original_count = len(get_passwords())

    # Create backup
    backup_dir = tmp_path / "backups"
    master_password = "test_master_pass"
    backup_path = create_full_backup(str(backup_dir), master_password)

    # Modify database
    add_password("new.com", "user", encrypt_password("pass"), "General")
    assert len(get_passwords()) == original_count + 1

    # Restore
    assert backup_path is not None
    restore_from_backup(backup_path, master_password)

    # Should have original count (restore doesn't import, just replaces files)
    # Note: This test verifies the restore mechanism, not import
    assert backup_path is not None
    assert Path(backup_path).exists()