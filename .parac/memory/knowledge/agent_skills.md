# Agent Skills Knowledge Base

## Overview

**Agent Skills** is an open format developed by Anthropic for extending AI agent capabilities with specialized knowledge and workflows. Skills are folders of instructions, scripts, and resources that agents can discover and use to perform better at specific tasks.

The format enables a "write once, use everywhere" approach - developers create skill packages that multiple agents can leverage across different applications.

## Core Concepts

### What is a Skill?

A skill is fundamentally a **folder containing a `SKILL.md` file** as its centerpiece. This markdown file includes YAML frontmatter specifying metadata and markdown body containing instructions.

```
my-skill/
├── SKILL.md           # Required: Main skill definition
├── scripts/           # Optional: Executable scripts
├── references/        # Optional: Additional documentation
└── assets/            # Optional: Resources (images, templates)
```

### Progressive Disclosure Pattern

Skills use a three-stage activation process to manage context efficiently:

1. **Discovery**: Agents load minimal metadata (name + description, ~50-100 tokens) at startup
2. **Activation**: When a task matches a skill's description, full `SKILL.md` instructions load
3. **Execution**: Agent follows instructions and optionally loads referenced files or executes scripts

This pattern keeps agent context lean until specific capabilities are needed.

## SKILL.md Specification

### Required Frontmatter Fields

```yaml
---
name: my-skill-name
description: A clear description of what this skill does and when to use it
---
```

| Field | Constraints | Description |
|-------|-------------|-------------|
| `name` | 1-64 chars, lowercase alphanumeric + hyphens, no leading/trailing/consecutive hyphens | Unique identifier, must match parent directory name |
| `description` | 1-1024 chars | What the skill does and when to use it. Include keywords for task matching |

### Optional Frontmatter Fields

```yaml
---
name: my-skill-name
description: Description here
license: Apache-2.0
compatibility: Requires Python 3.10+, network access for API calls
metadata:
  author: team-name
  version: "1.0.0"
allowed-tools: bash python read_file
---
```

| Field | Description |
|-------|-------------|
| `license` | Licensing terms (name or file reference) |
| `compatibility` | Environment requirements (1-500 chars) |
| `metadata` | Key-value mapping for additional properties |
| `allowed-tools` | Space-delimited list of pre-approved tools (experimental) |

### Body Content Guidelines

- Keep `SKILL.md` under **500 lines** (~5000 tokens recommended)
- Move detailed material to separate reference files
- Include:
  - Step-by-step guidance
  - Input/output examples
  - Edge case handling
  - Guidelines and constraints

## Example Skill Structure

```yaml
---
name: code-review
description: Perform thorough code reviews following best practices. Use when asked to review pull requests, code changes, or provide feedback on code quality.
license: Apache-2.0
compatibility: Works with any programming language
metadata:
  category: development
  author: paracle-team
---

# Code Review Skill

## Purpose
Perform comprehensive code reviews that identify issues, suggest improvements, and ensure code quality.

## Process

1. **Understand Context**: Review the PR description and related issues
2. **Check Structure**: Evaluate code organization and architecture
3. **Verify Logic**: Identify bugs, edge cases, and potential issues
4. **Assess Quality**: Check naming, formatting, and documentation
5. **Security Scan**: Look for vulnerabilities and security concerns
6. **Provide Feedback**: Write constructive, actionable comments

## Guidelines

- Be constructive, not critical
- Explain the "why" behind suggestions
- Prioritize issues (blocking vs. nice-to-have)
- Acknowledge good practices
- Suggest alternatives when rejecting approaches

## Output Format

Provide feedback in structured sections:
- **Summary**: Overall assessment (1-2 sentences)
- **Critical Issues**: Must fix before merge
- **Suggestions**: Improvements to consider
- **Positive Notes**: What was done well
```

## Integration Approaches

### Filesystem-Based Agents

Agents with shell access can directly read skill files:

```bash
cat /path/to/my-skill/SKILL.md
```

This is the most capable option, allowing full access to scripts and resources.

### Tool-Based Agents

Agents without filesystem access implement tools for skill activation:

```python
# Example tool implementation
def activate_skill(skill_name: str) -> str:
    """Load and return skill instructions."""
    skill_path = skills_dir / skill_name / "SKILL.md"
    return skill_path.read_text()
```

### System Prompt Format

Include skill metadata in system prompts using XML (particularly for Claude):

```xml
<available-skills>
  <skill>
    <name>code-review</name>
    <description>Perform thorough code reviews following best practices</description>
    <location>/skills/code-review/SKILL.md</location>
  </skill>
  <skill>
    <name>documentation</name>
    <description>Generate comprehensive documentation for code and APIs</description>
    <location>/skills/documentation/SKILL.md</location>
  </skill>
</available-skills>
```

## Security Considerations

When implementing skills support:

1. **Sandbox script execution**: Isolate skill scripts from system resources
2. **Use allowlists**: Only load skills from trusted sources
3. **Request confirmation**: Before dangerous operations
4. **Log executions**: Audit trail for all script runs
5. **Validate frontmatter**: Sanitize metadata before use

## Adoption & Ecosystem

Agent Skills is supported by major AI development tools:
- **Claude Code** (Anthropic)
- **Cursor**
- **GitHub Copilot**
- **VS Code Extensions**
- **OpenAI Assistants**

## Relevance to Paracle

### Current Implementation

Paracle has a skill system defined in `.parac/agents/SKILL_ASSIGNMENTS.md` that maps skills to agents. This system is conceptually aligned with Agent Skills but uses a different format.

### Integration Opportunities

1. **Format Compatibility**: Consider supporting the Agent Skills format for skill definitions
2. **Skill Discovery**: Implement progressive disclosure for efficient context management
3. **Interoperability**: Allow Paracle agents to use skills from the broader ecosystem
4. **Export**: Enable Paracle skills to be exported in Agent Skills format

### Paracle vs Agent Skills Comparison

| Aspect | Paracle Skills | Agent Skills |
|--------|---------------|--------------|
| Format | YAML in manifest | SKILL.md with frontmatter |
| Location | `.parac/agents/skills/` | Standalone folders |
| Scope | Per-agent assignment | Agent-agnostic |
| Discovery | At agent load | Progressive disclosure |
| Ecosystem | Paracle-specific | Cross-platform |

## References

- **Specification**: https://agentskills.io/specification
- **Integration Guide**: https://agentskills.io/integrate-skills
- **Example Skills**: https://github.com/anthropics/skills
- **Reference Library**: https://github.com/agentskills/agentskills/tree/main/skills-ref
- **Blog Post**: https://anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills

## Open Questions

- Q: Should Paracle adopt Agent Skills format as the standard for skill definitions?
- Q: How to bridge existing Paracle skill assignments with Agent Skills format?
- Q: Should skills be shareable across Paracle workspaces?
