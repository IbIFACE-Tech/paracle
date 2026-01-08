# State Management Concurrency & File Locking

## Overview

Paracle's state management system implements **file-level locking** and **optimistic concurrency control** to prevent data corruption and lost updates in multi-process scenarios.

## Problem Statement

Before file locking, concurrent access to `current_state.yaml` could cause:

1. **Lost Updates**: Two processes read state, modify it, and write back → last write wins
2. **Data Corruption**: Partial writes if process crashes mid-write
3. **Race Conditions**: CLI + API + git hooks all modifying state simultaneously

## Solution

### 1. File-Level Locking

Uses `filelock` library for cross-platform file locking:

```python
from paracle_core.parac.state import load_state, save_state

# Automatic locking
state = load_state(parac_root)  # Acquires read lock
save_state(state, parac_root)   # Acquires write lock
```

**How it works:**
- Creates `.yaml.lock` file alongside `current_state.yaml`
- Blocks concurrent writes until lock is released
- Timeout after 10 seconds (configurable)
- Cross-platform (Windows, Linux, macOS)

### 2. Atomic Writes

Implements write-to-temp-then-rename pattern:

```python
# Write to temp file
temp_file = state_file.with_suffix(".yaml.tmp")
with open(temp_file, "w") as f:
    yaml.dump(state, f)

# Atomic rename (overwrites existing)
temp_file.replace(state_file)
```

**Benefits:**
- No partial writes if crash occurs
- Readers always see valid YAML
- Temp file cleaned up on error

### 3. Optimistic Locking

Uses revision counter to detect conflicts:

```python
@dataclass
class ParacState:
    revision: int = 0  # Increments on each save

# Load → modify → save
state = load_state()  # revision=5
state.update_progress(80)
save_state(state)     # revision becomes 6

# Concurrent modification detected
state2 = load_state()  # revision=5 (stale)
save_state(state2)     # Raises StateConflictError
```

**Flow:**
1. Load state with current revision (e.g., rev=5)
2. Another process saves → revision becomes 6
3. Attempt to save with rev=5 → conflict detected
4. Raises `StateConflictError` with clear message

### 4. State Change Logging

Append-only audit trail in `.parac/memory/logs/state_changes.jsonl`:

```python
from paracle_core.parac.state_logging import log_state_change

log_state_change(
    parac_root,
    change_type="progress",
    description="Updated phase progress",
    old_value="50%",
    new_value="75%",
    revision=6
)
```

**Log format:**
```json
{
  "timestamp": "2026-01-06T14:30:00.123456",
  "process_id": 12345,
  "change_type": "progress",
  "description": "Updated phase progress from 50% to 75%",
  "old_value": "50%",
  "new_value": "75%",
  "revision": 6
}
```

## API Reference

### Loading State

```python
from paracle_core.parac.state import load_state, StateLockError

try:
    state = load_state(parac_root, timeout=10.0)
except StateLockError:
    print("Could not acquire lock (timeout)")
```

**Parameters:**
- `parac_root`: Path to `.parac/` directory (optional, auto-detected)
- `timeout`: Lock acquisition timeout in seconds (default: 10.0)

**Returns:**
- `ParacState` if found and valid
- `None` if not found or invalid YAML

**Raises:**
- `StateLockError` if lock cannot be acquired

### Saving State

```python
from paracle_core.parac.state import save_state, StateConflictError

try:
    save_state(state, parac_root, check_conflict=True)
except StateConflictError as e:
    print(f"State modified by another process: {e}")
    # Reload and retry
    state = load_state(parac_root)
    # Re-apply changes
    save_state(state, parac_root)
```

**Parameters:**
- `state`: ParacState to save
- `parac_root`: Path to `.parac/` directory (optional)
- `timeout`: Lock timeout in seconds (default: 10.0)
- `check_conflict`: Enable optimistic locking (default: True)

**Returns:**
- `True` if saved successfully
- `False` on I/O error

**Raises:**
- `StateConflictError` if revision mismatch
- `StateLockError` if lock cannot be acquired

### Handling Conflicts

```python
from paracle_core.parac.state import load_state, save_state, StateConflictError

def update_with_retry(parac_root, max_retries=3):
    """Update state with automatic conflict resolution."""
    for attempt in range(max_retries):
        try:
            # Load fresh state
            state = load_state(parac_root)

            # Apply changes
            state.update_progress(75)

            # Save with conflict check
            save_state(state, parac_root, check_conflict=True)
            return True

        except StateConflictError:
            if attempt < max_retries - 1:
                continue  # Retry
            raise  # Give up after max_retries

    return False
```

## Concurrency Scenarios

### Scenario 1: Multiple CLI Commands

```bash
# Terminal 1
paracle session end &

# Terminal 2
paracle validate &
```

**Behavior:**
- First acquires lock, second waits
- Second proceeds after first releases lock
- No data loss or corruption

### Scenario 2: API + Background Worker

```python
# API request handler
@app.post("/state/update")
async def update_state():
    state = load_state()  # Lock acquired
    state.update_progress(80)
    save_state(state)     # Lock released

# Background workflow
async def complete_workflow():
    state = load_state()  # Waits for API lock
    state.add_completed("workflow_123")
    save_state(state)
```

**Behavior:**
- Operations serialized by file lock
- Second operation gets fresh state
- Optimistic locking detects conflicts if needed

### Scenario 3: Git Hooks + Manual Commands

```bash
# Git pre-commit hook
python .parac/tools/hooks/auto-maintain.py

# User runs simultaneously
paracle sync --roadmap
```

**Behavior:**
- Both use file locking
- One waits for other to complete
- Atomic writes prevent corruption

## Performance

### Lock Overhead

- Lock acquisition: < 1ms (typical)
- Lock timeout: 10s (configurable)
- File write: 5-20ms (depends on YAML size)

### Recommendations

**For high-throughput scenarios:**
```python
# Batch updates to reduce lock contention
state = load_state()
for item in items:
    state.add_completed(item)
save_state(state)  # Single lock/write
```

**For long-running operations:**
```python
# Load → process → save
state = load_state()
# ... long computation ...
try:
    save_state(state, check_conflict=True)
except StateConflictError:
    # State changed during computation
    # Decide: retry or merge changes
```

## Testing

Comprehensive concurrency tests in `tests/unit/test_state_concurrency.py`:

```bash
# Run concurrency tests
pytest tests/unit/test_state_concurrency.py -v

# Run with slow tests (multiprocess)
pytest tests/unit/test_state_concurrency.py -v -m slow
```

**Test coverage:**
- File locking correctness
- Atomic write verification
- Optimistic locking conflicts
- Concurrent reads (non-blocking)
- Sequential writes (blocking)
- Multiprocess scenarios
- Error handling and recovery
- Lock timeout behavior

## Troubleshooting

### Lock Timeout

**Problem:** `StateLockError: Could not acquire lock within 10s`

**Solutions:**
1. Check for stale locks: `rm .parac/memory/context/*.lock`
2. Increase timeout: `load_state(timeout=30.0)`
3. Identify long-running operations blocking lock

### Conflict Errors

**Problem:** `StateConflictError: State modified by another process`

**Solutions:**
1. Reload state and retry operation
2. Disable conflict check: `save_state(state, check_conflict=False)`
3. Implement retry logic with exponential backoff

### Performance Issues

**Problem:** Slow state operations

**Solutions:**
1. Batch updates instead of frequent saves
2. Reduce lock contention by minimizing critical sections
3. Use async operations where possible
4. Consider distributed locking for multi-server (Phase 6+)

## Future Enhancements

### Phase 5+: Distributed Locking

For multi-server API deployments:

```python
from redis import Redis
from redis.lock import Lock as RedisLock

def save_state_distributed(state, redis_client):
    """Save with Redis distributed lock."""
    with RedisLock(redis_client, "parac:state:lock", timeout=10):
        # Save state...
```

### Phase 6: Event Sourcing

Replace file-based state with event log:

```python
# Append events instead of rewriting state
event_store.append(Event(
    type="progress_updated",
    data={"from": "50%", "to": "75%"},
    timestamp=now(),
))

# Rebuild state from events
state = event_store.replay()
```

## References

- [Architecture Overview](architecture.md)
- [API Reference](api-reference.md)
- [Security Guide](../SECURITY.md)
- [Phase 6 Roadmap](../.parac/roadmap/roadmap.yaml)

---

**Status:** ✅ Production Ready
**Last Updated:** 2026-01-06
**Version:** 1.0
