"""Tests for memory models."""

from datetime import UTC, datetime, timedelta

import pytest

from paracle_memory.models import (
    ConversationMemory,
    EpisodicMemory,
    Memory,
    MemorySummary,
    MemoryType,
    SemanticMemory,
    WorkingMemory,
)


class TestMemory:
    """Tests for Memory model."""

    def test_create_memory(self) -> None:
        """Test creating a memory."""
        memory = Memory(
            agent_id="agent1",
            content="Test memory content",
        )

        assert memory.agent_id == "agent1"
        assert memory.content == "Test memory content"
        assert memory.memory_type == MemoryType.LONG_TERM
        assert memory.importance == 0.5
        assert memory.access_count == 0
        assert memory.id is not None

    def test_memory_with_tags(self) -> None:
        """Test memory with tags."""
        memory = Memory(
            agent_id="agent1",
            content="Test",
            tags=["important", "user-preference"],
        )

        assert "important" in memory.tags
        assert len(memory.tags) == 2

    def test_memory_is_expired(self) -> None:
        """Test memory expiration check."""
        # Not expired
        memory1 = Memory(
            agent_id="agent1",
            content="Test",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        assert not memory1.is_expired()

        # Expired
        memory2 = Memory(
            agent_id="agent1",
            content="Test",
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
        assert memory2.is_expired()

        # No expiration
        memory3 = Memory(agent_id="agent1", content="Test")
        assert not memory3.is_expired()

    def test_update_access(self) -> None:
        """Test updating access count and timestamp."""
        memory = Memory(agent_id="agent1", content="Test")
        initial_count = memory.access_count
        initial_accessed = memory.last_accessed

        memory.update_access()

        assert memory.access_count == initial_count + 1
        assert memory.last_accessed >= initial_accessed

    def test_memory_repr(self) -> None:
        """Test memory string representation."""
        memory = Memory(agent_id="agent1", content="Test")
        repr_str = repr(memory)

        assert "Memory" in repr_str
        assert "agent1" in repr_str


class TestConversationMemory:
    """Tests for ConversationMemory."""

    def test_create_conversation_memory(self) -> None:
        """Test creating conversation memory."""
        memory = ConversationMemory(
            agent_id="agent1",
            content="User said hello",
            role="user",
            turn_index=0,
        )

        assert memory.memory_type == MemoryType.SHORT_TERM
        assert memory.role == "user"
        assert memory.turn_index == 0


class TestEpisodicMemory:
    """Tests for EpisodicMemory."""

    def test_create_episodic_memory(self) -> None:
        """Test creating episodic memory."""
        memory = EpisodicMemory(
            agent_id="agent1",
            content="Completed code review task",
            episode_type="task",
            outcome="success",
            duration_seconds=120.5,
        )

        assert memory.memory_type == MemoryType.EPISODIC
        assert memory.episode_type == "task"
        assert memory.outcome == "success"
        assert memory.duration_seconds == 120.5


class TestSemanticMemory:
    """Tests for SemanticMemory."""

    def test_create_semantic_memory(self) -> None:
        """Test creating semantic memory."""
        memory = SemanticMemory(
            agent_id="agent1",
            content="Python is a programming language",
            source="documentation",
            confidence=0.95,
            embedding=[0.1, 0.2, 0.3],
        )

        assert memory.memory_type == MemoryType.SEMANTIC
        assert memory.source == "documentation"
        assert memory.confidence == 0.95
        assert memory.embedding is not None


class TestWorkingMemory:
    """Tests for WorkingMemory."""

    def test_create_working_memory(self) -> None:
        """Test creating working memory."""
        memory = WorkingMemory(
            agent_id="agent1",
            content="Current task: implement feature X",
            task_id="task123",
            priority=1,
        )

        assert memory.memory_type == MemoryType.WORKING
        assert memory.task_id == "task123"
        assert memory.priority == 1


class TestMemorySummary:
    """Tests for MemorySummary."""

    def test_create_summary(self) -> None:
        """Test creating memory summary."""
        summary = MemorySummary(
            agent_id="agent1",
            total_memories=100,
            by_type={"long_term": 80, "short_term": 20},
            total_access_count=500,
        )

        assert summary.agent_id == "agent1"
        assert summary.total_memories == 100
        assert summary.by_type["long_term"] == 80
