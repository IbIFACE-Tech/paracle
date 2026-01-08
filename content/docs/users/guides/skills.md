# Working with Skills

Complete guide to creating and using skills in Paracle.

## What is a Skill?

A **skill** is a reusable capability that can be assigned to agents. Skills encapsulate domain-specific knowledge, prompts, and behavior patterns.

```yaml
# .parac/agents/skills/code-review/skill.yaml
name: code-review
description: "Expert code review capability"
version: "1.0"

prompts:
  review: |
    Review the following code for:
    - Code quality and style
    - Security vulnerabilities
    - Performance issues
    - Best practices

parameters:
  severity_levels: ["critical", "major", "minor", "info"]
  focus_areas: ["security", "performance", "style"]
```

## Creating Skills

### Method 1: Manual YAML

Create a folder in `.parac/agents/skills/`:

```
.parac/agents/skills/code-review/
├── skill.yaml       # Skill definition
└── SKILL.md         # Detailed documentation
```

**skill.yaml:**

```yaml
name: code-review
description: "Comprehensive code review skill"
version: "1.0"
author: "Your Team"

# Skill capabilities
capabilities:
  - static_analysis
  - security_review
  - style_check

# Configurable parameters
parameters:
  severity_threshold:
    type: string
    default: "minor"
    options: ["critical", "major", "minor", "info"]

  focus_areas:
    type: list
    default: ["security", "style"]

# Prompts for different operations
prompts:
  analyze: |
    Analyze this code for quality issues.
    Focus on: {{ focus_areas | join(", ") }}
    Report issues with severity >= {{ severity_threshold }}

  summarize: |
    Provide a summary of the code review findings.

# Output format
output:
  format: markdown
  sections:
    - summary
    - issues
    - recommendations
```

**SKILL.md:**

```markdown
# Code Review Skill

## Overview

This skill provides comprehensive code review capabilities.

## Usage

Assign to an agent in its spec:

\`\`\`yaml
skills:
  - code-review
\`\`\`

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| severity_threshold | string | minor | Minimum severity to report |
| focus_areas | list | [security, style] | Areas to focus on |

## Examples

### Basic Review

\`\`\`bash
paracle agents run reviewer --task "Review src/main.py"
\`\`\`

### Security-focused Review

\`\`\`bash
paracle agents run reviewer --task "Security review" \
  --input focus_areas=security
\`\`\`
```

### Method 2: CLI Generation

```bash
# Interactive creation
paracle skills create

# With options
paracle skills create --name code-review --description "Code review skill"
```

### Method 3: AI Generation

```bash
# Generate with AI
paracle meta generate skill \
  --name "security-audit" \
  --description "Security auditing for Python applications"
```

## Skill Specification

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique skill identifier |
| `description` | string | What the skill does |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `version` | string | "1.0" | Skill version |
| `author` | string | None | Skill author |
| `capabilities` | list | [] | What the skill can do |
| `parameters` | object | {} | Configurable parameters |
| `prompts` | object | {} | Prompt templates |
| `output` | object | {} | Output configuration |
| `dependencies` | list | [] | Required skills |

### Full Example

```yaml
name: documentation-writer
description: "Technical documentation writing skill"
version: "2.0"
author: "Documentation Team"

# Prerequisites
dependencies:
  - code-analyzer

# Capabilities
capabilities:
  - api_docs
  - user_guides
  - tutorials
  - readme_generation

# Parameters
parameters:
  style:
    type: string
    default: "technical"
    options: ["technical", "casual", "formal"]
    description: "Writing style"

  format:
    type: string
    default: "markdown"
    options: ["markdown", "rst", "html"]
    description: "Output format"

  include_examples:
    type: boolean
    default: true
    description: "Include code examples"

# Prompts
prompts:
  api_reference: |
    Generate API documentation for the following code.
    Style: {{ style }}
    Format: {{ format }}
    Include examples: {{ include_examples }}

    Focus on:
    - Function signatures
    - Parameters and return values
    - Usage examples
    - Error handling

  user_guide: |
    Write a user guide for this feature.
    Audience: {{ audience | default("developers") }}
    Level: {{ level | default("intermediate") }}

  readme: |
    Generate a README.md with:
    - Project overview
    - Installation instructions
    - Quick start guide
    - API reference summary

# Output configuration
output:
  format: "{{ format }}"
  structure:
    - overview
    - installation
    - usage
    - api_reference
    - examples

# Metadata
metadata:
  category: documentation
  tags: ["docs", "writing", "api"]
  license: MIT
```

## Assigning Skills to Agents

### In Agent Spec

```yaml
# .parac/agents/specs/documenter.md
---
name: documenter
description: "Technical documentation writer"
model: claude-sonnet-4-20250514
temperature: 0.6

skills:
  - documentation-writer
  - code-analyzer

skill_config:
  documentation-writer:
    style: technical
    include_examples: true
---

# Documenter Agent

Writes technical documentation...
```

### In SKILL_ASSIGNMENTS.md

```markdown
# Skill Assignments

| Agent | Skills |
|-------|--------|
| coder | code-generation, refactoring |
| reviewer | code-review, security-audit |
| documenter | documentation-writer |
| tester | test-generation, coverage-analysis |
```

## Skill Inheritance

Skills can depend on other skills:

```yaml
name: security-audit
description: "Security auditing skill"

# Requires code-analyzer skill
dependencies:
  - code-analyzer

# Extends capabilities
capabilities:
  - vulnerability_scan
  - dependency_audit
  - secret_detection
```

## Using Skills

### Via Agent Execution

```bash
# Agent uses its assigned skills
paracle agents run reviewer --task "Review src/app.py"

# Override skill parameters
paracle agents run documenter --task "Write API docs" \
  --input style=formal \
  --input include_examples=false
```

### Skill-Specific Tasks

```bash
# Run specific skill capability
paracle agents run reviewer --task "security_review" \
  --input focus_areas=security
```

## Listing Skills

```bash
# List all skills
paracle skills list

# Show skill details
paracle skills show code-review

# List skills by category
paracle skills list --category documentation
```

## Skill Parameters

### Parameter Types

| Type | Description | Example |
|------|-------------|---------|
| `string` | Text value | `"high"` |
| `boolean` | True/false | `true` |
| `number` | Numeric value | `0.8` |
| `list` | Array of values | `["a", "b"]` |
| `object` | Key-value pairs | `{key: value}` |

### Default Values

```yaml
parameters:
  threshold:
    type: number
    default: 0.8
    min: 0.0
    max: 1.0
    description: "Confidence threshold"
```

### Validation

```yaml
parameters:
  severity:
    type: string
    required: true
    options: ["low", "medium", "high", "critical"]
    description: "Issue severity level"
```

## Prompt Templates

### Basic Template

```yaml
prompts:
  analyze: |
    Analyze the following code:
    {{ code }}
```

### With Parameters

```yaml
prompts:
  review: |
    Review this code with focus on {{ focus_areas | join(", ") }}.
    Minimum severity: {{ severity_threshold }}

    Code:
    {{ code }}
```

### Conditional Content

```yaml
prompts:
  document: |
    Write documentation for this code.
    {% if include_examples %}
    Include usage examples.
    {% endif %}
    {% if format == "markdown" %}
    Use GitHub-flavored markdown.
    {% endif %}
```

## Best Practices

### 1. Single Responsibility

Each skill should do one thing well:

```yaml
# Good - focused skill
name: security-scan
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

### 2. Clear Parameters

Document all parameters:

```yaml
parameters:
  threshold:
    type: number
    default: 0.8
    min: 0.0
    max: 1.0
    description: "Confidence threshold for issue detection"
    examples:
      - value: 0.9
        description: "High confidence only"
      - value: 0.5
        description: "Include uncertain findings"
```

### 3. Reusable Prompts

Create prompts that work across contexts:

```yaml
prompts:
  base_analysis: |
    Analyze the {{ artifact_type }} with focus on:
    {% for area in focus_areas %}
    - {{ area }}
    {% endfor %}
```

### 4. Version Your Skills

Track changes with versions:

```yaml
name: code-review
version: "2.1.0"  # Major.Minor.Patch

changelog:
  "2.1.0": "Added security focus area"
  "2.0.0": "Restructured output format"
  "1.0.0": "Initial release"
```

## Examples

### Code Review Skill

```yaml
name: code-review
description: "Comprehensive code review"
version: "1.0"

capabilities:
  - quality_check
  - security_review
  - style_analysis

parameters:
  focus:
    type: list
    default: ["quality", "security"]
  severity:
    type: string
    default: "minor"

prompts:
  review: |
    Review this code for issues.
    Focus: {{ focus | join(", ") }}
    Minimum severity: {{ severity }}

    Provide:
    1. Summary
    2. Issues found (with line numbers)
    3. Recommendations

output:
  format: markdown
  sections: [summary, issues, recommendations]
```

### Test Generation Skill

```yaml
name: test-generation
description: "Generate comprehensive tests"
version: "1.0"

capabilities:
  - unit_tests
  - integration_tests
  - edge_cases

parameters:
  framework:
    type: string
    default: "pytest"
    options: ["pytest", "unittest", "jest"]
  coverage_target:
    type: number
    default: 80

prompts:
  generate: |
    Generate {{ framework }} tests for this code.
    Target coverage: {{ coverage_target }}%

    Include:
    - Unit tests for all functions
    - Edge cases
    - Error conditions
```

### Documentation Skill

```yaml
name: api-documentation
description: "Generate API documentation"
version: "1.0"

capabilities:
  - endpoint_docs
  - schema_docs
  - examples

parameters:
  format:
    type: string
    default: "openapi"
  include_examples:
    type: boolean
    default: true

prompts:
  document: |
    Generate {{ format }} documentation.
    {% if include_examples %}
    Include request/response examples.
    {% endif %}
```

## Troubleshooting

### Skill Not Found

```bash
# Check skill exists
ls .parac/agents/skills/

# Validate skill
paracle skills validate code-review
```

### Parameter Errors

```bash
# Check parameter types
paracle skills show code-review --verbose

# Test with explicit parameters
paracle agents run reviewer --task "Test" \
  --input severity=high
```

### Prompt Issues

Test prompts independently:

```bash
# Preview rendered prompt
paracle skills render code-review --prompt review \
  --input focus_areas=security,style
```

## Related Documentation

- [Working with Agents](agents.md)
- [Working with Workflows](workflows.md)
- [CLI Reference](../../technical/cli-reference.md)
