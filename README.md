
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
├── app.py                # Main application
├── requirements.txt      # Python dependencies
├── README.md              # Project documentation
├── .gitignore             # Ignored files
├── utils/                 # Helper modules
│   ├── crypto.py          # Encryption/decryption functions
│   ├── database.py        # Database handling
│   └── ui.py              # (Future UI handling)
└── tests/                 # (Future: unit tests)
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

- Add a Master Password authentication.
- Password strength generator.
- GUI version (Tkinter or PyQT).
- Unit tests for critical functions.
- Docker support.

---

## 👨‍💻 Author

- **Your Name** – [GitHub Profile](https://github.com/yourusername)

---

## ⚡ License

This project is open-source and available under the [MIT License](LICENSE).
