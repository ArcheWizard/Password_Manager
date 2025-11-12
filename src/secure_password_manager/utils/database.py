"""Database utilities for Password Manager."""

import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple

from secure_password_manager.utils.paths import get_database_path


def _get_db_file() -> str:
    """Get the database file path."""
    return str(get_database_path())


def init_db() -> None:
    """Initialize the database and create tables if not exists."""
    conn = sqlite3.connect(_get_db_file())
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

    conn.commit()
    conn.close()


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

    conn = sqlite3.connect(_get_db_file())
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
    conn.commit()
    conn.close()


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
    conn = sqlite3.connect(_get_db_file())
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
    rows = cursor.fetchall()
    conn.close()
    return rows


def delete_password(entry_id: int) -> None:
    """Delete a password entry by ID."""
    conn = sqlite3.connect(_get_db_file())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM passwords WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()


def update_password(
    entry_id: int,
    website: Optional[str] = None,
    username: Optional[str] = None,
    encrypted_password: Optional[bytes] = None,
    category: Optional[str] = None,
    notes: Optional[str] = None,
    expiry_days: Optional[int] = None,
    favorite: Optional[bool] = None,
) -> None:
    """Update a password entry with new information."""
    conn = sqlite3.connect(_get_db_file())
    cursor = conn.cursor()

    # Get current values
    cursor.execute("SELECT * FROM passwords WHERE id = ?", (entry_id,))
    current = cursor.fetchone()

    if not current:
        conn.close()
        raise ValueError(f"No password entry with ID {entry_id}")

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
        expiry_date = current_time + (expiry_days * 86400) if expiry_days > 0 else None
        updates["expiry_date"] = expiry_date

    if favorite is not None:
        updates["favorite"] = 1 if favorite else 0

    # Build update query
    set_clause = ", ".join(f"{key} = ?" for key in updates.keys())
    query = f"UPDATE passwords SET {set_clause} WHERE id = ?"

    # Execute update
    params = list(updates.values()) + [entry_id]
    cursor.execute(query, params)
    conn.commit()
    conn.close()


def get_categories() -> List[Tuple[str, str]]:
    """Get list of all categories with their colors."""
    conn = sqlite3.connect(_get_db_file())
    cursor = conn.cursor()
    cursor.execute("SELECT name, color FROM categories")
    categories = cursor.fetchall()
    conn.close()
    return categories


def add_category(name: str, color: str = "blue") -> None:
    """Add a new category."""
    conn = sqlite3.connect(_get_db_file())
    cursor = conn.cursor()
    cursor.execute("INSERT INTO categories (name, color) VALUES (?, ?)", (name, color))
    conn.commit()
    conn.close()


def get_expiring_passwords(days: int = 30) -> List[Tuple]:
    """Get passwords expiring within specified days."""
    expiry_threshold = int(time.time()) + (days * 86400)

    conn = sqlite3.connect(_get_db_file())
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM passwords
        WHERE expiry_date IS NOT NULL
        AND expiry_date < ?
        AND expiry_date > ?
    """,
        (expiry_threshold, int(time.time())),
    )

    rows = cursor.fetchall()
    conn.close()
    return rows
