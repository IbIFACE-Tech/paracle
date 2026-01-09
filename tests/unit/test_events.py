"""Tests for event system."""

import asyncio

import pytest
from paracle_events import (
    Event,
    EventBus,
    EventStore,
    EventType,
    agent_completed,
    agent_created,
    agent_failed,
    agent_started,
    get_event_bus,
    reset_event_bus,
    tool_completed,
    tool_invoked,
    workflow_completed,
    workflow_failed,
    workflow_started,
)


class TestEvent:
    """Tests for Event model."""

    def test_create_event(self) -> None:
        """Test creating an event."""
        event = Event(
            type=EventType.AGENT_CREATED,
            source="agent_123",
            payload={"agent_id": "agent_123"},
        )

        assert event.id.startswith("evt_")
        assert event.type == EventType.AGENT_CREATED
        assert event.source == "agent_123"
        assert event.timestamp is not None

    def test_event_immutable(self) -> None:
        """Test events are immutable."""
        event = Event(
            type=EventType.AGENT_CREATED,
            source="agent_123",
        )

        with pytest.raises(Exception):  # Pydantic ValidationError
            event.source = "different"

    def test_to_dict(self) -> None:
        """Test converting event to dict."""
        event = Event(
            type=EventType.AGENT_CREATED,
            source="agent_123",
            payload={"key": "value"},
        )

        d = event.to_dict()

        assert d["type"] == "agent.created"
        assert d["source"] == "agent_123"
        assert d["payload"]["key"] == "value"


class TestEventFactories:
    """Tests for event factory functions."""

    def test_agent_created(self) -> None:
        """Test agent_created factory."""
        event = agent_created("agent_123", "test-agent", team="engineering")

        assert event.type == EventType.AGENT_CREATED
        assert event.source == "agent_123"
        assert event.payload["spec_name"] == "test-agent"
        assert event.metadata["team"] == "engineering"

    def test_agent_started(self) -> None:
        """Test agent_started factory."""
        event = agent_started("agent_123")

        assert event.type == EventType.AGENT_STARTED
        assert event.payload["agent_id"] == "agent_123"

    def test_agent_completed(self) -> None:
        """Test agent_completed factory."""
        event = agent_completed("agent_123", result={"output": "success"})

        assert event.type == EventType.AGENT_COMPLETED
        assert event.payload["result"]["output"] == "success"

    def test_agent_failed(self) -> None:
        """Test agent_failed factory."""
        event = agent_failed("agent_123", "Something went wrong")

        assert event.type == EventType.AGENT_FAILED
        assert event.payload["error"] == "Something went wrong"

    def test_workflow_started(self) -> None:
        """Test workflow_started factory."""
        event = workflow_started("wf_123")

        assert event.type == EventType.WORKFLOW_STARTED
        assert event.payload["workflow_id"] == "wf_123"

    def test_workflow_completed(self) -> None:
        """Test workflow_completed factory."""
        event = workflow_completed("wf_123", results={"status": "ok"})

        assert event.type == EventType.WORKFLOW_COMPLETED
        assert event.payload["results"]["status"] == "ok"

    def test_workflow_failed(self) -> None:
        """Test workflow_failed factory."""
        event = workflow_failed("wf_123", "Timeout")

        assert event.type == EventType.WORKFLOW_FAILED
        assert event.payload["error"] == "Timeout"

    def test_tool_invoked(self) -> None:
        """Test tool_invoked factory."""
        event = tool_invoked(
            "tool_123",
            "read_file",
            "agent_123",
            parameters={"path": "/tmp/file.txt"},
        )

        assert event.type == EventType.TOOL_INVOKED
        assert event.payload["tool_name"] == "read_file"
        assert event.payload["agent_id"] == "agent_123"

    def test_tool_completed(self) -> None:
        """Test tool_completed factory."""
        event = tool_completed(
            "tool_123",
            "read_file",
            "agent_123",
            result="file contents",
        )

        assert event.type == EventType.TOOL_COMPLETED
        assert event.payload["result"] == "file contents"


class TestEventBus:
    """Tests for EventBus."""

    def test_subscribe_and_publish(self) -> None:
        """Test subscribing and publishing events."""
        bus = EventBus()
        received = []

        bus.subscribe(EventType.AGENT_CREATED, lambda e: received.append(e))
        bus.publish(agent_created("agent_123", "test"))

        assert len(received) == 1
        assert received[0].type == EventType.AGENT_CREATED

    def test_unsubscribe(self) -> None:
        """Test unsubscribing from events."""
        bus = EventBus()
        received = []

        unsub = bus.subscribe(EventType.AGENT_CREATED, lambda e: received.append(e))
        bus.publish(agent_created("agent_1", "test"))
        unsub()
        bus.publish(agent_created("agent_2", "test"))

        assert len(received) == 1

    def test_wildcard_subscription(self) -> None:
        """Test wildcard subscription (agent.*)."""
        bus = EventBus()
        received = []

        bus.subscribe("agent.*", lambda e: received.append(e))

        bus.publish(agent_created("a1", "test"))
        bus.publish(agent_started("a1"))
        bus.publish(agent_completed("a1"))
        bus.publish(workflow_started("wf1"))  # Should not match

        assert len(received) == 3

    def test_subscribe_all(self) -> None:
        """Test subscribing to all events."""
        bus = EventBus()
        received = []

        bus.subscribe_all(lambda e: received.append(e))

        bus.publish(agent_created("a1", "test"))
        bus.publish(workflow_started("wf1"))
        bus.publish(tool_invoked("t1", "read", "a1"))

        assert len(received) == 3

    def test_multiple_handlers(self) -> None:
        """Test multiple handlers for same event."""
        bus = EventBus()
        results = {"h1": 0, "h2": 0}

        bus.subscribe(
            EventType.AGENT_CREATED, lambda e: results.update(h1=results["h1"] + 1)
        )
        bus.subscribe(
            EventType.AGENT_CREATED, lambda e: results.update(h2=results["h2"] + 1)
        )

        bus.publish(agent_created("a1", "test"))

        assert results["h1"] == 1
        assert results["h2"] == 1

    def test_history(self) -> None:
        """Test event history."""
        bus = EventBus()

        bus.publish(agent_created("a1", "test"))
        bus.publish(agent_started("a1"))
        bus.publish(workflow_started("wf1"))

        history = bus.get_history()
        assert len(history) == 3

        agent_history = bus.get_history(EventType.AGENT_CREATED)
        assert len(agent_history) == 1

        limited = bus.get_history(limit=2)
        assert len(limited) == 2

    def test_history_for_source(self) -> None:
        """Test getting history for a specific source."""
        bus = EventBus()

        bus.publish(agent_created("a1", "test"))
        bus.publish(agent_started("a1"))
        bus.publish(agent_created("a2", "test"))
        bus.publish(agent_started("a2"))

        a1_history = bus.get_history_for_source("a1")
        assert len(a1_history) == 2

    def test_max_history(self) -> None:
        """Test history respects max size."""
        bus = EventBus(max_history=5)

        for i in range(10):
            bus.publish(agent_created(f"a{i}", "test"))

        assert len(bus.get_history()) == 5

    def test_clear_history(self) -> None:
        """Test clearing history."""
        bus = EventBus()

        bus.publish(agent_created("a1", "test"))
        bus.publish(agent_created("a2", "test"))

        cleared = bus.clear_history()
        assert cleared == 2
        assert len(bus.get_history()) == 0

    def test_handler_error_doesnt_stop_others(self) -> None:
        """Test handler error doesn't prevent other handlers."""
        bus = EventBus()
        results = []

        def bad_handler(e: Event) -> None:
            raise ValueError("Oops")

        def good_handler(e: Event) -> None:
            results.append(e)

        bus.subscribe(EventType.AGENT_CREATED, bad_handler)
        bus.subscribe(EventType.AGENT_CREATED, good_handler)

        bus.publish(agent_created("a1", "test"))

        # Good handler should still be called
        assert len(results) == 1

    def test_handler_count(self) -> None:
        """Test handler count property."""
        bus = EventBus()

        assert bus.handler_count == 0

        bus.subscribe(EventType.AGENT_CREATED, lambda e: None)
        bus.subscribe(EventType.AGENT_STARTED, lambda e: None)
        bus.subscribe("*", lambda e: None)

        assert bus.handler_count == 3


class TestEventBusAsync:
    """Tests for async EventBus functionality."""

    @pytest.mark.asyncio
    async def test_async_handler(self) -> None:
        """Test async handlers work."""
        bus = EventBus()
        results = []

        async def async_handler(e: Event) -> None:
            await asyncio.sleep(0.01)
            results.append(e)

        bus.subscribe(EventType.AGENT_CREATED, async_handler)
        await bus.publish_async(agent_created("a1", "test"))

        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_mixed_handlers(self) -> None:
        """Test mix of sync and async handlers."""
        bus = EventBus()
        results = []

        def sync_handler(e: Event) -> None:
            results.append(("sync", e))

        async def async_handler(e: Event) -> None:
            await asyncio.sleep(0.01)
            results.append(("async", e))

        bus.subscribe(EventType.AGENT_CREATED, sync_handler)
        bus.subscribe(EventType.AGENT_CREATED, async_handler)

        await bus.publish_async(agent_created("a1", "test"))

        assert len(results) == 2


class TestEventStore:
    """Tests for EventStore."""

    def test_append_and_get_all(self) -> None:
        """Test appending and getting events."""
        store = EventStore()

        store.append(agent_created("a1", "test"))
        store.append(agent_started("a1"))

        events = store.get_all()
        assert len(events) == 2

    def test_get_by_type(self) -> None:
        """Test getting events by type."""
        store = EventStore()

        store.append(agent_created("a1", "test"))
        store.append(agent_started("a1"))
        store.append(agent_created("a2", "test"))

        created = store.get_by_type(EventType.AGENT_CREATED)
        assert len(created) == 2

    def test_get_by_source(self) -> None:
        """Test getting events by source."""
        store = EventStore()

        store.append(agent_created("a1", "test"))
        store.append(agent_started("a1"))
        store.append(agent_created("a2", "test"))

        a1_events = store.get_by_source("a1")
        assert len(a1_events) == 2

    def test_get_since(self) -> None:
        """Test getting events since a specific event."""
        store = EventStore()

        e1 = agent_created("a1", "test")
        e2 = agent_started("a1")
        e3 = agent_completed("a1")

        store.append(e1)
        store.append(e2)
        store.append(e3)

        since = store.get_since(e1.id)
        assert len(since) == 2
        assert since[0].id == e2.id

    def test_to_ndjson(self) -> None:
        """Test exporting to NDJSON."""
        store = EventStore()

        store.append(agent_created("a1", "test"))
        store.append(agent_started("a1"))

        ndjson = store.to_ndjson()
        lines = ndjson.strip().split("\n")

        assert len(lines) == 2
        assert "agent.created" in lines[0]
        assert "agent.started" in lines[1]

    def test_replay(self) -> None:
        """Test replaying events through a bus."""
        store = EventStore()
        bus = EventBus()
        received = []

        bus.subscribe_all(lambda e: received.append(e))

        store.append(agent_created("a1", "test"))
        store.append(agent_started("a1"))

        count = store.replay(bus)

        assert count == 2
        assert len(received) == 2


class TestGlobalEventBus:
    """Tests for global event bus functions."""

    def test_get_event_bus(self) -> None:
        """Test getting global event bus."""
        reset_event_bus()

        bus1 = get_event_bus()
        bus2 = get_event_bus()

        assert bus1 is bus2

    def test_reset_event_bus(self) -> None:
        """Test resetting global event bus."""
        reset_event_bus()

        bus1 = get_event_bus()
        bus1.publish(agent_created("a1", "test"))

        reset_event_bus()

        bus2 = get_event_bus()
        assert bus1 is not bus2
        assert bus2.history_count == 0
