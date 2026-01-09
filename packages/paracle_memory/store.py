"""Memory storage implementations.

This module provides storage backends for agent memory.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

from paracle_core.compat import UTC, datetime

from paracle_memory.models import Memory, MemorySummary, MemoryType

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class MemoryStoreError(Exception):
    """Base exception for memory store errors."""

    pass


class MemoryStore(ABC):
    """Abstract base class for memory storage."""

    @abstractmethod
    async def save(self, memory: Memory) -> str:
        """Save a memory record.

        Args:
            memory: Memory to save

        Returns:
            Memory ID
        """
        pass

    @abstractmethod
    async def get(self, memory_id: str) -> Memory | None:
        """Get a memory by ID.

        Args:
            memory_id: Memory ID

        Returns:
            Memory if found, None otherwise
        """
        pass

    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID.

        Args:
            memory_id: Memory ID

        Returns:
            True if deleted
        """
        pass

    @abstractmethod
    async def list_by_agent(
        self,
        agent_id: str,
        *,
        memory_type: MemoryType | None = None,
        tags: list[str] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Memory]:
        """List memories for an agent.

        Args:
            agent_id: Agent ID
            memory_type: Optional filter by type
            tags: Optional filter by tags
            limit: Maximum results
            offset: Result offset

        Returns:
            List of memories
        """
        pass

    @abstractmethod
    async def search(
        self,
        agent_id: str,
        query_embedding: list[float],
        *,
        top_k: int = 10,
        memory_type: MemoryType | None = None,
        min_score: float = 0.0,
    ) -> list[tuple[Memory, float]]:
        """Search memories by semantic similarity.

        Args:
            agent_id: Agent ID
            query_embedding: Query embedding vector
            top_k: Number of results
            memory_type: Optional filter by type
            min_score: Minimum similarity score

        Returns:
            List of (memory, score) tuples
        """
        pass

    @abstractmethod
    async def clear_agent(self, agent_id: str) -> int:
        """Clear all memories for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Number of memories deleted
        """
        pass

    @abstractmethod
    async def get_summary(self, agent_id: str) -> MemorySummary:
        """Get memory summary for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Memory summary
        """
        pass

    @abstractmethod
    async def cleanup_expired(self) -> int:
        """Remove expired memories.

        Returns:
            Number of memories removed
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the store connection."""
        pass


class InMemoryStore(MemoryStore):
    """In-memory storage for testing and ephemeral use."""

    def __init__(self) -> None:
        self._memories: dict[str, Memory] = {}

    async def save(self, memory: Memory) -> str:
        self._memories[memory.id] = memory
        return memory.id

    async def get(self, memory_id: str) -> Memory | None:
        memory = self._memories.get(memory_id)
        if memory:
            memory.update_access()
        return memory

    async def delete(self, memory_id: str) -> bool:
        if memory_id in self._memories:
            del self._memories[memory_id]
            return True
        return False

    async def list_by_agent(
        self,
        agent_id: str,
        *,
        memory_type: MemoryType | None = None,
        tags: list[str] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Memory]:
        results = []
        for memory in self._memories.values():
            if memory.agent_id != agent_id:
                continue
            if memory_type and memory.memory_type != memory_type:
                continue
            if tags and not any(t in memory.tags for t in tags):
                continue
            if not memory.is_expired():
                results.append(memory)

        # Sort by created_at descending
        results.sort(key=lambda m: m.created_at, reverse=True)
        return results[offset : offset + limit]

    async def search(
        self,
        agent_id: str,
        query_embedding: list[float],
        *,
        top_k: int = 10,
        memory_type: MemoryType | None = None,
        min_score: float = 0.0,
    ) -> list[tuple[Memory, float]]:
        """Search by cosine similarity."""
        results = []

        for memory in self._memories.values():
            if memory.agent_id != agent_id:
                continue
            if memory_type and memory.memory_type != memory_type:
                continue
            if memory.is_expired():
                continue
            if memory.embedding is None:
                continue

            score = self._cosine_similarity(query_embedding, memory.embedding)
            if score >= min_score:
                results.append((memory, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    async def clear_agent(self, agent_id: str) -> int:
        to_delete = [mid for mid, m in self._memories.items() if m.agent_id == agent_id]
        for mid in to_delete:
            del self._memories[mid]
        return len(to_delete)

    async def get_summary(self, agent_id: str) -> MemorySummary:
        memories = [m for m in self._memories.values() if m.agent_id == agent_id]

        by_type: dict[str, int] = {}
        oldest = None
        newest = None
        total_access = 0

        for m in memories:
            by_type[m.memory_type.value] = by_type.get(m.memory_type.value, 0) + 1
            total_access += m.access_count
            if oldest is None or m.created_at < oldest:
                oldest = m.created_at
            if newest is None or m.created_at > newest:
                newest = m.created_at

        return MemorySummary(
            agent_id=agent_id,
            total_memories=len(memories),
            by_type=by_type,
            oldest_memory=oldest,
            newest_memory=newest,
            total_access_count=total_access,
        )

    async def cleanup_expired(self) -> int:
        expired = [mid for mid, m in self._memories.items() if m.is_expired()]
        for mid in expired:
            del self._memories[mid]
        return len(expired)

    async def close(self) -> None:
        self._memories.clear()

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)


class SQLiteMemoryStore(MemoryStore):
    """SQLite-based memory storage."""

    def __init__(self, database_path: str | Path) -> None:
        self._db_path = Path(database_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: Any = None

    def _get_connection(self) -> Any:
        """Get or create database connection."""
        if self._connection is None:
            import sqlite3

            self._connection = sqlite3.connect(
                str(self._db_path),
                check_same_thread=False,
            )
            self._connection.row_factory = sqlite3.Row
            self._create_schema()
        return self._connection

    def _create_schema(self) -> None:
        """Create database schema."""
        conn = self._get_connection()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                content TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                tags TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}',
                importance REAL DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                expires_at TEXT,
                embedding TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_memories_agent
                ON memories(agent_id);
            CREATE INDEX IF NOT EXISTS idx_memories_type
                ON memories(agent_id, memory_type);
            CREATE INDEX IF NOT EXISTS idx_memories_created
                ON memories(agent_id, created_at);
        """
        )
        conn.commit()

    async def save(self, memory: Memory) -> str:
        conn = self._get_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO memories
            (id, agent_id, content, memory_type, tags, metadata,
             importance, access_count, created_at, last_accessed,
             expires_at, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory.id,
                memory.agent_id,
                memory.content,
                memory.memory_type.value,
                json.dumps(memory.tags),
                json.dumps(memory.metadata),
                memory.importance,
                memory.access_count,
                memory.created_at.isoformat(),
                memory.last_accessed.isoformat(),
                memory.expires_at.isoformat() if memory.expires_at else None,
                json.dumps(memory.embedding) if memory.embedding else None,
            ),
        )
        conn.commit()
        return memory.id

    async def get(self, memory_id: str) -> Memory | None:
        conn = self._get_connection()
        row = conn.execute(
            "SELECT * FROM memories WHERE id = ?", (memory_id,)
        ).fetchone()

        if not row:
            return None

        memory = self._row_to_memory(row)

        # Update access
        memory.update_access()
        conn.execute(
            "UPDATE memories SET access_count = ?, last_accessed = ? WHERE id = ?",
            (memory.access_count, memory.last_accessed.isoformat(), memory_id),
        )
        conn.commit()

        return memory

    async def delete(self, memory_id: str) -> bool:
        conn = self._get_connection()
        cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.commit()
        return cursor.rowcount > 0

    async def list_by_agent(
        self,
        agent_id: str,
        *,
        memory_type: MemoryType | None = None,
        tags: list[str] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Memory]:
        conn = self._get_connection()

        query = "SELECT * FROM memories WHERE agent_id = ?"
        params: list[Any] = [agent_id]

        if memory_type:
            query += " AND memory_type = ?"
            params.append(memory_type.value)

        # Filter expired
        query += " AND (expires_at IS NULL OR expires_at > ?)"
        params.append(datetime.now(UTC).isoformat())

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        memories = [self._row_to_memory(row) for row in rows]

        # Filter by tags in Python (SQLite JSON support is limited)
        if tags:
            memories = [m for m in memories if any(t in m.tags for t in tags)]

        return memories

    async def search(
        self,
        agent_id: str,
        query_embedding: list[float],
        *,
        top_k: int = 10,
        memory_type: MemoryType | None = None,
        min_score: float = 0.0,
    ) -> list[tuple[Memory, float]]:
        """Search by cosine similarity (in-memory computation)."""
        conn = self._get_connection()

        query = """
            SELECT * FROM memories
            WHERE agent_id = ?
            AND embedding IS NOT NULL
            AND (expires_at IS NULL OR expires_at > ?)
        """
        params: list[Any] = [agent_id, datetime.now(UTC).isoformat()]

        if memory_type:
            query += " AND memory_type = ?"
            params.append(memory_type.value)

        rows = conn.execute(query, params).fetchall()

        results = []
        for row in rows:
            memory = self._row_to_memory(row)
            if memory.embedding:
                score = InMemoryStore._cosine_similarity(
                    query_embedding, memory.embedding
                )
                if score >= min_score:
                    results.append((memory, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    async def clear_agent(self, agent_id: str) -> int:
        conn = self._get_connection()
        cursor = conn.execute("DELETE FROM memories WHERE agent_id = ?", (agent_id,))
        conn.commit()
        return cursor.rowcount

    async def get_summary(self, agent_id: str) -> MemorySummary:
        conn = self._get_connection()

        # Get counts by type
        rows = conn.execute(
            """
            SELECT memory_type, COUNT(*) as cnt
            FROM memories WHERE agent_id = ?
            GROUP BY memory_type
            """,
            (agent_id,),
        ).fetchall()

        by_type = {row["memory_type"]: row["cnt"] for row in rows}

        # Get stats
        stats = conn.execute(
            """
            SELECT
                COUNT(*) as total,
                MIN(created_at) as oldest,
                MAX(created_at) as newest,
                SUM(access_count) as total_access
            FROM memories WHERE agent_id = ?
            """,
            (agent_id,),
        ).fetchone()

        return MemorySummary(
            agent_id=agent_id,
            total_memories=stats["total"] or 0,
            by_type=by_type,
            oldest_memory=(
                datetime.fromisoformat(stats["oldest"]) if stats["oldest"] else None
            ),
            newest_memory=(
                datetime.fromisoformat(stats["newest"]) if stats["newest"] else None
            ),
            total_access_count=stats["total_access"] or 0,
        )

    async def cleanup_expired(self) -> int:
        conn = self._get_connection()
        cursor = conn.execute(
            "DELETE FROM memories WHERE expires_at IS NOT NULL AND expires_at < ?",
            (datetime.now(UTC).isoformat(),),
        )
        conn.commit()
        return cursor.rowcount

    async def close(self) -> None:
        if self._connection:
            self._connection.close()
            self._connection = None

    def _row_to_memory(self, row: Any) -> Memory:
        """Convert database row to Memory object."""
        return Memory(
            id=row["id"],
            agent_id=row["agent_id"],
            content=row["content"],
            memory_type=MemoryType(row["memory_type"]),
            tags=json.loads(row["tags"]),
            metadata=json.loads(row["metadata"]),
            importance=row["importance"],
            access_count=row["access_count"],
            created_at=datetime.fromisoformat(row["created_at"]),
            last_accessed=datetime.fromisoformat(row["last_accessed"]),
            expires_at=(
                datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None
            ),
            embedding=json.loads(row["embedding"]) if row["embedding"] else None,
        )
