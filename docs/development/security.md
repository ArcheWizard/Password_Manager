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
- **NEW in v1.8**: Optional key protection: `secret.key` can be wrapped (encrypted) with a KEK derived from the master password and stored in `secret.key.enc`. When protected, the master password context must be set at login to unwrap the vault key.
- Password-derived key (for exports/imports): PBKDF2-HMAC-SHA256, iterations and salt configurable, stored in `crypto.salt` as JSON with KDF version metadata
  - Current default: 100,000 iterations (v1)
  - Used by `encrypt_with_password_envelope()` for export/import sealing; returns separate encryption + HMAC keys
- **NEW in v1.8**: KDF versioning in `crypto.salt`: stores `{"kdf": "PBKDF2HMAC", "version": 1, "iterations": 100000, "salt": "<base64>", "updated_at": <ts>}` for forward compatibility; legacy raw salt files are auto-migrated on first load.

Notes:

- The module supports multiple KDF params for future flexibility (Argon2id/scrypt can be added)
- Backward compatible: legacy raw salt files and raw Fernet tokens (v2.0 exports) are still supported

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

- **NEW in v1.8**: Encrypted export with integrity HMAC: entries are decrypted, serialized to JSON, then encrypted with a key derived from a user-supplied password (PBKDF2 + salt). The ciphertext is wrapped in a JSON envelope containing metadata and an HMAC-SHA256 integrity tag. Output is a `.dat` file.
  - Export format version: `2.1` (includes `{"format": "spm-export", "version": "2.1", "kdf": {...}, "ciphertext": "<base64>", "hmac": "<hex>", "hmac_alg": "HMAC-SHA256"}`)
  - Import verifies HMAC before decryption; falls back to legacy raw token format (v2.0) for backward compatibility.
- Full backup (zip): includes `passwords.db`, `secret.key` (or `secret.key.enc` if protected), `auth.json`, `crypto.salt`, and the encrypted export + metadata.
- Restore: verifies the archive and replaces local files, keeping timestamped backups of previous files.

## Operational Security Guidelines

- File permissions: restrict read access to `secret.key`, `auth.json`, `crypto.salt`, and the database
- Backups: treat full backups as sensitive; store in secure locations (encrypted storage)
- Clipboard: copied passwords persist in clipboard history on some systems; clear clipboard if possible
- Networking: breach checks require outbound HTTPS; on failure, the app errs on the side of "not breached"
- Logging: avoid logging plaintext secrets; current logs focus on operations, not contents

## Known Gaps / Future Hardening

- **IMPROVED in v1.8**: At-rest key protection: optional feature to encrypt `secret.key` with a KEK derived from the master password (see `protect_key_with_master_password()` in `utils/crypto.py`). When enabled, `secret.key.enc` is used and requires the master password context to be set at login. This reduces the risk if the file key is stolen without the master password.
- Stronger KDF: configurable PBKDF2 iterations and salt with version metadata (v1.8); future versions can add Argon2id (memory-hard) or scrypt, and make iterations/salt fully configurable per-user.
- **IMPROVED in v1.8**: Import robustness: bulk insert using `executemany` in a single transaction to avoid SQLite locks (replaces individual add_password calls with delays).
- Secure UI: optional password reveal timeouts and redactions; auto-clear clipboard
- DB hardening: add per-entry nonces, integrity checks, and optional key rotation strategy
- Secrets storage: optional OS keyring integration (e.g., Secret Service, Keychain, Credential Manager)
