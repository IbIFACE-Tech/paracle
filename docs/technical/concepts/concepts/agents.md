# Agents

Agents are autonomous AI entities with specific roles, capabilities, and behavior.

## What is an Agent?

An **agent** is a configured AI model with:
- A specific role and purpose
- Tools it can use
- Skills for specialized knowledge
- Behavioral parameters (temperature, etc.)
- Optionally inherits from other agents

Think of agents like specialized team members - each has their expertise and tools.

## Basic Agent

```yaml
---
name: code-assistant
role: developer
description: Helps with Python development
provider: openai
model: gpt-4
temperature: 0.7
---

# Code Assistant

I help with Python development tasks.

## Capabilities

- Write Python code
- Fix bugs
- Review code
- Write tests
```

## Agent Specification

### Required Fields

| Field         | Type   | Description                    |
| ------------- | ------ | ------------------------------ |
| `name`        | string | Unique agent identifier        |
| `description` | string | What the agent does            |
| `provider`    | string | LLM provider (openai, etc.)    |
| `model`       | string | Model name (gpt-4, etc.)       |

### Optional Fields

| Field            | Type    | Description                      | Default |
| ---------------- | ------- | -------------------------------- | ------- |
| `role`           | string  | Agent role                       | -       |
| `temperature`    | float   | Randomness (0.0-2.0)             | 0.7     |
| `max_tokens`     | int     | Max response length              | 4096    |
| `system_prompt`  | string  | System instructions              | -       |
| `tools`          | list    | Available tools                  | []      |
| `skills`         | list    | Assigned skills                  | []      |
| `parent`         | string  | Parent agent (inheritance)       | -       |

## Agent Inheritance

Agents can inherit from other agents, like classes in OOP:

```yaml
# base-developer.md
---
name: base-developer
provider: openai
model: gpt-4
temperature: 0.7
tools:
  - filesystem
  - python
---

# Base Developer

General development agent.
```

```yaml
# python-expert.md
---
name: python-expert
parent: base-developer  # Inherit from base
temperature: 0.5        # Override temperature
skills:
  - python-expert       # Add skills
---

# Python Expert

Specialized in Python development.
```

**Result:**
- `python-expert` has all tools from `base-developer`
- Temperature is overridden (0.5 instead of 0.7)
- Additional skills added
- System prompt extended

[Learn more about inheritance →](../agent-inheritance-example.md)

## Tools

Agents use tools to interact with the world:

```yaml
tools:
  - filesystem  # Read/write files
  - http        # Make HTTP requests
  - shell       # Execute commands
  - python      # Run Python code
  - search      # Search web/docs
```

[View all built-in tools →](../builtin-tools.md)

## Skills

Skills add specialized knowledge:

```yaml
skills:
  - python-expert      # Python best practices
  - security-hardening # Security patterns
  - api-development    # API design
```

[Learn about skills →](../agent-skills.md)

## Creating Agents

### Method 1: YAML Files

Create `.parac/agents/specs/my-agent.md`:

```yaml
---
name: my-agent
description: My first agent
provider: openai
model: gpt-4
tools:
  - filesystem
---

# My Agent

This is my first agent.
```

### Method 2: Python Code

```python
from paracle_domain.models import AgentSpec, Agent

spec = AgentSpec(
    name="my-agent",
    description="My first agent",
    provider="openai",
    model="gpt-4",
    tools=["filesystem"]
)

agent = Agent(spec=spec)
```

### Method 3: CLI

```bash
paracle agents create my-agent \
  --provider openai \
  --model gpt-4 \
  --tools filesystem,http
```

### Method 4: Interactive Tutorial

```bash
paracle tutorial start
# Follow Step 1: Create Agent
```

## Using Agents

### Run with CLI

```bash
paracle agents run my-agent --task "Read README.md"
```

### Run with Python

```python
from paracle_orchestration import execute_agent

result = await execute_agent(
    agent_id="my-agent",
    task="Read README.md"
)
print(result.output)
```

### In Workflows

```yaml
name: my-workflow
steps:
  - id: step1
    agent: my-agent
    task: "{{ input.task }}"
```

## Agent Lifecycle

```
┌──────────┐
│ Created  │ ← Agent spec defined
└────┬─────┘
     │
     ▼
┌──────────┐
│ Loaded   │ ← Inheritance resolved
└────┬─────┘
     │
     ▼
┌──────────┐
│ Executed │ ← Task performed
└────┬─────┘
     │
     ▼
┌──────────┐
│ Complete │ ← Result returned
└──────────┘
```

## Best Practices

### ✅ Do

- Give agents clear, specific roles
- Use inheritance to avoid duplication
- Provide only needed tools
- Use appropriate temperature (low for precise, high for creative)
- Test agents with dry runs

### ❌ Don't

- Give all tools to every agent
- Use vague descriptions
- Set temperature too high for production
- Forget to specify provider/model
- Skip validation

## Examples

### Code Reviewer

```yaml
---
name: code-reviewer
role: reviewer
description: Reviews code for quality and security
provider: anthropic
model: claude-3-opus
temperature: 0.3
tools:
  - filesystem
  - python_analyzer
skills:
  - security-hardening
  - code-quality
---

# Code Reviewer

I review code focusing on:
- Security vulnerabilities
- Code quality
- Best practices
- Performance issues
```

### Data Analyst

```yaml
---
name: data-analyst
role: analyst
description: Analyzes data and generates insights
provider: openai
model: gpt-4
temperature: 0.5
tools:
  - filesystem
  - python
  - search
skills:
  - data-analysis
  - visualization
---

# Data Analyst

I analyze data and create visualizations.
```

### API Designer

```yaml
---
name: api-designer
role: architect
description: Designs RESTful APIs
provider: openai
model: gpt-4-turbo
temperature: 0.7
tools:
  - filesystem
  - http
skills:
  - api-development
  - openapi
---

# API Designer

I design RESTful APIs following best practices.
```

## Next Steps

- [Create your first agent](../guides/creating-agents.md)
- [Learn about inheritance](../agent-inheritance-example.md)
- [Explore agent skills](../agent-skills.md)
- [Use agents in workflows](../workflow-guide.md)
