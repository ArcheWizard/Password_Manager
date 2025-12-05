# Architecture Reference

This reference explains how Secure Password Manager is assembled, including runtime components, module responsibilities, data flow, and extensibility points.

## High-Level Diagram

```text
+----------------------+           +---------------------+
|        CLI           |           |        GUI          |
| apps/app.py         |           | apps/gui.py         |
+----------+-----------+           +----------+----------+
           |                                  |
           v                                  v
      +----+----------------------------------+----+
      |         Application Services               |
      |  utils/ (auth, crypto, database, etc.)     |
      |  services/ (browser_bridge)                |
      +----+----------------------+----------------+
           |                      |                |
           v                      v                v
    SQLite DB          Key Material       Browser Bridge
  (passwords.db)    (secret.key, etc.)   (FastAPI/uvicorn)
```

## Modules & Responsibilities

| Module | Path | Responsibility |
| --- | --- | --- |
| CLI App | `src/secure_password_manager/apps/app.py` | Text menus, workflow orchestration, ANSI formatting. |
| GUI App | `src/secure_password_manager/apps/gui.py` | PyQt5 interface, dialogs, tables, notifications. |
| Authentication | `src/secure_password_manager/utils/auth.py` | Master password setup/verification, login rate limiting. |
| Crypto | `src/secure_password_manager/utils/crypto.py` | Key generation, Fernet encryption/decryption, PBKDF2 derivation, key protection. |
| Key Management | `src/secure_password_manager/utils/key_management.py` | Mode switching (file-key ⇌ password-derived), KDF benchmarking, parameter tuning. |
| Database | `src/secure_password_manager/utils/database.py` | Schema creation, CRUD helpers, query utilities (favorites, expiring, search). |
| Password Analysis | `src/secure_password_manager/utils/password_analysis.py` | Strength scoring, entropy, generator logic. |
| Security Audit | `src/secure_password_manager/utils/security_audit.py` & `security_analyzer.py` | Weak/reused/expired/breached detection, scoring. |
| Two-Factor | `src/secure_password_manager/utils/two_factor.py` | TOTP enrollment/verification, QR provisioning. |
| Backup | `src/secure_password_manager/utils/backup.py` | Full backups, encrypted exports, restore routines. |
| Logger | `src/secure_password_manager/utils/logger.py` | Structured logging, log rotation, CLI/GUI friendly formatting. |
| Paths | `src/secure_password_manager/utils/paths.py` | XDG Base Directory support, file path resolution, dev vs. production modes. |
| UI Helpers | `src/secure_password_manager/utils/ui.py`, `interactive.py` | Reusable menu prompts, table renderers, clipboard helpers. |
| Browser Bridge Service | `src/secure_password_manager/services/browser_bridge.py` | FastAPI/uvicorn server issuing pairing codes and scoped tokens for browser extensions (v1.8.4). |

## Data Flow

1. **Startup**
   - CLI/GUI prompts for master password.
   - `auth.authenticate` validates hash stored in `auth.json` (PBKDF2-HMAC-SHA256).
   - In file-key mode: `crypto.unprotect_key` decrypts `secret.key` using KEK derived from master password.
   - In password-derived mode: `crypto.derive_key_from_password` regenerates vault key from master password on each unlock.
   - `crypto.set_master_password_context` stores password in memory for the session.
2. **Database Access**
   - Services call `database.get_connection()` (context-managed) to run queries.
   - Results are mapped into domain objects or dictionaries for UI layers.
3. **Password Operations**
   - Before persistence, passwords are encrypted via `crypto.encrypt_password`.
   - Metadata (category, expiry, tags) stored alongside ciphertext.
4. **Security Audit**
   - `security_audit.run_security_audit` gathers decrypted entries, performs checks, caches breach results, and logs summary data.
5. **Backup/Restore**
   - Export pipeline decrypts entries in-memory, builds JSON payload, encrypts with user passphrase, then writes to disk.
   - Restore pipeline verifies HMAC, copies files, and refreshes caches.

## Dependency Guidelines

- UI layers (CLI/GUI) may depend on services in `utils`, but `utils` must remain UI-agnostic.
- `utils/database.py` is the only module permitted to touch SQLite. Other modules request operations through typed helper functions.
- Long-running or background tasks should live in dedicated service modules to allow reuse by future daemons (browser bridge, sync agent).

## Extension Points

1. **Browser Bridge**: Local RPC server is implemented (v1.8.4). FastAPI service reuses authentication, crypto, and audit services. Browser extensions are in development. See `browser-extension-ipc.md`.
2. **Background Jobs**: Scheduler/worker design will call into database/audit helpers; architecture is outlined in `background-jobs-observability.md`.
3. **Plugin API**: Future entry points will expose hooks for custom breach providers or policy engines via Python entry points.

## Performance Considerations

- SQLite pragmas tuned for safety over speed (journal_mode=WAL, synchronous=FULL). Batch operations use transactions and `executemany` to reduce locks.
- Breach checks cache prefix responses in `breach_cache.json` to minimize network calls.
- GUI employs background threads for long operations, posting results back to the main thread via Qt signals.

## Known Technical Debt

- `apps/app.py` (1,600+ lines) and `apps/gui.py` (2,400+ lines) contain monolithic implementations; refactoring into feature modules is planned.
- Database migrations are manual; a schema version table plus migrator utility is on the roadmap.
- Config management uses a simple JSON file; consider a more robust solution for complex enterprise deployments.
- Tests cover critical utilities but need expansion to cover GUI presenters and error paths.

## Future State Snapshot

- Modular service layer (passwords, audit, backup) consumable by CLI, GUI, browser bridge, and automation jobs.
- Configurable data directory, enabling USB-portable distributions and multi-profile setups.
- Clear separation between core logic and UI frameworks to ease porting to other toolkits.
