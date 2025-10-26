# Current Status

Last updated: 2025-10-26

- Project: Secure Password Manager
- Version: v1.7.0 (from `VERSION.txt`)
- Maturity: Beta (per project classifiers)
- Python: 3.8+
- Interfaces: CLI (`apps.app:main`) and GUI (`apps.gui:main` via PyQt5)
- Storage: Local SQLite (`passwords.db`)

## Feature Snapshot

- Master password gate with PBKDF2-HMAC-SHA256 (100k iterations) stored in `auth.json`
- Symmetric encryption via Fernet for all stored passwords
- Optional encryption derived from master password for backups
- Categories, notes, expiry, favorites, search, generator, strength checks
- Two-Factor Authentication (TOTP) with QR provisioning
- Backup/restore (encrypted export; full zip backup including DB, key, and config)
- Security audit (weak/reused/duplicate/expired/breached checks)
- CLI with Colorama output and a full PyQt5 GUI
- Logging to `logs/password_manager.log`

## Key Files and Artifacts

- Database: `passwords.db`
- Crypto key: `secret.key` (Fernet)
- KDF salt: `crypto.salt` (for password-derived key option)
- Master auth store: `auth.json` (PBKDF2 salted hash)
- 2FA config: `totp_config.json` (TOTP secret, timestamp)
- Breach cache: `breach_cache.json` (HIBP k-anonymity prefix cache)
- Logs: `logs/password_manager.log`

## Test Suite

Tests are located in `tests/`:

- `test_crypto.py`: Encrypt/decrypt and key lifecycle
- `test_database.py`: Basic CRUD using an in-memory DB (standalone, not the utils db)
- `test_integration.py`: DB/crypto/auth/backup integration with tempfile and patching
- `test_password_analysis.py`: Strength, entropy, patterns, suggestions

Note: The integration test includes a workaround for SQLite locking during import; it manually re-inserts entries after export for determinism.

How to run locally (example):

```bash
# Optional: create & activate venv
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pytest -q
```

## Known Limitations / Risks

- Encryption key `secret.key` is stored locally in plaintext; if the OS user account or filesystem is compromised, encrypted data can be decrypted. Consider protecting the key (permissions, hardware/OS keyrings, or deriving from master password).
- Backups: "Full backup" zips can include `passwords.db`, `secret.key`, `auth.json`, `crypto.salt`; protect backup files with strong controls.
- Breach checks use the HaveIBeenPwned range API. Network issues fall back to treating passwords as not breached.
- No explicit DB migrations; schema is created if missing. Future changes should include migration steps.
- Clipboard operations (copy password) depend on OS clipboard and introduce exposure risk.
- Concurrency: SQLite DB_FILE is a single file; no concurrent write handling beyond SQLite defaults.

## Recent Highlights

- GUI tables improved (sorting, masking, favorites, context menu)
- Security audit scoring and issue breakdown
- Expiry handling and renewal
- Categories with default seeds and color field

## Health Summary

- Codebase organized into `apps/` and `utils/`, packaged via `pyproject.toml` with console scripts
- Logging present; no telemetry
- Tests present; CI not configured in-repo

If you need a release checklist or CI pipeline, see `docs/development.md` and `docs/roadmap.md`.
