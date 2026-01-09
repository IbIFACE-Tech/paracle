"""Base session classes for interactive modes.

This module provides the base classes for session management.
Sessions maintain conversation state and tool context.

Example:
    >>> from paracle_meta.sessions.base import Session, SessionConfig
    >>>
    >>> config = SessionConfig(max_turns=50)
    >>> session = Session(provider, registry, config)
    >>> await session.initialize()
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from paracle_meta.capabilities.provider_protocol import CapabilityProvider
    from paracle_meta.registry import CapabilityRegistry


class SessionStatus(Enum):
    """Session status."""

    CREATED = "created"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class SessionMessage:
    """A message in a session.

    Attributes:
        id: Message ID.
        role: Message role (user, assistant, system, tool).
        content: Message content.
        tool_calls: Tool calls made (for assistant messages).
        tool_results: Tool results (for tool messages).
        timestamp: When the message was created.
        metadata: Additional metadata.
    """

    role: str
    content: str
    id: str = field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    tool_calls: list[dict[str, Any]] | None = None
    tool_results: list[dict[str, Any]] | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionMessage:
        """Create from dictionary."""
        return cls(
            id=data.get("id", f"msg_{uuid.uuid4().hex[:12]}"),
            role=data["role"],
            content=data["content"],
            tool_calls=data.get("tool_calls"),
            tool_results=data.get("tool_results"),
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if "timestamp" in data
                else datetime.now(timezone.utc)
            ),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SessionConfig:
    """Base session configuration.

    Attributes:
        system_prompt: System instructions.
        max_turns: Maximum conversation turns.
        max_tokens: Maximum tokens per response.
        temperature: Sampling temperature.
        enable_tools: Whether to enable tool use.
        persist_memory: Whether to persist to memory capability.
        timeout_seconds: Response timeout.
    """

    system_prompt: str | None = None
    max_turns: int = 100
    max_tokens: int = 4096
    temperature: float = 0.7
    enable_tools: bool = True
    persist_memory: bool = True
    timeout_seconds: float = 120.0


class Session(ABC):
    """Abstract base class for interactive sessions.

    Sessions provide stateful interaction with an LLM, maintaining
    conversation history and tool context.

    Attributes:
        id: Session ID.
        provider: LLM provider.
        registry: Capability registry.
        config: Session configuration.
        messages: Conversation history.
        status: Current session status.
    """

    def __init__(
        self,
        provider: CapabilityProvider,
        registry: CapabilityRegistry,
        config: SessionConfig | None = None,
    ):
        """Initialize session.

        Args:
            provider: LLM provider.
            registry: Capability registry for tools.
            config: Session configuration.
        """
        self.id = f"session_{uuid.uuid4().hex[:12]}"
        self.provider = provider
        self.registry = registry
        self.config = config or SessionConfig()
        self.messages: list[SessionMessage] = []
        self.status = SessionStatus.CREATED
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at
        self._metadata: dict[str, Any] = {}

    @property
    def turn_count(self) -> int:
        """Number of conversation turns (user messages)."""
        return sum(1 for m in self.messages if m.role == "user")

    @property
    def is_active(self) -> bool:
        """Whether session is active."""
        return self.status == SessionStatus.ACTIVE

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the session."""
        ...

    @abstractmethod
    async def send(self, message: str) -> SessionMessage:
        """Send a message and get response.

        Args:
            message: User message.

        Returns:
            Assistant response message.
        """
        ...

    async def add_message(
        self,
        role: str,
        content: str,
        **kwargs: Any,
    ) -> SessionMessage:
        """Add a message to the session.

        Args:
            role: Message role.
            content: Message content.
            **kwargs: Additional message attributes.

        Returns:
            The created message.
        """
        msg = SessionMessage(role=role, content=content, **kwargs)
        self.messages.append(msg)
        self.updated_at = datetime.now(timezone.utc)
        return msg

    def get_history(self, max_messages: int | None = None) -> list[SessionMessage]:
        """Get conversation history.

        Args:
            max_messages: Maximum messages to return.

        Returns:
            List of messages.
        """
        if max_messages:
            return self.messages[-max_messages:]
        return self.messages

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.messages.clear()
        self.updated_at = datetime.now(timezone.utc)

    async def pause(self) -> None:
        """Pause the session."""
        self.status = SessionStatus.PAUSED
        self.updated_at = datetime.now(timezone.utc)

    async def resume(self) -> None:
        """Resume the session."""
        self.status = SessionStatus.ACTIVE
        self.updated_at = datetime.now(timezone.utc)

    async def complete(self) -> None:
        """Mark session as completed."""
        self.status = SessionStatus.COMPLETED
        self.updated_at = datetime.now(timezone.utc)

    async def shutdown(self) -> None:
        """Shutdown the session."""
        if self.status != SessionStatus.COMPLETED:
            await self.complete()

    def to_dict(self) -> dict[str, Any]:
        """Serialize session to dictionary."""
        return {
            "id": self.id,
            "status": self.status.value,
            "config": {
                "system_prompt": self.config.system_prompt,
                "max_turns": self.config.max_turns,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "enable_tools": self.config.enable_tools,
            },
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self._metadata,
        }

    async def __aenter__(self) -> Session:
        """Enter async context."""
        await self.initialize()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context."""
        await self.shutdown()
