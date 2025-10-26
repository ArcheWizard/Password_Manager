import os
import sqlite3
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Use an in-memory database for testing
DB_FILE = ":memory:"


def test_database_operations():
    """Test full database operations cycle (create, add, get, delete)."""
    # Initialize in-memory database
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            website TEXT NOT NULL,
            username TEXT NOT NULL,
            password BLOB NOT NULL
        )
    """
    )

    # Test adding a password
    website = "example.com"
    username = "testuser"
    password = b"encrypted_password_bytes"

    cursor.execute(
        "INSERT INTO passwords (website, username, password) VALUES (?, ?, ?)",
        (website, username, password),
    )

    # Test getting passwords
    cursor.execute("SELECT * FROM passwords")
    results = cursor.fetchall()
    assert len(results) == 1
    assert results[0][1] == website
    assert results[0][2] == username
    assert results[0][3] == password

    # Test deleting a password
    cursor.execute("DELETE FROM passwords WHERE id = ?", (results[0][0],))
    cursor.execute("SELECT * FROM passwords")
    results = cursor.fetchall()
    assert len(results) == 0

    conn.close()
