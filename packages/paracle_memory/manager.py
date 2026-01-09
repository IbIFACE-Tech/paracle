"""Memory manager - high-level memory API.

This module provides the main interface for agent memory management.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from paracle_core.compat import UTC, datetime, timedelta

from paracle_memory.config import MemoryBackend, MemoryConfig, MemoryRetentionPolicy
from paracle_memory.models import Memory, MemorySummary, MemoryType
from paracle_memory.store import InMemoryStore, MemoryStore, SQLiteMemoryStore

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class MemoryManager:
    """High-level memory management interface.

    Provides a unified API for storing, retrieving, and managing
    agent memories with automatic embedding generation and cleanup.

    Usage:
        manager = MemoryManager(config=MemoryConfig(backend="sqlite"))

        # Store a memory
        memory_id = await manager.store(
            agent_id="coder",
            content="User prefers Python 3.12",
            memory_type=MemoryType.LONG_TERM,
            tags=["preferences"]
        )

        # Retrieve memories
        memories = await manager.retrieve(
            agent_id="coder",
            query="What Python version?",
            top_k=5
        )

        # Clear agent memory
        await manager.clear(agent_id="coder")
    """

    def __init__(
        self,
        config: MemoryConfig | None = None,
        store: MemoryStore | None = None,
    ) -> None:
        """Initialize memory manager.

        Args:
            config: Memory configuration
            store: Optional custom memory store
        """
        self._config = config or MemoryConfig()
        self._store = store
        self._embedding_service: Any = None
        self._cleanup_task: asyncio.Task | None = None

    async def _get_store(self) -> MemoryStore:
        """Get or create memory store."""
        if self._store is None:
            if self._config.backend == MemoryBackend.MEMORY:
                self._store = InMemoryStore()
            elif self._config.backend == MemoryBackend.SQLITE:
                db_path = Path(self._config.persist_dir) / "memory.db"
                self._store = SQLiteMemoryStore(db_path)
            elif self._config.backend == MemoryBackend.VECTOR:
                # Use vector store with SQLite fallback for metadata
                db_path = Path(self._config.persist_dir) / "memory.db"
                self._store = SQLiteMemoryStore(db_path)
            elif self._config.backend == MemoryBackend.HYBRID:
                # Hybrid uses SQLite for storage with vector search
                db_path = Path(self._config.persist_dir) / "memory.db"
                self._store = SQLiteMemoryStore(db_path)
            else:
                self._store = InMemoryStore()

        return self._store

    async def _get_embedding_service(self) -> Any:
        """Get or create embedding service."""
        if self._embedding_service is None and self._config.enable_semantic_search:
            try:
                from paracle_vector.embeddings import (
                    EmbeddingConfig,
                    EmbeddingProvider,
                    EmbeddingService,
                )

                provider = EmbeddingProvider(self._config.embedding_provider)
                emb_config = EmbeddingConfig(
                    provider=provider,
                    model=self._config.embedding_model,
                    dimension=self._config.embedding_dimension,
                )
                self._embedding_service = EmbeddingService(config=emb_config)
            except ImportError:
                logger.warning(
                    "paracle_vector not available, disabling semantic search"
                )
                self._config.enable_semantic_search = False

        return self._embedding_service

    async def store(
        self,
        agent_id: str,
        content: str,
        *,
        memory_type: MemoryType = MemoryType.LONG_TERM,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        importance: float = 0.5,
        ttl_hours: int | None = None,
        generate_embedding: bool = True,
    ) -> str:
        """Store a new memory.

        Args:
            agent_id: ID of the agent
            content: Memory content
            memory_type: Type of memory
            tags: Optional tags for categorization
            metadata: Optional metadata
            importance: Importance score (0-1)
            ttl_hours: Time-to-live in hours
            generate_embedding: Whether to generate embedding

        Returns:
            Memory ID
        """
        store = await self._get_store()

        # Calculate expiration
        expires_at = None
        if ttl_hours is not None:
            expires_at = datetime.now(UTC) + timedelta(hours=ttl_hours)
        elif memory_type == MemoryType.SHORT_TERM:
            expires_at = datetime.now(UTC) + timedelta(
                hours=self._config.short_term_ttl_hours
            )

        # Generate embedding if enabled
        embedding = None
        if generate_embedding and self._config.enable_semantic_search:
            embedding_service = await self._get_embedding_service()
            if embedding_service:
                embedding = await embedding_service.embed_single(content)

        memory = Memory(
            agent_id=agent_id,
            content=content,
            memory_type=memory_type,
            tags=tags or [],
            metadata=metadata or {},
            importance=importance,
            expires_at=expires_at,
            embedding=embedding,
        )

        memory_id = await store.save(memory)
        logger.debug("Stored memory %s for agent %s", memory_id, agent_id)

        return memory_id

    async def retrieve(
        self,
        agent_id: str,
        query: str | None = None,
        *,
        top_k: int = 10,
        memory_type: MemoryType | None = None,
        tags: list[str] | None = None,
        min_score: float | None = None,
    ) -> list[Memory]:
        """Retrieve memories for an agent.

        If query is provided, performs semantic search.
        Otherwise returns recent memories.

        Args:
            agent_id: Agent ID
            query: Optional search query
            top_k: Number of results
            memory_type: Filter by memory type
            tags: Filter by tags
            min_score: Minimum similarity score (semantic search only)

        Returns:
            List of memories
        """
        store = await self._get_store()

        if query and self._config.enable_semantic_search:
            # Semantic search
            embedding_service = await self._get_embedding_service()
            if embedding_service:
                query_embedding = await embedding_service.embed_single(query)
                threshold = min_score or self._config.similarity_threshold

                results = await store.search(
                    agent_id,
                    query_embedding,
                    top_k=top_k,
                    memory_type=memory_type,
                    min_score=threshold,
                )

                memories = [memory for memory, score in results]
                logger.debug(
                    "Found %d memories for agent %s (semantic)", len(memories), agent_id
                )
                return memories

        # Fallback to listing
        memories = await store.list_by_agent(
            agent_id,
            memory_type=memory_type,
            tags=tags,
            limit=top_k,
        )
        logger.debug("Found %d memories for agent %s", len(memories), agent_id)
        return memories

    async def get(self, memory_id: str) -> Memory | None:
        """Get a specific memory by ID.

        Args:
            memory_id: Memory ID

        Returns:
            Memory if found
        """
        store = await self._get_store()
        return await store.get(memory_id)

    async def delete(self, memory_id: str) -> bool:
        """Delete a memory.

        Args:
            memory_id: Memory ID

        Returns:
            True if deleted
        """
        store = await self._get_store()
        deleted = await store.delete(memory_id)
        if deleted:
            logger.debug("Deleted memory %s", memory_id)
        return deleted

    async def clear(
        self,
        agent_id: str,
        *,
        memory_type: MemoryType | None = None,
    ) -> int:
        """Clear memories for an agent.

        Args:
            agent_id: Agent ID
            memory_type: Optional filter by type

        Returns:
            Number of memories deleted
        """
        store = await self._get_store()

        if memory_type:
            # Delete by type (get then delete)
            memories = await store.list_by_agent(
                agent_id, memory_type=memory_type, limit=10000
            )
            count = 0
            for memory in memories:
                if await store.delete(memory.id):
                    count += 1
            return count

        count = await store.clear_agent(agent_id)
        logger.info("Cleared %d memories for agent %s", count, agent_id)
        return count

    async def get_summary(self, agent_id: str) -> MemorySummary:
        """Get memory summary for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Memory summary
        """
        store = await self._get_store()
        return await store.get_summary(agent_id)

    async def cleanup(
        self,
        policy: MemoryRetentionPolicy | None = None,
    ) -> int:
        """Clean up memories based on retention policy.

        Args:
            policy: Retention policy (uses defaults if not provided)

        Returns:
            Number of memories removed
        """
        store = await self._get_store()

        # First, remove expired memories
        expired_count = await store.cleanup_expired()
        logger.debug("Removed %d expired memories", expired_count)

        return expired_count

    async def start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        if self._cleanup_task is not None:
            return

        async def cleanup_loop() -> None:
            while True:
                try:
                    await asyncio.sleep(self._config.cleanup_interval_hours * 3600)
                    await self.cleanup()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("Memory cleanup failed: %s", e)

        self._cleanup_task = asyncio.create_task(cleanup_loop())
        logger.info("Started memory cleanup task")

    async def stop_cleanup_task(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Stopped memory cleanup task")

    async def close(self) -> None:
        """Close the memory manager."""
        await self.stop_cleanup_task()
        if self._store:
            await self._store.close()
            self._store = None


# Convenience functions


async def create_memory_manager(
    backend: MemoryBackend = MemoryBackend.SQLITE,
    persist_dir: str | Path = ".paracle/memory",
    **kwargs: Any,
) -> MemoryManager:
    """Create a memory manager with sensible defaults.

    Args:
        backend: Storage backend
        persist_dir: Directory for persistence
        **kwargs: Additional config options

    Returns:
        Configured MemoryManager
    """
    config = MemoryConfig(
        backend=backend,
        persist_dir=persist_dir,
        **kwargs,
    )
    return MemoryManager(config=config)
