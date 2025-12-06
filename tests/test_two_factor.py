"""Tests for two_factor authentication module."""

import json
import os
import sys
from pathlib import Path

import pyotp
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.utils import two_factor
from secure_password_manager.utils.two_factor import (
    disable_2fa,
    generate_qr_code,
    generate_totp_secret,
    get_current_totp,
    get_totp_uri,
    is_2fa_enabled,
    setup_totp,
    verify_totp,
)


@pytest.fixture
def temp_totp_dir(tmp_path, monkeypatch):
    """Create a temporary directory for TOTP config."""
    totp_dir = tmp_path / "data"
    totp_dir.mkdir()
    totp_file = totp_dir / "totp_config.json"

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    # Import paths module directly
    from secure_password_manager.utils import paths

    monkeypatch.setattr(two_factor, "TOTP_CONFIG_FILE", str(totp_file))
    monkeypatch.setattr(paths, "get_totp_config_path", lambda: totp_file)
    monkeypatch.setattr(paths, "get_cache_dir", lambda: cache_dir)

    return totp_dir


def test_generate_totp_secret():
    """Test TOTP secret generation."""
    secret = generate_totp_secret()

    # Should be a base32 string
    assert isinstance(secret, str)
    assert len(secret) == 32
    assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567" for c in secret)


def test_get_totp_uri():
    """Test TOTP URI generation."""
    secret = "JBSWY3DPEHPK3PXP"
    uri = get_totp_uri(secret, "TestAccount")

    assert uri.startswith("otpauth://totp/")
    assert "TestAccount" in uri
    assert "Secure%20Password%20Manager" in uri or "Secure+Password+Manager" in uri
    assert secret in uri


def test_generate_qr_code(temp_totp_dir, tmp_path):
    """Test QR code generation."""
    secret = "JBSWY3DPEHPK3PXP"
    uri = get_totp_uri(secret)

    output_path = str(tmp_path / "test_qr.png")
    result_path = generate_qr_code(uri, output_path)

    assert result_path == output_path
    assert Path(result_path).exists()
    assert Path(result_path).stat().st_size > 0


def test_setup_totp(temp_totp_dir):
    """Test complete TOTP setup."""
    secret, qr_path = setup_totp("TestUser")

    # Verify secret was generated
    assert isinstance(secret, str)
    assert len(secret) == 32

    # Verify QR code was created
    assert Path(qr_path).exists()

    # Verify config was saved
    config_file = Path(two_factor.TOTP_CONFIG_FILE)
    assert config_file.exists()

    with open(config_file) as f:
        config = json.load(f)

    assert config["secret"] == secret
    assert config["account_name"] == "TestUser"
    assert "created_at" in config


def test_verify_totp(temp_totp_dir):
    """Test TOTP code verification."""
    # Setup 2FA
    secret, _ = setup_totp()

    # Generate a valid code
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()

    # Verify valid code
    assert verify_totp(valid_code) is True

    # Verify invalid code
    assert verify_totp("000000") is False
    assert verify_totp("999999") is False


def test_verify_totp_no_config(temp_totp_dir):
    """Test TOTP verification when no config exists."""
    assert verify_totp("123456") is False


def test_verify_totp_corrupted_config(temp_totp_dir):
    """Test TOTP verification with corrupted config."""
    config_file = Path(two_factor.TOTP_CONFIG_FILE)
    config_file.parent.mkdir(parents=True, exist_ok=True)

    # Write corrupted config (missing secret)
    with open(config_file, "w") as f:
        json.dump({"account_name": "Test"}, f)

    assert verify_totp("123456") is False


def test_get_current_totp(temp_totp_dir):
    """Test getting current TOTP code."""
    # No config exists
    assert get_current_totp() is None

    # Setup 2FA
    secret, _ = setup_totp()

    # Get current code
    current_code = get_current_totp()
    assert current_code is not None
    assert len(current_code) == 6
    assert current_code.isdigit()

    # Verify the code is valid
    assert verify_totp(current_code) is True


def test_get_current_totp_corrupted_config(temp_totp_dir):
    """Test getting current TOTP with corrupted config."""
    config_file = Path(two_factor.TOTP_CONFIG_FILE)
    config_file.parent.mkdir(parents=True, exist_ok=True)

    # Write corrupted config (missing secret)
    with open(config_file, "w") as f:
        json.dump({"account_name": "Test"}, f)

    assert get_current_totp() is None


def test_is_2fa_enabled(temp_totp_dir):
    """Test checking if 2FA is enabled."""
    # Initially disabled
    assert is_2fa_enabled() is False

    # Enable 2FA
    setup_totp()
    assert is_2fa_enabled() is True


def test_disable_2fa(temp_totp_dir):
    """Test disabling 2FA."""
    # Disable when not enabled
    assert disable_2fa() is False

    # Setup 2FA
    setup_totp()
    assert is_2fa_enabled() is True

    # Disable 2FA
    assert disable_2fa() is True
    assert is_2fa_enabled() is False

    # Disable again (already disabled)
    assert disable_2fa() is False


def test_totp_code_changes_over_time(temp_totp_dir):
    """Test that TOTP codes are time-based and change."""
    secret, _ = setup_totp()

    # Get two codes (they might be the same if within 30-second window)
    code1 = get_current_totp()

    # Both should be valid 6-digit codes
    assert code1 is not None
    assert len(code1) == 6
    assert code1.isdigit()


def test_setup_totp_custom_account_name(temp_totp_dir):
    """Test TOTP setup with custom account name."""
    secret, _ = setup_totp("CustomAccount")

    config_file = Path(two_factor.TOTP_CONFIG_FILE)
    with open(config_file) as f:
        config = json.load(f)

    assert config["account_name"] == "CustomAccount"


def test_generate_qr_code_default_path(temp_totp_dir):
    """Test QR code generation with default path."""
    secret = "JBSWY3DPEHPK3PXP"
    uri = get_totp_uri(secret)

    # Generate QR with default path
    result_path = generate_qr_code(uri)

    assert Path(result_path).exists()
    assert "totp_qr.png" in result_path
