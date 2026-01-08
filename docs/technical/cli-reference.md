# Paracle CLI Reference

Complete command reference for the Paracle CLI.

## Overview

The Paracle CLI provides command-line access to all framework features. It follows an API-first architecture, using REST endpoints when available and falling back to local execution.

```bash
paracle --help
```

## Global Options

| Option      | Description           |
| ----------- | --------------------- |
| `--version` | Show version and exit |
| `--help`    | Show help message     |

---

## Commands

### hello

Test installation and show welcome message.

```bash
paracle hello
```

**Output:**
```
Paracle v0.0.1

Framework successfully installed!

Get started:
  paracle init              - Initialize a project
  paracle agents list       - List available agents
  paracle agents run coder -t 'Fix bug'  - Run an agent
  paracle --help            - Show all commands
```

---

### init

Initialize a new `.parac/` workspace with template-based configuration.

```bash
paracle init [PATH] [OPTIONS]
```

**Arguments:**

| Argument | Default | Description                                        |
| -------- | ------- | -------------------------------------------------- |
| `PATH`   | `.`     | Directory to initialize (created if doesn't exist) |

**Options:**

| Option                | Description                                    |
| --------------------- | ---------------------------------------------- |
| `--name NAME`         | Project name (defaults to directory name)      |
| `--template TEMPLATE` | Template tier: lite, standard, or advanced     |
| `-i, --interactive`   | Interactive prompts for template/name/provider |
| `-v, --verbose`       | Show detailed progress output                  |
| `--force`             | Overwrite existing workspace                   |
| `--lite`              | (Deprecated) Use --template lite               |
| `--all`               | (Deprecated) Use --template advanced           |

**Templates:**

| Template   | Agents | Database   | Features                     | Best For      |
| ---------- | ------ | ---------- | ---------------------------- | ------------- |
| `lite`     | 1      | File-based | Zero dependencies, < 2 min   | Learning      |
| `standard` | 2-3    | SQLite     | Production-ready             | Most projects |
| `advanced` | 8      | PostgreSQL | Docker, CI/CD, full policies | Enterprise    |

**Example:**

```bash
# Interactive mode (recommended for first-time users)
paracle init -i

# Quick start - lite template
paracle init --template lite

# Standard workspace (default)
paracle init my-project --template standard

# Enterprise with all features
paracle init --template advanced

# Interactive + verbose (see what's happening)
paracle init -i -v

# Non-interactive with specific template
paracle init my-project --name "My Project" --template advanced

# Overwrite existing workspace
paracle init --force --template standard

# Legacy syntax (still works)
paracle init --lite  # → --template lite
paracle init --all   # → --template advanced
```

**Workspace Structure (--lite):**

```text
.parac/
├── .gitignore                # Git ignore patterns
├── project.yaml              # Project config
├── changelog.md              # Project changelog
│
├── agents/
│   ├── manifest.yaml         # Agent registry
│   ├── SKILL_ASSIGNMENTS.md  # Skill-to-agent mapping
│   ├── specs/
│   │   └── myagent.md        # Sample agent
│   └── skills/
│       ├── README.md
│       └── my-first-skill/   # Sample skill folder
│
├── memory/
│   ├── index.yaml            # Memory index
│   ├── context/
│   │   ├── current_state.yaml
│   │   └── open_questions.md
│   └── logs/
│       ├── README.md
│       ├── agent_actions.log
│       └── decisions.log
│
├── roadmap/
│   ├── roadmap.yaml          # Project roadmap
│   ├── decisions.md          # ADR index
│   └── constraints.yaml      # Project constraints
│
├── tools/
│   ├── README.md
│   ├── registry.yaml         # Tool registry
│   ├── custom/               # Custom tools
│   └── builtin/              # Built-in tools
│
└── integrations/
    ├── README.md
    └── ide/
        └── _manifest.yaml    # IDE manifest
```

**Workspace Structure (default):**

```text
.parac/
├── GOVERNANCE.md
├── memory/
│   ├── context/
│   ├── knowledge/
│   ├── summaries/
│   └── logs/
├── roadmap/
├── agents/
│   ├── specs/
│   └── skills/
├── policies/
├── tools/hooks/
├── adapters/
└── integrations/ide/
```

**Workspace Structure (--all):**

Includes all of the above plus:

- Default agents (coder, reviewer)
- Policy templates (CODE_STYLE.md, TESTING.md, SECURITY.md)
- ADR templates
- Workflow templates
- Full directory structure with runtime logs

---

### status

Show current project state from `.parac/`.

```bash
paracle status [OPTIONS]
```

**Options:**
| Option   | Description    |
| -------- | -------------- |
| `--json` | Output as JSON |

**Example:**
```bash
paracle status
paracle status --json
```

---

### serve

Start the Paracle API server.

```bash
paracle serve [OPTIONS]
```

**Options:**
| Option     | Default   | Description        |
| ---------- | --------- | ------------------ |
| `--host`   | 127.0.0.1 | Host to bind       |
| `--port`   | 8000      | Port to bind       |
| `--reload` | false     | Enable auto-reload |

**Example:**
```bash
paracle serve
paracle serve --port 8080 --host 0.0.0.0
paracle serve --reload  # Development mode
```

---

## Interactive Learning

### tutorial

Interactive onboarding tutorial for new users. Guides you through creating agents, adding tools, skills, templates, testing, and workflows.

```bash
paracle tutorial [COMMAND]
```

**Commands:**

#### tutorial start

Start the interactive tutorial from the beginning or a specific step.

```bash
paracle tutorial start [OPTIONS]
```

**Options:**

| Option        | Description                    |
| ------------- | ------------------------------ |
| `--step STEP` | Start from specific step (1-6) |

**Example:**

```bash
# Start from beginning
paracle tutorial start

# Start from step 3 (Add Skills)
paracle tutorial start --step 3
```

#### tutorial resume

Resume the tutorial from your last checkpoint.

```bash
paracle tutorial resume
```

**Example:**

```bash
paracle tutorial resume
```

#### tutorial status

Show your current tutorial progress.

```bash
paracle tutorial status
```

**Example:**

```bash
paracle tutorial status
```

**Output:**

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

#### tutorial reset

Reset tutorial progress (with confirmation).

```bash
paracle tutorial reset
```

**Example:**

```bash
paracle tutorial reset
# Prompts: "Reset tutorial progress? This will delete your checkpoint. [y/N]:"
```

**Tutorial Steps:**

The interactive tutorial covers 6 steps (~30 minutes):

1. **Create Agent** (5 min) - Interactive prompts to create your first agent spec
2. **Add Tools** (5 min) - Select from built-in tools (filesystem, http, shell, python, search)
3. **Add Skills** (5 min) - Create custom skill modules with YAML + Markdown
4. **Create Templates** (5 min) - Build reusable project templates
5. **Test Agent** (7 min) - Configure API keys, run dry-run execution
6. **Create Workflow** (3 min) - Generate workflow YAML with agent orchestration

Progress is automatically saved to `.parac/memory/.tutorial_progress.json`.

---

## Agent Commands

### agents list

List all agents defined in `.parac/agents/specs/`.

```bash
paracle agents list [OPTIONS]
```

**Options:**
| Option   | Description    |
| -------- | -------------- |
| `--json` | Output as JSON |

**Example:**
```bash
paracle agents list
paracle agents list --json
```

### agents get

Get details for a specific agent.

```bash
paracle agents get NAME [OPTIONS]
```

**Options:**
| Option   | Description    |
| -------- | -------------- |
| `--json` | Output as JSON |

**Example:**
```bash
paracle agents get code-reviewer
paracle agents get code-reviewer --json
```

### agents export

Export all agents to JSON or YAML.

```bash
paracle agents export [OPTIONS]
```

**Options:**
| Option     | Default | Description               |
| ---------- | ------- | ------------------------- |
| `--format` | json    | Output format (json/yaml) |
| `--output` | stdout  | Output file path          |

**Example:**
```bash
paracle agents export
paracle agents export --format yaml --output agents.yaml
```

---

## Workflow Commands

### workflow list

List all workflows.

```bash
paracle workflow list [OPTIONS]
```

**Options:**
| Option   | Description    |
| -------- | -------------- |
| `--json` | Output as JSON |

### workflow run

Execute a workflow.

```bash
paracle workflow run WORKFLOW_ID [OPTIONS]
```

**Options:**
| Option                  | Description                  |
| ----------------------- | ---------------------------- |
| `-i, --input KEY=VALUE` | Input parameter (repeatable) |
| `--sync`                | Run synchronously            |
| `--watch`               | Watch execution progress     |
| `--timeout SECONDS`     | Execution timeout            |

**Example:**
```bash
paracle workflow run code-review -i code="def hello(): pass"
paracle workflow run deploy --watch
paracle workflow run test --sync --timeout 300
```

### workflow status

Check workflow execution status.

```bash
paracle workflow status EXECUTION_ID
```

**Example:**
```bash
paracle workflow status exec_abc123
```

### workflow cancel

Cancel a running workflow execution.

```bash
paracle workflow cancel EXECUTION_ID
```

**Example:**
```bash
paracle workflow cancel exec_abc123
```

---

## Tools Commands

### tools list

List all available tools.

```bash
paracle tools list [OPTIONS]
```

**Options:**
| Option       | Description        |
| ------------ | ------------------ |
| `--category` | Filter by category |
| `--json`     | Output as JSON     |

**Example:**
```bash
paracle tools list
paracle tools list --category filesystem
```

**Output:**
```
                        Available Tools
+----------------------------------------------------------------------+
| Name             | Category   | Description              | Source   |
|------------------+------------+--------------------------+----------|
| read_file        | filesystem | Read the contents of ... | builtin  |
| write_file       | filesystem | Write content to a file  | builtin  |
| list_directory   | filesystem | List contents of a dir   | builtin  |
| delete_file      | filesystem | Delete a file            | builtin  |
| http_get         | http       | Make HTTP GET request    | builtin  |
| http_post        | http       | Make HTTP POST request   | builtin  |
| http_put         | http       | Make HTTP PUT request    | builtin  |
| http_delete      | http       | Make HTTP DELETE request | builtin  |
| run_command      | shell      | Execute a shell command  | builtin  |
+----------------------------------------------------------------------+

Total: 9 tools
Built-in: 9 | MCP: 0
```

### tools info

Show detailed information about a tool.

```bash
paracle tools info TOOL_NAME
```

**Example:**
```bash
paracle tools info read_file
```

### tools test

Test a tool with sample parameters.

```bash
paracle tools test TOOL_NAME [OPTIONS]
```

**Options:**
| Option              | Description                 |
| ------------------- | --------------------------- |
| `--param KEY=VALUE` | Tool parameter (repeatable) |

**Example:**
```bash
paracle tools test read_file --param path=README.md
paracle tools test http_get --param url=https://api.github.com
```

### tools register

Register a custom tool from spec file.

```bash
paracle tools register SPEC_FILE
```

---

## Provider Commands

### providers list

List all available LLM providers.

```bash
paracle providers list [OPTIONS]
```

**Options:**
| Option   | Description    |
| -------- | -------------- |
| `--json` | Output as JSON |

**Output:**
```
                          LLM Providers
+----------------------------------------------------------------------+
| Provider        | Status     | Models                               |
|-----------------+------------+--------------------------------------|
| OpenAI          | available  | gpt-4, gpt-3.5-turbo                 |
| Anthropic       | available  | claude-3-opus, claude-3-sonnet       |
| Google Gemini   | available  | gemini-pro                           |
| Ollama (Local)  | registered | llama2, mistral, codellama           |
+----------------------------------------------------------------------+

Registered: 11 | Available: 4
```

### providers add

Register a new provider.

```bash
paracle providers add PROVIDER [OPTIONS]
```

**Options:**
| Option       | Description              |
| ------------ | ------------------------ |
| `--api-key`  | API key for the provider |
| `--base-url` | Custom base URL          |

**Example:**
```bash
paracle providers add anthropic --api-key sk-ant-xxx
paracle providers add ollama --base-url http://localhost:11434
```

### providers test

Test provider connection and model availability.

```bash
paracle providers test PROVIDER [OPTIONS]
```

**Options:**
| Option    | Description            |
| --------- | ---------------------- |
| `--model` | Specific model to test |

**Example:**
```bash
paracle providers test openai
paracle providers test anthropic --model claude-3-sonnet
```

### providers default

Set or show default provider.

```bash
paracle providers default [PROVIDER]
```

**Example:**
```bash
paracle providers default          # Show current default
paracle providers default openai   # Set default
```

---

## Log Commands

### logs list

List available log files.

```bash
paracle logs list
```

### logs show

Show log contents.

```bash
paracle logs show [LOG_NAME] [OPTIONS]
```

**Options:**
| Option         | Default | Description             |
| -------------- | ------- | ----------------------- |
| `-n, --tail`   | 50      | Number of lines to show |
| `-f, --follow` | false   | Follow log output       |
| `--json`       | false   | Output as JSON          |
| `-g, --filter` |         | Filter lines by pattern |

**Example:**
```bash
paracle logs show                    # Show actions log
paracle logs show -n 100             # Show last 100 lines
paracle logs show -f                 # Follow in real-time
paracle logs show -g "ERROR"         # Filter for errors
paracle logs show decisions          # Show decisions log
```

### logs clear

Clear a log file.

```bash
paracle logs clear [LOG_NAME] [OPTIONS]
```

**Options:**
| Option        | Description       |
| ------------- | ----------------- |
| `-f, --force` | Skip confirmation |

### logs export

Export logs to file.

```bash
paracle logs export [LOG_NAME] [OPTIONS]
```

**Options:**
| Option         | Default | Description                   |
| -------------- | ------- | ----------------------------- |
| `-o, --output` | auto    | Output file path              |
| `-f, --format` | json    | Format (json/csv/ndjson)      |
| `--from-date`  |         | Filter from date (YYYY-MM-DD) |
| `--to-date`    |         | Filter to date (YYYY-MM-DD)   |

### logs audit

Show audit log (ISO 42001 compliance trail).

```bash
paracle logs audit [OPTIONS]
```

**Options:**
| Option           | Default | Description        |
| ---------------- | ------- | ------------------ |
| `-n, --tail`     | 50      | Number of entries  |
| `-c, --category` |         | Filter by category |
| `-s, --severity` |         | Filter by severity |

---

## IDE Commands

### ide list

List supported IDEs.

```bash
paracle ide list
```

**Output:**
```
Supported IDEs:

| IDE            | File             | Destination |
| -------------- | ---------------- | ----------- |
| Cursor         | .cursorrules     | ./          |
| Claude Code    | CLAUDE.md        | .claude/    |
| Cline          | .clinerules      | ./          |
| GitHub Copilot | copilot-instr... | .github/    |
| Windsurf       | .windsurfrules   | ./          |
```

### ide init

Initialize IDE configuration files.

```bash
paracle ide init [OPTIONS]
```

**Options:**
| Option             | Description                          |
| ------------------ | ------------------------------------ |
| `--ide NAME`       | IDE(s) to initialize (repeatable)    |
| `--force`          | Overwrite existing files             |
| `--copy/--no-copy` | Copy to project root (default: copy) |

**Example:**
```bash
paracle ide init --ide=cursor
paracle ide init --ide=all
paracle ide init --ide=cursor --ide=claude --force
```

### ide status

Show IDE integration status.

```bash
paracle ide status [OPTIONS]
```

**Options:**
| Option   | Description    |
| -------- | -------------- |
| `--json` | Output as JSON |

### ide sync

Synchronize IDE configs with `.parac/` state.

```bash
paracle ide sync [OPTIONS]
```

**Options:**
| Option             | Description          |
| ------------------ | -------------------- |
| `--copy/--no-copy` | Copy to project root |
| `--watch`          | Watch for changes    |

### ide build

Build native agent files for IDEs.

```bash
paracle ide build --target TARGET [OPTIONS]
```

**Options:**
| Option             | Description                                              |
| ------------------ | -------------------------------------------------------- |
| `--target`         | Target IDE: vscode, claude, cursor, windsurf, codex, all |
| `--copy/--no-copy` | Copy to expected IDE locations (default: copy)           |
| `--output`         | Custom output directory                                  |

**Example:**
```bash
paracle ide build --target vscode
paracle ide build --target all --copy
paracle ide build --target claude --no-copy --output ./custom/
```

---

## MCP Commands

### mcp serve

Start MCP server exposing Paracle tools.

```bash
paracle mcp serve [OPTIONS]
```

**Options:**
| Option    | Default | Description                               |
| --------- | ------- | ----------------------------------------- |
| `--stdio` | false   | Use stdio transport (for IDE integration) |
| `--port`  | 3000    | HTTP port (when not using stdio)          |

**Example:**
```bash
paracle mcp serve --stdio    # For IDE integration (recommended)
paracle mcp serve --port 3000  # For debugging/testing
```

### mcp list

List available MCP tools.

```bash
paracle mcp list [OPTIONS]
```

**Options:**
| Option       | Description                                               |
| ------------ | --------------------------------------------------------- |
| `--json`     | Output as JSON                                            |
| `--category` | Filter by category: agent, context, workflow, memory, all |

### mcp config

Show MCP configuration for IDEs.

```bash
paracle mcp config [OPTIONS]
```

**Options:**
| Option  | Description                                                    |
| ------- | -------------------------------------------------------------- |
| `--ide` | Show config for specific IDE: vscode, cursor, windsurf, claude |

---

## Agent Run Command

### agents run

Run a single agent for a specific task.

```bash
paracle agents run AGENT_NAME --task "TASK" [OPTIONS]
```

**Required:**
| Option       | Description                     |
| ------------ | ------------------------------- |
| `--task, -t` | Task description or instruction |

**Execution Options:**
| Option       | Default | Description                                 |
| ------------ | ------- | ------------------------------------------- |
| `--mode, -m` | safe    | Execution mode: safe, yolo, sandbox, review |
| `--timeout`  | 300     | Timeout in seconds                          |
| `--dry-run`  | false   | Validate without executing                  |

**LLM Configuration:**
| Option          | Description                                                |
| --------------- | ---------------------------------------------------------- |
| `--model`       | Model name (e.g., gpt-4, claude-3-opus)                    |
| `--provider`    | Provider: openai, anthropic, google, mistral, groq, ollama |
| `--temperature` | Temperature 0.0-2.0                                        |
| `--max-tokens`  | Maximum tokens to generate                                 |

**Inputs:**
| Option        | Description                        |
| ------------- | ---------------------------------- |
| `--input, -i` | Key=value pairs (multiple allowed) |
| `--file, -f`  | Input files (multiple allowed)     |

**Cost & Output:**
| Option                 | Description                     |
| ---------------------- | ------------------------------- |
| `--cost-limit`         | Maximum cost in USD             |
| `--output, -o`         | Save output to JSON file        |
| `--stream/--no-stream` | Stream output (default: stream) |
| `--verbose, -v`        | Show detailed information       |

**Examples:**
```bash
# Basic code review
paracle agents run reviewer --task "Review changes in src/app.py"

# Bug fix with yolo mode (auto-approve all actions)
paracle agents run coder --task "Fix memory leak" --mode yolo

# Sandboxed execution (safe environment)
paracle agents run tester --task "Run integration tests" --mode sandbox

# With custom model and inputs
paracle agents run architect \
    --task "Design auth system" \
    --model gpt-4-turbo \
    --input feature=authentication \
    --input users=1000000

# Cost-limited execution
paracle agents run coder \
    --task "Implement feature X" \
    --cost-limit 2.50 \
    --output result.json
```

---

## Session Commands

### session start

Start a new work session.

```bash
paracle session start [OPTIONS]
```

**Options:**
| Option    | Description            |
| --------- | ---------------------- |
| `--name`  | Session name           |
| `--focus` | Focus area description |

### session end

End work session with `.parac/` updates.

```bash
paracle session end [OPTIONS]
```

**Options:**
| Option        | Description          |
| ------------- | -------------------- |
| `--summary`   | Session summary      |
| `--no-update` | Skip .parac/ updates |

---

## Validation Commands

### validate

Validate governance compliance and structure.

```bash
paracle validate [OPTIONS]
```

**Options:**
| Option  | Description               |
| ------- | ------------------------- |
| `--all` | Run all validation checks |

### validate governance

Validate `.parac/` directory structure and files.

```bash
paracle validate governance
```

### validate roadmap

Validate roadmap consistency.

```bash
paracle validate roadmap
```

### validate ai-instructions

Validate AI instruction files have pre-flight checklist.

```bash
paracle validate ai-instructions
```

---

## Sync Commands

### sync

Synchronize `.parac/` state with project reality.

```bash
paracle sync [OPTIONS]
```

**Options:**
| Option      | Description                   |
| ----------- | ----------------------------- |
| `--dry-run` | Show changes without applying |
| `--force`   | Force sync even if conflicts  |

---

## Environment Variables

| Variable               | Description                                     |
| ---------------------- | ----------------------------------------------- |
| `PARACLE_API_URL`      | API server URL (default: http://localhost:8000) |
| `PARACLE_LOG_LEVEL`    | Log level (DEBUG/INFO/WARNING/ERROR)            |
| `PARACLE_AUTH_ENABLED` | Enable/disable authentication                   |
| `OPENAI_API_KEY`       | OpenAI API key                                  |
| `ANTHROPIC_API_KEY`    | Anthropic API key                               |
| `GOOGLE_API_KEY`       | Google API key                                  |

---

## Exit Codes

| Code | Description        |
| ---- | ------------------ |
| 0    | Success            |
| 1    | General error      |
| 2    | Invalid arguments  |
| 3    | Resource not found |
| 4    | Permission denied  |
| 5    | API unavailable    |

---

## Configuration

### Config File Location

```
~/.paracle/config.yaml
# or
.parac/config.yaml (project-level)
```

### Example Configuration

```yaml
api:
  base_url: http://localhost:8000
  timeout: 30

defaults:
  provider: openai
  model: gpt-4

cli:
  color: true
  json_output: false
```

---

**Last Updated:** 2026-01-05
**CLI Version:** 0.0.1
