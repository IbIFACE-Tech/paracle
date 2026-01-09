"""Sandbox configuration."""

from typing import Literal

from pydantic import BaseModel, Field

NetworkMode = Literal["none", "bridge", "host"]


class SandboxConfig(BaseModel):
    """Configuration for sandbox execution environment.

    Defines resource limits, isolation settings, and container configuration
    for safe agent execution.

    Attributes:
        base_image: Docker base image (default: paracle/sandbox:latest)
        cpu_cores: CPU core limit (0.5 = 50% of one core)
        memory_mb: Memory limit in megabytes
        disk_mb: Disk space limit in megabytes
        timeout_seconds: Maximum execution time
        network_mode: Network isolation mode (none, bridge, host)
        read_only_filesystem: Mount root filesystem as read-only
        drop_capabilities: Drop Linux capabilities for security
        working_dir: Working directory inside container
        env_vars: Environment variables to inject
    """

    base_image: str = Field(
        default="paracle/sandbox:latest", description="Docker image for sandbox"
    )

    cpu_cores: float = Field(
        default=1.0, ge=0.1, le=16.0, description="CPU cores (0.5 = 50% of one core)"
    )

    memory_mb: int = Field(
        default=512, ge=128, le=16384, description="Memory limit in MB"
    )

    disk_mb: int = Field(
        default=1024, ge=256, le=10240, description="Disk space limit in MB"
    )

    timeout_seconds: int = Field(
        default=300, ge=10, le=3600, description="Execution timeout"
    )

    network_mode: NetworkMode = Field(
        default="none", description="Network isolation mode"
    )

    read_only_filesystem: bool = Field(
        default=True, description="Mount root filesystem as read-only"
    )

    drop_capabilities: bool = Field(
        default=True, description="Drop all Linux capabilities"
    )

    working_dir: str = Field(default="/workspace", description="Working directory")

    env_vars: dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )

    cleanup_timeout: int = Field(
        default=30, ge=5, le=300, description="Timeout for cleanup operations"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "base_image": "paracle/sandbox:latest",
                    "cpu_cores": 1.0,
                    "memory_mb": 512,
                    "disk_mb": 1024,
                    "timeout_seconds": 300,
                    "network_mode": "none",
                    "read_only_filesystem": True,
                    "drop_capabilities": True,
                }
            ]
        }
    }
