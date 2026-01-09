"""Documentation generator for agent specs.

Generates SCHEMA.md and TEMPLATE.md in .parac/agents/specs/ from the
source of truth in this module.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from paracle_core.agents.schema import ParacPaths
from paracle_core.agents.template import AgentTemplate
from paracle_core.agents.validator import AgentSpecValidator


class AgentDocsGenerator:
    """Generates documentation files from code definitions.

    Creates:
    - SCHEMA.md: Explains required/optional sections
    - TEMPLATE.md: Copy-paste template for new agents
    """

    # Header for generated files
    GENERATED_HEADER = """<!--
  AUTO-GENERATED FILE - DO NOT EDIT MANUALLY
  Source: paracle_core.agents
  Generated: {timestamp}

  To regenerate: paracle sync (or paracle init)
-->

"""

    def __init__(self, specs_dir: Optional[Path] = None):
        """Initialize generator.

        Args:
            specs_dir: Target directory for generated files
        """
        self.specs_dir = specs_dir
        self.template = AgentTemplate()
        self.validator = AgentSpecValidator()

    def generate_schema_md(self) -> str:
        """Generate SCHEMA.md content.

        Returns:
            Complete markdown content for SCHEMA.md
        """
        timestamp = datetime.now().isoformat()
        header = self.GENERATED_HEADER.format(timestamp=timestamp)

        content = f"""{header}# Agent Specification Schema

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
| `{ParacPaths.CURRENT_STATE}` | Current phase & status | Before any task |
| `{ParacPaths.ROADMAP}` | Priorities | Before any task |
| `{ParacPaths.ACTION_LOG}` | Action logging | After any task |

### 4. Skills

```markdown
## Skills

- skill-name-1
- skill-name-2
```

List skills from `.parac/skills/` that this agent uses.
See `{ParacPaths.SKILL_ASSIGNMENTS}` for assignments.

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

{self._generate_paths_table()}

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
- `{ParacPaths.SKILL_ASSIGNMENTS}` - Skill assignments per agent
- `{ParacPaths.GOVERNANCE}` - Project governance rules
"""
        return content

    def generate_template_md(self) -> str:
        """Generate TEMPLATE.md content.

        Returns:
            Complete markdown content for TEMPLATE.md
        """
        timestamp = datetime.now().isoformat()
        header = self.GENERATED_HEADER.format(timestamp=timestamp)

        template = AgentTemplate.create_for_agent(
            agent_id="new-agent",
            agent_name="New Agent",
            agent_role="[Describe what this agent does in 1-2 sentences]",
        )

        content = f"""{header}# Agent Specification Template

> **How to use this template:**
>
> 1. Copy this file to `your-agent.md` in the same folder
> 2. Replace all `[bracketed placeholders]` with your content
> 3. Keep all section headings - they are required
> 4. Run `paracle agents validate your-agent` to check
> 5. Run `paracle agents format your-agent` to auto-fix

---

## Required vs Optional

- **(required)** - Section must exist and have content
- **(optional)** - Section can be removed if not needed

---

# [Agent Name] (required)

## Role (required)

[Describe the agent's primary function in 1-2 sentences]

## Governance Integration (required)

### Before Starting Any Task

1. Read `{ParacPaths.CURRENT_STATE}` - Current phase & status
2. Check `{ParacPaths.ROADMAP}` - Priorities for current phase
3. Review `{ParacPaths.OPEN_QUESTIONS}` - Check for blockers
4. Consult relevant policies in `.parac/policies/`

### During Work

- Follow `{ParacPaths.GOVERNANCE}` rules
- Check `{ParacPaths.SKILL_ASSIGNMENTS}` for available skills
- Reference `{ParacPaths.DECISIONS}` for architectural context

### After Completing Work

Log action to `{ParacPaths.ACTION_LOG}`:

```
[TIMESTAMP] [AGENT_ID] [ACTION_TYPE] Description of work done
```

**Action Types**: IMPLEMENTATION, TEST, BUGFIX, REFACTORING, REVIEW, DOCUMENTATION, DECISION, PLANNING, UPDATE

### Decision Recording

If making an architectural decision, document in `{ParacPaths.DECISIONS}`:

```markdown
### ADR-XXX: [Title]

**Date**: YYYY-MM-DD
**Status**: Accepted
**Context**: [Why this decision was needed]
**Decision**: [What was decided]
**Consequences**: [Impact of the decision]
```

## Skills (required)

- [skill-name-1]
- [skill-name-2]

> See `{ParacPaths.SKILL_ASSIGNMENTS}` for available skills.

## Responsibilities (required)

### [Primary Category]

- [First responsibility]
- [Second responsibility]
- [Third responsibility]

### [Secondary Category]

- [Additional responsibility]
- [Another responsibility]

## Tools & Capabilities (optional)

- [Tool or capability 1]
- [Tool or capability 2]

## Expertise Areas (optional)

- [Technology or domain 1]
- [Technology or domain 2]

## Coding Standards (optional)

- [Standard 1]
- [Standard 2]

## Examples (optional)

### Example: [Scenario Name]

**Context**: [Describe the situation]

**Actions**:
1. [First action taken]
2. [Second action taken]

**Outcome**: [Result of the actions]
"""
        return content

    def _generate_paths_table(self) -> str:
        """Generate markdown table of all .parac/ paths."""
        lines = [
            "| Category | Path | Description |",
            "|----------|------|-------------|",
        ]

        categories = {
            "Governance": [
                (ParacPaths.GOVERNANCE, "Project governance rules"),
                (ParacPaths.STRUCTURE, "Project structure"),
            ],
            "Context": [
                (ParacPaths.CURRENT_STATE, "Current phase & status"),
                (ParacPaths.OPEN_QUESTIONS, "Unresolved questions"),
                (ParacPaths.TECH_DEBT, "Technical debt tracking"),
            ],
            "Roadmap": [
                (ParacPaths.ROADMAP, "Project roadmap & phases"),
                (ParacPaths.DECISIONS, "Architecture decisions (ADRs)"),
            ],
            "Logs": [
                (ParacPaths.ACTION_LOG, "Agent action history"),
                (ParacPaths.DECISIONS_LOG, "Decision log"),
            ],
            "Policies": [
                (ParacPaths.CODE_STYLE, "Code style guide"),
                (ParacPaths.TESTING, "Testing policy"),
                (ParacPaths.SECURITY, "Security policy"),
            ],
            "Knowledge": [
                (ParacPaths.ARCHITECTURE, "Architecture knowledge"),
                (ParacPaths.GLOSSARY, "Project glossary"),
            ],
            "Agents": [
                (ParacPaths.AGENTS_MANIFEST, "Agent registry"),
                (ParacPaths.SKILL_ASSIGNMENTS, "Skill assignments"),
            ],
        }

        for category, paths in categories.items():
            for path, desc in paths:
                lines.append(f"| {category} | `{path}` | {desc} |")

        return "\n".join(lines)

    def generate_to_directory(
        self, specs_dir: Optional[Path] = None
    ) -> dict[str, Path]:
        """Generate documentation files to directory.

        Args:
            specs_dir: Target directory (uses self.specs_dir if None)

        Returns:
            Dictionary mapping filename to path
        """
        target_dir = specs_dir or self.specs_dir
        if target_dir is None:
            raise ValueError("No target directory specified")

        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        generated = {}

        # Generate SCHEMA.md
        schema_path = target_dir / "SCHEMA.md"
        schema_content = self.generate_schema_md()
        schema_path.write_text(schema_content, encoding="utf-8")
        generated["SCHEMA.md"] = schema_path

        # Generate TEMPLATE.md
        template_path = target_dir / "TEMPLATE.md"
        template_content = self.generate_template_md()
        template_path.write_text(template_content, encoding="utf-8")
        generated["TEMPLATE.md"] = template_path

        return generated

    def ensure_docs_exist(self, specs_dir: Path) -> bool:
        """Ensure documentation files exist, create if missing.

        Called by init/sync commands.

        Args:
            specs_dir: Path to .parac/agents/specs/

        Returns:
            True if files were created/updated
        """
        schema_path = specs_dir / "SCHEMA.md"
        template_path = specs_dir / "TEMPLATE.md"

        needs_update = False

        if not schema_path.exists():
            needs_update = True
        if not template_path.exists():
            needs_update = True

        if needs_update:
            self.generate_to_directory(specs_dir)

        return needs_update
