# Getting Started Guide

This guide walks through installing Secure Password Manager, initializing a vault, and validating the environment on Linux, macOS, and Windows.

## Prerequisites

- Python 3.8 or newer
- Git (for source checkouts)
- Build tools for PyQt5 (`qtbase5-dev`, `libxcb`, etc. on Linux; Xcode Command Line Tools on macOS; Visual Studio Build Tools on Windows)
- `pip` and `virtualenv`
- Optional: `pyperclip` backends (`xclip`, `xsel`, `pbcopy`, or Windows clipboard support)

## Installation Steps

1. **Clone the repository**

   ```bash
   git clone https://github.com/ArcheWizard/password-manager.git
   cd password-manager
   ```

2. **Create a virtual environment**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -e .
   ```

4. **Verify entry points**

   ```bash
   password-manager --help
   password-manager-gui --version
   ```

## First-Time Setup

1. **Initialize the vault**

   ```bash
   password-manager --init
   ```

   - Sets the master password
   - Generates `secret.key`, `crypto.salt`, and `auth.json`
   - Creates `passwords.db` with the default schema
2. **Enable two-factor authentication (optional)**

   ```bash
   password-manager --enable-2fa
   ```

   - Displays a QR code for authenticator apps
   - Stores TOTP metadata in `totp_config.json`
3. **Seed demo data (development only)**

   ```bash
   python scripts/initialize.py --demo
   ```

## Verifying the Installation

- Run the CLI and add a password entry.
- Launch the GUI and confirm the entry appears in the table.
- Perform a security audit via CLI option `Security Audit > Full Audit`.
- Execute the automated test suite:

  ```bash
  pytest -q
  ```

## Directory Layout After Setup

In development mode (when running from source):

```text
password-manager/
└── .data/
    ├── passwords.db
    ├── secret.key
    ├── crypto.salt
    ├── auth.json
    ├── totp_config.json (if 2FA enabled)
    ├── browser_bridge_tokens.json (if Browser Bridge enabled)
    └── logs/
        └── password_manager.log
```

In production mode (installed via pip):

```text
~/.local/share/secure-password-manager/  # Data files
~/.config/secure-password-manager/        # Configuration (settings.json)
~/.cache/secure-password-manager/         # Cache (breach_cache.json)
```

## Troubleshooting

| Symptom | Resolution |
| --- | --- |
| `qt.qpa.plugin: Could not load the Qt platform plugin` | Install missing system packages (`sudo apt install qtbase5-dev`) or run in a desktop session. |
| `sqlite3.OperationalError: database is locked` | Ensure only one instance writes at a time; see `operations-runbook.md` for recovery steps. |
| Clipboard copy fails in CLI | Install `xclip`/`xsel` on Linux or ensure the terminal has clipboard access. |
| Tests cannot import modules | Confirm `src/` is on `PYTHONPATH`; the provided `pytest.ini` handles this when running from repo root. |

## Next Steps

- Explore daily workflows in the [User Manual](user-manual.md).
- Review [Security Whitepaper](security-whitepaper.md) before storing production secrets.
