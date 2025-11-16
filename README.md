# 🔐 Secure Password Manager

A local-first Password Manager built with Python that securely stores your passwords using strong encryption.

Current version: see `VERSION.txt` (v1.8.0)

**🆕 What's New in v1.8.0:**

- **KDF versioning** for future-proof key derivation
- **Optional key protection** with master password (encrypt `secret.key`)
- **Export integrity HMAC** to detect tampering
- **Bulk import transactions** for faster, lock-free restore
- See [v1.8.0 improvements](docs/v1.8.0_improvements.md) for details

## 🚀 Features

- **Secure Storage**: All passwords encrypted with Fernet symmetric encryption
- **Password Management**: Add, view, edit, and delete passwords
- **Security Analysis**: Password strength evaluation and suggestions
- **Password Generator**: Create strong, random passwords
- **Master Password**: Protect access with a master password
- **Two-Factor Authentication**: Additional security with TOTP (Time-based One-Time Password)
- **Categorization**: Organize passwords by category
- **Security Audit**: Find weak, reused, expired, or breached passwords
- **Backup & Restore**: Export/import functionality
- **Password Expiration**: Set expiry dates for passwords
- **Command-Line Interface**: User-friendly CLI with color formatting
- **GUI Interface**: Optional PyQt5 graphical interface
- **Activity Logging**: Track all important actions

## 📚 Documentation

Comprehensive project documentation is organized in the `docs/` folder:

### For Users

- [Documentation Index](docs/README.md) - Complete documentation overview

### For Developers

- [Architecture](docs/development/architecture.md) - System architecture and design
- [Security Model](docs/development/security.md) - Security implementation details
- [Database Schema](docs/development/database-schema.md) - Database structure
- [Contributing Guide](docs/development/contributing.md) - Development guide
- [Roadmap](docs/releases/roadmap.md) - Future plans

### Build Documentation

- [Build Guide](docs/build/readme.md) - Building from source
- [Linux Build](docs/build/linux-build-guide.md) - Linux-specific instructions

## 🛠️ Installation

### Option 1: Install from PyPI (Recommended)

The simplest way to install Secure Password Manager:

```bash
pip install secure-password-manager
```

After installation, you can run the application with:

```bash
# For the command-line interface
password-manager

# For the graphical interface
password-manager-gui
```

### Option 2: Install from Source

1. Clone the repository:

    ```bash
    git clone https://github.com/ArcheWizard/password-manager.git
    cd password-manager
    ```

2. Create and activate a virtual environment:

    ```bash
    python3 -m venv venv
    source venv/bin/activate   # On Windows: venv\Scripts\activate
    ```

3. Install the package in development mode:

    ```bash
    pip install -e .
    ```

4. If upgrading from an older version, run the migration script:

    ```bash
    python scripts/migrate_to_new_structure.py
    ```

    This will move existing data files to the new `.data/` directory.

## 🛡️ Requirements

- Python 3.8+
- Core dependencies (installed automatically):
  - `cryptography`: For secure encryption
  - `PyQt5`: For the GUI interface
  - `zxcvbn`: For password strength analysis
  - `pillow`: For image processing
  - Additional dependencies as listed in `requirements.txt`

## 📂 Project Structure

The project follows PEP 517 src/ layout for better packaging and distribution:

```plaintext
password-manager/
├── src/                   # Source code (PEP 517 layout)
│   └── secure_password_manager/
│       ├── __init__.py    # Package initialization
│       ├── apps/          # Application entry points
│       │   ├── app.py     # CLI application
│       │   └── gui.py     # GUI application
│       └── utils/         # Core utilities
│           ├── auth.py            # Authentication
│           ├── backup.py          # Import/export
│           ├── crypto.py          # Encryption/decryption
│           ├── database.py        # Database operations
│           ├── interactive.py     # CLI input utilities
│           ├── logger.py          # Logging facilities
│           ├── password_analysis.py # Password evaluation
│           ├── paths.py           # Path management (XDG)
│           ├── security_analyzer.py # Breach checking
│           ├── security_audit.py  # Security auditing
│           ├── two_factor.py      # 2FA implementation
│           └── ui.py              # UI formatting
├── tests/                 # Unit & integration tests
├── docs/                  # Documentation
│   ├── development/       # Technical documentation
│   ├── build/             # Build instructions
│   └── releases/          # Release notes
├── scripts/               # Build and utility scripts
├── assets/                # Static assets
│   ├── icons/             # Application icons
│   └── screenshots/       # UI screenshots
├── .data/                 # Development data (gitignored)
└── pyproject.toml         # Project configuration
```

### Data Storage

The application uses XDG Base Directory Specification for organized data storage:

**Development Mode** (when running from source):

- All data stored in `.data/` directory in project root

**Production Mode** (when installed via pip):

- Data files: `~/.local/share/secure-password-manager/`
- Config files: `~/.config/secure-password-manager/`
- Cache files: `~/.cache/secure-password-manager/`
- Log files: `~/.local/share/secure-password-manager/logs/`

## 📸 Screenshots

### First Time Setup

![First Time Setup](https://raw.githubusercontent.com/ArcheWizard/password-manager/main/assets/screenshots/First_Time_Setup.png)
![Setting Master Password](https://raw.githubusercontent.com/ArcheWizard/password-manager/main/assets/screenshots/First_Time_Password.png)
![Weak Password Warning](https://raw.githubusercontent.com/ArcheWizard/password-manager/main/assets/screenshots/First_Time_Weak_Password_Warning.png)
![Password Confirmation](https://raw.githubusercontent.com/ArcheWizard/password-manager/main/assets/screenshots/First_Time_Password_Confirm.png)
![Setup Complete](https://raw.githubusercontent.com/ArcheWizard/password-manager/main/assets/screenshots/First_Time_Setup_Complete.png)

### Login

![Login Screen](https://raw.githubusercontent.com/ArcheWizard/password-manager/main/assets/screenshots/Login.png)

### Home Screen

![Home Screen](https://raw.githubusercontent.com/ArcheWizard/password-manager/main/assets/screenshots/Home.png)

### Password Management

![Adding a Password](https://raw.githubusercontent.com/ArcheWizard/password-manager/main/assets/screenshots/Add_Password.png)
![Editing a Password](https://raw.githubusercontent.com/ArcheWizard/password-manager/main/assets/screenshots/Edit_Password.png)

### Categories

![Categories](https://raw.githubusercontent.com/ArcheWizard/password-manager/main/assets/screenshots/Categories.png)

### Security Audit

![Security Audit](https://raw.githubusercontent.com/ArcheWizard/password-manager/main/assets/screenshots/Security.png)

### Backup & Restore

![Backup Options](https://raw.githubusercontent.com/ArcheWizard/password-manager/main/assets/screenshots/Backup.png)
![Exporting Passwords](https://raw.githubusercontent.com/ArcheWizard/password-manager/main/assets/screenshots/Export.png)
![Importing Passwords](https://raw.githubusercontent.com/ArcheWizard/password-manager/main/assets/screenshots/Import.png)

### Settings & Logs

![Settings](https://raw.githubusercontent.com/ArcheWizard/password-manager/main/assets/screenshots/Settings.png)
![Activity Logs](https://raw.githubusercontent.com/ArcheWizard/password-manager/main/assets/screenshots/Logs.png)

## 🔒 How It Works

### Security Model

This Password Manager uses a multi-layered security approach:

1. **Master Password**: Access to the application is protected by a master password that is never stored directly. Instead, a salted hash is stored using PBKDF2 with 100,000 iterations.

2. **Encryption**: All passwords are encrypted using Fernet symmetric encryption (AES-128-CBC + HMAC integrity, via `cryptography`).

3. **Key Management**: The encryption key is stored locally and is used for encrypting/decrypting the stored passwords.

4. **Database**: Passwords are stored in a local SQLite database, with the password values stored as encrypted binary data.

5. **Backup Protection**: When exporting passwords, the entire backup file is encrypted using the same strong encryption.

### Data Flow

1. When adding a password:
   - Password is encrypted using the local key
   - Encrypted data is stored in the SQLite database

2. When viewing passwords:
   - Encrypted data is retrieved from the database
   - Each password is decrypted for display

3. When exporting passwords:
   - All passwords are decrypted
   - The entire password list is serialized to JSON
   - The JSON is encrypted and written to a file

## 🧪 Testing

```bash
pytest -q
```

Notes:

- Integration tests use temporary databases and patch `DB_FILE`
- Network-dependent breach checks are limited and resilient to failures
- SQLite can lock under concurrent operations; tests include small delays/workarounds

## 🗺️ Roadmap (excerpt)

See `docs/roadmap.md` for the full plan. Highlights:

- Derive or protect `secret.key` using the master password (or OS keyring)
- Stronger KDF defaults (Argon2id/scrypt) with parameter versioning
- Improved import/restore reliability and integrity verification
- Clipboard auto-clear and additional UX hardening

## 📝 Changelog

See `CHANGELOG.md` for release notes.

## 📚 Future Improvements (historical)

- ✅ Master Password authentication
- ✅ Password strength evaluation and generator
- ✅ Unit tests for critical functions
- ✅ Backup and restore functionality
- ✅ Search
- ✅ Categories/tags
- ✅ Password expiration notifications
- ✅ GUI version (PyQt)
- ✅ Package available on PyPI
- ✅ Two-factor authentication (TOTP)
- Password history tracking
- Cross-platform desktop application (PyInstaller)
- Docker support

## 👨‍💻 Author

- **ArcheWizard** – [GitHub Profile](https://github.com/ArcheWizard)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

For security considerations and design details, start with `docs/security.md` and `docs/architecture.md`.
