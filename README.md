# 🔐 Password Manager

A simple Password Manager built with Python that securely stores your passwords locally using encryption.

## 🚀 Features

- Add new passwords (encrypted).
- View saved passwords (decrypted).
- Delete passwords by ID.
- Local SQLite database storage.
- Encrypted with **Fernet** symmetric encryption.
- Colorful, user-friendly Command-Line Interface (CLI).

## 📂 Project Structure

```plaintext
password-manager/
├── app.py                 # Main application
├── initialize.py          # Setup script
├── requirements.txt       # Python dependencies
├── README.md              # Project documentation
├── VERSION.txt            # Version information
├── .gitignore             # Ignored files
├── auth.json              # Master password hash
├── utils/                 # Helper modules
│   ├── crypto.py          # Encryption/decryption functions
│   ├── database.py        # Database handling
│   ├── ui.py              # UI formatting utilities
│   ├── auth.py            # Authentication utilities
│   ├── backup.py          # Import/export utilities
│   └── password_strength.py # Password evaluation
├── tests/                 # Unit tests
│   ├── __init__.py
│   ├── test_crypto.py     # Tests for crypto functions
│   └── test_database.py   # Tests for database functions
└── .github/               # GitHub specific files
    └── workflows/         # GitHub Actions
        └── ci.yml         # Continuous Integration
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

## 👨‍💻 Author

- **ArcheWizard** – [GitHub Profile](https://github.com/ArcheWizard)

---

## Create a MIT license file

curl <https://opensource.org/licenses/MIT> > LICENSE
