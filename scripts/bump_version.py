#!/usr/bin/env python3
"""Version management script for automated releases.

This script updates version numbers across all project files:
- VERSION.txt
- src/secure_password_manager/__init__.py
- pyproject.toml
- browser-extension/manifest.json
- browser-extension/manifest-firefox.json
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Tuple


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def read_current_version() -> str:
    """Read the current version from VERSION.txt."""
    version_file = get_project_root() / "VERSION.txt"
    return version_file.read_text().strip()


def parse_version(version: str) -> Tuple[int, int, int]:
    """Parse semantic version string into (major, minor, patch)."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def format_version(major: int, minor: int, patch: int) -> str:
    """Format version tuple into string."""
    return f"{major}.{minor}.{patch}"


def bump_version(current: str, bump_type: str) -> str:
    """Bump version according to type (major, minor, patch)."""
    major, minor, patch = parse_version(current)

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

    return format_version(major, minor, patch)


def update_version_txt(new_version: str) -> None:
    """Update VERSION.txt file."""
    version_file = get_project_root() / "VERSION.txt"
    version_file.write_text(new_version + "\n")
    print(f"✅ Updated VERSION.txt to {new_version}")


def update_init_py(new_version: str) -> None:
    """Update __init__.py __version__ field."""
    init_file = get_project_root() / "src" / "secure_password_manager" / "__init__.py"
    content = init_file.read_text()

    # Replace version line
    new_content = re.sub(
        r'__version__ = "[^"]+"',
        f'__version__ = "{new_version}"',
        content
    )

    init_file.write_text(new_content)
    print(f"✅ Updated __init__.py to {new_version}")


def update_pyproject_toml(new_version: str) -> None:
    """Update pyproject.toml version field."""
    pyproject_file = get_project_root() / "pyproject.toml"
    content = pyproject_file.read_text()

    # Replace version line in [project] section
    new_content = re.sub(
        r'version = "[^"]+"',
        f'version = "{new_version}"',
        content,
        count=1
    )

    pyproject_file.write_text(new_content)
    print(f"✅ Updated pyproject.toml to {new_version}")


def update_manifest_json(new_version: str, manifest_path: Path) -> None:
    """Update browser extension manifest.json version field."""
    if not manifest_path.exists():
        print(f"⚠️  Manifest not found: {manifest_path}")
        return

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    manifest["version"] = new_version

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    print(f"✅ Updated {manifest_path.name} to {new_version}")


def update_all_manifests(new_version: str) -> None:
    """Update all browser extension manifests."""
    ext_dir = get_project_root() / "browser-extension"

    update_manifest_json(new_version, ext_dir / "manifest.json")
    update_manifest_json(new_version, ext_dir / "manifest-firefox.json")


def update_changelog(new_version: str) -> None:
    """Add new version entry to CHANGELOG.md."""
    changelog_file = get_project_root() / "CHANGELOG.md"

    if not changelog_file.exists():
        print("⚠️  CHANGELOG.md not found, skipping")
        return

    content = changelog_file.read_text()

    # Find where to insert new entry (after title)
    lines = content.split("\n")
    insert_index = 0
    for i, line in enumerate(lines):
        if line.startswith("## "):
            insert_index = i
            break

    # Create new entry
    from datetime import date
    today = date.today().strftime("%Y-%m-%d")
    new_entry = f"""## [{new_version}] - {today}

### Added

-

### Changed

-

### Fixed

-

"""

    # Insert new entry
    lines.insert(insert_index, new_entry)
    new_content = "\n".join(lines)

    changelog_file.write_text(new_content)
    print(f"✅ Added {new_version} entry to CHANGELOG.md")


def create_git_tag(new_version: str, push: bool = False) -> None:
    """Create and optionally push git tag."""
    import subprocess

    try:
        # Create annotated tag
        subprocess.run(
            ["git", "tag", "-a", f"v{new_version}", "-m", f"Release v{new_version}"],
            check=True,
            capture_output=True
        )
        print(f"✅ Created git tag v{new_version}")

        if push:
            subprocess.run(
                ["git", "push", "origin", f"v{new_version}"],
                check=True,
                capture_output=True
            )
            print(f"✅ Pushed tag v{new_version} to origin")

    except subprocess.CalledProcessError as e:
        print(f"⚠️  Git operation failed: {e.stderr.decode()}")
    except FileNotFoundError:
        print("⚠️  Git not found, skipping tag creation")


def main():
    parser = argparse.ArgumentParser(
        description="Bump version across all project files"
    )
    parser.add_argument(
        "bump_type",
        choices=["major", "minor", "patch"],
        help="Type of version bump"
    )
    parser.add_argument(
        "--new-version",
        help="Explicitly set new version (overrides bump_type)"
    )
    parser.add_argument(
        "--tag",
        action="store_true",
        help="Create git tag for new version"
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push git tag to origin (implies --tag)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes"
    )

    args = parser.parse_args()

    # Read current version
    current_version = read_current_version()
    print(f"Current version: {current_version}")

    # Determine new version
    if args.new_version:
        # Validate format
        parse_version(args.new_version)
        new_version = args.new_version
    else:
        new_version = bump_version(current_version, args.bump_type)

    print(f"New version: {new_version}")

    if args.dry_run:
        print("\n🔍 Dry run - no changes will be made")
        return 0

    # Confirm
    response = input("\nProceed with version bump? [y/N] ")
    if response.lower() != "y":
        print("❌ Cancelled")
        return 1

    print("\n📝 Updating version files...")

    # Update all files
    update_version_txt(new_version)
    update_init_py(new_version)
    update_pyproject_toml(new_version)
    update_all_manifests(new_version)
    update_changelog(new_version)

    print(f"\n✨ Version bumped from {current_version} to {new_version}")

    # Create git tag if requested
    if args.tag or args.push:
        print("\n🏷️  Creating git tag...")
        create_git_tag(new_version, push=args.push)

    print("\n📋 Next steps:")
    print("  1. Review changes: git diff")
    print("  2. Update CHANGELOG.md with release notes")
    print("  3. Commit changes: git add -A && git commit -m 'Bump version to {}'".format(new_version))
    if not args.push:
        print("  4. Create and push tag: git tag -a v{} -m 'Release v{}' && git push origin v{}".format(new_version, new_version, new_version))
    print("  5. Push changes: git push")
    print("  6. Create GitHub release from tag")

    return 0


if __name__ == "__main__":
    sys.exit(main())
