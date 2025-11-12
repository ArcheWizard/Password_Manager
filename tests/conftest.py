"""Pytest configuration and fixtures for Password Manager tests."""

import os
import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="function", autouse=True)
def test_env(tmp_path, monkeypatch):
    """
    Set up a clean test environment for each test.

    This fixture:
    - Creates a temporary directory for test data
    - Sets environment variables to use the temp directory
    - Patches the paths module to use the temp directory
    - Cleans up after each test
    """
    # Create test data directory
    test_data_dir = tmp_path / ".data"
    test_data_dir.mkdir()

    # Set environment variables for XDG directories
    monkeypatch.setenv("XDG_DATA_HOME", str(test_data_dir))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(test_data_dir))
    monkeypatch.setenv("XDG_CACHE_HOME", str(test_data_dir))

    # Store original working directory
    original_cwd = os.getcwd()

    # Change to temp directory
    os.chdir(tmp_path)

    # Patch the paths module to force development mode in temp directory
    from secure_password_manager.utils import paths

    original_get_project_root = paths.get_project_root
    original_is_dev_mode = paths.is_development_mode

    def mock_get_project_root():
        return tmp_path

    def mock_is_dev_mode():
        return True

    monkeypatch.setattr(paths, "get_project_root", mock_get_project_root)
    monkeypatch.setattr(paths, "is_development_mode", mock_is_dev_mode)

    yield tmp_path

    # Restore original working directory
    os.chdir(original_cwd)


@pytest.fixture(scope="function")
def clean_crypto_files(test_env):
    """Remove any crypto-related files before and after tests."""
    from secure_password_manager.utils.paths import (
        get_auth_json_path,
        get_crypto_salt_path,
        get_secret_key_enc_path,
        get_secret_key_path,
    )

    files_to_clean = [
        get_secret_key_path(),
        get_secret_key_enc_path(),
        get_crypto_salt_path(),
        get_auth_json_path(),
    ]

    # Clean before test
    for file_path in files_to_clean:
        if file_path.exists():
            file_path.unlink()

    yield

    # Clean after test
    for file_path in files_to_clean:
        if file_path.exists():
            file_path.unlink()


@pytest.fixture(scope="function")
def clean_database(test_env):
    """Remove database file before and after tests."""
    from secure_password_manager.utils.paths import get_database_path

    db_path = get_database_path()

    # Clean before test
    if db_path.exists():
        db_path.unlink()

    yield

    # Clean after test
    if db_path.exists():
        db_path.unlink()
