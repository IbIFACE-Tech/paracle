<!--
  AUTO-GENERATED FILE - DO NOT EDIT MANUALLY
  Source: paracle_core.agents
  Generated: 2026-01-08T09:06:20.422048

  To regenerate: paracle sync (or paracle init)
-->

# Agent Specification Schema

This document defines the required structure for agent specifications
in `.parac/agents/specs/`.

> **Source of Truth**: `paracle_core.agents.schema`
>
> This file is generated documentation. The actual schema is enforced
> by the `paracle agents validate` command.

---

## Quick Start

1. Copy `TEMPLATE.md` to `your-agent.md`
2. Fill in the required sections
3. Run `paracle agents validate` to check
4. Run `paracle agents format` to auto-fix issues

---

## Required Sections

Every agent spec MUST have these sections:

### 1. Title (H1)

```markdown
# Agent Name
```

The title should match the filename. For `coder.md`, use `# Coder Agent`.

### 2. Role

```markdown
## Role

One-paragraph description of what this agent does.
```

### 3. Governance Integration

```markdown
## Governance Integration

### Before Starting Any Task
[Instructions for pre-task .parac/ reads]

### After Completing Work
[Instructions for post-task logging]
```

**Required .parac/ references:**

| Path | Purpose | When |
|------|---------|------|
| `.parac/memory/context/current_state.yaml` | Current phase & status | Before any task |
| `.parac/roadmap/roadmap.yaml` | Priorities | Before any task |
| `.parac/memory/logs/agent_actions.log` | Action logging | After any task |

### 4. Skills

```markdown

## 🚨 CRITICAL: File Placement Rules (MANDATORY)

**NEVER create files in project root. Only 5 files allowed: README.md, CHANGELOG.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md**

All other files MUST go in:
- Project governance/memory → `.parac/memory/summaries/`, `.parac/memory/knowledge/`
- User documentation → `content/docs/`
- Code examples → `content/examples/`

**See [.parac/STRUCTURE.md](../.parac/STRUCTURE.md) for complete rules.**

## Skills

- skill-name-1
- skill-name-2
```

List skills from `.parac/skills/` that this agent uses.
See `.parac/agents/SKILL_ASSIGNMENTS.md` for assignments.

### 5. Responsibilities

```markdown
## Responsibilities

### Category Name

- Responsibility item 1
- Responsibility item 2
```

Group responsibilities into categories using H3 headings.

---

## Optional Sections

These sections are recommended but not required:

### Tools & Capabilities

```markdown
## Tools & Capabilities

- Tool or capability 1
- Tool or capability 2
```

### Expertise Areas

```markdown
## Expertise Areas

- Technology 1
- Technology 2
```

### Coding Standards

```markdown
## Coding Standards

- Standard 1
- Standard 2
```

### Examples

```markdown
## Examples

### Example: Scenario Name

**Context**: Description of situation
**Actions**: What the agent does
**Outcome**: Result
```

---

## All .parac/ Paths

Agents may reference these paths:

| Category | Path | Description |
|----------|------|-------------|
| Governance | `.parac/GOVERNANCE.md` | Project governance rules |
| Governance | `.parac/STRUCTURE.md` | Project structure |
| Context | `.parac/memory/context/current_state.yaml` | Current phase & status |
| Context | `.parac/memory/context/open_questions.md` | Unresolved questions |
| Context | `.parac/memory/context/tech_debt.md` | Technical debt tracking |
| Roadmap | `.parac/roadmap/roadmap.yaml` | Project roadmap & phases |
| Roadmap | `.parac/roadmap/decisions.md` | Architecture decisions (ADRs) |
| Logs | `.parac/memory/logs/agent_actions.log` | Agent action history |
| Logs | `.parac/memory/logs/decisions.log` | Decision log |
| Policies | `.parac/policies/CODE_STYLE.md` | Code style guide |
| Policies | `.parac/policies/TESTING.md` | Testing policy |
| Policies | `.parac/policies/SECURITY.md` | Security policy |
| Knowledge | `.parac/memory/knowledge/architecture.md` | Architecture knowledge |
| Knowledge | `.parac/memory/knowledge/glossary.md` | Project glossary |
| Agents | `.parac/agents/manifest.yaml` | Agent registry |
| Agents | `.parac/agents/SKILL_ASSIGNMENTS.md` | Skill assignments |

---

## Validation Rules

The `paracle agents validate` command checks:

1. **Required sections exist** and are not empty
2. **Governance section** has pre-task and post-task subsections
3. **Skills section** has at least one skill listed
4. **Responsibilities section** has categorized items
5. **Required .parac/ paths** are referenced

### Severity Levels

| Level | Meaning |
|-------|---------|
| ERROR | Must fix - spec is invalid |
| WARNING | Should fix - spec may not work correctly |
| INFO | Suggestion for improvement |

---

## CLI Commands

```bash
# Validate all agent specs
paracle agents validate

# Validate specific agent
paracle agents validate coder

# Auto-fix common issues
paracle agents format

# Create new agent from template
paracle agents create my-agent --role "Description"

# List all agents
paracle agents list
```

---

## See Also

- `TEMPLATE.md` - Copy this to create new agents
- `.parac/agents/SKILL_ASSIGNMENTS.md` - Skill assignments per agent
- `.parac/GOVERNANCE.md` - Project governance rules
