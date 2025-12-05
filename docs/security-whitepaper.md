# Security Whitepaper

This document describes the security goals, threat model, cryptographic design, operational safeguards, and planned evolutions of Secure Password Manager.

## Goals

1. Protect credentials at rest using strong, audited primitives.
2. Minimize the blast radius of host compromise through layered defenses.
3. Preserve privacy when interacting with external services (e.g., breach APIs).
4. Provide clear guidance for secure operation, backups, and incident response.

## Non-Goals

- Cloud storage or multi-tenant hosting (all storage remains local).
- Automatic trust of remote browser extensions without explicit pairing.
- Telemetry beyond anonymized optional metrics (not yet implemented).

## Threat Model

| Threat | Mitigation |
| --- | --- |
| Offline attacker with database file but no key | Strong KDF + envelope encryption; optional KEK derived from master password only. |
| Compromised local account while vault unlocked | Auto-lock timers, clipboard clearing, minimal plaintext exposure. |
| Malicious breach-check service | k-anonymity queries (first 5 SHA-1 chars), offline dictionary support, request throttling. |
| Rogue browser extension | Token-based IPC, per-origin allowlists, mandatory user approval prompts (v1.9.1+), rate limiting. |
| Tampered backups | HMAC-SHA256 integrity envelopes, manifest hashes, restore-time verification. |

## Cryptography

- **Key Derivation**: PBKDF2-HMAC-SHA256 with user-tunable iterations (default 390,000) and salt size (default 16 bytes). A built-in benchmarking wizard (CLI/GUI) measures device throughput, recommends iteration counts meeting a target unlock time (default 350ms), and rehashes both `auth.json` and the encryption salt metadata so changes take effect immediately. The system supports versioned KDF parameters for future migration to Argon2id and scrypt.
- **Master Key Storage**: `secret.key` encrypted by a Key Encryption Key (KEK) derived from the master password. Users can switch to a master-password-derived mode that removes `secret.key` entirely and recreates the vault key on each unlock; the mode switcher re-encrypts all vault entries atomically.
- **Data Encryption**: Fernet tokens (AES-128-CBC + HMAC-SHA256) per password entry.
- **Integrity**: Export files contain versioned metadata plus HMAC over ciphertext.
- **Randomness**: `secrets` module with OS entropy; password generator supports per-character-class entropy tuning.

## Authentication & Access Control

1. **Master Password**: Mandatory on every launch.
2. **Two-Factor Authentication**: RFC 6238-compliant TOTP with QR provisioning. Verification occurs before decrypting vault contents.
3. **Session Lock**: Optional idle timer requiring re-authentication.
4. **Role Separation** (planned): Profiles for personal vs. team vaults, each with distinct KDF settings and audit policies.

## Clipboard & UI Protections

- Passwords copied via CLI/GUI trigger automatic clearing timers (default 25 seconds, user-configurable) that wipe the clipboard using a background thread.
- The clipboard manager cancels previous timers when new content is copied, ensuring only the most recent timer is active.
- Users can immediately clear the clipboard or disable auto-clear per operation.
- GUI uses masked fields by default; unmasking requires explicit action.
- Keyboard shortcuts avoid logging sensitive data.

## Network Interactions

- Breach checks call Have I Been Pwned range API using first five SHA-1 characters of the password hash, preserving anonymity.
- Browser Bridge (v1.9.1+) runs a FastAPI server on `127.0.0.1:43110`, issuing short-lived tokens after an in-app pairing ceremony; no traffic leaves the host.
- **Desktop Approval Prompts (v1.9.1)**: Every credential access request from browser extensions triggers an explicit user approval prompt showing origin, browser, and entry details. Users can approve once or remember the decision for trusted domains. Approval decisions are persisted and logged for audit trails.
- Proxy settings and offline breach dictionaries are supported to minimize direct outbound calls.

## Logging & Telemetry

- Application logs default to `logs/password_manager.log` with timestamps, log level, module, and redactable entry IDs.
- No plaintext passwords, master keys, or TOTP secrets are ever logged.
- Auditable events include login success/failure, backup operations, imports/exports, and audit summaries.

## Backup & Recovery Security

1. **Full Backups**: Zip archives containing database, key files, salts, auth config, breach cache, and manifest. Archives can be optionally encrypted with a passphrase before offsite storage.
2. **Encrypted Exports**: JSON payload encrypted with a user-supplied passphrase; includes metadata version and HMAC for tamper detection.
3. **Restore Process**: Creates timestamped `.bak` copies before overwriting production files. Integrity hashes validated prior to import.

## Incident Response Guidance

1. **Suspected Compromise**
   - Disconnect from network, copy logs, capture system state.
   - Rotate master password and regenerate KEK/secret key.
   - Run full security audit; mark affected entries for rotation.
2. **Lost Device**
   - Ensure backups are encrypted and stored offsite.
   - Restore backup on a clean machine, rotate master password, enable 2FA.
3. **Breach Findings**
   - Use audit export JSON as evidence.
   - Coordinate with service owners to rotate credentials and add monitoring.

## Future Enhancements

- Hardware-backed keys (TPM, Secure Enclave, FIDO2) for unlocking vaults.
- End-to-end encrypted sync with selective sharing groups.
- Signed plugin ecosystem with permission manifest.
- Automatic policy enforcement (minimum length, rotation interval, forbidden domains).

## Responsible Disclosure

Security researchers can report vulnerabilities via the contact listed in `README.md`. Provide reproduction steps, affected components, and any proof-of-concept code. We commit to timely acknowledgment and coordinated disclosure.
