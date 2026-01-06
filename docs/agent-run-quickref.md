# Agent Run Command - Quick Reference

## Overview

The `paracle agents run` command enables **single-agent task execution** for quick, targeted operations without creating full workflows.

## Basic Usage

```bash
paracle agents run <agent_name> --task "<task_description>"
```

## Execution Modes

### 🛡️ Safe Mode (Default)
**Recommended for production and critical tasks**

```bash
paracle agents run coder --task "Fix bug in auth" --mode safe
```

- Human approval required for sensitive operations
- Full audit trail
- Maximum safety

### 🚀 YOLO Mode
**Automated execution with auto-approval**

```bash
paracle agents run coder --task "Update dependencies" --mode yolo
```

- Auto-approves all gates
- Unattended execution
- Ideal for CI/CD, testing, trusted automation
- ⚠️ **Use responsibly in production!**

### 📦 Sandbox Mode
**Isolated execution environment**

```bash
paracle agents run tester --task "Run security tests" --mode sandbox
```

- Isolated file system
- Network restrictions
- Safe for untrusted code
- Rollback on failure

### 👀 Review Mode
**Human-in-the-loop with mandatory review**

```bash
paracle agents run architect --task "Design API" --mode review
```

- Mandatory human approval for all steps
- Detailed artifact review
- Best for critical decisions

## Common Examples

### 1. Code Review

```bash
paracle agents run reviewer \
  --task "Review changes in PR #42" \
  --file src/api.py \
  --file tests/test_api.py \
  --mode safe
```

### 2. Bug Fix (YOLO)

```bash
paracle agents run coder \
  --task "Fix memory leak in worker" \
  --mode yolo \
  --input bug_id=123 \
  --input severity=high
```

### 3. Documentation Generation

```bash
paracle agents run documenter \
  --task "Generate API reference" \
  --file src/api/ \
  --output docs/api.json
```

### 4. Architecture Design

```bash
paracle agents run architect \
  --task "Design authentication system" \
  --model gpt-4-turbo \
  --input users=1000000 \
  --input compliance=SOC2 \
  --mode review
```

### 5. Testing in Sandbox

```bash
paracle agents run tester \
  --task "Run integration tests" \
  --mode sandbox \
  --timeout 600
```

### 6. Cost-Limited Execution

```bash
paracle agents run coder \
  --task "Implement feature X" \
  --cost-limit 5.00 \
  --model gpt-4 \
  --output result.json
```

## All Options

```bash
paracle agents run <agent_name> [OPTIONS]

Required:
  --task, -t TEXT           Task description or instruction

Execution:
  --mode, -m CHOICE         safe|yolo|sandbox|review (default: safe)
  --timeout INT             Timeout in seconds (default: 300)
  --dry-run                 Validate without executing

LLM Configuration:
  --model TEXT              Model name (e.g., gpt-4, claude-3-opus)
  --provider CHOICE         openai|anthropic|google|mistral|groq|ollama
  --temperature FLOAT       Temperature 0.0-2.0
  --max-tokens INT          Maximum tokens to generate

Inputs:
  --input, -i TEXT          Key=value pairs (multiple allowed)
  --file, -f PATH           Input files (multiple allowed)

Cost & Output:
  --cost-limit FLOAT        Maximum cost in USD
  --output, -o PATH         Save output to JSON file
  --stream/--no-stream      Stream output (default: stream)

Display:
  --verbose, -v             Show detailed information
```

## Agent Selection

Choose agent based on task type:

| Agent            | Use Cases                                    |
| ---------------- | -------------------------------------------- |
| `architect`      | Design, architecture decisions               |
| `coder`          | Implementation, bug fixes, features          |
| `tester`         | Test creation, test execution, validation    |
| `reviewer`       | Code review, quality checks, security review |
| `documenter`     | Documentation, guides, API references        |
| `pm`             | Planning, coordination, governance           |
| `releasemanager` | Versioning, releases, deployment             |

## Mode Comparison

| Mode        | Auto-Approve | Isolated | Review Required | Use Case                |
| ----------- | ------------ | -------- | --------------- | ----------------------- |
| **safe**    | ❌            | ❌        | Optional        | Production operations   |
| **yolo**    | ✅            | ❌        | ❌               | CI/CD, automation       |
| **sandbox** | ❌            | ✅        | Optional        | Untrusted code, testing |
| **review**  | ❌            | ❌        | ✅               | Critical decisions      |

## Tips & Best Practices

### 1. Start with Dry Run

```bash
paracle agents run coder --task "Refactor module X" --dry-run
# Validates configuration without executing
```

### 2. Use Verbose for Debugging

```bash
paracle agents run reviewer --task "Review code" --verbose
# Shows detailed execution info and cost breakdown
```

### 3. Set Cost Limits

```bash
paracle agents run coder --task "Large refactoring" --cost-limit 10.00
# Prevents unexpected costs
```

### 4. Save Outputs for Analysis

```bash
paracle agents run architect --task "Design system" --output design.json
# Save results for later review or processing
```

### 5. Combine Multiple Inputs

```bash
paracle agents run coder \
  --task "Implement auth" \
  --input provider=oauth2 \
  --input users=100000 \
  --file requirements.txt \
  --file design.md
```

## YOLO Mode Guidelines

### ✅ Safe for YOLO

- Dependency updates
- Code formatting
- Documentation generation
- Test execution
- Non-destructive analysis
- Development environments

### ⚠️ Use with Caution

- Database migrations
- Production deployments
- Security changes
- Data deletion
- External API calls
- Cost-intensive operations

### ❌ Avoid YOLO

- Production database operations
- Financial transactions
- User data modifications
- Critical infrastructure changes
- Irreversible operations

## Error Handling

### Timeout

```bash
# Increase timeout for long-running tasks
paracle agents run coder --task "Large refactor" --timeout 1800  # 30 min
```

### Cost Exceeded

```bash
# Set higher limit or optimize task
paracle agents run coder --task "Task" --cost-limit 20.00
```

### Agent Not Found

```bash
# Ensure agent exists in .parac/agents/specs/
ls .parac/agents/specs/
```

## Integration with Workflows

Agent run is perfect for:
- Quick prototyping before creating workflows
- Testing individual workflow steps
- Debugging agent behavior
- One-off operations

For multi-step processes, use workflows:

```bash
# Single agent (quick)
paracle agents run coder --task "Fix bug"

# Multi-agent workflow (comprehensive)
paracle workflow run bugfix --bug_description "Memory leak"
```

## Examples by Agent

### Architect Agent

```bash
# System design
paracle agents run architect \
  --task "Design microservices architecture" \
  --input services=api,worker,scheduler \
  --mode review

# Performance analysis
paracle agents run architect \
  --task "Analyze bottlenecks" \
  --file profiling_results.json
```

### Coder Agent

```bash
# Feature implementation
paracle agents run coder \
  --task "Implement JWT authentication" \
  --file design.md \
  --mode yolo

# Bug fix
paracle agents run coder \
  --task "Fix SQL injection in auth" \
  --input cve=CVE-2024-1234 \
  --mode safe
```

### Tester Agent

```bash
# Test generation
paracle agents run tester \
  --task "Generate tests for UserService" \
  --file src/services/user.py

# Test execution
paracle agents run tester \
  --task "Run security tests" \
  --mode sandbox \
  --timeout 600
```

### Reviewer Agent

```bash
# Code review
paracle agents run reviewer \
  --task "Review PR #42" \
  --file changes.diff \
  --input focus=security

# Performance review
paracle agents run reviewer \
  --task "Check performance regressions" \
  --file benchmark_results.json
```

### Documenter Agent

```bash
# API documentation
paracle agents run documenter \
  --task "Generate API reference" \
  --file src/api/ \
  --output docs/api.md

# User guide
paracle agents run documenter \
  --task "Write getting started guide" \
  --input audience=beginners
```

### Release Manager Agent

```bash
# Version check
paracle agents run releasemanager \
  --task "Validate release readiness" \
  --mode safe

# Changelog generation
paracle agents run releasemanager \
  --task "Generate changelog from commits" \
  --input from_tag=v0.1.0 \
  --input to_tag=v0.2.0
```

## See Also

- [Workflow Guide](workflow-guide.md) - Multi-agent orchestration
- [Agent Specs](.parac/agents/specs/) - Available agents
- [YOLO Mode Design](yolo-mode-design.md) - YOLO mode deep dive
- [CLI Reference](cli-reference.md) - All CLI commands

---

**Version**: 1.0
**Last Updated**: 2026-01-06

