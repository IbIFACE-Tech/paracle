"""Paracle A2A Protocol Integration.

This package implements the A2A (Agent-to-Agent) protocol for Paracle,
enabling inter-agent communication with external A2A-compatible agents.

A2A is an open standard by Google/Linux Foundation for AI agent interoperability.
https://a2a-protocol.org/

Features:
- Server Mode: Expose Paracle agents as A2A-compatible endpoints
- Client Mode: Call external A2A agents from Paracle workflows
- Agent Cards: Discovery mechanism for agent capabilities
- Task Lifecycle: Full support for A2A task states
- SSE Streaming: Real-time updates for long-running tasks
"""

from paracle_a2a.config import A2AClientConfig, A2AServerConfig
from paracle_a2a.exceptions import (
    A2AError,
    AgentNotFoundError,
    ContentTypeNotSupportedError,
    InvalidRequestError,
    TaskCancelledError,
    TaskNotFoundError,
)
from paracle_a2a.models import (
    AgentCapabilities,
    AgentCard,
    AgentProvider,
    AgentSkill,
    Artifact,
    DataPart,
    FilePart,
    Message,
    Part,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)
from paracle_a2a.registry import (
    RemoteAgentConfig,
    RemoteAgentRegistry,
    get_remote_registry,
)

__all__ = [
    # Models
    "AgentCard",
    "AgentCapabilities",
    "AgentProvider",
    "AgentSkill",
    "Artifact",
    "DataPart",
    "FilePart",
    "Message",
    "Part",
    "Task",
    "TaskArtifactUpdateEvent",
    "TaskState",
    "TaskStatus",
    "TaskStatusUpdateEvent",
    "TextPart",
    # Config
    "A2AClientConfig",
    "A2AServerConfig",
    # Exceptions
    "A2AError",
    "AgentNotFoundError",
    "ContentTypeNotSupportedError",
    "InvalidRequestError",
    "TaskCancelledError",
    "TaskNotFoundError",
    # Registry
    "RemoteAgentConfig",
    "RemoteAgentRegistry",
    "get_remote_registry",
]
