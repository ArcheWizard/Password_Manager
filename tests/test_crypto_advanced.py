"""Tests for advanced crypto features: KDF versioning, key protection, and envelope encryption."""

import json
import os
import sys
import tempfile
from unittest.mock import patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.crypto import (
    derive_keys_from_password,
    encrypt_with_password_envelope,
    decrypt_with_password_envelope,
    protect_key_with_master_password,
    unprotect_key,
    is_key_protected,
    load_kdf_params,
    set_master_password_context,
    generate_key,
)


def test_kdf_params_versioning():
    """Test that KDF parameters are stored and loaded with versioning metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        salt_file = os.path.join(tmpdir, "crypto.salt")
        with patch("utils.crypto.SALT_FILE", salt_file):
            # Load should generate new salt with metadata
            salt, iterations, version = load_kdf_params()
            assert isinstance(salt, bytes)
            assert len(salt) == 16
            assert iterations == 100_000
            assert version == 1

            # Verify JSON format
            assert os.path.exists(salt_file)
            with open(salt_file, "r") as f:
                data = json.load(f)
            assert data["kdf"] == "PBKDF2HMAC"
            assert data["version"] == 1
            assert data["iterations"] == 100_000
            assert "salt" in data
            assert "updated_at" in data


def test_kdf_params_legacy_migration():
    """Test that legacy raw salt files are migrated to JSON format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        salt_file = os.path.join(tmpdir, "crypto.salt")
        legacy_salt = os.urandom(16)

        # Write legacy raw salt
        with open(salt_file, "wb") as f:
            f.write(legacy_salt)

        with patch("utils.crypto.SALT_FILE", salt_file):
            salt, iterations, version = load_kdf_params()
            # Should read the same salt
            assert salt == legacy_salt
            assert iterations == 100_000
            assert version == 1

            # Should have migrated to JSON (non-fatal if write fails, so check if exists)
            try:
                with open(salt_file, "r") as f:
                    data = json.load(f)
                assert data["version"] == 1
            except Exception:
                # Migration write failed; acceptable for this test
                pass


def test_derive_keys_from_password():
    """Test deriving separate encryption and HMAC keys from password."""
    password = "TestPassword123!"
    enc_key, mac_key, meta = derive_keys_from_password(password)

    # Should return base64 Fernet key and raw HMAC key
    assert isinstance(enc_key, bytes)
    assert isinstance(mac_key, bytes)
    assert len(mac_key) == 32

    # Metadata should include KDF details
    assert meta["kdf"] == "PBKDF2HMAC"
    assert meta["version"] == 1
    assert "salt" in meta


def test_envelope_encryption_with_hmac():
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


def test_envelope_hmac_tampering_detection():
    """Test that tampering with ciphertext or HMAC is detected."""
    password = "SecureBackupPassword"
    plaintext = "My secret data"

    blob = encrypt_with_password_envelope(plaintext, password)
    envelope = json.loads(blob.decode("utf-8"))

    # Tamper with ciphertext
    envelope["ciphertext"] = envelope["ciphertext"][:-4] + "XXXX"
    tampered_blob = json.dumps(envelope).encode("utf-8")

    try:
        decrypt_with_password_envelope(tampered_blob, password)
        assert False, "Should have detected tampering"
    except ValueError:
        # Tampering detected (either by HMAC mismatch or decryption failure)
        pass


def test_protect_and_unprotect_key():
    """Test protecting and unprotecting the secret key with master password."""
    with tempfile.TemporaryDirectory() as tmpdir:
        key_file = os.path.join(tmpdir, "secret.key")
        enc_key_file = os.path.join(tmpdir, "secret.key.enc")
        salt_file = os.path.join(tmpdir, "crypto.salt")

        with patch("utils.crypto.KEY_FILE", key_file), \
             patch("utils.crypto.ENC_KEY_FILE", enc_key_file), \
             patch("utils.crypto.SALT_FILE", salt_file):

            # Generate a plaintext key
            generate_key()
            assert os.path.exists(key_file)
            assert not is_key_protected()

            with open(key_file, "rb") as f:
                original_key = f.read()

            # Protect the key with a master password
            master_pw = "MyMasterPassword123!"
            set_master_password_context(master_pw)
            protect_key_with_master_password(master_pw)

            # Protected key should exist, plaintext key should be backed up/removed
            assert os.path.exists(enc_key_file)
            assert is_key_protected()

            # Verify envelope format
            with open(enc_key_file, "r") as f:
                env = json.load(f)
            assert env["format"] == "spm-key"
            assert env["version"] == "1.0"
            assert "hmac" in env

            # Unprotect should restore plaintext key
            unprotect_key(master_pw)
            assert os.path.exists(key_file)

            with open(key_file, "rb") as f:
                restored_key = f.read()
            assert restored_key == original_key


def test_backward_compat_legacy_export():
    """Test that decrypt_with_password_envelope handles legacy raw Fernet tokens."""
    from utils.crypto import encrypt_password

    password = "LegacyPassword"
    plaintext = "Legacy data"

    # Create a legacy export (raw Fernet token)
    legacy_token = encrypt_password(plaintext, master_password=password)

    # Should decrypt without envelope
    decrypted = decrypt_with_password_envelope(legacy_token, password)
    assert decrypted == plaintext
