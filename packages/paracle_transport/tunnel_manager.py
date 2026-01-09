"""Tunnel manager with health monitoring and auto-reconnection."""

import asyncio
import logging
from typing import Any

from paracle_transport.remote_config import RemoteConfig
from paracle_transport.ssh import SSHTransport, SSHTunnelError

logger = logging.getLogger(__name__)


class TunnelManager:
    """Manages SSH tunnels with automatic reconnection.

    The tunnel manager monitors tunnel health and automatically
    reconnects dead tunnels without user intervention.

    Example:
        ```python
        config = RemoteConfig(
            name="production",
            host="user@prod.com",
            workspace="/opt/paracle",
            tunnels=[TunnelConfig(local=8000, remote=8000)]
        )

        manager = TunnelManager(config)
        await manager.start()

        # Tunnels are now monitored and auto-reconnect on failure
        # Use manager.transport to execute commands

        await manager.stop()
        ```
    """

    def __init__(
        self,
        config: RemoteConfig,
        health_check_interval: int = 10,
        auto_reconnect: bool = True,
    ):
        """Initialize tunnel manager.

        Args:
            config: Remote configuration.
            health_check_interval: Seconds between health checks (default: 10).
            auto_reconnect: Enable automatic reconnection (default: True).
        """
        self.config = config
        self.health_check_interval = health_check_interval
        self.auto_reconnect = auto_reconnect
        self.transport = SSHTransport(config)
        self._monitor_task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        """Start tunnel manager and establish connection.

        Raises:
            RemoteConnectionError: If initial connection fails.
        """
        logger.info(f"Starting tunnel manager for {self.config.name}")
        await self.transport.connect()
        self._running = True

        if self.auto_reconnect:
            self._monitor_task = asyncio.create_task(self._monitor_health())
            logger.info(
                f"Health monitoring enabled (interval: {self.health_check_interval}s)"
            )

    async def stop(self) -> None:
        """Stop tunnel manager and close connection."""
        logger.info(f"Stopping tunnel manager for {self.config.name}")
        self._running = False

        # Stop health monitor
        if self._monitor_task is not None:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        # Disconnect transport
        await self.transport.disconnect()

    async def _monitor_health(self) -> None:
        """Monitor tunnel health and auto-reconnect.

        This runs as a background task, checking tunnel health
        at regular intervals and reconnecting if needed.
        """
        logger.info("Tunnel health monitoring started")

        while self._running:
            try:
                await asyncio.sleep(self.health_check_interval)

                # Check connection health
                if not await self.transport.is_connected():
                    logger.warning("Connection lost, attempting full reconnect...")
                    await self._reconnect_transport()
                    continue

                # Check tunnel health
                await self.transport.ensure_tunnel_health()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitor: {e}", exc_info=True)
                # Continue monitoring despite errors

        logger.info("Tunnel health monitoring stopped")

    async def _reconnect_transport(self) -> None:
        """Reconnect SSH transport and tunnels.

        Raises:
            SSHTunnelError: If reconnection fails.
        """
        try:
            # Disconnect first
            await self.transport.disconnect()

            # Wait a bit before reconnecting
            await asyncio.sleep(2)

            # Reconnect
            await self.transport.connect()
            logger.info("Successfully reconnected transport")

        except Exception as e:
            logger.error(f"Failed to reconnect transport: {e}")
            raise SSHTunnelError(f"Transport reconnection failed: {e}") from e

    async def execute(self, command: str, **kwargs: Any) -> dict[str, Any]:
        """Execute command via managed transport.

        This is a convenience method that delegates to the underlying transport.

        Args:
            command: Command to execute.
            **kwargs: Additional arguments.

        Returns:
            dict: Execution result.
        """
        return await self.transport.execute(command, **kwargs)

    async def __aenter__(self):
        """Context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.stop()
