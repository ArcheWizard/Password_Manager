# User Manual

This manual covers everyday workflows for individuals and teams operating Secure Password Manager via both the command-line interface (CLI) and the PyQt5 graphical user interface (GUI).

## Audience & Scope

- End users managing personal or organizational credentials.
- Operators responsible for backups, audits, and recovery drills.
- Anyone needing a definitive guide to feature behavior.

## Terminology

- **Vault**: The encrypted SQLite database (`passwords.db`).
- **Master Password**: Primary secret unlocking the vault.
- **Entry**: A row containing website/app identifier, username, password, notes, category, and metadata (created_at, updated_at, expiry_date, favorite).
- **Security Audit**: Automated analysis detecting weak, reused, expired, or breached passwords.
- **Browser Bridge**: Local FastAPI service (v1.8.4) that enables browser extension integration via token-based authentication.
- **Key Mode**: File-key (default, uses `secret.key`) or password-derived (regenerates key from master password on each unlock).

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
| Edit/delete | `1. Password Vault > 3/4` | Editing re-encrypts instantly; deletions require confirmation. Editing prompts for rotation reason. |
| Copy password | `1. Password Vault > 2. View Passwords > Select entry > c` | Copies to clipboard with automatic clearing after configured timeout (default: 25 seconds). |
| View history | CLI/GUI context menu or options | Shows all password changes with timestamps, reasons, and who made changes. |
| Security audit | `2. Security Center` | Runs multiple checks; results summarized with remediation tips. |
| Backup/restore | `3. Backup & Restore` | Full backups produce zip archives; exports produce encrypted `.dat` files. |
| Settings | `4. Settings` | Manage categories, key mode, KDF benchmarking, Browser Bridge, and security preferences. |

### Shortcuts & Tips

- Press `q` anywhere to return to the previous menu.
- Use the search prompt inside "View Passwords" to filter by website or tag.
- For rapid entry creation, call:

   ```bash
   password-manager --add --website example.com --username alice
   ```

### Browser Bridge (Experimental)

- **Enable/disable**: CLI `Settings > Browser Bridge` or GUI `Settings` tab → "Browser Bridge" panel. The toggle controls whether the FastAPI service starts automatically on launch.
- **Start/stop service**: Both interfaces expose a dedicated button; the service binds to `http://127.0.0.1:43110` by default (configurable in `settings.json`).
- **Pair extensions**: Generate a 6-digit pairing code from the same menu. Codes expire after two minutes; share them directly with the requesting extension prompt.
- **Token management**: View or revoke issued tokens at any time. Tokens are stored in `browser_bridge_tokens.json` under the data directory, and revocation immediately severs the extension's access.
- **Security reminder**: The service only listens on localhost, but you should stop or disable it when not using browser automation.

## Key Management & KDF Tuning

### CLI (`Settings > Key management mode` / `KDF tuning wizard`)

1. **Switch modes**: Choose between `File key` (stores `secret.key` on disk) and `Master-password-derived` (derives the data key every unlock, removing the file). The wizard prompts for your master password and displays how many entries were re-encrypted.
2. **Benchmark PBKDF2**: Enter a target unlock time (default 350 ms). The wizard profiles PBKDF2 on your hardware, shows iteration/time samples, and recommends a value.
3. **Apply recommendations**: Confirm the salt size (16–64 bytes) and your master password. The CLI re-hashes `auth.json`, rotates the salt metadata, rewraps any protected `secret.key`, and—if password-derived mode is active—re-encrypts every vault entry.

### GUI (`Settings` tab → "Key Management Mode" / "KDF Tuning & Benchmark")

1. **Inspect status**: The panels show the current mode, whether key files exist, the configured iteration counts, and salt length.
2. **Switch modes**: Click *Switch Mode*, pick the desired option, and confirm with your master password. Progress dialogs keep the UI responsive while the vault is re-encrypted.
3. **Run benchmark wizard**: Click *Run Benchmark Wizard*, choose a target time, review the measured samples, then accept to apply. The GUI handles salt rotation, master-password rehashing, and key re-protection automatically.
4. **Post-change checks**: Status labels update immediately; the status bar confirms success, and the `System Information` card reflects the new configuration for audit trails.

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
