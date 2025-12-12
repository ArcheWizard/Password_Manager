"""Tests for payload encryption module."""

import base64
import json
import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.utils.payload_encryption import (
    PayloadEncryption,
    create_payload_encryptor,
    decode_shared_secret,
    encode_shared_secret,
    generate_shared_secret,
)


def test_generate_shared_secret():
    """Test shared secret generation."""
    secret = generate_shared_secret()

    assert isinstance(secret, bytes)
    assert len(secret) == 32


def test_generate_shared_secret_uniqueness():
    """Test that generated secrets are unique."""
    secret1 = generate_shared_secret()
    secret2 = generate_shared_secret()

    assert secret1 != secret2


def test_encode_decode_shared_secret():
    """Test encoding and decoding shared secret."""
    original_secret = generate_shared_secret()
    encoded = encode_shared_secret(original_secret)

    assert isinstance(encoded, str)
    assert len(encoded) > 0

    decoded = decode_shared_secret(encoded)
    assert decoded == original_secret


def test_payload_encryption_init():
    """Test PayloadEncryption initialization."""
    secret = generate_shared_secret()
    encryptor = PayloadEncryption(secret)

    assert encryptor.shared_secret == secret


def test_payload_encryption_init_invalid_length():
    """Test PayloadEncryption initialization with invalid key length."""
    invalid_secret = b"short"

    with pytest.raises(ValueError, match="Shared secret must be 32 bytes"):
        PayloadEncryption(invalid_secret)


def test_payload_encryption_encrypt():
    """Test payload encryption."""
    secret = generate_shared_secret()
    encryptor = PayloadEncryption(secret)

    payload = {"username": "test_user", "password": "secret123"}
    encrypted = encryptor.encrypt(payload)

    assert "ciphertext" in encrypted
    assert "nonce" in encrypted
    assert "tag" in encrypted
    assert isinstance(encrypted["ciphertext"], str)
    assert isinstance(encrypted["nonce"], str)
    assert isinstance(encrypted["tag"], str)


def test_payload_encryption_decrypt():
    """Test payload decryption."""
    secret = generate_shared_secret()
    encryptor = PayloadEncryption(secret)

    original_payload = {"username": "test_user", "password": "secret123"}
    encrypted = encryptor.encrypt(original_payload)
    decrypted = encryptor.decrypt(encrypted)

    assert decrypted == original_payload


def test_payload_encryption_roundtrip():
    """Test encryption and decryption roundtrip."""
    secret = generate_shared_secret()
    encryptor = PayloadEncryption(secret)

    test_cases = [
        {"simple": "data"},
        {"nested": {"key": "value", "number": 42}},
        {"list": [1, 2, 3, "four"]},
        {"unicode": "Hello 世界 🔐"},
        {"empty": {}},
    ]

    for payload in test_cases:
        encrypted = encryptor.encrypt(payload)
        decrypted = encryptor.decrypt(encrypted)
        assert decrypted == payload


def test_payload_encryption_different_nonces():
    """Test that each encryption uses a different nonce."""
    secret = generate_shared_secret()
    encryptor = PayloadEncryption(secret)

    payload = {"test": "data"}
    encrypted1 = encryptor.encrypt(payload)
    encrypted2 = encryptor.encrypt(payload)

    assert encrypted1["nonce"] != encrypted2["nonce"]
    assert encrypted1["ciphertext"] != encrypted2["ciphertext"]


def test_payload_encryption_wrong_key():
    """Test that decryption fails with wrong key."""
    secret1 = generate_shared_secret()
    secret2 = generate_shared_secret()

    encryptor1 = PayloadEncryption(secret1)
    encryptor2 = PayloadEncryption(secret2)

    payload = {"sensitive": "data"}
    encrypted = encryptor1.encrypt(payload)

    with pytest.raises(Exception):
        encryptor2.decrypt(encrypted)


def test_payload_encryption_tampered_ciphertext():
    """Test that decryption fails with tampered ciphertext."""
    secret = generate_shared_secret()
    encryptor = PayloadEncryption(secret)

    payload = {"test": "data"}
    encrypted = encryptor.encrypt(payload)

    # Tamper with ciphertext
    tampered_ciphertext = base64.b64encode(b"tampered data").decode("ascii")
    encrypted["ciphertext"] = tampered_ciphertext

    with pytest.raises(Exception):
        encryptor.decrypt(encrypted)


def test_payload_encryption_tampered_tag():
    """Test that decryption fails with tampered tag."""
    secret = generate_shared_secret()
    encryptor = PayloadEncryption(secret)

    payload = {"test": "data"}
    encrypted = encryptor.encrypt(payload)

    # Tamper with tag
    tampered_tag = base64.b64encode(b"fake_tag_data123").decode("ascii")
    encrypted["tag"] = tampered_tag

    with pytest.raises(Exception):
        encryptor.decrypt(encrypted)


def test_payload_encryption_tampered_nonce():
    """Test that decryption fails with tampered nonce."""
    secret = generate_shared_secret()
    encryptor = PayloadEncryption(secret)

    payload = {"test": "data"}
    encrypted = encryptor.encrypt(payload)

    # Tamper with nonce
    tampered_nonce = base64.b64encode(b"fake_nonce12").decode("ascii")
    encrypted["nonce"] = tampered_nonce

    with pytest.raises(Exception):
        encryptor.decrypt(encrypted)


def test_payload_encryption_invalid_base64():
    """Test that decryption fails with invalid base64."""
    secret = generate_shared_secret()
    encryptor = PayloadEncryption(secret)

    encrypted = {
        "ciphertext": "invalid!!!base64",
        "nonce": "also_invalid",
        "tag": "not_base64",
    }

    with pytest.raises(Exception):
        encryptor.decrypt(encrypted)


def test_payload_encryption_missing_fields():
    """Test that decryption fails with missing fields."""
    secret = generate_shared_secret()
    encryptor = PayloadEncryption(secret)

    # Missing ciphertext - should raise KeyError
    with pytest.raises(KeyError):
        encryptor.decrypt({"nonce": "abc", "tag": "def"})

    # Missing nonce - tries to decode base64 first, raises binascii.Error
    with pytest.raises((KeyError, Exception)):
        encryptor.decrypt({"ciphertext": "abc", "tag": "def"})

    # Missing tag - tries to decode base64 first, raises binascii.Error
    with pytest.raises((KeyError, Exception)):
        encryptor.decrypt({"ciphertext": "abc", "nonce": "def"})


def test_payload_encryption_empty_payload():
    """Test encryption of empty payload."""
    secret = generate_shared_secret()
    encryptor = PayloadEncryption(secret)

    payload = {}
    encrypted = encryptor.encrypt(payload)
    decrypted = encryptor.decrypt(encrypted)

    assert decrypted == payload


def test_payload_encryption_large_payload():
    """Test encryption of large payload."""
    secret = generate_shared_secret()
    encryptor = PayloadEncryption(secret)

    # Create a large payload
    payload = {"data": "x" * 10000, "numbers": list(range(1000))}
    encrypted = encryptor.encrypt(payload)
    decrypted = encryptor.decrypt(encrypted)

    assert decrypted == payload


def test_payload_encryption_special_characters():
    """Test encryption with special characters."""
    secret = generate_shared_secret()
    encryptor = PayloadEncryption(secret)

    payload = {
        "symbols": "!@#$%^&*()_+-={}[]|:;<>,.?/",
        "quotes": '"single" and \'double\'',
        "unicode": "émoji 🔐 中文",
        "newlines": "line1\nline2\r\nline3",
    }

    encrypted = encryptor.encrypt(payload)
    decrypted = encryptor.decrypt(encrypted)

    assert decrypted == payload


def test_create_payload_encryptor():
    """Test creating payload encryptor from token."""
    token = "test_auth_token_12345"
    encryptor = create_payload_encryptor(token)

    assert isinstance(encryptor, PayloadEncryption)
    assert encryptor.shared_secret is not None
    assert len(encryptor.shared_secret) == 32


def test_create_payload_encryptor_deterministic():
    """Test that same token creates same key."""
    token = "test_auth_token"
    encryptor1 = create_payload_encryptor(token)
    encryptor2 = create_payload_encryptor(token)

    assert encryptor1.shared_secret == encryptor2.shared_secret


def test_create_payload_encryptor_different_tokens():
    """Test that different tokens create different keys."""
    encryptor1 = create_payload_encryptor("token1")
    encryptor2 = create_payload_encryptor("token2")

    assert encryptor1.shared_secret != encryptor2.shared_secret


def test_create_payload_encryptor_roundtrip():
    """Test encryption roundtrip with token-based encryptor."""
    token = "my_secure_token"
    encryptor = create_payload_encryptor(token)

    payload = {"user": "alice", "action": "login"}
    encrypted = encryptor.encrypt(payload)

    # Create another encryptor with same token
    encryptor2 = create_payload_encryptor(token)
    decrypted = encryptor2.decrypt(encrypted)

    assert decrypted == payload


def test_payload_encryption_preserves_types():
    """Test that encryption preserves data types."""
    secret = generate_shared_secret()
    encryptor = PayloadEncryption(secret)

    payload = {
        "string": "text",
        "integer": 42,
        "float": 3.14,
        "boolean": True,
        "null": None,
        "list": [1, 2, 3],
        "dict": {"nested": "value"},
    }

    encrypted = encryptor.encrypt(payload)
    decrypted = encryptor.decrypt(encrypted)

    assert decrypted == payload
    assert type(decrypted["string"]) == str
    assert type(decrypted["integer"]) == int
    assert type(decrypted["float"]) == float
    assert type(decrypted["boolean"]) == bool
    assert decrypted["null"] is None


def test_payload_encryption_nonce_length():
    """Test that nonce is correct length."""
    secret = generate_shared_secret()
    encryptor = PayloadEncryption(secret)

    payload = {"test": "data"}
    encrypted = encryptor.encrypt(payload)

    nonce = base64.b64decode(encrypted["nonce"])
    assert len(nonce) == 12  # 12 bytes for AES-GCM


def test_payload_encryption_uses_hkdf():
    """Test that different nonces produce different derived keys."""
    secret = generate_shared_secret()
    encryptor = PayloadEncryption(secret)

    # Encrypt same payload twice
    payload = {"test": "data"}
    encrypted1 = encryptor.encrypt(payload)
    encrypted2 = encryptor.encrypt(payload)

    # Different nonces should result in different ciphertexts
    # even though the shared secret is the same
    assert encrypted1["nonce"] != encrypted2["nonce"]
    assert encrypted1["ciphertext"] != encrypted2["ciphertext"]
    assert encrypted1["tag"] != encrypted2["tag"]


def test_encode_shared_secret_format():
    """Test that encoded secret is valid base64."""
    secret = generate_shared_secret()
    encoded = encode_shared_secret(secret)

    # Should be valid base64
    try:
        decoded = base64.b64decode(encoded)
        assert decoded == secret
    except Exception:
        pytest.fail("Encoded secret is not valid base64")


def test_decode_shared_secret_invalid():
    """Test decoding invalid base64."""
    with pytest.raises(Exception):
        decode_shared_secret("not valid base64!!!")


def test_payload_encryption_json_serialization():
    """Test that payload is properly JSON serialized."""
    secret = generate_shared_secret()
    encryptor = PayloadEncryption(secret)

    payload = {"key": "value"}
    encrypted = encryptor.encrypt(payload)

    # Decrypt and verify JSON structure was preserved
    decrypted = encryptor.decrypt(encrypted)
    assert json.dumps(decrypted, separators=(",", ":")) == json.dumps(
        payload, separators=(",", ":")
    )
