"""TLS certificate generation and management for browser bridge.

This module provides utilities for generating self-signed TLS certificates
for secure localhost communication between the browser extension and the
desktop app.
"""

from __future__ import annotations

import datetime
import hashlib
import ipaddress
from pathlib import Path
from typing import Optional, Tuple

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, ExtensionOID, NameOID

from secure_password_manager.utils.logger import log_info, log_warning
from secure_password_manager.utils.paths import get_config_dir


def get_cert_dir() -> Path:
    """Get the directory for storing TLS certificates."""
    cert_dir = get_config_dir() / "tls"
    cert_dir.mkdir(parents=True, exist_ok=True)
    return cert_dir


def get_cert_paths() -> Tuple[Path, Path]:
    """Get the paths to the certificate and private key files."""
    cert_dir = get_cert_dir()
    return cert_dir / "localhost.crt", cert_dir / "localhost.key"


def get_cert_fingerprint(cert_path: Path) -> Optional[str]:
    """Get SHA256 fingerprint of a certificate for pinning."""
    try:
        with open(cert_path, "rb") as f:
            cert_data = f.read()
        cert = x509.load_pem_x509_certificate(cert_data)
        fingerprint = hashlib.sha256(cert.public_bytes(serialization.Encoding.DER)).hexdigest()
        return ":".join(fingerprint[i:i+2] for i in range(0, len(fingerprint), 2))
    except Exception as e:
        log_warning(f"Failed to get certificate fingerprint: {e}")
        return None


def generate_self_signed_cert(
    hostname: str = "localhost",
    validity_days: int = 365,
) -> Tuple[Path, Path]:
    """Generate a self-signed TLS certificate for localhost.

    Args:
        hostname: The hostname for the certificate (default: localhost)
        validity_days: Certificate validity period in days (default: 365)

    Returns:
        Tuple of (cert_path, key_path)
    """
    cert_path, key_path = get_cert_paths()

    # Check if certificate already exists and is still valid
    if cert_path.exists() and key_path.exists():
        try:
            with open(cert_path, "rb") as f:
                cert = x509.load_pem_x509_certificate(f.read())

            # Check if certificate is still valid for at least 30 days
            days_remaining = (cert.not_valid_after_utc - datetime.datetime.now(datetime.timezone.utc)).days
            if days_remaining > 30:
                log_info(f"Using existing TLS certificate (valid for {days_remaining} more days)")
                return cert_path, key_path
            else:
                log_info(f"TLS certificate expires in {days_remaining} days, regenerating...")
        except Exception as e:
            log_warning(f"Failed to load existing certificate: {e}, regenerating...")

    log_info("Generating new self-signed TLS certificate for browser bridge...")

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Create certificate subject
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Local"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Secure Password Manager"),
        x509.NameAttribute(NameOID.COMMON_NAME, hostname),
    ])

    # Build certificate
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=validity_days))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(hostname),
                x509.DNSName("127.0.0.1"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                x509.IPAddress(ipaddress.IPv6Address("::1")),
            ]),
            critical=False,
        )
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([
                ExtendedKeyUsageOID.SERVER_AUTH,
            ]),
            critical=False,
        )
        .sign(private_key, hashes.SHA256())
    )

    # Write private key
    with open(key_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    # Write certificate
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    # Set restrictive permissions
    key_path.chmod(0o600)
    cert_path.chmod(0o644)

    fingerprint = get_cert_fingerprint(cert_path)
    log_info(f"Generated TLS certificate with fingerprint: {fingerprint}")
    log_info(f"Certificate saved to: {cert_path}")
    log_info(f"Private key saved to: {key_path}")

    return cert_path, key_path


def cert_exists() -> bool:
    """Check if TLS certificate and key files exist."""
    cert_path, key_path = get_cert_paths()
    return cert_path.exists() and key_path.exists()


def remove_cert() -> bool:
    """Remove existing TLS certificate and key files."""
    cert_path, key_path = get_cert_paths()
    removed = False

    if cert_path.exists():
        cert_path.unlink()
        removed = True
        log_info(f"Removed certificate: {cert_path}")

    if key_path.exists():
        key_path.unlink()
        removed = True
        log_info(f"Removed private key: {key_path}")

    return removed
