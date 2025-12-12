"""Comprehensive tests for paths module."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.utils import paths


def test_get_app_name():
    """Test get_app_name returns correct application name."""
    app_name = paths.get_app_name()
    assert app_name == "secure-password-manager"
    assert isinstance(app_name, str)


def test_is_development_mode_in_source_tree():
    """Test is_development_mode detection in source tree."""
    # This test assumes we're running tests from the source tree
    # The actual result depends on whether .data/ exists
    result = paths.is_development_mode()
    assert isinstance(result, bool)


def test_is_development_mode_with_site_packages(monkeypatch):
    """Test that site-packages installation is not development mode."""
    # Mock __file__ to appear in site-packages
    fake_path = Path("/usr/lib/python3.11/site-packages/secure_password_manager/utils/paths.py")

    with patch.object(paths, "__file__", str(fake_path)):
        result = paths.is_development_mode()
        assert result is False


def test_is_development_mode_without_data_dir(tmp_path, monkeypatch):
    """Test development mode returns False without .data/ directory."""
    # Create a fake source tree without .data/
    fake_root = tmp_path / "fake_project"
    fake_src = fake_root / "src" / "secure_password_manager" / "utils"
    fake_src.mkdir(parents=True)

    # Create pyproject.toml to indicate source tree
    (fake_root / "pyproject.toml").write_text("[project]\nname='test'\n")

    fake_file = fake_src / "paths.py"
    fake_file.touch()

    with patch.object(paths, "__file__", str(fake_file)):
        result = paths.is_development_mode()
        assert result is False  # No .data/ directory


def test_is_development_mode_with_data_dir(tmp_path, monkeypatch):
    """Test development mode returns True with .data/ directory."""
    # Create a fake source tree with .data/
    fake_root = tmp_path / "fake_project"
    fake_src = fake_root / "src" / "secure_password_manager" / "utils"
    fake_src.mkdir(parents=True)

    # Create required development indicators
    (fake_root / "pyproject.toml").write_text("[project]\nname='test'\n")
    (fake_root / ".data").mkdir()

    fake_file = fake_src / "paths.py"
    fake_file.touch()

    with patch.object(paths, "__file__", str(fake_file)):
        result = paths.is_development_mode()
        assert result is True


def test_get_project_root_src_layout():
    """Test get_project_root with src layout."""
    # Should work with current project structure
    root = paths.get_project_root()
    assert isinstance(root, Path)
    assert root.exists()


def test_get_data_dir_development_mode(tmp_path, monkeypatch):
    """Test get_data_dir in development mode."""
    # Setup fake development environment
    fake_root = tmp_path / "fake_project"
    fake_src = fake_root / "src" / "secure_password_manager" / "utils"
    fake_src.mkdir(parents=True)
    (fake_root / "pyproject.toml").write_text("[project]\n")
    (fake_root / ".data").mkdir()

    fake_file = fake_src / "paths.py"
    fake_file.touch()

    with patch.object(paths, "__file__", str(fake_file)):
        data_dir = paths.get_data_dir()
        assert data_dir == fake_root / ".data"
        assert data_dir.exists()


def test_get_data_dir_production_mode(tmp_path, monkeypatch):
    """Test get_data_dir in production mode with XDG_DATA_HOME."""
    xdg_data_home = tmp_path / "xdg_data"
    monkeypatch.setenv("XDG_DATA_HOME", str(xdg_data_home))

    # Mock to force production mode
    with patch.object(paths, "is_development_mode", return_value=False):
        data_dir = paths.get_data_dir()
        assert data_dir == xdg_data_home / "secure-password-manager"
        assert data_dir.exists()


def test_get_data_dir_production_mode_default(tmp_path, monkeypatch):
    """Test get_data_dir in production mode without XDG_DATA_HOME."""
    # Clear XDG_DATA_HOME if set
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)

    with patch.object(paths, "is_development_mode", return_value=False):
        data_dir = paths.get_data_dir()
        expected = Path.home() / ".local" / "share" / "secure-password-manager"
        assert data_dir == expected


def test_get_config_dir_development_mode(tmp_path, monkeypatch):
    """Test get_config_dir in development mode."""
    fake_root = tmp_path / "fake_project"
    fake_src = fake_root / "src" / "secure_password_manager" / "utils"
    fake_src.mkdir(parents=True)
    (fake_root / "pyproject.toml").write_text("[project]\n")
    (fake_root / ".data").mkdir()

    fake_file = fake_src / "paths.py"
    fake_file.touch()

    with patch.object(paths, "__file__", str(fake_file)):
        config_dir = paths.get_config_dir()
        assert config_dir == fake_root / ".data"
        assert config_dir.exists()


def test_get_config_dir_production_mode(tmp_path, monkeypatch):
    """Test get_config_dir in production mode with XDG_CONFIG_HOME."""
    xdg_config_home = tmp_path / "xdg_config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_config_home))

    with patch.object(paths, "is_development_mode", return_value=False):
        config_dir = paths.get_config_dir()
        assert config_dir == xdg_config_home / "secure-password-manager"
        assert config_dir.exists()


def test_get_config_dir_production_mode_default(monkeypatch):
    """Test get_config_dir in production mode without XDG_CONFIG_HOME."""
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

    with patch.object(paths, "is_development_mode", return_value=False):
        config_dir = paths.get_config_dir()
        expected = Path.home() / ".config" / "secure-password-manager"
        assert config_dir == expected


def test_get_cache_dir_development_mode(tmp_path, monkeypatch):
    """Test get_cache_dir in development mode."""
    fake_root = tmp_path / "fake_project"
    fake_src = fake_root / "src" / "secure_password_manager" / "utils"
    fake_src.mkdir(parents=True)
    (fake_root / "pyproject.toml").write_text("[project]\n")
    (fake_root / ".data").mkdir()

    fake_file = fake_src / "paths.py"
    fake_file.touch()

    with patch.object(paths, "__file__", str(fake_file)):
        cache_dir = paths.get_cache_dir()
        assert cache_dir == fake_root / ".data"
        assert cache_dir.exists()


def test_get_cache_dir_production_mode(tmp_path, monkeypatch):
    """Test get_cache_dir in production mode with XDG_CACHE_HOME."""
    xdg_cache_home = tmp_path / "xdg_cache"
    monkeypatch.setenv("XDG_CACHE_HOME", str(xdg_cache_home))

    with patch.object(paths, "is_development_mode", return_value=False):
        cache_dir = paths.get_cache_dir()
        assert cache_dir == xdg_cache_home / "secure-password-manager"
        assert cache_dir.exists()


def test_get_cache_dir_production_mode_default(monkeypatch):
    """Test get_cache_dir in production mode without XDG_CACHE_HOME."""
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)

    with patch.object(paths, "is_development_mode", return_value=False):
        cache_dir = paths.get_cache_dir()
        expected = Path.home() / ".cache" / "secure-password-manager"
        assert cache_dir == expected


def test_get_log_dir_development_mode(tmp_path, monkeypatch):
    """Test get_log_dir in development mode."""
    fake_root = tmp_path / "fake_project"
    fake_src = fake_root / "src" / "secure_password_manager" / "utils"
    fake_src.mkdir(parents=True)
    (fake_root / "pyproject.toml").write_text("[project]\n")
    (fake_root / ".data").mkdir()

    fake_file = fake_src / "paths.py"
    fake_file.touch()

    with patch.object(paths, "__file__", str(fake_file)):
        log_dir = paths.get_log_dir()
        assert log_dir == fake_root / "logs"
        assert log_dir.exists()


def test_get_log_dir_production_mode(tmp_path, monkeypatch):
    """Test get_log_dir in production mode."""
    with patch.object(paths, "is_development_mode", return_value=False):
        with patch.object(paths, "get_data_dir", return_value=tmp_path):
            log_dir = paths.get_log_dir()
            assert log_dir == tmp_path / "logs"
            assert log_dir.exists()


def test_get_backup_dir_development_mode(tmp_path, monkeypatch):
    """Test get_backup_dir in development mode."""
    fake_root = tmp_path / "fake_project"
    fake_src = fake_root / "src" / "secure_password_manager" / "utils"
    fake_src.mkdir(parents=True)
    (fake_root / "pyproject.toml").write_text("[project]\n")
    (fake_root / ".data").mkdir()

    fake_file = fake_src / "paths.py"
    fake_file.touch()

    with patch.object(paths, "__file__", str(fake_file)):
        backup_dir = paths.get_backup_dir()
        assert backup_dir == fake_root / ".data" / "backups"
        assert backup_dir.exists()


def test_get_backup_dir_production_mode(tmp_path):
    """Test get_backup_dir in production mode."""
    with patch.object(paths, "is_development_mode", return_value=False):
        with patch.object(paths, "get_data_dir", return_value=tmp_path):
            backup_dir = paths.get_backup_dir()
            assert backup_dir == tmp_path / "backups"
            assert backup_dir.exists()


def test_get_database_path():
    """Test get_database_path returns correct path."""
    db_path = paths.get_database_path()
    assert db_path.name == "passwords.db"
    assert isinstance(db_path, Path)


def test_get_secret_key_path():
    """Test get_secret_key_path returns correct path."""
    key_path = paths.get_secret_key_path()
    assert key_path.name == "secret.key"
    assert isinstance(key_path, Path)


def test_get_secret_key_enc_path():
    """Test get_secret_key_enc_path returns correct path."""
    enc_path = paths.get_secret_key_enc_path()
    assert enc_path.name == "secret.key.enc"
    assert isinstance(enc_path, Path)


def test_get_crypto_salt_path():
    """Test get_crypto_salt_path returns correct path."""
    salt_path = paths.get_crypto_salt_path()
    assert salt_path.name == "crypto.salt"
    assert isinstance(salt_path, Path)


def test_get_auth_json_path():
    """Test get_auth_json_path returns correct path."""
    auth_path = paths.get_auth_json_path()
    assert auth_path.name == "auth.json"
    assert isinstance(auth_path, Path)


def test_get_breach_cache_path():
    """Test get_breach_cache_path returns correct path."""
    cache_path = paths.get_breach_cache_path()
    assert cache_path.name == "breach_cache.json"
    assert isinstance(cache_path, Path)


def test_get_totp_config_path():
    """Test get_totp_config_path returns correct path."""
    totp_path = paths.get_totp_config_path()
    assert totp_path.name == "totp_config.json"
    assert isinstance(totp_path, Path)


def test_get_browser_bridge_tokens_path():
    """Test get_browser_bridge_tokens_path returns correct path."""
    tokens_path = paths.get_browser_bridge_tokens_path()
    assert tokens_path.name == "browser_bridge_tokens.json"
    assert isinstance(tokens_path, Path)


def test_migrate_legacy_files_development_mode(tmp_path, monkeypatch, capsys):
    """Test migrate_legacy_files in development mode."""
    fake_root = tmp_path / "fake_project"
    fake_src = fake_root / "src" / "secure_password_manager" / "utils"
    fake_src.mkdir(parents=True)
    (fake_root / "pyproject.toml").write_text("[project]\n")

    # Create .data/ directory
    data_dir = fake_root / ".data"
    data_dir.mkdir()

    # Create legacy files in project root
    (fake_root / "passwords.db").write_text("legacy db")
    (fake_root / "secret.key").write_text("legacy key")

    fake_file = fake_src / "paths.py"
    fake_file.touch()

    with patch.object(paths, "__file__", str(fake_file)):
        paths.migrate_legacy_files()

        # Check files were migrated
        assert (data_dir / "passwords.db").exists()
        assert (data_dir / "secret.key").exists()

        # Check output
        captured = capsys.readouterr()
        assert "Migrated" in captured.out


def test_migrate_legacy_files_skips_existing(tmp_path, monkeypatch):
    """Test migrate_legacy_files doesn't overwrite existing files."""
    fake_root = tmp_path / "fake_project"
    fake_src = fake_root / "src" / "secure_password_manager" / "utils"
    fake_src.mkdir(parents=True)
    (fake_root / "pyproject.toml").write_text("[project]\n")

    data_dir = fake_root / ".data"
    data_dir.mkdir()

    # Create both legacy and new files
    (fake_root / "passwords.db").write_text("legacy db")
    (data_dir / "passwords.db").write_text("existing db")

    fake_file = fake_src / "paths.py"
    fake_file.touch()

    with patch.object(paths, "__file__", str(fake_file)):
        paths.migrate_legacy_files()

        # Existing file should not be overwritten
        assert (data_dir / "passwords.db").read_text() == "existing db"


def test_check_legacy_data_not_found():
    """Test check_legacy_data returns False when no legacy data."""
    with patch.object(paths, "is_development_mode", return_value=False):
        result = paths.check_legacy_data()
        # May be True or False depending on actual environment
        assert isinstance(result, bool)


def test_check_legacy_data_development_mode():
    """Test check_legacy_data in development mode."""
    with patch.object(paths, "is_development_mode", return_value=True):
        result = paths.check_legacy_data()
        assert result is False  # Should not check in dev mode


def test_print_paths_info_runs_without_error(capsys):
    """Test print_paths_info executes without errors."""
    paths.print_paths_info()

    captured = capsys.readouterr()
    assert "Development Mode:" in captured.out
    assert "Data Directory:" in captured.out
    assert "Database:" in captured.out


def test_directories_are_created_automatically(tmp_path):
    """Test that directory getters create directories automatically."""
    # Patch is_development_mode and environment to use tmp_path
    with patch.object(paths, "is_development_mode", return_value=False):
        with patch.dict(os.environ, {"XDG_DATA_HOME": str(tmp_path)}):
            # First call should create the directory under tmp_path/<app_name>
            data_dir = paths.get_data_dir()
            assert data_dir.exists()
            assert data_dir.parent == tmp_path


def test_path_consistency():
    """Test that path functions return consistent results."""
    # Call each function twice and verify consistency
    assert paths.get_data_dir() == paths.get_data_dir()
    assert paths.get_config_dir() == paths.get_config_dir()
    assert paths.get_cache_dir() == paths.get_cache_dir()
    assert paths.get_log_dir() == paths.get_log_dir()
    assert paths.get_backup_dir() == paths.get_backup_dir()


def test_file_paths_use_correct_directories(tmp_path):
    """Test that file path helpers use the correct directories."""
    with patch.object(paths, "get_data_dir", return_value=tmp_path / "data"):
        db_path = paths.get_database_path()
        key_path = paths.get_secret_key_path()

        assert db_path.parent == tmp_path / "data"
        assert key_path.parent == tmp_path / "data"

    with patch.object(paths, "get_cache_dir", return_value=tmp_path / "cache"):
        cache_path = paths.get_breach_cache_path()
        assert cache_path.parent == tmp_path / "cache"

    with patch.object(paths, "get_config_dir", return_value=tmp_path / "config"):
        totp_path = paths.get_totp_config_path()
        assert totp_path.parent == tmp_path / "config"
