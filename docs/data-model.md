# Data Model & Storage Specification

This document defines the structure of the vault database, supporting configuration files, and serialized backup/export formats.

## Database Overview

- Engine: SQLite 3
- File: `passwords.db`
- Pragmas: WAL mode, foreign keys on, secure delete optional.

## Tables

### passwords

| Column | Type | Description |
| --- | --- | --- |
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | Entry identifier. |
| `website` | TEXT NOT NULL | Label or URL. |
| `username` | TEXT NOT NULL | Login identifier. |
| `password` | BLOB NOT NULL | Fernet-encrypted secret. |
| `category` | TEXT DEFAULT 'General' | Logical grouping. |
| `notes` | TEXT | User-supplied notes (encrypted). |
| `created_at` | INTEGER | Unix timestamp (seconds). |
| `updated_at` | INTEGER | Last modification timestamp. |
| `expiry_date` | INTEGER NULL | Optional timestamp for rotation reminders. |
| `is_favorite` | INTEGER DEFAULT 0 | Boolean flag (0/1). |
| `strength_score` | INTEGER | Cached score (0–100). |
| `breach_count` | INTEGER DEFAULT 0 | Number of breaches detected (cached). |

### categories

| Column | Type | Description |
| --- | --- | --- |
| `name` | TEXT PRIMARY KEY | Category identifier. |
| `color` | TEXT | Hex or ANSI code. |
| `icon` | TEXT | Optional icon/font reference. |

### metadata (planned)

- Stores schema version, migration history, user preferences.

### tags & password_tags (planned)

- Enables many-to-many tagging once implemented. Schema draft:

  ```text
  tags(id INTEGER PK, name TEXT UNIQUE)
  password_tags(password_id INTEGER, tag_id INTEGER, PRIMARY KEY(password_id, tag_id))
  ```

## Configuration & Secret Files

| File | Purpose | Notes |
| --- | --- | --- |
| `secret.key` | Encrypted data-encryption-key (DEK). | Wrapped by KEK derived from master password. |
| `crypto.salt` | Salt for PBKDF2/Argon2id. | Stored as JSON with metadata (`iteration`, `salt`, `kdf_version`). |
| `auth.json` | Master password hash + settings. | Contains PBKDF2 parameters, 2FA flags, lockout counters. |
| `totp_config.json` | TOTP shared secret + metadata. | AES-encrypted blob keyed by KEK. |
| `breach_cache.json` | SHA-1 prefix cache for breach lookups. | Stores prefix -> max breach count, last_updated. |
| `settings.json` (planned) | UI/security preferences. | Helps sync CLI/GUI options. |

## Backup Formats

### Full Backup (zip)

```text
backup_YYYYMMDD_HHMMSS.zip
├── passwords.db
├── secret.key
├── crypto.salt
├── auth.json
├── totp_config.json (optional)
├── breach_cache.json
├── logs/password_manager.log (optional)
└── manifest.json
```

- `manifest.json` includes hashes (SHA-256) for every file and metadata (version, timestamp, platform).

### Encrypted Export (`.dat`)

- Envelope structure:

  ```text
  {
    "version": "2.1",
    "kdf": { "name": "PBKDF2", "iterations": 390000, "salt": "..." },
    "ciphertext": "...",  # base64
    "hmac": "..."
  }
  ```

- Payload (after decrypting `ciphertext`) is JSON array of entries with plaintext passwords, metadata, and audit state.

## Migration Strategy

1. Increment `schema_version` in the forthcoming `metadata` table.
2. Provide upgrade routines in `utils.database.migrate()` that execute within a transaction.
3. Maintain backward compatibility for exports by supporting previous envelope versions.
4. When removing columns, keep compatibility views until a major release.

## Data Integrity Checks

- Database integrity verified via `PRAGMA integrity_check` during backup jobs.
- Export/import flows compute HMAC-SHA256 of ciphertext and include the digest in the envelope.
- Restore operations validate manifest hashes before writing files.

## Data Retention & Privacy

- Logs redact usernames and hash entry IDs to avoid storing plaintext credentials.
- Clipboard auto-clear ensures secrets are not left in system clipboards.
- Optional data anonymization pipeline can drop metadata fields before exporting for audits.

## Future Enhancements

- Attachments table storing encrypted blobs plus metadata (filename, size, mime type).
- Per-entry password history table for retaining prior versions with rotation timestamps.
- Multi-profile support with separate namespaces inside a single database.
