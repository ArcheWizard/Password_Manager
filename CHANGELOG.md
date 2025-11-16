# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned

- Derive vault key from master password and/or protect `secret.key` using OS keyring
- KDF migration path (Argon2id/scrypt) with parameter versioning
- Improved import/restore with integrity validation and fewer SQLite lock issues
- Clipboard auto-clear and additional UX hardening
- CI/CD pipeline and code quality tooling (pylint, mypy, black)
- Password history tracking
- Cross-platform desktop application (PyInstaller/PyOxidizer)
- Docker container support

## [1.8.1] - 2025-11-11

### Added

- Comprehensive screenshot documentation for first-time setup flow
- Enhanced GUI layout and responsiveness in PyQt5 interface
- Improved visual feedback for password strength indicators

### Changed

- Updated README.md with complete screenshot gallery organized by feature
- Migrated screenshot references to use absolute GitHub URLs for PyPI compatibility
- Improved documentation structure in `docs/user-guide/`

### Fixed

- Screenshot display issues on PyPI package page
- Minor UI alignment issues in dialog windows
- Enhanced error handling for file I/O operations

## [1.8.0] - 2025-10-27

## [1.8.0] - 2025-10-27

### Added

- **KDF parameter versioning**: Introduced JSON-based metadata format for `crypto.salt` file including KDF algorithm identifier, version number, iteration count, salt value, and timestamp
  - Schema: `{"algorithm": "PBKDF2-HMAC-SHA256", "version": 1, "iterations": 100000, "salt": "<hex>", "timestamp": "<ISO8601>"}`
  - Enables future migration to Argon2id/scrypt with backward compatibility
  - Automatic migration from legacy raw salt files on first load
- **Optional key protection**: New cryptographic layer to protect `secret.key` with master password
  - `protect_key_with_master_password()`: Derives KEK from master password using PBKDF2-HMAC-SHA256, encrypts vault key with Fernet, stores as `secret.key.enc`
  - `unprotect_key()`: Decrypts protected key using master password-derived KEK
  - HMAC-SHA256 integrity verification of encrypted key file
  - `set_master_password_context()`: Maintains master password in memory during session for seamless key unwrapping
- **Export integrity protection**: Enhanced backup format with HMAC-SHA256 authentication
  - Export format v2.1: JSON envelope with `{"version": "2.1", "ciphertext": "<base64>", "hmac": "<hex>"}`
  - HMAC computed over ciphertext using vault encryption key
  - Prevents tampering and detects corrupted backups during import
- **Transactional bulk import**: Optimized password restore with single-transaction batch inserts
  - Replaced per-password `execute()` with `executemany()` for bulk operations
  - Eliminates SQLite lock contention and improves performance by ~10x on large imports
  - Maintains atomicity: all passwords imported or none on failure

### Changed

- **Crypto module enhancements**:
  - `crypto.salt` file format: Migrated to versioned JSON structure with automatic legacy conversion
  - `encrypt_password()` and `decrypt_password()`: Added `Optional[str]` type hint for `master_password` parameter
  - Enhanced error handling with specific exceptions for key protection failures
- **Database operations**:
  - `add_password()`: Changed `expiry_days` parameter from `int` with default to `Optional[int]` (default `None`)
  - `import_passwords()`: Refactored to use `executemany()` within single transaction
  - Improved type annotations with proper `Dict[str, Any]` and `Optional` usage
- **Backup module**:
  - `export_passwords()`: Generates v2.1 format with HMAC envelope
  - `import_passwords()`: Validates HMAC on v2.1 files, maintains backward compatibility with v2.0 raw Fernet tokens
  - Enhanced error messages with format version details

### Fixed

- Type annotation errors in `utils/database.py` for dictionary updates and optional parameters
- Return type inconsistency in `apps/app.py` login flow
- Import performance issues with large password databases
- Potential race conditions during concurrent backup operations

### Security

- Enhanced key derivation with versioned KDF parameters for future cryptographic agility
- Optional at-rest protection for vault encryption key
- Cryptographic authentication of backup files prevents silent corruption
- Improved defense against SQLite injection through parameterized bulk operations

## [1.7.0] - 2025-10-26

### Added

- **Two-Factor Authentication (TOTP)**:
  - `utils/two_factor.py`: Complete TOTP implementation with QR code provisioning
  - Time-based One-Time Password generation and verification (RFC 6238)
  - QR code generation for mobile authenticator app enrollment
  - CLI and GUI integration for 2FA setup and login
  - Per-user 2FA configuration stored in `auth.json`
- **Security Audit System**:
  - `utils/security_audit.py`: Comprehensive password health analysis
  - Weak password detection (strength score < 3/4)
  - Reused password identification across accounts
  - Duplicate password detection
  - Expired password tracking with configurable thresholds
  - Breach detection via Have I Been Pwned API (k-anonymity protocol)
  - Breach cache (`breach_cache.json`) for offline verification
  - Security scoring algorithm (0-100) with weighted factors
- **Password Expiration**:
  - Database schema: Added `expiry_date` column to `passwords` table
  - Configurable expiration periods during password creation
  - "Expiring Passwords" view with days-until-expiry indicator
  - Automatic expiration notifications in CLI and GUI
- **Favorites System**:
  - Database schema: Added `is_favorite` boolean flag
  - Quick-access marking for frequently used passwords
  - Dedicated "Favorites" filter view
  - Sort by favorites in password lists
- **GUI Improvements**:
  - Advanced filtering: All, Favorites, Expiring, Weak, Reused
  - Context menu for right-click password operations
  - Optional masked/unmasked password display toggle
  - Security Audit dedicated view with detailed recommendations
  - Real-time password strength indicator during entry
- **Backup Enhancements**:
  - Encrypted export format v2.0 with structured metadata
  - Category preservation in exports
  - Format version tagging for future compatibility
  - Improved import validation and error reporting

### Changed

- Documentation reorganization:
  - Created `docs/` directory structure with categorized guides
  - `docs/development/`: architecture.md, database-schema.md, security.md, contributing.md
  - `docs/build/`: Build and distribution guides
  - `docs/releases/`: roadmap.md, current-status.md
- README.md: Streamlined with documentation links and improved structure
- Enhanced CLI color schemes and progress indicators
- Improved error messages with actionable troubleshooting steps

### Fixed

- SQLite threading issues with connection pooling
- Race conditions in concurrent password operations
- Backup restore edge cases with malformed JSON
- GUI responsiveness during long-running operations (breach checks)

### Security

- Breach detection respects k-anonymity (only first 5 chars of SHA-1 hash transmitted)
- Local breach cache reduces API exposure
- Enhanced input validation for all user-supplied data
- Improved session timeout handling

## [1.6.0] - 2025-09-15

### Added

- Master password authentication with PBKDF2-HMAC-SHA256 (100,000 iterations)
- Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256) for password storage
- SQLite database backend with encrypted BLOB storage
- Password CRUD operations (Create, Read, Update, Delete)
- Category/tag organization system
- Password strength evaluation using zxcvbn library
- Cryptographically secure password generator
- Basic CLI with colored output (colorama)
- Backup and restore functionality (JSON export/import)
- Activity logging to file
- PyQt5 GUI with main window and dialogs
- PyPI package distribution

### Security

- Salted password hashing for master password (PBKDF2, 100K iterations)
- Local-only storage (no cloud dependencies)
- Encrypted database with Fernet (AES-128-CBC + HMAC)
- Secure key generation and storage

---

## Version Comparison

- **v1.8.0**: KDF versioning, optional key protection, HMAC backup integrity, bulk import optimization
- **v1.7.0**: 2FA/TOTP, security audit, breach checking, password expiration, favorites
- **v1.6.0**: Core functionality, master password, encryption, basic GUI

---

## Links

[Unreleased]: https://github.com/ArcheWizard/password-manager/compare/v1.8.1...HEAD
[1.8.1]: https://github.com/ArcheWizard/password-manager/compare/v1.8.0...v1.8.1
[1.8.0]: https://github.com/ArcheWizard/password-manager/compare/v1.7.0...v1.8.0
[1.7.0]: https://github.com/ArcheWizard/password-manager/compare/v1.6.0...v1.7.0
[1.6.0]: https://github.com/ArcheWizard/password-manager/releases/tag/v1.6.0
