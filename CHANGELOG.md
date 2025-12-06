# Changelog

All notable changes will be documented in this file. The format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and uses semantic versioning when practical.

## [1.10.0] - 2024-12-05

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
- All credential access requires desktop approval (leverages v1.9.1 approval system).
- Audit trail for all extension credential queries.

### Notes

- Extension currently uses HTTP. TLS with certificate pinning planned for v1.11.0.
- Firefox extension requires temporary add-on loading (needs Mozilla signing for distribution).
- Chrome extension can be loaded in developer mode for testing.

---

## [1.9.1] - 2024-12-05

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

## [1.9.0] - 2024-12-05

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

## [1.8.5] - 2024-12-05

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

## [1.8.4] - 2024-11-18

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
