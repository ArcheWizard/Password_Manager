"""Encrypted payload utilities for browser bridge communication.

This module provides end-to-end encryption for sensitive payloads exchanged
between the browser extension and the desktop app, adding an extra layer of
security beyond TLS.
"""

from __future__ import annotations

import base64
import json
import secrets
from typing import Any, Dict, Optional, Tuple

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from secure_password_manager.utils.logger import log_warning


class PayloadEncryption:
    """Handles symmetric encryption/decryption of JSON payloads."""

    def __init__(self, shared_secret: bytes):
        """Initialize with a shared secret key.

        Args:
            shared_secret: 32-byte shared secret for encryption
        """
        if len(shared_secret) != 32:
            raise ValueError("Shared secret must be 32 bytes")
        self.shared_secret = shared_secret

    def encrypt(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """Encrypt a JSON payload.

        Args:
            payload: Dictionary to encrypt

        Returns:
            Dictionary with 'ciphertext', 'nonce', and 'tag' as base64 strings
        """
        try:
            # Serialize to JSON
            plaintext = json.dumps(payload, separators=(',', ':')).encode('utf-8')

            # Generate a random nonce (12 bytes for AES-GCM)
            nonce = secrets.token_bytes(12)

            # Derive a unique key using HKDF with nonce as info
            derived_key = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=None,
                info=nonce,
            ).derive(self.shared_secret)

            # Encrypt with AES-256-GCM
            cipher = Cipher(
                algorithms.AES(derived_key),
                modes.GCM(nonce),
            )
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(plaintext) + encryptor.finalize()

            return {
                'ciphertext': base64.b64encode(ciphertext).decode('ascii'),
                'nonce': base64.b64encode(nonce).decode('ascii'),
                'tag': base64.b64encode(encryptor.tag).decode('ascii'),
            }
        except Exception as e:
            log_warning(f"Payload encryption failed: {e}")
            raise

    def decrypt(self, encrypted: Dict[str, str]) -> Dict[str, Any]:
        """Decrypt an encrypted payload.

        Args:
            encrypted: Dictionary with 'ciphertext', 'nonce', and 'tag' as base64 strings

        Returns:
            Decrypted dictionary
        """
        try:
            # Decode from base64
            ciphertext = base64.b64decode(encrypted['ciphertext'])
            nonce = base64.b64decode(encrypted['nonce'])
            tag = base64.b64decode(encrypted['tag'])

            # Derive the same key using HKDF with nonce as info
            derived_key = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=None,
                info=nonce,
            ).derive(self.shared_secret)

            # Decrypt with AES-256-GCM
            cipher = Cipher(
                algorithms.AES(derived_key),
                modes.GCM(nonce, tag),
            )
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            # Parse JSON
            return json.loads(plaintext.decode('utf-8'))
        except Exception as e:
            log_warning(f"Payload decryption failed: {e}")
            raise


def generate_shared_secret() -> bytes:
    """Generate a new 32-byte shared secret for payload encryption."""
    return secrets.token_bytes(32)


def encode_shared_secret(secret: bytes) -> str:
    """Encode shared secret to base64 for transmission."""
    return base64.b64encode(secret).decode('ascii')


def decode_shared_secret(encoded: str) -> bytes:
    """Decode base64-encoded shared secret."""
    return base64.b64decode(encoded)


def create_payload_encryptor(token: str) -> PayloadEncryption:
    """Create a payload encryptor using a token as the shared secret.

    Args:
        token: Authentication token to use as basis for encryption key

    Returns:
        PayloadEncryption instance
    """
    # Derive a 32-byte key from the token
    key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'secure-password-manager-payload-encryption',
        info=b'browser-bridge-v1',
    ).derive(token.encode('utf-8'))

    return PayloadEncryption(key)
