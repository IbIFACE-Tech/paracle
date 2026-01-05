# Governance Improvements Plan

**Date**: 2026-01-05
**Status**: Proposed
**Priority**: P1 (High)

## Context

Following the implementation of ADR-016 (Mandatory Pre-Flight Checklist), we've identified 4 areas where governance can be strengthened further. This document outlines concrete solutions for each weakness.

---

## Weakness 1: Enforcement Validation ⚠️

### Problem
No automated verification that AI agents actually follow the pre-flight checklist or that IDE instruction files contain required sections.

### Solutions

#### Solution 1.1: CLI Validation Command
**Implementation**: Phase 4 (current phase)
**Effort**: Small (1-2 days)

```python
# packages/paracle_cli/commands/validate.py

@click.group()
def validate():
    """Validate governance compliance."""
    pass

@validate.command()
def ai_instructions():
    """Validate AI instruction files have pre-flight checklist."""
    ide_files = [
        ".cursorrules",
        ".parac/integrations/ide/.clinerules",
        ".parac/integrations/ide/.windsurfrules",
        ".parac/integrations/ide/CLAUDE.md",
        ".github/copilot-instructions.md",
    ]

    required_sections = [
        "MANDATORY PRE-FLIGHT CHECKLIST",
        "READ THIS FIRST: PRE_FLIGHT_CHECKLIST.md",
        "VALIDATE",
        "If Task NOT in Roadmap",
    ]

    missing = []
    for file in ide_files:
        if not check_sections(file, required_sections):
            missing.append(file)

    if missing:
        click.echo(f"❌ Missing checklist sections: {missing}")
        sys.exit(1)
    else:
        click.echo("✅ All AI instructions valid")

@validate.command()
def governance():
    """Validate .parac/ structure and consistency."""
    # Check required files exist
    # Check YAML syntax
    # Check current_state matches roadmap
    # Check no orphaned references
    pass
```

**Usage**:
```bash
paracle validate ai-instructions  # Check IDE configs
paracle validate governance       # Check .parac/ structure
paracle validate --all            # Check everything
```

#### Solution 1.2: Pre-commit Hook
**Implementation**: Phase 4
**Effort**: Small (1 day)

```yaml
# .pre-commit-config.yaml (CREATE THIS FILE)

repos:
  - repo: local
    hooks:
      - id: validate-ai-instructions
        name: Validate AI Instructions
        entry: uv run paracle validate ai-instructions
        language: system
        pass_filenames: false

      - id: validate-governance
        name: Validate Governance
        entry: uv run paracle validate governance
        language: system
        files: ^\.parac/
        pass_filenames: false

      - id: check-agent-logs
        name: Check Agent Actions Logged
        entry: python scripts/check_logs.py
        language: system
        pass_filenames: false
```

**Installation**:
```bash
make pre-commit-install  # Already in Makefile!
```

#### Solution 1.3: CI/CD Validation
**Implementation**: Phase 4
**Effort**: Small (1 hour)

```yaml
# .github/workflows/governance.yml (NEW FILE)

name: Governance Validation

on:
  pull_request:
    paths:
      - '.parac/**'
      - '.cursorrules'
      - '.github/copilot-instructions.md'
  push:
    branches: [main, develop]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - run: pip install uv
      - run: uv sync
      - run: uv run paracle validate --all
      - run: uv run paracle validate roadmap  # Check roadmap consistency
```

**Benefit**: PR can't merge if governance invalid

#### Solution 1.4: Automated Tests
**Implementation**: Phase 4
**Effort**: Medium (2-3 days)

```python
# tests/governance/test_ai_instructions.py (NEW TEST)

def test_all_ide_configs_have_checklist():
    """Ensure all IDE instruction files contain pre-flight checklist."""
    ide_files = [
        ".cursorrules",
        ".parac/integrations/ide/.clinerules",
        ".parac/integrations/ide/.windsurfrules",
        ".parac/integrations/ide/CLAUDE.md",
        ".github/copilot-instructions.md",
    ]

    for file_path in ide_files:
        with open(file_path) as f:
            content = f.read()

        # Check required sections
        assert "MANDATORY PRE-FLIGHT CHECKLIST" in content
        assert "PRE_FLIGHT_CHECKLIST.md" in content
        assert "VALIDATE" in content
        assert "If Task NOT in Roadmap" in content
        assert "STOP and ask user" in content

def test_current_state_matches_roadmap():
    """Ensure current_state.yaml progress matches roadmap.yaml."""
    current_state = yaml.safe_load(open(".parac/memory/context/current_state.yaml"))
    roadmap = yaml.safe_load(open(".parac/roadmap/roadmap.yaml"))

    # Check phase alignment
    assert current_state["current_phase"]["id"] == roadmap["current_phase"]

    # Check progress is reasonable
    phase = current_state["current_phase"]
    assert 0 <= phase["progress"] <= 100

def test_adr_numbering_sequential():
    """Ensure ADR numbers are sequential with no gaps."""
    with open(".parac/roadmap/decisions.md") as f:
        content = f.read()

    adr_numbers = re.findall(r"## ADR-(\d+):", content)
    adr_numbers = sorted([int(n) for n in adr_numbers])

    # Check sequential
    expected = list(range(1, len(adr_numbers) + 1))
    assert adr_numbers == expected
```

**Run**: `make test` includes these

---

## Weakness 2: Manual Logging ⚠️

### Problem
AI agents manually append to `agent_actions.log`, which is error-prone and inconsistent.

### Solutions

#### Solution 2.1: Python Logging Decorators
**Implementation**: Phase 5 (next phase)
**Effort**: Medium (3-4 days)

```python
# packages/paracle_core/governance/logging.py (ENHANCE EXISTING)

from functools import wraps
from datetime import datetime
from pathlib import Path
from typing import Optional
import inspect

class AgentActionLogger:
    """Automatic logging for agent actions."""

    def __init__(self, log_path: Path = None):
        self.log_path = log_path or Path(".parac/memory/logs/agent_actions.log")

    def log_action(
        self,
        agent: str,
        action_type: str,
        description: str,
        metadata: Optional[dict] = None
    ):
        """Log agent action with structured format."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{agent}] [{action_type}] {description}"

        if metadata:
            log_entry += f" | {metadata}"

        with open(self.log_path, "a") as f:
            f.write(log_entry + "\n")


def log_agent_action(agent: str, action_type: str):
    """Decorator to automatically log agent actions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute function
            result = func(*args, **kwargs)

            # Auto-generate description from function name and params
            func_name = func.__name__.replace("_", " ")
            description = f"{func_name}"

            # Extract file paths from args/kwargs if present
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            files = [v for v in bound.arguments.values() if isinstance(v, (str, Path)) and ("/" in str(v) or "\\" in str(v))]

            if files:
                description += f" in {', '.join(str(f) for f in files)}"

            # Log action
            logger = AgentActionLogger()
            logger.log_action(agent, action_type, description)

            return result
        return wrapper
    return decorator


# Context manager for explicit logging
class agent_context:
    """Context manager for agent actions with automatic logging."""

    def __init__(self, agent: str, action_type: str = "ACTION"):
        self.agent = agent
        self.action_type = action_type
        self.logger = AgentActionLogger()

    def __enter__(self):
        self.start_time = datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        if exc_type:
            self.logger.log_action(
                self.agent,
                "ERROR",
                f"{self.action_type} failed: {exc_val}",
                {"duration": duration}
            )
        return False

    def log(self, description: str, metadata: dict = None):
        """Log within context."""
        self.logger.log_action(self.agent, self.action_type, description, metadata)
```

**Usage**:
```python
from paracle_core.governance import log_agent_action, agent_context

# Decorator usage
@log_agent_action(agent="CoderAgent", action_type="IMPLEMENTATION")
def implement_feature(file_path: str):
    # Implementation...
    pass

# Context manager usage
with agent_context("CoderAgent", "IMPLEMENTATION") as ctx:
    implement_feature("packages/paracle_api/main.py")
    ctx.log("Added REST endpoint", {"endpoint": "/api/workflows"})
```

#### Solution 2.2: Integration with CLI/API
**Implementation**: Phase 5
**Effort**: Medium (2-3 days)

```python
# packages/paracle_cli/main.py (ENHANCE)

from paracle_core.governance import agent_context

@click.command()
@click.argument("workflow")
def run(workflow: str):
    """Run a workflow with automatic logging."""
    with agent_context("CLIAgent", "EXECUTION") as ctx:
        result = orchestrator.execute(workflow)
        ctx.log(f"Executed workflow {workflow}", {
            "status": result.status,
            "duration": result.duration
        })
```

#### Solution 2.3: Structured Logging with JSON
**Implementation**: Phase 5
**Effort**: Medium (2 days)

```python
# Enhanced logging with structured data
import json

class StructuredLogger(AgentActionLogger):
    """Logger with JSON output for machine parsing."""

    def log_action(self, agent, action_type, description, metadata=None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action_type": action_type,
            "description": description,
            "metadata": metadata or {}
        }

        # Human-readable format
        with open(self.log_path, "a") as f:
            timestamp = entry["timestamp"][:19].replace("T", " ")
            f.write(f"[{timestamp}] [{agent}] [{action_type}] {description}\n")

        # Machine-readable format
        json_path = self.log_path.parent / "agent_actions.jsonl"
        with open(json_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
```

**Benefits**:
- `.log` file for humans
- `.jsonl` file for machines/analytics

---

## Weakness 3: No Rollback ⚠️

### Problem
Decisions are immutable, but there's no easy way to revert to previous states.

### Solutions

#### Solution 3.1: State Snapshots
**Implementation**: Phase 5
**Effort**: Medium (3-4 days)

```python
# packages/paracle_core/parac/snapshots.py (NEW)

from datetime import datetime
import shutil
from pathlib import Path

class ParacSnapshot:
    """Create and restore .parac/ snapshots."""

    def __init__(self, parac_path: Path = None):
        self.parac_path = parac_path or Path(".parac")
        self.snapshots_path = self.parac_path / "memory" / "snapshots"
        self.snapshots_path.mkdir(exist_ok=True, parents=True)

    def create(self, name: str = None) -> Path:
        """Create snapshot of current .parac/ state."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_name = name or f"snapshot_{timestamp}"
        snapshot_path = self.snapshots_path / snapshot_name

        # Copy entire .parac/ (excluding snapshots dir)
        shutil.copytree(
            self.parac_path,
            snapshot_path,
            ignore=shutil.ignore_patterns("snapshots", "__pycache__", "*.pyc")
        )

        # Create manifest
        manifest = {
            "name": snapshot_name,
            "created_at": datetime.now().isoformat(),
            "phase": self._get_current_phase(),
            "commit": self._get_git_commit(),
        }

        with open(snapshot_path / "SNAPSHOT_MANIFEST.yaml", "w") as f:
            yaml.dump(manifest, f)

        return snapshot_path

    def restore(self, snapshot_name: str, backup_current: bool = True):
        """Restore .parac/ from snapshot."""
        snapshot_path = self.snapshots_path / snapshot_name

        if not snapshot_path.exists():
            raise ValueError(f"Snapshot not found: {snapshot_name}")

        # Backup current state before restoring
        if backup_current:
            self.create(f"before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

        # Clear current .parac/ (except snapshots)
        for item in self.parac_path.iterdir():
            if item.name != "memory":
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

        # Restore from snapshot
        for item in snapshot_path.iterdir():
            if item.name != "SNAPSHOT_MANIFEST.yaml":
                dest = self.parac_path / item.name
                if item.is_dir():
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)

    def list(self) -> list:
        """List all snapshots."""
        snapshots = []
        for snapshot_dir in self.snapshots_path.iterdir():
            if snapshot_dir.is_dir():
                manifest_path = snapshot_dir / "SNAPSHOT_MANIFEST.yaml"
                if manifest_path.exists():
                    with open(manifest_path) as f:
                        manifest = yaml.safe_load(f)
                    snapshots.append(manifest)
        return sorted(snapshots, key=lambda x: x["created_at"], reverse=True)
```

**CLI Commands**:
```bash
paracle snapshot create                # Auto-named snapshot
paracle snapshot create pre-refactoring # Named snapshot
paracle snapshot list                   # List all snapshots
paracle snapshot restore snapshot_20260105_143000
paracle snapshot diff snapshot_A snapshot_B  # Compare snapshots
```

#### Solution 3.2: ADR Superseding Workflow
**Implementation**: Phase 5
**Effort**: Small (1-2 days)

```python
# Enhance .parac/roadmap/decisions.md format

## ADR-016: Mandatory Pre-Flight Checklist
**Status**: Accepted
**Supersedes**: None
**Superseded By**: None

## ADR-017: Enhanced Logging System
**Status**: Accepted
**Supersedes**: None
**Superseded By**: None

## ADR-018: Revised Pre-Flight Checklist  # When reverting ADR-016
**Status**: Accepted
**Supersedes**: ADR-016
**Superseded By**: None
```

**CLI Command**:
```bash
paracle adr supersede ADR-016 "Enhanced checklist with automated validation"
# Creates new ADR, marks old one as superseded
```

#### Solution 3.3: Roadmap Versioning
**Implementation**: Phase 5
**Effort**: Small (1 day)

```yaml
# .parac/roadmap/versions/roadmap_v1.0.yaml
# .parac/roadmap/versions/roadmap_v1.1.yaml
# .parac/roadmap/versions/roadmap_v1.2.yaml

# With automatic versioning on changes
```

---

## Weakness 4: Single-Repo Limitation ⚠️

### Problem
`.parac/` works only within a single repository, no multi-repo coordination.

### Solutions

#### Solution 4.1: Workspace Federation
**Implementation**: Phase 8 (future)
**Effort**: Large (2-3 weeks)

```yaml
# .parac/federation.yaml (NEW)

federation:
  name: "my-company-workspace"
  repositories:
    - path: "../paracle-core"
      role: "framework"
      shared_agents: ["architect", "reviewer"]

    - path: "../paracle-plugins"
      role: "extensions"
      inherits_from: "../paracle-core"

    - path: "../my-app"
      role: "application"
      inherits_from: "../paracle-core"
      shared_roadmap: true

  shared:
    agents:
      - id: "architect"
        primary_repo: "../paracle-core"
        available_in: ["../paracle-plugins", "../my-app"]

    policies:
      - source: "../paracle-core/.parac/policies/CODE_STYLE.md"
        applies_to: ["../paracle-plugins", "../my-app"]

    roadmap:
      consolidation: "merge"  # Merge all roadmaps into one view
```

**CLI Commands**:
```bash
paracle federation init              # Create federation
paracle federation sync              # Sync across repos
paracle federation roadmap          # View merged roadmap
paracle federation agents list      # List all agents across repos
```

#### Solution 4.2: Shared Configuration
**Implementation**: Phase 8
**Effort**: Medium (1 week)

```yaml
# .parac/shared/config.yaml (referenced by multiple repos)

shared_policies:
  - CODE_STYLE.md
  - TESTING.md
  - SECURITY.md

shared_agents:
  - architect
  - reviewer

shared_knowledge:
  - architecture.md
  - glossary.md
```

#### Solution 4.3: Cross-Repo Agent Coordination
**Implementation**: Phase 9 (future)
**Effort**: Large (3-4 weeks)

```python
# packages/paracle_federation/coordinator.py (NEW PACKAGE)

class FederatedCoordinator:
    """Coordinate agents across multiple repositories."""

    def execute_cross_repo(self, workflow: str, repos: list[str]):
        """Execute workflow across multiple repos."""
        # 1. Validate all repos have .parac/
        # 2. Check federated permissions
        # 3. Coordinate execution order
        # 4. Aggregate results
        pass
```

---

## Implementation Priority

### Phase 4 (Current - Immediate)
**Focus**: Enforcement validation
- ✅ P0: CLI validation command (`paracle validate`)
- ✅ P0: Pre-commit hook
- ✅ P0: CI/CD validation workflow
- ✅ P1: Automated tests for governance

**Timeline**: 1 week
**Benefit**: Catch governance violations automatically

### Phase 5 (Next)
**Focus**: Automated logging + Rollback
- ✅ P0: Python logging decorators
- ✅ P1: State snapshots system
- ✅ P1: ADR superseding workflow
- ✅ P2: Structured logging (JSON)

**Timeline**: 2 weeks
**Benefit**: Reduce manual work, enable recovery

### Phase 8 (Future)
**Focus**: Multi-repo support
- ✅ P2: Workspace federation
- ✅ P2: Shared configuration
- ✅ P3: Cross-repo coordination

**Timeline**: 3-4 weeks
**Benefit**: Scale to multiple projects

---

## Success Metrics

### Enforcement Validation
- ✅ 100% of PRs validated before merge
- ✅ 0 governance violations in production
- ✅ < 5 min to detect invalid AI instructions

### Automated Logging
- ✅ 90%+ actions logged automatically
- ✅ < 10% manual logging required
- ✅ Structured logs for analytics

### Rollback Capability
- ✅ < 1 min to create snapshot
- ✅ < 5 min to restore from snapshot
- ✅ 100% state recovery success rate

### Multi-Repo Support
- ✅ Coordinate 3+ repos simultaneously
- ✅ Shared agents across repos
- ✅ Unified roadmap view

---

## Next Steps

1. **Create ADR-017** for governance improvements
2. **Update roadmap.yaml** with Phase 4 tasks
3. **Implement P0 items** (validation commands)
4. **Test validation** in CI/CD
5. **Document new commands** in CLI guide

---

**Last Updated**: 2026-01-05
**Status**: Proposal
**Requires Review**: Yes
**Estimated Total Effort**: 8-10 weeks (phased)
**ROI**: High (prevents governance drift, enables scaling)
