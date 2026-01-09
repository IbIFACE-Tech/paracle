"""SSH transport implementation with tunnel management."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from paracle_transport.base import Transport, TransportError
from paracle_transport.remote_config import RemoteConfig, TunnelConfig

# asyncssh is an optional dependency for SSH transport
try:
    import asyncssh

    ASYNCSSH_AVAILABLE = True
except ImportError:
    asyncssh = None  # type: ignore[assignment]
    ASYNCSSH_AVAILABLE = False

if TYPE_CHECKING:
    import asyncssh

logger = logging.getLogger(__name__)


class SSHTunnelError(TransportError):
    """SSH tunnel creation or management failed."""

    pass


class RemoteConnectionError(TransportError):
    """Connection to remote host failed."""

    pass


class RemoteExecutionError(TransportError):
    """Command execution on remote host failed."""

    pass


class RemoteWorkspaceNotFound(TransportError):
    """Remote .parac/ workspace not found."""

    pass


class SSHTunnel:
    """Individual SSH tunnel management.

    Attributes:
        local_port: Local port number.
        remote_port: Remote port number.
        description: Tunnel description.
        listener: asyncssh tunnel listener.
    """

    def __init__(self, config: TunnelConfig):
        """Initialize SSH tunnel.

        Args:
            config: Tunnel configuration.

        Raises:
            ImportError: If asyncssh is not installed.
        """
        if not ASYNCSSH_AVAILABLE:
            raise ImportError(
                "asyncssh is required for SSH transport. "
                "Install it with: pip install asyncssh"
            )
        self.local_port = config.local
        self.remote_port = config.remote
        self.description = config.description
        self.listener: "asyncssh.SSHTCPListener | None" = None

    async def start(self, connection: "asyncssh.SSHClientConnection") -> None:
        """Start SSH tunnel.

        Args:
            connection: Active SSH connection.

        Raises:
            SSHTunnelError: If tunnel creation fails.
        """
        try:
            logger.info(
                f"Creating SSH tunnel: localhost:{self.local_port} -> "
                f"remote:{self.remote_port} ({self.description})"
            )
            self.listener = await connection.forward_local_port(
                "127.0.0.1",
                self.local_port,
                "127.0.0.1",
                self.remote_port,
            )
            logger.info(
                f"Tunnel active: localhost:{self.local_port} -> "
                f"remote:{self.remote_port}"
            )
        except Exception as e:
            raise SSHTunnelError(
                f"Failed to create tunnel {self.local_port} -> {self.remote_port}: {e}"
            ) from e

    async def stop(self) -> None:
        """Stop SSH tunnel."""
        if self.listener is not None:
            self.listener.close()
            await self.listener.wait_closed()
            logger.info(f"Tunnel stopped: localhost:{self.local_port}")
            self.listener = None

    def is_alive(self) -> bool:
        """Check if tunnel is active.

        Returns:
            bool: True if tunnel is active, False otherwise.
        """
        return self.listener is not None


class SSHTransport(Transport):
    """SSH transport for remote Paracle execution.

    This transport establishes SSH connections to remote hosts,
    creates port forwarding tunnels, and executes commands remotely.

    Example:
        ```python
        config = RemoteConfig(
            name="production",
            host="user@prod-server.com",
            workspace="/opt/paracle",
            tunnels=[TunnelConfig(local=8000, remote=8000)]
        )

        async with SSHTransport(config) as transport:
            result = await transport.execute("paracle agents list")
            print(result["stdout"])
        ```
    """

    def __init__(self, config: RemoteConfig):
        """Initialize SSH transport.

        Args:
            config: Remote configuration.

        Raises:
            ImportError: If asyncssh is not installed.
        """
        if not ASYNCSSH_AVAILABLE:
            raise ImportError(
                "asyncssh is required for SSH transport. "
                "Install it with: pip install asyncssh"
            )
        self.config = config
        self.connection: "asyncssh.SSHClientConnection | None" = None
        self.tunnels: dict[int, SSHTunnel] = {}

    async def connect(self) -> None:
        """Establish SSH connection and create tunnels.

        Raises:
            RemoteConnectionError: If connection fails.
            RemoteWorkspaceNotFound: If workspace doesn't exist.
            SSHTunnelError: If tunnel creation fails.
        """
        try:
            logger.info(f"Connecting to {self.config.host}:{self.config.port}")

            # Build connection options
            options: dict[str, Any] = {
                "host": self.config.hostname,
                "port": self.config.port,
                "username": self.config.username,
                # Disable known_hosts for flexibility, but users should
                # configure ~/.ssh/known_hosts for production use
                "known_hosts": None,
            }

            # Add SSH key if specified
            if self.config.identity_file:
                key_path = Path(self.config.identity_file).expanduser()
                options["client_keys"] = [str(key_path)]

            # Connect
            self.connection = await asyncssh.connect(**options)
            logger.info(f"Connected to {self.config.host}")

            # Verify workspace exists
            await self._verify_workspace()

            # Create tunnels
            await self._create_tunnels()

        except asyncssh.Error as e:
            raise RemoteConnectionError(
                f"Failed to connect to {self.config.host}: {e}"
            ) from e
        except Exception:
            # Clean up on failure
            await self.disconnect()
            raise

    async def disconnect(self) -> None:
        """Close SSH connection and stop all tunnels."""
        # Stop tunnels
        for tunnel in list(self.tunnels.values()):
            try:
                await tunnel.stop()
            except Exception as e:
                logger.warning(f"Error stopping tunnel: {e}")

        self.tunnels.clear()

        # Close connection
        if self.connection is not None:
            self.connection.close()
            await self.connection.wait_closed()
            logger.info(f"Disconnected from {self.config.host}")
            self.connection = None

    async def execute(self, command: str, **kwargs: Any) -> dict[str, Any]:
        """Execute command on remote host.

        Args:
            command: Command to execute (e.g., "paracle agents list").
            **kwargs: Additional arguments (unused).

        Returns:
            dict: Execution result with stdout, stderr, exit_code.

        Raises:
            RemoteConnectionError: If not connected.
            RemoteExecutionError: If command execution fails.
        """
        if not await self.is_connected():
            raise RemoteConnectionError("Not connected to remote host")

        try:
            # Change to workspace directory and execute command
            full_command = f"cd {self.config.workspace} && {command}"
            logger.debug(f"Executing: {full_command}")

            result = await self.connection.run(full_command, check=False)

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_status,
            }

        except Exception as e:
            raise RemoteExecutionError(f"Failed to execute command: {e}") from e

    async def is_connected(self) -> bool:
        """Check if SSH connection is active.

        Returns:
            bool: True if connected, False otherwise.
        """
        if self.connection is None:
            return False

        try:
            # Quick connectivity check - run simple command
            result = await self.connection.run("echo ping", check=False, timeout=5)
            return result.exit_status == 0
        except Exception:
            return False

    async def _verify_workspace(self) -> None:
        """Verify remote workspace exists and contains .parac/.

        Raises:
            RemoteWorkspaceNotFound: If workspace not found.
        """
        result = await self.connection.run(
            f"test -d {self.config.workspace}/.parac && echo exists", check=False
        )

        if result.exit_status != 0 or "exists" not in result.stdout:
            raise RemoteWorkspaceNotFound(
                f"Workspace not found or missing .parac/ at {self.config.workspace}"
            )

        logger.info(f"Verified workspace at {self.config.workspace}")

    async def _create_tunnels(self) -> None:
        """Create all configured SSH tunnels.

        Raises:
            SSHTunnelError: If tunnel creation fails.
        """
        for tunnel_config in self.config.tunnels:
            tunnel = SSHTunnel(tunnel_config)
            await tunnel.start(self.connection)
            self.tunnels[tunnel_config.local] = tunnel

    async def ensure_tunnel_health(self) -> None:
        """Check tunnel health and reconnect if needed.

        This can be called periodically to ensure tunnels stay active.

        Raises:
            SSHTunnelError: If tunnel reconnection fails.
        """
        for local_port, tunnel in list(self.tunnels.items()):
            if not tunnel.is_alive():
                logger.warning(
                    f"Tunnel {local_port} is dead, attempting reconnection..."
                )
                try:
                    await tunnel.stop()
                    await tunnel.start(self.connection)
                except Exception as e:
                    raise SSHTunnelError(
                        f"Failed to reconnect tunnel {local_port}: {e}"
                    ) from e
