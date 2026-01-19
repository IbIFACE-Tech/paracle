"""Tests for memory storage backends."""

from pathlib import Path

import pytest
from paracle_memory.models import Memory, MemoryType
from paracle_memory.store import InMemoryStore, SQLiteMemoryStore


class TestInMemoryStore:
    """Tests for InMemoryStore."""

    @pytest.fixture
    def store(self) -> InMemoryStore:
        """Create an in-memory store."""
        return InMemoryStore()

    @pytest.mark.asyncio
    async def test_save_and_get(self, store: InMemoryStore) -> None:
        """Test saving and retrieving a memory."""
        memory = Memory(agent_id="agent1", content="Test content")
        memory_id = await store.save(memory)

        retrieved = await store.get(memory_id)
        assert retrieved is not None
        assert retrieved.content == "Test content"
        assert retrieved.access_count == 1  # Incremented on get

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, store: InMemoryStore) -> None:
        """Test getting a non-existent memory."""
        result = await store.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, store: InMemoryStore) -> None:
        """Test deleting a memory."""
        memory = Memory(agent_id="agent1", content="Test")
        memory_id = await store.save(memory)

        deleted = await store.delete(memory_id)
        assert deleted is True

        result = await store.get(memory_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, store: InMemoryStore) -> None:
        """Test deleting a non-existent memory."""
        deleted = await store.delete("nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_list_by_agent(self, store: InMemoryStore) -> None:
        """Test listing memories by agent."""
        await store.save(Memory(agent_id="agent1", content="Memory 1"))
        await store.save(Memory(agent_id="agent1", content="Memory 2"))
        await store.save(Memory(agent_id="agent2", content="Memory 3"))

        memories = await store.list_by_agent("agent1")
        assert len(memories) == 2

    @pytest.mark.asyncio
    async def test_list_by_type(self, store: InMemoryStore) -> None:
        """Test filtering by memory type."""
        await store.save(
            Memory(
                agent_id="agent1",
                content="Long term",
                memory_type=MemoryType.LONG_TERM,
            )
        )
        await store.save(
            Memory(
                agent_id="agent1",
                content="Short term",
                memory_type=MemoryType.SHORT_TERM,
            )
        )

        memories = await store.list_by_agent("agent1", memory_type=MemoryType.LONG_TERM)
        assert len(memories) == 1
        assert memories[0].memory_type == MemoryType.LONG_TERM

    @pytest.mark.asyncio
    async def test_list_with_tags(self, store: InMemoryStore) -> None:
        """Test filtering by tags."""
        await store.save(
            Memory(
                agent_id="agent1",
                content="Tagged",
                tags=["important"],
            )
        )
        await store.save(
            Memory(
                agent_id="agent1",
                content="Untagged",
                tags=[],
            )
        )

        memories = await store.list_by_agent("agent1", tags=["important"])
        assert len(memories) == 1
        assert "important" in memories[0].tags

    @pytest.mark.asyncio
    async def test_search_by_embedding(self, store: InMemoryStore) -> None:
        """Test semantic search."""
        await store.save(
            Memory(
                agent_id="agent1",
                content="Hello",
                embedding=[1.0, 0.0, 0.0],
            )
        )
        await store.save(
            Memory(
                agent_id="agent1",
                content="World",
                embedding=[0.0, 1.0, 0.0],
            )
        )

        results = await store.search(
            "agent1",
            query_embedding=[0.9, 0.1, 0.0],
            top_k=2,
        )

        assert len(results) == 2
        # First result should be more similar to query
        assert results[0][1] > results[1][1]

    @pytest.mark.asyncio
    async def test_clear_agent(self, store: InMemoryStore) -> None:
        """Test clearing agent memories."""
        await store.save(Memory(agent_id="agent1", content="Memory 1"))
        await store.save(Memory(agent_id="agent1", content="Memory 2"))
        await store.save(Memory(agent_id="agent2", content="Memory 3"))

        count = await store.clear_agent("agent1")
        assert count == 2

        remaining = await store.list_by_agent("agent1")
        assert len(remaining) == 0

        agent2_memories = await store.list_by_agent("agent2")
        assert len(agent2_memories) == 1

    @pytest.mark.asyncio
    async def test_get_summary(self, store: InMemoryStore) -> None:
        """Test getting memory summary."""
        await store.save(
            Memory(
                agent_id="agent1",
                content="Long term",
                memory_type=MemoryType.LONG_TERM,
            )
        )
        await store.save(
            Memory(
                agent_id="agent1",
                content="Short term",
                memory_type=MemoryType.SHORT_TERM,
            )
        )

        summary = await store.get_summary("agent1")

        assert summary.agent_id == "agent1"
        assert summary.total_memories == 2
        assert summary.by_type["long_term"] == 1
        assert summary.by_type["short_term"] == 1


class TestSQLiteMemoryStore:
    """Tests for SQLiteMemoryStore."""

    @pytest.fixture
    def store(self, tmp_path: Path) -> SQLiteMemoryStore:
        """Create a SQLite store with temp database."""
        db_path = tmp_path / "test_memory.db"
        return SQLiteMemoryStore(db_path)

    @pytest.mark.asyncio
    async def test_save_and_get(self, store: SQLiteMemoryStore) -> None:
        """Test saving and retrieving a memory."""
        memory = Memory(agent_id="agent1", content="Test content")
        memory_id = await store.save(memory)

        retrieved = await store.get(memory_id)
        assert retrieved is not None
        assert retrieved.content == "Test content"

    @pytest.mark.asyncio
    async def test_save_with_embedding(self, store: SQLiteMemoryStore) -> None:
        """Test saving memory with embedding."""
        memory = Memory(
            agent_id="agent1",
            content="Test",
            embedding=[0.1, 0.2, 0.3],
        )
        memory_id = await store.save(memory)

        retrieved = await store.get(memory_id)
        assert retrieved is not None
        assert retrieved.embedding == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_list_by_agent(self, store: SQLiteMemoryStore) -> None:
        """Test listing memories by agent."""
        await store.save(Memory(agent_id="agent1", content="Memory 1"))
        await store.save(Memory(agent_id="agent1", content="Memory 2"))

        memories = await store.list_by_agent("agent1")
        assert len(memories) == 2

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, store: SQLiteMemoryStore) -> None:
        """Test cleaning up expired memories."""
        from datetime import datetime, timedelta

        from paracle_core.compat import UTC

        # Create expired memory
        expired = Memory(
            agent_id="agent1",
            content="Expired",
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
        await store.save(expired)

        # Create non-expired memory
        valid = Memory(agent_id="agent1", content="Valid")
        await store.save(valid)

        count = await store.cleanup_expired()
        assert count == 1

        remaining = await store.list_by_agent("agent1")
        assert len(remaining) == 1
        assert remaining[0].content == "Valid"

    @pytest.mark.asyncio
    async def test_close(self, store: SQLiteMemoryStore) -> None:
        """Test closing the store."""
        await store.save(Memory(agent_id="agent1", content="Test"))
        await store.close()

        # Connection should be closed
        assert store._connection is None
