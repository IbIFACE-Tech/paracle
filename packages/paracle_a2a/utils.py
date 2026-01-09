"""A2A Utilities.

Helper functions for working with a2a-sdk types.
These provide convenience methods that don't exist on the base SDK models.
"""

from datetime import datetime
from typing import Any

from a2a.types import (
    AgentCard,
    Artifact,
    DataPart,
    Message,
    Task,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)
from ulid import ULID

# =============================================================================
# Message Utilities
# =============================================================================


def create_message(
    text: str,
    role: str = "user",
    message_id: str | None = None,
    context_id: str | None = None,
    task_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Message:
    """Create a Message from text.

    Args:
        text: Message text content
        role: Message role (user/agent)
        message_id: Optional message ID (generated if not provided)
        context_id: Optional context ID
        task_id: Optional task ID
        metadata: Optional metadata

    Returns:
        Message object
    """
    return Message(
        message_id=message_id or str(ULID()),
        role=role,
        parts=[TextPart(text=text)],
        context_id=context_id,
        task_id=task_id,
        metadata=metadata,
    )


def get_message_text(message: Message) -> str:
    """Extract text content from a Message.

    Args:
        message: Message to extract text from

    Returns:
        Concatenated text from all TextParts
    """
    texts = []
    for part in message.parts:
        # SDK wraps parts in a Part container with .root
        actual_part = getattr(part, "root", part)
        if isinstance(actual_part, TextPart):
            texts.append(actual_part.text)
    return "\n".join(texts)


def get_message_data(message: Message) -> list[dict[str, Any]]:
    """Extract data content from a Message.

    Args:
        message: Message to extract data from

    Returns:
        List of data dictionaries from DataParts
    """
    data = []
    for part in message.parts:
        # SDK wraps parts in a Part container with .root
        actual_part = getattr(part, "root", part)
        if isinstance(actual_part, DataPart):
            data.append(actual_part.data)
    return data


# =============================================================================
# Artifact Utilities
# =============================================================================


def create_artifact(
    text: str,
    name: str = "output",
    artifact_type: str = "text",
    mime_type: str = "text/plain",
    artifact_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Artifact:
    """Create an Artifact from text.

    Args:
        text: Artifact text content
        name: Artifact name
        artifact_type: Artifact type
        mime_type: MIME type
        artifact_id: Optional artifact ID (generated if not provided)
        metadata: Optional metadata

    Returns:
        Artifact object
    """
    return Artifact(
        artifact_id=artifact_id or str(ULID()),
        name=name,
        parts=[TextPart(text=text)],
        metadata=metadata,
    )


def create_data_artifact(
    data: dict[str, Any],
    name: str = "data",
    artifact_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Artifact:
    """Create an Artifact from structured data.

    Args:
        data: Data dictionary
        name: Artifact name
        artifact_id: Optional artifact ID (generated if not provided)
        metadata: Optional metadata

    Returns:
        Artifact object
    """
    return Artifact(
        artifact_id=artifact_id or str(ULID()),
        name=name,
        parts=[DataPart(data=data)],
        metadata=metadata,
    )


def get_artifact_text(artifact: Artifact) -> str:
    """Extract text content from an Artifact.

    Args:
        artifact: Artifact to extract text from

    Returns:
        Concatenated text from all TextParts
    """
    texts = []
    for part in artifact.parts:
        # SDK wraps parts in a Part container with .root
        actual_part = getattr(part, "root", part)
        if isinstance(actual_part, TextPart):
            texts.append(actual_part.text)
    return "\n".join(texts)


def get_artifact_data(artifact: Artifact) -> list[dict[str, Any]]:
    """Extract data content from an Artifact.

    Args:
        artifact: Artifact to extract data from

    Returns:
        List of data dictionaries from DataParts
    """
    data = []
    for part in artifact.parts:
        # SDK wraps parts in a Part container with .root
        actual_part = getattr(part, "root", part)
        if isinstance(actual_part, DataPart):
            data.append(actual_part.data)
    return data


# =============================================================================
# Task Utilities
# =============================================================================


def create_task(
    task_id: str | None = None,
    context_id: str | None = None,
    status: TaskStatus | None = None,
    metadata: dict[str, Any] | None = None,
    history: list[Message] | None = None,
    artifacts: list[Artifact] | None = None,
) -> Task:
    """Create a Task.

    Args:
        task_id: Optional task ID (generated if not provided)
        context_id: Context ID (generated if not provided)
        status: Task status (defaults to submitted)
        metadata: Optional metadata
        history: Optional message history
        artifacts: Optional artifacts

    Returns:
        Task object
    """
    return Task(
        id=task_id or str(ULID()),
        context_id=context_id or str(ULID()),
        status=status or TaskStatus(state=TaskState.submitted),
        metadata=metadata,
        history=history,
        artifacts=artifacts,
    )


def update_task_status(
    task: Task,
    state: TaskState,
    message: str | None = None,
    timestamp: str | None = None,
) -> Task:
    """Update task status (returns new Task, original is immutable).

    Args:
        task: Task to update
        state: New state
        message: Optional status message
        timestamp: Optional timestamp (defaults to now)

    Returns:
        New Task with updated status
    """
    status_message = None
    if message:
        status_message = create_message(message, role="agent")

    new_status = TaskStatus(
        state=state,
        message=status_message,
        timestamp=timestamp or datetime.utcnow().isoformat(),
    )

    # Create new task with updated status
    return Task(
        id=task.id,
        context_id=task.context_id,
        status=new_status,
        metadata=task.metadata,
        history=task.history,
        artifacts=task.artifacts,
    )


def is_task_terminal(task: Task) -> bool:
    """Check if task is in a terminal state.

    Args:
        task: Task to check

    Returns:
        True if task is completed, failed, canceled, or rejected
    """
    terminal_states = {
        TaskState.completed,
        TaskState.failed,
        TaskState.canceled,
        TaskState.rejected,
    }
    return task.status.state in terminal_states


def add_task_artifact(task: Task, artifact: Artifact) -> Task:
    """Add artifact to task (returns new Task).

    Args:
        task: Task to update
        artifact: Artifact to add

    Returns:
        New Task with artifact added
    """
    artifacts = list(task.artifacts or [])
    artifacts.append(artifact)

    return Task(
        id=task.id,
        context_id=task.context_id,
        status=task.status,
        metadata=task.metadata,
        history=task.history,
        artifacts=artifacts,
    )


def add_task_message(task: Task, message: Message) -> Task:
    """Add message to task history (returns new Task).

    Args:
        task: Task to update
        message: Message to add

    Returns:
        New Task with message added to history
    """
    history = list(task.history or [])
    history.append(message)

    return Task(
        id=task.id,
        context_id=task.context_id,
        status=task.status,
        metadata=task.metadata,
        history=history,
        artifacts=task.artifacts,
    )


# =============================================================================
# AgentCard Utilities
# =============================================================================


def agent_card_to_well_known(card: AgentCard) -> dict[str, Any]:
    """Convert AgentCard to .well-known format.

    Args:
        card: AgentCard to convert

    Returns:
        Dictionary in .well-known/agent.json format
    """
    return card.model_dump(by_alias=True, exclude_none=True)


# =============================================================================
# Event Utilities
# =============================================================================


def event_to_sse(event: TaskStatusUpdateEvent) -> str:
    """Convert event to SSE format.

    Args:
        event: Event to convert

    Returns:
        SSE formatted string
    """
    import json

    data = event.model_dump(by_alias=True, exclude_none=True)
    return f"data: {json.dumps(data)}\n\n"


# =============================================================================
# State Mapping
# =============================================================================

# A2A uses lowercase state names
TASK_STATE_ALIASES = {
    "SUBMITTED": TaskState.submitted,
    "WORKING": TaskState.working,
    "INPUT_REQUIRED": TaskState.input_required,
    "AUTH_REQUIRED": TaskState.auth_required,
    "COMPLETED": TaskState.completed,
    "FAILED": TaskState.failed,
    "CANCELLED": TaskState.canceled,  # Note: SDK uses 'canceled' (US spelling)
    "REJECTED": TaskState.rejected,
    "UNKNOWN": TaskState.unknown,
}


def normalize_task_state(state: str | TaskState) -> TaskState:
    """Normalize task state to SDK TaskState enum.

    Args:
        state: State string or TaskState

    Returns:
        TaskState enum value
    """
    if isinstance(state, TaskState):
        return state

    # Try uppercase alias
    upper = state.upper()
    if upper in TASK_STATE_ALIASES:
        return TASK_STATE_ALIASES[upper]

    # Try direct enum value
    try:
        return TaskState(state.lower())
    except ValueError:
        return TaskState.unknown
