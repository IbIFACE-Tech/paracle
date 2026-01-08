# Kanban Task Management Guide

## Overview

Paracle includes a built-in Kanban system for organizing and tracking work across agents. Tasks flow through customizable columns (statuses) as work progresses.

## Quick Start

### 1. Create a Board

```bash
# Create a board
paracle board create "Feature Development" \
  --description "Track feature implementation"

# List boards
paracle board list
```

### 2. Create Tasks

```bash
# Create a task
paracle task create <board_id> "Design API endpoints" \
  --priority HIGH \
  --type FEATURE \
  --tags api design

# Create and assign
paracle task create <board_id> "Implement auth" \
  --priority CRITICAL \
  --type FEATURE \
  --assignee architect_agent
```

### 3. Move Tasks Through Workflow

```bash
# Move task to TODO
paracle task move <task_id> TODO

# Move to IN_PROGRESS
paracle task move <task_id> IN_PROGRESS

# Move to REVIEW
paracle task move <task_id> REVIEW

# Block a task
paracle task move <task_id> BLOCKED \
  --reason "Waiting for design approval"

# Complete task
paracle task move <task_id> DONE
```

### 4. View Board

```bash
# Show visual board
paracle board show <board_id>

# Get statistics
paracle board stats <board_id>
```

## Task Lifecycle

### Status Workflow

```
BACKLOG → TODO → IN_PROGRESS → REVIEW → DONE
              ↓         ↓         ↓
            BLOCKED   BLOCKED
```

Valid transitions:
- `BACKLOG` → `TODO`, `ARCHIVED`
- `TODO` → `IN_PROGRESS`, `BACKLOG`, `ARCHIVED`
- `IN_PROGRESS` → `REVIEW`, `BLOCKED`, `TODO`, `DONE`
- `REVIEW` → `IN_PROGRESS`, `DONE`, `TODO`
- `BLOCKED` → `IN_PROGRESS`, `TODO`
- `DONE` → `IN_PROGRESS`, `ARCHIVED`
- `ARCHIVED` → (terminal state)

### Priority Levels

- `LOW` - Nice to have
- `MEDIUM` - Standard priority
- `HIGH` - Important
- `CRITICAL` - Urgent, blocking

### Task Types

- `FEATURE` - New functionality
- `BUG` - Bug fix
- `REFACTOR` - Code refactoring
- `DOCS` - Documentation
- `TEST` - Testing
- `CHORE` - Maintenance tasks

## CLI Commands

### Task Management

```bash
# Create task
paracle task create <board_id> <title> [OPTIONS]
  --description, -d TEXT      Task description
  --priority, -p CHOICE       LOW|MEDIUM|HIGH|CRITICAL
  --type, -t CHOICE          FEATURE|BUG|REFACTOR|DOCS|TEST|CHORE
  --assignee, -a TEXT        Assign to agent ID
  --tags, -g TEXT            Tags (multiple allowed)
  --json                     Output as JSON

# List tasks
paracle task list [OPTIONS]
  --board, -b TEXT           Filter by board ID
  --status, -s CHOICE        Filter by status
  --assignee, -a TEXT        Filter by assignee
  --priority, -p CHOICE      Filter by priority
  --json                     Output as JSON

# Get task details
paracle task get <task_id> [--json]

# Move task
paracle task move <task_id> <status> [--reason TEXT]

# Assign/unassign
paracle task assign <task_id> <agent_id>
paracle task unassign <task_id>

# Delete task
paracle task delete <task_id>
```

### Board Management

```bash
# Create board
paracle board create <name> [OPTIONS]
  --description, -d TEXT     Board description
  --json                     Output as JSON

# List boards
paracle board list [OPTIONS]
  --archived                 Include archived boards
  --json                     Output as JSON

# Get board details
paracle board get <board_id> [--json]

# Show visual board
paracle board show <board_id>

# Board statistics
paracle board stats <board_id> [--json]

# Archive board
paracle board archive <board_id>

# Delete board (and all tasks)
paracle board delete <board_id>
```

## Python API

### Basic Usage

```python
from paracle_kanban import Task, TaskPriority, TaskStatus, TaskType, Board
from paracle_kanban.board import BoardRepository

# Initialize repository
repo = BoardRepository()

# Create a board
board = Board(
    name="Feature Development",
    description="Track features"
)
board = repo.create_board(board)

# Create a task
task = Task(
    board_id=board.id,
    title="Implement auth",
    priority=TaskPriority.HIGH,
    task_type=TaskType.FEATURE,
    tags=["auth", "security"]
)
task = repo.create_task(task)

# Move task through workflow
task.move_to(TaskStatus.TODO)
task.assign("coder_agent")
task.move_to(TaskStatus.IN_PROGRESS)
repo.update_task(task)

# Complete task
task.move_to(TaskStatus.DONE)
repo.update_task(task)

# Get metrics
cycle_time = task.cycle_time()  # Hours from start to completion
lead_time = task.lead_time()    # Hours from creation to completion
```

### Querying Tasks

```python
# List all tasks
tasks = repo.list_tasks()

# Filter by board
tasks = repo.list_tasks(board_id=board.id)

# Filter by status
tasks = repo.list_tasks(status=TaskStatus.IN_PROGRESS)

# Filter by assignee
tasks = repo.list_tasks(assigned_to="coder_agent")

# Multiple filters
tasks = repo.list_tasks(
    board_id=board.id,
    status=TaskStatus.IN_PROGRESS,
    priority=TaskPriority.HIGH
)
```

### Board Statistics

```python
# Get statistics
stats = repo.get_board_stats(board.id)

# Access metrics
total_tasks = stats["total_tasks"]
status_counts = stats["status_counts"]
avg_cycle_time = stats["avg_cycle_time_hours"]
avg_lead_time = stats["avg_lead_time_hours"]

print(f"Total: {total_tasks}")
print(f"In Progress: {status_counts.get('IN_PROGRESS', 0)}")
print(f"Avg Cycle Time: {avg_cycle_time:.1f}h")
```

## Integration with Workflows

### Agent Task Assignment

```python
from paracle_orchestration import WorkflowEngine
from paracle_kanban.board import BoardRepository

# Create board for workflow
repo = BoardRepository()
board = repo.create_board(Board(name="Code Review Workflow"))

# Create tasks for workflow steps
design_task = Task(
    board_id=board.id,
    title="Architecture review",
    task_type=TaskType.FEATURE,
    assigned_to="architect_agent"
)
repo.create_task(design_task)

code_task = Task(
    board_id=board.id,
    title="Implement feature",
    task_type=TaskType.FEATURE,
    assigned_to="coder_agent",
    depends_on=[design_task.id]  # Dependency
)
repo.create_task(code_task)

# Update task status as workflow progresses
design_task.move_to(TaskStatus.IN_PROGRESS)
repo.update_task(design_task)
```

### Tracking Agent Progress

```python
# List tasks by agent
agent_tasks = repo.list_tasks(assigned_to="coder_agent")

# Filter active work
active_tasks = repo.list_tasks(
    assigned_to="coder_agent",
    status=TaskStatus.IN_PROGRESS
)

# Get blocked tasks
blocked_tasks = repo.list_tasks(status=TaskStatus.BLOCKED)
for task in blocked_tasks:
    print(f"Task: {task.title}")
    print(f"Blocked by: {task.blocked_by}")
```

## Advanced Features

### Dependencies

```python
# Create task with dependencies
task = Task(
    board_id=board.id,
    title="Integration tests",
    depends_on=["task_id_1", "task_id_2"]  # Must complete first
)
```

### Blocking Tasks

```python
# Block a task
task.move_to(TaskStatus.BLOCKED, reason="Waiting for API keys")
repo.update_task(task)

# Check if blocked
if task.is_blocked():
    print(f"Blocked: {task.blocked_by}")

# Unblock
task.move_to(TaskStatus.IN_PROGRESS)
repo.update_task(task)
```

### Tags and Metadata

```python
# Add tags
task.add_tag("security")
task.add_tag("critical")

# Custom metadata
task.metadata["review_url"] = "https://github.com/pr/123"
task.metadata["reviewer"] = "reviewer_agent"

repo.update_task(task)
```

### Metrics and Analytics

```python
# Get all completed tasks
completed = repo.list_tasks(
    board_id=board.id,
    status=TaskStatus.DONE
)

# Calculate average metrics
total_cycle_time = 0
count = 0

for task in completed:
    cycle_time = task.cycle_time()
    if cycle_time:
        total_cycle_time += cycle_time
        count += 1

avg_cycle_time = total_cycle_time / count if count > 0 else 0
print(f"Average cycle time: {avg_cycle_time:.1f} hours")
```

## Storage

Tasks and boards are persisted in SQLite:

```
.parac/memory/data/kanban.db
```

Tables:
- `boards` - Board metadata
- `tasks` - Task details with foreign keys to boards

Indexes for performance:
- `idx_tasks_board_id` - Fast board queries
- `idx_tasks_status` - Fast status filtering
- `idx_tasks_assigned_to` - Fast assignee filtering

## Best Practices

1. **Use descriptive titles** - Make tasks easy to identify
2. **Set appropriate priorities** - Use CRITICAL sparingly
3. **Track blockers** - Always provide reason when blocking
4. **Leverage tags** - Group related tasks
5. **Monitor metrics** - Track cycle and lead times
6. **Keep boards focused** - One board per project/workflow
7. **Archive completed boards** - Keep UI clean
8. **Use dependencies** - Model task relationships

## Examples

See `examples/16_kanban_workflow.py` for a complete working example.

## See Also

- [Workflow Guide](workflow-guide.md) - Orchestrating multi-agent workflows
- [Agent Execution](agent-execution-quickref.md) - Running agents
- [CLI Reference](cli-reference.md) - All CLI commands

---

**Version**: 1.0
**Last Updated**: 2026-01-07
**Status**: Active
