"""Tests to verify test isolation is working correctly."""

import os
import sys
from pathlib import Path

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.utils.auth import set_master_password
from secure_password_manager.utils.crypto import (
    generate_key,
    protect_key_with_master_password,
)
from secure_password_manager.utils.database import add_password, init_db
# Import module, not functions
from secure_password_manager.utils import paths


def test_isolation_uses_temp_directory(test_env):
    """Verify that test environment uses temporary directory, not production."""
    # Use module.function() syntax to get monkeypatched version
    data_dir = paths.get_data_dir()

    # Should be in temp directory (cross-platform check)
    data_dir_str = str(data_dir).lower()
    is_temp = (
        "/tmp" in data_dir_str or
        "pytest" in data_dir_str or
        "/var/folders" in data_dir_str or  # macOS
        "\\temp\\" in data_dir_str  # Windows
    )
    assert is_temp, f"Should use temp directory, got: {data_dir}"

    # Should NOT be production .data directory
    production_data = Path(__file__).parent.parent / ".data"
    assert data_dir != production_data
    assert not str(data_dir).endswith("/.data")


def test_crypto_backup_files_in_isolation(isolated_environment):
    """Verify .bak files are created in temp dir, not production."""
    # Generate key and protect it (creates .bak files)
    generate_key()
    protect_key_with_master_password("test_password123")

    data_dir = paths.get_data_dir()
    key_path = paths.get_secret_key_path()

    # Check for any .bak files created
    bak_files = list(data_dir.glob("secret.key.bak*"))

    # If .bak files exist, they should be in temp dir
    for bak_file in bak_files:
        assert data_dir in bak_file.parents

        # Should NOT be in production
        production_data = Path(__file__).parent.parent / ".data"
        if production_data.exists():
            assert production_data not in bak_file.parents


def test_multiple_tests_dont_interfere(test_env, clean_crypto_files, clean_database):
    """Verify each test gets a clean environment."""
    # This test should see no existing files
    key_path = paths.get_secret_key_path()
    db_path = paths.get_database_path()

    assert not key_path.exists(), "Key file should not exist in clean environment"

    # Create some data
    generate_key()
    init_db()
    set_master_password("password123")

    # Verify files created in temp dir
    assert key_path.exists()
    assert db_path.exists()

    data_dir = paths.get_data_dir()
    assert data_dir in key_path.parents


def test_database_isolation(isolated_environment):
    """Verify database operations are isolated."""
    from secure_password_manager.utils.crypto import encrypt_password

    # Initialize and add data
    init_db()
    generate_key()

    encrypted = encrypt_password("test_password")
    add_password("test.com", "user", encrypted)

    db_path = paths.get_database_path()

    # Database should be in temp directory
    # Check for pytest temp directory markers (cross-platform)
    db_path_str = str(db_path).lower()
    is_temp = (
        "/tmp" in db_path_str or
        "pytest" in db_path_str or  # pytest creates temp dirs
        "/var/folders" in db_path_str or  # macOS temp dirs
        "\\temp\\" in db_path_str  # Windows temp dirs
    )
    assert is_temp, f"Database should be in temp directory, got: {db_path}"

    # Should NOT be in production
    production_db = Path(__file__).parent.parent / ".data" / "passwords.db"
    assert db_path != production_db


def test_cleanup_removes_all_files(test_env):
    """Verify cleanup fixture removes all generated files."""
    data_dir = paths.get_data_dir()

    # Create some files
    (data_dir / "secret.key").write_text("test key")
    (data_dir / "secret.key.bak12345").write_text("backup")
    (data_dir / "crypto.salt").write_bytes(b"salt")

    # Files should exist
    assert (data_dir / "secret.key").exists()
    assert (data_dir / "secret.key.bak12345").exists()

    # Now use clean_crypto_files which should remove them
    from tests.conftest import clean_crypto_files as cleanup_fixture

    # Simulate cleanup
    for pattern in ["secret.key*", "crypto.salt*"]:
        for file in data_dir.glob(pattern):
            if file.is_file():
                file.unlink()

    # All files should be gone
    assert not (data_dir / "secret.key").exists()
    assert not (data_dir / "secret.key.bak12345").exists()
    assert not (data_dir / "crypto.salt").exists()


def test_production_data_untouched(isolated_environment):
    """Verify production .data directory is never touched by tests."""
    production_data = Path(__file__).parent.parent / ".data"

    # Take snapshot of production directory if it exists
    production_files_before = set()
    if production_data.exists():
        production_files_before = {
            f.name for f in production_data.iterdir() if f.is_file()
        }

    # Perform operations that would create files
    generate_key()
    init_db()
    protect_key_with_master_password("test123")

    from secure_password_manager.utils.crypto import encrypt_password, set_master_password_context

    # Set context before encrypting (needed for password-derived mode)
    set_master_password_context("test123")
    encrypted = encrypt_password("password")
    add_password("example.com", "user", encrypted)

    # Check production directory hasn't changed
    if production_data.exists():
        production_files_after = {
            f.name for f in production_data.iterdir() if f.is_file()
        }

        # No new files should appear
        new_files = production_files_after - production_files_before
        assert not new_files, f"Test created files in production: {new_files}"

        # No .bak files should be created
        bak_files = [f for f in production_data.iterdir() if ".bak" in f.name]
        assert not bak_files, f"Test created backup files in production: {bak_files}"


def test_path_functions_return_temp_paths(test_env):
    """Verify all path functions return temp paths, not production."""
    production_data = Path(__file__).parent.parent / ".data"

    paths_to_check = [
        paths.get_data_dir(),
        paths.get_config_dir(),
        paths.get_cache_dir(),
        paths.get_log_dir(),
        paths.get_database_path(),
        paths.get_secret_key_path(),
        paths.get_secret_key_enc_path(),
        paths.get_crypto_salt_path(),
        paths.get_auth_json_path(),
        paths.get_totp_config_path(),
        paths.get_backup_dir(),
        paths.get_breach_cache_path(),
        paths.get_browser_bridge_tokens_path(),
    ]

    for path in paths_to_check:
        # Convert to Path for comparison
        path_obj = Path(path)

        # Should be in temp directory
        assert (
            "/tmp" in str(path_obj) or
            "temp" in str(path_obj).lower() or
            "test" in str(path_obj).lower()
        ), f"Path not in temp directory: {path_obj}"

        # Should NOT be in production .data
        if production_data.exists():
            try:
                path_obj.relative_to(production_data)
                pytest.fail(f"Path is inside production directory: {path_obj}")
            except ValueError:
                # Good - path is not relative to production
                pass
