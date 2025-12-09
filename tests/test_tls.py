"""Tests for TLS certificate generation."""

import os
import sys
from pathlib import Path

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.utils.tls import (
    cert_exists,
    generate_self_signed_cert,
    get_cert_fingerprint,
    get_cert_paths,
    remove_cert,
)


def test_generate_self_signed_cert_creates_files():
    """Test that generate_self_signed_cert creates certificate files."""
    # Clean up any existing certs
    remove_cert()

    cert_path, key_path = generate_self_signed_cert()

    # Check files were created
    assert cert_path.exists()
    assert key_path.exists()

    # Check files have content
    assert cert_path.stat().st_size > 0
    assert key_path.stat().st_size > 0

    # Clean up
    remove_cert()


def test_generate_self_signed_cert_returns_existing():
    """Test that generate_self_signed_cert reuses valid certificates."""
    remove_cert()

    # Generate first time
    cert_path1, key_path1 = generate_self_signed_cert()
    fingerprint1 = get_cert_fingerprint(cert_path1)

    # Generate second time - should reuse
    cert_path2, key_path2 = generate_self_signed_cert()
    fingerprint2 = get_cert_fingerprint(cert_path2)

    # Should be the same certificate
    assert cert_path1 == cert_path2
    assert fingerprint1 == fingerprint2

    remove_cert()


def test_cert_exists_function():
    """Test the cert_exists helper function."""
    remove_cert()

    assert cert_exists() is False

    generate_self_signed_cert()
    assert cert_exists() is True

    remove_cert()
    assert cert_exists() is False


def test_get_cert_fingerprint_valid():
    """Test getting certificate SHA256 fingerprint."""
    remove_cert()

    cert_path, _ = generate_self_signed_cert()
    fingerprint = get_cert_fingerprint(cert_path)

    assert fingerprint is not None
    # SHA256 fingerprint with colons should be 95 characters (64 hex + 31 colons)
    assert len(fingerprint) == 95
    # Should be in format XX:XX:XX...
    parts = fingerprint.split(':')
    assert len(parts) == 32  # 32 pairs of hex digits
    assert all(len(part) == 2 for part in parts)
    assert all(all(c in '0123456789abcdef' for c in part.lower()) for part in parts)

    remove_cert()
def test_get_cert_fingerprint_nonexistent():
    """Test fingerprint of nonexistent certificate."""
    fake_path = Path("/nonexistent/cert.pem")
    fingerprint = get_cert_fingerprint(fake_path)

    assert fingerprint is None


def test_remove_cert_function():
    """Test removing certificates."""
    remove_cert()  # Clean slate

    generate_self_signed_cert()
    assert cert_exists() is True

    result = remove_cert()
    assert result is True
    assert cert_exists() is False


def test_certificate_contains_san_entries():
    """Test that certificate includes Subject Alternative Names."""
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend

    remove_cert()

    cert_path, _ = generate_self_signed_cert()

    # Load and inspect certificate
    with open(cert_path, 'rb') as f:
        cert = x509.load_pem_x509_certificate(f.read(), default_backend())

    # Check SAN extension exists
    san_ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
    assert san_ext is not None

    # Check required names are present
    dns_names = san_ext.value.get_values_for_type(x509.DNSName)
    assert 'localhost' in dns_names

    ip_addresses = [str(ip) for ip in san_ext.value.get_values_for_type(x509.IPAddress)]
    assert '127.0.0.1' in ip_addresses
    assert '::1' in ip_addresses

    remove_cert()


def test_private_key_is_rsa_2048():
    """Test that private key is RSA 2048-bit."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend

    remove_cert()

    _, key_path = generate_self_signed_cert()

    # Load private key
    with open(key_path, 'rb') as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )

    # Check key type and size
    assert isinstance(private_key, rsa.RSAPrivateKey)
    assert private_key.key_size == 2048

    remove_cert()