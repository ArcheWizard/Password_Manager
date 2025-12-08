"""Application configuration helpers.

This module centralizes reading and writing of user configuration stored in
``settings.json``. Settings follow a nested dictionary structure and are merged
with ``DEFAULT_SETTINGS`` to ensure missing keys fall back to safe defaults.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict

from secure_password_manager.utils import paths

KEY_MODE_FILE = "file-key"
KEY_MODE_PASSWORD = "password-derived"

DEFAULT_SETTINGS: Dict[str, Any] = {
    "key_management": {
        "mode": KEY_MODE_FILE,
        "kdf_iterations": 390_000,
        "benchmark_target_ms": 350,
    },
    "clipboard": {
        "auto_clear_seconds": 25,
    },
    "password_history": {
        "enabled": True,
        "max_versions": 10,
    },
    "browser_bridge": {
        "enabled": False,
        "host": "127.0.0.1",
        "port": 43110,
        "token_ttl_hours": 24,
        "pairing_window_seconds": 120,
    },
    "data_persistence": {
        "remove_on_uninstall": False,  # Keep data safe by default
        "uninstall_warning_shown": False,
    },
}


def _get_settings_path() -> Path:
    """Return the absolute path to the settings.json file."""
    return paths.get_config_dir() / "settings.json"


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge ``override`` into ``base`` (mutating and returning ``base``)."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def load_settings() -> Dict[str, Any]:
    """Load settings from disk, falling back to defaults on errors."""
    settings = copy.deepcopy(DEFAULT_SETTINGS)
    path = _get_settings_path()
    if not path.exists():
        return settings

    try:
        with open(path, encoding="utf-8") as handle:
            file_data = json.load(handle)
        if isinstance(file_data, dict):
            _deep_merge(settings, file_data)
    except (OSError, json.JSONDecodeError):
        # Fall back to defaults; corruption will be repaired on next save.
        pass
    return settings


def save_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Persist the provided settings dictionary to disk."""
    path = _get_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2, sort_keys=True)
    return settings


def update_settings(partial: Dict[str, Any]) -> Dict[str, Any]:
    """Load settings, apply ``partial`` updates, and persist the result."""
    settings = load_settings()
    _deep_merge(settings, partial)
    return save_settings(settings)


def get_setting(path_expr: str, default: Any = None) -> Any:
    """Retrieve a nested setting using dot-separated notation.

    Example::
        iterations = get_setting("key_management.kdf_iterations", 390000)
    """
    cursor: Any = load_settings()
    for segment in path_expr.split("."):
        if not isinstance(cursor, dict):
            return default
        if segment not in cursor:
            return default
        cursor = cursor[segment]
    return cursor


def ensure_setting(path_expr: str, value: Any) -> Any:
    """Ensure the given setting path equals ``value``.

    This is a convenience helper for callers that want to force a default while
    still writing the value to disk.
    """
    segments = path_expr.split(".")
    settings = load_settings()
    cursor: Dict[str, Any] = settings
    for segment in segments[:-1]:
        cursor = cursor.setdefault(segment, {})  # type: ignore[assignment]
    cursor[segments[-1]] = value
    save_settings(settings)
    return value
