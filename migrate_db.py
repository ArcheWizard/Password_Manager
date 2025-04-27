"""Database migration script to update schema."""
import sqlite3
import sys
import os
import time

def migrate_database():
    """Update the database schema to the latest version."""
    db_file = 'passwords.db'
    
    # Check if database exists
    if not os.path.exists(db_file):
        print(f"Database file {db_file} not found.")
        return False
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # Start a transaction
        conn.execute("BEGIN TRANSACTION")
        
        # First, retrieve existing data
        cursor.execute("SELECT id, website, username, password FROM passwords")
        existing_data = cursor.fetchall()
        
        # Create a new table with the full schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS passwords_new (
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
        ''')
        
        # Insert existing data into new table with defaults for new columns
        current_time = int(time.time())
        for row in existing_data:
            cursor.execute('''
                INSERT INTO passwords_new (id, website, username, password, 
                                          category, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'General', '', ?, ?)
            ''', (row[0], row[1], row[2], row[3], current_time, current_time))
        
        # Drop the old table and rename the new one
        cursor.execute("DROP TABLE passwords")
        cursor.execute("ALTER TABLE passwords_new RENAME TO passwords")
        
        # Create categories table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT DEFAULT 'blue'
            )
        ''')
        
        # Insert default categories if they don't exist
        default_categories = [
            ('General', 'blue'),
            ('Work', 'red'),
            ('Personal', 'green'),
            ('Finance', 'purple'),
            ('Social', 'orange')
        ]
        
        for category, color in default_categories:
            cursor.execute('INSERT OR IGNORE INTO categories (name, color) VALUES (?, ?)',
                          (category, color))
        
        # Commit the transaction
        conn.commit()
        print("Database migration completed successfully!")
        return True
        
    except sqlite3.Error as e:
        # Rollback in case of error
        conn.rollback()
        print(f"Database migration failed: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()