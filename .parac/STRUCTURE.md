# .parac Folder Structure

> **Purpose**: Define the canonical structure and file placement rules for `.parac/` workspaces.

## Overview

The `.parac/` directory is the **single source of truth** for Paracle projects. Every file has a specific location based on its purpose and lifecycle.

## Directory Structure

```
.parac/
├── agents/              # Agent definitions and specifications
│   ├── specs/          # Agent specification files (*.md)
│   ├── skills/         # Agent skills (YAML + SKILL.md)
│   └── manifest.yaml   # Agent registry (AUTO-GENERATED)
│
├── workflows/          # Workflow definitions
│   ├── *.yaml         # Workflow specifications
│   └── README.md      # Workflow documentation
│
├── tools/             # Custom tool definitions
│   ├── *.yaml        # Tool specifications
│   └── README.md     # Tool documentation
│
├── adapters/          # Framework adapters
│   └── *.yaml        # Adapter configurations
│
├── integrations/      # External integrations
│   └── *.yaml        # Integration configurations
│
├── memory/            # Project memory and operational data
│   ├── context/      # Current project context
│   │   ├── current_state.yaml    # Current project state
│   │   └── open_questions.md     # Unresolved questions
│   │
│   ├── logs/         # Operational logs
│   │   ├── agent_actions.log     # Agent activity log
│   │   └── decisions.log         # Decision history
│   │
│   ├── knowledge/    # Knowledge base
│   │   ├── architecture.md       # Architecture knowledge
│   │   ├── glossary.md          # Terms and definitions
│   │   └── *.md                 # Topic-specific knowledge
│   │
│   ├── summaries/    # Periodic summaries
│   │   ├── weekly_*.md          # Weekly summaries
│   │   └── phase_*.md           # Phase completion summaries
│   │
│   └── data/         # Operational databases and data files
│       ├── costs.db             # Cost tracking database
│       ├── metrics.db           # Performance metrics
│       └── *.db                 # Other operational databases
│
├── roadmap/           # Planning and roadmap
│   ├── roadmap.yaml             # Master roadmap
│   ├── decisions.md             # Architecture Decision Records (ADRs)
│   └── phase_planning/          # Phase-specific planning
│       ├── PHASE*_*.md         # Phase progress reports
│       └── baseline_*.json     # Performance baselines
│
├── policies/          # Governance policies
│   ├── CODE_STYLE.md           # Code style guide
│   ├── TESTING.md              # Testing policy
│   ├── SECURITY.md             # Security policy
│   ├── policy-pack.yaml        # Policy definitions
│   └── security.yaml           # Security configurations
│
├── config/            # Configuration files
│   └── *.yaml        # Various configurations
│
├── runs/              # Execution artifacts (gitignored)
│   ├── agents/       # Agent execution logs
│   ├── workflows/    # Workflow execution logs
│   └── artifacts/    # Generated artifacts
│
├── project.yaml       # Manual project configuration
├── manifest.yaml      # AUTO-GENERATED workspace state
├── changelog.md       # Project changelog
├── GOVERNANCE.md      # Governance protocol
└── .gitignore        # Git ignore patterns

```

## File Placement Rules

### 1. Configuration Files

**Location**: `.parac/` root or `.parac/config/`

**Rules**:
- `project.yaml` - **ROOT** - User-editable project configuration
- `manifest.yaml` - **ROOT** - Auto-generated, DO NOT EDIT manually
- Other configs - `.parac/config/*.yaml`

**Example**:
```yaml
# ✅ Correct
.parac/project.yaml
.parac/manifest.yaml
.parac/config/custom_settings.yaml

# ❌ Wrong
.parac/agents/config.yaml
.parac/my-config.yaml
```

### 2. Operational Data

**Location**: `.parac/memory/data/`

**Rules**:
- **All databases** → `.parac/memory/data/*.db`
- **Metrics files** → `.parac/memory/data/metrics.*`
- **Cache files** → `.parac/memory/data/cache/`
- **Never in .parac root**

**Example**:
```bash
# ✅ Correct
.parac/memory/data/costs.db
.parac/memory/data/metrics.db
.parac/memory/data/cache/responses.json

# ❌ Wrong
.parac/costs.db                    # Not in root!
.parac/memory/costs.db             # Not in memory root!
packages/paracle_core/costs.db     # Not in code!
```

### 3. Logs

**Location**: `.parac/memory/logs/`

**Rules**:
- **Activity logs** → `.parac/memory/logs/*.log`
- **Decision logs** → `.parac/memory/logs/decisions.log`
- **Never in code directories**

**Example**:
```bash
# ✅ Correct
.parac/memory/logs/agent_actions.log
.parac/memory/logs/decisions.log
.parac/memory/logs/errors.log

# ❌ Wrong
.parac/logs/agent.log              # Not directly under .parac
packages/logs/app.log              # Not in code!
logs/paracle.log                   # Not in project root!
```

### 4. Documentation

**Location**: Depends on type

**Rules**:
- **Governance docs** → `.parac/*.md` (GOVERNANCE.md, etc.)
- **Knowledge base** → `.parac/memory/knowledge/*.md`
- **Summaries** → `.parac/memory/summaries/*.md`
- **Decisions (ADRs)** → `.parac/roadmap/decisions.md`
- **User-facing docs** → `content/docs/` (NOT in .parac/)
- **Examples** → `content/examples/` (NOT in .parac/)
- **Templates** → `content/templates/` (NOT in .parac/)

**Example**:
```bash
# ✅ Correct
.parac/GOVERNANCE.md                     # Governance
.parac/memory/knowledge/api.md           # Technical knowledge
.parac/memory/summaries/week1.md         # Summary
content/docs/getting-started.md          # User docs
content/examples/01_basic_agent.py       # Code examples
content/templates/.parac-template/       # Project templates

# ❌ Wrong
.parac/api-docs.md                       # Should be in memory/knowledge/
.parac/decisions.md                      # Should be in roadmap/
.parac/docs/                             # Belongs in content/docs/
docs/getting-started.md                  # Should be in content/docs/
examples/demo.py                         # Should be in content/examples/
templates/                               # Should be in content/templates/
```

### 5. Agent Definitions

**Location**: `.parac/agents/`

**Rules**:
- **Agent specs** → `.parac/agents/specs/*.md`
- **Agent skills** → `.parac/agents/skills/*.{yaml,md}`
- **Agent manifest** → `.parac/agents/manifest.yaml` (AUTO-GENERATED)

### 6. Execution Artifacts

**Location**: `.parac/runs/` (gitignored)

**Rules**:
- **Agent runs** → `.parac/runs/agents/<agent_id>/<run_id>/`
- **Workflow runs** → `.parac/runs/workflows/<workflow_id>/<run_id>/`
- **Always gitignored**

## Validation Checklist

Use this checklist when adding new files:

- [ ] **Is it operational data?** → `.parac/memory/data/`
- [ ] **Is it a log file?** → `.parac/memory/logs/`
- [ ] **Is it project knowledge?** → `.parac/memory/knowledge/`
- [ ] **Is it a decision record?** → `.parac/roadmap/decisions.md`
- [ ] **Is it user-facing documentation?** → `content/docs/`
- [ ] **Is it a code example?** → `content/examples/`
- [ ] **Is it a project template?** → `content/templates/`
- [ ] **Is it an agent definition?** → `.parac/agents/specs/`
- [ ] **Is it a workflow?** → `.parac/workflows/`
- [ ] **Is it a policy?** → `.parac/policies/`
- [ ] **Is it configuration?** → `.parac/config/`
- [ ] **Is it execution output?** → `.parac/runs/` (+ .gitignore)

## Common Mistakes

### ❌ Database in Wrong Location

```python
# WRONG - Database in .parac root
db_path = parac_dir / "costs.db"

# CORRECT - Database in memory/data
db_path = parac_dir / "memory" / "data" / "costs.db"
```

### ❌ Logs in Code Directory

```python
# WRONG - Logs in packages
log_file = "packages/paracle_core/debug.log"

# CORRECT - Logs in .parac/memory/logs
log_file = ".parac/memory/logs/debug.log"
```

### ❌ Config Files Scattered

```bash
# WRONG - Multiple config locations
.parac/my_config.yaml
.parac/agents/agent_config.yaml
config/settings.yaml

# CORRECT - Centralized configuration
.parac/project.yaml          # Main config
.parac/config/settings.yaml  # Additional configs
```

## Code Guidelines

### When Creating New Data Files

```python
from pathlib import Path

def get_data_path(filename: str) -> Path:
    """Get path for operational data files.

    Args:
        filename: Name of data file (e.g., 'costs.db', 'metrics.json')

    Returns:
        Path in .parac/memory/data/
    """
    parac_dir = find_parac_root()
    data_dir = parac_dir / "memory" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / filename

# Usage
db_path = get_data_path("costs.db")  # → .parac/memory/data/costs.db
```

### When Creating New Log Files

```python
def get_log_path(log_name: str) -> Path:
    """Get path for log files.

    Args:
        log_name: Name of log file (e.g., 'agent_actions.log')

    Returns:
        Path in .parac/memory/logs/
    """
    parac_dir = find_parac_root()
    logs_dir = parac_dir / "memory" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir / log_name

# Usage
log_path = get_log_path("agent_actions.log")  # → .parac/memory/logs/agent_actions.log
```

## Automated Validation

### CLI Validation Command

```bash
# Validate .parac structure
paracle validate structure

# Check for files in wrong locations
paracle validate structure --strict

# Fix common issues automatically
paracle validate structure --fix
```

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: validate-parac-structure
      name: Validate .parac structure
      entry: paracle validate structure
      language: system
      pass_filenames: false
```

## Migration Guide

If you have files in wrong locations:

```bash
# Check for misplaced files
paracle validate structure

# See what would be moved
paracle validate structure --dry-run

# Move files to correct locations
paracle validate structure --fix

# Update code references
grep -r "\.parac/costs\.db" packages/
# Then update to: .parac/memory/data/costs.db
```

## See Also

- [GOVERNANCE.md](GOVERNANCE.md) - Governance protocol
- [project.yaml](project.yaml) - Project configuration
- [manifest.yaml](manifest.yaml) - Workspace state (auto-generated)

---

**Last Updated**: 2026-01-07
**Version**: 1.0
**Status**: Active
