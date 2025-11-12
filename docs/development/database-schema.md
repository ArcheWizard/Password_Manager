# Database

This document describes the local SQLite storage used by Secure Password Manager.

## Engine and Location

- Engine: SQLite3
- Default file: `passwords.db`
- Created automatically by `utils.database.init_db()` on first run

## Schema

### Table: passwords

Columns:

- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `website` TEXT NOT NULL
- `username` TEXT NOT NULL
- `password` BLOB NOT NULL  — encrypted bytes (Fernet)
- `category` TEXT DEFAULT 'General'
- `notes` TEXT DEFAULT ''
- `created_at` INTEGER NOT NULL — epoch seconds
- `updated_at` INTEGER NOT NULL — epoch seconds
- `expiry_date` INTEGER DEFAULT NULL — epoch seconds
- `favorite` BOOLEAN DEFAULT 0

### Table: categories

Columns:

- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `name` TEXT NOT NULL UNIQUE
- `color` TEXT DEFAULT 'blue'

Seed data inserted on init:

- General (blue), Work (red), Personal (green), Finance (purple), Social (orange)

## Access Patterns

- Reads are performed via `get_passwords(category=None, search_term=None, show_expired=True)`
  - WHERE clause composed dynamically by filters
  - Ordered by `favorite DESC, website ASC`
- Writes via `add_password(...)` and `update_password(...)`
- Deletes via `delete_password(id)`
- Expiry queries via `get_expiring_passwords(days)`
- Category management via `get_categories()` and `add_category(name, color)`

## Data Flow

- Passwords are encrypted before insert using `utils.crypto.encrypt_password`
- Decryption occurs in UI layers (CLI/GUI) just-in-time for display or export

## Indexing and Performance

- No explicit indexes are defined beyond the primary keys
- For large datasets, consider adding indexes on (`website`, `username`), `category`, and `expiry_date`

## Backups and Restore

- Encrypted export serializes decrypted entries to JSON and encrypts with a password-derived key; see `docs/security.md`
- Full backup is a zip containing DB and key/config files
- Restore replaces local files and keeps timestamped `.bak` copies

## Migrations

- Current schema is created if missing; no migration framework is included
- For future schema changes, add a `schema_version` table and incremental migrations

## Testing Notes

- Unit test `tests/test_database.py` uses an isolated in-memory DB and direct SQL to validate CRUD basics
- Integration tests patch `DB_FILE` to a tempfile
