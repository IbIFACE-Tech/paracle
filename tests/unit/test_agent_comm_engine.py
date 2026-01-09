"""Unit tests for paracle_agent_comm engine.

Tests for GroupCollaborationEngine and related components.
"""

from typing import Any

import pytest
from paracle_agent_comm.engine import GroupCollaborationEngine
from paracle_agent_comm.exceptions import (
    CoordinatorRequiredError,
    MaxMessagesExceededError,
    SessionTimeoutError,
)
from paracle_agent_comm.models import (
    AgentGroup,
    CommunicationPattern,
    GroupConfig,
    GroupSessionStatus,
    MessageType,
)


class MockAgent:
    """Mock agent for testing."""

    def __init__(self, agent_id: str, responses: list[dict[str, Any]] | None = None):
        """Initialize mock agent.

        Args:
            agent_id: Agent identifier
            responses: Optional list of responses to return in sequence
        """
        self._id = agent_id
        self._responses = responses or [{"message": f"Response from {agent_id}"}]
        self._response_index = 0
        self.calls: list[dict[str, Any]] = []

    @property
    def id(self) -> str:
        return self._id

    async def respond_to_group(
        self,
        session: Any,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Mock response to group."""
        self.calls.append({"session": session, "context": context})
        response = self._responses[self._response_index % len(self._responses)]
        self._response_index += 1
        return response


class MockAgentRegistry:
    """Mock agent registry for testing."""

    def __init__(self, agents: dict[str, MockAgent] | None = None):
        """Initialize registry with agents."""
        self._agents = agents or {}

    def add(self, agent: MockAgent) -> None:
        """Add an agent to the registry."""
        self._agents[agent.id] = agent

    async def get(self, agent_id: str) -> MockAgent:
        """Get agent by ID."""
        if agent_id not in self._agents:
            raise KeyError(f"Agent not found: {agent_id}")
        return self._agents[agent_id]


class MockEventBus:
    """Mock event bus for testing."""

    def __init__(self):
        """Initialize event bus."""
        self.events: list[dict[str, Any]] = []

    async def publish(self, event: dict[str, Any]) -> None:
        """Publish an event."""
        self.events.append(event)


@pytest.fixture
def mock_agents() -> dict[str, MockAgent]:
    """Create mock agents."""
    return {
        "agent-a": MockAgent("agent-a"),
        "agent-b": MockAgent("agent-b"),
        "agent-c": MockAgent("agent-c"),
    }


@pytest.fixture
def mock_registry(mock_agents: dict[str, MockAgent]) -> MockAgentRegistry:
    """Create mock registry with agents."""
    registry = MockAgentRegistry(mock_agents)
    return registry


@pytest.fixture
def mock_event_bus() -> MockEventBus:
    """Create mock event bus."""
    return MockEventBus()


@pytest.fixture
def simple_group() -> AgentGroup:
    """Create a simple peer-to-peer group."""
    return AgentGroup(
        name="Test Team",
        members=["agent-a", "agent-b", "agent-c"],
        max_rounds=3,
        max_messages=50,
        timeout_seconds=10.0,
    )


@pytest.fixture
def coordinator_group() -> AgentGroup:
    """Create a group with coordinator pattern."""
    return AgentGroup(
        name="Coordinated Team",
        members=["coordinator", "worker-1", "worker-2"],
        coordinator="coordinator",
        communication_pattern=CommunicationPattern.COORDINATOR,
        max_rounds=3,
        max_messages=50,
        timeout_seconds=10.0,
    )


class TestGroupCollaborationEngineInit:
    """Tests for engine initialization."""

    def test_init_with_defaults(
        self,
        simple_group: AgentGroup,
        mock_registry: MockAgentRegistry,
    ):
        """Test engine initializes with default config."""
        engine = GroupCollaborationEngine(
            group=simple_group,
            agent_registry=mock_registry,
        )

        assert engine.group == simple_group
        assert engine.registry == mock_registry
        assert engine.event_bus is None
        assert engine.config is not None

    def test_init_with_event_bus(
        self,
        simple_group: AgentGroup,
        mock_registry: MockAgentRegistry,
        mock_event_bus: MockEventBus,
    ):
        """Test engine initializes with event bus."""
        engine = GroupCollaborationEngine(
            group=simple_group,
            agent_registry=mock_registry,
            event_bus=mock_event_bus,
        )

        assert engine.event_bus == mock_event_bus

    def test_init_with_custom_config(
        self,
        simple_group: AgentGroup,
        mock_registry: MockAgentRegistry,
    ):
        """Test engine initializes with custom config."""
        config = GroupConfig(require_consensus=True, max_retries=5)
        engine = GroupCollaborationEngine(
            group=simple_group,
            agent_registry=mock_registry,
            config=config,
        )

        assert engine.config.require_consensus is True
        assert engine.config.max_retries == 5


class TestGroupCollaborationEngineCollaborate:
    """Tests for the collaborate method."""

    @pytest.mark.asyncio
    async def test_collaborate_creates_session(
        self,
        simple_group: AgentGroup,
        mock_registry: MockAgentRegistry,
    ):
        """Test collaborate creates and returns a session."""
        engine = GroupCollaborationEngine(
            group=simple_group,
            agent_registry=mock_registry,
        )

        # Use termination function to end immediately
        session = await engine.collaborate(
            goal="Test collaboration",
            termination_fn=lambda s: True,  # End after first check
        )

        assert session is not None
        assert session.goal == "Test collaboration"
        assert session.group_id == simple_group.id

    @pytest.mark.asyncio
    async def test_collaborate_with_initial_context(
        self,
        simple_group: AgentGroup,
        mock_registry: MockAgentRegistry,
    ):
        """Test collaborate uses initial context."""
        engine = GroupCollaborationEngine(
            group=simple_group,
            agent_registry=mock_registry,
        )

        initial_context = {"key": "value", "count": 42}
        session = await engine.collaborate(
            goal="Test",
            initial_context=initial_context,
            termination_fn=lambda s: True,
        )

        assert session.shared_context["key"] == "value"
        assert session.shared_context["count"] == 42

    @pytest.mark.asyncio
    async def test_collaborate_emits_events(
        self,
        simple_group: AgentGroup,
        mock_registry: MockAgentRegistry,
        mock_event_bus: MockEventBus,
    ):
        """Test collaborate emits start and end events."""
        engine = GroupCollaborationEngine(
            group=simple_group,
            agent_registry=mock_registry,
            event_bus=mock_event_bus,
        )

        await engine.collaborate(
            goal="Test",
            termination_fn=lambda s: True,
        )

        # Check events were emitted
        event_types = [e["type"] for e in mock_event_bus.events]
        assert "group.session.started" in event_types
        assert "group.session.ended" in event_types

    @pytest.mark.asyncio
    async def test_collaborate_broadcasts_goal(
        self,
        simple_group: AgentGroup,
        mock_registry: MockAgentRegistry,
    ):
        """Test collaborate broadcasts goal message."""
        engine = GroupCollaborationEngine(
            group=simple_group,
            agent_registry=mock_registry,
        )

        session = await engine.collaborate(
            goal="Design a new feature",
            termination_fn=lambda s: True,
        )

        # First message should be the goal broadcast
        assert len(session.messages) >= 1
        first_msg = session.messages[0]
        assert first_msg.sender == "system"
        assert "Design a new feature" in first_msg.get_text_content()

    @pytest.mark.asyncio
    async def test_collaborate_runs_all_agents(
        self,
        mock_agents: dict[str, MockAgent],
        mock_registry: MockAgentRegistry,
    ):
        """Test all agents get a turn in each round."""
        group = AgentGroup(
            name="Test",
            members=["agent-a", "agent-b", "agent-c"],
            max_rounds=1,
        )

        engine = GroupCollaborationEngine(
            group=group,
            agent_registry=mock_registry,
        )

        await engine.collaborate(goal="Test")

        # Each agent should have been called at least once
        for agent_id, agent in mock_agents.items():
            assert len(agent.calls) >= 1, f"Agent {agent_id} was not called"

    @pytest.mark.asyncio
    async def test_collaborate_respects_max_rounds(
        self,
        mock_registry: MockAgentRegistry,
    ):
        """Test collaborate stops at max rounds."""
        group = AgentGroup(
            name="Test",
            members=["agent-a", "agent-b"],
            max_rounds=2,
        )

        engine = GroupCollaborationEngine(
            group=group,
            agent_registry=mock_registry,
        )

        session = await engine.collaborate(goal="Test")

        assert session.round_count <= 2
        assert session.status == GroupSessionStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_collaborate_uses_termination_function(
        self,
        simple_group: AgentGroup,
        mock_registry: MockAgentRegistry,
    ):
        """Test custom termination function stops collaboration."""
        engine = GroupCollaborationEngine(
            group=simple_group,
            agent_registry=mock_registry,
        )

        call_count = [0]

        def termination_fn(session):
            call_count[0] += 1
            return call_count[0] >= 2

        session = await engine.collaborate(
            goal="Test",
            termination_fn=termination_fn,
        )

        assert session.outcome == "Termination condition met"


class TestGroupCollaborationEngineCoordinator:
    """Tests for coordinator pattern."""

    @pytest.mark.asyncio
    async def test_coordinator_pattern_requires_coordinator(
        self,
        mock_registry: MockAgentRegistry,
    ):
        """Test coordinator pattern fails without coordinator."""
        group = AgentGroup(
            name="Test",
            members=["agent-a", "agent-b"],
            communication_pattern=CommunicationPattern.COORDINATOR,
            # No coordinator specified
        )

        engine = GroupCollaborationEngine(
            group=group,
            agent_registry=mock_registry,
        )

        with pytest.raises(CoordinatorRequiredError):
            await engine.collaborate(goal="Test")

    @pytest.mark.asyncio
    async def test_coordinator_delegates_to_agents(
        self,
        mock_event_bus: MockEventBus,
    ):
        """Test coordinator can delegate to other agents."""
        coordinator = MockAgent(
            "coordinator",
            responses=[
                {"message": "Let agent-a handle this", "delegate_to": "agent-a"},
            ],
        )
        worker = MockAgent("agent-a")

        registry = MockAgentRegistry({"coordinator": coordinator, "agent-a": worker})

        group = AgentGroup(
            name="Test",
            members=["coordinator", "agent-a"],
            coordinator="coordinator",
            communication_pattern=CommunicationPattern.COORDINATOR,
            max_rounds=1,
        )

        engine = GroupCollaborationEngine(
            group=group,
            agent_registry=registry,
            event_bus=mock_event_bus,
        )

        await engine.collaborate(goal="Test")

        # Worker should have been called after delegation
        assert len(worker.calls) >= 1


class TestGroupCollaborationEngineErrors:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_agent_not_in_group_error(
        self,
        mock_registry: MockAgentRegistry,
    ):
        """Test error when agent is not in group."""
        group = AgentGroup(
            name="Test",
            members=["agent-a"],  # Only agent-a
            max_rounds=1,
        )

        engine = GroupCollaborationEngine(
            group=group,
            agent_registry=mock_registry,
        )

        # This should work since agent-a is in the group
        session = await engine.collaborate(goal="Test")
        assert session is not None

    @pytest.mark.asyncio
    async def test_max_messages_exceeded(
        self,
        mock_registry: MockAgentRegistry,
    ):
        """Test error when max messages exceeded."""
        group = AgentGroup(
            name="Test",
            members=["agent-a", "agent-b"],
            max_rounds=100,  # High rounds
            max_messages=3,  # Very low message limit
        )

        engine = GroupCollaborationEngine(
            group=group,
            agent_registry=mock_registry,
        )

        with pytest.raises(MaxMessagesExceededError):
            await engine.collaborate(goal="Test")

    @pytest.mark.asyncio
    async def test_session_timeout(
        self,
        mock_registry: MockAgentRegistry,
    ):
        """Test error when session times out."""

        # Create agent that takes time
        async def slow_response(session, context):
            import asyncio

            await asyncio.sleep(0.5)
            return {"message": "Slow response"}

        slow_agent = MockAgent("agent-a")
        slow_agent.respond_to_group = slow_response
        registry = MockAgentRegistry({"agent-a": slow_agent})

        group = AgentGroup(
            name="Test",
            members=["agent-a"],
            max_rounds=10,
            timeout_seconds=0.1,  # Very short timeout
        )

        engine = GroupCollaborationEngine(
            group=group,
            agent_registry=registry,
        )

        with pytest.raises(SessionTimeoutError):
            await engine.collaborate(goal="Test")


class TestGroupCollaborationEngineHumanInjection:
    """Tests for human message injection."""

    @pytest.mark.asyncio
    async def test_inject_human_message(
        self,
        simple_group: AgentGroup,
        mock_registry: MockAgentRegistry,
    ):
        """Test injecting a human message."""
        engine = GroupCollaborationEngine(
            group=simple_group,
            agent_registry=mock_registry,
        )

        # Create a session first
        session = await engine.collaborate(
            goal="Test",
            termination_fn=lambda s: True,
        )

        # Inject human message
        message = await engine.inject_human_message(
            session,
            text="Human feedback",
            message_type=MessageType.INFORM,
        )

        assert message.sender == "human"
        assert "Human feedback" in message.get_text_content()

    @pytest.mark.asyncio
    async def test_inject_human_message_disabled(
        self,
        simple_group: AgentGroup,
        mock_registry: MockAgentRegistry,
    ):
        """Test human injection when disabled."""
        config = GroupConfig(allow_human_injection=False)
        engine = GroupCollaborationEngine(
            group=simple_group,
            agent_registry=mock_registry,
            config=config,
        )

        session = await engine.collaborate(
            goal="Test",
            termination_fn=lambda s: True,
        )

        with pytest.raises(ValueError, match="not allowed"):
            await engine.inject_human_message(session, text="Blocked")


class TestAgentContext:
    """Tests for agent context building."""

    @pytest.mark.asyncio
    async def test_agent_receives_context(
        self,
        mock_agents: dict[str, MockAgent],
        mock_registry: MockAgentRegistry,
    ):
        """Test agents receive proper context."""
        group = AgentGroup(
            name="Test",
            members=["agent-a", "agent-b"],
            max_rounds=1,
        )

        engine = GroupCollaborationEngine(
            group=group,
            agent_registry=mock_registry,
        )

        await engine.collaborate(goal="Test goal")

        # Check context was passed to agent
        agent_a = mock_agents["agent-a"]
        assert len(agent_a.calls) >= 1
        context = agent_a.calls[0]["context"]

        assert context["goal"] == "Test goal"
        assert "shared_context" in context
        assert "recent_messages" in context
        assert "round" in context
        assert "group_members" in context

    @pytest.mark.asyncio
    async def test_coordinator_receives_special_context(self):
        """Test coordinator receives is_coordinator flag."""
        coordinator = MockAgent("coordinator")
        registry = MockAgentRegistry({"coordinator": coordinator})

        group = AgentGroup(
            name="Test",
            members=["coordinator"],
            coordinator="coordinator",
            communication_pattern=CommunicationPattern.COORDINATOR,
            max_rounds=1,
        )

        engine = GroupCollaborationEngine(
            group=group,
            agent_registry=registry,
        )

        await engine.collaborate(goal="Test")

        # Check coordinator context
        context = coordinator.calls[0]["context"]
        assert context["is_coordinator"] is True
        assert "available_agents" in context
