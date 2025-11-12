"""Pytest configuration and fixtures."""

import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def test_env(tmp_path, monkeypatch):
    """Create isolated test environment with temporary directories."""
    # Create temporary directories
    data_dir = tmp_path / ".data"
    data_dir.mkdir()

    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    # Patch all path functions to use temp directories
    from secure_password_manager.utils import paths

    monkeypatch.setattr(paths, "get_data_dir", lambda: data_dir)
    monkeypatch.setattr(paths, "get_log_dir", lambda: logs_dir)
    monkeypatch.setattr(paths, "get_database_path", lambda: data_dir / "passwords.db")
    monkeypatch.setattr(paths, "get_secret_key_path", lambda: data_dir / "secret.key")
    monkeypatch.setattr(
        paths, "get_secret_key_enc_path", lambda: data_dir / "secret.key.enc"
    )
    monkeypatch.setattr(paths, "get_crypto_salt_path", lambda: data_dir / "crypto.salt")
    monkeypatch.setattr(paths, "get_auth_json_path", lambda: data_dir / "auth.json")
    monkeypatch.setattr(
        paths, "get_totp_config_path", lambda: data_dir / "totp_config.json"
    )
    monkeypatch.setattr(paths, "get_backup_dir", lambda: data_dir / "backups")
    monkeypatch.setattr(
        paths, "get_breach_cache_path", lambda: data_dir / "breach_cache.json"
    )

    # Reset crypto module state
    from secure_password_manager.utils import crypto

    crypto._MASTER_PW_CONTEXT = None

    yield {
        "data_dir": data_dir,
        "logs_dir": logs_dir,
    }

    # Cleanup: reset crypto context
    crypto._MASTER_PW_CONTEXT = None


@pytest.fixture
def clean_crypto_files(test_env):
    """Provide clean crypto environment for each test."""
    data_dir = test_env["data_dir"]

    # Remove any existing crypto files
    crypto_files = [
        data_dir / "secret.key",
        data_dir / "secret.key.enc",
        data_dir / "secret.key.bak",
        data_dir / "crypto.salt",
    ]

    for file in crypto_files:
        if file.exists():
            file.unlink()

    # Reset crypto module context
    from secure_password_manager.utils import crypto

    crypto._MASTER_PW_CONTEXT = None

    yield data_dir

    # Cleanup after test
    crypto._MASTER_PW_CONTEXT = None


@pytest.fixture
def clean_database(test_env):
    """Provide clean database for each test."""
    from secure_password_manager.utils.database import init_db
    from secure_password_manager.utils.paths import get_database_path

    db_path = get_database_path()

    # Remove existing database
    if db_path.exists():
        db_path.unlink()

    # Initialize fresh database
    init_db()

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()
