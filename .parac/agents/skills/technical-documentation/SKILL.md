---
name: technical-documentation
description: Write clear technical documentation, API references, user guides, tutorials, and architecture docs. Use when creating or updating documentation.
license: Apache-2.0
compatibility: Markdown, reStructuredText, MkDocs, Sphinx
metadata:
  author: paracle-core-team
  version: "1.0.0"
  category: communication
  level: intermediate
  display_name: "Technical Documentation Writing"
  tags:
    - documentation
    - markdown
    - api-docs
    - guides
    - tutorials
  capabilities:
    - documentation_writing
    - api_documentation
    - tutorial_creation
    - user_guides
    - architecture_docs
  requirements:
    - skill_name: code-reading
      min_level: intermediate
allowed-tools: Read Write
---

# Technical Documentation Skill

## When to use this skill

Use this skill when:
- Writing user-facing documentation
- Creating API references
- Documenting architecture decisions
- Writing tutorials and guides
- Updating README files
- Creating code examples
- Writing docstrings

## Paracle Documentation Structure

```
docs/
├── index.md                    # Documentation home
├── getting-started.md          # Quick start guide
├── user-guide/                 # User documentation
│   ├── installation.md
│   ├── configuration.md
│   ├── agents.md
│   ├── workflows.md
│   └── tools.md
├── api-reference/              # API documentation
│   ├── agents.md
│   ├── workflows.md
│   └── providers.md
├── architecture/               # Architecture docs
│   ├── overview.md
│   ├── design-patterns.md
│   └── decisions.md
└── examples/                   # Code examples
    ├── hello-world.md
    └── advanced-workflows.md
```

## Documentation Patterns

### Pattern 1: README Structure

```markdown
# Project Name

Brief one-sentence description.

## Overview

2-3 paragraphs explaining:
- What the project does
- Key features
- Why it's useful

## Quick Start

Minimal example to get started in <5 minutes:

\`\`\`bash
# Installation
pip install paracle

# Run
paracle init
paracle agents create my-agent
\`\`\`

## Features

- ✨ Feature 1 - Brief description
- 🚀 Feature 2 - Brief description
- 🔧 Feature 3 - Brief description

## Installation

Detailed installation instructions:

\`\`\`bash
# Using pip
pip install paracle

# Using uv
uv pip install paracle

# From source
git clone https://github.com/org/paracle
cd paracle
uv sync
\`\`\`

## Usage

Common use cases with code examples.

## Documentation

Link to full documentation: [docs.paracle.io](https://docs.paracle.io)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

Apache 2.0 - See [LICENSE](LICENSE)
```

### Pattern 2: Tutorial Structure

```markdown
# Tutorial: Building Your First Agent

## What You'll Learn

- How to create an agent
- How to configure agent behavior
- How to run agent tasks

## Prerequisites

- Python 3.10+
- Paracle installed
- Basic Python knowledge

## Step 1: Create Agent Configuration

First, create a `.parac/` directory:

\`\`\`bash
paracle init
\`\`\`

This creates:

\`\`\`
.parac/
├── project.yaml
├── agents/
│   └── specs/
└── workflows/
\`\`\`

## Step 2: Define Your Agent

Create `.parac/agents/specs/my-agent.yaml`:

\`\`\`yaml
name: my-agent
model: gpt-4
temperature: 0.7
system_prompt: |
  You are a helpful coding assistant.
\`\`\`

## Step 3: Run Your Agent

\`\`\`bash
paracle agents run my-agent
\`\`\`

### Expected Output

\`\`\`
Agent: my-agent
Status: ready
>
\`\`\`

## Next Steps

- Learn about [agent inheritance](./agent-inheritance.md)
- Explore [skills](./skills.md)
- Build [workflows](./workflows.md)

## Troubleshooting

### Problem: Command not found

**Solution**: Ensure Paracle is installed and in your PATH.

\`\`\`bash
pip install paracle
which paracle  # Unix
where paracle  # Windows
\`\`\`

### Problem: Invalid configuration

**Solution**: Validate your YAML syntax:

\`\`\`bash
paracle config validate
\`\`\`
```

### Pattern 3: API Reference

```markdown
# Agent API Reference

## `Agent`

Represents an AI agent with specific capabilities and configuration.

### Constructor

\`\`\`python
Agent(spec: AgentSpec, provider: Provider | None = None)
\`\`\`

**Parameters:**

- `spec` (`AgentSpec`): Agent specification defining behavior
- `provider` (`Provider`, optional): LLM provider instance. Defaults to configured provider.

**Returns:** `Agent` instance

**Raises:**

- `ValidationError`: If spec is invalid
- `ProviderNotFoundError`: If provider not available

**Example:**

\`\`\`python
from paracle_domain import Agent, AgentSpec

spec = AgentSpec(
    name="my-agent",
    model="gpt-4",
    temperature=0.7,
)

agent = Agent(spec=spec)
\`\`\`

### Methods

#### `execute(task: str, context: dict | None = None) -> Result`

Execute a task with optional context.

**Parameters:**

- `task` (`str`): Task description
- `context` (`dict`, optional): Additional context

**Returns:** `Result` containing execution output

**Example:**

\`\`\`python
result = agent.execute(
    "Write a hello world function",
    context={"language": "python"},
)

print(result.output)
# def hello_world():
#     print("Hello, World!")
\`\`\`

## `AgentSpec`

Pydantic model for agent configuration.

### Fields

| Field           | Type          | Default   | Description                    |
| --------------- | ------------- | --------- | ------------------------------ |
| `name`          | `str`         | Required  | Unique agent name              |
| `model`         | `str`         | `"gpt-4"` | LLM model identifier           |
| `temperature`   | `float`       | `0.7`     | Sampling temperature (0.0-2.0) |
| `system_prompt` | `str \| None` | `None`    | Custom system prompt           |
| `max_tokens`    | `int \| None` | `None`    | Maximum output tokens          |
| `skills`        | `list[str]`   | `[]`      | Enabled skills                 |

### Validation

- `name`: 1-100 characters, alphanumeric and hyphens
- `temperature`: Must be between 0.0 and 2.0
- `model`: Must be supported by configured provider
```

### Pattern 4: Architecture Documentation

```markdown
# Paracle Architecture Overview

## System Context

Paracle is a multi-agent orchestration framework that enables users to:

1. Define agent behaviors via configuration
2. Orchestrate complex workflows
3. Integrate custom tools and skills

## High-Level Architecture

\`\`\`
┌─────────────────────────────────────────┐
│         User Configuration              │
│            (.parac/)                    │
├─────────────────────────────────────────┤
│        Application Layer                │
│      (CLI, API, Orchestrator)          │
├─────────────────────────────────────────┤
│          Domain Layer                   │
│  (Agents, Workflows, Tools, Skills)    │
├─────────────────────────────────────────┤
│       Infrastructure Layer              │
│  (Events, Storage, Providers)          │
├─────────────────────────────────────────┤
│          Adapters Layer                 │
│  (OpenAI, Anthropic, Azure, MCP)       │
└─────────────────────────────────────────┘
\`\`\`

## Key Components

### 1. Domain Layer

**Responsibility**: Core business logic

**Components**:
- `Agent`: Agent entity with execution logic
- `AgentSpec`: Agent configuration model
- `Workflow`: Workflow definition
- `Tool`: Tool interface

**Principles**:
- Pure domain logic
- No external dependencies
- Pydantic for validation

### 2. Application Layer

**Responsibility**: Application services and orchestration

**Components**:
- CLI: Command-line interface
- API: REST API endpoints
- Orchestrator: Workflow execution engine

### 3. Infrastructure Layer

**Responsibility**: Technical infrastructure

**Components**:
- Event Bus: Event publishing/subscription
- Storage: Persistence layer
- Logging: Structured logging

## Design Patterns

### Hexagonal Architecture (Ports & Adapters)

\`\`\`
     ┌──────────────┐
     │   Domain     │
     │    Core      │
     └──────┬───────┘
            │
    ┌───────┴───────┐
    │               │
┌───▼────┐     ┌───▼────┐
│  Port  │     │  Port  │
│Provider│     │Storage │
└───┬────┘     └───┬────┘
    │              │
┌───▼────┐     ┌───▼────┐
│Adapter │     │Adapter │
│OpenAI  │     │ SQLite │
└────────┘     └────────┘
\`\`\`

**Benefits**:
- Domain logic independent of infrastructure
- Easy to test (mock adapters)
- Pluggable implementations

## Data Flow

\`\`\`
User Request
    │
    ▼
┌─────────────┐
│  CLI/API    │ Validate input
└─────┬───────┘
      │
      ▼
┌─────────────┐
│ Application │ Business logic
└─────┬───────┘
      │
      ▼
┌─────────────┐
│   Domain    │ Execute agent
└─────┬───────┘
      │
      ▼
┌─────────────┐
│  Adapter    │ Call LLM provider
└─────┬───────┘
      │
      ▼
Response
\`\`\`

## Decision Records

See [Architecture Decisions](./decisions/) for ADRs.
```

### Pattern 5: Code Examples

```markdown
# Code Examples

## Basic Agent Usage

\`\`\`python
from paracle_domain import Agent, AgentSpec

# Create agent spec
spec = AgentSpec(
    name="coder",
    model="gpt-4",
    temperature=0.7,
    system_prompt="You are an expert Python developer.",
)

# Create agent
agent = Agent(spec=spec)

# Execute task
result = agent.execute("Write a fibonacci function")

print(result.output)
\`\`\`

**Output:**

\`\`\`python
def fibonacci(n):
    """Generate Fibonacci sequence up to n terms."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]

    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib
\`\`\`

## Agent with Skills

\`\`\`python
spec = AgentSpec(
    name="researcher",
    model="gpt-4",
    skills=["web-search", "data-analysis"],
)

agent = Agent(spec=spec)

result = agent.execute("Research latest AI trends")
\`\`\`

## Workflow Orchestration

\`\`\`python
from paracle_orchestration import Workflow, Step

workflow = Workflow(
    name="code-review",
    steps=[
        Step(
            id="analyze",
            agent="code-analyzer",
            input="Review this code: {code}",
        ),
        Step(
            id="suggest",
            agent="code-improver",
            input="Improve based on analysis: {analyze.output}",
            depends_on=["analyze"],
        ),
    ],
)

result = await workflow.execute(context={"code": source_code})
\`\`\`
```

## Documentation Best Practices

### 1. Write for Your Audience

**For Users:**
- Focus on "how to"
- Provide complete examples
- Explain common use cases
- Include troubleshooting

**For Developers:**
- Explain architecture
- Document design decisions
- Include code patterns
- Link to source code

### 2. Start with "Why"

```markdown
# Agent Inheritance

## Why Use Inheritance?

Inheritance allows you to:
- Reuse common agent configurations
- Create agent families (e.g., all coding agents)
- Override specific properties
- Maintain consistency across agents

## How It Works

...
```

### 3. Show, Don't Just Tell

```markdown
# ❌ Bad: Just telling
Temperature controls randomness in agent responses.

# ✅ Good: Showing
\`\`\`yaml
# Low temperature (0.1) = deterministic
name: sql-generator
temperature: 0.1  # Consistent SQL queries

# High temperature (1.0) = creative
name: story-writer
temperature: 1.0  # Varied storytelling
\`\`\`
```

### 4. Use Progressive Disclosure

```markdown
# Quick Start (Simple)

\`\`\`bash
paracle agents create my-agent
\`\`\`

# Advanced Configuration (Detailed)

<details>
<summary>Click to expand advanced options</summary>

\`\`\`yaml
name: my-agent
model: gpt-4
temperature: 0.7
max_tokens: 2000
system_prompt: |
  Custom multi-line prompt
  with detailed instructions
skills:
  - web-search
  - code-execution
\`\`\`

</details>
```

### 5. Keep It Current

- Update docs with code changes
- Add "Last updated" dates
- Mark deprecated features
- Link to changelog

## Docstring Standards

### Google Style (Paracle Standard)

\`\`\`python
def resolve_inheritance(
    spec: AgentSpec,
    registry: AgentRegistry,
) -> AgentSpec:
    """Resolve agent inheritance chain and merge properties.

    Walks up the inheritance tree, merging properties from parent
    agents. Child properties override parent properties.

    Args:
        spec: The agent specification to resolve.
        registry: Registry containing all agent definitions.

    Returns:
        A new AgentSpec with all inherited properties merged.

    Raises:
        AgentNotFoundError: If a parent agent doesn't exist.
        CircularInheritanceError: If circular inheritance detected.

    Example:
        >>> parent = AgentSpec(name="base", temperature=0.7)
        >>> child = AgentSpec(name="custom", inherits="base")
        >>> resolved = resolve_inheritance(child, registry)
        >>> resolved.temperature
        0.7
    """
\`\`\`

## Common Pitfalls

❌ **Don't:**
- Assume user knowledge
- Use jargon without explanation
- Write outdated examples
- Skip error scenarios
- Forget prerequisites

✅ **Do:**
- Explain concepts clearly
- Provide working code examples
- Update with code changes
- Include troubleshooting
- List prerequisites

## Resources

- [Write the Docs](https://www.writethedocs.org/)
- [Google Developer Docs Style Guide](https://developers.google.com/style)
- [Markdown Guide](https://www.markdownguide.org/)
- Paracle Docs: `docs/`
