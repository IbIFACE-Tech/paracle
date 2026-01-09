# Working with Agents

Complete guide to creating and using agents in Paracle.

## What is an Agent?

An **agent** is an AI-powered assistant configured to perform specific tasks. Agents are defined in YAML and executed by Paracle.

```yaml
# .parac/agents/specs/coder.yaml
name: coder
description: "Python coding assistant"
model: claude-sonnet-4-20250514
temperature: 0.7
system_prompt: |
  You are an expert Python developer.
  Write clean, well-documented code.
```

## Creating Agents

### Method 1: Manual YAML

Create a file in `.parac/agents/specs/`:

```yaml
# .parac/agents/specs/reviewer.yaml
name: reviewer
description: "Code review assistant"
model: gpt-4o
temperature: 0.3
capabilities:
  - code_review
  - security_analysis
system_prompt: |
  You are a senior code reviewer.
  Focus on code quality, security, and best practices.
```

### Method 2: CLI Generation

```bash
# Interactive creation
paracle agents create

# With options
paracle agents create --name reviewer --model gpt-4o
```

### Method 3: AI Generation

```bash
# Generate with AI
paracle meta generate agent \
  --name "SecurityAuditor" \
  --description "Reviews Python code for security vulnerabilities"
```

## Agent Specification

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique agent identifier |
| `description` | string | What the agent does |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `model` | string | `claude-sonnet-4` | LLM model |
| `temperature` | float | `0.7` | Response randomness (0-2) |
| `system_prompt` | string | None | Custom instructions |
| `parent` | string | None | Parent agent to inherit from |
| `capabilities` | list | `[]` | Agent capabilities |
| `tools` | list | `[]` | Available tools |
| `max_tokens` | int | `4096` | Max response tokens |

### Full Example

```yaml
name: senior-coder
description: "Senior Python developer with security focus"
model: claude-sonnet-4-20250514
temperature: 0.5
max_tokens: 8192

# Inherit from base coder
parent: coder

# Custom prompt
system_prompt: |
  You are a senior Python developer with 10+ years of experience.
  You write secure, performant, well-tested code.
  Always consider:
  - Security implications
  - Error handling
  - Performance
  - Testability

# Available capabilities
capabilities:
  - code_generation
  - code_review
  - security_analysis
  - documentation

# Available tools
tools:
  - read_file
  - write_file
  - run_tests
  - search_code

# Metadata
metadata:
  team: platform
  version: "1.0"
```

## Agent Inheritance

Agents can inherit from parent agents:

```yaml
# Base agent
name: base-coder
model: gpt-4o
temperature: 0.7
capabilities:
  - code_generation

---
# Child agent (inherits and extends)
name: python-coder
parent: base-coder
temperature: 0.5  # Overrides parent
capabilities:
  - python_specific  # Adds to parent
system_prompt: |
  You specialize in Python development.
```

### Inheritance Rules

1. Child inherits all parent properties
2. Child can override any property
3. Lists (capabilities, tools) are merged
4. System prompts can be concatenated

## Running Agents

### CLI Execution

```bash
# Run agent with task
paracle agent run coder --task "Create a hello world script"

# With input file
paracle agent run reviewer --input code.py

# Interactive mode
paracle agent run coder --interactive

# Specific model override
paracle agent run coder --task "..." --model gpt-4o
```

### Execution Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `safe` | Manual approval required | Production |
| `yolo` | Auto-approve all | CI/CD |
| `sandbox` | Isolated execution | Testing |
| `review` | Human review required | Critical tasks |

```bash
# Safe mode (default)
paracle agent run coder --mode safe

# YOLO mode (auto-approve)
paracle agent run coder --mode yolo

# Sandbox mode
paracle agent run coder --mode sandbox
```

## Agent Capabilities

### Built-in Capabilities

| Capability | Description |
|------------|-------------|
| `code_generation` | Generate code |
| `code_review` | Review and analyze code |
| `documentation` | Write documentation |
| `testing` | Write and run tests |
| `security_analysis` | Security review |
| `refactoring` | Refactor code |

### Tool Access

```yaml
# Grant specific tools
tools:
  - read_file        # Read files
  - write_file       # Write files
  - run_command      # Execute commands
  - web_search       # Search the web
  - search_code      # Search codebase
```

### Dangerous Tools

Some tools require explicit approval:

```yaml
tools:
  - write_file:
      requires_approval: true
  - run_command:
      requires_approval: true
      sandbox: true
```

## Listing Agents

```bash
# List all agents
paracle agents list

# Show agent details
paracle agents show coder

# Filter by capability
paracle agents list --capability code_generation
```

## Best Practices

### 1. Clear Descriptions

```yaml
# Good
description: "Reviews Python code for security vulnerabilities, focusing on OWASP Top 10"

# Bad
description: "Security stuff"
```

### 2. Focused System Prompts

```yaml
system_prompt: |
  You are a Python security expert.

  Focus areas:
  - Input validation
  - SQL injection
  - XSS prevention
  - Authentication

  Always provide:
  - Severity rating
  - Code location
  - Fix recommendation
```

### 3. Appropriate Temperature

| Task | Temperature | Reasoning |
|------|-------------|-----------|
| Code generation | 0.3-0.5 | Consistent output |
| Creative writing | 0.7-0.9 | Varied output |
| Code review | 0.1-0.3 | Precise analysis |
| Brainstorming | 0.8-1.0 | Diverse ideas |

### 4. Use Inheritance

```yaml
# Define base agents for common patterns
name: base-security
capabilities:
  - security_analysis
system_prompt: |
  Apply security best practices...

---
# Specialized agents inherit
name: web-security
parent: base-security
system_prompt: |
  Focus on web application security...
```

## Examples

### Code Reviewer

```yaml
name: code-reviewer
description: "Reviews code for quality and best practices"
model: claude-sonnet-4-20250514
temperature: 0.3
capabilities:
  - code_review
tools:
  - read_file
  - search_code
system_prompt: |
  You are a thorough code reviewer.

  Check for:
  - Code style and consistency
  - Error handling
  - Security issues
  - Performance concerns
  - Test coverage

  Format: Use markdown with severity tags.
```

### Documentation Writer

```yaml
name: documenter
description: "Writes technical documentation"
model: gpt-4o
temperature: 0.6
capabilities:
  - documentation
tools:
  - read_file
  - write_file
system_prompt: |
  You write clear, concise technical documentation.

  Style:
  - Use active voice
  - Include code examples
  - Add diagrams when helpful
  - Keep paragraphs short
```

### Test Writer

```yaml
name: tester
description: "Writes comprehensive test suites"
model: claude-sonnet-4-20250514
temperature: 0.4
capabilities:
  - testing
tools:
  - read_file
  - write_file
  - run_tests
system_prompt: |
  You write thorough test suites.

  Include:
  - Unit tests for all functions
  - Edge cases
  - Error conditions
  - Integration tests
  - Clear test names

  Framework: pytest
```

## Next Steps

- [Workflows Guide](workflows.md) - Orchestrate multiple agents
- [Skills Guide](skills.md) - Reusable agent capabilities
- [CLI Reference](../../technical/cli-reference.md) - Full command reference
