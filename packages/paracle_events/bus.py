"""Event Bus implementation.

This module provides the Event Bus for publishing and subscribing to events.
The bus enables loose coupling between components through async event handling.

Key features:
- Publish/Subscribe pattern
- Wildcard subscriptions (e.g., "agent.*")
- Event history (for replay/debugging)
- Async handlers support
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable

from paracle_core.logging import get_logger

from paracle_events.events import Event, EventType

logger = get_logger(__name__)

# Handler type: can be sync or async
EventHandler = Callable[[Event], None] | Callable[[Event], Awaitable[None]]


class EventBus:
    """In-memory event bus implementation.

    Supports both sync and async handlers.
    Maintains event history for debugging and replay.
    """

    def __init__(
        self,
        max_history: int = 1000,
    ) -> None:
        """Initialize event bus.

        Args:
            max_history: Maximum number of events to keep in history
        """
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._history: list[Event] = []
        self._max_history = max_history

    def subscribe(
        self,
        event_type: EventType | str,
        handler: EventHandler,
    ) -> Callable[[], None]:
        """Subscribe to an event type.

        Args:
            event_type: Event type to subscribe to (or pattern like "agent.*")
            handler: Handler function to call when event is published

        Returns:
            Unsubscribe function
        """
        key = event_type.value if isinstance(event_type, EventType) else event_type
        self._handlers[key].append(handler)

        def unsubscribe() -> None:
            self._handlers[key].remove(handler)

        return unsubscribe

    def subscribe_all(self, handler: EventHandler) -> Callable[[], None]:
        """Subscribe to all events.

        Args:
            handler: Handler function to call for every event

        Returns:
            Unsubscribe function
        """
        return self.subscribe("*", handler)

    def publish(self, event: Event) -> None:
        """Publish an event synchronously.

        Calls all matching handlers in order.
        For async handlers, creates tasks but doesn't await them.

        Args:
            event: Event to publish
        """
        self._add_to_history(event)
        handlers = self._get_matching_handlers(event.type)

        for handler in handlers:
            try:
                result = handler(event)
                # If handler is async, schedule it
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
            except Exception:
                logger.exception(f"Error in event handler for {event.type}")

    async def publish_async(self, event: Event) -> None:
        """Publish an event asynchronously.

        Awaits all async handlers.

        Args:
            event: Event to publish
        """
        self._add_to_history(event)
        handlers = self._get_matching_handlers(event.type)

        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                logger.exception(f"Error in event handler for {event.type}")

    def _add_to_history(self, event: Event) -> None:
        """Add event to history, respecting max size."""
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

    def _get_matching_handlers(self, event_type: EventType) -> list[EventHandler]:
        """Get all handlers matching the event type."""
        handlers: list[EventHandler] = []
        event_key = event_type.value

        # Exact match
        handlers.extend(self._handlers.get(event_key, []))

        # Wildcard matches (e.g., "agent.*" matches "agent.created")
        parts = event_key.split(".")
        if len(parts) >= 2:
            wildcard = f"{parts[0]}.*"
            handlers.extend(self._handlers.get(wildcard, []))

        # Global wildcard
        handlers.extend(self._handlers.get("*", []))

        return handlers

    def get_history(
        self,
        event_type: EventType | str | None = None,
        limit: int | None = None,
    ) -> list[Event]:
        """Get event history.

        Args:
            event_type: Optional filter by event type
            limit: Maximum number of events to return

        Returns:
            List of events (newest last)
        """
        events = self._history

        if event_type is not None:
            key = event_type.value if isinstance(event_type, EventType) else event_type
            events = [e for e in events if e.type.value == key]

        if limit is not None:
            events = events[-limit:]

        return events

    def get_history_for_source(
        self,
        source: str,
        limit: int | None = None,
    ) -> list[Event]:
        """Get event history for a specific source.

        Args:
            source: Source ID to filter by
            limit: Maximum number of events to return

        Returns:
            List of events (newest last)
        """
        events = [e for e in self._history if e.source == source]

        if limit is not None:
            events = events[-limit:]

        return events

    def clear_history(self) -> int:
        """Clear event history.

        Returns:
            Number of events cleared
        """
        count = len(self._history)
        self._history.clear()
        return count

    def clear_handlers(self) -> None:
        """Clear all handlers."""
        self._handlers.clear()

    @property
    def handler_count(self) -> int:
        """Get total number of registered handlers."""
        return sum(len(handlers) for handlers in self._handlers.values())

    @property
    def history_count(self) -> int:
        """Get number of events in history."""
        return len(self._history)


# Global event bus instance
_default_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get the default event bus instance.

    Returns:
        Default EventBus instance
    """
    global _default_bus
    if _default_bus is None:
        _default_bus = EventBus()
    return _default_bus


def reset_event_bus() -> None:
    """Reset the default event bus (useful for testing)."""
    global _default_bus
    _default_bus = None


class EventStore:
    """Persistent event store interface.

    For v0.0.1, uses in-memory storage.
    Future versions will support SQLite and other backends.
    """

    def __init__(self) -> None:
        """Initialize event store."""
        self._events: list[Event] = []

    def append(self, event: Event) -> None:
        """Append an event to the store."""
        self._events.append(event)

    def get_all(self) -> list[Event]:
        """Get all events."""
        return list(self._events)

    def get_by_type(self, event_type: EventType) -> list[Event]:
        """Get events by type."""
        return [e for e in self._events if e.type == event_type]

    def get_by_source(self, source: str) -> list[Event]:
        """Get events by source."""
        return [e for e in self._events if e.source == source]

    def get_since(self, event_id: str) -> list[Event]:
        """Get events since a specific event ID."""
        found = False
        result: list[Event] = []
        for event in self._events:
            if found:
                result.append(event)
            elif event.id == event_id:
                found = True
        return result

    def count(self) -> int:
        """Get total event count."""
        return len(self._events)

    def clear(self) -> int:
        """Clear all events."""
        count = len(self._events)
        self._events.clear()
        return count

    def to_ndjson(self) -> str:
        """Export events as NDJSON (newline-delimited JSON)."""
        import json

        lines = [json.dumps(e.to_dict()) for e in self._events]
        return "\n".join(lines)

    def replay(self, bus: EventBus) -> int:
        """Replay all events through an event bus.

        Args:
            bus: EventBus to replay events through

        Returns:
            Number of events replayed
        """
        for event in self._events:
            bus.publish(event)
        return len(self._events)
