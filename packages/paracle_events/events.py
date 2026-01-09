"""Event definitions for Paracle.

This module defines the base Event class and domain events.
Events are immutable records of things that happened in the system.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_serializer


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def generate_event_id() -> str:
    """Generate a unique event ID."""
    return f"evt_{uuid4().hex[:12]}"


class EventType(str, Enum):
    """Event type enumeration."""

    # Agent events
    AGENT_CREATED = "agent.created"
    AGENT_UPDATED = "agent.updated"
    AGENT_DELETED = "agent.deleted"
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"

    # Workflow events
    WORKFLOW_CREATED = "workflow.created"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_STEP_STARTED = "workflow.step.started"
    WORKFLOW_STEP_COMPLETED = "workflow.step.completed"
    WORKFLOW_STEP_FAILED = "workflow.step.failed"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"

    # Tool events
    TOOL_REGISTERED = "tool.registered"
    TOOL_INVOKED = "tool.invoked"
    TOOL_COMPLETED = "tool.completed"
    TOOL_FAILED = "tool.failed"

    # System events
    SYSTEM_STARTED = "system.started"
    SYSTEM_STOPPED = "system.stopped"
    SYSTEM_ERROR = "system.error"


class Event(BaseModel):
    """Base event class.

    All events are immutable and contain:
    - Unique ID
    - Event type
    - Timestamp
    - Source (who created the event)
    - Payload (event-specific data)
    - Metadata (optional additional data)
    """

    model_config = ConfigDict(
        frozen=True,  # Immutable
    )

    id: str = Field(default_factory=generate_event_id)
    type: EventType = Field(..., description="Event type")
    timestamp: datetime = Field(default_factory=utc_now)

    @field_serializer("timestamp", when_used="json")
    def serialize_datetime(self, dt: datetime) -> str:
        return dt.isoformat()

    source: str = Field(..., description="Event source (e.g., agent ID)")
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def event_type(self) -> str:
        """Get event type as string (convenience property)."""
        return self.type.value

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        return self.model_dump(mode="json")


# Convenience factory functions for common events


def agent_created(agent_id: str, spec_name: str, **metadata: Any) -> Event:
    """Create an agent.created event."""
    return Event(
        type=EventType.AGENT_CREATED,
        source=agent_id,
        payload={"agent_id": agent_id, "spec_name": spec_name},
        metadata=metadata,
    )


def agent_started(agent_id: str, **metadata: Any) -> Event:
    """Create an agent.started event."""
    return Event(
        type=EventType.AGENT_STARTED,
        source=agent_id,
        payload={"agent_id": agent_id},
        metadata=metadata,
    )


def agent_completed(agent_id: str, result: Any = None, **metadata: Any) -> Event:
    """Create an agent.completed event."""
    return Event(
        type=EventType.AGENT_COMPLETED,
        source=agent_id,
        payload={"agent_id": agent_id, "result": result},
        metadata=metadata,
    )


def agent_failed(agent_id: str, error: str, **metadata: Any) -> Event:
    """Create an agent.failed event."""
    return Event(
        type=EventType.AGENT_FAILED,
        source=agent_id,
        payload={"agent_id": agent_id, "error": error},
        metadata=metadata,
    )


def workflow_started(workflow_id: str, **metadata: Any) -> Event:
    """Create a workflow.started event."""
    return Event(
        type=EventType.WORKFLOW_STARTED,
        source=workflow_id,
        payload={"workflow_id": workflow_id},
        metadata=metadata,
    )


def workflow_completed(
    workflow_id: str, results: dict[str, Any] | None = None, **metadata: Any
) -> Event:
    """Create a workflow.completed event."""
    return Event(
        type=EventType.WORKFLOW_COMPLETED,
        source=workflow_id,
        payload={"workflow_id": workflow_id, "results": results or {}},
        metadata=metadata,
    )


def workflow_failed(workflow_id: str, error: str, **metadata: Any) -> Event:
    """Create a workflow.failed event."""
    return Event(
        type=EventType.WORKFLOW_FAILED,
        source=workflow_id,
        payload={"workflow_id": workflow_id, "error": error},
        metadata=metadata,
    )


def tool_invoked(
    tool_id: str,
    tool_name: str,
    agent_id: str,
    parameters: dict[str, Any] | None = None,
    **metadata: Any,
) -> Event:
    """Create a tool.invoked event."""
    return Event(
        type=EventType.TOOL_INVOKED,
        source=agent_id,
        payload={
            "tool_id": tool_id,
            "tool_name": tool_name,
            "agent_id": agent_id,
            "parameters": parameters or {},
        },
        metadata=metadata,
    )


def tool_completed(
    tool_id: str,
    tool_name: str,
    agent_id: str,
    result: Any = None,
    **metadata: Any,
) -> Event:
    """Create a tool.completed event."""
    return Event(
        type=EventType.TOOL_COMPLETED,
        source=agent_id,
        payload={
            "tool_id": tool_id,
            "tool_name": tool_name,
            "agent_id": agent_id,
            "result": result,
        },
        metadata=metadata,
    )
