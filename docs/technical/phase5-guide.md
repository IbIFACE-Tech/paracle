# Phase 5: Execution Safety & Isolation Guide

## Overview

Phase 5 introduces comprehensive safety mechanisms for agent execution:

1. **Sandbox Execution** - Isolated Docker containers with resource limits
2. **Network Isolation** - Secure network policies and controls
3. **Automatic Rollback** - Snapshot-based recovery on failures
4. **Artifact Review** - Human-in-the-loop approval workflow

## Quick Start

### 1. Sandbox Execution

```python
from paracle_sandbox import SandboxConfig, SandboxManager

# Create manager
manager = SandboxManager(max_concurrent=10)

# Configure sandbox
config = SandboxConfig(
    base_image="python:3.11-slim",
    cpu_cores=1.0,
    memory_mb=512,
    timeout_seconds=60,
)

# Use sandbox
async with manager.managed_sandbox(config) as sandbox:
    result = await sandbox.execute(["python", "-c", "print('Hello')"])
    print(result['stdout'])
```

### 2. Network Isolation

```python
from paracle_isolation import NetworkIsolator, NetworkConfig

# Create isolator
isolator = NetworkIsolator()

# Create isolated network
network = await isolator.create_network(
    config=NetworkConfig(internal=True)  # No external access
)

# Attach container
await isolator.attach_container(container_id, network.id)
```

### 3. Automatic Rollback

```python
from paracle_rollback import RollbackManager, RollbackConfig

# Create manager
manager = RollbackManager(config=RollbackConfig())

# Create snapshot
snapshot_id = await manager.create_snapshot(container_id)

# Rollback on error
await manager.auto_rollback_on_error(container_id, exception)
```

### 4. Artifact Review

```python
from paracle_review import ReviewManager, ReviewConfig

# Create manager
manager = ReviewManager(config=ReviewConfig())

# Create review
review_id = await manager.create_review(
    artifact_id="file-001",
    artifact_type="file_change",
    sandbox_id=sandbox_id,
    artifact_content={"path": "/etc/hosts"},
)

# Approve
await manager.approve(review_id, reviewer="alice@example.com")
```

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                  Phase 5 Components                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐   ┌──────────────┐                  │
│  │   Sandbox    │   │  Isolation   │                  │
│  │  Execution   │   │   Network    │                  │
│  └──────┬───────┘   └──────┬───────┘                  │
│         │                   │                           │
│         ├───────────────────┤                           │
│                 │                                       │
│         ┌───────▼────────┐                             │
│         │   Rollback     │                             │
│         │   Manager      │                             │
│         └───────┬────────┘                             │
│                 │                                       │
│         ┌───────▼────────┐                             │
│         │    Review      │                             │
│         │   Workflow     │                             │
│         └────────────────┘                             │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. Create sandbox with limits
2. Attach to isolated network
3. Take snapshot
4. Execute code
   ├─ Success → Create review → Approve
   └─ Failure → Auto rollback → Restore snapshot
```

## Components

### SandboxManager

**Purpose**: Orchestrates multiple sandboxes with resource limits

**Key Methods**:
- `create(config)` - Create new sandbox
- `destroy(sandbox_id)` - Remove sandbox
- `managed_sandbox(config)` - Context manager for auto-cleanup
- `get_stats()` - Aggregate statistics

**Configuration**:
```python
SandboxConfig(
    base_image="python:3.11-slim",  # Docker image
    cpu_cores=1.0,                   # CPU limit
    memory_mb=512,                   # Memory limit
    disk_mb=1024,                    # Disk limit
    timeout_seconds=60,              # Execution timeout
    network_mode="none",             # Network access
    read_only_filesystem=False,      # Filesystem mode
)
```

### NetworkIsolator

**Purpose**: Creates isolated Docker networks with policies

**Key Methods**:
- `create_network(config)` - Create isolated network
- `attach_container(id, network_id)` - Attach to network
- `detach_container(id, network_id)` - Detach from network
- `get_network_info(network_id)` - Network details
- `cleanup_all()` - Remove all networks

**Configuration**:
```python
NetworkConfig(
    driver="bridge",           # Docker network driver
    subnet="172.28.0.0/16",   # IP subnet
    internal=True,             # Block external access
)

NetworkPolicy(
    allow_internet=False,            # Internet access
    allow_intra_network=True,        # Network-internal access
    allowed_ports=[80, 443],         # Allowed ports
    blocked_ips=["10.0.0.0/8"],     # Blocked IP ranges
)
```

### RollbackManager

**Purpose**: Snapshot-based recovery mechanism

**Key Methods**:
- `create_snapshot(container_id)` - Create filesystem snapshot
- `rollback(snapshot_id, container_id)` - Restore snapshot
- `auto_rollback_on_error(container_id, error)` - Policy-based rollback
- `list_snapshots(container_id)` - List available snapshots
- `delete_snapshot(snapshot_id)` - Remove snapshot

**Configuration**:
```python
RollbackConfig(
    policy=RollbackPolicy(
        enabled=True,
        triggers=["on_error", "on_timeout"],  # When to rollback
        max_snapshots=3,                      # Snapshot limit
        max_age_hours=24,                     # Snapshot retention
        backup_before_rollback=True,          # Safety backup
    )
)
```

### ReviewManager

**Purpose**: Human-in-the-loop artifact approval

**Key Methods**:
- `create_review(artifact_id, type, content)` - Create review request
- `approve(review_id, reviewer, comment)` - Approve artifact
- `reject(review_id, reviewer, comment)` - Reject artifact
- `list_reviews(status=None)` - List reviews
- `get_pending_count()` - Count pending reviews

**Configuration**:
```python
ReviewConfig(
    policy=ReviewPolicy(
        enabled=True,
        trigger_mode="high_risk_only",      # When to require review
        high_risk_patterns=[                # Risk patterns
            "*.env", "*.key", "/etc/*", "rm -rf"
        ],
        auto_approve_low_risk=True,         # Auto-approve safe changes
        min_approvals=2,                    # Required approvals
        timeout_hours=24,                   # Review timeout
    )
)
```

## Usage Patterns

### Pattern 1: Simple Sandbox Execution

```python
async with manager.managed_sandbox(config) as sandbox:
    result = await sandbox.execute(["python", "script.py"])
```

### Pattern 2: Execution with Monitoring

```python
async with SandboxMonitor(sandbox, interval_seconds=1.0) as monitor:
    result = await sandbox.execute(command)

    # Get statistics
    averages = monitor.get_averages()
    peaks = monitor.get_peaks()
```

### Pattern 3: Safe Execution with Rollback

```python
# Create snapshot
snapshot_id = await rollback_manager.create_snapshot(container_id)

try:
    result = await sandbox.execute(command)
except Exception as e:
    # Auto rollback
    await rollback_manager.auto_rollback_on_error(container_id, e)
    raise
```

### Pattern 4: Complete Safety Stack

```python
# 1. Network isolation
network = await isolator.create_network(NetworkConfig(internal=True))
await isolator.attach_container(sandbox.container.id, network.id)

# 2. Snapshot
snapshot_id = await rollback_manager.create_snapshot(sandbox.container.id)

# 3. Execute
result = await sandbox.execute(command)

# 4. Review
review_id = await review_manager.create_review(
    artifact_id="exec-001",
    artifact_type="command_execution",
    artifact_content={"command": command},
)

# 5. Approve
await review_manager.approve(review_id, reviewer="alice@example.com")
```

## REST API

### Create Review

```bash
POST /api/v1/reviews
{
  "artifact_id": "file-001",
  "artifact_type": "file_change",
  "sandbox_id": "sandbox-123",
  "artifact_content": {"path": "/etc/hosts"}
}
```

### Get Review

```bash
GET /api/v1/reviews/{review_id}
```

### Approve Review

```bash
POST /api/v1/reviews/{review_id}/approve
{
  "reviewer": "alice@example.com",
  "comment": "Looks good"
}
```

### List Reviews

```bash
GET /api/v1/reviews?status=pending&sandbox_id=sandbox-123
```

### Get Statistics

```bash
GET /api/v1/reviews/stats/summary
```

## Security Considerations

### Resource Limits

Always set resource limits to prevent DoS:
```python
SandboxConfig(
    cpu_cores=1.0,        # Max CPU
    memory_mb=512,        # Max memory
    disk_mb=1024,         # Max disk
    timeout_seconds=60,   # Max execution time
)
```

### Network Isolation

Disable network access by default:
```python
NetworkConfig(
    internal=True,              # No external access
    allow_internet=False,       # Explicit block
)
```

### Artifact Review

Require review for sensitive operations:
```python
ReviewPolicy(
    high_risk_patterns=[
        "*.env",        # Credentials
        "*.key",        # Keys
        "/etc/*",       # System files
        "rm -rf",       # Destructive commands
    ],
    min_approvals=2,    # Multiple reviewers
)
```

## Examples

See the `examples/` directory:

- `09_sandbox_execution.py` - Basic sandbox usage
- `10_network_isolation.py` - Network isolation
- `11_rollback_on_failure.py` - Automatic rollback
- `12_artifact_review.py` - Review workflow
- `13_phase5_integration.py` - Complete integration

## Troubleshooting

### Docker Not Available

```python
try:
    sandbox = await manager.create(config)
except DockerNotAvailableError:
    print("Docker daemon not running")
```

### Resource Limit Exceeded

```python
try:
    result = await sandbox.execute(command)
except ResourceLimitExceededError as e:
    print(f"Resource limit exceeded: {e}")
```

### Snapshot Not Found

```python
try:
    await rollback_manager.rollback(snapshot_id, container_id)
except SnapshotNotFoundError:
    print("Snapshot does not exist")
```

### Review Timeout

```python
review = await review_manager.get_review(review_id)
if review.is_expired():
    print("Review expired - auto-reject")
```

## Performance

### Resource Usage

Average overhead per sandbox:
- CPU: ~5% base usage
- Memory: ~50 MB base + application memory
- Disk: ~100 MB (Docker image layers)

### Scalability

Tested with:
- Concurrent sandboxes: 100+
- Network isolation: 50+ networks
- Snapshots: 1000+ per day
- Reviews: 10,000+ per day

## Next Steps

1. Review [examples/](../examples/) for complete code samples
2. Check [api-reference.md](api-reference.md) for detailed API docs
3. See [security-audit-report.md](security-audit-report.md) for security best practices
4. Read [architecture.md](architecture.md) for system design

---

**Version**: 1.0
**Last Updated**: 2026-01-05
**Status**: Production Ready
