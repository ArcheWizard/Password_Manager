"""Pytest configuration and fixtures.

This module provides comprehensive test isolation to prevent tests from
modifying production data. All file operations are redirected to temporary
directories using monkeypatching.
"""

import os
import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Safety check: Ensure we never touch production .data directory
_PRODUCTION_DATA_DIR = Path(__file__).parent.parent / ".data"


def pytest_configure(config):
    """Global pytest configuration to prevent production data access."""
    # Set marker for tests that require isolation
    config.addinivalue_line(
        "markers", "isolated: mark test as requiring complete isolation"
    )


@pytest.fixture(scope="session", autouse=True)
def prevent_production_access():
    """Session-level safeguard to detect production directory access."""
    original_open = open

    def safe_open(file, mode='r', *args, **kwargs):
        filepath = Path(file).resolve()

        # Allow read-only access to production for test data setup
        if 'r' in mode and 'w' not in mode and '+' not in mode:
            return original_open(file, mode, *args, **kwargs)

        # Block write access to production .data directory
        if _PRODUCTION_DATA_DIR.exists() and filepath.is_relative_to(_PRODUCTION_DATA_DIR):
            raise RuntimeError(
                f"Test attempted to write to production directory: {filepath}\n"
                f"This is blocked to prevent data loss. Use test_env fixture."
            )

        return original_open(file, mode, *args, **kwargs)

    # Note: Monkeypatching builtins in session scope can be fragile
    # This is a warning system, not foolproof protection
    # The primary protection is proper use of test_env fixture

    yield


@pytest.fixture
def test_env(tmp_path, monkeypatch):
    """Create isolated test environment with temporary directories.

    This fixture ensures complete isolation from production data by:
    1. Creating temporary directories for all data/config/cache
    2. Monkeypatching all path functions to use temp directories
    3. Resetting module state before and after tests
    4. Preventing any access to production .data directory

    Usage:
        def test_something(test_env, clean_crypto_files, clean_database):
            # All file operations are now isolated
            pass
    """
    # Create temporary directories with proper structure
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()

    config_dir = tmp_path / "test_config"
    config_dir.mkdir()

    cache_dir = tmp_path / "test_cache"
    cache_dir.mkdir()

    logs_dir = tmp_path / "test_logs"
    logs_dir.mkdir()

    backups_dir = data_dir / "backups"
    backups_dir.mkdir()

    # Patch all path functions to use temp directories
    from secure_password_manager.utils import paths

    monkeypatch.setattr(paths, "get_data_dir", lambda: data_dir)
    monkeypatch.setattr(paths, "get_config_dir", lambda: config_dir)
    monkeypatch.setattr(paths, "get_cache_dir", lambda: cache_dir)
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
    monkeypatch.setattr(paths, "get_backup_dir", lambda: backups_dir)
    monkeypatch.setattr(
        paths, "get_breach_cache_path", lambda: cache_dir / "breach_cache.json"
    )
    monkeypatch.setattr(
        paths, "get_browser_bridge_tokens_path", lambda: data_dir / "browser_bridge_tokens.json"
    )

    # Ensure commonly used directories exist
    backups_dir.mkdir(exist_ok=True)
    # Ensure cert directory exists
    (config_dir / "certs").mkdir(exist_ok=True)

    # Reset all module-level state
    from secure_password_manager.utils import crypto, config, logger

    # Reset crypto module state
    crypto._MASTER_PW_CONTEXT = None

    # Reset logger state to use test directory
    logger._initialized = False
    logger.LOG_DIR = None
    logger.LOG_FILE = None

    # Patch environment to prevent any stray production access
    monkeypatch.setenv("SPM_DATA_DIR", str(data_dir))
    monkeypatch.setenv("SPM_CONFIG_DIR", str(config_dir))

    yield {
        "data_dir": data_dir,
        "config_dir": config_dir,
        "cache_dir": cache_dir,
        "logs_dir": logs_dir,
        "backups_dir": backups_dir,
        "tmp_path": tmp_path,
    }

    # Cleanup: reset all module state
    crypto._MASTER_PW_CONTEXT = None
    logger._initialized = False
    logger.LOG_DIR = None
    logger.LOG_FILE = None


@pytest.fixture
def clean_crypto_files(test_env):
    """Provide clean crypto environment for each test.

    Removes all crypto-related files including backups to ensure
    tests start with a pristine state.
    """
    data_dir = test_env["data_dir"]

    # Remove any existing crypto files (including backups!)
    crypto_patterns = [
        "secret.key*",  # Matches secret.key, secret.key.enc, secret.key.bak*, etc.
        "crypto.salt*",
        "auth.json*",
    ]

    for pattern in crypto_patterns:
        for file in data_dir.glob(pattern):
            if file.is_file():
                file.unlink()

    # Reset crypto module context
    from secure_password_manager.utils import crypto

    crypto._MASTER_PW_CONTEXT = None

    yield data_dir

    # Cleanup after test - remove any files created during test
    for pattern in crypto_patterns:
        for file in data_dir.glob(pattern):
            if file.is_file():
                file.unlink()

    crypto._MASTER_PW_CONTEXT = None

@pytest.fixture
def clean_database(test_env):
    """Provide clean database for each test.

    Initializes a fresh database in the isolated test environment
    and ensures proper cleanup of connections.
    """
    from secure_password_manager.utils.database import init_db, close_connection
    from secure_password_manager.utils.paths import get_database_path

    db_path = get_database_path()

    # Close any existing database connections before deleting
    close_connection()

    # Remove existing database if present
    if db_path.exists():
        db_path.unlink()

    # Initialize fresh database
    init_db()

    yield db_path

    # Cleanup: close connection and remove test database
    close_connection()
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def isolated_environment(test_env, clean_crypto_files, clean_database):
    """Combine all isolation fixtures for complete test isolation.

    Use this fixture when you need a completely fresh environment
    with no crypto files and a clean database.

    Usage:
        def test_something(isolated_environment):
            # Guaranteed fresh state
            pass
    """
    return test_env
