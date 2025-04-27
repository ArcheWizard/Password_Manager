from cryptography.fernet import Fernet
import os

# Key generation/loading
KEY_FILE = 'secret.key'

def generate_key() -> None:
    """Generate and save a key for encryption."""
    key = Fernet.generate_key()
    with open(KEY_FILE, 'wb') as key_file:
        key_file.write(key)

def load_key() -> bytes:
    """Load the encryption key from the file."""
    if not os.path.exists(KEY_FILE):
        generate_key()
    with open(KEY_FILE, 'rb') as key_file:
        return key_file.read()

# Encryption/Decryption
def encrypt_password(password: str) -> bytes:
    """Encrypt a password."""
    key = load_key()
    f = Fernet(key)
    return f.encrypt(password.encode())

def decrypt_password(encrypted_password: bytes) -> str:
    """Decrypt a password."""
    key = load_key()
    f = Fernet(key)
    return f.decrypt(encrypted_password).decode()
