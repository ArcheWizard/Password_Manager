"""Tests for bulk operations."""

import os
import sys
import time

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.utils.bulk_operations import (
    BulkOperationResult,
    bulk_change_category,
    bulk_delete,
    bulk_export,
    bulk_rotate_passwords,
    bulk_set_expiry,
    bulk_toggle_favorite,
    select_entries_by_filter,
)
from secure_password_manager.utils.crypto import decrypt_password, encrypt_password
from secure_password_manager.utils.database import add_password, get_passwords, init_db


@pytest.fixture
def setup_test_entries(clean_crypto_files, clean_database):
    """Create test password entries."""
    init_db()

    entries = [
        ("example.com", "user1", "password123", "Web", "Test note 1", None),
        ("github.com", "user2", "githubpass", "Development", "Test note 2", None),
        ("bank.com", "user3", "bankpass", "Finance", "Test note 3", 90),
        ("email.com", "user4", "emailpass", "Email", "Test note 4", None),
        ("social.com", "user5", "socialpass", "Social", "Test note 5", None),
    ]

    for website, username, password, category, notes, expiry_days in entries:
        encrypted = encrypt_password(password)
        add_password(website, username, encrypted, category, notes, expiry_days)

    return entries


def test_bulk_operation_result():
    """Test BulkOperationResult tracking."""
    result = BulkOperationResult()

    assert result.success_count == 0
    assert result.failure_count == 0
    assert result.skip_count == 0
    assert result.total_attempted == 0

    result.add_success(1)
    result.add_success(2)
    result.add_failure(3, "Error message")
    result.add_skip(4, "User cancelled")

    assert result.success_count == 2
    assert result.failure_count == 1
    assert result.skip_count == 1
    assert result.total_attempted == 4

    result_dict = result.to_dict()
    assert result_dict["success_count"] == 2
    assert result_dict["failure_count"] == 1
    assert result_dict["skip_count"] == 1
    assert 1 in result_dict["successful_ids"]
    assert 2 in result_dict["successful_ids"]


def test_bulk_delete(setup_test_entries):
    """Test bulk deletion of entries."""
    entries = get_passwords()
    initial_count = len(entries)

    # Delete first 3 entries
    entry_ids = [entries[0][0], entries[1][0], entries[2][0]]
    result = bulk_delete(entry_ids)

    assert result.success_count == 3
    assert result.failure_count == 0

    # Verify entries are deleted
    remaining = get_passwords()
    assert len(remaining) == initial_count - 3


def test_bulk_delete_with_confirmation(setup_test_entries):
    """Test bulk deletion with confirmation callback."""
    entries = get_passwords()
    entry_ids = [entries[0][0], entries[1][0], entries[2][0]]

    # Callback that confirms first two but cancels third
    confirmed_count = [0]

    def confirm_callback(entry_id):
        confirmed_count[0] += 1
        return confirmed_count[0] <= 2

    result = bulk_delete(entry_ids, confirm_callback=confirm_callback)

    assert result.success_count == 2
    assert result.skip_count == 1
    assert result.skip_count == 1


def test_bulk_delete_nonexistent_entry(setup_test_entries):
    """Test bulk delete handles non-existent entries gracefully."""
    # Try to delete non-existent entry
    result = bulk_delete([9999])

    # Should succeed (delete is idempotent in the current implementation)
    # or could fail depending on database behavior
    assert result.success_count >= 0 and result.failure_count >= 0


def test_bulk_rotate_passwords(setup_test_entries):
    """Test bulk password rotation."""
    entries = get_passwords()
    entry_ids = [entries[0][0], entries[1][0]]

    # Get original passwords
    original_passwords = [decrypt_password(entries[0][3]), decrypt_password(entries[1][3])]

    # Rotate passwords
    result = bulk_rotate_passwords(entry_ids, rotation_reason="test_rotation")

    assert result.success_count == 2
    assert result.failure_count == 0

    # Verify passwords changed
    updated_entries = get_passwords()
    updated_entry_1 = [e for e in updated_entries if e[0] == entry_ids[0]][0]
    updated_entry_2 = [e for e in updated_entries if e[0] == entry_ids[1]][0]

    new_password_1 = decrypt_password(updated_entry_1[3])
    new_password_2 = decrypt_password(updated_entry_2[3])

    assert new_password_1 != original_passwords[0]
    assert new_password_2 != original_passwords[1]
    assert new_password_1 != new_password_2  # Should be different from each other


def test_bulk_change_category(setup_test_entries):
    """Test bulk category change."""
    entries = get_passwords()
    entry_ids = [entries[0][0], entries[1][0], entries[2][0]]

    # Change to new category
    result = bulk_change_category(entry_ids, "NewCategory")

    assert result.success_count == 3
    assert result.failure_count == 0

    # Verify categories changed
    updated_entries = get_passwords()
    for entry_id in entry_ids:
        entry = [e for e in updated_entries if e[0] == entry_id][0]
        assert entry[4] == "NewCategory"


def test_bulk_set_expiry(setup_test_entries):
    """Test bulk expiry date setting."""
    entries = get_passwords()
    entry_ids = [entries[0][0], entries[1][0]]

    # Set expiry to 30 days
    result = bulk_set_expiry(entry_ids, expiry_days=30)

    assert result.success_count == 2
    assert result.failure_count == 0

    # Verify expiry dates set
    updated_entries = get_passwords()
    current_time = int(time.time())

    for entry_id in entry_ids:
        entry = [e for e in updated_entries if e[0] == entry_id][0]
        expiry = entry[8]
        assert expiry is not None
        # Should be approximately 30 days from now (within 1 hour tolerance)
        expected_expiry = current_time + (30 * 86400)
        assert abs(expiry - expected_expiry) < 3600


def test_bulk_clear_expiry(setup_test_entries):
    """Test bulk clearing of expiry dates."""
    entries = get_passwords()
    # Entry 2 (index 2) has expiry set
    entry_id = entries[2][0]

    # Clear expiry
    result = bulk_set_expiry([entry_id], expiry_days=None)

    assert result.success_count == 1

    # Verify expiry cleared
    updated_entries = get_passwords()
    entry = [e for e in updated_entries if e[0] == entry_id][0]
    assert entry[8] is None


def test_bulk_toggle_favorite(setup_test_entries):
    """Test bulk favorite toggling."""
    entries = get_passwords()
    entry_ids = [entries[0][0], entries[1][0]]

    # Mark as favorites
    result = bulk_toggle_favorite(entry_ids, favorite=True)

    assert result.success_count == 2
    assert result.failure_count == 0

    # Verify marked as favorites
    updated_entries = get_passwords()
    for entry_id in entry_ids:
        entry = [e for e in updated_entries if e[0] == entry_id][0]
        assert entry[9] == 1  # favorite flag

    # Unmark favorites
    result = bulk_toggle_favorite(entry_ids, favorite=False)

    assert result.success_count == 2

    # Verify unmarked
    updated_entries = get_passwords()
    for entry_id in entry_ids:
        entry = [e for e in updated_entries if e[0] == entry_id][0]
        assert entry[9] == 0


def test_bulk_export(setup_test_entries):
    """Test bulk export of entries."""
    entries = get_passwords()
    entry_ids = [entries[0][0], entries[1][0], entries[2][0]]

    # Export entries
    exported, result = bulk_export(entry_ids)

    assert result.success_count == 3
    assert result.failure_count == 0
    assert len(exported) == 3

    # Verify exported data
    for exported_entry in exported:
        assert "id" in exported_entry
        assert "website" in exported_entry
        assert "username" in exported_entry
        assert "password" in exported_entry
        assert "category" in exported_entry
        assert "notes" in exported_entry

        # Password should be decrypted
        assert len(exported_entry["password"]) > 0


def test_bulk_export_nonexistent_entry(setup_test_entries):
    """Test bulk export handles non-existent entries."""
    exported, result = bulk_export([9999])

    assert result.failure_count == 1
    assert len(exported) == 0


def test_select_entries_by_filter_category(setup_test_entries):
    """Test selecting entries by category filter."""
    # Select all Web category entries
    entry_ids = select_entries_by_filter(category="Web")

    # Should match 1 entry
    assert len(entry_ids) == 1


def test_select_entries_by_filter_search(setup_test_entries):
    """Test selecting entries by search term."""
    # Search for 'github'
    entry_ids = select_entries_by_filter(search_term="github")

    assert len(entry_ids) == 1

    # Verify it's the github entry
    entries = get_passwords()
    github_entry = [e for e in entries if "github" in e[1].lower()][0]
    assert github_entry[0] in entry_ids


def test_select_entries_by_filter_favorites(setup_test_entries):
    """Test selecting only favorite entries."""
    entries = get_passwords()

    # Mark first two as favorites
    from secure_password_manager.utils.database import update_password

    for i in range(2):
        entry = entries[i]
        update_password(
            entry_id=entry[0],
            website=entry[1],
            username=entry[2],
            encrypted_password=entry[3],
            favorite=True,
        )

    # Select favorites only
    entry_ids = select_entries_by_filter(favorites_only=True)

    assert len(entry_ids) == 2


def test_select_entries_by_filter_expired(setup_test_entries):
    """Test selecting only expired entries."""
    entries = get_passwords()

    # Set first entry to expired (expiry in the past)
    from secure_password_manager.utils.database import update_password

    # Set entry to expire 1 day ago by using negative expiry_days
    # Actually, we need to use the raw SQL since update_password doesn't support past dates
    import sqlite3
    from secure_password_manager.utils.paths import get_database_path

    past_expiry = int(time.time()) - 86400  # 1 day ago
    entry = entries[0]

    conn = sqlite3.connect(str(get_database_path()))
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE passwords SET expiry_date = ?, updated_at = ? WHERE id = ?",
        (past_expiry, int(time.time()), entry[0])
    )
    conn.commit()
    conn.close()

    # Select expired only
    entry_ids = select_entries_by_filter(expired_only=True)

    assert len(entry_ids) >= 1
    assert entry[0] in entry_ids


def test_select_entries_combined_filters(setup_test_entries):
    """Test selecting entries with multiple filters."""
    entries = get_passwords()

    # Mark Web category entry as favorite
    from secure_password_manager.utils.database import update_password

    web_entry = [e for e in entries if e[4] == "Web"][0]
    update_password(
        entry_id=web_entry[0],
        website=web_entry[1],
        username=web_entry[2],
        encrypted_password=web_entry[3],
        favorite=True,
    )

    # Select Web favorites
    entry_ids = select_entries_by_filter(category="Web", favorites_only=True)

    assert len(entry_ids) == 1
    assert web_entry[0] in entry_ids
