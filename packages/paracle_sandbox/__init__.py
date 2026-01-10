"""Paracle Sandbox - Isolated execution environments for agents.

This package provides Docker-based sandboxing for safe agent execution with
resource limits, network isolation, and filesystem controls.

Components:
- SandboxManager: Orchestrates sandbox lifecycle
- DockerSandbox: Docker container wrapper with resource limits
- SandboxConfig: Configuration for sandbox environments
- SandboxMonitor: Real-time resource usage tracking

Example:
    ```python
    from paracle_sandbox import SandboxManager, SandboxConfig

    # Create sandbox manager
    manager = SandboxManager()

    # Configure sandbox
    config = SandboxConfig(
        base_image="paracle/sandbox:latest",
        cpu_cores=1.0,
        memory_mb=512,
        timeout_seconds=300
    )

    # Create and use sandbox
    async with manager.create(config) as sandbox:
        result = await sandbox.execute(agent_code)
        print(f"Result: {result}")
    ```
"""

from paracle_sandbox.config import SandboxConfig
from paracle_sandbox.docker_sandbox import DockerSandbox
from paracle_sandbox.exceptions import (
    DockerConnectionError,
    ResourceLimitError,
    SandboxCleanupError,
    SandboxCreationError,
    SandboxError,
    SandboxExecutionError,
    SandboxTimeoutError,
)
from paracle_sandbox.executor import SandboxExecutor
from paracle_sandbox.manager import SandboxManager
from paracle_sandbox.monitor import SandboxMonitor

__all__ = [
    "SandboxManager",
    "DockerSandbox",
    "SandboxConfig",
    "SandboxMonitor",
    "SandboxExecutor",
    "SandboxError",
    "SandboxCreationError",
    "SandboxExecutionError",
    "ResourceLimitError",
    "SandboxTimeoutError",
    "SandboxCleanupError",
    "DockerConnectionError",
]

__version__ = "1.0.1"
