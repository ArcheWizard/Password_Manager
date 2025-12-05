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
| `favorite` | INTEGER DEFAULT 0 | Boolean flag (0/1). |

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

Files are stored following XDG Base Directory specification:

- **Data directory** (`~/.local/share/secure-password-manager/` or `.data/` in dev mode)
- **Config directory** (`~/.config/secure-password-manager/` or `.data/` in dev mode)
- **Cache directory** (`~/.cache/secure-password-manager/` or `.data/` in dev mode)

| File | Location | Purpose | Notes |
| --- | --- | --- | --- |
| `secret.key` | Data | Encrypted data-encryption-key (DEK). | Wrapped by KEK derived from master password. Removed in password-derived mode. |
| `crypto.salt` | Data | Salt for PBKDF2. | Stored as JSON with metadata (`iterations`, `salt`, `kdf_version`, `updated_at`). |
| `auth.json` | Data | Master password hash + settings. | Contains PBKDF2 parameters, 2FA flags, lockout counters. |
| `totp_config.json` | Data | TOTP shared secret + metadata. | JSON with secret, created_at, account_name. |
| `breach_cache.json` | Cache | SHA-1 prefix cache for breach lookups. | Stores prefix -> max breach count, last_updated. |
| `settings.json` | Config | UI/security preferences. | Nested dictionary with key_management, clipboard, and browser_bridge settings. |
| `browser_bridge_tokens.json` | Data | Browser extension tokens. | Token store with fingerprints, expiry times, and metadata. |

## Backup Formats

### Full Backup (zip)

Created in the backup directory (`~/.local/share/secure-password-manager/backups/` or `.data/backups/` in dev mode):

```text
backup_YYYYMMDD_HHMMSS.zip
├── passwords.db
├── secret.key (if in file-key mode)
├── crypto.salt
├── auth.json
├── totp_config.json (if 2FA enabled)
├── breach_cache.json
├── settings.json
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
