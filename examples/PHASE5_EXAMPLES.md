# Phase 5 Examples - Execution Safety & Isolation

## Overview

These examples demonstrate the Phase 5 safety and isolation features added to Paracle.

## Prerequisites

### Docker

All Phase 5 examples require Docker to be running:

```bash
# Check Docker is running
docker --version
docker info

# If not running:
# - Windows: Start Docker Desktop
# - Linux: sudo systemctl start docker
# - Mac: Start Docker Desktop
```

### Python Dependencies

```bash
# Install Paracle with sandbox support
pip install -e ".[sandbox]"

# Or with uv
uv sync
```

## Examples

### 09. Sandbox Execution (`09_sandbox_execution.py`)

**Demonstrates**: Basic Docker sandbox with resource monitoring

**Features**:

- Creating sandboxes with resource limits
- Executing code in isolation
- Real-time resource monitoring
- Automatic cleanup

**Run**:

```bash
uv run python examples/09_sandbox_execution.py
```

**Output**:

```
=== Docker Sandbox Example ===

1. Creating sandbox...
   ✓ Sandbox created: sandbox-01hk...

2. Starting resource monitor...
   ✓ Monitor started

3. Executing Python code in sandbox...
   Exit code: 0
   Output:
   Python 3.11.x
   Hello from sandbox!

4. Resource usage:
   CPU: 12.5%
   Memory: 45.2 MB (8.8%)
   ...
```

**Use Case**: Safe execution of untrusted code with resource limits

---

### 10. Network Isolation (`10_network_isolation.py`)

**Demonstrates**: Network isolation and security policies

**Features**:

- Creating isolated Docker networks
- Attaching containers to networks
- Network policy enforcement
- Inter-container communication control

**Run**:

```bash
uv run python examples/10_network_isolation.py
```

**Output**:

```
=== Network Isolation Example ===

1. Creating isolated network...
   ✓ Network created: paracle-isolated (a8f2d3)

2. Defining network policy...
   ✓ Policy defined
     - Internet: False
     - Allowed ports: [80, 443]
   ...
```

**Use Case**: Secure agent execution with controlled network access

---

### 11. Rollback on Failure (`11_rollback_on_failure.py`)

**Demonstrates**: Automatic snapshot-based recovery

**Features**:

- Creating filesystem snapshots
- Automatic rollback on errors
- Manual rollback to checkpoints
- Snapshot retention policies

**Run**:

```bash
uv run python examples/11_rollback_on_failure.py
```

**Output**:

```
=== Automatic Rollback Example ===

1. Creating sandbox...
   ✓ Sandbox created: sandbox-01hk...

2. Creating initial snapshot...
   ✓ Snapshot created: snap-01hk...

5. Simulating execution failure...
   ✗ Execution failed: Simulated failure

6. Performing automatic rollback...
   ✓ Automatic rollback successful

7. Verifying file restoration...
   File contents: test data
   ✓ File restored successfully!
   ...
```

**Use Case**: Recovery from failed operations with state restoration

---

### 12. Artifact Review (`12_artifact_review.py`)

**Demonstrates**: Human-in-the-loop artifact approval

**Features**:

- Creating artifact reviews
- Risk assessment (low/medium/high)
- Multi-reviewer approval workflow
- Auto-approval for low-risk changes

**Run**:

```bash
uv run python examples/12_artifact_review.py
```

**Output**:

```
=== Artifact Review Workflow Example ===

1. Creating low-risk artifact review...
   Review ID: review-01hk...
   Risk Level: low
   Status: approved
   ✓ Auto-approved (low risk)

2. Creating high-risk artifact review...
   Review ID: review-01hj...
   Risk Level: high
   Status: pending
   Required approvals: 2

3. First reviewer approving...
   Approvals: 1/2
   Status: pending

4. Second reviewer approving...
   Approvals: 2/2
   Status: approved
   ✓ Fully approved!
   ...
```

**Use Case**: Human oversight for sensitive operations (ISO 42001 compliance)

---

### 13. Phase 5 Integration (`13_phase5_integration.py`)

**Demonstrates**: Complete Phase 5 safety stack

**Features**:

- All Phase 5 components working together
- Sandbox + Network + Rollback + Review
- Error handling and recovery
- Production-ready patterns

**Run**:

```bash
uv run python examples/13_phase5_integration.py
```

**Output**:

```
=== Complete Phase 5 Integration ===

==================================================
Test 1: Successful Execution
==================================================
→ Creating isolated network...
→ Creating sandbox...
→ Attaching to network...
→ Creating snapshot...
→ Executing code...
✓ Execution successful
  Output: Hello from safe sandbox!
→ Creating artifact review...
  Review: approved (risk: low)
→ Cleaning up...

==================================================
Test 2: Failed Execution (with rollback)
==================================================
→ Creating isolated network...
→ Creating sandbox...
→ Attaching to network...
→ Creating snapshot...
→ Executing code...
✗ Execution failed: Simulated failure
→ Rolling back...
✓ Rollback successful
✓ Failure handled gracefully
   ...
```

**Use Case**: Production deployment with full safety guarantees

---

## Common Patterns

### Pattern 1: Simple Sandbox

```python
from paracle_sandbox import SandboxManager, SandboxConfig

manager = SandboxManager()
config = SandboxConfig(
    base_image="python:3.11-slim",
    cpu_cores=1.0,
    memory_mb=512,
)

async with manager.managed_sandbox(config) as sandbox:
    result = await sandbox.execute(["python", "-c", "print('Hello')"])
    print(result['stdout'])
```

### Pattern 2: With Monitoring

```python
from paracle_sandbox import SandboxMonitor

async with SandboxMonitor(sandbox, interval_seconds=1.0) as monitor:
    result = await sandbox.execute(command)
    averages = monitor.get_averages()
    print(f"Avg CPU: {averages['cpu_percent']:.1f}%")
```

### Pattern 3: Safe Execution

```python
from paracle_rollback import RollbackManager

# Create snapshot
snapshot_id = await rollback_manager.create_snapshot(container_id)

try:
    result = await sandbox.execute(command)
except Exception as e:
    # Auto rollback
    await rollback_manager.auto_rollback_on_error(container_id, e)
    raise
```

### Pattern 4: Complete Safety

```python
# 1. Network isolation
network = await isolator.create_network(NetworkConfig(internal=True))
await isolator.attach_container(sandbox.container.id, network.id)

# 2. Snapshot
snapshot_id = await rollback_manager.create_snapshot(sandbox.container.id)

# 3. Execute
result = await sandbox.execute(command)

# 4. Review
review_id = await review_manager.create_review(...)
await review_manager.approve(review_id, reviewer="alice@example.com")
```

## Troubleshooting

### Docker Not Running

```
Error: Cannot connect to the Docker daemon
```

**Solution**: Start Docker Desktop or Docker daemon

```bash
# Windows: Start Docker Desktop
# Linux
sudo systemctl start docker

# Mac: Start Docker Desktop
```

### Permission Denied

```
Error: Permission denied while trying to connect to Docker
```

**Solution**: Add user to docker group (Linux)

```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Resource Limits

```
Error: ResourceLimitExceededError: Memory limit exceeded
```

**Solution**: Increase resource limits in config

```python
SandboxConfig(
    memory_mb=1024,  # Increase from 512
    cpu_cores=2.0,   # Increase from 1.0
)
```

### Network Issues

```
Error: Network not found
```

**Solution**: Clean up old networks

```bash
# Remove all paracle networks
docker network ls | grep paracle | awk '{print $1}' | xargs docker network rm
```

### Snapshot Storage

```
Error: No space left on device
```

**Solution**: Clean up old snapshots

```python
# Delete old snapshots
for snap_id in rollback_manager.list_snapshots():
    await rollback_manager.delete_snapshot(snap_id)
```

## Performance Tips

1. **Use smaller base images**: `python:3.11-slim` instead of `python:3.11`
2. **Reuse networks**: Create once, attach multiple containers
3. **Limit snapshot retention**: Use `max_snapshots=3` policy
4. **Monitor resource usage**: Use `SandboxMonitor` to track overhead
5. **Cleanup regularly**: Destroy sandboxes and networks when done

## Security Notes

1. **Always use resource limits**: Prevent DoS attacks
2. **Disable network by default**: Use `network_mode="none"`
3. **Review high-risk artifacts**: Set `trigger_mode="high_risk_only"`
4. **Snapshot before risky ops**: Enable `triggers=["on_error"]`
5. **Timeout everything**: Set `timeout_seconds` on all operations

## Next Steps

1. Read [docs/phase5-guide.md](../docs/phase5-guide.md) for complete documentation
2. Review [docs/phase5-quickref.md](../docs/phase5-quickref.md) for quick reference
3. Check [tests/unit/test_phase5_smoke.py](../tests/unit/test_phase5_smoke.py) for test examples
4. See [.parac/memory/summaries/phase5_completion.md](../.parac/memory/summaries/phase5_completion.md) for implementation details

## Support

- **Documentation**: [docs/phase5-guide.md](../docs/phase5-guide.md)
- **API Reference**: [docs/api-reference.md](../docs/api-reference.md)
- **Security**: [docs/security-audit-report.md](../docs/security-audit-report.md)
- **Issues**: <https://github.com/IbIFACE-Tech/paracle-lite/issues>

---

**Last Updated**: 2026-01-05
**Version**: paracle-lite v0.0.1
**Status**: Production Ready
