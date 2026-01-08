# Paracle Skills System

> **Write Once, Use Anywhere** - Define skills once, export to all AI platforms.

The Paracle Skills System allows you to define reusable agent capabilities in a single location (`.parac/agents/skills/`) and automatically export them to multiple AI platforms including GitHub Copilot, Cursor, Claude Code, OpenAI Codex, and MCP.

## Overview

```
.parac/agents/skills/<skill-name>/
├── SKILL.md              ← Canonical definition (Agent Skills spec)
├── scripts/              ← Optional executable scripts
├── references/           ← Optional documentation
└── assets/               ← Optional templates/configs
         │
         ▼ paracle agents skill export --all
┌──────────────────────────────────────────────────────────────┐
│                    PLATFORM EXPORTS                          │
├────────────┬────────────┬────────────┬────────────┬─────────┤
│  Copilot   │  Cursor    │  Claude    │  Codex     │   MCP   │
│ .github/   │ .cursor/   │ .claude/   │ .codex/    │  JSON   │
│ skills/    │ skills/    │ skills/    │ skills/    │  tools  │
└────────────┴────────────┴────────────┴────────────┴─────────┘
```

## Quick Start

### 1. Create a New Skill

```bash
paracle agents skill create my-skill --category automation
```

This creates:
```
.parac/agents/skills/my-skill/
└── SKILL.md
```

### 2. Edit the SKILL.md

```markdown
---
name: my-skill
description: Brief description of what this skill does and when to use it.
license: Apache-2.0
compatibility: Python 3.10+
metadata:
  author: your-name
  version: "1.0.0"
  category: automation
  level: intermediate
  display_name: "My Skill"
  tags:
    - automation
    - example
  capabilities:
    - capability_1
    - capability_2
allowed-tools: Read Write Bash(git:*)
---

# My Skill

## When to use this skill

Use this skill when:
- [Condition 1]
- [Condition 2]

## Instructions

[Detailed instructions for the AI agent...]
```

### 3. Validate Your Skill

```bash
paracle agents skill validate my-skill
```

### 4. Export to All Platforms

```bash
paracle agents skill export --all
```

## SKILL.md Format

The SKILL.md file follows the [Agent Skills Specification](https://agentskills.io/specification).

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique identifier (1-64 chars, lowercase, hyphens) |
| `description` | string | Brief description (1-1024 chars) |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `license` | string | License name (e.g., "Apache-2.0") |
| `compatibility` | string | Environment requirements (max 500 chars) |
| `metadata` | object | Extended metadata (see below) |
| `allowed-tools` | string | Space-delimited list of pre-approved tools |

### Metadata Object

```yaml
metadata:
  author: your-name           # Skill author
  version: "1.0.0"            # Semantic version
  category: automation        # Skill category
  level: intermediate         # Complexity level
  display_name: "My Skill"    # Human-friendly name
  tags:                       # Keywords for discovery
    - tag1
    - tag2
  capabilities:               # What the skill can do
    - capability_1
    - capability_2
  requirements:               # Dependencies on other skills
    - skill_name: other-skill
      min_version: "1.0.0"
```

### Categories

| Category | Description |
|----------|-------------|
| `creation` | Content/code generation |
| `analysis` | Code analysis, reviews |
| `automation` | Workflow automation |
| `integration` | External integrations |
| `quality` | Quality assurance |
| `devops` | CI/CD, infrastructure |
| `security` | Security scanning |
| `version-control` | Git operations |
| `documentation` | Docs generation |
| `testing` | Test creation/execution |

### Levels

| Level | Description |
|-------|-------------|
| `basic` | Simple, straightforward tasks |
| `intermediate` | Moderate complexity |
| `advanced` | Complex, multi-step tasks |
| `expert` | Specialized domain knowledge |

## Directory Structure

Each skill can have optional subdirectories:

```
.parac/agents/skills/my-skill/
├── SKILL.md              # Required: Skill definition
├── scripts/              # Optional: Executable scripts
│   ├── setup.sh
│   └── validate.py
├── references/           # Optional: Documentation
│   ├── api-docs.md
│   └── examples.md
└── assets/               # Optional: Templates, configs
    ├── template.jinja2
    └── config.yaml
```

These directories are automatically copied when exporting to platforms.

## CLI Commands

### List Skills

```bash
# List all skills
paracle agents skill list

# JSON output
paracle agents skill list --format=json

# Verbose mode
paracle agents skill list -v
```

### Show Skill Details

```bash
# Show formatted details
paracle agents skill show git-management

# Show raw SKILL.md content
paracle agents skill show git-management --raw
```

### Create New Skill

```bash
# Basic creation
paracle agents skill create my-skill

# With options
paracle agents skill create my-skill \
  --category quality \
  --level advanced \
  --with-scripts \
  --with-references \
  --with-assets
```

### Validate Skills

```bash
# Validate specific skill
paracle agents skill validate my-skill

# Validate all skills
paracle agents skill validate --all
```

### Export Skills

```bash
# Export to all platforms
paracle agents skill export --all

# Export to specific platforms
paracle agents skill export -p cursor -p claude

# Export specific skill
paracle agents skill export -p copilot --skill my-skill

# Overwrite existing files
paracle agents skill export --all --overwrite

# Dry run (preview)
paracle agents skill export --all --dry-run
```

## Supported Platforms

### GitHub Copilot

**Output:** `.github/skills/<skill-name>/SKILL.md`

GitHub Copilot uses the Agent Skills specification for custom instructions.

```bash
paracle agents skill export -p copilot
```

### Cursor

**Output:** `.cursor/skills/<skill-name>/SKILL.md`

Cursor IDE supports skills for contextual AI assistance.

```bash
paracle agents skill export -p cursor
```

### Claude Code

**Output:** `.claude/skills/<skill-name>/SKILL.md`

Claude Code CLI uses skills for specialized capabilities.

```bash
paracle agents skill export -p claude
```

### OpenAI Codex

**Output:** `.codex/skills/<skill-name>/SKILL.md`

OpenAI Codex supports the same Agent Skills format.

```bash
paracle agents skill export -p codex
```

### MCP (Model Context Protocol)

**Output:** `.parac/tools/mcp/<skill-name>.json`

For skills with tool definitions, exports as MCP-compatible JSON.

```bash
paracle agents skill export -p mcp
```

## Adding Tools to Skills

Skills can include tool definitions for MCP export:

```yaml
---
name: code-analysis
description: Analyze code for quality and issues.
metadata:
  category: analysis
tools:
  - name: analyze-complexity
    description: Calculate cyclomatic complexity
    input_schema:
      type: object
      properties:
        file_path:
          type: string
          description: Path to file to analyze
      required:
        - file_path
    implementation: scripts/analyze.py:ComplexityTool

  - name: check-security
    description: Scan for security vulnerabilities
    input_schema:
      type: object
      properties:
        file_path:
          type: string
        severity:
          type: string
          enum: [low, medium, high, critical]
      required:
        - file_path
---
```

## Programmatic Usage

### Loading Skills

```python
from pathlib import Path
from paracle_skills import SkillLoader

# Load all skills
loader = SkillLoader(Path(".parac/agents/skills"))
skills = loader.load_all()

for skill in skills:
    print(f"{skill.name}: {skill.description}")
```

### Exporting Skills

```python
from pathlib import Path
from paracle_skills import SkillLoader, SkillExporter

# Load skills
loader = SkillLoader(Path(".parac/agents/skills"))
skills = loader.load_all()

# Export to multiple platforms
exporter = SkillExporter(skills)
results = exporter.export_all(
    output_dir=Path("."),
    platforms=["copilot", "cursor", "claude"],
    overwrite=True
)

for result in results:
    print(f"{result.skill_name}: {result.success_count} platforms")
```

### IDE Generator Integration

```python
from pathlib import Path
from paracle_core.parac.ide_generator import IDEConfigGenerator

generator = IDEConfigGenerator(Path(".parac"))

# Export skills along with IDE configs
results = generator.sync_with_skills(
    platforms=["copilot", "cursor", "claude", "codex"],
    overwrite=True
)

print(f"IDE configs: {len(results['ide_configs'])}")
print(f"Skills exported: {results['skills']}")
```

## Best Practices

### Skill Naming

- Use lowercase with hyphens: `code-review`, `git-management`
- Be descriptive but concise
- Avoid reserved words: `anthropic`, `claude`

### Descriptions

- Start with action verb: "Analyze...", "Generate...", "Manage..."
- Include when to use: "Use when reviewing pull requests..."
- Keep under 1024 characters

### Instructions

- Be specific and actionable
- Include examples and code snippets
- Reference related skills
- Document edge cases

### Organization

- Group related skills by category
- Use consistent metadata patterns
- Keep skills focused (single responsibility)

## Examples

### Code Review Skill

```markdown
---
name: code-review
description: Perform comprehensive code reviews following project standards. Use when reviewing PRs, checking code quality, or auditing security.
license: Apache-2.0
metadata:
  author: paracle-team
  version: "1.0.0"
  category: quality
  level: advanced
  tags:
    - code-review
    - quality
    - security
  capabilities:
    - static_analysis
    - security_scanning
    - style_checking
allowed-tools: Read Grep Glob Bash(ruff:*) Bash(mypy:*)
---

# Code Review

## When to use this skill

Use this skill when:
- Reviewing pull requests
- Auditing code for security issues
- Checking code style compliance
- Identifying performance issues

## Review Checklist

### 1. Code Quality
- [ ] Follows project code style
- [ ] No code duplication
- [ ] Functions are focused and small

### 2. Security
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] No SQL injection risks

### 3. Performance
- [ ] No N+1 queries
- [ ] Efficient algorithms
- [ ] Proper caching
```

### Git Management Skill

See `.parac/agents/skills/git-management/SKILL.md` for a comprehensive example.

## Troubleshooting

### Skill Not Loading

1. Check YAML frontmatter syntax
2. Verify required fields (`name`, `description`)
3. Run `paracle agents skill validate <skill-name>`

### Export Failing

1. Check target directory permissions
2. Use `--overwrite` if files exist
3. Run with `--dry-run` to preview

### Platform Not Recognized

Supported platforms: `copilot`, `cursor`, `claude`, `codex`, `mcp`

## Related Documentation

- [Agent Skills Specification](https://agentskills.io/specification)
- [Claude Code Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [MCP Integration](./mcp-integration.md)
- [IDE Integration](./ide-integration.md)

## API Reference

### SkillSpec

Main model representing a skill definition.

```python
class SkillSpec(BaseModel):
    name: str                    # Skill identifier
    description: str             # Brief description
    license: str | None          # License name
    compatibility: str | None    # Environment requirements
    metadata: SkillMetadata      # Extended metadata
    allowed_tools: str | None    # Pre-approved tools
    tools: list[SkillTool]       # Tool definitions (MCP)
    assigned_agents: list[str]   # Agent assignments
    instructions: str            # SKILL.md body content
```

### SkillLoader

Loads skills from SKILL.md files.

```python
class SkillLoader:
    def __init__(self, skills_dir: Path): ...
    def load_all(self) -> list[SkillSpec]: ...
    def load_skill(self, skill_md_path: Path) -> SkillSpec: ...
    def get_skill_names(self) -> list[str]: ...
    def skill_exists(self, name: str) -> bool: ...
```

### SkillExporter

Exports skills to multiple platforms.

```python
class SkillExporter:
    def __init__(self, skills: list[SkillSpec]): ...
    def export_all(
        self,
        output_dir: Path,
        platforms: list[str] | None = None,
        overwrite: bool = False,
    ) -> list[MultiExportResult]: ...
    def export_skill(
        self,
        skill: SkillSpec,
        output_dir: Path,
        platforms: list[str] | None = None,
        overwrite: bool = False,
    ) -> MultiExportResult: ...
```
