import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.utils.crypto import (
    decrypt_password,
    encrypt_password,
    generate_key,
    load_key,
    set_master_password_context,
)


def test_encryption_decryption(clean_crypto_files):
    """Test that encryption and decryption functions work correctly."""
    # Generate a key for testing (plaintext mode, no master password protection)
    generate_key()

    # Don't set master password context for plaintext key mode
    original = "mySecretPassword123!"
    encrypted = encrypt_password(original)
    decrypted = decrypt_password(encrypted)

    # Check that encrypted value is different from original
    assert encrypted != original.encode()
    # Check that decryption returns the original value
    assert decrypted == original


def test_key_generation_and_loading(clean_crypto_files):
    """Test that key generation and loading work properly."""
    from secure_password_manager.utils.paths import get_secret_key_path

    key_path = get_secret_key_path()

    # Test that generate_key creates a file
    generate_key()
    assert key_path.exists()

    # Test that load_key returns bytes (plaintext mode)
    key = load_key()
    assert isinstance(key, bytes)
    assert len(key) > 0
