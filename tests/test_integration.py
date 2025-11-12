"""Integration tests for password manager."""

import os
import sqlite3
import sys
import tempfile
from unittest.mock import patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.utils.auth import authenticate, set_master_password
from secure_password_manager.utils.backup import export_passwords
from secure_password_manager.utils.crypto import (
    decrypt_password,
    encrypt_password,
    generate_key,
    set_master_password_context,
)
from secure_password_manager.utils.database import add_password, get_passwords, init_db


@pytest.fixture
def test_db(clean_database, clean_crypto_files):
    """Create a temporary test database with crypto setup."""
    from secure_password_manager.utils.paths import get_database_path

    # Generate crypto key for the test
    generate_key()

    db_path = get_database_path()

    yield str(db_path)


def test_add_and_get_password_integration(test_db):
    """Test adding and retrieving a password."""
    website = "example.com"
    username = "user@example.com"
    password = "SecurePassword123!"

    # Encrypt and add password (using plaintext key mode)
    encrypted = encrypt_password(password)
    add_password(website, username, encrypted)

    # Retrieve and verify
    passwords = get_passwords()
    assert len(passwords) > 0

    found = False
    for entry in passwords:
        if entry[1] == website and entry[2] == username:
            decrypted = decrypt_password(entry[3])
            assert decrypted == password
            found = True
            break

    assert found, "Password not found in database"


def test_master_password_auth(clean_crypto_files):
    """Test master password authentication."""
    from secure_password_manager.utils.paths import get_auth_json_path

    auth_file = get_auth_json_path()

    password = "MyMasterPassword123"

    # Set master password
    set_master_password(password)
    assert auth_file.exists()

    # Test authentication
    assert authenticate(password)
    assert not authenticate("WrongPassword")


def test_backup_and_restore(test_db):
    """Test backup and restore functionality."""
    import time

    # Create temporary backup file
    fd, backup_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)

    try:
        # Add some test data
        passwords_to_add = []
        for i in range(5):
            site = f"site{i}.com"
            user = f"user{i}"
            password = f"pass{i}"
            encrypted = encrypt_password(password)
            add_password(site, user, encrypted)
            passwords_to_add.append(
                {
                    "website": site,
                    "username": user,
                    "password": password,
                    "category": "General",
                    "notes": "",
                }
            )

        # Export to backup with a separate password
        master_pass = "BackupTestPassword"
        result = export_passwords(backup_path, master_pass)
        assert result is True

        # Verify backup file exists
        assert os.path.exists(backup_path)
        assert os.path.getsize(backup_path) > 0

    finally:
        # Clean up
        if os.path.exists(backup_path):
            os.remove(backup_path)
