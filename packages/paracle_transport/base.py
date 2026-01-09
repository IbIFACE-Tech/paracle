"""Base transport interface for remote execution."""

from abc import ABC, abstractmethod
from typing import Any


class TransportError(Exception):
    """Base exception for transport-related errors."""

    pass


class Transport(ABC):
    """Abstract base class for transport mechanisms.

    Transport implementations handle communication with remote Paracle instances,
    including command execution, file transfer, and connection management.
    """

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to remote host.

        Raises:
            TransportError: If connection fails.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to remote host."""
        pass

    @abstractmethod
    async def execute(self, command: str, **kwargs: Any) -> dict[str, Any]:
        """Execute command on remote host.

        Args:
            command: Command to execute (e.g., "paracle agents list").
            **kwargs: Additional transport-specific arguments.

        Returns:
            dict: Execution result with keys:
                - stdout: Command output
                - stderr: Error output
                - exit_code: Command exit code

        Raises:
            TransportError: If execution fails.
        """
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if transport is currently connected.

        Returns:
            bool: True if connected, False otherwise.
        """
        pass

    async def __aenter__(self):
        """Context manager entry - establish connection."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connection."""
        await self.disconnect()
