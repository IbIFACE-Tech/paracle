# Paracle Sandbox - Complete Guide

**Complete isolation for safe agent execution with Docker containers**

## Overview

Paracle Sandbox provides Docker-based sandboxing for secure agent execution with:
- 🔒 **Complete Isolation** - Network, filesystem, and process isolation
- 💾 **Resource Limits** - CPU, memory, disk, and timeout controls
- 📊 **Real-time Monitoring** - Track resource usage with callbacks
- 🚨 **Automatic Rollback** - Clean up on failure
- 🔄 **Batch Execution** - Run multiple jobs in parallel sandboxes

---

## Quick Start

### 1. Health Check

```bash
paracle sandbox health
```

Verifies Docker is available and sandbox execution works.

### 2. Simple Test

```bash
paracle sandbox test --cpu 0.5 --memory 256
```

Runs a simple test to verify sandbox functionality.

### 3. Execute Code

```bash
# Execute Python file in sandbox
paracle sandbox execute agent.py --cpu 1.0 --memory 512 --timeout 300

# With inputs
paracle sandbox execute agent.py --inputs inputs.json --monitor --verbose

# Save results
paracle sandbox execute agent.py --output results.json
```

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                   Paracle Sandbox                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Executor   │  │   Manager    │  │   Monitor    │     │
│  │              │  │              │  │              │     │
│  │ High-level   │  │ Lifecycle    │  │ Resource     │     │
│  │ agent exec   │  │ management   │  │ tracking     │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │             │
│         └─────────────────┼─────────────────┘             │
│                           │                               │
│                  ┌────────▼────────┐                       │
│                  │ DockerSandbox   │                       │
│                  │                 │                       │
│                  │ Container with  │                       │
│                  │ resource limits │                       │
│                  └─────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Docker Engine  │
                  │                 │
                  │  Isolated       │
                  │  containers     │
                  └─────────────────┘
```

### Layers

1. **SandboxExecutor** - High-level API for agent execution
2. **SandboxManager** - Lifecycle and concurrency management
3. **DockerSandbox** - Docker container wrapper
4. **SandboxMonitor** - Real-time resource tracking
5. **SandboxConfig** - Configuration model

---

## Configuration

### SandboxConfig Options

```python
from paracle_sandbox import SandboxConfig

config = SandboxConfig(
    # Docker image
    base_image="paracle/sandbox:latest",
    
    # Resource limits
    cpu_cores=1.0,        # 0.1-16.0 (1.0 = 100% of one core)
    memory_mb=512,        # 128-16384 MB
    disk_mb=1024,         # 256-10240 MB
    timeout_seconds=300,  # 10-3600 seconds
    
    # Network isolation
    network_mode="none",  # "none", "bridge", or "host"
    
    # Security
    read_only_filesystem=True,     # Root filesystem read-only
    drop_capabilities=True,        # Drop all Linux capabilities
    
    # Directories
    working_dir="/workspace",
    
    # Environment
    env_vars={"DEBUG": "1"},
    
    # Cleanup
    cleanup_timeout=30,
)
```

### Recommended Configurations

**Untrusted Code** (Maximum Security):
```python
config = SandboxConfig(
    cpu_cores=0.5,
    memory_mb=256,
    network_mode="none",
    read_only_filesystem=True,
    drop_capabilities=True,
    timeout_seconds=60,
)
```

**Standard Execution**:
```python
config = SandboxConfig(
    cpu_cores=1.0,
    memory_mb=512,
    network_mode="none",
    timeout_seconds=300,
)
```

**High-Performance**:
```python
config = SandboxConfig(
    cpu_cores=4.0,
    memory_mb=2048,
    disk_mb=4096,
    network_mode="bridge",  # Allow network if needed
    timeout_seconds=600,
)
```

---

## Usage Examples

### 1. Simple Execution

```python
import asyncio
from paracle_sandbox import SandboxExecutor, SandboxConfig

async def main():
    executor = SandboxExecutor()
    
    result = await executor.execute_agent(
        agent_code="print('Hello from sandbox!')",
        config=SandboxConfig(cpu_cores=0.5, memory_mb=256),
        monitor=False,
    )
    
    print(f"Success: {result['success']}")
    print(f"Output: {result['result']['stdout']}")

asyncio.run(main())
```

### 2. With Inputs

```python
agent_code = """
import json

with open('/workspace/inputs.json') as f:
    inputs = json.load(f)

name = inputs['name']
print(f"Hello {name}!")
"""

result = await executor.execute_agent(
    agent_code=agent_code,
    inputs={"name": "Paracle"},
    config=SandboxConfig(),
)
```

### 3. With Monitoring

```python
result = await executor.execute_agent(
    agent_code="""
import time
for i in range(5):
    print(f"Iteration {i+1}")
    time.sleep(0.5)
""",
    config=SandboxConfig(),
    monitor=True,  # Enable monitoring
)

# Check monitoring stats
if "monitoring" in result["stats"]:
    print(f"Average CPU: {result['stats']['monitoring']['averages']['cpu_percent']:.1f}%")
    print(f"Peak Memory: {result['stats']['monitoring']['peaks']['memory_mb']:.1f} MB")
```

### 4. Batch Execution

```python
jobs = [
    {"agent_code": f"print('Job {i}')", "inputs": {"id": i}, "monitor": False}
    for i in range(1, 6)
]

results = await executor.execute_batch(jobs, max_concurrent=3)

for i, result in enumerate(results, 1):
    print(f"Job {i}: {'✓' if result['success'] else '✗'}")
```

### 5. Manager Context

```python
from paracle_sandbox import SandboxManager

manager = SandboxManager(max_concurrent=5)

async with manager.managed_sandbox(config) as sandbox:
    result = await sandbox.execute("python3 script.py")
    print(result["stdout"])
# Sandbox automatically destroyed
```

### 6. Custom Monitoring

```python
from paracle_sandbox import SandboxMonitor

def on_warning(stats):
    print(f"⚠️ High usage: CPU {stats['cpu_percent']:.1f}%, Memory {stats['memory_percent']:.1f}%")

monitor = SandboxMonitor(
    sandbox,
    interval_seconds=0.5,
    on_warning=on_warning,
)

async with monitor:
    await sandbox.execute("python3 intensive_task.py")

print(f"Average CPU: {monitor.get_averages()['cpu_percent']:.1f}%")
```

---

## CLI Reference

### Health Check

```bash
paracle sandbox health [--verbose]
```

Checks if sandbox is available (Docker installed and working).

### Execute Code

```bash
paracle sandbox execute <file> [OPTIONS]

Options:
  --cpu FLOAT                CPU cores (0.5-16.0) [default: 1.0]
  --memory INT               Memory in MB [default: 512]
  --timeout INT              Timeout in seconds [default: 300]
  --network [none|bridge|host]  Network mode [default: none]
  --inputs FILE              JSON file with inputs
  --monitor / --no-monitor   Enable monitoring [default: monitor]
  --output FILE              Save results to JSON
  --verbose, -v              Verbose output
```

**Examples:**

```bash
# Simple execution
paracle sandbox execute agent.py

# With resource limits
paracle sandbox execute agent.py --cpu 0.5 --memory 256 --timeout 60

# With inputs and monitoring
paracle sandbox execute agent.py --inputs data.json --monitor --verbose

# Save results
paracle sandbox execute agent.py --output results.json
```

### Test Sandbox

```bash
paracle sandbox test [--cpu 0.5] [--memory 256]
```

Runs a simple test to verify sandbox functionality.

### List Active Sandboxes

```bash
paracle sandbox list
```

Shows all currently active sandboxes with resource usage.

### Cleanup

```bash
paracle sandbox cleanup --all [--force]
```

Destroys all active sandboxes.

---

## Integration with Agents

### In agent_run.py

The sandbox mode is integrated into agent execution:

```bash
# Run agent in sandbox
paracle agents run coder --task "Fix bug" --mode sandbox
```

When `--mode sandbox` is used:
1. Checks if sandbox available (`_check_sandbox_available()`)
2. Falls back to `safe` mode if not available
3. Sets `config["sandbox"] = True` in agent configuration

### Agent Execution Flow

```python
# In agent executor
if config.get("sandbox"):
    # Use SandboxExecutor instead of direct execution
    executor = SandboxExecutor()
    result = await executor.execute_agent(
        agent_code=agent_code,
        config=SandboxConfig(),
    )
```

---

## Security Features

### 1. Network Isolation

**None (Recommended)**:
- No network access
- Maximum security
- Best for untrusted code

```python
config = SandboxConfig(network_mode="none")
```

**Bridge**:
- Limited network access via Docker bridge
- Use when network is required
- Can restrict with firewall rules

```python
config = SandboxConfig(network_mode="bridge")
```

**Host**:
- Direct host network access
- Least secure
- Only for trusted code

### 2. Filesystem Isolation

- **Read-only root**: Prevents system modifications
- **Tmpfs volumes**: Temporary writable storage
- **Working directory**: Isolated `/workspace` with size limit

```python
config = SandboxConfig(
    read_only_filesystem=True,
    working_dir="/workspace",
    disk_mb=1024,
)
```

### 3. Capability Dropping

Drops all Linux capabilities for security:

```python
config = SandboxConfig(drop_capabilities=True)
```

Prevents:
- Raw socket access
- System administration
- Kernel module loading
- Many privilege escalation attacks

### 4. Resource Limits

**CPU**:
```python
config = SandboxConfig(cpu_cores=1.0)  # 100% of one core
```

**Memory**:
```python
config = SandboxConfig(
    memory_mb=512,  # Hard limit
)
```

**Disk**:
```python
config = SandboxConfig(disk_mb=1024)  # Working dir size
```

**Time**:
```python
config = SandboxConfig(timeout_seconds=300)
```

---

## Error Handling

### Exception Hierarchy

```python
SandboxError
├── SandboxCreationError      # Container creation failed
├── SandboxExecutionError     # Execution error
├── ResourceLimitError         # Resource limit exceeded
├── SandboxTimeoutError        # Execution timed out
├── SandboxCleanupError        # Cleanup failed
└── DockerConnectionError      # Docker not available
```

### Error Handling Example

```python
from paracle_sandbox import (
    SandboxExecutor,
    SandboxExecutionError,
    SandboxTimeoutError,
    ResourceLimitError,
)

try:
    result = await executor.execute_agent(
        agent_code=code,
        rollback_on_error=True,  # Auto-cleanup on error
    )
except SandboxTimeoutError as e:
    print(f"Execution timed out after {e.timeout_seconds}s")
except ResourceLimitError as e:
    print(f"Resource limit exceeded: {e.resource_type} ({e.usage}/{e.limit})")
except SandboxExecutionError as e:
    print(f"Execution failed: {e}")
    print(f"Stderr: {e.stderr}")
```

---

## Monitoring & Observability

### Resource Usage Stats

```python
result = await executor.execute_agent(code, monitor=True)

stats = result["stats"]
print(f"CPU: {stats['cpu_percent']:.1f}%")
print(f"Memory: {stats['memory_mb']:.1f} MB ({stats['memory_percent']:.1f}%)")
print(f"Network RX: {stats['network_rx_bytes']} bytes")
print(f"Network TX: {stats['network_tx_bytes']} bytes")

# Monitoring history (if enabled)
if "monitoring" in stats:
    print(f"Average CPU: {stats['monitoring']['averages']['cpu_percent']:.1f}%")
    print(f"Peak Memory: {stats['monitoring']['peaks']['memory_mb']:.1f} MB")
```

### Custom Monitoring

```python
monitor = SandboxMonitor(
    sandbox,
    interval_seconds=1.0,
    on_warning=lambda stats: print(f"⚠️ High usage: {stats}"),
    on_limit_exceeded=lambda stats: print(f"🚨 Limit exceeded: {stats}"),
)

async with monitor:
    await sandbox.execute("heavy_task.py")

# Get history
history = monitor.get_history(limit=10)  # Last 10 samples
averages = monitor.get_averages()
peaks = monitor.get_peaks()
```

---

## Best Practices

### 1. Always Use Resource Limits

```python
# ✅ Good
config = SandboxConfig(
    cpu_cores=1.0,
    memory_mb=512,
    timeout_seconds=300,
)

# ❌ Bad (no limits)
config = SandboxConfig()
```

### 2. Enable Monitoring for Long Tasks

```python
# ✅ Good for long-running tasks
result = await executor.execute_agent(code, monitor=True)

# ⚠️ OK for quick tasks
result = await executor.execute_agent(code, monitor=False)
```

### 3. Handle Errors Gracefully

```python
# ✅ Good
result = await executor.execute_agent(
    code,
    rollback_on_error=True,  # Auto-cleanup
)

if not result["success"]:
    print(f"Error: {result['error']}")
    # Handle error
```

### 4. Use Batch Execution for Multiple Jobs

```python
# ✅ Good - parallel execution
results = await executor.execute_batch(jobs, max_concurrent=3)

# ❌ Bad - sequential
for job in jobs:
    await executor.execute_agent(job["code"])
```

### 5. Network Isolation by Default

```python
# ✅ Good - no network by default
config = SandboxConfig(network_mode="none")

# ⚠️ Only when necessary
config = SandboxConfig(network_mode="bridge")
```

---

## Troubleshooting

### Docker Not Available

**Error**: `Docker not available: ...`

**Solutions**:
1. Install Docker: https://docs.docker.com/get-docker/
2. Start Docker daemon
3. Add user to docker group (Linux):
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```
4. Check Docker is running:
   ```bash
   docker ps
   ```

### Image Not Found

**Error**: `Image not found: paracle/sandbox:latest`

**Solutions**:
1. Pull image manually:
   ```bash
   docker pull paracle/sandbox:latest
   ```
2. Or use a different base image:
   ```python
   config = SandboxConfig(base_image="python:3.10-slim")
   ```

### Memory Limit Exceeded

**Error**: `ResourceLimitError: Memory limit exceeded`

**Solutions**:
1. Increase memory limit:
   ```python
   config = SandboxConfig(memory_mb=1024)  # Increase to 1GB
   ```
2. Optimize agent code to use less memory
3. Process data in chunks

### Timeout

**Error**: `SandboxTimeoutError: Execution timed out`

**Solutions**:
1. Increase timeout:
   ```python
   config = SandboxConfig(timeout_seconds=600)
   ```
2. Optimize agent code
3. Use batch execution with shorter timeouts

### Permission Denied

**Error**: `Permission denied` when accessing files

**Solutions**:
1. Files must be in working directory (`/workspace`)
2. Check filesystem is not read-only for writes
3. Use tmpfs volumes for temporary files

---

## Performance Considerations

### CPU Allocation

- **0.5 cores**: Light tasks, quick scripts
- **1.0 cores**: Standard execution
- **2.0+ cores**: CPU-intensive tasks, data processing

### Memory Allocation

- **256 MB**: Minimal scripts, simple tasks
- **512 MB**: Standard Python execution
- **1024 MB**: Data processing, ML inference
- **2048+ MB**: Heavy computations, large datasets

### Disk Allocation

- **256 MB**: Small scripts, minimal files
- **1024 MB**: Standard workloads
- **2048+ MB**: Large file processing

### Timeout Settings

- **60s**: Quick tasks, API calls
- **300s**: Standard execution (default)
- **600s+**: Long-running computations

---

## FAQ

**Q: Is Docker required?**
A: Yes, Paracle Sandbox requires Docker for container-based isolation.

**Q: Can I use custom Docker images?**
A: Yes, specify `base_image` in SandboxConfig.

**Q: What happens if a limit is exceeded?**
A: The sandbox is killed and a ResourceLimitError is raised.

**Q: Can sandboxes communicate?**
A: No, each sandbox is isolated. Use shared storage or external services.

**Q: How many concurrent sandboxes can I run?**
A: Limited by `SandboxManager(max_concurrent=N)` and host resources.

**Q: What about GPU access?**
A: Not currently supported. Future feature for ML workloads.

---

## See Also

- [Examples](../examples/25_sandbox_basics.py) - Complete code examples
- [API Reference](../packages/paracle_sandbox/README.md) - Full API documentation
- [Security Policy](../.parac/policies/SECURITY.md) - Security best practices
- [Docker Documentation](https://docs.docker.com/) - Docker setup and usage

---

**Status**: Production Ready | **Version**: 1.0.1 | **Last Updated**: 2026-01-10
