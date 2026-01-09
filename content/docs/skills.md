# Skills System

Paracle's skills system enables "write once, export everywhere" - define skills once and export to multiple AI platforms.

## Overview

A **skill** is a reusable capability that can be assigned to agents. Skills encapsulate domain-specific knowledge, prompts, tools, and behavior patterns that can be exported to:

- **GitHub Copilot** (`.github/skills/`)
- **Cursor** (`.cursor/skills/`)
- **Claude Code** (`.claude/skills/`)
- **OpenAI Codex** (`.codex/skills/`)
- **MCP Protocol** (`.parac/tools/mcp/`)
- **Rovo Dev** (Atlassian)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Paracle Skills                                │
│                .parac/agents/skills/                            │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │  code-review/   │    │  security-audit/ │                   │
│  │   SKILL.md      │    │   SKILL.md       │                   │
│  │   scripts/      │    │   scripts/       │                   │
│  └─────────────────┘    └─────────────────┘                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼ Export
┌─────────────────────────────────────────────────────────────────┐
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Copilot  │  │  Cursor  │  │  Claude  │  │   MCP    │        │
│  │ .github/ │  │ .cursor/ │  │ .claude/ │  │ .parac/  │        │
│  │ skills/  │  │ skills/  │  │ skills/  │  │ tools/   │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

## Skill Format

Skills follow the [Agent Skills specification](https://agentskills.io/specification) with Paracle extensions.

### Directory Structure

```
.parac/agents/skills/
└── code-review/
    ├── SKILL.md           # Skill definition (required)
    ├── scripts/           # Tool implementations
    │   └── analyze.py
    ├── references/        # Reference documentation
    │   └── GUIDELINES.md
    └── assets/            # Templates, configs
        └── report-template.md
```

### SKILL.md Format

```markdown
---
name: code-review
description: Expert code review with security and quality analysis
license: MIT
compatibility: Python 3.10+

metadata:
  author: Platform Team
  version: "1.0.0"
  category: quality
  level: intermediate
  display_name: "Code Review"
  tags:
    - code-quality
    - security
    - review
  capabilities:
    - static_analysis
    - security_review
    - style_check

allowed-tools: Read Glob Grep Bash
---

# Code Review Skill

## Overview

This skill provides comprehensive code review capabilities.

## When to Use

Use this skill when:
- Reviewing pull requests
- Performing security audits
- Checking code quality

## Instructions

1. Analyze the code structure
2. Check for security vulnerabilities
3. Review code style and patterns
4. Generate a detailed report

## Output Format

Provide findings in this format:
- **Critical**: Must fix before merge
- **Major**: Should fix before merge
- **Minor**: Nice to fix
- **Info**: Suggestions
```

## Skill Specification

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique identifier (1-64 chars, lowercase alphanumeric + hyphens) |
| `description` | string | What the skill does and when to use (1-1024 chars) |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `license` | string | None | License name (e.g., "MIT", "Apache-2.0") |
| `compatibility` | string | None | Environment requirements |
| `metadata` | object | {} | Extended metadata |
| `allowed-tools` | string | None | Space-delimited list of pre-approved tools |

### Metadata Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `author` | string | None | Skill author or team |
| `version` | string | "1.0.0" | Semantic version |
| `category` | enum | "automation" | Skill category |
| `level` | enum | "intermediate" | Complexity level |
| `display_name` | string | From name | Human-friendly name |
| `tags` | list[string] | [] | Keywords for discovery |
| `capabilities` | list[string] | [] | What the skill can do |
| `requirements` | list[object] | [] | Dependencies |

### Categories

```python
class SkillCategory(str, Enum):
    CREATION = "creation"          # Code/content generation
    ANALYSIS = "analysis"          # Code analysis, review
    AUTOMATION = "automation"      # Task automation
    INTEGRATION = "integration"    # External integrations
    COMMUNICATION = "communication"  # Documentation, reports
    QUALITY = "quality"            # Testing, QA
    DEVOPS = "devops"              # CI/CD, deployment
    SECURITY = "security"          # Security auditing
    VERSION_CONTROL = "version-control"  # Git operations
    DOCUMENTATION = "documentation"  # Docs generation
    TESTING = "testing"            # Test creation
    INFRASTRUCTURE = "infrastructure"  # Infra management
```

### Complexity Levels

```python
class SkillLevel(str, Enum):
    BASIC = "basic"              # Simple, single-purpose
    INTERMEDIATE = "intermediate"  # Moderate complexity
    ADVANCED = "advanced"        # Complex workflows
    EXPERT = "expert"            # Requires deep expertise
```

## Name Validation

Skill names must follow these rules:

```python
# Valid names
"code-review"
"security-audit"
"test-generator"
"api-docs"

# Invalid names
"Code-Review"      # No uppercase
"code_review"      # No underscores
"-code-review"     # Can't start with hyphen
"code--review"     # No consecutive hyphens
"my-claude-skill"  # Can't contain "claude" (reserved)
```

## Creating Skills

### Method 1: Manual YAML

Create a folder in `.parac/agents/skills/`:

```bash
mkdir -p .parac/agents/skills/my-skill
touch .parac/agents/skills/my-skill/SKILL.md
```

### Method 2: CLI

```bash
# Interactive creation
paracle skills create

# With options
paracle skills create --name my-skill --description "My custom skill"
```

### Method 3: AI Generation

```bash
# Generate with AI
paracle meta generate skill \
  --name "api-documentation" \
  --description "Generate API documentation from code"
```

## Assigning Skills to Agents

### In Agent Spec

```yaml
# .parac/agents/specs/reviewer.md
---
name: reviewer
description: Code review agent
model: claude-sonnet-4-20250514

skills:
  - code-review
  - security-audit
---

# Reviewer Agent

Expert code reviewer...
```

### In SKILL_ASSIGNMENTS.md

```markdown
# .parac/agents/SKILL_ASSIGNMENTS.md

# Skill Assignments

| Agent | Skills |
|-------|--------|
| coder | code-generation, refactoring |
| reviewer | code-review, security-audit |
| documenter | api-docs, readme-generator |
| tester | test-generator, coverage-analysis |
```

## Exporting Skills

### Export All

```bash
# Export to all platforms
paracle skills export

# Export to specific platforms
paracle skills export --platforms copilot,cursor

# Export with overwrite
paracle skills export --force
```

### Export Single Skill

```bash
# Export specific skill
paracle skills export code-review

# Export to specific platform
paracle skills export code-review --platforms mcp
```

### Programmatic Export

```python
from paracle_skills import SkillLoader, SkillExporter

# Load skills from .parac/
loader = SkillLoader(".parac/agents/skills")
skills = loader.load_all()

# Export to all platforms
exporter = SkillExporter(skills)
results = exporter.export_all(
    output_dir=Path("."),
    platforms=["copilot", "cursor", "claude", "mcp"],
    overwrite=True,
)

for result in results:
    print(f"{result.skill_name}: {result.success_count}/{len(result.results)}")
```

## Platform Exports

### GitHub Copilot

```
.github/skills/
└── code-review/
    └── SKILL.md
```

### Cursor

```
.cursor/skills/
└── code-review/
    └── SKILL.md
```

### Claude Code

```
.claude/skills/
└── code-review/
    └── SKILL.md
```

### OpenAI Codex

```
.codex/skills/
└── code-review/
    └── SKILL.md
```

### MCP Protocol

Skills with tools are exported as MCP tool definitions:

```json
{
  "name": "code-review",
  "description": "Expert code review",
  "inputSchema": {
    "type": "object",
    "properties": {
      "file_path": {"type": "string"},
      "focus_areas": {"type": "array"}
    }
  }
}
```

## Tools in Skills

Skills can bundle tools for MCP export:

```yaml
---
name: code-analyzer
description: Static code analysis tool

tools:
  - name: analyze-code
    description: Analyze code for issues
    input_schema:
      type: object
      properties:
        file_path:
          type: string
          description: Path to file to analyze
        severity:
          type: string
          enum: [critical, major, minor, info]
    implementation: scripts/analyzer.py:analyze
---
```

### Tool Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | string | Yes | Tool identifier |
| `description` | string | Yes | What the tool does |
| `input_schema` | object | Yes | JSON Schema for parameters |
| `output_schema` | object | No | JSON Schema for output |
| `implementation` | string | No | Path to implementation |
| `annotations` | object | No | MCP annotations |

### MCP Annotations

```yaml
tools:
  - name: write-file
    description: Write content to file
    annotations:
      readOnlyHint: false
      destructiveHint: true
      idempotentHint: true
      openWorldHint: false
```

## Listing Skills

```bash
# List all skills
paracle skills list

# List by category
paracle skills list --category security

# Show skill details
paracle skills show code-review

# Show with full content
paracle skills show code-review --verbose
```

## Validating Skills

```bash
# Validate all skills
paracle skills validate

# Validate specific skill
paracle skills validate code-review

# Fix common issues
paracle skills validate --fix
```

## Best Practices

### 1. Single Responsibility

Each skill should do one thing well:

```yaml
# Good - focused skill
name: security-scan
description: Scan code for security vulnerabilities
capabilities:
  - vulnerability_detection
  - dependency_audit

# Avoid - too broad
name: do-everything
capabilities:
  - security
  - documentation
  - testing
  - deployment
```

### 2. Clear Description

Write descriptions that help AI understand when to use:

```yaml
# Good - specific and actionable
description: |
  Analyze Python code for security vulnerabilities including
  SQL injection, XSS, and hardcoded secrets. Use for pre-commit
  security checks and pull request reviews.

# Avoid - vague
description: Security stuff for code
```

### 3. Versioning

Track changes with semantic versions:

```yaml
metadata:
  version: "2.1.0"

# In SKILL.md body, add changelog:
## Changelog

### 2.1.0
- Added dependency audit capability
- Improved secret detection

### 2.0.0
- Restructured output format
- Breaking: Changed parameter names

### 1.0.0
- Initial release
```

### 4. Categorize Properly

Use appropriate categories for discovery:

```yaml
# Code quality skill
metadata:
  category: quality
  tags: [code-review, static-analysis]

# DevOps skill
metadata:
  category: devops
  tags: [ci-cd, deployment, docker]
```

### 5. Document Capabilities

List what the skill can do:

```yaml
metadata:
  capabilities:
    - analyze_code_quality
    - detect_security_issues
    - suggest_improvements
    - generate_reports
```

## Examples

### Code Review Skill

```yaml
---
name: code-review
description: |
  Comprehensive code review with quality and security analysis.
  Use for pull request reviews and code quality checks.

license: MIT
compatibility: Python 3.10+, TypeScript 5+

metadata:
  author: Platform Team
  version: "1.0.0"
  category: quality
  level: intermediate
  tags: [code-review, quality, security]
  capabilities:
    - static_analysis
    - security_review
    - style_check

allowed-tools: Read Glob Grep
---

# Code Review

## Usage

Analyze code for:
1. Code quality issues
2. Security vulnerabilities
3. Style violations
4. Best practices

## Output Format

| Severity | Description |
|----------|-------------|
| Critical | Must fix before merge |
| Major | Should fix before merge |
| Minor | Nice to fix |
| Info | Suggestions |
```

### API Documentation Skill

```yaml
---
name: api-docs
description: |
  Generate comprehensive API documentation from code.
  Supports OpenAPI, GraphQL, and REST endpoints.

metadata:
  version: "1.2.0"
  category: documentation
  capabilities:
    - openapi_generation
    - endpoint_documentation
    - schema_documentation
---

# API Documentation Generator

## Supported Formats

- OpenAPI 3.0+
- GraphQL SDL
- REST API markdown

## Usage

Point at API code and generate:
1. Endpoint documentation
2. Request/response schemas
3. Authentication details
4. Usage examples
```

## Troubleshooting

### Skill Not Found

```bash
# Check skill exists
ls .parac/agents/skills/

# Verify SKILL.md format
paracle skills validate my-skill
```

### Export Errors

```bash
# Check export output
paracle skills export --verbose

# Verify platform directories exist
ls -la .github/skills/ .cursor/skills/
```

### Name Validation Errors

```bash
# Common issues:
# - Uppercase letters: use lowercase only
# - Underscores: use hyphens instead
# - Reserved words: avoid "claude", "anthropic"

# Fix:
paracle skills validate --fix
```

## Related Documentation

- [Working with Agents](users/guides/agents.md) - Agent configuration
- [MCP Integration](mcp-integration.md) - MCP protocol support
- [Built-in Tools](builtin-tools.md) - Available tools
- [CLI Reference](technical/cli-reference.md) - Command reference
