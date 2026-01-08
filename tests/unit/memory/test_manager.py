"""Tests for MemoryManager."""

import pytest

from paracle_memory.config import MemoryBackend, MemoryConfig
from paracle_memory.manager import MemoryManager, create_memory_manager
from paracle_memory.models import MemoryType
from paracle_memory.store import InMemoryStore


class TestMemoryManager:
    """Tests for MemoryManager."""

    @pytest.fixture
    def manager(self) -> MemoryManager:
        """Create a memory manager with in-memory store."""
        config = MemoryConfig(
            backend=MemoryBackend.MEMORY,
            enable_semantic_search=False,
        )
        return MemoryManager(config=config)

    @pytest.mark.asyncio
    async def test_store_memory(self, manager: MemoryManager) -> None:
        """Test storing a memory."""
        memory_id = await manager.store(
            agent_id="agent1",
            content="Test memory",
        )

        assert memory_id is not None

        # Retrieve it
        memory = await manager.get(memory_id)
        assert memory is not None
        assert memory.content == "Test memory"
        assert memory.agent_id == "agent1"

    @pytest.mark.asyncio
    async def test_store_with_tags(self, manager: MemoryManager) -> None:
        """Test storing memory with tags."""
        memory_id = await manager.store(
            agent_id="agent1",
            content="Tagged memory",
            tags=["important", "user-pref"],
        )

        memory = await manager.get(memory_id)
        assert memory is not None
        assert "important" in memory.tags

    @pytest.mark.asyncio
    async def test_store_with_importance(self, manager: MemoryManager) -> None:
        """Test storing memory with importance."""
        memory_id = await manager.store(
            agent_id="agent1",
            content="Important memory",
            importance=0.9,
        )

        memory = await manager.get(memory_id)
        assert memory is not None
        assert memory.importance == 0.9

    @pytest.mark.asyncio
    async def test_store_short_term_memory(self, manager: MemoryManager) -> None:
        """Test storing short-term memory sets expiration."""
        memory_id = await manager.store(
            agent_id="agent1",
            content="Short term",
            memory_type=MemoryType.SHORT_TERM,
        )

        memory = await manager.get(memory_id)
        assert memory is not None
        assert memory.memory_type == MemoryType.SHORT_TERM
        assert memory.expires_at is not None

    @pytest.mark.asyncio
    async def test_retrieve_memories(self, manager: MemoryManager) -> None:
        """Test retrieving memories."""
        await manager.store(agent_id="agent1", content="Memory 1")
        await manager.store(agent_id="agent1", content="Memory 2")
        await manager.store(agent_id="agent2", content="Memory 3")

        memories = await manager.retrieve(agent_id="agent1")
        assert len(memories) == 2

    @pytest.mark.asyncio
    async def test_retrieve_by_type(self, manager: MemoryManager) -> None:
        """Test retrieving by memory type."""
        await manager.store(
            agent_id="agent1",
            content="Long term",
            memory_type=MemoryType.LONG_TERM,
        )
        await manager.store(
            agent_id="agent1",
            content="Working",
            memory_type=MemoryType.WORKING,
        )

        memories = await manager.retrieve(
            agent_id="agent1",
            memory_type=MemoryType.LONG_TERM,
        )
        assert len(memories) == 1

    @pytest.mark.asyncio
    async def test_delete_memory(self, manager: MemoryManager) -> None:
        """Test deleting a memory."""
        memory_id = await manager.store(agent_id="agent1", content="To delete")

        deleted = await manager.delete(memory_id)
        assert deleted is True

        memory = await manager.get(memory_id)
        assert memory is None

    @pytest.mark.asyncio
    async def test_clear_agent_memories(self, manager: MemoryManager) -> None:
        """Test clearing all memories for an agent."""
        await manager.store(agent_id="agent1", content="Memory 1")
        await manager.store(agent_id="agent1", content="Memory 2")
        await manager.store(agent_id="agent2", content="Memory 3")

        count = await manager.clear(agent_id="agent1")
        assert count == 2

        # Verify cleared
        memories = await manager.retrieve(agent_id="agent1")
        assert len(memories) == 0

        # Other agent unaffected
        memories2 = await manager.retrieve(agent_id="agent2")
        assert len(memories2) == 1

    @pytest.mark.asyncio
    async def test_get_summary(self, manager: MemoryManager) -> None:
        """Test getting memory summary."""
        await manager.store(
            agent_id="agent1",
            content="Long term",
            memory_type=MemoryType.LONG_TERM,
        )
        await manager.store(
            agent_id="agent1",
            content="Working",
            memory_type=MemoryType.WORKING,
        )

        summary = await manager.get_summary("agent1")

        assert summary.agent_id == "agent1"
        assert summary.total_memories == 2

    @pytest.mark.asyncio
    async def test_close(self, manager: MemoryManager) -> None:
        """Test closing the manager."""
        await manager.store(agent_id="agent1", content="Test")
        await manager.close()

        # Store should be cleared
        assert manager._store is None


class TestCreateMemoryManager:
    """Tests for create_memory_manager factory."""

    @pytest.mark.asyncio
    async def test_create_with_defaults(self, tmp_path) -> None:
        """Test creating manager with defaults."""
        manager = await create_memory_manager(
            backend=MemoryBackend.MEMORY,
            persist_dir=str(tmp_path),
        )

        assert manager is not None
        assert manager._config.backend == MemoryBackend.MEMORY

    @pytest.mark.asyncio
    async def test_create_sqlite_manager(self, tmp_path) -> None:
        """Test creating SQLite manager."""
        manager = await create_memory_manager(
            backend=MemoryBackend.SQLITE,
            persist_dir=str(tmp_path),
        )

        # Store and retrieve
        memory_id = await manager.store(agent_id="agent1", content="Test")
        memory = await manager.get(memory_id)

        assert memory is not None
        assert memory.content == "Test"

        await manager.close()
