# Operations Runbook

Procedures for keeping Secure Password Manager healthy in production or enterprise deployments.

## Audience

- Site reliability engineers maintaining managed workstations.
- Security teams running periodic audits.
- Support engineers responding to incidents.

## Runtime Artifacts

| Path | Description |
| --- | --- |
| `passwords.db` | Encrypted SQLite database. |
| `secret.key`, `crypto.salt`, `auth.json` | Key material and authentication metadata. |
| `totp_config.json` | Encrypted TOTP configuration (if enabled). |
| `logs/password_manager.log` | Application log. |
| `breach_cache.json` | Cached responses from breach lookups. |

## Routine Tasks

1. **Daily**
   - Verify automated backups completed.
   - Check logs for WARN/ERROR entries.
2. **Weekly**
   - Run full security audit; export report for tracking.
   - Review open issues or vulnerability advisories.
3. **Monthly**
   - Rotate master password if mandated.
   - Test restore process on a clean machine.
   - Update dependencies (`pip install -U -r requirements.txt`).

## Monitoring & Alerts

- Tail `logs/password_manager.log` or ship to central log aggregation.
- Key log messages:
  - `LOGIN_FAILED` / `LOGIN_SUCCESS`
  - `BACKUP_COMPLETE` / `BACKUP_FAILED`
  - `BREACH_CHECK_ERROR`
  - `SECURITY_AUDIT_RESULT`
- Configure alerting for repeated login failures, backup failures, or breach API outages.

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
