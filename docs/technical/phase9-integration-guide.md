# Phase 9 Integration Guide - Complete Reference

This comprehensive guide covers all Phase 9 Agent Collaboration Tools and how to use them effectively in multi-agent workflows.

## Table of Contents

1. [Conditional Retry](#conditional-retry)
2. [Kanban Task Management](#kanban-task-management)
3. [Automatic Git Commits](#automatic-git-commits)
4. [Conflict Resolution](#conflict-resolution)
5. [Human-in-the-Loop](#human-in-the-loop)
6. [Integration Patterns](#integration-patterns)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Conditional Retry

### Overview

The conditional retry system provides intelligent retry logic with exponential backoff for handling transient errors in agent operations.

### Quick Start

```python
from paracle_retry import RetryManager, RetryPolicy
from paracle_retry.conditions import NetworkErrorCondition, RateLimitCondition

# Create retry manager
retry_manager = RetryManager()

# Define policy
policy = RetryPolicy(
    max_retries=3,
    initial_delay=1.0,
    max_delay=60.0,
    exponential_backoff=True,
    jitter=True,
    conditions=[NetworkErrorCondition(), RateLimitCondition()],
)

# Apply to function
@retry_manager.with_retry(policy)
def api_call():
    response = call_external_api()
    return response
```

### Retry Conditions

#### Built-in Conditions

1. **RateLimitCondition** - Retry on rate limit errors
   ```python
   RateLimitCondition()  # Detects "rate limit", "429", "too many requests"
   ```

2. **NetworkErrorCondition** - Retry on network errors
   ```python
   NetworkErrorCondition()  # Detects ConnectionError, requests.RequestException
   ```

3. **TimeoutCondition** - Retry on timeouts
   ```python
   TimeoutCondition()  # Detects TimeoutError, socket.timeout
   ```

4. **ServerErrorCondition** - Retry on server errors
   ```python
   ServerErrorCondition()  # Detects "500", "502", "503", "504"
   ```

5. **CustomCondition** - Custom retry logic
   ```python
   def should_retry(error):
       return "retry_me" in str(error)

   CustomCondition(should_retry)
   ```

#### Combining Conditions

```python
policy = RetryPolicy(
    max_retries=5,
    conditions=[
        NetworkErrorCondition(),
        TimeoutCondition(),
        RateLimitCondition(),
        CustomCondition(lambda e: "temporary" in str(e).lower()),
    ],
)
```

### Exponential Backoff

Delays increase exponentially: 1s → 2s → 4s → 8s → ...

```python
policy = RetryPolicy(
    initial_delay=1.0,      # Start with 1 second
    max_delay=60.0,         # Cap at 60 seconds
    exponential_backoff=True,  # Enable exponential growth
    jitter=True,            # Add randomness (± 20%)
)
```

**Backoff Formula**: `delay = min(initial_delay * 2^attempt, max_delay) * (1 ± jitter)`

### History Tracking

```python
# View retry history
history = retry_manager.get_history()
for entry in history:
    print(f"{entry['operation_id']}: {entry['attempts']} attempts, success={entry['success']}")

# Get statistics
stats = retry_manager.get_statistics()
print(f"Success rate: {stats['success_rate']}%")
print(f"Avg attempts: {stats['avg_attempts']}")

# Clear history
retry_manager.clear_history()
```

### CLI Commands

```bash
# View retry statistics
paracle retry info

# View retry history
paracle retry history [--limit 50]

# Clear retry history
paracle retry clear
```

### Advanced Patterns

#### Infinite Retries

```python
policy = RetryPolicy(max_retries=-1)  # Retry forever
```

#### No Exponential Backoff (Fixed Delay)

```python
policy = RetryPolicy(
    initial_delay=2.0,
    exponential_backoff=False,  # Use fixed 2s delay
)
```

#### Disable History

```python
retry_manager = RetryManager(history_enabled=False)
```

---

## Kanban Task Management

### Overview

Complete task board system with TODO/IN_PROGRESS/BLOCKED/DONE columns, priority levels, and full CRUD operations.

### Quick Start

```python
from paracle_kanban import TaskManager, TaskPriority, TaskStatus

# Create manager
manager = TaskManager()

# Create task
task = manager.create_task(
    title="Implement authentication",
    description="Add JWT authentication to API",
    priority=TaskPriority.HIGH,
    tags=["backend", "security"],
    assigned_to="coder_agent",
    due_date=datetime.now() + timedelta(days=7),
)

# Update task
manager.update_task(task.id, status=TaskStatus.IN_PROGRESS)

# Complete task
manager.update_task(task.id, status=TaskStatus.DONE)
```

### Task Lifecycle

```
TODO → IN_PROGRESS → DONE
  ↓          ↓
BLOCKED ←────┘
```

### Task Properties

```python
from paracle_kanban import Task, TaskPriority, TaskStatus

task = Task(
    id="auto-generated-ulid",
    title="Task title (required)",
    description="Detailed description",
    status=TaskStatus.TODO,           # TODO, IN_PROGRESS, BLOCKED, DONE
    priority=TaskPriority.MEDIUM,     # LOW, MEDIUM, HIGH, CRITICAL
    tags=["backend", "api", "v2"],    # Searchable tags
    assigned_to="coder_agent",        # Agent assignment
    created_by="pm_agent",            # Creator tracking
    due_date=datetime(...),           # Optional deadline
    created_at=datetime.now(),        # Auto-generated
    updated_at=datetime.now(),        # Auto-updated
    completed_at=None,                # Set when status=DONE
)
```

### CLI Commands

```bash
# Initialize board
paracle board init [--name sprint-1]

# Create task
paracle board create "Task title" --priority high --tags api,backend --assigned coder_agent

# List all tasks
paracle board list [--status TODO] [--priority HIGH]

# Show task details
paracle board show <task_id>

# Update task
paracle board update <task_id> --title "New title" --priority critical

# Move task
paracle board move <task_id> IN_PROGRESS

# Complete task
paracle board complete <task_id>

# Delete task
paracle board delete <task_id>

# Show statistics
paracle board stats

# Search tasks
paracle board search "authentication"

# Get metrics
paracle board metrics

# Export/Import
paracle board export tasks.json
paracle board import tasks.json

# Archive completed tasks
paracle board archive [--days 30]

# Clear all tasks
paracle board clear
```

### Workflow Integration

```python
from paracle_orchestration import Workflow, WorkflowStep
from paracle_kanban import TaskManager

class TaskTrackingWorkflow(Workflow):
    def __init__(self):
        self.task_manager = TaskManager()

    async def execute(self):
        # Create task at workflow start
        task = self.task_manager.create_task(
            title=f"Workflow: {self.name}",
            status=TaskStatus.IN_PROGRESS,
        )

        try:
            # Execute workflow steps
            result = await self._execute_steps()

            # Mark complete on success
            self.task_manager.update_task(task.id, status=TaskStatus.DONE)
            return result

        except Exception as e:
            # Mark blocked on failure
            self.task_manager.update_task(
                task.id,
                status=TaskStatus.BLOCKED,
                description=f"Error: {str(e)}",
            )
            raise
```

### Query & Filter

```python
# Get tasks by status
todo_tasks = manager.list_tasks(status=TaskStatus.TODO)

# Get tasks by priority
critical_tasks = manager.list_tasks(priority=TaskPriority.CRITICAL)

# Get tasks by assignee
my_tasks = [t for t in manager.list_tasks() if t.assigned_to == "my_agent"]

# Search by text
search_results = manager.search_tasks("authentication backend")

# Get overdue tasks
now = datetime.now()
overdue = [t for t in manager.list_tasks() if t.due_date and t.due_date < now]
```

---

## Automatic Git Commits

### Overview

Agent-aware git commits with conventional commit format and automatic metadata enrichment.

### Quick Start

```python
from paracle_git import AutoCommitManager, CommitType, CommitConfig

# Configure
config = CommitConfig(
    enabled=True,
    require_approval=False,
    conventional_commits=True,
    prefix_agent_name=True,
    include_metadata=True,
)

# Create manager
manager = AutoCommitManager(".", config=config)

# Detect changes
changes = manager.get_changed_files()

# Commit with agent tracking
manager.commit_agent_changes(
    agent_name="coder_agent",
    changes=changes,
    commit_type=CommitType.FEAT,
    description="Implement user authentication",
    scope="api",
    body="Added JWT authentication with OAuth2 support",
)
```

### Conventional Commit Format

```
[AgentName] <type>(scope): <description>

<body>

Agent: AgentName
Timestamp: 2026-01-07T10:30:00Z
Files: 5

<footer>
```

### Commit Types

| Type       | Description                  | Example                                   |
| ---------- | ---------------------------- | ----------------------------------------- |
| `feat`     | New feature                  | `feat(api): Add user registration`        |
| `fix`      | Bug fix                      | `fix(auth): Resolve token expiration bug` |
| `docs`     | Documentation                | `docs: Update API reference`              |
| `style`    | Code style (no logic change) | `style: Format with black`                |
| `refactor` | Code restructuring           | `refactor(db): Optimize queries`          |
| `perf`     | Performance improvement      | `perf(api): Add response caching`         |
| `test`     | Add/update tests             | `test(auth): Add JWT validation tests`    |
| `build`    | Build system/dependencies    | `build: Update dependencies`              |
| `ci`       | CI/CD changes                | `ci: Add GitHub Actions workflow`         |
| `chore`    | Maintenance tasks            | `chore: Update .gitignore`                |
| `revert`   | Revert previous commit       | `revert: Revert "Add feature X"`          |

### Breaking Changes

```python
commit = ConventionalCommit(
    type=CommitType.FEAT,
    description="New API version",
    breaking=True,  # Adds "!" after type
    body="Complete API redesign\n\nBREAKING CHANGE: All endpoints have new paths",
)

# Output: feat!: New API version
```

### CLI Commands

```bash
# Configure auto-commits
paracle git config --enable --conventional --prefix

# Show git status
paracle git status

# Create conventional commit
paracle git commit "Add feature" \\
    --type feat \\
    --scope api \\
    --body "Detailed description" \\
    --agent coder_agent

# Show commit history
paracle git log [--limit 20]
```

### Integration with Existing Git Tools

#### paracle_tools/git_tools.py (FOR AGENTS)
- 15 low-level git operation tools
- Used by agents during execution
- Tools: GitAddTool, GitCommitTool, GitPushTool, etc.

#### paracle_git + CLI (FOR MANAGING AGENT CHANGES)
- High-level auto-commit workflow
- Agent tracking and metadata
- Conventional commits enforcement

**They complement each other** - tools for agent operations, commands for managing agent changes.

---

## Conflict Resolution

### Overview

File-level locking system with conflict detection and 5 resolution strategies.

### Quick Start

```python
from paracle_conflicts import LockManager, ConflictDetector, ConflictResolver, ResolutionStrategy

# Initialize components
lock_manager = LockManager()
detector = ConflictDetector()
resolver = ConflictResolver()

# Acquire lock before modifying
if lock_manager.acquire_lock("api.py", "coder_agent", timeout=300):
    try:
        # Make changes
        with open("api.py", "w") as f:
            f.write("modified content")

        # Record modification
        conflict = detector.record_modification("api.py", "coder_agent")

    finally:
        lock_manager.release_lock("api.py", "coder_agent")
```

### File Locking

```python
# Acquire lock
success = lock_manager.acquire_lock(
    file_path="src/api.py",
    agent_id="coder_agent",
    timeout=300,          # Seconds until expiration
    operation="write",    # or "read"
)

# Check if locked
is_locked = lock_manager.is_locked("src/api.py")

# Get lock info
lock = lock_manager.get_lock("src/api.py")
if lock:
    print(f"Locked by: {lock.agent_id}")
    print(f"Expires: {lock.expires_at}")

# Release lock
lock_manager.release_lock("src/api.py", "coder_agent")

# Wait for lock (polling)
success = lock_manager.wait_for_lock(
    file_path="src/api.py",
    agent_id="coder_agent",
    timeout=60,           # Max wait time
    poll_interval=0.5,    # Check every 0.5s
)

# Cleanup expired locks
cleared = lock_manager.clear_expired_locks()
```

### Conflict Detection

```python
# Record modification (returns conflict if detected)
conflict = detector.record_modification("api.py", "coder_agent")

if conflict:
    print(f"Conflict detected!")
    print(f"Agent 1: {conflict.agent1_id}")
    print(f"Agent 2: {conflict.agent2_id}")

    # Resolve conflict
    result = resolver.resolve(conflict, ResolutionStrategy.LAST_WINS)

    if result.success:
        detector.mark_resolved(conflict)

# Get all conflicts
conflicts = detector.get_conflicts(resolved=False)

# Clear modification tracking
detector.clear_modifications("api.py")
```

### Resolution Strategies

#### 1. MANUAL - Human Review Required

```python
result = resolver.resolve(conflict, ResolutionStrategy.MANUAL)
# Creates backups of both versions
# Requires manual review and decision
# Best for: Critical files, complex conflicts
```

#### 2. FIRST_WINS - Keep First Agent's Changes

```python
result = resolver.resolve(conflict, ResolutionStrategy.FIRST_WINS)
# Keeps agent1's changes
# Backs up agent2's changes
# Best for: Time-based priority, "don't overwrite" policies
```

#### 3. LAST_WINS - Keep Last Agent's Changes

```python
result = resolver.resolve(conflict, ResolutionStrategy.LAST_WINS)
# Keeps agent2's changes (current state)
# Backs up agent1's changes
# Best for: "Latest wins", agile workflows
```

#### 4. MERGE - Automatic Merge (Placeholder)

```python
result = resolver.resolve(conflict, ResolutionStrategy.MERGE)
# Not implemented - returns failure
# Future: Use git merge or diff3
# Best for: Compatible changes, structured files
```

#### 5. BACKUP_BOTH - Save Both Versions

```python
result = resolver.resolve(conflict, ResolutionStrategy.BACKUP_BOTH)
# Saves both versions as backups
# Leaves current file unchanged
# Best for: Audit trail, comparison needed
```

### CLI Commands

```bash
# Show active locks
paracle conflicts locks

# Acquire lock
paracle conflicts lock <file_path> <agent_id> [--timeout 300]

# Release lock
paracle conflicts unlock <file_path> <agent_id>

# Cleanup expired locks
paracle conflicts cleanup

# Detect conflicts
paracle conflicts detect

# Resolve conflicts
paracle conflicts resolve --strategy last_wins

# List backups
paracle conflicts backups
```

### Safe Concurrent Modification Pattern

```python
def modify_file_safely(file_path, agent_id, modification_fn):
    """Safe pattern for concurrent file modification."""
    lock_manager = LockManager()
    detector = ConflictDetector()

    # Step 1: Wait for lock
    if not lock_manager.wait_for_lock(file_path, agent_id, timeout=60):
        raise TimeoutError(f"Could not acquire lock on {file_path}")

    try:
        # Step 2: Perform modification
        modification_fn(file_path)

        # Step 3: Record modification
        conflict = detector.record_modification(file_path, agent_id)

        if conflict:
            # Step 4: Resolve conflict
            resolver = ConflictResolver()
            result = resolver.resolve(conflict, ResolutionStrategy.MANUAL)

            if not result.success:
                raise ValueError(f"Could not resolve conflict: {result.message}")

    finally:
        # Step 5: Always release lock
        lock_manager.release_lock(file_path, agent_id)

# Usage
modify_file_safely("api.py", "coder_agent", lambda f: write_code(f))
```

---

## Human-in-the-Loop

### Overview

Pre-existing approval system for human oversight of agent operations (implemented in Phase 4).

### Quick Start

```python
from paracle_orchestration.approval import ApprovalManager, ApprovalRequest, ApprovalType

# Create manager
manager = ApprovalManager()

# Request approval
request = ApprovalRequest(
    agent_id="coder_agent",
    operation="deploy_to_production",
    context={"environment": "prod", "version": "1.0.0"},
    approval_type=ApprovalType.MANUAL,
    priority="high",
)

approval = manager.create_approval(request)

# Wait for approval (blocking)
approved = manager.wait_for_approval(approval.id, timeout=300)

if approved:
    # Proceed with operation
    deploy()
else:
    # Operation rejected or timed out
    cancel()
```

### CLI Commands

```bash
# List pending approvals
paracle approvals list [--status pending]

# Get approval details
paracle approvals get <approval_id>

# Approve request
paracle approvals approve <approval_id> [--comment "Approved for release"]

# Reject request
paracle approvals reject <approval_id> [--reason "Failed security review"]

# Cancel request
paracle approvals cancel <approval_id>

# Show approval statistics
paracle approvals stats
```

---

## Integration Patterns

### Pattern 1: Workflow with All Phase 9 Tools

```python
from paracle_orchestration import Workflow, WorkflowStep
from paracle_retry import RetryManager, RetryPolicy
from paracle_kanban import TaskManager
from paracle_git import AutoCommitManager, CommitType
from paracle_conflicts import LockManager
from paracle_orchestration.approval import ApprovalManager

class ComprehensiveWorkflow(Workflow):
    def __init__(self):
        self.retry_manager = RetryManager()
        self.task_manager = TaskManager()
        self.git_manager = AutoCommitManager(".")
        self.lock_manager = LockManager()
        self.approval_manager = ApprovalManager()

    async def execute(self):
        # 1. Create task for tracking
        task = self.task_manager.create_task(
            title="Execute comprehensive workflow",
            status=TaskStatus.IN_PROGRESS,
        )

        try:
            # 2. Execute with retry
            policy = RetryPolicy(max_retries=3)

            @self.retry_manager.with_retry(policy)
            async def execute_with_retry():
                # 3. Acquire lock for file modification
                if self.lock_manager.acquire_lock("output.txt", "workflow_agent"):
                    try:
                        # 4. Perform work
                        result = await self._do_work()

                        # 5. Request approval for critical operation
                        approval = self.approval_manager.request_approval(
                            operation="commit_changes",
                            context={"result": result},
                        )

                        if self.approval_manager.wait_for_approval(approval.id):
                            # 6. Commit changes
                            changes = self.git_manager.get_changed_files()
                            self.git_manager.commit_agent_changes(
                                agent_name="workflow_agent",
                                changes=changes,
                                commit_type=CommitType.FEAT,
                                description="Workflow execution complete",
                            )

                        return result
                    finally:
                        self.lock_manager.release_lock("output.txt", "workflow_agent")

            result = await execute_with_retry()

            # 7. Mark task complete
            self.task_manager.update_task(task.id, status=TaskStatus.DONE)

            return result

        except Exception as e:
            # Mark task blocked on failure
            self.task_manager.update_task(task.id, status=TaskStatus.BLOCKED)
            raise
```

### Pattern 2: Multi-Agent Collaboration

```python
from paracle_conflicts import LockManager, ConflictDetector, ConflictResolver, ResolutionStrategy

class MultiAgentProject:
    def __init__(self):
        self.lock_manager = LockManager()
        self.detector = ConflictDetector()
        self.resolver = ConflictResolver()

    async def agent_work(self, agent_id, file_path, work_fn):
        """Safe multi-agent work pattern."""
        # Wait for lock
        if not self.lock_manager.wait_for_lock(file_path, agent_id, timeout=60):
            raise TimeoutError(f"{agent_id} could not acquire lock")

        try:
            # Perform work
            work_fn()

            # Detect conflicts
            conflict = self.detector.record_modification(file_path, agent_id)

            if conflict:
                # Resolve automatically
                result = self.resolver.resolve(conflict, ResolutionStrategy.LAST_WINS)
                if result.success:
                    self.detector.mark_resolved(conflict)
                else:
                    raise ValueError(f"Could not resolve conflict: {result.message}")

        finally:
            self.lock_manager.release_lock(file_path, agent_id)
```

---

## Best Practices

### Retry Best Practices

1. ✅ **Use specific conditions** - Don't retry on all errors
2. ✅ **Set reasonable max retries** - Usually 3-5
3. ✅ **Enable jitter** - Prevents thundering herd
4. ✅ **Cap max delay** - Avoid excessively long waits
5. ✅ **Track history** - Monitor retry patterns
6. ❌ **Don't retry idempotency violations** - Risk data corruption
7. ❌ **Don't retry business logic errors** - Only transient errors

### Kanban Best Practices

1. ✅ **Use descriptive titles** - Clear, actionable task names
2. ✅ **Add relevant tags** - Enable search and filtering
3. ✅ **Set priorities** - Focus on important work
4. ✅ **Archive completed tasks** - Keep board clean
5. ✅ **Use due dates** - Track deadlines
6. ❌ **Don't create micro-tasks** - Too granular, overhead
7. ❌ **Don't leave tasks in IN_PROGRESS** - Move to BLOCKED if stuck

### Git Commits Best Practices

1. ✅ **Use conventional commits** - Enables automation
2. ✅ **Include scope** - Clarify affected area
3. ✅ **Write clear descriptions** - Imperative mood
4. ✅ **Add body for complex changes** - Explain why
5. ✅ **Enable agent tracking** - Audit trail
6. ❌ **Don't commit work-in-progress** - Complete logical units
7. ❌ **Don't skip commit messages** - Always describe changes

### Conflict Resolution Best Practices

1. ✅ **Always acquire locks** - Before modifying shared files
2. ✅ **Use timeouts** - Prevent deadlocks
3. ✅ **Release in finally blocks** - Ensure cleanup
4. ✅ **Choose appropriate strategy** - Based on use case
5. ✅ **Monitor conflicts** - Track patterns
6. ❌ **Don't hold locks too long** - Blocks other agents
7. ❌ **Don't ignore conflicts** - Resolve or escalate

---

## Troubleshooting

### Retry Issues

**Problem**: Retries not triggering

```python
# Solution: Check conditions
policy = RetryPolicy(conditions=[NetworkErrorCondition()])  # Add conditions!
```

**Problem**: Too many retries

```python
# Solution: Lower max_retries
policy = RetryPolicy(max_retries=3)  # Not 10+
```

**Problem**: Delays too long

```python
# Solution: Cap max_delay
policy = RetryPolicy(max_delay=30.0)  # Cap at 30s
```

### Kanban Issues

**Problem**: Can't find tasks

```bash
# Solution: Use search
paracle board search "keyword"
```

**Problem**: Board too cluttered

```bash
# Solution: Archive completed
paracle board archive --days 30
```

### Git Issues

**Problem**: Commit message format wrong

```python
# Solution: Use ConventionalCommit
commit = ConventionalCommit(
    type=CommitType.FEAT,  # Must be valid type
    description="Description",  # Required
)
```

**Problem**: Changes not detected

```python
# Solution: Check git status
manager = AutoCommitManager(".")
if not manager.is_git_repo():
    raise ValueError("Not a git repository!")
```

### Conflict Issues

**Problem**: Lock acquisition fails

```python
# Solution: Wait for lock
success = lock_manager.wait_for_lock(file_path, agent_id, timeout=60)
if not success:
    raise TimeoutError("Could not acquire lock")
```

**Problem**: Locks not released

```python
# Solution: Always use try/finally
try:
    lock_manager.acquire_lock(file, agent)
    # work
finally:
    lock_manager.release_lock(file, agent)  # Always release!
```

---

## Performance Considerations

### Retry Performance

- **Exponential backoff**: Prevents overwhelming services
- **Jitter**: Distributes load over time
- **History tracking**: Small SQLite overhead (~1ms per operation)

### Kanban Performance

- **SQLite database**: Fast for <10K tasks
- **In-memory caching**: Manager keeps board in memory
- **Archive regularly**: Keep active tasks under 1K

### Git Performance

- **Git operations**: Subprocess overhead (~50-100ms)
- **Change detection**: `git status` can be slow in large repos
- **Commit creation**: ~100ms including metadata

### Conflict Performance

- **Lock file operations**: File I/O overhead (~1-5ms)
- **Hash computation**: SHA256 of file (~1ms per KB)
- **Lock polling**: Configurable interval (default 0.5s)

---

## See Also

- [Phase 9 Completion Report](../.parac/memory/summaries/phase_9_completion.md)
- [Retry Example](../examples/15_conditional_retry.py)
- [Kanban Example](../examples/16_kanban_workflow.py)
- [Git Example](../examples/17_automatic_commits.py)
- [Conflicts Example](../examples/18_conflict_resolution.py)
- [Human-in-the-Loop Example](../examples/07_human_in_the_loop.py)

---

**Version**: 1.0
**Last Updated**: 2026-01-07
**Phase**: 9 - Agent Collaboration Tools
**Status**: Complete
