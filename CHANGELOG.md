# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning where practical.

## [Unreleased]

- Consider deriving vault key from master password and/or protecting `secret.key`
- KDF migration path (Argon2id/scrypt) with parameter versioning
- Improved import/restore with integrity validation and fewer SQLite lock issues
- Clipboard auto-clear and additional UX hardening
- CI pipeline and code quality tooling

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
