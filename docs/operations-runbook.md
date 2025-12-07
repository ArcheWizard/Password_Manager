# Operations Runbook

Procedures for keeping Secure Password Manager healthy in production or enterprise deployments.

## Audience

- Site reliability engineers maintaining managed workstations.
- Security teams running periodic audits.
- Support engineers responding to incidents.

## Runtime Artifacts

Files follow XDG Base Directory specification. In development mode, all files are in `.data/`; in production, files are split across data/config/cache directories.

| File | Location Type | Description |
| --- | --- | --- |
| `passwords.db` | Data | Encrypted SQLite database with schema version tracking. |
| `secret.key` | Data | Encrypted master key (only in file-key mode). |
| `secret.key.enc` | Data | Password-protected master key (when key protection enabled). |
| `crypto.salt` | Data | KDF salt and parameters (JSON). |
| `auth.json` | Data | Master password hash and authentication metadata. |
| `totp_config.json` | Data | TOTP configuration (if 2FA enabled). |
| `settings.json` | Config | User preferences and feature toggles. |
| `logs/password_manager.log` | Data/logs | Application log with rotation. |
| `breach_cache.json` | Cache | Cached HIBP prefix responses. |
| `browser_bridge_tokens.json` | Data | Token store for paired browser extensions. |
| `approval_store.json` | Data | Remembered approval decisions for browser origins. |

## Routine Tasks

1. **Daily**
   - Verify automated backups completed.
   - Check logs for WARN/ERROR entries.
   - Review browser bridge approval prompts for suspicious origins.
2. **Weekly**
   - Run full security audit; export report for tracking.
   - Review open issues or vulnerability advisories.
   - If Browser Bridge is enabled, revoke stale tokens and review approval store for suspicious domains.
   - Review password history for unusual rotation patterns.
3. **Monthly**
   - Rotate master password if mandated.
   - Test restore process on a clean machine.
   - Update dependencies (`pip install -U -r requirements.txt`).
   - Review KDF parameters and consider benchmarking on updated hardware.
   - Audit remembered approval decisions and revoke untrusted origins.

## Monitoring & Alerts

- Tail `logs/password_manager.log` or ship to central log aggregation.
- Key log messages:
  - `LOGIN_FAILED` / `LOGIN_SUCCESS`
  - `BACKUP_COMPLETE` / `BACKUP_FAILED`
  - `BREACH_CHECK_ERROR`
  - `SECURITY_AUDIT_RESULT`
  - `BROWSER_BRIDGE_TOKEN_ISSUED` / `BROWSER_BRIDGE_TOKEN_REVOKED`
  - `APPROVAL_GRANTED` / `APPROVAL_DENIED` / `APPROVAL_REMEMBERED`
  - `PASSWORD_ROTATED` with rotation reason (manual, expiry, breach, strength)
- Configure alerting for repeated login failures, backup failures, breach API outages, or suspicious approval patterns.
- Monitor `approval_store.json` for unexpected auto-approved origins.

## Browser Bridge Operations

- **Service control**: Use CLI `Settings > Browser Bridge` or GUI Settings tab to enable, start, or stop the FastAPI service. The daemon listens on `127.0.0.1:43110` by default and shuts down automatically when the app exits.
- **Token hygiene**: Tokens reside in `browser_bridge_tokens.json`. Delete the file (with the app closed) or use the UI revoke button to invalidate every browser session after an incident.
- **Troubleshooting**:
  - If extensions cannot connect, ensure no firewall blocks localhost and confirm the service reports `running` in Settings.
  - Check logs for `BROWSER_BRIDGE_*` entries to trace pairing attempts.
  - Port conflicts: adjust `browser_bridge.port` in `settings.json`, then restart the application.

## Backup Rotation Policy

1. Store daily backups for 7 days, weekly backups for 4 weeks, monthly backups for 12 months.
2. Encrypt archives before uploading to cloud or tape.
3. Maintain checksum + signature files for each backup.
4. Document storage locations and retention dates in an asset tracker.

## Restore Procedure

1. Retrieve the desired backup zip and verify SHA-256 hash plus GPG signature.
2. On a clean workstation:

   ```bash
   unzip backup_<timestamp>.zip -d ~/restore
   ```

3. Stop running instances of the app.
4. Move current files to a safe location:

   ```bash
   mv passwords.db passwords.db.bak
   mv secret.key secret.key.bak
   ```

5. Copy restored files into place and ensure permissions are restricted (0600).
6. Start the application, enter the master password, and confirm data integrity.

## Handling Locked Databases

Symptoms: `sqlite3.OperationalError: database is locked`.

Resolution:

1. Ensure only one CLI/GUI instance is running.
2. Delete stray `passwords.db-journal` or `-wal` files _only after_ confirming no process uses them.
3. Run `PRAGMA wal_checkpoint(TRUNCATE);` via sqlite3 shell if WAL grows excessively.
4. Consider increasing WAL autocheckpoint frequency in future releases.

## Breach Cache Maintenance

- File: `breach_cache.json`
- Use `password-manager --refresh-breach-cache` (planned) or delete the file to force re-fetch.
- Keep file permissions tight; while data is anonymized, it reveals usage patterns.

## Incident Response Quick Steps

1. **Credential Leak Suspected**
   - Run audit, export affected entries, rotate credentials upstream.
   - Rotate master password and KEK.
   - Review logs around the suspected timeframe.
2. **Key Material Exposure**
   - Immediately generate new `secret.key` and salts via CLI settings.
   - Re-encrypt database and invalidate old backups.
3. **Device Loss/Theft**
   - Assume vault files compromised. Restore on new hardware, rotate all secrets, update breach monitoring.

## Contact & Escalation

- Primary: Maintainers via GitHub issues labeled `operations`.
- Secondary: Security mailing list (see `README.md`).
- Always include log excerpts, platform details, and reproduction steps.
