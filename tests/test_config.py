"""Tests for config module."""

import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.utils.config import (
    DEFAULT_SETTINGS,
    ensure_setting,
    get_setting,
    load_settings,
    save_settings,
    update_settings,
)


@pytest.fixture
def temp_settings_dir(tmp_path, monkeypatch):
    """Create a temporary settings directory."""
    settings_dir = tmp_path / "config"
    settings_dir.mkdir()

    # Import paths module directly
    from secure_password_manager.utils import paths

    monkeypatch.setattr(paths, "get_config_dir", lambda: settings_dir)
    return settings_dir


def test_load_settings_defaults(temp_settings_dir):
    """Test loading settings returns defaults when file doesn't exist."""
    settings = load_settings()
    assert settings == DEFAULT_SETTINGS
    assert settings["clipboard"]["auto_clear_seconds"] == 25
    assert settings["key_management"]["mode"] == "file-key"


def test_save_and_load_settings(temp_settings_dir):
    """Test saving and loading settings."""
    test_settings = {
        "clipboard": {"auto_clear_seconds": 30},
        "key_management": {"mode": "password-derived"},
    }

    saved = save_settings(test_settings)
    assert saved == test_settings

    loaded = load_settings()
    assert loaded["clipboard"]["auto_clear_seconds"] == 30
    assert loaded["key_management"]["mode"] == "password-derived"


def test_update_settings(temp_settings_dir):
    """Test updating settings with partial updates."""
    # Start with defaults
    initial = load_settings()
    assert initial["clipboard"]["auto_clear_seconds"] == 25

    # Update only clipboard settings
    updated = update_settings({"clipboard": {"auto_clear_seconds": 60}})
    assert updated["clipboard"]["auto_clear_seconds"] == 60
    assert updated["key_management"]["mode"] == "file-key"  # Unchanged

    # Verify persistence
    loaded = load_settings()
    assert loaded["clipboard"]["auto_clear_seconds"] == 60


def test_get_setting(temp_settings_dir):
    """Test retrieving nested settings."""
    save_settings(
        {
            "clipboard": {"auto_clear_seconds": 45},
            "browser_bridge": {"port": 8080},
        }
    )

    # Valid paths
    assert get_setting("clipboard.auto_clear_seconds") == 45
    assert get_setting("browser_bridge.port") == 8080

    # Non-existent path
    assert get_setting("nonexistent.setting") is None
    assert get_setting("nonexistent.setting", default=123) == 123

    # Partial path
    clipboard_settings = get_setting("clipboard")
    assert clipboard_settings == {"auto_clear_seconds": 45}


def test_ensure_setting(temp_settings_dir):
    """Test ensuring a setting value."""
    # Set a value
    result = ensure_setting("clipboard.auto_clear_seconds", 90)
    assert result == 90

    # Verify it was persisted
    loaded = load_settings()
    assert loaded["clipboard"]["auto_clear_seconds"] == 90

    # Ensure overwrites existing value
    ensure_setting("clipboard.auto_clear_seconds", 120)
    loaded = load_settings()
    assert loaded["clipboard"]["auto_clear_seconds"] == 120


def test_load_settings_corrupted_file(temp_settings_dir):
    """Test loading settings when file is corrupted."""
    settings_file = temp_settings_dir / "settings.json"
    settings_file.write_text("not valid json", encoding="utf-8")

    # Should fall back to defaults
    settings = load_settings()
    assert settings == DEFAULT_SETTINGS


def test_deep_merge_nested_dictionaries(temp_settings_dir):
    """Test deep merging of nested settings."""
    # Save initial settings
    save_settings(
        {
            "clipboard": {"auto_clear_seconds": 25, "enabled": True},
            "browser_bridge": {"port": 43110, "host": "127.0.0.1"},
        }
    )

    # Update with partial nested structure
    update_settings(
        {
            "clipboard": {"auto_clear_seconds": 50},  # Update one key
            "browser_bridge": {"port": 8080},  # Update one key
        }
    )

    loaded = load_settings()
    assert loaded["clipboard"]["auto_clear_seconds"] == 50
    assert loaded["clipboard"]["enabled"] is True  # Preserved
    assert loaded["browser_bridge"]["port"] == 8080
    assert loaded["browser_bridge"]["host"] == "127.0.0.1"  # Preserved


def test_get_setting_non_dict_cursor(temp_settings_dir):
    """Test get_setting when cursor becomes non-dict."""
    save_settings({"clipboard": {"auto_clear_seconds": 25}})

    # Try to access nested path where parent is not a dict
    assert get_setting("clipboard.auto_clear_seconds.invalid") is None


def test_ensure_setting_creates_nested_structure(temp_settings_dir):
    """Test ensure_setting creates nested dictionaries as needed."""
    # Ensure a deeply nested setting
    ensure_setting("new_feature.sub_feature.enabled", True)

    loaded = load_settings()
    assert loaded["new_feature"]["sub_feature"]["enabled"] is True
