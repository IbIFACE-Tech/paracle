"""Resource monitoring for sandboxes."""

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from paracle_sandbox.docker_sandbox import DockerSandbox
from paracle_sandbox.exceptions import ResourceLimitError

logger = logging.getLogger(__name__)


class SandboxMonitor:
    """Monitors sandbox resource usage and enforces limits.

    Periodically checks resource usage and can trigger callbacks
    when limits are approached or exceeded.

    Attributes:
        sandbox: Sandbox to monitor
        interval_seconds: Monitoring interval
        on_warning: Callback for resource warnings
        on_limit_exceeded: Callback for limit violations
    """

    def __init__(
        self,
        sandbox: DockerSandbox,
        interval_seconds: float = 1.0,
        on_warning: Callable[[dict[str, Any]], None] | None = None,
        on_limit_exceeded: Callable[[dict[str, Any]], None] | None = None,
    ):
        """Initialize sandbox monitor.

        Args:
            sandbox: Sandbox to monitor
            interval_seconds: Monitoring check interval
            on_warning: Callback when resource usage is high (>80%)
            on_limit_exceeded: Callback when limit exceeded
        """
        self.sandbox = sandbox
        self.interval_seconds = interval_seconds
        self.on_warning = on_warning
        self.on_limit_exceeded = on_limit_exceeded
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._history: list[dict[str, Any]] = []
        self._max_history = 100

    async def start(self) -> None:
        """Start monitoring."""
        if self._task and not self._task.done():
            logger.warning(f"Monitor already running for {self.sandbox.sandbox_id}")
            return

        self._stop_event.clear()
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Started monitoring {self.sandbox.sandbox_id}")

    async def stop(self) -> None:
        """Stop monitoring."""
        self._stop_event.set()
        if self._task:
            await self._task
            self._task = None
        logger.info(f"Stopped monitoring {self.sandbox.sandbox_id}")

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while not self._stop_event.is_set():
            try:
                # Get current stats
                stats = await self.sandbox.get_stats()
                stats["timestamp"] = datetime.utcnow().isoformat()

                # Add to history
                self._history.append(stats)
                if len(self._history) > self._max_history:
                    self._history.pop(0)

                # Check for warnings (>80%)
                warning_triggered = False
                if stats["memory_percent"] > 80:
                    logger.warning(
                        f"Sandbox {self.sandbox.sandbox_id} memory high: "
                        f"{stats['memory_percent']:.1f}%"
                    )
                    warning_triggered = True

                if stats["cpu_percent"] > self.sandbox.config.cpu_cores * 80:
                    logger.warning(
                        f"Sandbox {self.sandbox.sandbox_id} CPU high: "
                        f"{stats['cpu_percent']:.1f}%"
                    )
                    warning_triggered = True

                if warning_triggered and self.on_warning:
                    try:
                        self.on_warning(stats)
                    except Exception as e:
                        logger.error(f"Warning callback failed: {e}")

                # Check for limit violations
                try:
                    await self.sandbox.check_limits()
                except ResourceLimitError as e:
                    logger.error(
                        f"Resource limit exceeded in {self.sandbox.sandbox_id}: {e}"
                    )
                    if self.on_limit_exceeded:
                        try:
                            self.on_limit_exceeded(stats)
                        except Exception as cb_error:
                            logger.error(f"Limit callback failed: {cb_error}")

            except Exception as e:
                logger.error(f"Monitor error for {self.sandbox.sandbox_id}: {e}")

            # Wait for next interval
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=self.interval_seconds
                )
            except asyncio.TimeoutError:
                continue

    def get_history(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Get resource usage history.

        Args:
            limit: Maximum number of records (all if None)

        Returns:
            List of stats snapshots
        """
        if limit:
            return self._history[-limit:]
        return self._history.copy()

    def get_averages(self) -> dict[str, float]:
        """Calculate average resource usage.

        Returns:
            Dict with average CPU, memory, etc.
        """
        if not self._history:
            return {
                "cpu_percent": 0.0,
                "memory_percent": 0.0,
                "memory_mb": 0.0,
            }

        total_cpu = sum(s["cpu_percent"] for s in self._history)
        total_mem_percent = sum(s["memory_percent"] for s in self._history)
        total_mem_mb = sum(s["memory_mb"] for s in self._history)
        count = len(self._history)

        return {
            "cpu_percent": total_cpu / count,
            "memory_percent": total_mem_percent / count,
            "memory_mb": total_mem_mb / count,
        }

    def get_peaks(self) -> dict[str, float]:
        """Get peak resource usage.

        Returns:
            Dict with peak CPU, memory, etc.
        """
        if not self._history:
            return {
                "cpu_percent": 0.0,
                "memory_percent": 0.0,
                "memory_mb": 0.0,
            }

        return {
            "cpu_percent": max(s["cpu_percent"] for s in self._history),
            "memory_percent": max(s["memory_percent"] for s in self._history),
            "memory_mb": max(s["memory_mb"] for s in self._history),
        }

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
