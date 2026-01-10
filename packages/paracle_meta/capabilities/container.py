"""Container capability for MetaAgent.

Provides Docker/Podman container operations:
- Build images
- Run containers
- Manage containers (start, stop, restart, remove)
- View logs
- Execute commands in containers
- Image management

Requires Docker CLI or Podman CLI to be available.
"""

import asyncio
import json
import os
import time
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import Field

from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)


class ContainerRuntime(str, Enum):
    """Container runtime."""

    DOCKER = "docker"
    PODMAN = "podman"


class ContainerConfig(CapabilityConfig):
    """Configuration for container capability."""

    runtime: str = Field(
        default="auto",
        description="Container runtime: auto, docker, or podman",
    )
    default_registry: str = Field(
        default="docker.io",
        description="Default container registry",
    )
    timeout: float = Field(
        default=300.0,
        description="Default command timeout in seconds",
    )
    build_timeout: float = Field(
        default=600.0,
        description="Build timeout in seconds",
    )


class ContainerResult:
    """Result of a container operation."""

    def __init__(
        self,
        success: bool,
        operation: str,
        data: dict[str, Any] | None = None,
        error: str | None = None,
        stdout: str | None = None,
        stderr: str | None = None,
        duration_ms: float = 0,
    ):
        self.success = success
        self.operation = operation
        self.data = data or {}
        self.error = error
        self.stdout = stdout
        self.stderr = stderr
        self.duration_ms = duration_ms

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "success": self.success,
            "operation": self.operation,
            "duration_ms": self.duration_ms,
        }
        if self.data:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error
        if self.stdout:
            result["stdout"] = self.stdout
        if self.stderr:
            result["stderr"] = self.stderr
        return result


class ContainerCapability(BaseCapability):
    """Container capability for MetaAgent.

    Provides Docker/Podman container operations:
    - Build images from Dockerfile
    - Run containers with port mapping and volumes
    - Manage container lifecycle
    - View container logs
    - Execute commands in running containers
    - Image management (pull, push, list, remove)

    Example:
        >>> container = ContainerCapability()
        >>> await container.initialize()

        >>> # Build an image
        >>> result = await container.build(
        ...     path="./app",
        ...     tag="myapp:latest"
        ... )

        >>> # Run a container
        >>> result = await container.run(
        ...     image="nginx:latest",
        ...     name="web",
        ...     ports={"80": "8080"},
        ...     detach=True
        ... )

        >>> # View logs
        >>> result = await container.logs(container="web")

        >>> # Stop container
        >>> result = await container.stop(container="web")
    """

    name = "container"
    description = "Docker/Podman container operations"

    def __init__(self, config: ContainerConfig | None = None):
        """Initialize container capability."""
        super().__init__(config or ContainerConfig())
        self.config: ContainerConfig = self.config
        self._runtime: str | None = None

    async def initialize(self) -> None:
        """Initialize container capability and detect runtime."""
        self._runtime = await self._detect_runtime()
        await super().initialize()

    async def _detect_runtime(self) -> str:
        """Detect available container runtime."""
        if self.config.runtime != "auto":
            return self.config.runtime

        # Try Docker first
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            if proc.returncode == 0:
                return "docker"
        except FileNotFoundError:
            pass

        # Try Podman
        try:
            proc = await asyncio.create_subprocess_exec(
                "podman", "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            if proc.returncode == 0:
                return "podman"
        except FileNotFoundError:
            pass

        raise RuntimeError("No container runtime found (docker or podman)")

    async def _run_command(
        self,
        args: list[str],
        timeout: float | None = None,
        cwd: str | None = None,
    ) -> tuple[int, str, str]:
        """Run a container command."""
        timeout = timeout or self.config.timeout
        cmd = [self._runtime] + args

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise TimeoutError(f"Command timed out after {timeout}s")

        return (
            proc.returncode or 0,
            stdout.decode("utf-8", errors="replace"),
            stderr.decode("utf-8", errors="replace"),
        )

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute container operation.

        Args:
            action: Operation to perform
            **kwargs: Operation-specific parameters

        Returns:
            CapabilityResult with operation outcome
        """
        if not self._initialized:
            await self.initialize()

        action = kwargs.pop("action", "list")
        start_time = time.time()

        try:
            if action == "build":
                result = await self._build(**kwargs)
            elif action == "run":
                result = await self._run(**kwargs)
            elif action == "start":
                result = await self._start(**kwargs)
            elif action == "stop":
                result = await self._stop(**kwargs)
            elif action == "restart":
                result = await self._restart(**kwargs)
            elif action == "remove":
                result = await self._remove(**kwargs)
            elif action == "logs":
                result = await self._logs(**kwargs)
            elif action == "exec":
                result = await self._exec(**kwargs)
            elif action == "list":
                result = await self._list(**kwargs)
            elif action == "inspect":
                result = await self._inspect(**kwargs)
            elif action == "pull":
                result = await self._pull(**kwargs)
            elif action == "push":
                result = await self._push(**kwargs)
            elif action == "images":
                result = await self._images(**kwargs)
            elif action == "rmi":
                result = await self._remove_image(**kwargs)
            elif action == "stats":
                result = await self._stats(**kwargs)
            else:
                return CapabilityResult.error_result(
                    capability=self.name,
                    error=f"Unknown action: {action}",
                )

            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.success_result(
                capability=self.name,
                output=result.to_dict(),
                duration_ms=duration_ms,
                action=action,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.error_result(
                capability=self.name,
                error=str(e),
                duration_ms=duration_ms,
                action=action,
            )

    async def _build(
        self,
        path: str = ".",
        tag: str | None = None,
        dockerfile: str = "Dockerfile",
        build_args: dict[str, str] | None = None,
        no_cache: bool = False,
        **kwargs,
    ) -> ContainerResult:
        """Build a container image.

        Args:
            path: Build context path
            tag: Image tag
            dockerfile: Dockerfile path
            build_args: Build arguments
            no_cache: Don't use cache

        Returns:
            ContainerResult
        """
        start_time = time.time()
        args = ["build"]

        if tag:
            args.extend(["-t", tag])

        args.extend(["-f", dockerfile])

        if no_cache:
            args.append("--no-cache")

        for key, value in (build_args or {}).items():
            args.extend(["--build-arg", f"{key}={value}"])

        args.append(path)

        returncode, stdout, stderr = await self._run_command(
            args, timeout=self.config.build_timeout
        )

        duration_ms = (time.time() - start_time) * 1000

        if returncode != 0:
            return ContainerResult(
                success=False,
                operation="build",
                error=stderr or stdout,
                stdout=stdout,
                stderr=stderr,
                duration_ms=duration_ms,
            )

        return ContainerResult(
            success=True,
            operation="build",
            data={"tag": tag, "path": path},
            stdout=stdout,
            duration_ms=duration_ms,
        )

    async def _run(
        self,
        image: str,
        name: str | None = None,
        command: str | list[str] | None = None,
        ports: dict[str, str] | None = None,
        volumes: dict[str, str] | None = None,
        env: dict[str, str] | None = None,
        detach: bool = True,
        remove: bool = False,
        network: str | None = None,
        **kwargs,
    ) -> ContainerResult:
        """Run a container.

        Args:
            image: Image to run
            name: Container name
            command: Command to run
            ports: Port mappings {"container_port": "host_port"}
            volumes: Volume mappings {"host_path": "container_path"}
            env: Environment variables
            detach: Run in background
            remove: Remove container after exit
            network: Network to connect to

        Returns:
            ContainerResult
        """
        start_time = time.time()
        args = ["run"]

        if detach:
            args.append("-d")

        if remove:
            args.append("--rm")

        if name:
            args.extend(["--name", name])

        if network:
            args.extend(["--network", network])

        for container_port, host_port in (ports or {}).items():
            args.extend(["-p", f"{host_port}:{container_port}"])

        for host_path, container_path in (volumes or {}).items():
            args.extend(["-v", f"{host_path}:{container_path}"])

        for key, value in (env or {}).items():
            args.extend(["-e", f"{key}={value}"])

        args.append(image)

        if command:
            if isinstance(command, str):
                args.extend(command.split())
            else:
                args.extend(command)

        returncode, stdout, stderr = await self._run_command(args)
        duration_ms = (time.time() - start_time) * 1000

        if returncode != 0:
            return ContainerResult(
                success=False,
                operation="run",
                error=stderr or stdout,
                stderr=stderr,
                duration_ms=duration_ms,
            )

        container_id = stdout.strip()[:12] if detach else None

        return ContainerResult(
            success=True,
            operation="run",
            data={
                "image": image,
                "name": name,
                "container_id": container_id,
                "detached": detach,
            },
            stdout=stdout,
            duration_ms=duration_ms,
        )

    async def _start(self, container: str, **kwargs) -> ContainerResult:
        """Start a stopped container."""
        start_time = time.time()
        returncode, stdout, stderr = await self._run_command(["start", container])
        duration_ms = (time.time() - start_time) * 1000

        if returncode != 0:
            return ContainerResult(
                success=False,
                operation="start",
                error=stderr,
                duration_ms=duration_ms,
            )

        return ContainerResult(
            success=True,
            operation="start",
            data={"container": container},
            duration_ms=duration_ms,
        )

    async def _stop(
        self,
        container: str,
        timeout: int = 10,
        **kwargs,
    ) -> ContainerResult:
        """Stop a running container."""
        start_time = time.time()
        returncode, stdout, stderr = await self._run_command(
            ["stop", "-t", str(timeout), container]
        )
        duration_ms = (time.time() - start_time) * 1000

        if returncode != 0:
            return ContainerResult(
                success=False,
                operation="stop",
                error=stderr,
                duration_ms=duration_ms,
            )

        return ContainerResult(
            success=True,
            operation="stop",
            data={"container": container},
            duration_ms=duration_ms,
        )

    async def _restart(self, container: str, **kwargs) -> ContainerResult:
        """Restart a container."""
        start_time = time.time()
        returncode, stdout, stderr = await self._run_command(["restart", container])
        duration_ms = (time.time() - start_time) * 1000

        if returncode != 0:
            return ContainerResult(
                success=False,
                operation="restart",
                error=stderr,
                duration_ms=duration_ms,
            )

        return ContainerResult(
            success=True,
            operation="restart",
            data={"container": container},
            duration_ms=duration_ms,
        )

    async def _remove(
        self,
        container: str,
        force: bool = False,
        volumes: bool = False,
        **kwargs,
    ) -> ContainerResult:
        """Remove a container."""
        start_time = time.time()
        args = ["rm"]

        if force:
            args.append("-f")
        if volumes:
            args.append("-v")

        args.append(container)

        returncode, stdout, stderr = await self._run_command(args)
        duration_ms = (time.time() - start_time) * 1000

        if returncode != 0:
            return ContainerResult(
                success=False,
                operation="remove",
                error=stderr,
                duration_ms=duration_ms,
            )

        return ContainerResult(
            success=True,
            operation="remove",
            data={"container": container},
            duration_ms=duration_ms,
        )

    async def _logs(
        self,
        container: str,
        tail: int | None = 100,
        follow: bool = False,
        timestamps: bool = False,
        **kwargs,
    ) -> ContainerResult:
        """Get container logs."""
        start_time = time.time()
        args = ["logs"]

        if tail:
            args.extend(["--tail", str(tail)])
        if timestamps:
            args.append("-t")

        args.append(container)

        returncode, stdout, stderr = await self._run_command(args)
        duration_ms = (time.time() - start_time) * 1000

        return ContainerResult(
            success=returncode == 0,
            operation="logs",
            data={"container": container, "tail": tail},
            stdout=stdout,
            stderr=stderr,
            error=stderr if returncode != 0 else None,
            duration_ms=duration_ms,
        )

    async def _exec(
        self,
        container: str,
        command: str | list[str],
        interactive: bool = False,
        tty: bool = False,
        user: str | None = None,
        workdir: str | None = None,
        **kwargs,
    ) -> ContainerResult:
        """Execute command in running container."""
        start_time = time.time()
        args = ["exec"]

        if interactive:
            args.append("-i")
        if tty:
            args.append("-t")
        if user:
            args.extend(["-u", user])
        if workdir:
            args.extend(["-w", workdir])

        args.append(container)

        if isinstance(command, str):
            args.extend(command.split())
        else:
            args.extend(command)

        returncode, stdout, stderr = await self._run_command(args)
        duration_ms = (time.time() - start_time) * 1000

        return ContainerResult(
            success=returncode == 0,
            operation="exec",
            data={"container": container, "command": command},
            stdout=stdout,
            stderr=stderr,
            error=stderr if returncode != 0 else None,
            duration_ms=duration_ms,
        )

    async def _list(
        self,
        all: bool = False,
        filters: dict[str, str] | None = None,
        **kwargs,
    ) -> ContainerResult:
        """List containers."""
        start_time = time.time()
        args = ["ps", "--format", "json"]

        if all:
            args.append("-a")

        for key, value in (filters or {}).items():
            args.extend(["-f", f"{key}={value}"])

        returncode, stdout, stderr = await self._run_command(args)
        duration_ms = (time.time() - start_time) * 1000

        containers = []
        if stdout.strip():
            for line in stdout.strip().split("\n"):
                try:
                    containers.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

        return ContainerResult(
            success=returncode == 0,
            operation="list",
            data={"containers": containers, "count": len(containers)},
            error=stderr if returncode != 0 else None,
            duration_ms=duration_ms,
        )

    async def _inspect(self, container: str, **kwargs) -> ContainerResult:
        """Inspect a container."""
        start_time = time.time()
        returncode, stdout, stderr = await self._run_command(
            ["inspect", container]
        )
        duration_ms = (time.time() - start_time) * 1000

        info = None
        if stdout.strip():
            try:
                info = json.loads(stdout)[0]
            except (json.JSONDecodeError, IndexError):
                pass

        return ContainerResult(
            success=returncode == 0,
            operation="inspect",
            data={"container": container, "info": info},
            error=stderr if returncode != 0 else None,
            duration_ms=duration_ms,
        )

    async def _pull(self, image: str, **kwargs) -> ContainerResult:
        """Pull an image."""
        start_time = time.time()
        returncode, stdout, stderr = await self._run_command(
            ["pull", image],
            timeout=self.config.build_timeout,
        )
        duration_ms = (time.time() - start_time) * 1000

        return ContainerResult(
            success=returncode == 0,
            operation="pull",
            data={"image": image},
            stdout=stdout,
            error=stderr if returncode != 0 else None,
            duration_ms=duration_ms,
        )

    async def _push(self, image: str, **kwargs) -> ContainerResult:
        """Push an image."""
        start_time = time.time()
        returncode, stdout, stderr = await self._run_command(
            ["push", image],
            timeout=self.config.build_timeout,
        )
        duration_ms = (time.time() - start_time) * 1000

        return ContainerResult(
            success=returncode == 0,
            operation="push",
            data={"image": image},
            stdout=stdout,
            error=stderr if returncode != 0 else None,
            duration_ms=duration_ms,
        )

    async def _images(self, **kwargs) -> ContainerResult:
        """List images."""
        start_time = time.time()
        returncode, stdout, stderr = await self._run_command(
            ["images", "--format", "json"]
        )
        duration_ms = (time.time() - start_time) * 1000

        images = []
        if stdout.strip():
            for line in stdout.strip().split("\n"):
                try:
                    images.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

        return ContainerResult(
            success=returncode == 0,
            operation="images",
            data={"images": images, "count": len(images)},
            error=stderr if returncode != 0 else None,
            duration_ms=duration_ms,
        )

    async def _remove_image(
        self,
        image: str,
        force: bool = False,
        **kwargs,
    ) -> ContainerResult:
        """Remove an image."""
        start_time = time.time()
        args = ["rmi"]
        if force:
            args.append("-f")
        args.append(image)

        returncode, stdout, stderr = await self._run_command(args)
        duration_ms = (time.time() - start_time) * 1000

        return ContainerResult(
            success=returncode == 0,
            operation="rmi",
            data={"image": image},
            error=stderr if returncode != 0 else None,
            duration_ms=duration_ms,
        )

    async def _stats(
        self,
        container: str | None = None,
        no_stream: bool = True,
        **kwargs,
    ) -> ContainerResult:
        """Get container stats."""
        start_time = time.time()
        args = ["stats", "--format", "json"]

        if no_stream:
            args.append("--no-stream")

        if container:
            args.append(container)

        returncode, stdout, stderr = await self._run_command(args)
        duration_ms = (time.time() - start_time) * 1000

        stats = []
        if stdout.strip():
            for line in stdout.strip().split("\n"):
                try:
                    stats.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

        return ContainerResult(
            success=returncode == 0,
            operation="stats",
            data={"stats": stats},
            error=stderr if returncode != 0 else None,
            duration_ms=duration_ms,
        )

    # Convenience methods
    async def build(self, path: str = ".", tag: str = None, **kwargs) -> CapabilityResult:
        """Build a container image."""
        return await self.execute(action="build", path=path, tag=tag, **kwargs)

    async def run(self, image: str, **kwargs) -> CapabilityResult:
        """Run a container."""
        return await self.execute(action="run", image=image, **kwargs)

    async def stop(self, container: str, **kwargs) -> CapabilityResult:
        """Stop a container."""
        return await self.execute(action="stop", container=container, **kwargs)

    async def logs(self, container: str, **kwargs) -> CapabilityResult:
        """Get container logs."""
        return await self.execute(action="logs", container=container, **kwargs)

    async def ps(self, all: bool = False) -> CapabilityResult:
        """List containers."""
        return await self.execute(action="list", all=all)

    async def pull(self, image: str) -> CapabilityResult:
        """Pull an image."""
        return await self.execute(action="pull", image=image)
