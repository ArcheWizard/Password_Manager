"""Tests for advanced crypto features: KDF versioning, key protection, and envelope encryption."""

import json
import os
import sys
import tempfile
from unittest.mock import patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.utils.crypto import (
    decrypt_with_password_envelope,
    derive_keys_from_password,
    encrypt_with_password_envelope,
    generate_key,
    generate_salt,
    is_key_protected,
    load_kdf_params,
    protect_key_with_master_password,
    set_master_password_context,
    unprotect_key,
)


def test_kdf_params_versioning(clean_crypto_files):
    """Test that KDF parameters are stored and loaded with versioning metadata."""
    from secure_password_manager.utils.paths import get_crypto_salt_path

    salt_file = get_crypto_salt_path()

    # Generate salt should create versioned metadata
    generated_salt = generate_salt()

    # Load should return the same salt with metadata
    salt, iterations, version = load_kdf_params()
    assert salt == generated_salt
    assert isinstance(salt, bytes)
    assert len(salt) == 16
    assert iterations == 100_000
    assert version == 1

    # Verify JSON format
    assert salt_file.exists()
    with open(salt_file) as f:
        data = json.load(f)
    assert data["kdf"] == "PBKDF2HMAC"
    assert data["version"] == 1
    assert data["iterations"] == 100_000
    assert "salt" in data
    assert "updated_at" in data


def test_kdf_params_legacy_migration(clean_crypto_files):
    """Test that legacy raw salt files are migrated to JSON format."""
    from secure_password_manager.utils.paths import get_crypto_salt_path

    salt_file = get_crypto_salt_path()

    # Create a legacy salt file (raw bytes)
    legacy_salt = os.urandom(16)
    with open(salt_file, "wb") as f:
        f.write(legacy_salt)

    # Load should migrate to JSON
    salt, iterations, version = load_kdf_params()
    assert salt == legacy_salt
    assert iterations == 100_000
    assert version == 1

    # Check that file was migrated to JSON
    assert salt_file.exists()
    with open(salt_file) as f:
        data = json.load(f)
    assert data["kdf"] == "PBKDF2HMAC"


def test_derive_keys_from_password(clean_crypto_files):
    """Test deriving separate encryption and HMAC keys from password."""
    password = "TestPassword123"
    enc_key, mac_key, meta = derive_keys_from_password(password)

    # Check that keys are different
    assert enc_key != mac_key

    # Check key lengths
    assert len(enc_key) == 44  # Base64 encoded 32 bytes
    assert len(mac_key) == 32  # Raw 32 bytes

    # Check metadata
    assert meta["kdf"] == "PBKDF2HMAC"
    assert "iterations" in meta


def test_envelope_encryption_with_hmac(clean_crypto_files):
    """Test that envelope encryption includes HMAC and verifies on decrypt."""
    password = "SecureBackupPassword"
    plaintext = "My secret data"

    blob = encrypt_with_password_envelope(plaintext, password)
    assert isinstance(blob, bytes)

    # Blob should be valid JSON
    envelope = json.loads(blob.decode("utf-8"))
    assert envelope["format"] == "spm-export"
    assert envelope["version"] == "2.1"
    assert "ciphertext" in envelope
    assert "hmac" in envelope
    assert envelope["hmac_alg"] == "HMAC-SHA256"

    # Decrypt should verify HMAC and return plaintext
    decrypted = decrypt_with_password_envelope(blob, password)
    assert decrypted == plaintext


def test_envelope_hmac_tampering_detection(clean_crypto_files):
    """Test that tampering with ciphertext or HMAC is detected."""
    password = "TestPassword"
    plaintext = "Secret data"

    blob = encrypt_with_password_envelope(plaintext, password)
    envelope = json.loads(blob.decode("utf-8"))

    # Tamper with ciphertext
    import base64

    tampered_ct = base64.b64encode(b"tampered").decode("ascii")
    envelope["ciphertext"] = tampered_ct
    tampered_blob = json.dumps(envelope).encode("utf-8")

    try:
        decrypt_with_password_envelope(tampered_blob, password)
        assert False, "Should have detected tampering"
    except ValueError as e:
        # Check for integrity verification failure
        assert "integrity" in str(e).lower() or "verification" in str(e).lower()


def test_protect_and_unprotect_key(clean_crypto_files):
    """Test protecting and unprotecting the secret key with master password."""
    from secure_password_manager.utils.paths import (
        get_secret_key_enc_path,
        get_secret_key_path,
    )

    key_file = get_secret_key_path()
    enc_key_file = get_secret_key_enc_path()

    # Generate a plaintext key
    generate_key()
    assert key_file.exists()
    assert not is_key_protected()

    with open(key_file, "rb") as f:
        original_key = f.read()

    # Protect the key with a master password
    master_pw = "MyMasterPassword123!"
    set_master_password_context(master_pw)
    result = protect_key_with_master_password(master_pw)
    assert result is True

    # Protected key should exist, plaintext key should be backed up/removed
    assert enc_key_file.exists()
    assert is_key_protected()

    # Unprotect and verify
    result = unprotect_key(master_pw)
    assert result is True
    assert key_file.exists()

    with open(key_file, "rb") as f:
        restored_key = f.read()
    assert restored_key == original_key


def test_backward_compat_legacy_export(clean_crypto_files):
    """Test that decrypt_with_password_envelope handles legacy raw Fernet tokens."""
    from secure_password_manager.utils.crypto import encrypt_password

    password = "LegacyPassword"
    plaintext = "Legacy data"

    # Create a legacy export (raw Fernet token)
    legacy_token = encrypt_password(plaintext, master_password=password)

    # Should decrypt without envelope
    decrypted = decrypt_with_password_envelope(legacy_token, password)
    assert decrypted == plaintext
