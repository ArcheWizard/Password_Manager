"""Two-factor authentication utilities."""

import json
import os
from datetime import datetime
from typing import Optional, Tuple

import pyotp
import qrcode

from secure_password_manager.utils.paths import get_cache_dir, get_totp_config_path

# 2FA configuration file
TOTP_CONFIG_FILE = str(get_totp_config_path())


def generate_totp_secret() -> str:
    """Generate a random secret key for TOTP."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, account_name: str = "Password Manager") -> str:
    """Generate the URI for TOTP QR code."""
    return pyotp.totp.TOTP(secret).provisioning_uri(
        account_name, issuer_name="Secure Password Manager"
    )


def generate_qr_code(uri: str, output_path: Optional[str] = None) -> str:
    """Generate a QR code image for the TOTP URI."""
    if output_path is None:
        output_path = str(get_cache_dir() / "totp_qr.png")

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)
    return output_path


def setup_totp(account_name: str = "Password Manager") -> Tuple[str, str]:
    """
    Set up TOTP for 2FA.

    Returns:
        Tuple containing (secret, qr_code_path)
    """
    # Generate a secret
    secret = generate_totp_secret()

    # Generate a URI for the QR code
    uri = get_totp_uri(secret, account_name)

    # Generate QR code
    qr_path = generate_qr_code(uri)

    # Save configuration
    config = {
        "secret": secret,
        "created_at": datetime.now().isoformat(),
        "account_name": account_name,
    }

    with open(TOTP_CONFIG_FILE, "w") as f:
        json.dump(config, f)

    return secret, qr_path


def verify_totp(code: str) -> bool:
    """Verify a TOTP code."""
    if not os.path.exists(TOTP_CONFIG_FILE):
        return False

    with open(TOTP_CONFIG_FILE) as f:
        config = json.load(f)

    secret = config.get("secret")
    if not secret:
        return False

    totp = pyotp.TOTP(secret)
    return totp.verify(code)


def get_current_totp() -> Optional[str]:
    """Get the current TOTP code (for testing)."""
    if not os.path.exists(TOTP_CONFIG_FILE):
        return None

    with open(TOTP_CONFIG_FILE) as f:
        config = json.load(f)

    secret = config.get("secret")
    if not secret:
        return None

    totp = pyotp.TOTP(secret)
    return totp.now()


def is_2fa_enabled() -> bool:
    """Check if 2FA is enabled."""
    return os.path.exists(TOTP_CONFIG_FILE)


def disable_2fa() -> bool:
    """Disable 2FA by removing configuration."""
    if os.path.exists(TOTP_CONFIG_FILE):
        os.remove(TOTP_CONFIG_FILE)
        return True
    return False
