# 🔐 Secure Password Manager

A cross-platform vault that stores, audits, and rotates secrets entirely on your device. The application ships with both a rich CLI and a PyQt5 GUI, leverages modern cryptography, and is designed to integrate with upcoming browser extensions and automation services.

## Feature Highlights

- **End-to-end encryption** with Fernet (AES-128 + HMAC) backed by PBKDF2-derived master keys and optional Argon2id/scrypt migration hooks.
- **Dual interfaces**: interactive terminal workflow (`password-manager`) and a full desktop client (`password-manager-gui`).
- **Security automation** including strength analysis, breach checks, duplicate detection, expirations, and actionable remediation guidance.
- **Password history** tracking all password changes with rotation metadata (manual, expiry, breach, strength), configurable retention, and detailed audit trails.
- **Backup, restore, and export** pipelines with integrity protection, versioned envelopes, and disaster-recovery tooling.
- **Two-factor authentication (TOTP)** with automatic clipboard clearing (configurable timeout, default 25 seconds) and planned OS-keyring / hardware token support.
- **Extensible architecture** intended for browser auto-fill bridges, background jobs, and plugin-defined workflows.
- **Browser bridge** powered by FastAPI + uvicorn, issuing short-lived tokens to paired browser extensions over a localhost RPC channel, with desktop approval prompts for all credential access (v1.9.1+).
- **Browser extensions** for Chrome/Chromium (Manifest v3) and Firefox (Manifest v2) with secure pairing, credential autofill, and save prompts (v1.10.0).
- **Desktop approval system** requiring explicit user approval for browser extension credential queries, with "remember this domain" feature and comprehensive audit logging (v1.9.1).
- **Flexible key management** with a switchable master-password-derived mode, file-key fallback, and an interactive PBKDF2 benchmarking wizard that tunes iterations (default 390,000) and salt size per device.

## Quickstart

```bash
# 1. Create and activate an isolated environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install the application in editable mode
pip install -e .

# 3. Initialize the database and set a master password
password-manager --init

# 4. Launch CLI or GUI
password-manager
password-manager-gui
```

> **Tip:** The first run generates a `.data/` directory (in development mode) or uses XDG directories (when installed) containing `passwords.db`, `secret.key`, `crypto.salt`, `auth.json`, and (if configured) `totp_config.json`. Keep these files private and back them up using the provided tooling.

## Key Management & KDF Tuning

- **Switch modes**: In the CLI, visit `Settings → Key management mode`; in the GUI open the `Settings` tab and use the "Key Management Mode" card. Switching to the master-password-derived mode removes `secret.key` and re-encrypts the vault using a key derived each unlock.
- **Benchmark PBKDF2**: Run the "KDF tuning wizard" (CLI `Settings → KDF tuning wizard`, GUI `Settings` tab). The wizard measures the current CPU, recommends an iteration count for the target unlock time, and optionally rotates the salt size.
- **Apply new parameters**: When accepting the recommendation, the tool re-hashes `auth.json`, re-wraps any protected `secret.key`, and—if password-derived mode is active—re-encrypts every entry so the new parameters take effect immediately.
- **Configuration storage**: Selected mode, iteration targets, and salt metadata live in `settings.json` and `crypto.salt`. Backups include these files so restored environments preserve your hardening choices.

## Browser Extensions (v1.10.0)

Official browser extensions for **Chrome/Chromium** and **Firefox** provide seamless credential autofill and secure credential storage directly from your web browser.

### Features

- **🔒 Secure Pairing**: Pair with desktop app using 6-digit codes
- **🔑 Auto-Fill**: Click lock icon on password fields to fill credentials
- **💾 Save Credentials**: Automatically prompts to save new logins
- **✅ Desktop Approval**: All credential access requires explicit approval in desktop app
- **🦊 Multi-Browser**: Chrome (Manifest v3) and Firefox (Manifest v2) support

### Installation

**Build and Load Extension**:
```bash
cd browser-extension
./build-chrome.sh      # For Chrome/Chromium
./build-firefox.sh     # For Firefox
./build-all.sh         # Build both
```

**Chrome**: Load unpacked extension from `browser-extension/build/chrome/` at `chrome://extensions/`

**Firefox**: Load temporary add-on from `browser-extension/build/firefox/manifest.json` at `about:debugging`

### Usage

1. **Start Desktop App**: Launch `password-manager` or `password-manager-gui`
2. **Pair Extension**: Click extension icon → "Pair with Desktop App" → Enter 6-digit code from desktop
3. **Auto-Fill**: Visit login page → Click 🔒 lock icon on password field → Approve in desktop app
4. **Save**: Fill form manually → Submit → Click "Save" in save prompt → Approve in desktop app

**See [`browser-extension/README.md`](browser-extension/README.md) for full documentation, troubleshooting, and API details.**

## Browser Bridge (Desktop API)

The local browser bridge service unlocks auto-fill and audit integrations with browser extensions. It is disabled by default; enable it from either interface:

1. **CLI** → `Settings > Browser Bridge` to toggle auto-start, launch/stop the service, and manage tokens.
2. **GUI** → `Settings` tab → "Browser Bridge" panel to flip the enable checkbox, monitor status, and generate pairing codes.

Once enabled, the FastAPI service binds to `http://127.0.0.1:43110` (configurable via `settings.json`) and exposes the endpoints documented in [`docs/browser-extension-ipc.md`](docs/browser-extension-ipc.md). Pair new extensions by generating a 6-digit code; issued tokens are stored in `browser_bridge_tokens.json` under the config directory and can be revoked at any time from the same menus.
When the feature is marked enabled, the CLI/GUI automatically starts the service on launch and shuts it down cleanly on exit.

## Documentation Map

| Audience | Read This |
| --- | --- |
| Everyone | [`docs/README.md`](docs/README.md) |
| New users | [`docs/getting-started.md`](docs/getting-started.md), [`docs/user-manual.md`](docs/user-manual.md) |
| Security reviewers | [`docs/security-whitepaper.md`](docs/security-whitepaper.md) |
| Developers | [`docs/architecture-reference.md`](docs/architecture-reference.md), [`docs/contributing.md`](docs/contributing.md) |
| Operators & SRE | [`docs/operations-runbook.md`](docs/operations-runbook.md), [`docs/background-jobs-observability.md`](docs/background-jobs-observability.md) |
| Builders | [`docs/build-release-handbook.md`](docs/build-release-handbook.md) |
| Future integrations | [`docs/browser-extension-ipc.md`](docs/browser-extension-ipc.md) |
| Roadmap | [`docs/roadmap.md`](docs/roadmap.md) & [`CHANGELOG.md`](CHANGELOG.md) |

## Support & Feedback

- File issues or feature requests via GitHub.
- Use the `logs/password_manager.log` file along with `docs/operations-runbook.md` when reporting problems.
- Security disclosures should follow the responsible reporting process described in [`docs/security-whitepaper.md`](docs/security-whitepaper.md).
