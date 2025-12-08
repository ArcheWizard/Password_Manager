#!/usr/bin/env python3
"""
Migrate data from development mode to production XDG directories.

This script is for users who:
1. Developed/ran the app from source (with .data/ directory)
2. Want to install via pip and use XDG directories
3. Need to preserve their existing passwords

Run this BEFORE installing via pip:
    python scripts/migrate_to_production.py
    mv .data .data.backup  # Disable development mode
    pip install --upgrade secure-password-manager
"""

import shutil
from pathlib import Path


def get_project_root():
    """Find the project root (where .data/ exists)."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    return project_root


def get_production_dirs():
    """Get production XDG directory paths."""
    home = Path.home()

    data_dir = home / ".local" / "share" / "secure-password-manager"
    config_dir = home / ".config" / "secure-password-manager"
    cache_dir = home / ".cache" / "secure-password-manager"

    return data_dir, config_dir, cache_dir


def migrate_data():
    """Migrate all data from .data/ to production directories."""
    project_root = get_project_root()
    dev_data_dir = project_root / ".data"

    if not dev_data_dir.exists():
        print("❌ No .data/ directory found in project root")
        print(f"   Looked in: {project_root}")
        print("\n⚠️  If you're running from a pip install, your data should already be in XDG directories:")
        print(f"   Data:   ~/.local/share/secure-password-manager/")
        print(f"   Config: ~/.config/secure-password-manager/")
        print(f"   Cache:  ~/.cache/secure-password-manager/")
        return False

    data_dir, config_dir, cache_dir = get_production_dirs()

    # Create production directories
    print("📁 Creating production directories...")
    data_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Map of source files to destination
    migrations = [
        # Data files
        (dev_data_dir / "passwords.db", data_dir / "passwords.db"),
        (dev_data_dir / "secret.key", data_dir / "secret.key"),
        (dev_data_dir / "secret.key.enc", data_dir / "secret.key.enc"),
        (dev_data_dir / "crypto.salt", data_dir / "crypto.salt"),
        (dev_data_dir / "auth.json", data_dir / "auth.json"),
        (dev_data_dir / "totp_config.json", data_dir / "totp_config.json"),
        (dev_data_dir / "browser_bridge_tokens.json", data_dir / "browser_bridge_tokens.json"),
        (dev_data_dir / "approval_store.json", data_dir / "approval_store.json"),

        # Config files
        (dev_data_dir / "settings.json", config_dir / "settings.json"),

        # Cache files
        (dev_data_dir / "breach_cache.json", cache_dir / "breach_cache.json"),
    ]

    # Migrate logs directory
    dev_logs = dev_data_dir / "logs"
    prod_logs = data_dir / "logs"

    migrated_count = 0
    skipped_count = 0

    print("\n📦 Migrating files...")
    for src, dst in migrations:
        if src.exists():
            # Check if destination already exists
            if dst.exists():
                print(f"⚠️  Skipped (already exists): {dst.name}")
                skipped_count += 1
                continue

            # Copy file with metadata preserved
            shutil.copy2(src, dst)
            print(f"✅ Migrated: {src.name} → {dst}")
            migrated_count += 1
        else:
            print(f"ℹ️  Not found (skipping): {src.name}")

    # Migrate logs directory
    if dev_logs.exists():
        if not prod_logs.exists():
            shutil.copytree(dev_logs, prod_logs)
            print(f"✅ Migrated: logs/ → {prod_logs}")
            migrated_count += 1
        else:
            print(f"⚠️  Skipped (already exists): logs/")
            skipped_count += 1

    # Migrate backups directory
    dev_backups = dev_data_dir / "backups"
    prod_backups = data_dir / "backups"

    if dev_backups.exists():
        if not prod_backups.exists():
            shutil.copytree(dev_backups, prod_backups)
            print(f"✅ Migrated: backups/ → {prod_backups}")
            migrated_count += 1
        else:
            print(f"⚠️  Skipped (already exists): backups/")
            skipped_count += 1

    print(f"\n📊 Migration summary:")
    print(f"   Migrated: {migrated_count} items")
    print(f"   Skipped:  {skipped_count} items (already exist)")

    print(f"\n✅ Migration complete!")
    print(f"\n📂 Your data is now in:")
    print(f"   Data:   {data_dir}")
    print(f"   Config: {config_dir}")
    print(f"   Cache:  {cache_dir}")

    print(f"\n💡 Next steps:")
    print(f"   1. Verify your data works: password-manager-gui")
    print(f"   2. IMPORTANT: To enable production mode, rename the .data/ directory:")
    print(f"      mv {dev_data_dir} {dev_data_dir}.backup")
    print(f"   3. Test with pip-installed version:")
    print(f"      pip install --upgrade secure-password-manager")
    print(f"      password-manager-gui  # Should use XDG directories now")
    print(f"   4. Once verified working, you can delete:")
    print(f"      rm -rf {dev_data_dir}.backup")

    return True


if __name__ == "__main__":
    print("🔐 Secure Password Manager - Data Migration Tool")
    print("=" * 60)
    print()

    try:
        migrated = migrate_data()

        if migrated:
            print("\n" + "=" * 60)
            print("✅ SUCCESS: Data migrated to production directories")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("ℹ️  No migration needed or already completed")
            print("=" * 60)

    except Exception as e:
        print(f"\nERROR during migration: {e}")
        print("\nYour data is still safe in the .data/ directory.")
        print("Please report this issue on GitHub.")
        exit(1)