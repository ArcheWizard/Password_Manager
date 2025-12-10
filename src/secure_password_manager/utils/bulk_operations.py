"""Bulk operations for password entries.

This module provides utilities for performing operations on multiple
password entries simultaneously, such as bulk deletion, rotation, export,
and category changes.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from secure_password_manager.utils.crypto import decrypt_password, encrypt_password
from secure_password_manager.utils.database import (
    delete_password,
    get_passwords,
    update_password,
)
from secure_password_manager.utils.logger import log_info, log_warning
from secure_password_manager.utils.migrations import ensure_latest_schema
from secure_password_manager.utils.password_generator import (
    PasswordOptions,
    generate_password,
)


class BulkOperationResult:
    """Result of a bulk operation."""

    def __init__(self):
        self.successful: List[int] = []
        self.failed: List[Tuple[int, str]] = []
        self.skipped: List[Tuple[int, str]] = []

    @property
    def success_count(self) -> int:
        return len(self.successful)

    @property
    def failure_count(self) -> int:
        return len(self.failed)

    @property
    def skip_count(self) -> int:
        return len(self.skipped)

    @property
    def total_attempted(self) -> int:
        return self.success_count + self.failure_count + self.skip_count

    def add_success(self, entry_id: int) -> None:
        self.successful.append(entry_id)

    def add_failure(self, entry_id: int, reason: str) -> None:
        self.failed.append((entry_id, reason))

    def add_skip(self, entry_id: int, reason: str) -> None:
        self.skipped.append((entry_id, reason))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "skip_count": self.skip_count,
            "total_attempted": self.total_attempted,
            "successful_ids": self.successful,
            "failed": self.failed,
            "skipped": self.skipped,
        }


def bulk_delete(
    entry_ids: List[int],
    confirm_callback: Optional[Callable[[int], bool]] = None,
) -> BulkOperationResult:
    """Delete multiple password entries.

    Args:
        entry_ids: List of entry IDs to delete.
        confirm_callback: Optional callback to confirm each deletion.
                         Should return True to proceed, False to skip.

    Returns:
        BulkOperationResult with details of the operation.
    """
    result = BulkOperationResult()

    for entry_id in entry_ids:
        # Optional per-entry confirmation
        if confirm_callback and not confirm_callback(entry_id):
            result.add_skip(entry_id, "User cancelled")
            continue

        try:
            delete_password(entry_id)
            result.add_success(entry_id)
            log_info(f"Bulk delete: removed entry {entry_id}")
        except Exception as e:
            result.add_failure(entry_id, str(e))
            log_warning(f"Bulk delete failed for entry {entry_id}: {e}")

    log_info(
        f"Bulk delete completed: {result.success_count} succeeded, "
        f"{result.failure_count} failed, {result.skip_count} skipped"
    )
    return result


def bulk_rotate_passwords(
    entry_ids: List[int],
    password_options: Optional[PasswordOptions] = None,
    rotation_reason: str = "bulk_rotation",
) -> BulkOperationResult:
    """Rotate passwords for multiple entries.

    Args:
        entry_ids: List of entry IDs to rotate passwords for.
        password_options: Options for generating new passwords.
        rotation_reason: Reason for rotation (for history tracking).

    Returns:
        BulkOperationResult with details of the operation.
    """
    # Ensure password history table exists
    ensure_latest_schema()

    result = BulkOperationResult()

    for entry_id in entry_ids:
        try:
            # Get current entry
            entries = [e for e in get_passwords() if e[0] == entry_id]
            if not entries:
                result.add_failure(entry_id, "Entry not found")
                continue

            entry = entries[0]
            website = entry[1]
            username = entry[2]

            # Generate new password
            new_password = generate_password(options=password_options)

            # Encrypt new password
            encrypted = encrypt_password(new_password)

            # Update with rotation tracking
            update_password(
                entry_id=entry_id,
                website=website,
                username=username,
                encrypted_password=encrypted,
                rotation_reason=rotation_reason,
            )

            result.add_success(entry_id)
            log_info(f"Bulk rotate: updated password for entry {entry_id}")

        except Exception as e:
            result.add_failure(entry_id, str(e))
            log_warning(f"Bulk rotate failed for entry {entry_id}: {e}")

    log_info(
        f"Bulk password rotation completed: {result.success_count} succeeded, "
        f"{result.failure_count} failed"
    )
    return result


def bulk_change_category(
    entry_ids: List[int],
    new_category: str,
) -> BulkOperationResult:
    """Change category for multiple entries.

    Args:
        entry_ids: List of entry IDs to update.
        new_category: New category name.

    Returns:
        BulkOperationResult with details of the operation.
    """
    result = BulkOperationResult()

    for entry_id in entry_ids:
        try:
            # Get current entry
            entries = [e for e in get_passwords() if e[0] == entry_id]
            if not entries:
                result.add_failure(entry_id, "Entry not found")
                continue

            entry = entries[0]
            website = entry[1]
            username = entry[2]
            encrypted = entry[3]
            notes = entry[5] or ""

            # Update category
            update_password(
                entry_id=entry_id,
                website=website,
                username=username,
                encrypted_password=encrypted,
                category=new_category,
                notes=notes,
            )

            result.add_success(entry_id)
            log_info(f"Bulk category change: updated entry {entry_id} to '{new_category}'")

        except Exception as e:
            result.add_failure(entry_id, str(e))
            log_warning(f"Bulk category change failed for entry {entry_id}: {e}")

    log_info(
        f"Bulk category change completed: {result.success_count} succeeded, "
        f"{result.failure_count} failed"
    )
    return result


def bulk_set_expiry(
    entry_ids: List[int],
    expiry_days: Optional[int],
) -> BulkOperationResult:
    """Set expiry date for multiple entries.

    Args:
        entry_ids: List of entry IDs to update.
        expiry_days: Days until expiry (None to clear expiry).

    Returns:
        BulkOperationResult with details of the operation.
    """
    result = BulkOperationResult()

    for entry_id in entry_ids:
        try:
            # Get current entry
            entries = [e for e in get_passwords() if e[0] == entry_id]
            if not entries:
                result.add_failure(entry_id, "Entry not found")
                continue

            entry = entries[0]
            website = entry[1]
            username = entry[2]
            encrypted = entry[3]
            category = entry[4] or "General"
            notes = entry[5] or ""

            # Update expiry (database uses expiry_days, not expiry_date)
            # Pass None to clear, positive number to set days from now
            update_password(
                entry_id=entry_id,
                website=website,
                username=username,
                encrypted_password=encrypted,
                category=category,
                notes=notes,
                expiry_days=expiry_days,
            )

            result.add_success(entry_id)
            action = f"set to {expiry_days} days" if expiry_days else "cleared"
            log_info(f"Bulk expiry: {action} for entry {entry_id}")

        except Exception as e:
            result.add_failure(entry_id, str(e))
            log_warning(f"Bulk expiry update failed for entry {entry_id}: {e}")

    log_info(
        f"Bulk expiry update completed: {result.success_count} succeeded, "
        f"{result.failure_count} failed"
    )
    return result


def bulk_toggle_favorite(
    entry_ids: List[int],
    favorite: bool,
) -> BulkOperationResult:
    """Toggle favorite status for multiple entries.

    Args:
        entry_ids: List of entry IDs to update.
        favorite: True to mark as favorite, False to unmark.

    Returns:
        BulkOperationResult with details of the operation.
    """
    result = BulkOperationResult()

    for entry_id in entry_ids:
        try:
            # Get current entry
            entries = [e for e in get_passwords() if e[0] == entry_id]
            if not entries:
                result.add_failure(entry_id, "Entry not found")
                continue

            entry = entries[0]
            website = entry[1]
            username = entry[2]
            encrypted = entry[3]
            category = entry[4] or "General"
            notes = entry[5] or ""

            # Update favorite status
            update_password(
                entry_id=entry_id,
                website=website,
                username=username,
                encrypted_password=encrypted,
                category=category,
                notes=notes,
                favorite=favorite,
            )

            result.add_success(entry_id)
            action = "favorited" if favorite else "unfavorited"
            log_info(f"Bulk favorite: {action} entry {entry_id}")

        except Exception as e:
            result.add_failure(entry_id, str(e))
            log_warning(f"Bulk favorite toggle failed for entry {entry_id}: {e}")

    log_info(
        f"Bulk favorite toggle completed: {result.success_count} succeeded, "
        f"{result.failure_count} failed"
    )
    return result


def bulk_export(
    entry_ids: List[int],
) -> Tuple[List[Dict[str, Any]], BulkOperationResult]:
    """Export multiple entries to a list of dictionaries.

    Args:
        entry_ids: List of entry IDs to export.

    Returns:
        Tuple of (exported_entries, result).
        exported_entries is a list of dictionaries with decrypted data.
    """
    result = BulkOperationResult()
    exported = []

    for entry_id in entry_ids:
        try:
            # Get entry
            entries = [e for e in get_passwords() if e[0] == entry_id]
            if not entries:
                result.add_failure(entry_id, "Entry not found")
                continue

            entry = entries[0]
            (
                _id,
                website,
                username,
                encrypted,
                category,
                notes,
                created_at,
                updated_at,
                expiry_date,
                favorite,
            ) = entry

            # Decrypt password
            password = decrypt_password(encrypted)

            # Add to export list
            exported.append(
                {
                    "id": _id,
                    "website": website,
                    "username": username,
                    "password": password,
                    "category": category,
                    "notes": notes,
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "expiry_date": expiry_date,
                    "favorite": favorite,
                }
            )

            result.add_success(entry_id)

        except Exception as e:
            result.add_failure(entry_id, str(e))
            log_warning(f"Bulk export failed for entry {entry_id}: {e}")

    log_info(
        f"Bulk export completed: {result.success_count} entries exported, "
        f"{result.failure_count} failed"
    )
    return exported, result


def select_entries_by_filter(
    category: Optional[str] = None,
    search_term: Optional[str] = None,
    favorites_only: bool = False,
    expired_only: bool = False,
) -> List[int]:
    """Select entry IDs matching given filters.

    Args:
        category: Filter by category.
        search_term: Filter by search term in website/username.
        favorites_only: Only include favorites.
        expired_only: Only include expired entries.

    Returns:
        List of matching entry IDs.
    """
    entries = get_passwords(category=category, search_term=search_term)
    current_time = int(time.time())

    matching_ids = []
    for entry in entries:
        entry_id, _website, _username, _encrypted, _cat, _notes, _created, _updated, expiry, favorite = entry

        # Apply filters
        if favorites_only and not favorite:
            continue

        if expired_only:
            if not expiry or expiry > current_time:
                continue

        matching_ids.append(entry_id)

    return matching_ids
