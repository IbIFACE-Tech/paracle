#!/usr/bin/env python3
"""
Version bumping script for Paracle project.

Bumps the version in:
- pyproject.toml
- packages/paracle_core/__init__.py
- All other package __init__.py files

Usage:
    python scripts/bump_version.py major|minor|patch [--dry-run]
"""

import argparse
import re
from pathlib import Path


def parse_version(version: str) -> tuple[int, int, int]:
    """Parse semantic version string into components."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")
    return tuple(map(int, match.groups()))


def bump_version(current: str, bump_type: str) -> str:
    """Bump version based on type (major, minor, patch)."""
    major, minor, patch = parse_version(current)

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")


def update_pyproject_toml(root: Path, new_version: str, dry_run: bool = False) -> None:
    """Update version in pyproject.toml."""
    pyproject_path = root / "pyproject.toml"

    if not pyproject_path.exists():
        print(f"⚠️  File not found: {pyproject_path}")
        return

    content = pyproject_path.read_text(encoding="utf-8")

    # Update version = "X.Y.Z"
    updated = re.sub(r'version\s*=\s*"[\d\.]+"', f'version = "{new_version}"', content)

    if content != updated:
        if dry_run:
            print(f"[DRY RUN] Would update {pyproject_path}")
        else:
            pyproject_path.write_text(updated, encoding="utf-8")
            print(f"✅ Updated {pyproject_path}")
    else:
        print(f"⚠️  No changes in {pyproject_path}")


def update_package_init(
    package_path: Path, new_version: str, dry_run: bool = False
) -> None:
    """Update __version__ in package __init__.py."""
    init_path = package_path / "__init__.py"

    if not init_path.exists():
        print(f"⚠️  File not found: {init_path}")
        return

    content = init_path.read_text(encoding="utf-8")

    # Update __version__ = "X.Y.Z"
    updated = re.sub(
        r'__version__\s*=\s*["\'][\d\.]+["\']',
        f'__version__ = "{new_version}"',
        content,
    )

    if content != updated:
        if dry_run:
            print(f"[DRY RUN] Would update {init_path}")
        else:
            init_path.write_text(updated, encoding="utf-8")
            print(f"✅ Updated {init_path}")
    else:
        print(f"⚠️  No changes in {init_path}")


def get_current_version(root: Path) -> str:
    """Get current version from pyproject.toml."""
    pyproject_path = root / "pyproject.toml"

    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

    content = pyproject_path.read_text(encoding="utf-8")
    match = re.search(r'version\s*=\s*"([\d\.]+)"', content)

    if not match:
        raise ValueError("Version not found in pyproject.toml")

    return match.group(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Bump version in Paracle project files"
    )
    parser.add_argument(
        "bump_type", choices=["major", "minor", "patch"], help="Type of version bump"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    # Get project root (assuming script is in scripts/)
    root = Path(__file__).parent.parent.resolve()

    try:
        # Get current version
        current_version = get_current_version(root)
        print(f"📦 Current version: {current_version}")

        # Calculate new version
        new_version = bump_version(current_version, args.bump_type)
        print(f"📦 New version: {new_version}")

        if args.dry_run:
            print("\n🔍 DRY RUN MODE - No files will be modified\n")

        # Update pyproject.toml
        update_pyproject_toml(root, new_version, args.dry_run)

        # Update all package __init__.py files
        packages_dir = root / "packages"
        if packages_dir.exists():
            for package_dir in packages_dir.iterdir():
                if package_dir.is_dir() and not package_dir.name.endswith(".egg-info"):
                    update_package_init(package_dir, new_version, args.dry_run)

        if args.dry_run:
            print("\n✅ Dry run complete. Run without --dry-run to apply changes.")
        else:
            print(f"\n✅ Version bumped: {current_version} → {new_version}")
            print("\nNext steps:")
            print("  1. Review changes: git diff")
            print(
                f"  2. Commit: git commit -am 'chore(release): bump version to {new_version}'"
            )
            print(f"  3. Tag: git tag -a v{new_version} -m 'Release v{new_version}'")
            print("  4. Push: git push origin main --tags")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
