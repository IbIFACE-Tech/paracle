<!--
  AUTO-GENERATED FILE - DO NOT EDIT MANUALLY
  Source: paracle_core.agents
  Generated: 2026-01-08T09:06:20.424470

  To regenerate: paracle sync (or paracle init)
-->

# Agent Specification Template

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

1. Read `.parac/memory/context/current_state.yaml` - Current phase & status
2. Check `.parac/roadmap/roadmap.yaml` - Priorities for current phase
3. Review `.parac/memory/context/open_questions.md` - Check for blockers
4. Consult relevant policies in `.parac/policies/`

### During Work

- Follow `.parac/GOVERNANCE.md` rules
- Check `.parac/agents/SKILL_ASSIGNMENTS.md` for available skills
- Reference `.parac/roadmap/decisions.md` for architectural context

### After Completing Work

Log action to `.parac/memory/logs/agent_actions.log`:

```
[TIMESTAMP] [AGENT_ID] [ACTION_TYPE] Description of work done
```

**Action Types**: IMPLEMENTATION, TEST, BUGFIX, REFACTORING, REVIEW, DOCUMENTATION, DECISION, PLANNING, UPDATE

### Decision Recording

If making an architectural decision, document in `.parac/roadmap/decisions.md`:

```markdown
### ADR-XXX: [Title]

**Date**: YYYY-MM-DD
**Status**: Accepted
**Context**: [Why this decision was needed]
**Decision**: [What was decided]
**Consequences**: [Impact of the decision]
```


## 🚨 CRITICAL: File Placement Rules (MANDATORY)

**NEVER create files in project root. Only 5 files allowed: README.md, CHANGELOG.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md**

All other files MUST go in:
- Project governance/memory → `.parac/memory/summaries/`, `.parac/memory/knowledge/`
- User documentation → `content/docs/`
- Code examples → `content/examples/`

**See [.parac/STRUCTURE.md](../.parac/STRUCTURE.md) for complete rules.**

## Skills (required)

- [skill-name-1]
- [skill-name-2]

> See `.parac/agents/SKILL_ASSIGNMENTS.md` for available skills.

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
