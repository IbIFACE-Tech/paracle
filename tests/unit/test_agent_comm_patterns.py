"""Unit tests for paracle_agent_comm patterns.

Tests for PeerToPeerPattern, BroadcastPattern, and CoordinatorPattern.
"""

import pytest

from paracle_agent_comm.models import (
    AgentGroup,
    CommunicationPattern,
    GroupMessage,
    GroupSession,
    MessageType,
)
from paracle_agent_comm.patterns.broadcast import BroadcastPattern
from paracle_agent_comm.patterns.coordinator import CoordinatorPattern
from paracle_agent_comm.patterns.peer_to_peer import PeerToPeerPattern


@pytest.fixture
def simple_group() -> AgentGroup:
    """Create a simple group with three members."""
    return AgentGroup(
        name="Test Team",
        members=["agent-a", "agent-b", "agent-c"],
    )


@pytest.fixture
def coordinator_group() -> AgentGroup:
    """Create a group with coordinator."""
    return AgentGroup(
        name="Coordinated Team",
        members=["coordinator", "worker-1", "worker-2"],
        coordinator="coordinator",
        communication_pattern=CommunicationPattern.COORDINATOR,
    )


@pytest.fixture
def session(simple_group: AgentGroup) -> GroupSession:
    """Create a session for testing."""
    return GroupSession(
        group_id=simple_group.id,
        goal="Test session",
    )


class TestPeerToPeerPattern:
    """Tests for peer-to-peer communication pattern."""

    def test_init(self, simple_group: AgentGroup):
        """Test pattern initialization."""
        pattern = PeerToPeerPattern(simple_group)
        assert pattern.group == simple_group

    def test_can_send_to_member(self, simple_group: AgentGroup):
        """Test member can send to another member."""
        pattern = PeerToPeerPattern(simple_group)

        assert pattern.can_send_to("agent-a", "agent-b") is True
        assert pattern.can_send_to("agent-b", "agent-c") is True
        assert pattern.can_send_to("agent-c", "agent-a") is True

    def test_cannot_send_to_nonmember(self, simple_group: AgentGroup):
        """Test cannot send to non-member."""
        pattern = PeerToPeerPattern(simple_group)

        assert pattern.can_send_to("agent-a", "outsider") is False
        assert pattern.can_send_to("outsider", "agent-a") is False

    def test_route_targeted_message(self, simple_group: AgentGroup):
        """Test routing targeted message."""
        pattern = PeerToPeerPattern(simple_group)

        message = GroupMessage.create(
            group_id=simple_group.id,
            sender="agent-a",
            text="Hello B",
            message_type=MessageType.INFORM,
            recipients=["agent-b"],
        )

        recipients = pattern.route_message(message)
        assert recipients == ["agent-b"]

    def test_route_broadcast_message(self, simple_group: AgentGroup):
        """Test routing broadcast message."""
        pattern = PeerToPeerPattern(simple_group)

        message = GroupMessage.create(
            group_id=simple_group.id,
            sender="agent-a",
            text="Hello everyone",
            message_type=MessageType.INFORM,
            recipients=None,  # Broadcast
        )

        recipients = pattern.route_message(message)
        assert set(recipients) == {"agent-b", "agent-c"}
        assert "agent-a" not in recipients  # Sender excluded

    def test_route_excludes_invalid_recipients(self, simple_group: AgentGroup):
        """Test that invalid recipients are filtered out."""
        pattern = PeerToPeerPattern(simple_group)

        message = GroupMessage.create(
            group_id=simple_group.id,
            sender="agent-a",
            text="Hello",
            message_type=MessageType.INFORM,
            recipients=["agent-b", "outsider", "agent-c"],
        )

        recipients = pattern.route_message(message)
        assert set(recipients) == {"agent-b", "agent-c"}
        assert "outsider" not in recipients

    def test_route_excludes_sender_from_targeted(self, simple_group: AgentGroup):
        """Test sender is excluded even if in recipients."""
        pattern = PeerToPeerPattern(simple_group)

        message = GroupMessage.create(
            group_id=simple_group.id,
            sender="agent-a",
            text="Hello",
            message_type=MessageType.INFORM,
            recipients=["agent-a", "agent-b"],  # Includes sender
        )

        recipients = pattern.route_message(message)
        assert recipients == ["agent-b"]
        assert "agent-a" not in recipients

    def test_get_agent_context(
        self,
        simple_group: AgentGroup,
        session: GroupSession,
    ):
        """Test agent context in peer-to-peer mode."""
        pattern = PeerToPeerPattern(simple_group)

        context = pattern.get_agent_context(session, "agent-a")

        assert context["pattern"] == "peer-to-peer"
        assert context["can_broadcast"] is True
        assert set(context["can_message"]) == {"agent-b", "agent-c"}

    def test_get_agent_context_messages_to_me(
        self,
        simple_group: AgentGroup,
        session: GroupSession,
    ):
        """Test context includes messages directed to agent."""
        pattern = PeerToPeerPattern(simple_group)

        # Add broadcast message
        session.add_message(
            GroupMessage.create(
                group_id=simple_group.id,
                sender="agent-b",
                text="Broadcast",
                message_type=MessageType.INFORM,
                recipients=None,
            )
        )

        # Add targeted message to agent-a
        session.add_message(
            GroupMessage.create(
                group_id=simple_group.id,
                sender="agent-c",
                text="For A only",
                message_type=MessageType.INFORM,
                recipients=["agent-a"],
            )
        )

        # Add message NOT to agent-a
        session.add_message(
            GroupMessage.create(
                group_id=simple_group.id,
                sender="agent-b",
                text="For C only",
                message_type=MessageType.INFORM,
                recipients=["agent-c"],
            )
        )

        context = pattern.get_agent_context(session, "agent-a")

        # Agent-a should see broadcast and targeted message, not message to c
        messages_to_me = context["messages_to_me"]
        assert len(messages_to_me) == 2
        texts = [m.get_text_content() for m in messages_to_me]
        assert "Broadcast" in texts
        assert "For A only" in texts
        assert "For C only" not in texts


class TestBroadcastPattern:
    """Tests for broadcast communication pattern."""

    def test_init(self, simple_group: AgentGroup):
        """Test pattern initialization."""
        pattern = BroadcastPattern(simple_group)
        assert pattern.group == simple_group

    def test_route_message_always_broadcasts(self, simple_group: AgentGroup):
        """Test all messages are broadcast."""
        pattern = BroadcastPattern(simple_group)

        # Even with recipients specified, broadcast to all
        message = GroupMessage.create(
            group_id=simple_group.id,
            sender="agent-a",
            text="To B only?",
            message_type=MessageType.INFORM,
            recipients=["agent-b"],  # Should be ignored
        )

        recipients = pattern.route_message(message)
        # All members except sender
        assert set(recipients) == {"agent-b", "agent-c"}

    def test_route_excludes_sender(self, simple_group: AgentGroup):
        """Test sender is always excluded."""
        pattern = BroadcastPattern(simple_group)

        for sender in simple_group.members:
            message = GroupMessage.create(
                group_id=simple_group.id,
                sender=sender,
                text="Hello",
                message_type=MessageType.INFORM,
            )
            recipients = pattern.route_message(message)
            assert sender not in recipients
            assert len(recipients) == len(simple_group.members) - 1

    def test_get_agent_context(
        self,
        simple_group: AgentGroup,
        session: GroupSession,
    ):
        """Test agent context in broadcast mode."""
        pattern = BroadcastPattern(simple_group)

        context = pattern.get_agent_context(session, "agent-a")

        assert context["pattern"] == "broadcast"
        assert context["all_messages_visible"] is True
        assert context["can_message"] is None  # No direct messaging
        assert context["can_broadcast"] is True


class TestCoordinatorPattern:
    """Tests for coordinator communication pattern."""

    def test_init(self, coordinator_group: AgentGroup):
        """Test pattern initialization."""
        pattern = CoordinatorPattern(coordinator_group)
        assert pattern.group == coordinator_group
        assert pattern.coordinator_id == "coordinator"

    def test_init_without_coordinator_raises_error(self, simple_group: AgentGroup):
        """Test initialization fails without coordinator."""
        with pytest.raises(ValueError, match="no coordinator"):
            CoordinatorPattern(simple_group)

    def test_coordinator_can_send_to_anyone(self, coordinator_group: AgentGroup):
        """Test coordinator can send to any member."""
        pattern = CoordinatorPattern(coordinator_group)

        assert pattern.can_send_to("coordinator", "worker-1") is True
        assert pattern.can_send_to("coordinator", "worker-2") is True

    def test_worker_can_only_send_to_coordinator(self, coordinator_group: AgentGroup):
        """Test workers can only send to coordinator."""
        pattern = CoordinatorPattern(coordinator_group)

        # Worker can message coordinator
        assert pattern.can_send_to("worker-1", "coordinator") is True

        # Worker cannot message other workers
        assert pattern.can_send_to("worker-1", "worker-2") is False

    def test_route_coordinator_broadcast(self, coordinator_group: AgentGroup):
        """Test coordinator broadcast reaches all workers."""
        pattern = CoordinatorPattern(coordinator_group)

        message = GroupMessage.create(
            group_id=coordinator_group.id,
            sender="coordinator",
            text="Attention all",
            message_type=MessageType.INFORM,
            recipients=None,  # Broadcast
        )

        recipients = pattern.route_message(message)
        assert set(recipients) == {"worker-1", "worker-2"}

    def test_route_coordinator_targeted(self, coordinator_group: AgentGroup):
        """Test coordinator targeted message."""
        pattern = CoordinatorPattern(coordinator_group)

        message = GroupMessage.create(
            group_id=coordinator_group.id,
            sender="coordinator",
            text="Worker 1 only",
            message_type=MessageType.INFORM,
            recipients=["worker-1"],
        )

        recipients = pattern.route_message(message)
        assert recipients == ["worker-1"]

    def test_route_worker_message_to_coordinator(self, coordinator_group: AgentGroup):
        """Test worker message goes to coordinator only."""
        pattern = CoordinatorPattern(coordinator_group)

        message = GroupMessage.create(
            group_id=coordinator_group.id,
            sender="worker-1",
            text="Request help",
            message_type=MessageType.REQUEST,
            recipients=["worker-2"],  # Should be ignored
        )

        recipients = pattern.route_message(message)
        assert recipients == ["coordinator"]

    def test_get_coordinator_context(self, coordinator_group: AgentGroup):
        """Test coordinator receives special context."""
        pattern = CoordinatorPattern(coordinator_group)
        session = GroupSession(group_id=coordinator_group.id, goal="Test")

        context = pattern.get_agent_context(session, "coordinator")

        assert context["pattern"] == "coordinator"
        assert context["is_coordinator"] is True
        assert "coordinator" in context["can_message"]
        assert set(context["can_delegate_to"]) == {"worker-1", "worker-2"}
        assert context["can_broadcast"] is True
        assert "pending_requests" in context

    def test_get_worker_context(self, coordinator_group: AgentGroup):
        """Test worker receives limited context."""
        pattern = CoordinatorPattern(coordinator_group)
        session = GroupSession(group_id=coordinator_group.id, goal="Test")

        context = pattern.get_agent_context(session, "worker-1")

        assert context["pattern"] == "coordinator"
        assert context["is_coordinator"] is False
        assert context["can_message"] == ["coordinator"]
        assert context["coordinator"] == "coordinator"
        assert context["can_broadcast"] is False
        assert "my_assignments" in context

    def test_pending_requests_tracking(self, coordinator_group: AgentGroup):
        """Test coordinator sees pending requests."""
        pattern = CoordinatorPattern(coordinator_group)
        session = GroupSession(group_id=coordinator_group.id, goal="Test")

        # Worker sends request
        request = GroupMessage.create(
            group_id=coordinator_group.id,
            sender="worker-1",
            text="Need help",
            message_type=MessageType.REQUEST,
        )
        session.add_message(request)

        context = pattern.get_agent_context(session, "coordinator")
        assert len(context["pending_requests"]) == 1
        assert context["pending_requests"][0].id == request.id

    def test_pending_requests_excludes_responded(self, coordinator_group: AgentGroup):
        """Test responded requests are not pending."""
        pattern = CoordinatorPattern(coordinator_group)
        session = GroupSession(group_id=coordinator_group.id, goal="Test")

        # Worker sends request
        request = GroupMessage.create(
            group_id=coordinator_group.id,
            sender="worker-1",
            text="Need help",
            message_type=MessageType.REQUEST,
        )
        session.add_message(request)

        # Coordinator responds
        response = GroupMessage.create(
            group_id=coordinator_group.id,
            sender="coordinator",
            text="Here's help",
            message_type=MessageType.INFORM,
            in_reply_to=request.id,
        )
        session.add_message(response)

        context = pattern.get_agent_context(session, "coordinator")
        assert len(context["pending_requests"]) == 0

    def test_worker_assignments(self, coordinator_group: AgentGroup):
        """Test worker sees their assignments."""
        pattern = CoordinatorPattern(coordinator_group)
        session = GroupSession(group_id=coordinator_group.id, goal="Test")

        # Coordinator delegates to worker-1
        delegation = GroupMessage.create(
            group_id=coordinator_group.id,
            sender="coordinator",
            text="Please handle task X",
            message_type=MessageType.DELEGATE,
            recipients=["worker-1"],
        )
        session.add_message(delegation)

        # Add another delegation to worker-2
        other_delegation = GroupMessage.create(
            group_id=coordinator_group.id,
            sender="coordinator",
            text="Please handle task Y",
            message_type=MessageType.DELEGATE,
            recipients=["worker-2"],
        )
        session.add_message(other_delegation)

        # Worker-1 should see their assignment only
        context1 = pattern.get_agent_context(session, "worker-1")
        assert len(context1["my_assignments"]) == 1
        assert "task X" in context1["my_assignments"][0].get_text_content()

        # Worker-2 should see their assignment only
        context2 = pattern.get_agent_context(session, "worker-2")
        assert len(context2["my_assignments"]) == 1
        assert "task Y" in context2["my_assignments"][0].get_text_content()

    def test_broadcast_delegation_visible_to_all(self, coordinator_group: AgentGroup):
        """Test broadcast delegation is visible to all workers."""
        pattern = CoordinatorPattern(coordinator_group)
        session = GroupSession(group_id=coordinator_group.id, goal="Test")

        # Coordinator broadcasts delegation
        delegation = GroupMessage.create(
            group_id=coordinator_group.id,
            sender="coordinator",
            text="Everyone handle this",
            message_type=MessageType.DELEGATE,
            recipients=None,  # Broadcast
        )
        session.add_message(delegation)

        # Both workers should see it
        context1 = pattern.get_agent_context(session, "worker-1")
        context2 = pattern.get_agent_context(session, "worker-2")

        assert len(context1["my_assignments"]) == 1
        assert len(context2["my_assignments"]) == 1
