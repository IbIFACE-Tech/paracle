"""Docker-based sandbox implementation."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

import docker
from docker.errors import APIError, ImageNotFound
from docker.models.containers import Container
from paracle_sandbox.config import SandboxConfig
from paracle_sandbox.exceptions import (
    ResourceLimitError,
    SandboxCreationError,
    SandboxExecutionError,
    SandboxTimeoutError,
)

logger = logging.getLogger(__name__)


class DockerSandbox:
    """Docker container-based sandbox for agent execution.

    Provides isolated execution environment with resource limits,
    network isolation, and security controls.

    Attributes:
        sandbox_id: Unique identifier for this sandbox
        config: Sandbox configuration
        container: Docker container instance (when active)
    """

    def __init__(self, sandbox_id: str, config: SandboxConfig):
        """Initialize Docker sandbox.

        Args:
            sandbox_id: Unique sandbox identifier
            config: Sandbox configuration
        """
        self.sandbox_id = sandbox_id
        self.config = config
        self.container: Container | None = None
        self._client: docker.DockerClient | None = None

    async def start(self) -> None:
        """Start the sandbox container.

        Creates and starts a Docker container with configured resource
        limits and isolation settings.

        Raises:
            SandboxCreationError: If container creation fails
        """
        try:
            # Initialize Docker client
            self._client = docker.from_env()

            # Pull image if not present
            try:
                self._client.images.get(self.config.base_image)
            except ImageNotFound:
                logger.info(f"Pulling image: {self.config.base_image}")
                self._client.images.pull(self.config.base_image)

            # Calculate resource limits
            cpu_quota = int(self.config.cpu_cores * 100000)
            mem_limit = f"{self.config.memory_mb}m"

            # Configure container
            container_config = {
                "image": self.config.base_image,
                "name": f"paracle-sandbox-{self.sandbox_id}",
                "detach": True,
                "command": ["sleep", "infinity"],
                "working_dir": self.config.working_dir,
                "environment": self.config.env_vars,
                "cpu_quota": cpu_quota,
                "cpu_period": 100000,
                "mem_limit": mem_limit,
                "memswap_limit": mem_limit,  # Disable swap
                "network_mode": self.config.network_mode,
                "read_only": self.config.read_only_filesystem,
                "tmpfs": {
                    "/tmp": "rw,noexec,nosuid,size=100m",
                    self.config.working_dir: f"rw,size={self.config.disk_mb}m",
                },
                "security_opt": [],
                "labels": {
                    "paracle.sandbox_id": self.sandbox_id,
                    "paracle.managed": "true",
                },
            }

            # Drop capabilities if configured
            if self.config.drop_capabilities:
                container_config["cap_drop"] = ["ALL"]
                container_config["security_opt"].append("no-new-privileges")

            # Create and start container
            self.container = self._client.containers.create(**container_config)
            self.container.start()

            logger.info(
                f"Sandbox {self.sandbox_id} started with container {self.container.short_id}"
            )

        except (APIError, Exception) as e:
            raise SandboxCreationError(
                f"Failed to create sandbox: {e}", self.sandbox_id
            ) from e

    async def execute(
        self,
        command: str | list[str],
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """Execute command in sandbox.

        Args:
            command: Command to execute (string or list)
            timeout: Execution timeout (uses config default if None)

        Returns:
            Dict with keys: exit_code, stdout, stderr, timed_out

        Raises:
            SandboxExecutionError: If execution fails
            SandboxTimeoutError: If execution times out
        """
        if not self.container:
            raise SandboxExecutionError("Sandbox not started", self.sandbox_id)

        timeout = timeout or self.config.timeout_seconds

        try:
            # Execute command in container
            logger.debug(f"Executing in {self.sandbox_id}: {command}")

            exec_result = self.container.exec_run(
                command,
                stdout=True,
                stderr=True,
                demux=True,
            )

            # Wait for completion with timeout
            start_time = asyncio.get_event_loop().time()

            while True:
                # Check if still running
                self.container.reload()

                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= timeout:
                    # Kill container on timeout
                    self.container.kill()
                    raise SandboxTimeoutError(
                        f"Execution timed out after {timeout}s",
                        self.sandbox_id,
                        timeout,
                    )

                # Check if execution completed
                if exec_result.exit_code is not None:
                    break

                await asyncio.sleep(0.1)

            # Decode output
            stdout_bytes, stderr_bytes = exec_result.output or (b"", b"")
            stdout = (
                stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
            )
            stderr = (
                stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""
            )

            result = {
                "exit_code": exec_result.exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "timed_out": False,
            }

            logger.debug(
                f"Execution in {self.sandbox_id} completed: exit_code={result['exit_code']}"
            )

            return result

        except SandboxTimeoutError:
            raise
        except Exception as e:
            raise SandboxExecutionError(
                f"Execution failed: {e}",
                self.sandbox_id,
            ) from e

    async def get_stats(self) -> dict[str, Any]:
        """Get resource usage statistics.

        Returns:
            Dict with CPU, memory, network, and disk stats

        Raises:
            SandboxExecutionError: If stats retrieval fails
        """
        if not self.container:
            raise SandboxExecutionError("Sandbox not started", self.sandbox_id)

        try:
            self.container.reload()
            stats = self.container.stats(stream=False)

            # Parse CPU stats
            cpu_delta = (
                stats["cpu_stats"]["cpu_usage"]["total_usage"]
                - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            )
            system_delta = (
                stats["cpu_stats"]["system_cpu_usage"]
                - stats["precpu_stats"]["system_cpu_usage"]
            )
            cpu_percent = 0.0
            if system_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * 100.0

            # Parse memory stats
            mem_usage = stats["memory_stats"].get("usage", 0)
            mem_limit = stats["memory_stats"].get("limit", 0)
            mem_percent = 0.0
            if mem_limit > 0:
                mem_percent = (mem_usage / mem_limit) * 100.0

            return {
                "cpu_percent": cpu_percent,
                "memory_bytes": mem_usage,
                "memory_mb": mem_usage / (1024 * 1024),
                "memory_percent": mem_percent,
                "memory_limit_mb": mem_limit / (1024 * 1024),
                "network_rx_bytes": stats.get("networks", {})
                .get("eth0", {})
                .get("rx_bytes", 0),
                "network_tx_bytes": stats.get("networks", {})
                .get("eth0", {})
                .get("tx_bytes", 0),
            }

        except Exception as e:
            raise SandboxExecutionError(
                f"Failed to get stats: {e}",
                self.sandbox_id,
            ) from e

    async def check_limits(self) -> None:
        """Check if resource limits are exceeded.

        Raises:
            ResourceLimitError: If any resource limit is exceeded
        """
        stats = await self.get_stats()

        # Check memory limit
        if stats["memory_percent"] > 95:
            raise ResourceLimitError(
                f"Memory limit exceeded: {stats['memory_percent']:.1f}%",
                self.sandbox_id,
                "memory",
                stats["memory_mb"],
                self.config.memory_mb,
            )

        # Check CPU (warning only, not enforced)
        if stats["cpu_percent"] > self.config.cpu_cores * 100:
            logger.warning(
                f"Sandbox {self.sandbox_id} CPU usage high: {stats['cpu_percent']:.1f}%"
            )

    async def stop(self) -> None:
        """Stop and remove the sandbox container.

        Raises:
            SandboxExecutionError: If stop fails
        """
        if not self.container:
            return

        try:
            logger.info(f"Stopping sandbox {self.sandbox_id}")

            # Stop container with timeout
            self.container.stop(timeout=self.config.cleanup_timeout)

            # Remove container
            self.container.remove(force=True)

            logger.info(f"Sandbox {self.sandbox_id} stopped and removed")

        except Exception as e:
            logger.error(f"Failed to stop sandbox {self.sandbox_id}: {e}")
            # Try force removal
            try:
                if self.container:
                    self.container.remove(force=True)
            except Exception:
                pass

        finally:
            self.container = None
            if self._client:
                self._client.close()
                self._client = None

    @asynccontextmanager
    async def context(self):
        """Context manager for sandbox lifecycle.

        Automatically starts and stops the sandbox.

        Example:
            ```python
            sandbox = DockerSandbox("test-123", config)
            async with sandbox.context():
                result = await sandbox.execute("python script.py")
            ```
        """
        try:
            await self.start()
            yield self
        finally:
            await self.stop()
