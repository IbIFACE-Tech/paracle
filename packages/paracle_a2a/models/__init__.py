"""A2A Protocol Models.

Re-exports from official a2a-sdk types.
https://a2a-protocol.org/latest/
"""

# Import all types from official a2a-sdk
from a2a.types import (  # Agent Card; Messages & Parts; Tasks; Events
    AgentCapabilities,
    AgentCard,
    AgentProvider,
    AgentSkill,
    Artifact,
    DataPart,
    FilePart,
    FileWithBytes,
    FileWithUri,
    Message,
    MessageSendParams,  # SDK name for task send params
    Part,
    PushNotificationConfig,
    Task,
    TaskArtifactUpdateEvent,
    TaskIdParams,
    TaskPushNotificationConfig,
    TaskQueryParams,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)
from pydantic import BaseModel, Field

# Alias for backward compatibility
TaskSendParams = MessageSendParams

# Import utilities for working with SDK types
from paracle_a2a.utils import (  # noqa: E402
    add_task_artifact,
    add_task_message,
    agent_card_to_well_known,
    create_artifact,
    create_data_artifact,
    create_message,
    create_task,
    event_to_sse,
    get_artifact_data,
    get_artifact_text,
    get_message_data,
    get_message_text,
    is_task_terminal,
    normalize_task_state,
    update_task_status,
)

# Alias for backward compatibility
A2AEvent = TaskStatusUpdateEvent  # Base event type


class SecurityScheme(BaseModel):
    """Security scheme for A2A authentication (Paracle extension)."""

    scheme: str = Field(..., description="Security scheme name")
    type: str = Field(..., description="Security type: apiKey, http, oauth2")
    api_key_name: str | None = Field(default=None, description="API key header name")
    api_key_location: str | None = Field(default=None, description="API key location")
    bearer_format: str | None = Field(default=None, description="Bearer token format")


__all__ = [
    # Agent Card
    "AgentCapabilities",
    "AgentCard",
    "AgentProvider",
    "AgentSkill",
    "SecurityScheme",
    # Events
    "A2AEvent",
    "TaskArtifactUpdateEvent",
    "TaskStatusUpdateEvent",
    # Messages & Parts
    "Artifact",
    "DataPart",
    "FilePart",
    "FileWithBytes",
    "FileWithUri",
    "Message",
    "Part",
    "TextPart",
    # Tasks
    "PushNotificationConfig",
    "Task",
    "TaskIdParams",
    "TaskPushNotificationConfig",
    "TaskQueryParams",
    "TaskSendParams",
    "TaskState",
    "TaskStatus",
    # Utilities
    "create_message",
    "get_message_text",
    "get_message_data",
    "create_artifact",
    "create_data_artifact",
    "get_artifact_text",
    "get_artifact_data",
    "create_task",
    "update_task_status",
    "is_task_terminal",
    "add_task_artifact",
    "add_task_message",
    "agent_card_to_well_known",
    "event_to_sse",
    "normalize_task_state",
]
