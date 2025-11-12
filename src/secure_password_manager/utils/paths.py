"""
Path management utilities following XDG Base Directory Specification.

This module provides functions to get appropriate directories for:
- User data (passwords.db, secret.key, etc.)
- Configuration (settings, preferences)
- Cache (breach_cache.json, temp files)

Falls back to project root .data/ directory in development mode.
"""

import os
from pathlib import Path


def get_app_name() -> str:
    """Get the application name for directory paths."""
    return "secure-password-manager"


def is_development_mode() -> bool:
    """
    Check if running in development mode.

    Returns True if:
    - Running from source (apps/ and utils/ exist in parent dir)
    - .data/ directory exists in project root
    """
    # Get the project root
    # When in src layout: src/secure_password_manager/utils/paths.py -> ../../.. = project root
    # When in old layout: utils/paths.py -> .. = project root
    utils_dir = Path(__file__).parent

    # Try src layout first
    if utils_dir.parent.name == "secure_password_manager":
        project_root = utils_dir.parent.parent.parent
    else:
        # Old layout
        project_root = utils_dir.parent

    # Check if we're in the source tree
    data_dir = project_root / ".data"
    src_dir = project_root / "src"

    # Development mode if .data exists and we have src/ or old apps/utils structure
    return data_dir.exists() and (src_dir.exists() or (project_root / "apps").exists())


def get_project_root() -> Path:
    """Get the project root directory."""
    utils_dir = Path(__file__).parent

    # Try src layout first
    if utils_dir.parent.name == "secure_password_manager":
        return utils_dir.parent.parent.parent
    else:
        # Old layout
        return utils_dir.parent


def get_data_dir() -> Path:
    """
    Get the directory for user data files.

    In production: ~/.local/share/secure-password-manager/
    In development: <project-root>/.data/

    Stores: passwords.db, secret.key, crypto.salt, auth.json
    """
    if is_development_mode():
        data_dir = get_project_root() / ".data"
    else:
        # Follow XDG Base Directory Specification
        xdg_data_home = os.environ.get("XDG_DATA_HOME")
        if xdg_data_home:
            data_dir = Path(xdg_data_home) / get_app_name()
        else:
            data_dir = Path.home() / ".local" / "share" / get_app_name()

    # Create directory if it doesn't exist
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_config_dir() -> Path:
    """
    Get the directory for configuration files.

    In production: ~/.config/secure-password-manager/
    In development: <project-root>/.data/

    Stores: settings.json, preferences, etc.
    """
    if is_development_mode():
        config_dir = get_project_root() / ".data"
    else:
        # Follow XDG Base Directory Specification
        xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config_home:
            config_dir = Path(xdg_config_home) / get_app_name()
        else:
            config_dir = Path.home() / ".config" / get_app_name()

    # Create directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_cache_dir() -> Path:
    """
    Get the directory for cache files.

    In production: ~/.cache/secure-password-manager/
    In development: <project-root>/.data/

    Stores: breach_cache.json, temporary files
    """
    if is_development_mode():
        cache_dir = get_project_root() / ".data"
    else:
        # Follow XDG Base Directory Specification
        xdg_cache_home = os.environ.get("XDG_CACHE_HOME")
        if xdg_cache_home:
            cache_dir = Path(xdg_cache_home) / get_app_name()
        else:
            cache_dir = Path.home() / ".cache" / get_app_name()

    # Create directory if it doesn't exist
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_log_dir() -> Path:
    """
    Get the directory for log files.

    In production: ~/.local/share/secure-password-manager/logs/
    In development: <project-root>/logs/
    """
    if is_development_mode():
        log_dir = get_project_root() / "logs"
    else:
        log_dir = get_data_dir() / "logs"

    # Create directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_backup_dir() -> Path:
    """
    Get the directory for backup files.

    In production: ~/.local/share/secure-password-manager/backups/
    In development: <project-root>/.data/backups/
    """
    if is_development_mode():
        backup_dir = get_project_root() / ".data" / "backups"
    else:
        backup_dir = get_data_dir() / "backups"

    # Create directory if it doesn't exist
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


# File path helpers
def get_database_path() -> Path:
    """Get the path to the passwords database."""
    return get_data_dir() / "passwords.db"


def get_secret_key_path() -> Path:
    """Get the path to the secret key file."""
    return get_data_dir() / "secret.key"


def get_secret_key_enc_path() -> Path:
    """Get the path to the encrypted secret key file."""
    return get_data_dir() / "secret.key.enc"


def get_crypto_salt_path() -> Path:
    """Get the path to the crypto salt file."""
    return get_data_dir() / "crypto.salt"


def get_auth_json_path() -> Path:
    """Get the path to the authentication file."""
    return get_data_dir() / "auth.json"


def get_breach_cache_path() -> Path:
    """Get the path to the breach cache file."""
    return get_cache_dir() / "breach_cache.json"


def get_totp_config_path() -> Path:
    """Get the path to the TOTP configuration file."""
    return get_config_dir() / "totp_config.json"


def migrate_legacy_files() -> None:
    """
    Migrate files from project root to proper directories.

    This function should be called on first run to move existing
    user data files from the old location (project root) to the
    new XDG-compliant locations.
    """
    if is_development_mode():
        # In dev mode, files should stay in .data/
        project_root = get_project_root()
        data_dir = get_data_dir()
        cache_dir = get_cache_dir()

        # Map of old paths to new paths
        migrations = [
            (project_root / "passwords.db", data_dir / "passwords.db"),
            (project_root / "secret.key", data_dir / "secret.key"),
            (project_root / "secret.key.enc", data_dir / "secret.key.enc"),
            (project_root / "crypto.salt", data_dir / "crypto.salt"),
            (project_root / "auth.json", data_dir / "auth.json"),
            (project_root / "breach_cache.json", cache_dir / "breach_cache.json"),
            (project_root / "totp_config.json", data_dir / "totp_config.json"),
        ]

        for old_path, new_path in migrations:
            if old_path.exists() and not new_path.exists():
                try:
                    old_path.rename(new_path)
                    print(f"✓ Migrated {old_path.name} to {new_path.parent}")
                except Exception as e:
                    print(f"⚠ Warning: Could not migrate {old_path.name}: {e}")


def print_paths_info() -> None:
    """Print information about configured paths (useful for debugging)."""
    print(f"Development Mode: {is_development_mode()}")
    print(f"Data Directory:   {get_data_dir()}")
    print(f"Config Directory: {get_config_dir()}")
    print(f"Cache Directory:  {get_cache_dir()}")
    print(f"Log Directory:    {get_log_dir()}")
    print(f"Backup Directory: {get_backup_dir()}")
    print()
    print(f"Database:         {get_database_path()}")
    print(f"Secret Key:       {get_secret_key_path()}")
    print(f"Auth File:        {get_auth_json_path()}")
