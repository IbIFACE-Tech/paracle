# Phase 5 Quick Reference

## Installation

```bash
# Install with Phase 5 features
pip install paracle[sandbox]
```

## Components

| Component | Purpose            | Key Class         |
| --------- | ------------------ | ----------------- |
| Sandbox   | Isolated execution | `SandboxManager`  |
| Network   | Network isolation  | `NetworkIsolator` |
| Rollback  | Snapshot recovery  | `RollbackManager` |
| Review    | Artifact approval  | `ReviewManager`   |

## Quick Examples

### Sandbox

```python
from paracle_sandbox import SandboxManager, SandboxConfig

manager = SandboxManager()
async with manager.managed_sandbox(SandboxConfig()) as sandbox:
    result = await sandbox.execute(["python", "-c", "print('Hi')"])
```

### Network

```python
from paracle_isolation import NetworkIsolator, NetworkConfig

isolator = NetworkIsolator()
network = await isolator.create_network(NetworkConfig(internal=True))
```

### Rollback

```python
from paracle_rollback import RollbackManager

manager = RollbackManager()
snapshot_id = await manager.create_snapshot(container_id)
await manager.rollback(snapshot_id, container_id)
```

### Review

```python
from paracle_review import ReviewManager

manager = ReviewManager()
review_id = await manager.create_review("file-001", "file_change", "sandbox-1", {})
await manager.approve(review_id, "alice@example.com")
```

## REST API

```bash
# Create review
POST /api/v1/reviews

# Get review
GET /api/v1/reviews/{id}

# Approve
POST /api/v1/reviews/{id}/approve

# List reviews
GET /api/v1/reviews?status=pending
```

## Configuration

### Sandbox Limits

```python
SandboxConfig(
    cpu_cores=1.0,
    memory_mb=512,
    timeout_seconds=60,
)
```

### Network Policy

```python
NetworkPolicy(
    allow_internet=False,
    allowed_ports=[80, 443],
)
```

### Rollback Policy

```python
RollbackPolicy(
    enabled=True,
    triggers=["on_error"],
    max_snapshots=3,
)
```

### Review Policy

```python
ReviewPolicy(
    trigger_mode="high_risk_only",
    auto_approve_low_risk=True,
    min_approvals=2,
)
```

## Common Patterns

### Safe Execution

```python
# 1. Create sandbox
sandbox = await manager.create(config)

# 2. Snapshot
snapshot_id = await rollback_manager.create_snapshot(sandbox.container.id)

# 3. Execute
try:
    result = await sandbox.execute(command)
except Exception as e:
    await rollback_manager.auto_rollback_on_error(sandbox.container.id, e)
```

### Complete Stack

```python
# Network + Snapshot + Execution + Review
network = await isolator.create_network(NetworkConfig(internal=True))
await isolator.attach_container(sandbox.container.id, network.id)

snapshot_id = await rollback_manager.create_snapshot(sandbox.container.id)

result = await sandbox.execute(command)

review_id = await review_manager.create_review("exec-1", "cmd", sandbox_id, {})
await review_manager.approve(review_id, "alice@example.com")
```

## Monitoring

```python
from paracle_sandbox import SandboxMonitor

async with SandboxMonitor(sandbox, interval_seconds=1.0) as monitor:
    result = await sandbox.execute(command)

    # Get stats
    averages = monitor.get_averages()
    peaks = monitor.get_peaks()
    history = monitor.get_history()
```

## Error Handling

```python
from paracle_sandbox.exceptions import (
    ResourceLimitExceededError,
    SandboxTimeoutError,
)
from paracle_rollback.exceptions import SnapshotNotFoundError
from paracle_review.exceptions import ReviewTimeoutError

try:
    result = await sandbox.execute(command)
except ResourceLimitExceededError:
    print("Resource limit hit")
except SandboxTimeoutError:
    print("Execution timeout")
```

## Examples

- `examples/09_sandbox_execution.py`
- `examples/10_network_isolation.py`
- `examples/11_rollback_on_failure.py`
- `examples/12_artifact_review.py`
- `examples/13_phase5_integration.py`

## Documentation

- [Phase 5 Guide](phase5-guide.md) - Complete guide
- [API Reference](api-reference.md) - API documentation
- [Security](security-audit-report.md) - Security practices

---

**Quick Start**: See [examples/13_phase5_integration.py](../examples/13_phase5_integration.py)
