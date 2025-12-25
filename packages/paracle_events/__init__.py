"""Paracle Events - Event Bus.

This package provides the event system for Paracle:
- Event definitions (domain events)
- EventBus (publish/subscribe)
- EventStore (persistence for audit trail)

Usage:
    from paracle_events import EventBus, Event, EventType, agent_created

    bus = EventBus()
    bus.subscribe(EventType.AGENT_CREATED, lambda e: print(f"Agent created: {e}"))
    bus.publish(agent_created("agent_123", "code-reviewer"))
"""

from paracle_events.bus import (
    EventBus,
    EventHandler,
    EventStore,
    get_event_bus,
    reset_event_bus,
)
from paracle_events.events import (
    Event,
    EventType,
    agent_completed,
    agent_created,
    agent_failed,
    agent_started,
    tool_completed,
    tool_invoked,
    workflow_completed,
    workflow_failed,
    workflow_started,
)

__version__ = "0.0.1"

__all__ = [
    # Bus
    "EventBus",
    "EventHandler",
    "EventStore",
    "get_event_bus",
    "reset_event_bus",
    # Events
    "Event",
    "EventType",
    # Factory functions
    "agent_created",
    "agent_started",
    "agent_completed",
    "agent_failed",
    "workflow_started",
    "workflow_completed",
    "workflow_failed",
    "tool_invoked",
    "tool_completed",
]
