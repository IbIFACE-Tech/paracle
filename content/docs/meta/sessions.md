# Sessions Guide

Interactive AI sessions with `paracle_meta`.

## Overview

`paracle_meta` provides three session modes:

| Mode | Purpose | Use Case |
|------|---------|----------|
| **Chat** | Conversational AI | Interactive assistance, Q&A |
| **Plan** | Task decomposition | Complex multi-step tasks |
| **Edit** | Code editing | File modifications, refactoring |

## Chat Session

Interactive conversation with full tool access.

### CLI Usage

```bash
# Start new chat
paracle meta chat

# Resume last session
paracle meta chat --resume

# Use specific provider
paracle meta chat --provider openai

# Custom system prompt
paracle meta chat --system "You are a Python expert"
```

### Interactive Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/clear` | Clear conversation history |
| `/save` | Save current session |
| `/load <id>` | Load a saved session |
| `/history` | Show conversation history |
| `/tools` | List available tools |
| `/exit` | Exit chat |

### Example Session

```
$ paracle meta chat

Chat Session Started
Provider: anthropic (claude-sonnet-4-20250514)
Type /help for commands, /exit to quit

You: What files are in the current directory?

AI: Let me check the current directory.
[Using tool: list_directory]

The current directory contains:
- README.md
- pyproject.toml
- packages/
- tests/
- docs/

You: Explain what pyproject.toml does

AI: The pyproject.toml file is the modern Python project configuration...
[detailed explanation]

You: /save
Session saved: chat-2024-01-08-abc123

You: /exit
Goodbye!
```

### Python API

```python
from paracle_meta import ChatSession, ChatConfig
from paracle_meta.capabilities.providers import AnthropicProvider

# Create provider
provider = AnthropicProvider(api_key="sk-ant-...")

# Configure session
config = ChatConfig(
    max_history=100,
    save_history=True,
    tools_enabled=True,
)

# Start session
async with ChatSession(provider, config) as chat:
    # Send message
    response = await chat.send("Hello!")
    print(response.content)

    # Multi-turn conversation
    response = await chat.send("What can you help me with?")
    print(response.content)

    # Save session
    session_id = await chat.save()
    print(f"Saved: {session_id}")
```

### Resume Session

```python
# Resume by session ID
async with ChatSession.resume(session_id, provider) as chat:
    response = await chat.send("Continue our conversation")
```

## Plan Session

Structured task planning and execution.

### CLI Usage

```bash
# Create a plan
paracle meta plan "Build a REST API with authentication"

# Resume planning
paracle meta plan --resume

# Execute the plan
paracle meta plan --execute

# Dry run (show without executing)
paracle meta plan --dry-run
```

### Plan Structure

```yaml
plan:
  id: plan-abc123
  title: "Build a REST API with authentication"
  status: planning  # planning, approved, executing, completed

  steps:
    - id: step-1
      title: "Create project structure"
      description: "Set up FastAPI project with proper directory structure"
      status: pending
      dependencies: []

    - id: step-2
      title: "Define data models"
      description: "Create Pydantic models for User, Token"
      status: pending
      dependencies: [step-1]

    - id: step-3
      title: "Implement authentication"
      description: "JWT-based auth with login/logout endpoints"
      status: pending
      dependencies: [step-2]

    - id: step-4
      title: "Add protected routes"
      description: "Create example protected endpoints"
      status: pending
      dependencies: [step-3]

    - id: step-5
      title: "Write tests"
      description: "Unit tests for auth flow"
      status: pending
      dependencies: [step-4]
```

### Example Planning Session

```
$ paracle meta plan "Build a REST API with authentication"

Plan Session Started
Analyzing task...

Task Analysis:
- Type: Feature implementation
- Complexity: Medium
- Estimated steps: 5

Generated Plan:
================

1. [ ] Create project structure
   - Set up FastAPI project
   - Create directory layout

2. [ ] Define data models
   - User model
   - Token model
   Dependencies: Step 1

3. [ ] Implement authentication
   - JWT token generation
   - Login/logout endpoints
   Dependencies: Step 2

4. [ ] Add protected routes
   - Example endpoints
   - Permission checks
   Dependencies: Step 3

5. [ ] Write tests
   - Auth flow tests
   - Endpoint tests
   Dependencies: Step 4

Approve this plan? [y/n/edit]: y

Plan approved! Run 'paracle meta plan --execute' to execute.
```

### Python API

```python
from paracle_meta import PlanSession, PlanConfig, Plan, PlanStep
from paracle_meta.capabilities.providers import AnthropicProvider

provider = AnthropicProvider(api_key="sk-ant-...")

config = PlanConfig(
    max_steps=10,
    require_approval=True,
    auto_execute=False,
)

async with PlanSession(provider, config) as planner:
    # Create plan
    plan = await planner.create_plan(
        "Build a REST API with authentication"
    )

    # Review plan
    print(f"Plan: {plan.title}")
    for step in plan.steps:
        print(f"  - {step.title}")

    # Approve and execute
    await planner.approve(plan)
    result = await planner.execute(plan)

    # Check results
    for step_result in result.step_results:
        print(f"{step_result.step_id}: {step_result.status}")
```

### Plan Execution

```python
# Execute with progress callback
async def on_progress(step: PlanStep, status: str):
    print(f"Step {step.id}: {status}")

result = await planner.execute(
    plan,
    on_progress=on_progress,
)
```

## Edit Session

Batch file editing with preview and rollback.

### CLI Usage

```bash
# Start edit session
paracle meta edit

# Edit specific file
paracle meta edit --file src/main.py

# Apply edits immediately
paracle meta edit --auto-apply
```

### Edit Operations

| Operation | Description |
|-----------|-------------|
| `insert` | Insert text at position |
| `replace` | Replace text |
| `delete` | Delete text |
| `append` | Append to file |
| `prepend` | Prepend to file |

### Python API

```python
from paracle_meta import EditSession, EditConfig, EditOperation, EditType
from paracle_meta.capabilities.providers import AnthropicProvider

provider = AnthropicProvider(api_key="sk-ant-...")

config = EditConfig(
    auto_apply=False,
    create_backup=True,
    preview_mode=True,
)

async with EditSession(provider, config) as editor:
    # Add edit operation
    editor.add_operation(EditOperation(
        file_path="src/main.py",
        edit_type=EditType.REPLACE,
        old_text="def hello():",
        new_text="def hello_world():",
    ))

    # Preview changes
    preview = await editor.preview()
    print(preview)

    # Apply edits
    result = await editor.apply()

    # Rollback if needed
    await editor.rollback()
```

### Batch Edits

```python
# Create batch of edits
batch = EditBatch(
    name="refactor-function",
    operations=[
        EditOperation(
            file_path="src/main.py",
            edit_type=EditType.REPLACE,
            old_text="old_function",
            new_text="new_function",
        ),
        EditOperation(
            file_path="src/utils.py",
            edit_type=EditType.REPLACE,
            old_text="old_function",
            new_text="new_function",
        ),
    ],
)

# Apply batch
result = await editor.apply_batch(batch)
```

## Session Persistence

Sessions can be saved and resumed.

### Session Storage

Sessions are stored in:
- Linux: `~/.local/share/paracle/sessions/`
- macOS: `~/Library/Application Support/Paracle/sessions/`
- Windows: `%LOCALAPPDATA%\Paracle\sessions\`

### Session Format

```json
{
  "id": "chat-2024-01-08-abc123",
  "type": "chat",
  "provider": "anthropic",
  "model": "claude-sonnet-4-20250514",
  "created_at": "2024-01-08T10:30:00Z",
  "updated_at": "2024-01-08T11:45:00Z",
  "messages": [
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi! How can I help?"}
  ],
  "metadata": {
    "total_tokens": 1234,
    "total_cost": 0.05
  }
}
```

### List Sessions

```bash
paracle meta sessions list

# Output:
# ID                      Type    Provider    Updated
# chat-2024-01-08-abc123  chat    anthropic   2 hours ago
# plan-2024-01-07-def456  plan    openai      1 day ago
```

### Delete Session

```bash
paracle meta sessions delete chat-2024-01-08-abc123
```

## Session Configuration

### ChatConfig

```python
ChatConfig(
    max_history=100,        # Max messages in context
    save_history=True,      # Auto-save history
    tools_enabled=True,     # Enable tool use
    system_prompt=None,     # Custom system prompt
    temperature=0.7,        # Model temperature
)
```

### PlanConfig

```python
PlanConfig(
    max_steps=10,           # Max steps in plan
    require_approval=True,  # Require user approval
    auto_execute=False,     # Execute immediately
    step_timeout=300,       # Timeout per step (seconds)
)
```

### EditConfig

```python
EditConfig(
    auto_apply=False,       # Apply edits immediately
    create_backup=True,     # Backup files before edit
    preview_mode=True,      # Show preview before apply
    max_file_size=1048576,  # Max file size (1MB)
)
```

## Best Practices

1. **Use Chat for exploration** - Quick Q&A, learning
2. **Use Plan for complex tasks** - Multi-step implementations
3. **Use Edit for refactoring** - Safe batch modifications
4. **Save sessions regularly** - Resume where you left off
5. **Review before executing** - Always preview plans/edits
