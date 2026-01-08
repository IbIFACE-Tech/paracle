# paracle_cli

> Command-line interface for the Paracle framework

## Purpose

The `paracle_cli` module provides a comprehensive command-line interface for managing agents, workflows, tools, and all Paracle operations. Built with Click, it offers an intuitive, well-documented CLI with rich output formatting and interactive features.

**Key Features**:
- Complete agent lifecycle management
- Workflow execution and monitoring
- Interactive tutorial system
- Configuration management
- Rich terminal output with progress bars

## Key Components

### 1. Main CLI Entry Point

**Base Command**

```bash
# Show version
paracle --version

# Show help
paracle --help

# Verbose output
paracle --verbose agents list
```

**Global Options**:
- `--version` - Show version
- `--verbose`, `-v` - Enable verbose output
- `--workspace` - Specify workspace root
- `--config` - Use custom config file

### 2. Agent Commands

**List Agents**

```bash
# List all agents
paracle agents list

# Filter by parent
paracle agents list --parent base-developer

# JSON output
paracle agents list --format json
```

**Create Agent**

```bash
# Create agent from spec file
paracle agents create agent.yaml

# Create from template
paracle agents create --template code-reviewer

# Interactive creation
paracle agents create --interactive
```

**Run Agent**

```bash
# Basic execution
paracle agents run coder --task "Fix bug in auth.py"

# With execution mode
paracle agents run coder --task "Refactor module" --mode safe

# YOLO mode (auto-approve)
paracle agents run reviewer --task "Review PR" --mode yolo

# Sandbox mode
paracle agents run tester --task "Run tests" --mode sandbox

# With input files
paracle agents run documenter --task "Document API" --file api.py

# Stream output
paracle agents run coder --task "Implement feature" --stream

# Set cost limit
paracle agents run architect --task "Design system" --cost-limit 10.00

# Save output
paracle agents run coder --task "Generate code" --output result.json
```

**Agent Options**:
- `--mode` - Execution mode (safe, yolo, sandbox, review)
- `--task`, `-t` - Task description
- `--file`, `-f` - Input files (multiple allowed)
- `--input`, `-i` - Key=value inputs
- `--model` - Override model
- `--provider` - Override provider
- `--temperature` - Override temperature
- `--cost-limit` - Maximum cost in USD
- `--output`, `-o` - Save output file
- `--stream` / `--no-stream` - Stream output
- `--timeout` - Execution timeout
- `--dry-run` - Validate without executing

**Show Agent**

```bash
# Show agent details
paracle agents show coder

# Show with inheritance chain
paracle agents show python-expert --resolve
```

**Delete Agent**

```bash
# Delete agent
paracle agents delete old-agent

# Force delete (skip confirmation)
paracle agents delete old-agent --force
```

### 3. Workflow Commands

**List Workflows**

```bash
# List all workflows
paracle workflows list

# Filter by status
paracle workflows list --status active
```

**Run Workflow**

```bash
# Run workflow
paracle workflows run code-review

# With inputs
paracle workflows run feature-dev --input file=api.py --input priority=high

# With specific agents
paracle workflows run bugfix --agent-override coder=python-expert
```

**Show Workflow**

```bash
# Show workflow details
paracle workflows show code-review

# Show execution history
paracle workflows show code-review --history
```

### 4. Tutorial Commands

**Start Tutorial**

```bash
# Start interactive tutorial
paracle tutorial start

# Resume from checkpoint
paracle tutorial resume

# Specific lesson
paracle tutorial lesson agent-basics

# List lessons
paracle tutorial list
```

**Tutorial Features**:
- 📚 **10 Lessons** covering all Paracle features
- ✅ **Interactive** - Hands-on exercises
- 🎯 **Checkpoints** - Save progress
- 💡 **Hints** - Built-in help system
- 🏆 **Completion Tracking** - See your progress

### 5. Configuration Commands

**Show Configuration**

```bash
# Show current config
paracle config show

# Show specific key
paracle config get database_url
```

**Set Configuration**

```bash
# Set configuration value
paracle config set log_level DEBUG

# Set nested value
paracle config set providers.openai.model gpt-4-turbo
```

**Initialize Workspace**

```bash
# Initialize .parac/ workspace
paracle init

# With template
paracle init --template python-project

# Custom location
paracle init --workspace /path/to/project
```

### 6. Tool Commands

**List Tools**

```bash
# List all available tools
paracle tools list

# Filter by category
paracle tools list --category filesystem
```

**Show Tool**

```bash
# Show tool details
paracle tools show filesystem_read

# Show with examples
paracle tools show filesystem_read --examples
```

**Test Tool**

```bash
# Test tool execution
paracle tools test filesystem_read --args path=test.txt
```

### 7. Worker Commands

**Start Worker**

```bash
# Start background worker
paracle worker start

# With specific queues
paracle worker start --queues agent,workflow

# Number of workers
paracle worker start --workers 4
```

**Stop Worker**

```bash
# Stop worker
paracle worker stop

# Force stop
paracle worker stop --force
```

**Worker Status**

```bash
# Show worker status
paracle worker status

# Show with metrics
paracle worker status --metrics
```

### 8. MCP Commands

**Start MCP Server**

```bash
# Start MCP server (stdio)
paracle mcp serve --stdio

# With SSE transport
paracle mcp serve --sse --port 8080

# With WebSocket
paracle mcp serve --websocket --port 9000
```

**List MCP Tools**

```bash
# List available MCP tools
paracle mcp tools

# Show tool schema
paracle mcp tools filesystem_read --schema
```

### 9. IDE Commands

**Build IDE Configuration**

```bash
# Build all IDE configs
paracle ide build --target all

# Specific IDE
paracle ide build --target vscode

# Copy to clipboard
paracle ide build --target vscode --copy
```

**Sync IDE Configuration**

```bash
# Sync .parac/ to IDE configs
paracle ide sync --copy
```

### 10. Cost Tracking Commands

**Show Costs**

```bash
# Show all costs
paracle costs show

# Filter by date
paracle costs show --since 2026-01-01

# Filter by agent
paracle costs show --agent coder

# Summary view
paracle costs summary

# Export to CSV
paracle costs export --format csv --output costs.csv
```

## Module Structure

```
paracle_cli/
├── __init__.py              # Package exports
├── main.py                  # CLI entry point
├── commands/                # Command groups
│   ├── __init__.py
│   ├── agents.py           # Agent commands
│   ├── workflows.py        # Workflow commands
│   ├── tutorial.py         # Tutorial commands
│   ├── config.py           # Config commands
│   ├── tools.py            # Tool commands
│   ├── workers.py          # Worker commands
│   ├── mcp.py              # MCP commands
│   ├── ide.py              # IDE commands
│   └── costs.py            # Cost commands
├── utils/                   # CLI utilities
│   ├── __init__.py
│   ├── output.py           # Output formatting
│   ├── progress.py         # Progress bars
│   ├── prompts.py          # Interactive prompts
│   └── tables.py           # Table formatting
└── tutorial/                # Tutorial system
    ├── __init__.py
    ├── engine.py           # Tutorial engine
    ├── lessons/            # Lesson content
    └── checkpoints.py      # Progress tracking
```

## Usage Examples

### Complete Agent Workflow

```bash
# 1. Initialize workspace
paracle init

# 2. Create agent
paracle agents create --interactive
# Name: python-expert
# Provider: openai
# Model: gpt-4
# ...

# 3. Run agent
paracle agents run python-expert --task "Review code" --file api.py

# 4. Check costs
paracle costs show --agent python-expert

# 5. Show agent details
paracle agents show python-expert
```

### Workflow Execution

```bash
# 1. List workflows
paracle workflows list

# 2. Run workflow
paracle workflows run code-review \
  --input file=src/api.py \
  --input focus=security

# 3. Monitor execution
paracle workflows show code-review --history

# 4. Check results
paracle workflows show code-review --output
```

### Interactive Tutorial

```bash
# Start tutorial
paracle tutorial start

# 📚 Lesson 1: Introduction to Paracle
# Learn about agents, workflows, and tools...
#
# Exercise: Create your first agent
# > paracle agents create --interactive
#
# ✅ Checkpoint saved!

# Resume later
paracle tutorial resume

# Skip to specific lesson
paracle tutorial lesson workflow-basics
```

### Development Workflow

```bash
# 1. Create development agent
paracle agents create dev-agent.yaml

# 2. Test in sandbox mode
paracle agents run dev-agent \
  --task "Test new feature" \
  --mode sandbox \
  --verbose

# 3. Review output
cat .parac/runs/agents/dev-agent/latest/output.json

# 4. If good, run in safe mode
paracle agents run dev-agent \
  --task "Implement feature" \
  --mode safe
```

## Dependencies

**Required Packages**:
```toml
[project.dependencies]
click = "^8.1"              # CLI framework
rich = "^13.7"              # Terminal formatting
pydantic = "^2.5"           # Data validation
```

**Optional Packages**:
```toml
[project.optional-dependencies]
cli = [
    "questionary ^2.0",     # Interactive prompts
    "tabulate ^0.9",        # Table formatting
    "colorama ^0.4",        # Windows color support
]
```

**Internal Dependencies**:
- `paracle_core` - Core utilities
- `paracle_domain` - Domain models
- `paracle_orchestration` - Workflow execution
- `paracle_store` - Data persistence

## Output Formatting

### Rich Output

**Tables**:
```
┌────────────┬───────────────┬──────────┬─────────┐
│ Name       │ Provider      │ Model    │ Status  │
├────────────┼───────────────┼──────────┼─────────┤
│ coder      │ openai        │ gpt-4    │ active  │
│ reviewer   │ anthropic     │ claude-3 │ active  │
│ tester     │ openai        │ gpt-3.5  │ active  │
└────────────┴───────────────┴──────────┴─────────┘
```

**Progress Bars**:
```
Executing workflow... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 75% 3/4 steps
```

**Tree Views**:
```
code-review-workflow
├── analyze (static-analyzer) ✓ Complete
├── review (code-reviewer) ⟳ Running
└── report (documenter) ⏸ Pending
```

### JSON Output

```bash
paracle agents list --format json
```

```json
[
  {
    "name": "coder",
    "provider": "openai",
    "model": "gpt-4",
    "status": "active",
    "created_at": "2026-01-07T10:00:00Z"
  }
]
```

### Plain Text Output

```bash
paracle agents list --format plain
```

```
coder openai gpt-4 active
reviewer anthropic claude-3 active
tester openai gpt-3.5 active
```

## Error Handling

### User-Friendly Errors

```bash
$ paracle agents run unknown-agent --task "test"
Error: Agent 'unknown-agent' not found

Available agents:
  - coder
  - reviewer
  - tester

Try: paracle agents create unknown-agent
```

### Validation Errors

```bash
$ paracle agents create invalid.yaml
Error: Invalid agent specification
  - name: Field required
  - provider: Invalid provider 'invalid-llm'

See: paracle agents create --help
```

## Environment Variables

```bash
# Workspace location
export PARACLE_WORKSPACE_ROOT=/path/to/workspace

# Log level
export PARACLE_LOG_LEVEL=DEBUG

# Config file
export PARACLE_CONFIG_FILE=/path/to/config.yaml

# Disable colors
export NO_COLOR=1

# Force colors
export FORCE_COLOR=1
```

## Testing

### Unit Tests

```python
from click.testing import CliRunner
from paracle_cli.main import cli

def test_agents_list():
    runner = CliRunner()
    result = runner.invoke(cli, ['agents', 'list'])
    assert result.exit_code == 0
    assert 'coder' in result.output

def test_agents_run():
    runner = CliRunner()
    result = runner.invoke(cli, [
        'agents', 'run', 'coder',
        '--task', 'Test task',
        '--dry-run'
    ])
    assert result.exit_code == 0
```

### Integration Tests

```python
def test_complete_workflow(tmp_path):
    runner = CliRunner()

    # Init workspace
    result = runner.invoke(cli, ['init'], cwd=tmp_path)
    assert result.exit_code == 0

    # Create agent
    agent_yaml = tmp_path / 'agent.yaml'
    agent_yaml.write_text("""
    name: test-agent
    provider: openai
    model: gpt-4
    """)

    result = runner.invoke(cli, ['agents', 'create', str(agent_yaml)])
    assert result.exit_code == 0

    # List agents
    result = runner.invoke(cli, ['agents', 'list'])
    assert 'test-agent' in result.output
```

## See Also

- [CLI Reference](../cli-reference.md) - Complete command reference
- [Quick Start](../quickstart.md) - Getting started guide
- [Tutorial](../tutorial.md) - Interactive tutorial
- [Agent Execution](../agent-run-quickref.md) - Agent run guide

---

**Module Type**: Interface
**Dependencies**: paracle_core, paracle_domain, paracle_orchestration
**Status**: Stable
**Version**: 0.0.1

