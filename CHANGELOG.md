# Changelog

All notable changes will be documented in this file. The format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and uses semantic versioning when practical.

## [1.10.4] - 2025-12-10

### Fixed

- **CI/CD**: Fixed Windows GitHub Actions test failures by replacing hardcoded Unix `/tmp/` paths with cross-platform `tmp_path` pytest fixture.
- **Tests**: Updated GUI smoke tests (`test_gui_smoke.py`) to use platform-agnostic temporary directories for backup, export, import, and restore operations.
- **Cross-Platform Compatibility**: All tests now pass successfully on Windows, macOS, and Linux.

### Changed

- Modified test fixtures in `test_backup_create_dialog`, `test_export_passwords_dialog`, `test_import_passwords_dialog`, and `test_restore_from_backup_dialog` to accept `tmp_path` parameter for better cross-platform support.

## [1.10.3] - 2025-12-09

### Fixed

- **Browser Extension**: Fixed credential saving functionality - credentials are now properly stored in the vault database when saved from the browser extension.
- Improved success notification in browser extension to show username when credentials are saved.
- Added proper error handling and validation for the `/v1/credentials/store` endpoint.
- **Browser Extension**: Prevented duplicate credentials - the save prompt no longer appears if credentials for the same username and origin already exist in the vault.

### Added

- Test coverage for the browser bridge credentials store endpoint.
- Validation of required fields (origin, username, password) when storing credentials.
- Duplicate credential detection in browser extension before prompting to save.

---

## [1.10.2] - 2025-12-08

### Added

- **Data persistence through pip updates**: User data now persists by default through pip uninstall/reinstall cycles.
- Data persistence settings in GUI (Settings → Data Persistence) and CLI (Settings → Data Persistence Settings).
- Optional "Remove data on uninstall" setting for users who want data cleanup on uninstall.
- Uninstall cleanup script (`scripts/uninstall_cleanup.py`) that respects user preferences.
- Data location display in settings showing XDG directory paths.

### Fixed

- **Critical**: Fixed `is_development_mode()` detection to properly differentiate pip-installed vs source execution.
  - Now checks if running from `site-packages` or `dist-packages` to determine pip installation.
  - Prevents pip-installed versions from incorrectly trying to use `.data/` directory.
- Data no longer "disappears" when updating password manager via pip.

### Changed

- Development mode detection now checks installation location rather than just directory existence.
- Default behavior: data persists through uninstalls (safer for users).
- Users must explicitly enable "Remove data on uninstall" with strong warnings.

---

## [1.10.1] - 2025-12-08

### Added

- Migration script (`scripts/migrate_to_production.py`) to move data from development `.data/` directory to production XDG directories.
- Legacy data detection in `paths.py` with helpful migration instructions.
- Production installation guide in `getting-started.md` with migration warning.

### Fixed

- **Data loss issue**: Users installing via pip after running from source no longer lose data. The app now warns about legacy data and provides migration instructions.
- Updated all documentation to v1.10.0 consistency.
- Browser extension manifests updated to v1.10.1.

### Changed

- Improved documentation across all guides for accuracy and completeness.

---

## [1.10.0] - 2025-12-05

### Added

- Browser extension for Chrome/Chromium and Firefox with secure credential autofill.
- Chrome extension with Manifest v3 (service worker architecture).
- Firefox extension with Manifest v2 (background script with browser.* APIs).
- Secure pairing system using 6-digit codes for extension-to-desktop authentication.
- Token-based authentication with browser fingerprinting for security.
- Auto-fill interface with visual lock icons on password fields.
- Multi-credential selector modal when multiple entries match an origin.
- Automatic credential save prompts when detecting form submissions.
- Browser-specific build scripts (`build-chrome.sh`, `build-firefox.sh`, `build-all.sh`).
- Comprehensive extension documentation and usage guide.
- Desktop approval integration - extension queries require user approval in desktop app.

### Changed

- Browser bridge API now fully integrated with extension workflow.
- Token expiration handling (30-day tokens) with automatic re-pairing prompts.
- Origin-based credential isolation for enhanced security.

### Security

- Browser fingerprinting prevents token theft across different browsers.
- Localhost-only communication (HTTP on 127.0.0.1:43110).
- Token storage in browser's encrypted storage (`chrome.storage.local`).
- All credential access requires desktop approval (leverages approval system).
- Audit trail for all extension credential queries.

### Notes

- Extension currently uses HTTP. TLS with certificate pinning planned for v1.11.0.
- Firefox extension requires temporary add-on loading (needs Mozilla signing for distribution).
- Chrome extension can be loaded in developer mode for testing.

---

## [1.9.1] - 2025-12-05

### Added

- Desktop approval prompts for browser extension credential access requests.
- Interactive CLI approval prompt with origin, browser, and entry details.
- GUI modal approval dialog with approve/deny buttons and visual details.
- "Remember this domain" feature for auto-approving trusted origins.
- Persistent approval store (`approval_store.json`) for remembered decisions.
- `ApprovalManager` system for thread-safe approval request handling.
- Comprehensive test suite (17 tests) for approval system functionality.
- Audit logging for all approval decisions (approve/deny/timeout).

### Changed

- Browser bridge `/v1/credentials/query` endpoint now requires user approval before returning credentials.
- Approval prompts automatically triggered when browser extensions request credentials.
- Remembered approvals bypass prompt and auto-approve subsequent requests.
- Both CLI and GUI modes set up approval handlers on startup.

### Security

- Prevents rogue browser extensions from accessing credentials without explicit user consent.
- Per-origin approval tracking with browser fingerprint validation.
- Denial decisions can also be remembered to auto-reject malicious domains.
- All credential access now requires explicit user confirmation (unless pre-approved).

### Fixed

- N/A

---

## [1.9.0] - 2025-12-05

### Added

- Password history with rotation metadata tracking all password changes.
- Database migration system for schema versioning and upgrades.
- `password_history` table with rotation reasons (manual, expiry, breach, strength).
- CLI and GUI interfaces for viewing password change history.
- Configurable retention policy (default: keep last 10 versions).
- Rotation reason selection when updating passwords in both CLI and GUI.
- History viewing with filtering and detailed change logs.
- Comprehensive test suite (11 tests) for password history functionality.

### Changed

- `update_password()` function now accepts `rotation_reason` parameter.
- Database initialization now runs pending migrations automatically.
- Config includes `password_history` settings (enabled by default, max_versions: 10).

### Fixed

- N/A

---

## [1.8.5] - 2025-12-05

### Added

- Clipboard auto-clear feature with configurable timeout (default 25 seconds) for both CLI and GUI.
- New `clipboard_manager.py` module providing thread-safe clipboard operations with automatic clearing.
- Comprehensive test suite for clipboard manager functionality.

### Changed

- All clipboard copy operations now use the centralized clipboard manager.
- Status messages updated to indicate auto-clear is enabled.
- Security whitepaper updated with detailed clipboard protection mechanisms.

### Fixed

- N/A

---

## [1.8.4] - 2025-11-18

### Added

- Initial documentation suite covering onboarding, architecture, security, testing, and operations.
- Baseline roadmap outlining security and integration milestones.
- Experimental browser bridge service (FastAPI + uvicorn) with CLI/GUI management menus, pairing codes, and token persistence tests.
- Master-password-derived key management mode plus a PBKDF2 benchmarking wizard (CLI/GUI) for tuning iterations and salt size on each device.

### Changed

- Documentation folder reset to align with the new structure described in `docs/README.md`.
- README, user manual, and IPC spec updated to cover the browser bridge lifecycle and operational guidance.

### Fixed

- N/A

---

Historical entries will be appended as releases are cut.
