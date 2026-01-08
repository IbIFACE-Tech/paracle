# CLI Reference

Command-line interface for `paracle_meta`.

## Overview

```bash
paracle meta [COMMAND] [OPTIONS]
```

## Commands

### `paracle meta health`

Check the health of the meta engine.

```bash
paracle meta health
```

**Output:**
```
Meta Engine Health Check
========================

Status: HEALTHY

Components:
  database: healthy (PostgreSQL connected)
  providers: healthy
    - anthropic: up (claude-sonnet-4-20250514)
    - openai: up (gpt-4o)
  learning_engine: healthy (enabled, 42 templates)
  cost_tracker: healthy (daily: $2.50/$10.00, monthly: $45.00/$100.00)

Version: 1.5.0
Uptime: 2h 34m 12s
```

**Options:**
- `--json` - Output as JSON
- `--verbose` - Show detailed diagnostics

---

### `paracle meta chat`

Start an interactive chat session with AI assistance.

```bash
paracle meta chat [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--provider` | LLM provider to use | `anthropic` |
| `--model` | Specific model | Provider default |
| `--resume` | Resume last session | `false` |
| `--session-id` | Resume specific session | - |
| `--system` | Custom system prompt | Default |
| `--temperature` | Model temperature | `0.7` |

**Examples:**

```bash
# Start new chat with default provider
paracle meta chat

# Use specific provider
paracle meta chat --provider openai --model gpt-4o

# Resume previous session
paracle meta chat --resume

# Resume specific session by ID
paracle meta chat --session-id abc123

# Custom system prompt
paracle meta chat --system "You are a Python expert."
```

**Interactive Commands:**
- `/help` - Show available commands
- `/clear` - Clear conversation history
- `/save` - Save session
- `/load <id>` - Load session
- `/history` - Show conversation history
- `/exit` or `/quit` - Exit chat

---

### `paracle meta plan`

Plan and execute complex tasks with AI.

```bash
paracle meta plan [TASK] [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--provider` | LLM provider to use | `anthropic` |
| `--resume` | Resume last plan | `false` |
| `--execute` | Execute the plan | `false` |
| `--dry-run` | Show plan without executing | `false` |
| `--verbose` | Detailed output | `false` |

**Examples:**

```bash
# Create a plan for a task
paracle meta plan "Build a REST API with FastAPI"

# Resume and continue planning
paracle meta plan --resume

# Execute the plan
paracle meta plan --execute

# Dry run to see what would be executed
paracle meta plan --dry-run
```

**Plan Steps:**
1. **Analysis** - Understand the task requirements
2. **Decomposition** - Break into subtasks
3. **Planning** - Create step-by-step plan
4. **Review** - User reviews and approves
5. **Execution** - Execute plan steps (if `--execute`)

---

### `paracle meta generate`

Generate Paracle artifacts from descriptions.

```bash
paracle meta generate [TYPE] [OPTIONS]
```

**Types:**
- `agent` - Generate agent specification
- `workflow` - Generate workflow definition
- `skill` - Generate skill definition
- `policy` - Generate policy definition

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--name` | Name for the artifact | Required |
| `--description` | Description/requirements | Required |
| `--output` | Output file path | stdout |
| `--format` | Output format (yaml/json) | `yaml` |
| `--provider` | LLM provider | `anthropic` |

**Examples:**

```bash
# Generate an agent
paracle meta generate agent \
  --name SecurityAuditor \
  --description "Reviews code for security vulnerabilities"

# Generate a workflow
paracle meta generate workflow \
  --name PRReview \
  --description "Automated PR review workflow"

# Generate to file
paracle meta generate agent \
  --name Coder \
  --description "Python coding assistant" \
  --output .parac/agents/specs/coder.yaml
```

---

### `paracle meta config`

Manage configuration.

```bash
paracle meta config [SUBCOMMAND]
```

**Subcommands:**

```bash
# Show current configuration
paracle meta config show

# Validate configuration
paracle meta config validate

# Show configuration file path
paracle meta config path

# Create example configuration
paracle meta config init
```

---

### `paracle meta stats`

Show usage statistics.

```bash
paracle meta stats [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--period` | Time period (day/week/month) | `day` |
| `--provider` | Filter by provider | All |
| `--json` | Output as JSON | `false` |

**Output:**
```
Usage Statistics (Today)
========================

Requests: 42
Tokens: 125,430 (in: 45,230, out: 80,200)
Cost: $2.50

By Provider:
  anthropic: 30 requests, $1.80
  openai: 12 requests, $0.70

Quality:
  Average score: 8.2/10
  High quality: 85%
  Retries: 3
```

---

### `paracle meta templates`

Manage template library.

```bash
paracle meta templates [SUBCOMMAND]
```

**Subcommands:**

```bash
# List all templates
paracle meta templates list

# Show template details
paracle meta templates show <template-id>

# Search templates
paracle meta templates search "security audit"

# Export template
paracle meta templates export <template-id> --output template.yaml

# Import template
paracle meta templates import template.yaml
```

---

### `paracle meta feedback`

Submit feedback for generations.

```bash
paracle meta feedback [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--generation-id` | Generation to rate | Last |
| `--rating` | Rating 1-5 | Required |
| `--comment` | Optional comment | - |

**Examples:**

```bash
# Rate last generation
paracle meta feedback --rating 5 --comment "Excellent!"

# Rate specific generation
paracle meta feedback --generation-id abc123 --rating 4
```

---

## Global Options

Available for all commands:

| Option | Description |
|--------|-------------|
| `--help` | Show help message |
| `--version` | Show version |
| `--verbose` | Verbose output |
| `--quiet` | Minimal output |
| `--config` | Path to config file |

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | Provider error |
| 4 | Database error |
| 5 | User cancelled |

## Environment Variables

```bash
# Override default provider
PARACLE_META_DEFAULT_PROVIDER=openai

# Set API keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Enable verbose output
PARACLE_META_VERBOSE=true
```
