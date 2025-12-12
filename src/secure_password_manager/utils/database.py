"""Database utilities for Password Manager.

This module provides a centralized database interface with:
- WAL mode for better concurrency
- Connection pooling to prevent locks
- Thread-safe operations
- Proper transaction boundaries
- Automatic cleanup
"""

import sqlite3
import threading
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple

from secure_password_manager.utils import config
from secure_password_manager.utils.logger import log_info, log_warning
from secure_password_manager.utils.paths import get_database_path


# Thread-local storage for connections
_thread_local = threading.local()
_connection_lock = threading.RLock()


def _get_db_file() -> str:
    """Get the database file path."""
    return str(get_database_path())


def _initialize_connection(conn: sqlite3.Connection) -> None:
    """Initialize a database connection with optimal settings."""
    # Enable WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode=WAL")

    # Normal synchronous mode (faster while still safe with WAL)
    conn.execute("PRAGMA synchronous=NORMAL")

    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys=ON")

    # Set busy timeout (30 seconds)
    conn.execute("PRAGMA busy_timeout=30000")

    # Optimize cache size (2MB)
    conn.execute("PRAGMA cache_size=-2000")


def _get_connection() -> sqlite3.Connection:
    """Get or create a thread-local database connection.

    Each thread gets its own connection to prevent lock contention.
    Connections are cached per thread for performance.
    """
    if not hasattr(_thread_local, 'connection') or _thread_local.connection is None:
        with _connection_lock:
            conn = sqlite3.connect(_get_db_file(), timeout=30.0, check_same_thread=False)
            _initialize_connection(conn)
            _thread_local.connection = conn
            log_info("Created new database connection for thread")

    return _thread_local.connection


def close_connection() -> None:
    """Close the thread-local database connection.

    This should be called when a thread is done with database operations,
    especially in long-running threads or background workers.
    """
    if hasattr(_thread_local, 'connection') and _thread_local.connection is not None:
        try:
            _thread_local.connection.close()
            log_info("Closed database connection for thread")
        except Exception as e:
            log_warning(f"Error closing database connection: {e}")
        finally:
            _thread_local.connection = None


@contextmanager
def get_db_connection():
    """Context manager for database operations with automatic commit/rollback.

    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ...")
            # conn.commit() is called automatically on success
            # conn.rollback() is called automatically on exception
    """
    conn = _get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_db() -> None:
    """Initialize the database and create tables if not exists."""
    from secure_password_manager.utils.migrations import ensure_latest_schema

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Main passwords table with additional fields
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS passwords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    website TEXT NOT NULL,
                    username TEXT NOT NULL,
                    password BLOB NOT NULL,
                    category TEXT DEFAULT 'General',
                    notes TEXT DEFAULT '',
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    expiry_date INTEGER DEFAULT NULL,
                    favorite BOOLEAN DEFAULT 0
                )
            """
            )

            # Categories table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    color TEXT DEFAULT 'blue'
                )
            """
            )

            # Insert default categories if they don't exist
            default_categories = [
                ("General", "blue"),
                ("Work", "red"),
                ("Personal", "green"),
                ("Finance", "purple"),
                ("Social", "orange"),
            ]

            for category, color in default_categories:
                cursor.execute(
                    "INSERT OR IGNORE INTO categories (name, color) VALUES (?, ?)",
                    (category, color),
                )

        # Run any pending migrations (uses its own connection)
        ensure_latest_schema()
    except Exception as e:
        log_warning(f"Error initializing database: {e}")
        raise


def add_password(
    website: str,
    username: str,
    encrypted_password: bytes,
    category: str = "General",
    notes: str = "",
    expiry_days: Optional[int] = None,
) -> None:
    """Add a new password entry."""
    current_time = int(time.time())
    expiry_date = current_time + (expiry_days * 86400) if expiry_days else None

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO passwords
            (website, username, password, category, notes, created_at, updated_at, expiry_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                website,
                username,
                encrypted_password,
                category,
                notes,
                current_time,
                current_time,
                expiry_date,
            ),
        )


def get_passwords(
    category: Optional[str] = None,
    search_term: Optional[str] = None,
    show_expired: bool = True,
) -> List[Tuple]:
    """
    Retrieve password entries with filtering options.

    Args:
        category: Filter by category name
        search_term: Search in website and username
        show_expired: Whether to include expired passwords
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = "SELECT * FROM passwords"
        params = []
        conditions = []

        # Apply filters
        if category:
            conditions.append("category = ?")
            params.append(category)

        if search_term:
            conditions.append("(website LIKE ? OR username LIKE ?)")
            params.extend([f"%{search_term}%", f"%{search_term}%"])

        if not show_expired:
            conditions.append("(expiry_date IS NULL OR expiry_date > ?)")
            params.append(int(time.time()))

        # Construct WHERE clause if we have conditions
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Order by favorite first, then by website
        query += " ORDER BY favorite DESC, website ASC"

        cursor.execute(query, params)
        return cursor.fetchall()


def delete_password(entry_id: int) -> None:
    """Delete a password entry by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM passwords WHERE id = ?", (entry_id,))


def update_password(
    entry_id: int,
    website: Optional[str] = None,
    username: Optional[str] = None,
    encrypted_password: Optional[bytes] = None,
    category: Optional[str] = None,
    notes: Optional[str] = None,
    expiry_days: Optional[int] = None,
    favorite: Optional[bool] = None,
    rotation_reason: str = "manual",
) -> None:
    """Update a password entry with new information."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get current values
        cursor.execute("SELECT * FROM passwords WHERE id = ?", (entry_id,))
        current = cursor.fetchone()

        if not current:
            conn.rollback()
            raise ValueError(f"Password entry {entry_id} not found")

        # Map column names to indices
        columns = [
            "id",
            "website",
            "username",
            "password",
            "category",
            "notes",
            "created_at",
            "updated_at",
            "expiry_date",
            "favorite",
        ]
        col_idx = {col: i for i, col in enumerate(columns)}

        # If password is being changed, save old password to history
        if (
            encrypted_password is not None
            and encrypted_password != current[col_idx["password"]]
        ):
            # Check if password history is enabled
            history_enabled = config.get_setting("password_history.enabled", True)

            if history_enabled:
                add_password_history(
                    password_id=entry_id,
                    old_password=current[col_idx["password"]],
                    rotation_reason=rotation_reason,
                    changed_by="user",
                )

        # Prepare update values
        current_time = int(time.time())
        updates: Dict[str, Any] = {"updated_at": current_time}

        if website is not None:
            updates["website"] = website

        if username is not None:
            updates["username"] = username

        if encrypted_password is not None:
            updates["password"] = encrypted_password

        if category is not None:
            updates["category"] = category

        if notes is not None:
            updates["notes"] = notes

        if expiry_days is not None:
            updates["expiry_date"] = current_time + (expiry_days * 86400)

        if favorite is not None:
            updates["favorite"] = int(favorite)

        # Build update query
        set_clause = ", ".join(f"{key} = ?" for key in updates.keys())
        query = f"UPDATE passwords SET {set_clause} WHERE id = ?"

        # Execute update
        params = list(updates.values()) + [entry_id]
        cursor.execute(query, params)


def get_categories() -> List[Tuple[str, str]]:
    """Get list of all categories with their colors."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, color FROM categories")
        return cursor.fetchall()


def add_category(name: str, color: str = "blue") -> None:
    """Add a new category."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO categories (name, color) VALUES (?, ?)", (name, color))


def get_expiring_passwords(days: int = 30) -> List[Tuple]:
    """Get passwords expiring within the specified number of days."""
    current_time = int(time.time())
    expiry_threshold = current_time + (days * 86400)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM passwords
            WHERE expiry_date IS NOT NULL
            AND expiry_date > ?
            AND expiry_date <= ?
            ORDER BY expiry_date ASC
        """,
            (current_time, expiry_threshold),
        )
        return cursor.fetchall()


def add_password_history(
    password_id: int,
    old_password: bytes,
    rotation_reason: str = "manual",
    changed_by: str = "user",
) -> None:
    """Record a password change in history."""
    current_time = int(time.time())

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Add history entry
        cursor.execute(
            """
            INSERT INTO password_history
            (password_id, old_password, changed_at, rotation_reason, changed_by)
            VALUES (?, ?, ?, ?, ?)
        """,
            (password_id, old_password, current_time, rotation_reason, changed_by),
        )

        # Enforce retention limit
        max_versions = config.get_setting("password_history.max_versions", 10)

        if max_versions > 0:
            cursor.execute(
                """
                DELETE FROM password_history
                WHERE password_id = ?
                AND id NOT IN (
                    SELECT id FROM password_history
                    WHERE password_id = ?
                    ORDER BY changed_at DESC
                    LIMIT ?
                )
            """,
                (password_id, password_id, max_versions),
            )


def get_password_history(password_id: int, limit: int = 10) -> List[Tuple]:
    """Get password change history for an entry."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, password_id, old_password, changed_at, rotation_reason, changed_by
            FROM password_history
            WHERE password_id = ?
            ORDER BY changed_at DESC
            LIMIT ?
        """,
            (password_id, limit),
        )
        return cursor.fetchall()


def get_all_password_history(limit: int = 50) -> List[Tuple]:
    """
    Get recent password changes across all entries.

    Args:
        limit: Maximum number of history entries to return.

    Returns:
        List of tuples with password details and history.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                ph.id,
                ph.password_id,
                p.website,
                p.username,
                ph.changed_at,
                ph.rotation_reason,
                ph.changed_by
            FROM password_history ph
            JOIN passwords p ON ph.password_id = p.id
            ORDER BY ph.changed_at DESC
            LIMIT ?
        """,
            (limit,),
        )
        return cursor.fetchall()


def delete_password_history(password_id: int) -> None:
    """Delete all history for a password entry."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM password_history WHERE password_id = ?", (password_id,))
        log_info(f"Password history deleted for entry {password_id}")
