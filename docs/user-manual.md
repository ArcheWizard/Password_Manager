# User Manual

This manual covers everyday workflows for individuals and teams operating Secure Password Manager via both the command-line interface (CLI) and the PyQt5 graphical user interface (GUI).

## Audience & Scope

- End users managing personal or organizational credentials.
- Operators responsible for backups, audits, and recovery drills.
- Anyone needing a definitive guide to feature behavior.

## Terminology

- **Vault**: The encrypted SQLite database (`passwords.db`).
- **Master Password**: Primary secret unlocking the vault.
- **Entry**: A row containing website/app identifier, username, password, notes, category, and metadata.
- **Security Audit**: Automated analysis detecting weak, reused, expired, or breached passwords.

## CLI Workflow (`password-manager`)

### Launching

```bash
password-manager
```

- The first prompt requests the master password.
- Menus are numbered; type the index and press Enter.

### Core Tasks

| Task | Menu Path | Notes |
| --- | --- | --- |
| Add password | `1. Password Vault > 1. Add Password` | Supports random generation, categories, optional expiry date. |
| View passwords | `1. Password Vault > 2. View Passwords` | Filter by favorites, weak, reused, expiring. |
| Edit/delete | `1. Password Vault > 3/4` | Editing re-encrypts instantly; deletions require confirmation. |
| Copy password | `1. Password Vault > 2 > Select entry` | Copies to clipboard and starts auto-clear timer if configured. |
| Security audit | `2. Security Center` | Runs multiple checks; results summarized with remediation tips. |
| Backup/restore | `3. Backup & Restore` | Full backups produce zip archives; exports produce encrypted `.dat` files. |
| Settings | `4. Settings` | Manage categories, KDF parameters, and security preferences. |

### Shortcuts & Tips

- Press `q` anywhere to return to the previous menu.
- Use the search prompt inside "View Passwords" to filter by website or tag.
- For rapid entry creation, call:

   ```bash
   password-manager --add --website example.com --username alice
   ```

## GUI Workflow (`password-manager-gui`)

### Layout Overview

1. **Sidebar**: Filters (All, Favorites, Expiring, Weak, Reused, Breached).
2. **Password Table**: Sortable columns with inline search field.
3. **Detail Panel**: Shows entry metadata, password strength meter, rotation history.
4. **Action Bar**: Add, edit, delete, copy, favorite, audit.

### Frequent Actions

- **Add Entry**: Click “New Password,” fill fields, optionally generate via slider (length, symbols, pronounceability), set expiry and category.
- **Copy Credentials**: Hover over row, click copy icon for username or password. Auto-clear uses system timers (configurable).
- **Rotate Password**: Open entry, hit “Regenerate & Save,” optionally log reason.
- **Security Audit**: `Security > Run Audit` opens a modal with score, issue breakdown, suggested actions, and quick links to affected entries.
- **Backup/Restore**: `File > Backup Vault` or `File > Restore From Backup`. Wizards validate integrity hashes before writing.

### Keyboard Shortcuts

| Shortcut | Action |
| --- | --- |
| `Ctrl/Cmd + N` | New password entry |
| `Ctrl/Cmd + F` | Focus global search |
| `Ctrl/Cmd + E` | Edit selected entry |
| `Ctrl/Cmd + D` | Delete selected entry |
| `Ctrl/Cmd + L` | Copy password |
| `Ctrl/Cmd + Shift + L` | Copy username |
| `Ctrl/Cmd + B` | Create backup |
| `Ctrl/Cmd + Shift + A` | Run security audit |

### Notifications & Status

- Expiring passwords trigger banner alerts and optional system notifications (configurable per OS).
- Background breach checks surface toast notifications summarizing results.
- A status bar indicator shows sync status once browser/automation services are enabled.

## Password Lifecycle Best Practices

1. **Creation**: Use generator defaults (length ≥ 16, include numbers/symbols). Attach descriptive notes (e.g., MFA serial number).
2. **Rotation**: Track "Last Rotated" metadata; schedule audits monthly. Use batch rotation for high-risk categories.
3. **Expiration**: Set expiries for compliance, but rely on audit reminders for friendly prompts.
4. **Deletion**: Remove unused secrets after revoking from the upstream service; this avoids clutter and keeps audits meaningful.

## Favorites, Categories, and Tags

- Mark frequently used entries as favorites via star icons.
- Categories are color-coded (CLI uses ANSI colors, GUI uses badges). Configure via Settings.
- Planned tags will allow many-to-many classification; see `data-model.md` for schema evolution notes.

## Backup & Restore Procedures

1. **Creating a Backup**
   - CLI: `3. Backup & Restore > 1. Create Backup`
   - GUI: `File > Backup Vault`
   - Output: Timestamped zip containing database, key material, logs, and metadata manifest.
2. **Creating an Encrypted Export**
   - CLI: `3. Backup & Restore > 2. Export Passwords`
   - GUI: `File > Export`
   - Output: `.dat` file encrypted with a user-chosen passphrase; includes HMAC for tamper detection.
3. **Restoring**
   - Use the wizard; application backs up current files before overwriting.
   - Validate HMAC/manifest to avoid corrupted imports.

## Security Audit Playbook

1. Run `Security Center > Full Audit` or GUI equivalent.
2. Review the score (0–100) and issue list (weak, reused, duplicate, expired, breached).
3. For each issue, click "Remediate" to open the entry prefilled with rotate guidance.
4. Export the audit report if needed for compliance evidence.

## Logging & Activity History

- All sensitive operations log metadata (timestamp, action, entry ID hash) to `logs/password_manager.log`.
- GUI displays a condensed activity feed in the right-hand panel.
- Use logs during incident investigations or during support escalations.

## FAQ

**Q: How do I switch between CLI and GUI safely?**
A: Both use the same database. Avoid simultaneous writes by closing one before making changes in the other.

**Q: Can I store attachments?**
A: Attachments are on the roadmap. For now, store references or use encrypted notes.

**Q: How do I report a breach finding?**
A: Use the audit export feature to generate a JSON report, then follow your organization’s incident-response procedure.

## Additional Resources

- [Security Whitepaper](security-whitepaper.md)
- [Operations Runbook](operations-runbook.md)
- [Roadmap](roadmap.md)
