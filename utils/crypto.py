from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
import base64
import os

# Key generation/loading
KEY_FILE = 'secret.key'
SALT_FILE = 'crypto.salt'

def generate_salt() -> bytes:
    """Generate and save a salt for key derivation."""
    salt = os.urandom(16)
    with open(SALT_FILE, 'wb') as salt_file:
        salt_file.write(salt)
    return salt

def load_salt() -> bytes:
    """Load the salt from file or generate if not exists."""
    if not os.path.exists(SALT_FILE):
        return generate_salt()
    with open(SALT_FILE, 'rb') as salt_file:
        return salt_file.read()

def derive_key_from_password(password: str) -> bytes:
    """Derive a key from the master password using PBKDF2."""
    salt = load_salt()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

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

# Encryption/Decryption with master password option
def encrypt_password(password: str, master_password: str = None) -> bytes:
    """
    Encrypt a password.
    
    Args:
        password: The password to encrypt
        master_password: If provided, derive key from this instead of file
    """
    if master_password:
        key = derive_key_from_password(master_password)
    else:
        key = load_key()
    
    f = Fernet(key)
    return f.encrypt(password.encode())

def decrypt_password(encrypted_password: bytes, master_password: str = None) -> str:
    """
    Decrypt a password.
    
    Args:
        encrypted_password: The encrypted password to decrypt
        master_password: If provided, derive key from this instead of file
    """
    try:
        if master_password:
            key = derive_key_from_password(master_password)
        else:
            key = load_key()
        
        f = Fernet(key)
        return f.decrypt(encrypted_password).decode()
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")
