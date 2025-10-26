# Roadmap

This document outlines proposed improvements and priorities for future releases.

## Near-term

- Key management
  - Option to derive the vault key from the master password and remove plaintext `secret.key`
  - Encrypt `secret.key` with a KEK derived from master password (transition step)
- KDF hardening
  - Configurable PBKDF2 iterations and salt; consider Argon2id/scrypt with parameter versioning
- Import/Export
  - Robust import that avoids SQLite locks and supports transactional bulk insert
  - Validate backup file metadata and integrity (HMAC)
- Security audit
  - Batch breach checks with backoff and caching policies
  - Offline breach dictionary support
- UX
  - Auto-clear clipboard after timeout; minimize secret exposure in UI/CLI
  - Per-entry password history and last-rotated timestamp
  - Better category management (colors/icons)

## Mid-term

- Configurability
  - Allow custom data directory and DB path
  - Enable/disable breach checks; proxy configuration
- Platform integration
  - OS keyring integration for key storage
  - System notifications for upcoming expirations
- Data model
  - Add tags table and many-to-many tagging for entries
  - Attachments support (securely encrypted blobs)
- Testing/CI
  - Add GitHub Actions with matrix (Linux/macOS/Windows), artifacts, and coverage
  - Property-based tests for crypto and DB ops

## Long-term

- Sync and portability
  - Optional sync providers (self-hosted, file sync) with end-to-end encryption
  - Importers from other managers (CSV/JSON formats)
- Security
  - Key rotation, per-entry nonces, and envelope encryption design
  - Hardware-backed keys where available (TPM/Secure Enclave)
- Packaging
  - Cross-platform desktop app builds (PyInstaller/Briefcase)
  - Flatpak/AppImage/Win installer releases

## Release Cadence & Versioning

- Semantic-ish versioning; current: v1.7.0
- Keep `VERSION.txt` as single source of version truth for packaging
- Maintain a CHANGELOG and security advisories as features mature
