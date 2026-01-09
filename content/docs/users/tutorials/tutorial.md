# Interactive Tutorial

The Paracle interactive tutorial is a 30-minute guided experience that teaches you all the core concepts of the framework through hands-on exercises.

## Overview

The tutorial walks you through 6 progressive steps:

1. **Create Agent** (5 min) - Define your first agent with interactive prompts
2. **Add Tools** (5 min) - Select from built-in tools (filesystem, http, shell, python, search)
3. **Add Skills** (5 min) - Create custom skill modules for specialized knowledge
4. **Create Templates** (5 min) - Build reusable project templates
5. **Test Agent** (7 min) - Configure API keys and run a dry-run execution
6. **Create Workflow** (3 min) - Orchestrate multiple agents in a workflow

Progress is automatically saved, so you can take breaks and resume anytime.

## Quick Start

```bash
# Start the tutorial
paracle tutorial start

# Resume from last checkpoint
paracle tutorial resume

# Check your progress
paracle tutorial status

# Reset and start over
paracle tutorial reset
```

## Commands

### Start Tutorial

Start the tutorial from the beginning:

```bash
paracle tutorial start
```

Or start from a specific step:

```bash
paracle tutorial start --step 3
```

Valid step numbers: 1-6

### Resume Tutorial

Continue from your last checkpoint:

```bash
paracle tutorial resume
```

If you haven't started yet, this will start from Step 1.

### Check Status

View your current progress:

```bash
paracle tutorial status
```

Example output:

```
Tutorial Progress
┌──────┬────────────────────────┬──────────────┐
│ Step │ Name                   │ Status       │
├──────┼────────────────────────┼──────────────┤
│  1   │ Create Agent           │ OK           │
│  2   │ Add Tools              │ OK           │
│  3   │ Add Skills             │ In Progress  │
│  4   │ Create Templates       │ Not Started  │
│  5   │ Test Agent             │ Not Started  │
│  6   │ Create Workflow        │ Not Started  │
└──────┴────────────────────────┴──────────────┘
```

### Reset Progress

Clear your progress and start over:

```bash
paracle tutorial reset
```

You'll be asked to confirm before your progress is deleted.

## Step-by-Step Guide

### Step 1: Create Agent (5 min)

In this step, you'll create your first agent spec:

**What You'll Learn:**
- Agent specification format (Markdown with required sections)
- Governance integration with `.parac/`
- Where agent specs are stored (`.parac/agents/specs/`)

**What Gets Created:**
- `.parac/agents/specs/{agent-name}.md` - Your agent specification

**Option A: Use the CLI (Recommended)**

```bash
# Create agent with governance integration built-in
paracle agents create my-first-agent --role "A helpful coding assistant"

# Validate the agent spec
paracle agents validate my-first-agent
```

**Option B: Copy the Template**

```bash
# Copy the template (has all required sections)
cp .parac/agents/specs/TEMPLATE.md .parac/agents/specs/my-first-agent.md

# Edit the file with your details, then validate
paracle agents validate my-first-agent
```

**Example Agent Spec:**

```markdown
# My First Agent

## Role

A helpful coding assistant that helps with code generation and review.

## Governance Integration

### Before Starting Any Task

1. Read `.parac/memory/context/current_state.yaml` - Current phase & status
2. Check `.parac/roadmap/roadmap.yaml` - Priorities for current phase
3. Review `.parac/memory/context/open_questions.md` - Check for blockers

### After Completing Work

Log action to `.parac/memory/logs/agent_actions.log`:
[TIMESTAMP] [MY-FIRST-AGENT] [ACTION_TYPE] Description

## Skills

- paracle-development
- api-development

## Responsibilities

### Code Implementation

- Generate clean, maintainable code
- Follow project coding standards

### Code Review

- Review code for quality issues
- Suggest improvements
```

**Agent Management Commands:**

```bash
paracle agents list              # List all agents
paracle agents validate          # Validate all specs
paracle agents validate coder    # Validate specific agent
paracle agents format            # Auto-fix common issues
paracle agents format --dry-run  # Preview fixes
paracle agents create <id> -r "role"  # Create from template
```

**Reference Files in `.parac/agents/specs/`:**
- `SCHEMA.md` - Documents required/optional sections
- `TEMPLATE.md` - Copy this to create new agents

### Step 2: Add Tools (5 min)

Select tools to give your agent capabilities:

**What You'll Learn:**
- Built-in tool types
- Tool permissions and safety
- How tools are added to agents

**Available Tools:**

| Tool         | Description                      | Use Case          |
| ------------ | -------------------------------- | ----------------- |
| `filesystem` | Read/write files and directories | Code generation   |
| `http`       | Make HTTP requests               | API integration   |
| `shell`      | Execute shell commands           | System operations |
| `python`     | Run Python code                  | Data processing   |
| `search`     | Search web or documentation      | Research          |

**Example Selection:**

```
Select tools (comma-separated): filesystem, python, search
```

### Step 3: Add Skills (5 min)

Create custom skill modules for specialized knowledge:

**What You'll Learn:**
- Skill structure (YAML + Markdown)
- How skills enhance agent capabilities
- Progressive skill discovery pattern

**What Gets Created:**
- `.parac/agents/skills/{skill-name}/skill.yaml` - Skill metadata
- `.parac/agents/skills/{skill-name}/SKILL.md` - Skill documentation

**Example Skill:**

```yaml
# skill.yaml
name: python-expert
version: "1.0.0"
description: Expert-level Python development knowledge
category: programming

capabilities:
  - Python 3.10+ best practices
  - Async/await patterns
  - Type hints and Pydantic
  - Testing with pytest
```

### Step 4: Create Templates (5 min)

Build reusable project templates:

**What You'll Learn:**
- Template structure
- How templates scaffold new projects
- Template customization

**What Gets Created:**
- `.parac/templates/{template-name}/template.yaml` - Template config
- `.parac/templates/{template-name}/README.md` - Template docs

**Example Template:**

```yaml
name: python-api
description: FastAPI REST API template
structure:
  - app/
  - app/main.py
  - app/models.py
  - tests/
  - requirements.txt
  - README.md
```

### Step 5: Test Agent (7 min)

Configure API keys and test your agent:

**What You'll Learn:**
- API key configuration (.env file)
- Provider setup (OpenAI, Anthropic, etc.)
- Dry-run execution
- Cost estimation

**What Gets Created:**
- `.env` - API key configuration (if not exists)

**Example .env:**

```bash
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Dry Run Output:**

```
Agent: my-first-agent
Provider: openai
Model: gpt-4
Temperature: 0.7

Tools: filesystem, python, search
Skills: python-expert

Estimated Cost: $0.02 per request
```

### Step 6: Create Workflow (3 min)

Orchestrate agents in a workflow:

**What You'll Learn:**
- Workflow YAML format
- Agent coordination
- Input/output passing
- Step dependencies

**What Gets Created:**
- `.parac/workflows/{workflow-name}.yaml` - Workflow definition

**Example Workflow:**

```yaml
name: code-review-workflow
description: Automated code review process
version: "1.0.0"

steps:
  - id: analyze
    agent: my-first-agent
    task: "Analyze the code for issues"
    inputs:
      code: "{{ input.code }}"

  - id: suggest
    agent: my-first-agent
    task: "Suggest improvements"
    inputs:
      analysis: "{{ steps.analyze.output }}"

outputs:
  analysis: "{{ steps.analyze.output }}"
  suggestions: "{{ steps.suggest.output }}"
```

**Run Your Workflow:**

```bash
paracle workflow run code-review-workflow --input code="def hello(): return 'world'"
```

## Progress Tracking

The tutorial automatically saves your progress to:

```
.parac/memory/.tutorial_progress.json
```

**Progress File Format:**

```json
{
  "version": 1,
  "started": "2026-01-07T10:30:00",
  "last_step": 3,
  "checkpoints": {
    "step_1": "completed",
    "step_2": "completed",
    "step_3": "in_progress",
    "step_4": "not_started",
    "step_5": "not_started",
    "step_6": "not_started"
  }
}
```

This file is automatically managed - you don't need to edit it manually.

## Tips & Tricks

### Take Breaks

The tutorial is designed to be pausable:

```bash
# Work on Step 1
paracle tutorial start

# Take a break (progress saved automatically)
# ... do other work ...

# Come back later
paracle tutorial resume
```

### Skip to Specific Step

If you're familiar with earlier concepts:

```bash
# Jump to workflow creation
paracle tutorial start --step 6
```

### Review What You've Built

After completing the tutorial, explore what was created:

```bash
# View your agent
cat .parac/agents/specs/my-first-agent.md

# View your workflow
cat .parac/workflows/my-workflow.yaml

# List your skills
ls -la .parac/agents/skills/

# Check templates
ls -la .parac/templates/
```

### Redo the Tutorial

Want to practice again?

```bash
paracle tutorial reset
paracle tutorial start
```

## Troubleshooting

### "No .parac/ directory found"

Initialize a workspace first:

```bash
paracle init --template lite
paracle tutorial start
```

### "API key not configured"

The tutorial will guide you through API key setup in Step 5. If you encounter issues:

1. Create `.env` file in project root
2. Add your API key: `OPENAI_API_KEY=sk-...`
3. See [API Keys Guide](api-keys.md) for detailed setup

### "Progress file corrupted"

Reset and start over:

```bash
paracle tutorial reset
paracle tutorial start
```

### "Cannot resume - no progress found"

You haven't started the tutorial yet:

```bash
paracle tutorial start
```

## Next Steps

After completing the tutorial:

1. **Explore Examples** - Check out `examples/` directory
2. **Read Documentation** - Deep dive into [Getting Started](getting-started.md)
3. **Build Your First Project** - Use what you learned
4. **Join Community** - Share your experience on Discord

## See Also

- [Getting Started Guide](getting-started.md) - Complete framework overview
- [CLI Reference](cli-reference.md) - All CLI commands
- [Quick Start](quickstart.md) - Alternative quick start path
- [API Keys Guide](api-keys.md) - Configure LLM providers
- [Agent Guide](user-guide/agents.md) - Deep dive on agents
- [Workflow Guide](workflow-guide.md) - Advanced orchestration

---

**Ready to start?**

```bash
paracle tutorial start
```

Happy learning! 🚀
