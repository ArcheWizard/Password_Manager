"""Tests for password history functionality."""

import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.utils import config
from secure_password_manager.utils.crypto import decrypt_password, encrypt_password
from secure_password_manager.utils.database import (
    add_password,
    delete_password_history,
    get_all_password_history,
    get_password_history,
    get_passwords,
    init_db,
    update_password,
)
from secure_password_manager.utils.migrations import get_schema_version, run_migrations


@pytest.fixture
def test_db(test_env, clean_database, clean_crypto_files):
    """Set up a temporary database for testing."""
    from secure_password_manager.utils.crypto import generate_key

    # Generate encryption key
    generate_key()

    # Initialize database (already done by clean_database but ensures migrations run)
    init_db()

    yield test_env["data_dir"]

    # Cleanup handled by conftest fixtures


def test_migration_creates_password_history_table(test_db):
    """Test that migration creates password_history table."""
    # Check schema version
    version = get_schema_version()
    assert version >= 1, "Schema should be at least version 1"

    # Check that password_history table exists
    import sqlite3

    from secure_password_manager.utils.database import _get_db_file

    conn = sqlite3.connect(_get_db_file())
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='password_history'
    """
    )

    result = cursor.fetchone()
    conn.close()

    assert result is not None, "password_history table should exist"
    assert result[0] == "password_history"


def test_password_history_recorded_on_update(test_db):
    """Test that password changes are recorded in history."""
    # Add initial password
    password1 = "InitialPassword123"
    encrypted1 = encrypt_password(password1)
    add_password("example.com", "user@test.com", encrypted1)

    # Get the entry
    entries = get_passwords()
    entry_id = entries[0][0]

    # Update password
    password2 = "UpdatedPassword456"
    encrypted2 = encrypt_password(password2)
    update_password(entry_id, encrypted_password=encrypted2, rotation_reason="manual")

    # Check history
    history = get_password_history(entry_id)

    assert len(history) == 1, "Should have one history entry"

    hist_id, pw_id, old_encrypted, changed_at, reason, changed_by = history[0]

    assert pw_id == entry_id
    assert decrypt_password(old_encrypted) == password1
    assert reason == "manual"
    assert changed_by == "user"
    assert changed_at > 0


def test_password_history_rotation_reasons(test_db):
    """Test different rotation reasons are recorded correctly."""
    # Set high retention to keep all history
    config.update_settings({"password_history": {"max_versions": 10}})

    # Add initial password
    password = "TestPassword123"
    encrypted = encrypt_password(password)
    add_password("test.com", "user@test.com", encrypted)

    entries = get_passwords()
    entry_id = entries[0][0]

    # Test different rotation reasons
    reasons = ["manual", "expiry", "breach", "strength"]

    for reason in reasons:
        new_password = f"NewPassword_{reason}"
        new_encrypted = encrypt_password(new_password)
        config.update_settings({"password_history": {"max_versions": 10}})
        update_password(
            entry_id, encrypted_password=new_encrypted, rotation_reason=reason
        )

    # Check history
    history = get_password_history(entry_id, limit=10)

    assert len(history) == len(reasons), f"Should have {len(reasons)} history entries"

    # Verify all reasons are present (order might vary due to same timestamps)
    recorded_reasons = [h[4] for h in history]
    assert set(recorded_reasons) == set(reasons), (
        f"All reasons should be present. Got {recorded_reasons}"
    )


def test_password_history_retention_limit(test_db):
    """Test that history respects max_versions limit."""
    # Set retention limit to 3
    config.update_settings({"password_history": {"max_versions": 3}})

    # Add initial password
    password = "InitialPassword"
    encrypted = encrypt_password(password)
    add_password("retention-test.com", "user@test.com", encrypted)

    entries = get_passwords()
    entry_id = entries[0][0]

    # Update password 5 times
    for i in range(5):
        new_password = f"Password_{i}"
        new_encrypted = encrypt_password(new_password)
        update_password(
            entry_id, encrypted_password=new_encrypted, rotation_reason="manual"
        )

    # Check history
    history = get_password_history(entry_id)

    # Should only keep last 3 versions
    assert len(history) <= 3, "Should only keep last 3 versions"


def test_password_history_unchanged_password_no_record(test_db):
    """Test that unchanged passwords don't create history entries."""
    # Add initial password
    password = "TestPassword123"
    encrypted = encrypt_password(password)
    add_password("no-change.com", "user@test.com", encrypted)

    entries = get_passwords()
    entry_id = entries[0][0]

    # Update other fields but not password
    update_password(entry_id, website="no-change-updated.com", notes="Updated notes")

    # Check history
    history = get_password_history(entry_id)

    assert len(history) == 0, "Should have no history entries when password unchanged"


def test_get_all_password_history(test_db):
    """Test retrieving history across all entries."""
    # Add multiple passwords
    for i in range(3):
        password = f"Password_{i}"
        encrypted = encrypt_password(password)
        add_password(f"site{i}.com", f"user{i}@test.com", encrypted)

    # Update each password
    entries = get_passwords()
    for entry in entries:
        entry_id = entry[0]
        new_password = f"Updated_{entry_id}"
        new_encrypted = encrypt_password(new_password)
        update_password(
            entry_id, encrypted_password=new_encrypted, rotation_reason="manual"
        )

    # Get all history
    all_history = get_all_password_history(limit=50)

    assert len(all_history) == 3, "Should have history for all 3 entries"

    # Verify structure
    for hist in all_history:
        hist_id, pw_id, website, username, changed_at, reason, changed_by = hist
        assert website.startswith("site"), "Website should match pattern"
        assert username.startswith("user"), "Username should match pattern"
        assert reason == "manual"


def test_delete_password_history(test_db):
    """Test deleting history for a password entry."""
    # Add and update password
    password = "TestPassword"
    encrypted = encrypt_password(password)
    add_password("delete-test.com", "user@test.com", encrypted)

    entries = get_passwords()
    entry_id = entries[0][0]

    # Create some history
    for i in range(3):
        new_password = f"Password_{i}"
        new_encrypted = encrypt_password(new_password)
        update_password(
            entry_id, encrypted_password=new_encrypted, rotation_reason="manual"
        )

    # Verify history exists
    history = get_password_history(entry_id)
    assert len(history) == 3

    # Delete history
    delete_password_history(entry_id)

    # Verify history deleted
    history = get_password_history(entry_id)
    assert len(history) == 0, "History should be deleted"


def test_password_history_with_zero_max_versions(test_db):
    """Test that setting max_versions to 0 disables retention limit."""
    # Disable retention limit by updating config before adding password
    config.update_settings({"password_history": {"max_versions": 0}})

    # Add initial password
    password = "InitialPassword"
    encrypted = encrypt_password(password)
    add_password("unlimited-test.com", "user@test.com", encrypted)

    entries = get_passwords()
    entry_id = entries[0][0]

    # Update password many times
    num_updates = 15
    for i in range(num_updates):
        new_password = f"Password_{i}"
        new_encrypted = encrypt_password(new_password)
        # Ensure config is still set to 0
        config.update_settings({"password_history": {"max_versions": 0}})
        update_password(
            entry_id, encrypted_password=new_encrypted, rotation_reason="manual"
        )

    # Check history - with max_versions=0, all entries should be kept
    history = get_password_history(entry_id, limit=20)  # Use higher limit to see all

    # With max_versions=0, all entries should be kept (but limited by query limit)
    assert len(history) >= 10, f"Should keep many versions (got {len(history)})"
    # Since we query with limit=20 and created 15, we should see all 15
    assert len(history) == num_updates, f"Should keep all {num_updates} versions"


def test_password_history_limit_parameter(test_db):
    """Test that get_password_history respects limit parameter."""
    # Add initial password
    password = "InitialPassword"
    encrypted = encrypt_password(password)
    add_password("limit-test.com", "user@test.com", encrypted)

    entries = get_passwords()
    entry_id = entries[0][0]

    # Create 10 history entries
    for i in range(10):
        new_password = f"Password_{i}"
        new_encrypted = encrypt_password(new_password)
        update_password(
            entry_id, encrypted_password=new_encrypted, rotation_reason="manual"
        )

    # Get limited history
    history = get_password_history(entry_id, limit=5)

    assert len(history) == 5, "Should return only 5 entries"

    # Verify they're the most recent
    history_full = get_password_history(entry_id, limit=10)
    assert history == history_full[:5], "Should return most recent entries"


def test_migration_is_idempotent(test_db):
    """Test that running migrations multiple times is safe."""
    version_before = get_schema_version()

    # Run migrations again
    result = run_migrations()

    version_after = get_schema_version()

    assert version_before == version_after, "Version should not change"
    assert result["success"] == True
    assert len(result["migrations_run"]) == 0, "No migrations should run"


def test_password_history_with_special_characters(test_db):
    """Test that passwords with special characters are stored correctly in history."""
    # Add password with special characters
    password1 = "P@ssw0rd!#$%^&*()"
    encrypted1 = encrypt_password(password1)
    add_password("special-chars.com", "user@test.com", encrypted1)

    entries = get_passwords()
    entry_id = entries[0][0]

    # Update to another special password
    password2 = "Ñew©Pāss™wørd€2024"
    encrypted2 = encrypt_password(password2)
    update_password(entry_id, encrypted_password=encrypted2, rotation_reason="manual")

    # Check history
    history = get_password_history(entry_id)

    assert len(history) == 1
    old_encrypted = history[0][2]
    decrypted = decrypt_password(old_encrypted)

    assert decrypted == password1, "Special characters should be preserved"
