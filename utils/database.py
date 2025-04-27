import sqlite3
from typing import List, Tuple

DB_FILE = 'passwords.db'

def init_db() -> None:
    """Initialize the database and create tables if not exists."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            website TEXT NOT NULL,
            username TEXT NOT NULL,
            password BLOB NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_password(website: str, username: str, encrypted_password: bytes) -> None:
    """Add a new password entry."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO passwords (website, username, password) VALUES (?, ?, ?)',
                   (website, username, encrypted_password))
    conn.commit()
    conn.close()

def get_passwords() -> List[Tuple[int, str, str, bytes]]:
    """Retrieve all password entries."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM passwords')
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_password(entry_id: int) -> None:
    """Delete a password entry by ID."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM passwords WHERE id = ?', (entry_id,))
    conn.commit()
    conn.close()
