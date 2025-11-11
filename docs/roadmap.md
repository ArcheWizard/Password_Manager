# Roadmap

This document outlines proposed improvements and priorities for future releases.

## Completed in v1.8.0

- ✅ KDF parameter versioning and configurability (PBKDF2 iterations, salt stored as JSON with metadata)
- ✅ Optional key protection: encrypt `secret.key` with KEK derived from master password
- ✅ Export integrity HMAC: envelope format (v2.1) with HMAC-SHA256 over ciphertext
- ✅ Transactional bulk import: use `executemany` to avoid SQLite locks and improve performance
- ✅ Backward compatibility: legacy salt files and export formats (v2.0) still supported

## Near-term

- Key management
  - Option to fully derive the vault key from the master password and remove file-based key (extends v1.8 protection)
  - Make KDF iterations and salt size user-configurable via settings
- KDF hardening
  - Add support for Argon2id or scrypt with parameter versioning
  - Allow per-user KDF selection and migration path
- UX
  - Auto-clear clipboard after timeout; minimize secret exposure in UI/CLI
  - Per-entry password history and last-rotated timestamp
  - Better category management (colors/icons in CLI)
- Security audit improvements
  - Batch breach checks with backoff and caching policies
  - Offline breach dictionary support

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
