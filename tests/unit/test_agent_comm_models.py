"""Unit tests for paracle_agent_comm models.

Tests for AgentGroup, GroupMessage, GroupSession, and related models.
"""

from datetime import datetime, timezone

from paracle_agent_comm.models import (
    AgentGroup,
    CommunicationPattern,
    GroupConfig,
    GroupMessage,
    GroupSession,
    GroupSessionStatus,
    GroupStatus,
    MessagePart,
    MessagePartType,
    MessageType,
)


class TestMessagePart:
    """Tests for MessagePart model."""

    def test_create_text_part(self):
        """Test creating a text message part."""
        part = MessagePart.text("Hello world")
        assert part.type == MessagePartType.TEXT
        assert part.content == "Hello world"
        assert part.mime_type == "text/plain"

    def test_create_code_part(self):
        """Test creating a code message part."""
        code = "def hello(): pass"
        part = MessagePart.code(code, language="python")
        assert part.type == MessagePartType.CODE
        assert part.content == code
        assert part.language == "python"
        assert "python" in part.mime_type

    def test_create_json_part(self):
        """Test creating a JSON data message part."""
        data = {"key": "value", "count": 42}
        part = MessagePart.json_data(data)
        assert part.type == MessagePartType.JSON
        assert part.content == data
        assert part.mime_type == "application/json"

    def test_default_values(self):
        """Test default values for MessagePart."""
        part = MessagePart()
        assert part.type == MessagePartType.TEXT
        assert part.content == ""
        assert part.mime_type == "text/plain"
        assert part.metadata == {}


class TestGroupMessage:
    """Tests for GroupMessage model."""

    def test_create_simple_message(self):
        """Test creating a simple text message."""
        msg = GroupMessage.create(
            group_id="group-1",
            sender="agent-a",
            text="Hello everyone",
            message_type=MessageType.INFORM,
        )
        assert msg.group_id == "group-1"
        assert msg.sender == "agent-a"
        assert msg.message_type == MessageType.INFORM
        assert msg.recipients is None  # Broadcast
        assert len(msg.content) == 1
        assert msg.get_text_content() == "Hello everyone"

    def test_create_targeted_message(self):
        """Test creating a message with specific recipients."""
        msg = GroupMessage.create(
            group_id="group-1",
            sender="agent-a",
            text="Just for you",
            message_type=MessageType.REQUEST,
            recipients=["agent-b"],
        )
        assert msg.recipients == ["agent-b"]
        assert msg.message_type == MessageType.REQUEST

    def test_create_reply_message(self):
        """Test creating a reply to another message."""
        original = GroupMessage.create(
            group_id="group-1",
            sender="agent-a",
            text="Question?",
            message_type=MessageType.QUERY,
        )
        reply = GroupMessage.create(
            group_id="group-1",
            sender="agent-b",
            text="Answer!",
            message_type=MessageType.INFORM,
            in_reply_to=original.id,
        )
        assert reply.in_reply_to == original.id

    def test_message_has_unique_id(self):
        """Test that each message gets a unique ID."""
        msg1 = GroupMessage.create(
            group_id="g",
            sender="a",
            text="1",
            message_type=MessageType.INFORM,
        )
        msg2 = GroupMessage.create(
            group_id="g",
            sender="a",
            text="2",
            message_type=MessageType.INFORM,
        )
        assert msg1.id != msg2.id

    def test_message_has_timestamp(self):
        """Test that messages have timestamps."""
        before = datetime.now(timezone.utc).replace(tzinfo=None)
        msg = GroupMessage.create(
            group_id="g",
            sender="a",
            text="test",
            message_type=MessageType.INFORM,
        )
        after = datetime.now(timezone.utc).replace(tzinfo=None)
        assert before <= msg.timestamp <= after

    def test_all_message_types(self):
        """Test all message types can be created."""
        for msg_type in MessageType:
            msg = GroupMessage.create(
                group_id="g",
                sender="a",
                text=f"Type: {msg_type.value}",
                message_type=msg_type,
            )
            assert msg.message_type == msg_type

    def test_get_text_content_multiple_parts(self):
        """Test getting text from message with multiple parts."""
        msg = GroupMessage(
            group_id="g",
            sender="a",
            content=[
                MessagePart.text("Line 1"),
                MessagePart.code("code"),
                MessagePart.text("Line 2"),
            ],
            message_type=MessageType.INFORM,
        )
        text = msg.get_text_content()
        assert "Line 1" in text
        assert "Line 2" in text
        assert "code" not in text  # Code parts not included in text content


class TestGroupSession:
    """Tests for GroupSession model."""

    def test_create_session(self):
        """Test creating a new session."""
        session = GroupSession(
            group_id="group-1",
            goal="Design authentication system",
        )
        assert session.group_id == "group-1"
        assert session.goal == "Design authentication system"
        assert session.status == GroupSessionStatus.ACTIVE
        assert session.round_count == 0
        assert session.messages == []
        assert session.shared_context == {}

    def test_add_message(self):
        """Test adding messages to session."""
        session = GroupSession(group_id="g", goal="test")
        msg = GroupMessage.create(
            group_id="g",
            sender="a",
            text="Hello",
            message_type=MessageType.INFORM,
        )
        session.add_message(msg)
        assert len(session.messages) == 1
        assert session.messages[0] == msg

    def test_get_recent_messages(self):
        """Test getting recent messages."""
        session = GroupSession(group_id="g", goal="test")
        for i in range(15):
            msg = GroupMessage.create(
                group_id="g",
                sender="a",
                text=f"Msg {i}",
                message_type=MessageType.INFORM,
            )
            session.add_message(msg)

        recent = session.get_recent_messages(5)
        assert len(recent) == 5
        assert "Msg 14" in recent[-1].get_text_content()
        assert "Msg 10" in recent[0].get_text_content()

    def test_get_messages_by_sender(self):
        """Test filtering messages by sender."""
        session = GroupSession(group_id="g", goal="test")
        session.add_message(
            GroupMessage.create(
                group_id="g",
                sender="a",
                text="From A",
                message_type=MessageType.INFORM,
            )
        )
        session.add_message(
            GroupMessage.create(
                group_id="g",
                sender="b",
                text="From B",
                message_type=MessageType.INFORM,
            )
        )
        session.add_message(
            GroupMessage.create(
                group_id="g",
                sender="a",
                text="From A again",
                message_type=MessageType.INFORM,
            )
        )

        a_msgs = session.get_messages_by_sender("a")
        assert len(a_msgs) == 2
        b_msgs = session.get_messages_by_sender("b")
        assert len(b_msgs) == 1

    def test_get_messages_by_type(self):
        """Test filtering messages by type."""
        session = GroupSession(group_id="g", goal="test")
        session.add_message(
            GroupMessage.create(
                group_id="g",
                sender="a",
                text="Info",
                message_type=MessageType.INFORM,
            )
        )
        session.add_message(
            GroupMessage.create(
                group_id="g",
                sender="b",
                text="Proposal",
                message_type=MessageType.PROPOSE,
            )
        )
        session.add_message(
            GroupMessage.create(
                group_id="g",
                sender="a",
                text="More info",
                message_type=MessageType.INFORM,
            )
        )

        informs = session.get_messages_by_type(MessageType.INFORM)
        assert len(informs) == 2
        proposals = session.get_messages_by_type(MessageType.PROPOSE)
        assert len(proposals) == 1

    def test_has_consensus_no_proposal(self):
        """Test consensus check with no proposal."""
        session = GroupSession(group_id="g", goal="test")
        session.add_message(
            GroupMessage.create(
                group_id="g",
                sender="a",
                text="Info",
                message_type=MessageType.INFORM,
            )
        )
        assert session.has_consensus() is False

    def test_has_consensus_with_accepts(self):
        """Test consensus check with proposal and accepts."""
        session = GroupSession(group_id="g", goal="test")

        # Proposal
        session.add_message(
            GroupMessage.create(
                group_id="g",
                sender="a",
                text="Proposal",
                message_type=MessageType.PROPOSE,
            )
        )

        # Accepts from all participants
        session.add_message(
            GroupMessage.create(
                group_id="g",
                sender="b",
                text="OK",
                message_type=MessageType.ACCEPT,
            )
        )
        session.add_message(
            GroupMessage.create(
                group_id="g",
                sender="c",
                text="OK",
                message_type=MessageType.ACCEPT,
            )
        )

        # Check consensus (a proposed, b and c accepted)
        assert session.has_consensus() is True

    def test_session_statuses(self):
        """Test all session statuses."""
        for status in GroupSessionStatus:
            session = GroupSession(group_id="g", goal="test", status=status)
            assert session.status == status


class TestAgentGroup:
    """Tests for AgentGroup model."""

    def test_create_simple_group(self):
        """Test creating a simple group."""
        group = AgentGroup(
            name="Test Team",
            members=["agent-a", "agent-b", "agent-c"],
        )
        assert group.name == "Test Team"
        assert len(group.members) == 3
        assert group.coordinator is None
        assert group.communication_pattern == CommunicationPattern.PEER_TO_PEER
        assert group.status == GroupStatus.IDLE

    def test_create_group_with_coordinator(self):
        """Test creating a group with coordinator."""
        group = AgentGroup(
            name="Coordinated Team",
            members=["arch", "coder", "tester"],
            coordinator="arch",
            communication_pattern=CommunicationPattern.COORDINATOR,
        )
        assert group.coordinator == "arch"
        assert group.communication_pattern == CommunicationPattern.COORDINATOR

    def test_validate_member(self):
        """Test member validation."""
        group = AgentGroup(name="Team", members=["a", "b", "c"])
        assert group.validate_member("a") is True
        assert group.validate_member("b") is True
        assert group.validate_member("d") is False
        assert group.validate_member("system") is True  # System always valid

    def test_is_coordinator(self):
        """Test coordinator check."""
        group = AgentGroup(
            name="Team",
            members=["a", "b"],
            coordinator="a",
        )
        assert group.is_coordinator("a") is True
        assert group.is_coordinator("b") is False

    def test_get_member_count(self):
        """Test member count with external members."""
        group = AgentGroup(
            name="Team",
            members=["a", "b"],
            external_members=[
                {"url": "http://external1.com", "card": "card1"},
                {"url": "http://external2.com", "card": "card2"},
            ],
        )
        assert group.get_member_count() == 4

    def test_default_limits(self):
        """Test default limits are set."""
        group = AgentGroup(name="Team", members=["a"])
        assert group.max_rounds == 10
        assert group.max_messages == 100
        assert abs(group.timeout_seconds - 300.0) < 0.01

    def test_custom_limits(self):
        """Test custom limits."""
        group = AgentGroup(
            name="Team",
            members=["a"],
            max_rounds=5,
            max_messages=50,
            timeout_seconds=60.0,
        )
        assert group.max_rounds == 5
        assert group.max_messages == 50
        assert abs(group.timeout_seconds - 60.0) < 0.01

    def test_all_communication_patterns(self):
        """Test all communication patterns."""
        for pattern in CommunicationPattern:
            group = AgentGroup(
                name="Team",
                members=["a", "b"],
                communication_pattern=pattern,
            )
            assert group.communication_pattern == pattern


class TestGroupConfig:
    """Tests for GroupConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = GroupConfig()
        assert config.require_consensus is False
        assert config.require_all_participants is True
        assert config.min_rounds == 1
        assert config.max_tokens_per_round == 10000
        assert abs(config.max_cost_per_session - 10.0) < 0.01
        assert config.allow_delegation is True
        assert config.allow_human_injection is True
        assert config.record_reasoning is True
        assert config.retry_on_failure is True
        assert config.max_retries == 3

    def test_custom_config(self):
        """Test custom configuration."""
        config = GroupConfig(
            require_consensus=True,
            max_cost_per_session=5.0,
            allow_human_injection=False,
        )
        assert config.require_consensus is True
        assert abs(config.max_cost_per_session - 5.0) < 0.01
        assert config.allow_human_injection is False


class TestMessageType:
    """Tests for MessageType enum."""

    def test_all_message_types_exist(self):
        """Test all expected message types exist."""
        expected = [
            "inform", "request", "propose", "accept",
            "reject", "query", "delegate", "confirm", "cancel"
        ]
        actual = [mt.value for mt in MessageType]
        for exp in expected:
            assert exp in actual, f"Missing message type: {exp}"

    def test_message_type_values(self):
        """Test message type values are lowercase strings."""
        for mt in MessageType:
            assert mt.value == mt.value.lower()
            assert isinstance(mt.value, str)
