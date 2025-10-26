import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.crypto import decrypt_password, encrypt_password, generate_key, load_key


def test_encryption_decryption():
    """Test that encryption and decryption functions work correctly."""
    original = "mySecretPassword123!"
    encrypted = encrypt_password(original)
    decrypted = decrypt_password(encrypted)

    # Check that encrypted value is different from original
    assert encrypted != original.encode()
    # Check that decryption returns the original value
    assert decrypted == original


def test_key_generation_and_loading():
    """Test that key generation and loading work properly."""
    # Remove existing key file if present
    if os.path.exists("secret.key"):
        os.rename("secret.key", "secret.key.bak")

    try:
        # Test that generate_key creates a file
        generate_key()
        assert os.path.exists("secret.key")

        # Test that load_key returns bytes
        key = load_key()
        assert isinstance(key, bytes)
        assert len(key) > 0
    finally:
        # Restore original key file if existed
        if os.path.exists("secret.key.bak"):
            os.replace("secret.key.bak", "secret.key")
        elif os.path.exists("secret.key"):
            os.remove("secret.key")
