"""Memory system configuration.

This module defines configuration for the memory system.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class MemoryBackend(str, Enum):
    """Available memory storage backends."""

    # In-memory storage (testing, ephemeral)
    MEMORY = "memory"

    # SQLite storage (local persistence)
    SQLITE = "sqlite"

    # Vector store (semantic search)
    VECTOR = "vector"

    # Hybrid (SQLite + Vector)
    HYBRID = "hybrid"


class MemoryConfig(BaseModel):
    """Memory system configuration.

    Attributes:
        backend: Storage backend to use
        persist_dir: Directory for persistent storage
        database_url: Database URL (for SQLite/PostgreSQL)
        vector_store_type: Vector store type (chroma, pgvector)
        embedding_provider: Embedding provider (openai, local, mock)
        embedding_model: Embedding model name
        embedding_dimension: Embedding dimension
        max_short_term_memories: Max short-term memories per agent
        short_term_ttl_hours: Short-term memory TTL
        cleanup_interval_hours: Cleanup interval for expired memories
        enable_semantic_search: Enable semantic search
        similarity_threshold: Minimum similarity for search results
    """

    backend: MemoryBackend = MemoryBackend.SQLITE
    persist_dir: Path | str = ".paracle/memory"
    database_url: str | None = None
    vector_store_type: str = "chroma"
    embedding_provider: str = "mock"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    max_short_term_memories: int = 100
    short_term_ttl_hours: int = 24
    cleanup_interval_hours: int = 1
    enable_semantic_search: bool = True
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

    model_config = {"extra": "allow"}

    def get_database_url(self) -> str:
        """Get database URL, using default SQLite if not specified."""
        if self.database_url:
            return self.database_url

        persist_path = Path(self.persist_dir)
        persist_path.mkdir(parents=True, exist_ok=True)
        db_path = persist_path / "memory.db"
        return f"sqlite:///{db_path}"

    def get_vector_dir(self) -> Path:
        """Get vector store directory."""
        persist_path = Path(self.persist_dir)
        vector_dir = persist_path / "vectors"
        vector_dir.mkdir(parents=True, exist_ok=True)
        return vector_dir


class MemoryRetentionPolicy(BaseModel):
    """Policy for memory retention and cleanup.

    Attributes:
        max_age_days: Maximum age in days (None = no limit)
        max_memories: Maximum memories per agent
        min_importance: Minimum importance to retain
        min_access_count: Minimum access count to retain
        keep_recent: Number of recent memories to always keep
    """

    max_age_days: int | None = None
    max_memories: int | None = 1000
    min_importance: float = 0.0
    min_access_count: int = 0
    keep_recent: int = 50

    def should_retain(
        self,
        age_days: float,
        importance: float,
        access_count: int,
        rank: int,
    ) -> bool:
        """Check if a memory should be retained.

        Args:
            age_days: Age of memory in days
            importance: Memory importance score
            access_count: Number of times accessed
            rank: Rank by recency (0 = most recent)

        Returns:
            True if memory should be retained
        """
        # Always keep recent memories
        if rank < self.keep_recent:
            return True

        # Check age limit
        if self.max_age_days is not None and age_days > self.max_age_days:
            return False

        # Check importance threshold
        if importance < self.min_importance:
            return False

        # Check access count
        if access_count < self.min_access_count:
            return False

        return True
