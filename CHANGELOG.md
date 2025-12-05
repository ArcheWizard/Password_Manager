# Changelog

All notable changes will be documented in this file. The format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and uses semantic versioning when practical.

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
