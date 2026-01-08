# Getting Started with Paracle

Welcome to Paracle! This guide will help you get up and running in less than 5 minutes.

## Installation

### Prerequisites

- Python 3.10 or higher
- uv (recommended) or pip

### Install Paracle

```bash
# Using uv (recommended)
uv pip install paracle

# Using pip
pip install paracle
```

### Verify Installation

```bash
paracle hello
```

You should see:

```
Paracle v0.0.1 - Hello World!

Framework successfully installed!

Phase 0: Foundation - Complete

Next steps:
  - paracle agents create   - Create a new agent
  - paracle status          - View project state
  - paracle --help          - Show all commands
```

## First Steps

### Option A: Interactive Tutorial (Recommended)

The fastest way to learn Paracle is through our interactive tutorial:

```bash
paracle tutorial start
```

This 30-minute guided experience will teach you:

1. **Create Agent** (5 min) - Define your first agent with interactive prompts
2. **Add Tools** (5 min) - Select from built-in tools (filesystem, http, shell, python, search)
3. **Add Skills** (5 min) - Create custom skill modules for specialized knowledge
4. **Create Templates** (5 min) - Build reusable project templates
5. **Test Agent** (7 min) - Configure API keys and run a dry-run execution
6. **Create Workflow** (3 min) - Orchestrate multiple agents in a workflow

**Tutorial Commands:**

```bash
# Start from beginning
paracle tutorial start

# Resume from last checkpoint
paracle tutorial resume

# Check your progress
paracle tutorial status

# Start from specific step
paracle tutorial start --step 3

# Reset progress (with confirmation)
paracle tutorial reset
```

Progress is automatically saved to `.parac/memory/.tutorial_progress.json`, so you can take breaks and resume anytime.

### Option B: Manual Setup

### 1. Create a Simple Agent

Create a file `my_agent.py`:

```python
from paracle_domain.models import AgentSpec, Agent

# Define agent specification
agent_spec = AgentSpec(
    name="my-first-agent",
    description="A friendly assistant",
    provider="openai",
    model="gpt-4",
    temperature=0.7,
    system_prompt="You are a helpful assistant."
)

# Create agent instance
agent = Agent(spec=agent_spec)
print(f"✅ Agent created with ID: {agent.id}")
```

Run it:

```bash
python my_agent.py
```

### 2. Agent Inheritance Example

Create `inherited_agent.py`:

```python
from paracle_domain.models import AgentSpec

# Base agent
base = AgentSpec(
    name="base-assistant",
    provider="openai",
    model="gpt-4",
    temperature=0.7
)

# Specialized agent (inherits from base)
specialist = AgentSpec(
    name="python-expert",
    parent="base-assistant",
    system_prompt="You are an expert Python developer.",
    temperature=0.5  # Override parent's temperature
)

print(f"Base agent: {base.name}")
print(f"Specialist: {specialist.name} (inherits from {specialist.parent})")
```

### 3. CLI Commands

Paracle provides a CLI for common tasks:

```bash
# Show help
paracle --help

# Start the API server
paracle serve

# List agents from .parac/
paracle agents list

# Run a workflow
paracle workflow run my-workflow

# Check providers
paracle providers list
```

## Project Structure

When working with Paracle, you can organize your project:

```
my-paracle-project/
├── .parac/              # Paracle workspace (source of truth)
│   ├── project.yaml     # Project configuration
│   ├── agents/
│   │   ├── specs/       # Agent specifications
│   │   └── skills/      # Reusable agent skills
│   ├── workflows/       # Workflow definitions
│   ├── policies/        # Project policies
│   └── memory/          # Project state and logs
├── agents/              # Your agent code
├── workflows/           # Your workflow code
└── requirements.txt     # Dependencies
```

Initialize a workspace with:

```bash
# Quick start - complete structure for rapid prototyping
paracle init --lite

# Standard workspace (recommended)
paracle init

# Full workspace with templates and policies
paracle init --all
```

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# LLM Provider Keys
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Optional: Database
DATABASE_URL=sqlite:///paracle.db

# Optional: Features
ENABLE_MCP=true
```

### Project Configuration

Create `.parac/project.yaml`:

```yaml
name: my-paracle-project
version: 0.0.1
description: My first Paracle project

defaults:
  python_version: "3.10"
  model_provider: openai
  default_model: gpt-4
```

## Next Steps

Now that you're set up, explore:

1. **[Architecture Guide](architecture.md)** - Understand Paracle's design
2. **[API Reference](api.md)** - Detailed API documentation
3. **[Examples](../examples/)** - Sample projects
4. **[Roadmap](../.roadmap/)** - Upcoming features

## Common Issues

### Import Errors

If you see import errors:

```bash
# Reinstall with all dependencies
uv pip install paracle[all]
```

### Permission Errors

On Linux/Mac, you might need:

```bash
python3 -m pip install --user paracle
```

### API Key Issues

Make sure your API keys are set:

```bash
export OPENAI_API_KEY=your-key
# or
echo "OPENAI_API_KEY=your-key" >> .env
```

## Need Help?

- **Issues**: [GitHub Issues](https://github.com/IbIFACE-Tech/paracle-lite/issues)
- **Discussions**: [GitHub Discussions](https://github.com/IbIFACE-Tech/paracle-lite/discussions)
- **Documentation**: [Full Docs](https://github.com/IbIFACE-Tech/paracle-lite/docs)

---

**Ready to build?** Check out the [Examples](../examples/) to see Paracle in action!
