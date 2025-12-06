"""Database migration utilities."""

import sqlite3
from typing import Callable, Dict, List

from secure_password_manager.utils.logger import log_info, log_warning
from secure_password_manager.utils.paths import get_database_path


def _get_db_file() -> str:
    """Get the database file path."""
    return str(get_database_path())


def get_schema_version() -> int:
    """Get the current schema version from the database."""
    conn = sqlite3.connect(_get_db_file())
    cursor = conn.cursor()

    # Check if metadata table exists
    cursor.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='metadata'
    """
    )

    if not cursor.fetchone():
        # No metadata table means version 0
        conn.close()
        return 0

    # Get version from metadata
    cursor.execute("SELECT value FROM metadata WHERE key = 'schema_version'")
    result = cursor.fetchone()
    conn.close()

    return int(result[0]) if result else 0


def set_schema_version(version: int) -> None:
    """Set the schema version in the database."""
    conn = sqlite3.connect(_get_db_file())
    cursor = conn.cursor()

    # Create metadata table if it doesn't exist
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """
    )

    # Update or insert version
    cursor.execute(
        """
        INSERT OR REPLACE INTO metadata (key, value)
        VALUES ('schema_version', ?)
    """,
        (str(version),),
    )

    conn.commit()
    conn.close()


def migration_001_add_password_history() -> None:
    """Migration 001: Add password_history table."""
    conn = sqlite3.connect(_get_db_file())
    cursor = conn.cursor()

    # Create password_history table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS password_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            password_id INTEGER NOT NULL,
            old_password BLOB NOT NULL,
            changed_at INTEGER NOT NULL,
            rotation_reason TEXT DEFAULT 'manual',
            changed_by TEXT DEFAULT 'user',
            FOREIGN KEY (password_id) REFERENCES passwords(id) ON DELETE CASCADE
        )
    """
    )

    # Create index for faster lookups
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_password_history_password_id
        ON password_history(password_id)
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_password_history_changed_at
        ON password_history(changed_at DESC)
    """
    )

    conn.commit()
    conn.close()

    log_info("Migration 001: password_history table created")


# Migration registry: version -> migration function
MIGRATIONS: Dict[int, Callable[[], None]] = {
    1: migration_001_add_password_history,
}


def get_pending_migrations() -> List[int]:
    """Get list of pending migration versions."""
    current_version = get_schema_version()
    max_version = max(MIGRATIONS.keys()) if MIGRATIONS else 0

    return [v for v in range(current_version + 1, max_version + 1) if v in MIGRATIONS]


def run_migrations(target_version: int = None) -> Dict[str, any]:
    """
    Run pending migrations up to target version.

    Args:
        target_version: If specified, migrate up to this version. Otherwise, migrate to latest.

    Returns:
        Dictionary with migration results.
    """
    current_version = get_schema_version()
    max_version = max(MIGRATIONS.keys()) if MIGRATIONS else 0

    if target_version is None:
        target_version = max_version

    if target_version > max_version:
        log_warning(
            f"Target version {target_version} exceeds max available {max_version}"
        )
        target_version = max_version

    if current_version >= target_version:
        log_info(f"Database already at version {current_version}, no migrations needed")
        return {
            "current_version": current_version,
            "target_version": target_version,
            "migrations_run": [],
            "success": True,
        }

    migrations_run = []
    errors = []

    for version in range(current_version + 1, target_version + 1):
        if version not in MIGRATIONS:
            log_warning(f"Migration {version} not found, skipping")
            continue

        try:
            log_info(f"Running migration {version}...")
            MIGRATIONS[version]()
            set_schema_version(version)
            migrations_run.append(version)
            log_info(f"Migration {version} completed successfully")
        except Exception as e:
            error_msg = f"Migration {version} failed: {str(e)}"
            log_warning(error_msg)
            errors.append(error_msg)
            # Stop on first error
            break

    final_version = get_schema_version()

    return {
        "initial_version": current_version,
        "final_version": final_version,
        "target_version": target_version,
        "migrations_run": migrations_run,
        "errors": errors,
        "success": final_version == target_version,
    }


def ensure_latest_schema() -> None:
    """Ensure database is at the latest schema version."""
    result = run_migrations()

    if not result["success"]:
        log_warning(f"Schema migration incomplete: {result}")
    elif result["migrations_run"]:
        log_info(f"Schema updated to version {result['final_version']}")
