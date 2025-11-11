# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning where practical.

## [Unreleased]

- Consider deriving vault key from master password and/or protecting `secret.key`
- KDF migration path (Argon2id/scrypt) with parameter versioning
- Improved import/restore with integrity validation and fewer SQLite lock issues
- Clipboard auto-clear and additional UX hardening
- CI pipeline and code quality tooling

## [1.8.1] - 2025-11-11

### Added

- Improved GUI responsiveness
- Enhanced error handling

### Fixed

- Minor bug fixes
- UI improvements

## [1.8.0] - Previous Release

- Full feature set as documented

## [1.8.0] - 2025-10-27

### Added

- **KDF parameter versioning**: `crypto.salt` now stores JSON metadata including KDF algorithm, version, iterations, salt, and timestamp for forward compatibility and migration paths
- **Optional key protection**: New functions `protect_key_with_master_password()` and `unprotect_key()` allow encrypting `secret.key` with a KEK derived from the master password; stored in `secret.key.enc` with HMAC integrity check
- **Export integrity HMAC**: Encrypted backups (v2.1 format) now include an HMAC-SHA256 tag over the ciphertext in a JSON envelope; verified on import to detect tampering
- **Transactional bulk import**: `import_passwords()` now uses `executemany` in a single transaction to avoid SQLite locking issues and improve performance
- **Master password context**: New `set_master_password_context()` function called at login to enable protected key unwrapping without requiring password re-entry

### Changed

- `crypto.salt` format: migrates legacy raw salt files to versioned JSON on first load; backward compatible
- `export_passwords()` and `import_passwords()`: new envelope format (v2.1) with HMAC; still reads legacy v2.0 raw tokens
- `encrypt_password()` and `decrypt_password()` now use `Optional[str]` type hints for `master_password` parameter
- `add_password()` signature: `expiry_days` is now `Optional[int]` instead of `int` with default `None`
- `utils/database.py` now imports `Dict` and `Any` for proper type annotations

### Fixed

- Type errors in `utils/database.py` (updates dict) and `apps/app.py` (login return path)
- Import no longer adds small delays between operations; uses bulk insert instead

## [1.7.0] - 2025-10-26

### Added

- Two-Factor Authentication (TOTP) with QR provisioning (`utils/two_factor.py`) and CLI/GUI integration
- Security audit: weak/reused/duplicate/expired/breached checks with scoring (`utils/security_audit.py`), breach cache (`breach_cache.json`)
- Password expiry support and expiring-passwords view
- Favorites support and improved listing/sorting
- GUI improvements: filters, masked display, context menu, and audit view
- Encrypted export format with metadata version `2.0` and categories included
- Comprehensive documentation under `docs/` (architecture, database, security, development, roadmap, current status)

### Changed

- README updated with docs links, testing instructions, and refined security notes

### Fixed

- Various usability improvements in CLI/GUI workflows
- Minor robustness improvements around backup/restore and logging

## [1.6.0] - 2025-xx-xx

- Prior releases with core features: master password auth (PBKDF2), Fernet encryption, basic CRUD, categories, generator, strength checks, backup/restore, and initial GUI.

[Unreleased]: https://github.com/ArcheWizard/password-manager/compare/v1.7.0...HEAD
[1.7.0]: https://github.com/ArcheWizard/password-manager/releases/tag/v1.7.0
