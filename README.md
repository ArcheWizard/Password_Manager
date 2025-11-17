# 🔐 Secure Password Manager

A cross-platform vault that stores, audits, and rotates secrets entirely on your device. The application ships with both a rich CLI and a PyQt5 GUI, leverages modern cryptography, and is designed to integrate with upcoming browser extensions and automation services.

## Feature Highlights

- **End-to-end encryption** with Fernet (AES-128 + HMAC) backed by PBKDF2-derived master keys and optional Argon2id/scrypt migration hooks.
- **Dual interfaces**: interactive terminal workflow (`password-manager`) and a full desktop client (`password-manager-gui`).
- **Security automation** including strength analysis, breach checks, duplicate detection, expirations, and actionable remediation guidance.
- **Backup, restore, and export** pipelines with integrity protection, versioned envelopes, and disaster-recovery tooling.
- **Two-factor authentication (TOTP)**, clipboard hygiene controls, and planned OS-keyring / hardware token support.
- **Extensible architecture** intended for browser auto-fill bridges, background jobs, and plugin-defined workflows.

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

> **Tip:** The first run generates `passwords.db`, `secret.key`, `crypto.salt`, `auth.json`, and (if configured) `totp_config.json` in the working directory. Keep these files private and back them up using the provided tooling.

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
