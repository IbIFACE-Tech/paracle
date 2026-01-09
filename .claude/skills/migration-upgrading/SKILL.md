---
name: migration-upgrading
description: Handle version migrations, database schema changes, and breaking changes. Use when upgrading framework versions or migrating data.
license: Apache-2.0
compatibility: Python 3.10+, Alembic, SQLAlchemy
metadata:
  author: paracle-core-team
  version: "1.0.0"
  category: automation
  level: advanced
  display_name: "Migration & Upgrading"
  tags:
    - migration
    - upgrade
    - versioning
    - database
  capabilities:
    - version_migration
    - schema_migration
    - data_migration
    - breaking_changes
allowed-tools: Read Write Bash(python:*)
---

# Migration & Upgrading Skill

## When to use this skill

Use when:
- Upgrading Paracle framework versions
- Migrating database schema
- Handling breaking changes
- Converting old configurations
- Migrating agent specifications

## Version Migration Strategy

```markdown
# Migration Path

v0.1.x → v0.2.x → v0.3.x → v1.0.x
  ↓        ↓        ↓        ↓
  ✓        ✓        ✗        ✗  (must go through intermediate versions)
```

## Database Migrations (Alembic)

```python
# Create migration
# alembic revision --autogenerate -m "add_workflow_table"

"""add workflow table

Revision ID: abc123
Revises: def456
Create Date: 2024-01-15 10:00:00
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create table
    op.create_table(
        'workflows',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Add column to existing table
    op.add_column('agents', sa.Column('workflow_id', sa.String(), nullable=True))

    # Add index
    op.create_index('ix_agents_workflow_id', 'agents', ['workflow_id'])

    # Add foreign key
    op.create_foreign_key(
        'fk_agents_workflow_id',
        'agents', 'workflows',
        ['workflow_id'], ['id'],
    )

def downgrade():
    # Drop foreign key
    op.drop_constraint('fk_agents_workflow_id', 'agents', type_='foreignkey')

    # Drop index
    op.drop_index('ix_agents_workflow_id', 'agents')

    # Drop column
    op.drop_column('agents', 'workflow_id')

    # Drop table
    op.drop_table('workflows')
```

## Data Migration

```python
# packages/paracle_cli/commands/migrate.py
import click
from sqlalchemy import select

@click.command()
@click.option('--from-version', required=True)
@click.option('--to-version', required=True)
async def migrate_data(from_version: str, to_version: str):
    """Migrate data between versions."""

    if from_version == "0.1.0" and to_version == "0.2.0":
        await migrate_0_1_to_0_2()
    elif from_version == "0.2.0" and to_version == "0.3.0":
        await migrate_0_2_to_0_3()
    else:
        click.echo(f"No migration path from {from_version} to {to_version}")
        return

    click.echo(f"✅ Migration complete: {from_version} → {to_version}")

async def migrate_0_1_to_0_2():
    """Migrate from v0.1.0 to v0.2.0."""

    # Convert old agent format
    agents = await session.execute(select(Agent))
    for agent in agents:
        # Old format: tools as comma-separated string
        # New format: tools as JSON array
        if isinstance(agent.tools, str):
            agent.tools = agent.tools.split(',')
            session.add(agent)

    await session.commit()
```

## Configuration Migration

```python
# Migrate .parac/ files
from pathlib import Path
import yaml

def migrate_parac_config(parac_dir: Path, from_version: str, to_version: str):
    """Migrate .parac configuration."""

    # Migrate agent specs
    specs_dir = parac_dir / "agents" / "specs"
    for spec_file in specs_dir.glob("*.yaml"):
        spec = yaml.safe_load(spec_file.read_text())

        # v0.1 → v0.2: Rename 'prompt' to 'system_prompt'
        if 'prompt' in spec:
            spec['system_prompt'] = spec.pop('prompt')

        # v0.2 → v0.3: Add required 'metadata' field
        if 'metadata' not in spec:
            spec['metadata'] = {
                'version': '1.0.0',
                'author': 'user',
            }

        spec_file.write_text(yaml.dump(spec))

    # Update version
    version_file = parac_dir / "VERSION"
    version_file.write_text(to_version)
```

## Breaking Changes Handling

```python
# Deprecation warnings
import warnings

def old_function():
    warnings.warn(
        "old_function() is deprecated, use new_function() instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return new_function()

# Compatibility layer
class AgentV1:
    """Old agent interface (deprecated)."""

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "AgentV1 is deprecated, use Agent instead",
            DeprecationWarning,
        )
        self._agent = Agent(*args, **kwargs)

    def __getattr__(self, name):
        # Delegate to new implementation
        return getattr(self._agent, name)
```

## Version Compatibility Check

```python
from packaging import version

CURRENT_VERSION = "0.3.0"
MIN_SUPPORTED_VERSION = "0.2.0"

def check_compatibility(parac_dir: Path) -> bool:
    """Check if .parac is compatible."""
    version_file = parac_dir / "VERSION"

    if not version_file.exists():
        # Pre-versioning
        return False

    parac_version = version_file.read_text().strip()

    if version.parse(parac_version) < version.parse(MIN_SUPPORTED_VERSION):
        raise ValueError(
            f"Unsupported .parac version: {parac_version}\\n"
            f"Minimum supported: {MIN_SUPPORTED_VERSION}\\n"
            f"Please migrate your .parac using: paracle migrate"
        )

    return True
```

## CLI Migration Command

```bash
# Check current version
paracle version

# Check migration path
paracle migrate --check

# Perform migration
paracle migrate --from 0.2.0 --to 0.3.0

# Dry run (preview changes)
paracle migrate --from 0.2.0 --to 0.3.0 --dry-run

# Backup before migration
paracle migrate --from 0.2.0 --to 0.3.0 --backup
```

## Migration Testing

```python
def test_migration_0_1_to_0_2():
    """Test data migration."""
    # Setup old format
    agent = Agent(
        name="test",
        tools="file-read,file-write",  # Old format
    )
    session.add(agent)
    session.commit()

    # Run migration
    migrate_0_1_to_0_2()

    # Verify new format
    session.refresh(agent)
    assert isinstance(agent.tools, list)
    assert agent.tools == ["file-read", "file-write"]

def test_config_migration():
    """Test config file migration."""
    # Create old spec
    old_spec = {
        'name': 'test-agent',
        'prompt': 'You are helpful',  # Old field
    }

    # Migrate
    new_spec = migrate_spec_v1_to_v2(old_spec)

    # Verify
    assert 'system_prompt' in new_spec
    assert 'prompt' not in new_spec
    assert new_spec['system_prompt'] == 'You are helpful'
```

## CHANGELOG.md

```markdown
# Changelog

## [0.3.0] - 2024-01-15

### Added
- Workflow orchestration engine
- DAG execution support

### Changed
- **BREAKING**: Agent specs now require `metadata` field
- **BREAKING**: Tools field changed from string to array
- Improved error messages

### Deprecated
- `AgentV1` class (use `Agent` instead)
- `old_function()` (use `new_function()` instead)

### Removed
- Support for Python 3.9
- Legacy `prompt` field (use `system_prompt`)

### Migration Guide
```bash
paracle migrate --from 0.2.0 --to 0.3.0
```
```

## Best Practices

1. **Version everything** - Track .parac, database, code
2. **Test migrations** - On copy of production data
3. **Backup before migrating** - Always have rollback plan
4. **Deprecate before removing** - Give users time to adapt
5. **Document breaking changes** - Clear migration guides
6. **Provide CLI tools** - Automate migration process

## Migration Checklist

- [ ] Database schema updated (Alembic)
- [ ] Data migrated to new format
- [ ] Config files converted
- [ ] Tests updated for new version
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Migration guide written
- [ ] CLI migration command tested
- [ ] Backward compatibility layer added (if possible)
- [ ] Users notified of breaking changes

## Resources

- Alembic: https://alembic.sqlalchemy.org/
- Semantic Versioning: https://semver.org/
- Migration Scripts: `packages/paracle_cli/commands/migrate.py`
- CHANGELOG: `CHANGELOG.md`
