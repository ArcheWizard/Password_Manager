#!/usr/bin/env python3
"""Cleanup script for uninstalling secure-password-manager.

This script removes user data directories (XDG) ONLY if the user has
opted in to data removal via settings. By default, user data persists
through uninstalls to prevent accidental data loss.

Usage:
    python scripts/uninstall_cleanup.py [--force]

Options:
    --force    Remove all data regardless of settings (use with caution)
"""

import argparse
import json
import shutil
import sys
from pathlib import Path


def get_xdg_dirs() -> dict:
    """Get XDG directory paths for the application."""
    home = Path.home()

    # XDG Base Directory paths
    data_home = home / ".local" / "share" / "secure-password-manager"
    config_home = home / ".config" / "secure-password-manager"
    cache_home = home / ".cache" / "secure-password-manager"

    return {
        "data": data_home,
        "config": config_home,
        "cache": cache_home,
    }


def should_remove_data() -> bool:
    """Check if user has opted in to data removal on uninstall."""
    dirs = get_xdg_dirs()
    settings_path = dirs["config"] / "settings.json"

    if not settings_path.exists():
        # No settings file means default behavior: KEEP data
        return False

    try:
        with open(settings_path, encoding="utf-8") as f:
            settings = json.load(f)

        # Check the data_persistence.remove_on_uninstall setting
        return settings.get("data_persistence", {}).get("remove_on_uninstall", False)
    except (OSError, json.JSONDecodeError):
        # On error, default to KEEP data (safer)
        return False


def remove_directory(path: Path, dir_type: str) -> None:
    """Remove a directory and report the action."""
    if not path.exists():
        print(f"✓ {dir_type} directory does not exist: {path}")
        return

    try:
        shutil.rmtree(path)
        print(f"✓ Removed {dir_type} directory: {path}")
    except OSError as e:
        print(f"✗ Failed to remove {dir_type} directory: {path}")
        print(f"  Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Cleanup user data for secure-password-manager uninstall"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force remove all data regardless of settings (use with caution)",
    )
    args = parser.parse_args()

    dirs = get_xdg_dirs()

    print("=" * 70)
    print("Secure Password Manager - Uninstall Cleanup")
    print("=" * 70)
    print()

    # Check if user wants data removed
    if args.force:
        print("⚠️  FORCE MODE: Removing all data regardless of settings")
        remove_data = True
    else:
        remove_data = should_remove_data()

        if remove_data:
            print("✓ Settings indicate data should be removed on uninstall")
        else:
            print("✓ Settings indicate data should be KEPT (default)")
            print()
            print("Your passwords and settings will remain at:")
            for dir_type, path in dirs.items():
                if path.exists():
                    print(f"  - {dir_type}: {path}")
            print()
            print("To remove data on uninstall, change this setting:")
            print("  Settings → Data Persistence → Remove data on uninstall")
            print()
            print("Or use: python scripts/uninstall_cleanup.py --force")
            return 0

    print()
    print("Removing application directories...")
    print()

    # Remove directories
    remove_directory(dirs["cache"], "Cache")
    remove_directory(dirs["config"], "Config")
    remove_directory(dirs["data"], "Data")

    print()
    print("=" * 70)
    print("Cleanup complete!")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
