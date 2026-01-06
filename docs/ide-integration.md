# IDE Integration Guide

Guide to integrating Paracle with AI-powered IDEs and code editors.

## Overview

Paracle generates configuration files for popular AI-enabled IDEs, ensuring consistent AI behavior across your development team. These configurations include project context, coding standards, and agent specifications.

## Supported IDEs

| IDE | Config File | Destination | Features |
|-----|-------------|-------------|----------|
| Cursor | `.cursorrules` | `./` | Custom rules, context |
| Claude Code | `CLAUDE.md` | `.claude/` | Instructions, memory |
| Cline | `.clinerules` | `./` | Rules, context |
| GitHub Copilot | `copilot-instructions.md` | `.github/` | Custom instructions |
| Windsurf | `.windsurfrules` | `./` | Project rules |
| DeepSeek Coder | `.deepseek-coder.md` | `./` | Custom instructions |
| Google Gemini | `.google-gemini.md` | `./` | Project context |
| Mistral Codestral | `.mistral-codestral.md` | `./` | Coding guidelines |
| Kimi K2 | `.kimi-k2.md` | `./` | Instructions |

---

## Quick Start

### Initialize IDE Configurations

```bash
# Initialize all supported IDEs
paracle ide init --ide=all

# Initialize specific IDE
paracle ide init --ide=cursor

# Initialize multiple IDEs
paracle ide init --ide=cursor --ide=claude --ide=copilot

# Force overwrite existing files
paracle ide init --ide=cursor --force
```

### Check Status

```bash
# Show IDE configuration status
paracle ide status

# Output as JSON
paracle ide status --json
```

**Output:**
```
IDE Integration Status
+--------------------------------------------------------------+
| IDE           | Config File        | Status    | Location    |
|---------------+--------------------+-----------+-------------|
| Cursor        | .cursorrules       | active    | ./          |
| Claude Code   | CLAUDE.md          | active    | .claude/    |
| GitHub Copilot| copilot-instr...   | missing   | .github/    |
| Cline         | .clinerules        | active    | ./          |
| Windsurf      | .windsurfrules     | outdated  | ./          |
+--------------------------------------------------------------+
```

### Synchronize Configurations

```bash
# Sync IDE configs with .parac/ state
paracle ide sync

# Watch for changes and auto-sync
paracle ide sync --watch

# Sync without copying to project root
paracle ide sync --no-copy
```

---

## Configuration Generation

### What Gets Generated

IDE configuration files include:

1. **Project Context**
   - Project name, description, version
   - Technology stack
   - Architecture overview

2. **Coding Standards**
   - Style guidelines
   - Naming conventions
   - Documentation requirements

3. **Agent Context**
   - Available agents and their roles
   - Agent capabilities
   - Tool access permissions

4. **Governance Rules**
   - Quality gates
   - Review requirements
   - Compliance considerations

### Template System

Configurations are generated from templates in `.parac/`:

```
.parac/
├── templates/
│   └── ai-instructions/
│       ├── .cursorrules
│       ├── CLAUDE.md
│       ├── .clinerules
│       └── ...
└── config.yaml          # Project configuration
```

### Customization

#### Project-Level Settings

Configure in `.parac/config.yaml`:

```yaml
ide:
  # IDEs to auto-sync
  active:
    - cursor
    - claude
    - copilot

  # Custom rules to include
  custom_rules:
    - "Always use TypeScript for frontend code"
    - "Follow the repository pattern for data access"
    - "Include JSDoc comments for public functions"

  # Technology context
  tech_stack:
    languages:
      - python
      - typescript
    frameworks:
      - fastapi
      - react
    tools:
      - pytest
      - eslint

  # Auto-sync on changes
  auto_sync: true
```

#### Per-IDE Customization

Add IDE-specific rules in `.parac/templates/ai-instructions/`:

```markdown
<!-- .parac/templates/ai-instructions/.cursorrules -->

# Project: {{ project.name }}

## Custom Rules

{{ custom_rules }}

## Architecture

{{ architecture_overview }}

## Available Agents

{% for agent in agents %}
- **{{ agent.name }}**: {{ agent.description }}
{% endfor %}
```

---

## IDE-Specific Guides

### Cursor

**File:** `.cursorrules`

**Location:** Project root

**Features:**
- Custom coding rules
- Project context injection
- Architecture awareness

**Example Configuration:**

```markdown
# Cursor Rules for Paracle Project

## Project Overview
Multi-agent AI framework with hexagonal architecture.

## Coding Standards
- Use Python 3.11+ features
- Type hints required on all functions
- Pydantic models for domain entities
- Async/await for I/O operations

## Architecture
- Domain layer: Pure Python, no dependencies
- Infrastructure layer: Adapters for external systems
- API layer: FastAPI with proper validation

## Testing
- pytest with async support
- Arrange-Act-Assert pattern
- 80%+ coverage target
```

---

### Claude Code

**File:** `CLAUDE.md`

**Location:** `.claude/`

**Features:**
- Rich project instructions
- Multi-file context
- Memory persistence
- Custom rules

**Example Configuration:**

```markdown
# Paracle Framework - Claude Code Instructions

## Identity
You are working on Paracle, a multi-agent AI framework.

## Key Files
- packages/ - Framework source code
- .parac/ - Project governance
- docs/ - Documentation

## Coding Standards
[Detailed standards...]

## Architecture
[Architecture overview...]
```

---

### GitHub Copilot

**File:** `copilot-instructions.md`

**Location:** `.github/`

**Features:**
- Repository-wide instructions
- Team-shared context
- PR integration

**Example Configuration:**

```markdown
# GitHub Copilot Instructions

## Project Context
Paracle is a multi-agent AI framework built with Python.

## Code Style
- Follow PEP 8
- Use type hints
- Google-style docstrings

## Architecture Patterns
- Hexagonal architecture
- Repository pattern
- Event-driven design
```

---

### Cline

**File:** `.clinerules`

**Location:** Project root

**Features:**
- Custom rules
- Context awareness
- Tool restrictions

**Example Configuration:**

```markdown
# Cline Rules

## Project: Paracle

## Rules
- Always read .parac/ for project state
- Use existing patterns from codebase
- Run tests before completing tasks

## Forbidden
- Do not modify .parac/ without permission
- Do not add dependencies without justification
```

---

### Windsurf

**File:** `.windsurfrules`

**Location:** Project root

**Features:**
- Project rules
- Coding standards
- Context injection

---

## API Integration

### REST Endpoints

#### List Supported IDEs

```bash
GET /ide/list
```

**Response:**
```json
{
  "ides": [
    {
      "name": "cursor",
      "display_name": "Cursor",
      "file_name": ".cursorrules",
      "destination": "./"
    }
  ]
}
```

#### Get IDE Status

```bash
GET /ide/status
```

**Response:**
```json
{
  "ides": [
    {
      "name": "cursor",
      "status": "active",
      "file_exists": true,
      "last_synced": "2026-01-05T12:00:00Z",
      "needs_update": false
    }
  ]
}
```

#### Initialize IDE Config

```bash
POST /ide/init
```

**Request:**
```json
{
  "ides": ["cursor", "claude"],
  "force": false,
  "copy": true
}
```

#### Sync IDE Configs

```bash
POST /ide/sync
```

**Request:**
```json
{
  "copy": true
}
```

---

## Programmatic Usage

### Using IDEGenerator

```python
from paracle_core.parac.ide_generator import IDEGenerator

# Create generator
generator = IDEGenerator(parac_path=".parac")

# List supported IDEs
ides = generator.list_supported()
for ide in ides:
    print(f"{ide.name}: {ide.file_name}")

# Generate config for specific IDE
content = generator.generate("cursor")
print(content)

# Generate and write to file
generator.generate_and_write("cursor", copy_to_root=True)

# Sync all active IDEs
generator.sync_all()
```

### Custom Template Variables

```python
from paracle_core.parac.ide_generator import IDEGenerator

generator = IDEGenerator(parac_path=".parac")

# Add custom variables for template rendering
generator.set_variables({
    "team_name": "Platform Team",
    "review_required": True,
    "max_file_size": 1000
})

# Generate with custom variables
content = generator.generate("cursor")
```

---

## Best Practices

### 1. Keep Configs in Sync

```bash
# Add to pre-commit hook
paracle ide sync

# Or enable auto-sync
# .parac/config.yaml
ide:
  auto_sync: true
```

### 2. Version Control IDE Configs

```gitignore
# .gitignore - DO include IDE configs
# Don't ignore these:
# .cursorrules
# .clinerules
# .github/copilot-instructions.md
```

### 3. Team Alignment

Share IDE configurations to ensure consistent AI behavior:

```bash
# Initialize for all team members
paracle ide init --ide=all

# Commit to repository
git add .cursorrules .clinerules .github/
git commit -m "chore: add IDE configurations"
```

### 4. Update After Changes

Regenerate configs when project structure changes:

```bash
# After adding new agents
paracle ide sync

# After architecture changes
paracle ide init --ide=all --force
```

### 5. IDE-Specific Optimization

Customize rules for each IDE's strengths:

```yaml
# .parac/config.yaml
ide:
  cursor:
    extra_rules:
      - "Use Cursor's inline chat for quick fixes"

  claude:
    extra_rules:
      - "Use multi-file context for refactoring"

  copilot:
    extra_rules:
      - "Focus on completion suggestions"
```

---

## Troubleshooting

### Config Not Updating

```bash
# Force regenerate
paracle ide init --ide=cursor --force

# Check for sync issues
paracle ide status --json
```

### IDE Not Recognizing Config

1. Verify file location matches IDE requirements
2. Check file permissions
3. Restart IDE after config changes

### Template Errors

```bash
# Validate templates
paracle validate ai-instructions

# Check template syntax
cat .parac/templates/ai-instructions/.cursorrules
```

### Conflicts Between IDEs

Each IDE has its own config file, so conflicts are rare. If behavior differs:

1. Check each IDE's config file
2. Ensure `.parac/config.yaml` is consistent
3. Run `paracle ide sync` to align all configs

---

## Examples

### Multi-IDE Project Setup

```bash
# Initialize project
paracle init

# Set up IDE configurations
paracle ide init --ide=cursor --ide=claude --ide=copilot

# Verify
paracle ide status

# Add to CI
echo "paracle ide sync" >> .github/workflows/ci.yml
```

### Custom Rules for Team

```yaml
# .parac/config.yaml
ide:
  custom_rules:
    - "Follow our internal API design guidelines"
    - "Use the approved logging format"
    - "Include performance considerations in PRs"
    - "Reference ticket numbers in commits"
```

---

## Related Documentation

- [CLI Reference](cli-reference.md) - IDE commands
- [API Reference](api-reference.md) - IDE API endpoints
- [Getting Started](getting-started.md) - Project setup

---

**Last Updated:** 2026-01-05
**Version:** 0.0.1
