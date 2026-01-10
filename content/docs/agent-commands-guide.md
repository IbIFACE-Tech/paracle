# Agent Commands Enhancement Guide

**Version**: 1.0.0 | **Phase**: 10 | **Date**: 2026-01-10

Complete guide to enhanced agent management commands in Paracle CLI.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [List Command](#list-command)
4. [Inspect Command](#inspect-command)
5. [Validate Command](#validate-command)
6. [Test Command](#test-command)
7. [Run Command](#run-command)
8. [Export Command](#export-command)
9. [Create Command](#create-command)
10. [Skills Commands](#skills-commands)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)

---

## Overview

The **agent commands** provide comprehensive tools for managing AI agents in Paracle workspaces.

### Available Commands

| Command    | Purpose                           | New in v1.0.0 |
| ---------- | --------------------------------- | ------------- |
| `list`     | List all available agents         | ✅ Enhanced    |
| `inspect`  | Detailed agent configuration view | ✅ **NEW**     |
| `validate` | Validate agent specs              | ✅ **NEW**     |
| `test`     | Test agent execution              | ✅ **NEW**     |
| `run`      | Execute agent for a task          | ✅ Enhanced    |
| `export`   | Export agent specs                | ✅ Enhanced    |
| `create`   | Create new agent                  | Existing      |
| `skills`   | Manage agent skills               | Existing      |

### Key Features

- ✅ **Comprehensive Inspection** - View full agent configuration
- ✅ **Validation** - Check agent specs for errors
- ✅ **Automated Testing** - Test agents before deployment
- ✅ **Multiple Formats** - JSON, YAML, Rich terminal output
- ✅ **Batch Operations** - Validate/test multiple agents
- ✅ **Fix Common Issues** - Automatic fixes with `--fix` flag

---

## Quick Start

### List Agents

```bash
# Simple list
paracle agents list

# With remote agents
paracle agents list --remote

# JSON output
paracle agents list --format=json
```

### Inspect Agent

```bash
# Basic inspection
paracle agents inspect coder

# With system prompt
paracle agents inspect coder --show-system-prompt

# Full details
paracle agents inspect architect --show-tools --show-skills
```

### Validate Agent

```bash
# Validate single agent
paracle agents validate coder

# Validate all agents
paracle agents validate --all

# Strict validation
paracle agents validate --all --strict

# Auto-fix issues
paracle agents validate coder --fix
```

### Test Agent

```bash
# Basic test
paracle agents test coder

# Custom task
paracle agents test coder --task "Write a hello world function"

# Dry run (no execution)
paracle agents test coder --dry-run

# Extended timeout
paracle agents test architect --timeout 60
```

---

## List Command

### Basic Usage

```bash
paracle agents list
```

**Output**:
```
Agents (8 found)
┌────────────┬──────────────┬─────────────┬────────────────┐
│ ID         │ Name         │ Model       │ Capabilities   │
├────────────┼──────────────┼─────────────┼────────────────┤
│ architect  │ Architect    │ claude-4    │ architecture…  │
│ coder      │ Coder        │ claude-4    │ code, testing  │
│ tester     │ Tester       │ claude-4    │ testing, qa    │
└────────────┴──────────────┴─────────────┴────────────────┘
```

### With Remote Agents

```bash
paracle agents list --remote
```

Shows both local and remote A2A agents.

### Format Options

```bash
# Table (default)
paracle agents list

# JSON
paracle agents list --format=json

# YAML
paracle agents list --format=yaml
```

### Remote Only

```bash
paracle agents list --remote-only
```

Shows only remote A2A agents from manifest.

---

## Inspect Command

### Basic Inspection

```bash
paracle agents inspect coder
```

**Output**:
```
╭─ Agent: coder ─────────────────────────────────────────╮
│ Name: Coder Agent                                      │
│ Role: Implementation specialist                        │
│ Description: Implements features following standards   │
│                                                        │
│ Model Configuration:                                   │
│   • Model: claude-sonnet-4-20250514                   │
│   • Temperature: 0.7                                  │
│   • Max Tokens: default                               │
│                                                        │
│ Capabilities:                                          │
│   code, python, testing, debugging                    │
╰────────────────────────────────────────────────────────╯

Tools
├── read_file
├── write_file
├── run_command
└── search_code

Skills
├── paracle-development
├── testing-qa
└── api-development
```

### Show System Prompt

```bash
paracle agents inspect coder --show-system-prompt
```

Includes the full system prompt (can be long).

### Show All Details

```bash
paracle agents inspect architect --show-tools --show-skills
```

Shows expanded tool and skill information.

### JSON Output

```bash
paracle agents inspect coder --format=json > coder-config.json
```

Export configuration for programmatic use.

### Use Cases

| Use Case             | Command                                    |
| -------------------- | ------------------------------------------ |
| Quick overview       | `inspect coder`                            |
| Full configuration   | `inspect coder --show-system-prompt`       |
| Export configuration | `inspect coder --format=json`              |
| Compare agents       | `inspect coder --format=yaml > coder.yaml` |
| Debugging            | `inspect coder --show-tools --show-skills` |

---

## Validate Command

### Validate Single Agent

```bash
paracle agents validate coder
```

**Output**:
```
Validating: coder
  ✓ Valid
```

### Validate All Agents

```bash
paracle agents validate --all
```

**Output**:
```
Validating: architect
  ✓ Valid

Validating: coder
  ✓ Valid

Validating: tester
  ⚠ Missing 'description' field
  ⚠ Tool 'lint_code' not found in registry

============================================================
Validation Summary:
  Agents validated: 8
  Errors: 0
  Warnings: 2
```

### Strict Mode

```bash
paracle agents validate --all --strict
```

Enables additional checks:
- System prompt quality
- Capability coverage
- Tool availability
- Skill completeness

### Auto-Fix Issues

```bash
paracle agents validate coder --fix
```

Automatically fixes common issues:
- Adds placeholder descriptions
- Fixes formatting
- Updates deprecated fields

**Output**:
```
Validating: coder
  ⚠ Missing 'description' field
  ✓ Fixed: Added placeholder description
```

### Validation Checks

| Check                 | Type    | Description                           |
| --------------------- | ------- | ------------------------------------- |
| Required fields       | Error   | name, description, role               |
| Model validation      | Warning | Checks against known models           |
| Temperature range     | Error   | Must be 0.0 to 1.0                    |
| Parent exists         | Error   | Parent agent must exist               |
| Circular inheritance  | Error   | No inheritance loops                  |
| Tool references       | Warning | Tools must exist in registry          |
| Skill references      | Warning | Skill directories must exist          |
| System prompt quality | Warning | Prompt should be substantial (strict) |

---

## Test Command

### Basic Test

```bash
paracle agents test coder
```

**Output**:
```
Testing agent: coder
✓ Agent spec loaded
Model: claude-sonnet-4-20250514
Temperature: 0.7
Tools: 8 configured
Skills: 3 assigned

Executing test task: Say hello and introduce yourself
(This will consume a small amount of API credits)

✓ Test successful

Agent Response:
Hello! I'm Coder Agent, an implementation specialist in the Paracle
framework. I focus on writing production-quality code following best
practices and architectural standards.

Execution time: 2.34s
```

### Custom Test Task

```bash
paracle agents test coder --task "Write a hello world function in Python"
```

Test with specific task to verify agent capabilities.

### Dry Run

```bash
paracle agents test coder --dry-run
```

Validates configuration without executing (no API credits consumed).

**Output**:
```
Testing agent: coder
✓ Agent spec loaded
Model: claude-sonnet-4-20250514
Temperature: 0.7
Tools: 8 configured
Skills: 3 assigned

✓ Dry run successful - agent is valid
```

### Extended Timeout

```bash
paracle agents test architect --timeout 60
```

For complex agents that need more time.

### Use Cases

| Use Case                 | Command                              |
| ------------------------ | ------------------------------------ |
| Quick validation         | `test coder --dry-run`               |
| Verify after changes     | `test coder`                         |
| Test specific capability | `test coder --task "Implement auth"` |
| Complex agent            | `test architect --timeout 60`        |
| CI/CD smoke test         | `test --dry-run`                     |

---

## Run Command

### Basic Execution

```bash
paracle agents run coder --task "Implement user authentication"
```

Full execution with all features (resilience, tracing, etc.).

### Interactive Mode

```bash
paracle agents run coder -i
```

Interactive conversation mode.

### See Also

- [Agent Run Guide](agent-run-guide.md) - Complete `run` command documentation
- [Agent Run Quick Reference](agent-run-quickref.md) - Quick reference

---

## Export Command

### Export Single Agent

```bash
paracle agents export coder --format=json > coder.json
```

### Export All Agents

```bash
paracle agents export --all --format=yaml > agents.yaml
```

### Formats

- `json` - JSON format
- `yaml` - YAML format
- `markdown` - Markdown documentation

---

## Create Command

### Create Basic Agent

```bash
paracle agents create my-agent --role "Custom specialist"
```

### Create with AI Enhancement

```bash
paracle agents create my-agent \
  --role "Data analyst" \
  --ai-enhance \
  --model claude-opus-4-20250514
```

Uses AI to generate enhanced agent spec.

### See Also

- [Agent Creation Guide](agent-creation-guide.md) - Full agent creation workflow

---

## Skills Commands

### List Skills

```bash
paracle agents skills list
```

### Validate Skills

```bash
paracle agents skills validate --all
```

### Create Skill

```bash
paracle agents skills create my-skill \
  --description "Custom skill" \
  --template advanced
```

### See Also

- [Skills System Guide](skills-system-guide.md) - Complete skills documentation

---

## Best Practices

### 1. Validate Before Deploying

```bash
# Before committing changes
paracle agents validate --all --strict

# If issues found
paracle agents validate --all --fix
```

### 2. Test After Modifications

```bash
# Quick validation
paracle agents test coder --dry-run

# Full test
paracle agents test coder --task "Test task"
```

### 3. Use Inspect for Debugging

```bash
# When agent behaves unexpectedly
paracle agents inspect coder --show-system-prompt

# Check tool availability
paracle agents inspect coder --show-tools
```

### 4. Document with Export

```bash
# Export for documentation
paracle agents export --all --format=markdown > agents-docs.md

# Export for version control
paracle agents export --all --format=yaml > agents-backup.yaml
```

### 5. CI/CD Integration

```yaml
# .github/workflows/validate-agents.yml
name: Validate Agents

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate agent specs
        run: |
          paracle agents validate --all --strict
      - name: Test agents (dry run)
        run: |
          for agent in $(paracle agents list --format=json | jq -r '.[].id'); do
            paracle agents test "$agent" --dry-run
          done
```

---

## Troubleshooting

### Issue: Agent not found

**Cause**: Agent spec file doesn't exist or wrong agent ID

**Solution**:
```bash
# List available agents
paracle agents list

# Check spec file exists
ls .parac/agents/specs/
```

### Issue: Validation errors

**Cause**: Missing required fields or invalid configuration

**Solution**:
```bash
# See specific errors
paracle agents validate coder

# Auto-fix common issues
paracle agents validate coder --fix

# Check against template
cat .parac/agents/specs/TEMPLATE.md
```

### Issue: Test execution fails

**Cause**: Model not configured, API key missing, or timeout too short

**Solution**:
```bash
# Check configuration
paracle agents inspect coder

# Verify API key
echo $ANTHROPIC_API_KEY

# Increase timeout
paracle agents test coder --timeout 60

# Dry run first
paracle agents test coder --dry-run
```

### Issue: System prompt not showing

**Cause**: Not using `--show-system-prompt` flag

**Solution**:
```bash
# Include system prompt
paracle agents inspect coder --show-system-prompt

# Export with prompt
paracle agents inspect coder --format=json --show-system-prompt
```

---

## Related Documentation

- [Agent Run Guide](agent-run-guide.md) - Complete agent execution
- [Agent Creation Guide](agent-creation-guide.md) - Creating new agents
- [Skills System Guide](skills-system-guide.md) - Skills management
- [Agent Groups Guide](agent-groups-guide.md) - Multi-agent collaboration
- [CLI Reference](../cli-reference.md) - All CLI commands

---

**Status**: Phase 10 | **Version**: 1.0.0 | **Date**: 2026-01-10

