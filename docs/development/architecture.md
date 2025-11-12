# Architecture

This document describes the high-level architecture of Secure Password Manager, its modules, and the main flows for authentication, storage, encryption, and auditing.

## Overview

- CLI entrypoint: `apps.app:main`
- GUI entrypoint: `apps.gui:main` (PyQt5)
- Core utilities under `utils/`:
  - `auth.py`: Master password hashing/verification
  - `crypto.py`: Key management and Fernet encryption
  - `database.py`: SQLite schema and CRUD
  - `password_analysis.py`: Entropy/strength and generator
  - `security_analyzer.py`: HIBP breach checks and analysis
  - `security_audit.py`: Full vault audit and scoring
  - `two_factor.py`: TOTP setup/verify
  - `backup.py`: Encrypted export, full backup/restore
  - `logger.py`: Central logging
  - `ui.py` / `interactive.py`: CLI formatting and helpers

## Runtime Components

- Database: `passwords.db` (SQLite)
- Config/secrets: `secret.key`, `crypto.salt`, `auth.json`, `totp_config.json`
- Cache/logs: `breach_cache.json`, `logs/password_manager.log`

## Main Flow (CLI)

```text
User → apps.app.main → init_db
                 ↳ login() → utils.auth.authenticate
                               ↳ PBKDF2 verify (auth.json)
                               ↳ optional 2FA (utils.two_factor)
                 ↳ menus → CRUD ops (utils.database)
                               ↳ encrypt/decrypt (utils.crypto)
                 ↳ backup/restore (utils.backup)
                 ↳ security audit (utils.security_audit → analyzer/password_analysis)
                 ↳ logging (utils.logger)
```

## Main Flow (GUI)

```text
apps.gui.PasswordManagerApp
  ↳ init_db, authenticate (master pw), then build tabs
  ↳ Passwords Tab: filters/search → get_passwords → decrypt for view
  ↳ Security Tab: run_security_audit → displays score/issues
  ↳ Backup Tab: export/import/full-backup/restore
  ↳ Context actions: copy/mask/favorite/edit/delete
```

## Encryption & Key Management

- Symmetric crypto: `cryptography.fernet.Fernet` (32-byte key)
- Key file: `secret.key` (generated on first use if missing)
- Optional password-derived key: `derive_key_from_password()` (PBKDF2-HMAC-SHA256, 100k; salt at `crypto.salt`) used when a `master_password` is supplied to export/import encryption.
- Stored vault passwords are encrypted with the file key by default.

## Authentication and 2FA

- Master password: stored as `salt:hash` using PBKDF2-HMAC-SHA256 (100k iterations) in `auth.json`.
- Two-Factor Authentication (TOTP): `pyotp`-based secret saved in `totp_config.json`, QR provisioning via `qrcode`.

## Security Audit

- Strength checks: `password_analysis.evaluate_password_strength` + entropy/patterns.
- Reuse/duplicate detection: in-memory map across decrypted values.
- Expiry detection: compares `expiry_date` timestamps.
- Breach checks: HaveIBeenPwned range API (k-anonymity), cached by prefix in `breach_cache.json`.
- Score (0–100): weighted deductions for weak/reused/duplicate/expired/breached.

## Backup and Restore

- Export: decrypts entries, serializes to JSON, encrypts the JSON with a key derived from the provided master password; writes `.dat`.
- Full backup: creates a zip with `passwords.db`, `secret.key`, `auth.json`, `crypto.salt`, and the encrypted export plus metadata.
- Restore: extracts and copies files back; creates `.bak<ts>` copies of current files.

## Logging

- Central logger to file and stdout via `utils.logger`.
- User-visible views via CLI and GUI.

## Error Handling & Edge Cases

- SQLite locks: integration tests use delays/workarounds; write operations are simple transactions.
- Network errors in breach checks are swallowed; analysis treats as not breached.
- Clipboard exposure acknowledged; passwords copied via `pyperclip`.

## Extensibility Notes

- Replace Fernet/file key with OS keyring or hardware-backed keys.
- Pluggable breach providers or offline breach dictionaries.
- The GUI uses Qt widgets and can add tabs/actions without touching core logic.
