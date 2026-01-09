"""Unit tests for paracle_agent_comm persistence.

Tests for InMemorySessionStore and SQLiteSessionStore.
"""

import pytest

from paracle_agent_comm.exceptions import GroupNotFoundError, SessionNotFoundError
from paracle_agent_comm.models import (
    AgentGroup,
    CommunicationPattern,
    GroupMessage,
    GroupSession,
    GroupSessionStatus,
    MessagePart,
    MessageType,
)
from paracle_agent_comm.persistence import (
    InMemorySessionStore,
    SQLiteSessionStore,
)


@pytest.fixture
def group() -> AgentGroup:
    """Create a test group."""
    return AgentGroup(
        name="Test Team",
        members=["agent-a", "agent-b", "agent-c"],
        description="A test team",
    )


@pytest.fixture
def session(group: AgentGroup) -> GroupSession:
    """Create a test session with messages."""
    session = GroupSession(
        group_id=group.id,
        goal="Complete the test task",
        shared_context={"key": "value"},
    )

    # Add some messages
    session.add_message(
        GroupMessage.create(
            group_id=group.id,
            sender="system",
            text="Goal: Complete the test task",
            message_type=MessageType.INFORM,
        )
    )
    session.add_message(
        GroupMessage.create(
            group_id=group.id,
            sender="agent-a",
            text="I will start working on it",
            message_type=MessageType.INFORM,
        )
    )
    session.add_message(
        GroupMessage.create(
            group_id=group.id,
            sender="agent-b",
            text="Here is my proposal",
            message_type=MessageType.PROPOSE,
        )
    )

    return session


@pytest.fixture
def memory_store() -> InMemorySessionStore:
    """Create an in-memory store."""
    return InMemorySessionStore()


@pytest.fixture
def sqlite_store(tmp_path) -> SQLiteSessionStore:
    """Create a SQLite store with temp database."""
    db_path = tmp_path / "test_agent_comm.db"
    return SQLiteSessionStore(db_path)


class TestInMemorySessionStore:
    """Tests for InMemorySessionStore."""

    @pytest.mark.asyncio
    async def test_save_and_get_session(
        self,
        memory_store: InMemorySessionStore,
        session: GroupSession,
    ):
        """Test saving and retrieving a session."""
        await memory_store.save_session(session)
        retrieved = await memory_store.get_session(session.id)

        assert retrieved.id == session.id
        assert retrieved.goal == session.goal
        assert retrieved.group_id == session.group_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_session_raises_error(
        self,
        memory_store: InMemorySessionStore,
    ):
        """Test getting non-existent session raises error."""
        with pytest.raises(SessionNotFoundError):
            await memory_store.get_session("nonexistent-id")

    @pytest.mark.asyncio
    async def test_list_sessions(
        self,
        memory_store: InMemorySessionStore,
        group: AgentGroup,
    ):
        """Test listing sessions."""
        # Create multiple sessions
        session1 = GroupSession(group_id=group.id, goal="Task 1")
        session2 = GroupSession(group_id=group.id, goal="Task 2")
        session3 = GroupSession(group_id="other-group", goal="Task 3")

        await memory_store.save_session(session1)
        await memory_store.save_session(session2)
        await memory_store.save_session(session3)

        # List all
        all_sessions = await memory_store.list_sessions()
        assert len(all_sessions) == 3

        # List by group
        group_sessions = await memory_store.list_sessions(group_id=group.id)
        assert len(group_sessions) == 2

    @pytest.mark.asyncio
    async def test_list_sessions_by_status(
        self,
        memory_store: InMemorySessionStore,
        group: AgentGroup,
    ):
        """Test listing sessions by status."""
        session1 = GroupSession(
            group_id=group.id,
            goal="Active",
            status=GroupSessionStatus.ACTIVE,
        )
        session2 = GroupSession(
            group_id=group.id,
            goal="Completed",
            status=GroupSessionStatus.COMPLETED,
        )

        await memory_store.save_session(session1)
        await memory_store.save_session(session2)

        active = await memory_store.list_sessions(status=GroupSessionStatus.ACTIVE)
        assert len(active) == 1
        assert active[0].goal == "Active"

    @pytest.mark.asyncio
    async def test_delete_session(
        self,
        memory_store: InMemorySessionStore,
        session: GroupSession,
    ):
        """Test deleting a session."""
        await memory_store.save_session(session)
        await memory_store.delete_session(session.id)

        with pytest.raises(SessionNotFoundError):
            await memory_store.get_session(session.id)

    @pytest.mark.asyncio
    async def test_save_and_get_group(
        self,
        memory_store: InMemorySessionStore,
        group: AgentGroup,
    ):
        """Test saving and retrieving a group."""
        await memory_store.save_group(group)
        retrieved = await memory_store.get_group(group.id)

        assert retrieved.id == group.id
        assert retrieved.name == group.name
        assert retrieved.members == group.members

    @pytest.mark.asyncio
    async def test_get_nonexistent_group_raises_error(
        self,
        memory_store: InMemorySessionStore,
    ):
        """Test getting non-existent group raises error."""
        with pytest.raises(GroupNotFoundError):
            await memory_store.get_group("nonexistent-id")

    @pytest.mark.asyncio
    async def test_list_groups(
        self,
        memory_store: InMemorySessionStore,
    ):
        """Test listing groups."""
        group1 = AgentGroup(name="Team 1", members=["a"])
        group2 = AgentGroup(name="Team 2", members=["b"])

        await memory_store.save_group(group1)
        await memory_store.save_group(group2)

        groups = await memory_store.list_groups()
        assert len(groups) == 2

    def test_clear(self, memory_store: InMemorySessionStore):
        """Test clearing all data."""
        memory_store._sessions["test"] = "data"
        memory_store._groups["test"] = "data"

        memory_store.clear()

        assert len(memory_store._sessions) == 0
        assert len(memory_store._groups) == 0


class TestSQLiteSessionStore:
    """Tests for SQLiteSessionStore."""

    @pytest.mark.asyncio
    async def test_save_and_get_session(
        self,
        sqlite_store: SQLiteSessionStore,
        session: GroupSession,
    ):
        """Test saving and retrieving a session."""
        await sqlite_store.save_session(session)
        retrieved = await sqlite_store.get_session(session.id)

        assert retrieved.id == session.id
        assert retrieved.goal == session.goal
        assert retrieved.group_id == session.group_id
        assert retrieved.shared_context == session.shared_context

    @pytest.mark.asyncio
    async def test_session_messages_persisted(
        self,
        sqlite_store: SQLiteSessionStore,
        session: GroupSession,
    ):
        """Test session messages are persisted."""
        await sqlite_store.save_session(session)
        retrieved = await sqlite_store.get_session(session.id)

        assert len(retrieved.messages) == len(session.messages)
        assert (
            retrieved.messages[0].get_text_content() == "Goal: Complete the test task"
        )
        assert retrieved.messages[1].sender == "agent-a"
        assert retrieved.messages[2].message_type == MessageType.PROPOSE

    @pytest.mark.asyncio
    async def test_get_nonexistent_session_raises_error(
        self,
        sqlite_store: SQLiteSessionStore,
    ):
        """Test getting non-existent session raises error."""
        with pytest.raises(SessionNotFoundError):
            await sqlite_store.get_session("nonexistent-id")

    @pytest.mark.asyncio
    async def test_list_sessions(
        self,
        sqlite_store: SQLiteSessionStore,
        group: AgentGroup,
    ):
        """Test listing sessions."""
        session1 = GroupSession(group_id=group.id, goal="Task 1")
        session2 = GroupSession(group_id=group.id, goal="Task 2")
        session3 = GroupSession(group_id="other-group", goal="Task 3")

        await sqlite_store.save_session(session1)
        await sqlite_store.save_session(session2)
        await sqlite_store.save_session(session3)

        # List all
        all_sessions = await sqlite_store.list_sessions()
        assert len(all_sessions) == 3

        # List by group
        group_sessions = await sqlite_store.list_sessions(group_id=group.id)
        assert len(group_sessions) == 2

    @pytest.mark.asyncio
    async def test_list_sessions_by_status(
        self,
        sqlite_store: SQLiteSessionStore,
        group: AgentGroup,
    ):
        """Test listing sessions by status."""
        session1 = GroupSession(
            group_id=group.id,
            goal="Active",
            status=GroupSessionStatus.ACTIVE,
        )
        session2 = GroupSession(
            group_id=group.id,
            goal="Completed",
            status=GroupSessionStatus.COMPLETED,
        )

        await sqlite_store.save_session(session1)
        await sqlite_store.save_session(session2)

        active = await sqlite_store.list_sessions(status=GroupSessionStatus.ACTIVE)
        assert len(active) == 1
        assert active[0].goal == "Active"

    @pytest.mark.asyncio
    async def test_list_sessions_with_limit(
        self,
        sqlite_store: SQLiteSessionStore,
        group: AgentGroup,
    ):
        """Test listing sessions with limit."""
        for i in range(10):
            session = GroupSession(group_id=group.id, goal=f"Task {i}")
            await sqlite_store.save_session(session)

        limited = await sqlite_store.list_sessions(limit=5)
        assert len(limited) == 5

    @pytest.mark.asyncio
    async def test_delete_session(
        self,
        sqlite_store: SQLiteSessionStore,
        session: GroupSession,
    ):
        """Test deleting a session."""
        await sqlite_store.save_session(session)
        await sqlite_store.delete_session(session.id)

        with pytest.raises(SessionNotFoundError):
            await sqlite_store.get_session(session.id)

    @pytest.mark.asyncio
    async def test_delete_session_removes_messages(
        self,
        sqlite_store: SQLiteSessionStore,
        session: GroupSession,
    ):
        """Test deleting session also removes messages."""
        await sqlite_store.save_session(session)

        # Verify messages exist
        count = await sqlite_store.get_message_count(session.id)
        assert count == 3

        # Delete session
        await sqlite_store.delete_session(session.id)

        # Verify messages are gone
        count = await sqlite_store.get_message_count(session.id)
        assert count == 0

    @pytest.mark.asyncio
    async def test_save_and_get_group(
        self,
        sqlite_store: SQLiteSessionStore,
        group: AgentGroup,
    ):
        """Test saving and retrieving a group."""
        await sqlite_store.save_group(group)
        retrieved = await sqlite_store.get_group(group.id)

        assert retrieved.id == group.id
        assert retrieved.name == group.name
        assert retrieved.members == group.members
        assert retrieved.description == group.description

    @pytest.mark.asyncio
    async def test_group_with_coordinator(
        self,
        sqlite_store: SQLiteSessionStore,
    ):
        """Test saving group with coordinator pattern."""
        group = AgentGroup(
            name="Coordinated Team",
            members=["coord", "worker-1", "worker-2"],
            coordinator="coord",
            communication_pattern=CommunicationPattern.COORDINATOR,
            max_rounds=5,
            timeout_seconds=120.0,
        )

        await sqlite_store.save_group(group)
        retrieved = await sqlite_store.get_group(group.id)

        assert retrieved.coordinator == "coord"
        assert retrieved.communication_pattern == CommunicationPattern.COORDINATOR
        assert retrieved.max_rounds == 5
        assert abs(retrieved.timeout_seconds - 120.0) < 0.01

    @pytest.mark.asyncio
    async def test_get_nonexistent_group_raises_error(
        self,
        sqlite_store: SQLiteSessionStore,
    ):
        """Test getting non-existent group raises error."""
        with pytest.raises(GroupNotFoundError):
            await sqlite_store.get_group("nonexistent-id")

    @pytest.mark.asyncio
    async def test_list_groups(
        self,
        sqlite_store: SQLiteSessionStore,
    ):
        """Test listing groups."""
        group1 = AgentGroup(name="Team Alpha", members=["a"])
        group2 = AgentGroup(name="Team Beta", members=["b"])

        await sqlite_store.save_group(group1)
        await sqlite_store.save_group(group2)

        groups = await sqlite_store.list_groups()
        assert len(groups) == 2
        # Should be sorted by name
        assert groups[0].name == "Team Alpha"
        assert groups[1].name == "Team Beta"

    @pytest.mark.asyncio
    async def test_get_group_by_name(
        self,
        sqlite_store: SQLiteSessionStore,
    ):
        """Test getting group by name."""
        group = AgentGroup(name="Unique Team", members=["a"])
        await sqlite_store.save_group(group)

        retrieved = await sqlite_store.get_group_by_name("Unique Team")
        assert retrieved is not None
        assert retrieved.id == group.id

        not_found = await sqlite_store.get_group_by_name("Nonexistent")
        assert not_found is None

    @pytest.mark.asyncio
    async def test_delete_group(
        self,
        sqlite_store: SQLiteSessionStore,
        group: AgentGroup,
    ):
        """Test deleting a group."""
        await sqlite_store.save_group(group)

        # Create sessions for the group
        session = GroupSession(group_id=group.id, goal="Test")
        session.add_message(
            GroupMessage.create(
                group_id=group.id,
                sender="agent-a",
                text="Hello",
                message_type=MessageType.INFORM,
            )
        )
        await sqlite_store.save_session(session)

        # Delete group
        await sqlite_store.delete_group(group.id)

        # Group should be gone
        with pytest.raises(GroupNotFoundError):
            await sqlite_store.get_group(group.id)

        # Sessions should be gone too
        sessions = await sqlite_store.list_sessions(group_id=group.id)
        assert len(sessions) == 0

    @pytest.mark.asyncio
    async def test_get_session_count(
        self,
        sqlite_store: SQLiteSessionStore,
        group: AgentGroup,
    ):
        """Test getting session count."""
        # Initially zero
        count = await sqlite_store.get_session_count()
        assert count == 0

        # Add sessions
        for i in range(5):
            session = GroupSession(group_id=group.id, goal=f"Task {i}")
            await sqlite_store.save_session(session)

        # Count all
        count = await sqlite_store.get_session_count()
        assert count == 5

        # Add session for another group
        other_session = GroupSession(group_id="other", goal="Other")
        await sqlite_store.save_session(other_session)

        # Count by group
        group_count = await sqlite_store.get_session_count(group_id=group.id)
        assert group_count == 5

    @pytest.mark.asyncio
    async def test_update_session(
        self,
        sqlite_store: SQLiteSessionStore,
        session: GroupSession,
    ):
        """Test updating an existing session."""
        await sqlite_store.save_session(session)

        # Modify session
        session.status = GroupSessionStatus.COMPLETED
        session.outcome = "Task completed successfully"
        session.add_message(
            GroupMessage.create(
                group_id=session.group_id,
                sender="agent-c",
                text="Done!",
                message_type=MessageType.CONFIRM,
            )
        )

        # Save again (update)
        await sqlite_store.save_session(session)

        # Retrieve and verify
        retrieved = await sqlite_store.get_session(session.id)
        assert retrieved.status == GroupSessionStatus.COMPLETED
        assert retrieved.outcome == "Task completed successfully"
        assert len(retrieved.messages) == 4

    @pytest.mark.asyncio
    async def test_message_part_types(
        self,
        sqlite_store: SQLiteSessionStore,
        group: AgentGroup,
    ):
        """Test different message part types are persisted."""
        session = GroupSession(group_id=group.id, goal="Test parts")

        # Add message with multiple parts
        message = GroupMessage(
            group_id=group.id,
            sender="agent-a",
            content=[
                MessagePart.text("Here is some code:"),
                MessagePart.code("def hello(): pass", language="python"),
                MessagePart.json_data({"result": 42}),
            ],
            message_type=MessageType.INFORM,
        )
        session.add_message(message)

        await sqlite_store.save_session(session)
        retrieved = await sqlite_store.get_session(session.id)

        msg = retrieved.messages[0]
        assert len(msg.content) == 3
        assert msg.content[0].type.value == "text"
        assert msg.content[1].type.value == "code"
        assert msg.content[1].language == "python"
        assert msg.content[2].type.value == "json"
        assert msg.content[2].content == {"result": 42}
