# Security

This document describes the security model, cryptography choices, and operational considerations for Secure Password Manager.

## Threat Model (summary)

- Protect against local database disclosure by encrypting secrets at rest
- Prevent unauthorized app access via master password and optional 2FA
- Reduce risk from breached/reused/weak passwords via audits and guidance
- Accept that if `secret.key` and the database are both stolen, the vault is decryptable

## Cryptography

- Algorithm: Fernet (symmetric authenticated encryption; AES-128-CBC + HMAC; provided by the `cryptography` library)
- Default key: 32-byte key stored in `secret.key` (generated on first use)
- Optional password-derived key: PBKDF2-HMAC-SHA256, 100,000 iterations, salt stored in `crypto.salt`
  - Used by `encrypt_password(..., master_password=...)` for export/import sealing
  - Not used by default for the at-rest vault (which uses the file key)

Notes:

- The module imports `Scrypt` but currently only PBKDF2 is used for derivation
- Consider migrating to Argon2id or scrypt for KDF in future versions

## Master Password

- Stored as salted PBKDF2-HMAC-SHA256 hash in `auth.json`
- Format: `<salt_hex>:<hash_hex>`; 32-byte random salt, 100k iterations
- Verification is constant-time by re-deriving with stored salt

## Two-Factor Authentication (2FA)

- TOTP-based via `pyotp`
- Setup process generates a secret and a QR code written to `totp_qr.png`
- Config saved in `totp_config.json` with secret and metadata
- Verification done at login when 2FA is enabled

## Security Audit

- Weakness checks include strength score, patterns, entropy
- Reuse/duplicate detection across decrypted in-memory values
- Expiry detection by comparing `expiry_date` timestamps
- Breach checks via HaveIBeenPwned range API (k-anonymity: only SHA-1 prefix is sent)
- Breach responses cached by prefix in `breach_cache.json` to reduce network calls
- Overall score (0–100) based on weighted deductions

## Backup/Restore

- Encrypted export: entries are decrypted, serialized to JSON, then encrypted with a key derived from a user-supplied password (PBKDF2 + salt). Output is a `.dat` file.
- Full backup (zip): includes `passwords.db`, `secret.key`, `auth.json`, `crypto.salt`, and the encrypted export + metadata.
- Restore: verifies the archive and replaces local files, keeping timestamped backups of previous files.

## Operational Security Guidelines

- File permissions: restrict read access to `secret.key`, `auth.json`, `crypto.salt`, and the database
- Backups: treat full backups as sensitive; store in secure locations (encrypted storage)
- Clipboard: copied passwords persist in clipboard history on some systems; clear clipboard if possible
- Networking: breach checks require outbound HTTPS; on failure, the app errs on the side of "not breached"
- Logging: avoid logging plaintext secrets; current logs focus on operations, not contents

## Known Gaps / Future Hardening

- At-rest key protection: support deriving the vault key from the master password (and removing `secret.key`), or encrypt `secret.key` with a KEK derived from the master password
- Stronger KDF: migrate to Argon2id (memory-hard), make iterations/salt configurable, version KDF parameters
- Secure UI: optional password reveal timeouts and redactions; auto-clear clipboard
- DB hardening: add integrity checks and optional per-entry nonces or key rotation strategy
- Secrets storage: optional OS keyring integration (e.g., Secret Service, Keychain, Credential Manager)
