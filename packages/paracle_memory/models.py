"""Memory models and types.

This module defines the data structures for agent memory.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from paracle_core.compat import UTC, datetime
from paracle_core.ids import generate_ulid
from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """Types of agent memory."""

    # Short-term: Current conversation context
    SHORT_TERM = "short_term"

    # Long-term: Persistent knowledge
    LONG_TERM = "long_term"

    # Episodic: Specific interaction episodes
    EPISODIC = "episodic"

    # Working: Current task context
    WORKING = "working"

    # Semantic: Conceptual knowledge with embeddings
    SEMANTIC = "semantic"


class Memory(BaseModel):
    """Base memory record.

    Attributes:
        id: Unique memory identifier
        agent_id: ID of the agent this memory belongs to
        content: Memory content (text)
        memory_type: Type of memory
        tags: Optional tags for categorization
        metadata: Additional metadata
        importance: Importance score (0-1)
        access_count: Number of times accessed
        created_at: Creation timestamp
        last_accessed: Last access timestamp
        expires_at: Optional expiration timestamp
    """

    id: str = Field(default_factory=generate_ulid)
    agent_id: str
    content: str
    memory_type: MemoryType = MemoryType.LONG_TERM
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    access_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_accessed: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    embedding: list[float] | None = None

    def is_expired(self) -> bool:
        """Check if memory has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(UTC) > self.expires_at

    def update_access(self) -> None:
        """Update access timestamp and count."""
        self.last_accessed = datetime.now(UTC)
        self.access_count += 1

    def __repr__(self) -> str:
        return f"<Memory(id={self.id!r}, type={self.memory_type.value}, agent={self.agent_id!r})>"


class ConversationMemory(Memory):
    """Short-term conversation memory.

    Stores recent conversation turns for context.
    """

    memory_type: MemoryType = MemoryType.SHORT_TERM
    role: str = "user"  # user, assistant, system
    turn_index: int = 0
    session_id: str | None = None


class EpisodicMemory(Memory):
    """Episodic memory for specific interactions.

    Stores complete interaction episodes with outcomes.
    """

    memory_type: MemoryType = MemoryType.EPISODIC
    episode_type: str = "task"  # task, conversation, error, success
    outcome: str | None = None
    duration_seconds: float | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class SemanticMemory(Memory):
    """Semantic memory with vector embedding.

    Stores conceptual knowledge with embeddings for
    semantic search and retrieval.
    """

    memory_type: MemoryType = MemoryType.SEMANTIC
    source: str | None = None  # Where the knowledge came from
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    related_memories: list[str] = Field(default_factory=list)  # IDs of related memories


class WorkingMemory(Memory):
    """Working memory for current task context.

    Stores temporary task-related information.
    """

    memory_type: MemoryType = MemoryType.WORKING
    task_id: str | None = None
    priority: int = Field(default=0, ge=0)
    context_keys: list[str] = Field(default_factory=list)


class MemorySummary(BaseModel):
    """Summary statistics for agent memory.

    Attributes:
        agent_id: Agent identifier
        total_memories: Total memory count
        by_type: Count by memory type
        oldest_memory: Oldest memory timestamp
        newest_memory: Newest memory timestamp
        total_access_count: Sum of all access counts
    """

    agent_id: str
    total_memories: int = 0
    by_type: dict[str, int] = Field(default_factory=dict)
    oldest_memory: datetime | None = None
    newest_memory: datetime | None = None
    total_access_count: int = 0
