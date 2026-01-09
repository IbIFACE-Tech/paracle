#!/usr/bin/env python3
"""Migrate agent specs between versions.

Usage:
    python migrate_agent_specs.py --from 0.1.0 --to 0.2.0 .parac/agents/specs/
"""

import argparse
from pathlib import Path
from typing import Any

import yaml


def migrate_0_1_to_0_2(spec: dict[str, Any]) -> dict[str, Any]:
    """Migrate from v0.1.0 to v0.2.0."""

    # Rename 'prompt' to 'system_prompt'
    if 'prompt' in spec:
        spec['system_prompt'] = spec.pop('prompt')

    # Convert tools from string to list
    if 'tools' in spec and isinstance(spec['tools'], str):
        spec['tools'] = [t.strip() for t in spec['tools'].split(',')]

    return spec


def migrate_0_2_to_0_3(spec: dict[str, Any]) -> dict[str, Any]:
    """Migrate from v0.2.0 to v0.3.0."""

    # Add required metadata field
    if 'metadata' not in spec:
        spec['metadata'] = {
            'version': '1.0.0',
            'author': 'user',
        }

    return spec


MIGRATIONS = {
    ('0.1.0', '0.2.0'): migrate_0_1_to_0_2,
    ('0.2.0', '0.3.0'): migrate_0_2_to_0_3,
}


def migrate_spec_file(file_path: Path, from_version: str, to_version: str):
    """Migrate a single spec file."""

    migration_key = (from_version, to_version)
    if migration_key not in MIGRATIONS:
        print(
            f"⚠️  No migration available from {from_version} to {to_version}")
        return False

    print(f"📝 Migrating {file_path.name}")

    # Load spec
    with open(file_path) as f:
        spec = yaml.safe_load(f)

    # Apply migration
    migrator = MIGRATIONS[migration_key]
    spec = migrator(spec)

    # Save migrated spec
    with open(file_path, 'w') as f:
        yaml.dump(spec, f, default_flow_style=False, sort_keys=False)

    print(f"  ✓ Migrated to v{to_version}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Migrate agent specifications")
    parser.add_argument("--from", dest="from_version",
                        required=True, help="Source version")
    parser.add_argument("--to", dest="to_version",
                        required=True, help="Target version")
    parser.add_argument("path", help="Path to specs directory")

    args = parser.parse_args()

    specs_dir = Path(args.path)
    if not specs_dir.is_dir():
        print(f"❌ Directory not found: {specs_dir}")
        return 1

    print(
        f"\n🔄 Migrating specs from v{args.from_version} to v{args.to_version}\n")

    # Migrate all YAML files
    migrated = 0
    for spec_file in specs_dir.glob("*.yaml"):
        if migrate_spec_file(spec_file, args.from_version, args.to_version):
            migrated += 1

    print(f"\n✅ Migrated {migrated} spec file(s)")
    return 0


if __name__ == "__main__":
    exit(main())
