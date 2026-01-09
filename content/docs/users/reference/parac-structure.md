# .parac/ Folder Structure Reference

Complete reference for the `.parac/` workspace directory structure.

## Overview

The `.parac/` directory is the **single source of truth** for Paracle projects. It contains all agent definitions, workflows, configuration, and operational data.

## Directory Structure

```
.parac/
├── project.yaml           # Project configuration (user-editable)
├── manifest.yaml          # Workspace state (auto-generated)
├── changelog.md           # Project changelog
├── GOVERNANCE.md          # Governance protocol
├── .gitignore             # Git ignore patterns
│
├── agents/                # Agent definitions
│   ├── specs/            # Agent specifications (*.md)
│   │   ├── coder.md
│   │   ├── reviewer.md
│   │   ├── SCHEMA.md     # Schema reference
│   │   └── TEMPLATE.md   # Agent template
│   ├── skills/           # Agent skills
│   │   └── my-skill/
│   │       ├── skill.yaml
│   │       └── SKILL.md
│   ├── manifest.yaml     # Agent registry (auto-generated)
│   └── SKILL_ASSIGNMENTS.md
│
├── workflows/             # Workflow definitions
│   ├── *.yaml            # Workflow specifications
│   └── README.md
│
├── tools/                 # Custom tools
│   ├── registry.yaml     # Tool registry
│   ├── builtin/          # Built-in tools
│   ├── custom/           # Custom tool definitions
│   └── hooks/            # Tool hooks
│
├── policies/              # Governance policies
│   ├── CODE_STYLE.md     # Code style guide
│   ├── TESTING.md        # Testing policy
│   ├── SECURITY.md       # Security policy
│   ├── policy-pack.yaml  # Policy definitions
│   └── security.yaml     # Security configs
│
├── memory/                # Project memory
│   ├── context/          # Current context
│   │   ├── current_state.yaml
│   │   └── open_questions.md
│   ├── logs/             # Operational logs
│   │   ├── agent_actions.log
│   │   └── decisions.log
│   ├── knowledge/        # Knowledge base
│   │   ├── architecture.md
│   │   ├── glossary.md
│   │   └── *.md
│   ├── summaries/        # Periodic summaries
│   │   └── *.md
│   └── data/             # Operational databases
│       ├── costs.db
│       ├── metrics.db
│       └── *.db
│
├── roadmap/               # Planning
│   ├── roadmap.yaml      # Master roadmap
│   ├── decisions.md      # ADRs
│   ├── adr/              # ADR directory
│   │   └── ADR-*.md
│   └── constraints.yaml
│
├── config/                # Configuration files
│   └── *.yaml
│
├── integrations/          # External integrations
│   └── ide/              # IDE configurations
│       └── _manifest.yaml
│
├── adapters/              # Framework adapters
│   └── *.yaml
│
└── runs/                  # Execution artifacts (gitignored)
    ├── agents/           # Agent execution logs
    ├── workflows/        # Workflow execution logs
    └── artifacts/        # Generated artifacts
```

## Key Files

### Configuration Files

| File | Purpose | Editable |
|------|---------|----------|
| `project.yaml` | Project configuration | Yes |
| `manifest.yaml` | Workspace state | No (auto-generated) |
| `changelog.md` | Project changelog | Yes |
| `GOVERNANCE.md` | Governance rules | Yes |

### Agent Files

| File | Purpose |
|------|---------|
| `agents/specs/*.md` | Agent specifications |
| `agents/manifest.yaml` | Agent registry (auto-generated) |
| `agents/skills/*/skill.yaml` | Skill definitions |
| `agents/SKILL_ASSIGNMENTS.md` | Skill-to-agent mapping |

### Memory Files

| File | Purpose |
|------|---------|
| `memory/context/current_state.yaml` | Current project state |
| `memory/context/open_questions.md` | Unresolved questions |
| `memory/logs/agent_actions.log` | Agent activity log |
| `memory/logs/decisions.log` | Decision history |
| `memory/knowledge/*.md` | Project knowledge base |
| `memory/data/*.db` | Operational databases |

### Planning Files

| File | Purpose |
|------|---------|
| `roadmap/roadmap.yaml` | Master roadmap |
| `roadmap/decisions.md` | Architecture Decision Records |
| `roadmap/constraints.yaml` | Project constraints |

## File Placement Rules

### Rule 1: Operational Data

All databases and data files go in `.parac/memory/data/`:

```bash
# Correct
.parac/memory/data/costs.db
.parac/memory/data/metrics.json

# Wrong
.parac/costs.db
packages/data/costs.db
```

### Rule 2: Logs

All log files go in `.parac/memory/logs/`:

```bash
# Correct
.parac/memory/logs/agent_actions.log
.parac/memory/logs/errors.log

# Wrong
.parac/logs/agent.log
logs/paracle.log
```

### Rule 3: Agent Definitions

Agent specs in `.parac/agents/specs/`, skills in `.parac/agents/skills/`:

```bash
# Correct
.parac/agents/specs/coder.md
.parac/agents/skills/code-review/skill.yaml

# Wrong
.parac/coder.yaml
agents/coder.md
```

### Rule 4: Execution Artifacts

Execution outputs go in `.parac/runs/` (always gitignored):

```bash
# Correct
.parac/runs/agents/coder/run_123/output.json
.parac/runs/workflows/deploy/run_456/result.json

# These are automatically gitignored
```

## Initialization

Create the `.parac/` structure with:

```bash
# Basic workspace
paracle init

# With template
paracle init --template standard

# Interactive mode
paracle init -i
```

## Validation

Validate the structure with:

```bash
# Check structure
paracle validate governance

# Check all
paracle validate --all

# Fix issues
paracle validate structure --fix
```

## Synchronization

Keep `.parac/` in sync with the project:

```bash
# Sync state
paracle sync

# Preview changes
paracle sync --dry-run

# Force sync
paracle sync --force
```

## Common Operations

### Check Project State

```bash
paracle status
```

### View Logs

```bash
paracle logs show
paracle logs show decisions
```

### List Agents

```bash
paracle agents list
```

### Show Agent Details

```bash
paracle agents get coder
```

## Git Integration

The `.parac/` directory should be committed to git, except for:

- `.parac/runs/` - Execution artifacts
- `.parac/memory/data/*.db` - Operational databases (optional)

Example `.parac/.gitignore`:

```gitignore
# Execution artifacts
runs/

# Large databases (optional)
memory/data/*.db

# IDE-specific
.DS_Store
*.swp
```

## Best Practices

### 1. Keep `project.yaml` Clean

Only store essential configuration:

```yaml
# .parac/project.yaml
name: my-project
version: 0.1.0
description: "My project description"
```

### 2. Document Decisions

Use ADRs in `roadmap/decisions.md`:

```markdown
### ADR-001: Use PostgreSQL for Production

**Date:** 2026-01-08
**Status:** Accepted
**Context:** Need production-ready database
**Decision:** Use PostgreSQL with pgvector
**Consequences:** Requires PostgreSQL setup
```

### 3. Log Agent Actions

Ensure all agent actions are logged:

```python
from paracle_core.governance import log_action

log_action("IMPLEMENTATION", "Implemented feature X")
```

### 4. Regular Sync

Keep workspace synchronized:

```bash
# After major changes
paracle sync

# Before commits
paracle validate --all
```

## Troubleshooting

### Missing Files

If required files are missing:

```bash
# Reinitialize (preserves existing files)
paracle init --template standard

# Force reinitialize
paracle init --force --template standard
```

### Invalid Structure

If validation fails:

```bash
# Check issues
paracle validate governance

# Auto-fix
paracle validate structure --fix
```

### Corrupted State

If manifest is corrupted:

```bash
# Regenerate manifest
paracle sync --force
```

## Related Documentation

- [Installation Guide](../guides/installation.md)
- [Working with Agents](../guides/agents.md)
- [Working with Workflows](../guides/workflows.md)
- [CLI Reference](../../technical/cli-reference.md)
