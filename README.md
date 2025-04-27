# 🔐 Password Manager

A secure Password Manager built with Python that securely stores your passwords locally using strong encryption.

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

## 📂 Project Structure

The project is organized into modules for maintainability and separation of concerns:

```plaintext
password-manager/
├── [app.py](http://_vscodecontentref_/4)                 # CLI application entry point
├── [gui.py](http://_vscodecontentref_/5)                 # GUI application entry point
├── [initialize.py](http://_vscodecontentref_/6)          # Setup script
├── [migrate_db.py](http://_vscodecontentref_/7)          # Database migration tool
├── [requirements.txt](http://_vscodecontentref_/8)       # Python dependencies
├── [setup.py](http://_vscodecontentref_/9)               # Packaging configuration
├── utils/                 # Core utilities
│   ├── [auth.py](http://_vscodecontentref_/10)            # Authentication
│   ├── [backup.py](http://_vscodecontentref_/11)          # Import/export 
│   ├── [crypto.py](http://_vscodecontentref_/12)          # Encryption/decryption
│   ├── [database.py](http://_vscodecontentref_/13)        # Database operations
│   ├── [interactive.py](http://_vscodecontentref_/14)     # CLI input utilities
│   ├── [logger.py](http://_vscodecontentref_/15)          # Logging facilities
│   ├── [password_analysis.py](http://_vscodecontentref_/16) # Password evaluation
│   ├── [security_analyzer.py](http://_vscodecontentref_/17) # Breach checking
│   ├── [security_audit.py](http://_vscodecontentref_/18)  # Security auditing
│   ├── [two_factor.py](http://_vscodecontentref_/19)      # 2FA implementation
│   └── [ui.py](http://_vscodecontentref_/20)              # UI formatting
├── tests/                 # Unit & integration tests
│   ├── [test_crypto.py](http://_vscodecontentref_/21)     
│   ├── [test_database.py](http://_vscodecontentref_/22)   
│   ├── [test_integration.py](http://_vscodecontentref_/23)
│   └── [test_password_analysis.py](http://_vscodecontentref_/24)
└── [README.md](http://_vscodecontentref_/25)              # Project documentation
```

## 🛠️ Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/password-manager.git
    cd password-manager
    ```

2. Create and activate a virtual environment:

    ```bash
    python3 -m venv venv
    source venv/bin/activate   # On Windows: venv\Scripts\activate
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Run the application:

    ```bash
    python app.py
    ```

---

## 🛡️ Requirements

- Python 3.8+
- Libraries:
  - `cryptography`
  - `colorama`

Install them via:

```bash
pip install -r requirements.txt
```

---

## 📸 Screenshots

> (You can paste CLI screenshots later when running.)

---

## 📚 Future Improvements

- ✅ Add a Master Password authentication
- ✅ Password strength evaluation and generator
- ✅ Unit tests for critical functions
- ✅ Backup and restore functionality
- Add a search function for passwords
- Add password categories/tags
- Add password expiration notifications
- GUI version (Tkinter or PyQT)
- Two-factor authentication
- Password history tracking
- Cross-platform desktop application (using PyInstaller)
- Docker support

---

## 🔒 How It Works

### Security Model

This Password Manager uses a multi-layered security approach:

1. **Master Password**: Access to the application is protected by a master password that is never stored directly. Instead, a salted hash is stored using PBKDF2 with 100,000 iterations.

2. **Encryption**: All passwords are encrypted using Fernet symmetric encryption (AES-128 in CBC mode with PKCS7 padding).

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

---

## 👨‍💻 Author

- **ArcheWizard** – [GitHub Profile](https://github.com/ArcheWizard)

---

## Create a MIT license file

curl <https://opensource.org/licenses/MIT> > LICENSE
