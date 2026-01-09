"""Sandbox manager for orchestrating sandbox lifecycle."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from paracle_core.ids import generate_ulid

from paracle_sandbox.config import SandboxConfig
from paracle_sandbox.docker_sandbox import DockerSandbox
from paracle_sandbox.exceptions import SandboxError

logger = logging.getLogger(__name__)


class SandboxManager:
    """Manages sandbox creation, lifecycle, and cleanup.

    Coordinates multiple sandboxes, enforces limits, and handles
    automatic cleanup.

    Attributes:
        max_concurrent: Maximum concurrent sandboxes
        active_sandboxes: Currently active sandboxes
    """

    def __init__(self, max_concurrent: int = 10):
        """Initialize sandbox manager.

        Args:
            max_concurrent: Maximum concurrent sandboxes
        """
        self.max_concurrent = max_concurrent
        self.active_sandboxes: dict[str, DockerSandbox] = {}
        self._lock = asyncio.Lock()

    async def create(
        self,
        config: SandboxConfig,
        sandbox_id: str | None = None,
    ) -> DockerSandbox:
        """Create a new sandbox.

        Args:
            config: Sandbox configuration
            sandbox_id: Optional sandbox ID (generated if None)

        Returns:
            Created DockerSandbox instance

        Raises:
            SandboxError: If max concurrent limit reached
        """
        async with self._lock:
            # Check concurrent limit
            if len(self.active_sandboxes) >= self.max_concurrent:
                raise SandboxError(
                    f"Maximum concurrent sandboxes reached: {self.max_concurrent}"
                )

            # Generate ID if not provided
            if not sandbox_id:
                sandbox_id = generate_ulid()

            # Create sandbox
            sandbox = DockerSandbox(sandbox_id, config)
            await sandbox.start()

            # Track active sandbox
            self.active_sandboxes[sandbox_id] = sandbox

            logger.info(
                f"Created sandbox {sandbox_id} ({len(self.active_sandboxes)}/{self.max_concurrent})"
            )

            return sandbox

    async def get(self, sandbox_id: str) -> DockerSandbox | None:
        """Get active sandbox by ID.

        Args:
            sandbox_id: Sandbox identifier

        Returns:
            DockerSandbox if found, None otherwise
        """
        return self.active_sandboxes.get(sandbox_id)

    async def destroy(self, sandbox_id: str) -> None:
        """Destroy a sandbox.

        Args:
            sandbox_id: Sandbox identifier
        """
        async with self._lock:
            sandbox = self.active_sandboxes.pop(sandbox_id, None)
            if sandbox:
                await sandbox.stop()
                logger.info(
                    f"Destroyed sandbox {sandbox_id} ({len(self.active_sandboxes)}/{self.max_concurrent})"
                )

    async def destroy_all(self) -> None:
        """Destroy all active sandboxes."""
        async with self._lock:
            sandbox_ids = list(self.active_sandboxes.keys())
            for sandbox_id in sandbox_ids:
                sandbox = self.active_sandboxes.pop(sandbox_id)
                await sandbox.stop()

            logger.info(f"Destroyed all sandboxes ({len(sandbox_ids)} total)")

    async def get_stats(self) -> dict[str, Any]:
        """Get statistics for all active sandboxes.

        Returns:
            Dict with overall stats and per-sandbox stats
        """
        stats = {
            "total_sandboxes": len(self.active_sandboxes),
            "max_concurrent": self.max_concurrent,
            "utilization": len(self.active_sandboxes) / self.max_concurrent,
            "sandboxes": {},
        }

        for sandbox_id, sandbox in self.active_sandboxes.items():
            try:
                sandbox_stats = await sandbox.get_stats()
                stats["sandboxes"][sandbox_id] = sandbox_stats
            except Exception as e:
                logger.error(f"Failed to get stats for {sandbox_id}: {e}")
                stats["sandboxes"][sandbox_id] = {"error": str(e)}

        return stats

    @asynccontextmanager
    async def managed_sandbox(self, config: SandboxConfig):
        """Context manager for automatic sandbox lifecycle.

        Creates sandbox on enter, destroys on exit.

        Args:
            config: Sandbox configuration

        Yields:
            Created DockerSandbox

        Example:
            ```python
            manager = SandboxManager()
            async with manager.managed_sandbox(config) as sandbox:
                result = await sandbox.execute("python script.py")
            ```
        """
        sandbox = await self.create(config)
        try:
            yield sandbox
        finally:
            await self.destroy(sandbox.sandbox_id)
