"""Semantic memory capability for MetaAgent.

Hybrid storage combining vector search with structured data:
- Vector embeddings for semantic search
- SQLite for structured metadata
- Automatic embedding generation
- Hybrid queries (semantic + filters)
- Conversation history tracking
- Knowledge graph support

Inspired by AgentDB's hybrid architecture.
"""

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import Field

from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)

# Optional: Use existing vector_search capability
try:
    from paracle_meta.capabilities.vector_search import VectorSearchCapability

    HAS_VECTOR_SEARCH = True
except ImportError:
    HAS_VECTOR_SEARCH = False


class EmbeddingProvider(str):
    """Embedding provider options."""

    OPENAI = "openai"
    LOCAL = "local"  # sentence-transformers
    MOCK = "mock"  # For testing


@dataclass
class Memory:
    """A memory record."""

    id: str
    content: str
    embedding: np.ndarray | None
    memory_type: str  # conversation, knowledge, observation, etc.
    agent_name: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5  # 0.0 to 1.0
    access_count: int = 0
    last_accessed: datetime | None = None

    def to_dict(self, include_embedding: bool = False) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type,
            "agent_name": self.agent_name,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "importance": self.importance,
            "access_count": self.access_count,
            "last_accessed": (
                self.last_accessed.isoformat() if self.last_accessed else None
            ),
        }
        if include_embedding and self.embedding is not None:
            result["embedding"] = self.embedding.tolist()
        return result


@dataclass
class ConversationTurn:
    """A single conversation turn."""

    id: str
    conversation_id: str
    role: str  # user, assistant, system
    content: str
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class SemanticMemoryConfig(CapabilityConfig):
    """Configuration for semantic memory capability."""

    storage_path: Path = Field(
        default=Path("data/semantic_memory"),
        description="Path to store memory data",
    )
    embedding_provider: str = Field(
        default=EmbeddingProvider.MOCK,
        description="Embedding provider (openai, local, mock)",
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Model for embeddings",
    )
    embedding_dimensions: int = Field(
        default=1536,
        description="Embedding vector dimensions",
    )
    enable_vector_search: bool = Field(
        default=True,
        description="Enable vector search integration",
    )
    max_memories: int = Field(
        default=100000,
        description="Maximum memories to store",
    )
    importance_threshold: float = Field(
        default=0.3,
        description="Minimum importance for memory retention",
    )
    auto_prune: bool = Field(
        default=True,
        description="Automatically prune low-importance memories",
    )


class SemanticMemoryCapability(BaseCapability):
    """Semantic memory with hybrid storage.

    Combines vector embeddings with structured metadata for powerful memory:
    - Store memories with automatic embedding generation
    - Semantic search across memory content
    - Hybrid queries (semantic similarity + metadata filters)
    - Conversation history tracking
    - Importance-based retention
    - Access pattern tracking

    Example:
        >>> memory = SemanticMemoryCapability()
        >>> await memory.initialize()

        >>> # Store a memory
        >>> result = await memory.store(
        ...     content="User prefers Python over JavaScript",
        ...     memory_type="knowledge",
        ...     agent_name="assistant",
        ...     metadata={"category": "preferences"},
        ...     importance=0.8
        ... )

        >>> # Semantic search
        >>> results = await memory.search(
        ...     query="What programming language does user like?",
        ...     top_k=5
        ... )

        >>> # Hybrid search (semantic + filters)
        >>> results = await memory.search(
        ...     query="preferences",
        ...     memory_type="knowledge",
        ...     min_importance=0.5
        ... )

        >>> # Track conversation
        >>> await memory.add_conversation_turn(
        ...     conversation_id="conv-123",
        ...     role="user",
        ...     content="What's the weather?"
        ... )
    """

    name = "semantic_memory"
    description = "Hybrid semantic memory with vector search and structured storage"

    def __init__(self, config: SemanticMemoryConfig | None = None):
        """Initialize semantic memory capability."""
        super().__init__(config or SemanticMemoryConfig())
        self.config: SemanticMemoryConfig = self.config
        self._db: sqlite3.Connection | None = None
        self._vector_search: VectorSearchCapability | None = None
        self._embedding_provider = None

    async def initialize(self) -> None:
        """Initialize semantic memory storage."""
        self.config.storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize SQLite database
        db_path = self.config.storage_path / "memory.db"
        self._db = sqlite3.connect(str(db_path))
        self._db.row_factory = sqlite3.Row

        # Create tables
        self._create_tables()

        # Initialize vector search if enabled
        if self.config.enable_vector_search and HAS_VECTOR_SEARCH:
            from paracle_meta.capabilities.vector_search import (
                VectorSearchConfig,
                IndexType,
            )

            vector_config = VectorSearchConfig(
                storage_path=self.config.storage_path / "vectors",
                dimensions=self.config.embedding_dimensions,
                index_type=IndexType.HNSW,
                enable_persistence=True,
            )
            self._vector_search = VectorSearchCapability(vector_config)
            await self._vector_search.initialize()

        # Initialize embedding provider
        self._init_embedding_provider()

        await super().initialize()

    def _create_tables(self) -> None:
        """Create database tables."""
        cursor = self._db.cursor()

        # Memories table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                agent_name TEXT,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                importance REAL DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                last_accessed TEXT,
                has_embedding INTEGER DEFAULT 0
            )
        """
        )

        # Conversations table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                agent_name TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
        """
        )

        # Conversation turns table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_turns (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """
        )

        # Indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_agent_name ON memories(agent_name)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_conv_turns ON conversation_turns(conversation_id)"
        )

        self._db.commit()

    def _init_embedding_provider(self) -> None:
        """Initialize embedding provider."""
        if self.config.embedding_provider == EmbeddingProvider.MOCK:
            # Mock embeddings for testing
            self._embedding_provider = lambda text: np.random.randn(
                self.config.embedding_dimensions
            ).astype(np.float32)
        elif self.config.embedding_provider == EmbeddingProvider.OPENAI:
            try:
                import openai

                client = openai.OpenAI()

                def get_embedding(text: str) -> np.ndarray:
                    response = client.embeddings.create(
                        input=text, model=self.config.embedding_model
                    )
                    return np.array(response.data[0].embedding, dtype=np.float32)

                self._embedding_provider = get_embedding
            except ImportError:
                raise RuntimeError("OpenAI not available. Install: pip install openai")
        elif self.config.embedding_provider == EmbeddingProvider.LOCAL:
            try:
                from sentence_transformers import SentenceTransformer

                model = SentenceTransformer(self.config.embedding_model)
                self._embedding_provider = lambda text: model.encode(
                    text, convert_to_numpy=True
                ).astype(np.float32)
            except ImportError:
                raise RuntimeError(
                    "sentence-transformers not available. Install: pip install sentence-transformers"
                )

    async def shutdown(self) -> None:
        """Cleanup resources."""
        if self._vector_search:
            await self._vector_search.shutdown()

        if self._db:
            self._db.close()
            self._db = None

        await super().shutdown()

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute semantic memory operation.

        Args:
            action: Operation (store, search, recall, forget, conversations, stats)
            **kwargs: Operation-specific parameters

        Returns:
            CapabilityResult with operation outcome
        """
        if not self._initialized:
            await self.initialize()

        action = kwargs.pop("action", "search")
        start_time = time.time()

        try:
            if action == "store":
                result = await self._store_memory(**kwargs)
            elif action == "search":
                result = await self._search_memories(**kwargs)
            elif action == "recall":
                result = self._recall_memory(**kwargs)
            elif action == "forget":
                result = self._forget_memory(**kwargs)
            elif action == "add_turn":
                result = await self._add_conversation_turn(**kwargs)
            elif action == "get_conversation":
                result = self._get_conversation(**kwargs)
            elif action == "list_conversations":
                result = self._list_conversations(**kwargs)
            elif action == "stats":
                result = self._get_stats(**kwargs)
            elif action == "prune":
                result = await self._prune_memories(**kwargs)
            else:
                return CapabilityResult.error_result(
                    capability=self.name,
                    error=f"Unknown action: {action}",
                )

            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.success_result(
                capability=self.name,
                output=result,
                duration_ms=duration_ms,
                action=action,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.error_result(
                capability=self.name,
                error=str(e),
                duration_ms=duration_ms,
                action=action,
            )

    def _generate_id(self, prefix: str = "mem") -> str:
        """Generate unique ID."""
        unique = f"{prefix}-{time.time()}-{np.random.randint(0, 1000000)}"
        return hashlib.md5(unique.encode()).hexdigest()[:16]

    async def _store_memory(
        self,
        content: str,
        memory_type: str,
        agent_name: str | None = None,
        metadata: dict | None = None,
        importance: float = 0.5,
        **extra,
    ) -> dict[str, Any]:
        """Store a new memory.

        Args:
            content: Memory content
            memory_type: Type of memory (conversation, knowledge, observation, etc.)
            agent_name: Associated agent
            metadata: Additional metadata
            importance: Importance score (0.0 to 1.0)

        Returns:
            Memory info
        """
        memory_id = self._generate_id("mem")

        # Generate embedding
        embedding = None
        has_embedding = False
        if self._embedding_provider:
            try:
                embedding = self._embedding_provider(content)
                has_embedding = True
            except Exception as e:
                # Continue without embedding on error
                pass

        # Store in SQLite
        cursor = self._db.cursor()
        cursor.execute(
            """
            INSERT INTO memories (
                id, content, memory_type, agent_name, timestamp,
                metadata, importance, has_embedding
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                memory_id,
                content,
                memory_type,
                agent_name,
                datetime.utcnow().isoformat(),
                json.dumps(metadata or {}),
                importance,
                1 if has_embedding else 0,
            ),
        )
        self._db.commit()

        # Store in vector index if available
        if self._vector_search and embedding is not None:
            await self._vector_search.add(
                id=memory_id,
                vector=embedding,
                content=content,
                metadata={
                    "memory_type": memory_type,
                    "agent_name": agent_name,
                    "importance": importance,
                    **(metadata or {}),
                },
                namespace="memories",
            )

        # Auto-prune if needed
        if self.config.auto_prune:
            count = cursor.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            if count > self.config.max_memories:
                await self._prune_memories()

        return {
            "memory_id": memory_id,
            "content": content,
            "memory_type": memory_type,
            "importance": importance,
            "has_embedding": has_embedding,
        }

    async def _search_memories(
        self,
        query: str,
        top_k: int = 10,
        memory_type: str | None = None,
        agent_name: str | None = None,
        min_importance: float | None = None,
        **extra,
    ) -> dict[str, Any]:
        """Search memories semantically.

        Args:
            query: Search query
            top_k: Maximum results
            memory_type: Filter by type
            agent_name: Filter by agent
            min_importance: Minimum importance

        Returns:
            Search results
        """
        # Generate query embedding
        query_embedding = None
        if self._embedding_provider:
            try:
                query_embedding = self._embedding_provider(query)
            except Exception:
                pass

        # Vector search if available
        if self._vector_search and query_embedding is not None:
            # Build metadata filter
            filter_dict = {}
            if memory_type:
                filter_dict["memory_type"] = memory_type
            if agent_name:
                filter_dict["agent_name"] = agent_name
            if min_importance is not None:
                filter_dict["importance_gte"] = min_importance

            vector_result = await self._vector_search.search(
                query_vector=query_embedding,
                top_k=top_k,
                namespace="memories",
                filter=filter_dict if filter_dict else None,
            )

            if vector_result.success:
                results = vector_result.output.get("results", [])

                # Update access counts
                cursor = self._db.cursor()
                for result in results:
                    memory_id = result["id"]
                    cursor.execute(
                        """
                        UPDATE memories
                        SET access_count = access_count + 1,
                            last_accessed = ?
                        WHERE id = ?
                    """,
                        (datetime.utcnow().isoformat(), memory_id),
                    )
                self._db.commit()

                return {
                    "memories": results,
                    "count": len(results),
                    "method": "vector_search",
                }

        # Fallback: Text search
        cursor = self._db.cursor()

        sql = "SELECT * FROM memories WHERE 1=1"
        params = []

        if memory_type:
            sql += " AND memory_type = ?"
            params.append(memory_type)

        if agent_name:
            sql += " AND agent_name = ?"
            params.append(agent_name)

        if min_importance is not None:
            sql += " AND importance >= ?"
            params.append(min_importance)

        # Simple text search
        sql += " AND content LIKE ?"
        params.append(f"%{query}%")

        sql += " ORDER BY importance DESC, timestamp DESC LIMIT ?"
        params.append(top_k)

        rows = cursor.execute(sql, params).fetchall()

        memories = []
        for row in rows:
            memories.append(
                {
                    "id": row["id"],
                    "content": row["content"],
                    "memory_type": row["memory_type"],
                    "agent_name": row["agent_name"],
                    "timestamp": row["timestamp"],
                    "importance": row["importance"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "score": 0.5,  # Default score for text search
                }
            )

            # Update access count
            cursor.execute(
                """
                UPDATE memories
                SET access_count = access_count + 1,
                    last_accessed = ?
                WHERE id = ?
            """,
                (datetime.utcnow().isoformat(), row["id"]),
            )

        self._db.commit()

        return {
            "memories": memories,
            "count": len(memories),
            "method": "text_search",
        }

    def _recall_memory(self, memory_id: str, **kwargs) -> dict[str, Any]:
        """Recall a specific memory by ID.

        Args:
            memory_id: Memory ID

        Returns:
            Memory details
        """
        cursor = self._db.cursor()
        row = cursor.execute(
            "SELECT * FROM memories WHERE id = ?", (memory_id,)
        ).fetchone()

        if not row:
            raise ValueError(f"Memory not found: {memory_id}")

        # Update access count
        cursor.execute(
            """
            UPDATE memories
            SET access_count = access_count + 1,
                last_accessed = ?
            WHERE id = ?
        """,
            (datetime.utcnow().isoformat(), memory_id),
        )
        self._db.commit()

        return {
            "id": row["id"],
            "content": row["content"],
            "memory_type": row["memory_type"],
            "agent_name": row["agent_name"],
            "timestamp": row["timestamp"],
            "importance": row["importance"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            "access_count": row["access_count"] + 1,
            "last_accessed": datetime.utcnow().isoformat(),
        }

    def _forget_memory(self, memory_id: str, **kwargs) -> dict[str, Any]:
        """Delete a memory.

        Args:
            memory_id: Memory ID to delete

        Returns:
            Deletion result
        """
        cursor = self._db.cursor()

        # Check if exists
        row = cursor.execute(
            "SELECT id FROM memories WHERE id = ?", (memory_id,)
        ).fetchone()
        if not row:
            raise ValueError(f"Memory not found: {memory_id}")

        # Delete from SQLite
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        self._db.commit()

        # Delete from vector index if available
        if self._vector_search:
            # Note: VectorSearchCapability doesn't have delete in current implementation
            # This would need to be added to VectorSearchCapability
            pass

        return {
            "memory_id": memory_id,
            "deleted": True,
        }

    async def _add_conversation_turn(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
        **extra,
    ) -> dict[str, Any]:
        """Add a turn to a conversation.

        Args:
            conversation_id: Conversation ID
            role: Speaker role (user, assistant, system)
            content: Message content
            metadata: Additional metadata

        Returns:
            Turn info
        """
        cursor = self._db.cursor()

        # Ensure conversation exists
        row = cursor.execute(
            "SELECT id FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        if not row:
            # Create new conversation
            cursor.execute(
                """
                INSERT INTO conversations (id, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?)
            """,
                (
                    conversation_id,
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                    json.dumps({}),
                ),
            )

        # Add turn
        turn_id = self._generate_id("turn")
        cursor.execute(
            """
            INSERT INTO conversation_turns (id, conversation_id, role, content, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                turn_id,
                conversation_id,
                role,
                content,
                datetime.utcnow().isoformat(),
                json.dumps(metadata or {}),
            ),
        )

        # Update conversation timestamp
        cursor.execute(
            """
            UPDATE conversations
            SET updated_at = ?
            WHERE id = ?
        """,
            (datetime.utcnow().isoformat(), conversation_id),
        )

        self._db.commit()

        # Optionally store as memory
        await self._store_memory(
            content=content,
            memory_type="conversation",
            metadata={
                "conversation_id": conversation_id,
                "role": role,
                **(metadata or {}),
            },
            importance=0.5,
        )

        return {
            "turn_id": turn_id,
            "conversation_id": conversation_id,
            "role": role,
        }

    def _get_conversation(
        self,
        conversation_id: str,
        limit: int | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Get conversation history.

        Args:
            conversation_id: Conversation ID
            limit: Maximum turns to return

        Returns:
            Conversation turns
        """
        cursor = self._db.cursor()

        sql = """
            SELECT * FROM conversation_turns
            WHERE conversation_id = ?
            ORDER BY timestamp ASC
        """
        params = [conversation_id]

        if limit:
            sql += " LIMIT ?"
            params.append(limit)

        rows = cursor.execute(sql, params).fetchall()

        turns = [
            {
                "id": row["id"],
                "role": row["role"],
                "content": row["content"],
                "timestamp": row["timestamp"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            }
            for row in rows
        ]

        return {
            "conversation_id": conversation_id,
            "turns": turns,
            "count": len(turns),
        }

    def _list_conversations(
        self,
        agent_name: str | None = None,
        limit: int = 50,
        **kwargs,
    ) -> dict[str, Any]:
        """List conversations.

        Args:
            agent_name: Filter by agent
            limit: Maximum conversations

        Returns:
            Conversations list
        """
        cursor = self._db.cursor()

        sql = "SELECT * FROM conversations"
        params = []

        if agent_name:
            sql += " WHERE agent_name = ?"
            params.append(agent_name)

        sql += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        rows = cursor.execute(sql, params).fetchall()

        conversations = [
            {
                "id": row["id"],
                "agent_name": row["agent_name"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            }
            for row in rows
        ]

        return {
            "conversations": conversations,
            "count": len(conversations),
        }

    def _get_stats(self, **kwargs) -> dict[str, Any]:
        """Get memory statistics.

        Returns:
            Statistics
        """
        cursor = self._db.cursor()

        total = cursor.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        by_type = {}
        for row in cursor.execute(
            "SELECT memory_type, COUNT(*) as count FROM memories GROUP BY memory_type"
        ):
            by_type[row[0]] = row[1]

        avg_importance = (
            cursor.execute("SELECT AVG(importance) FROM memories").fetchone()[0] or 0.0
        )
        with_embeddings = cursor.execute(
            "SELECT COUNT(*) FROM memories WHERE has_embedding = 1"
        ).fetchone()[0]

        total_convs = cursor.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
        total_turns = cursor.execute(
            "SELECT COUNT(*) FROM conversation_turns"
        ).fetchone()[0]

        return {
            "total_memories": total,
            "by_type": by_type,
            "avg_importance": round(avg_importance, 3),
            "with_embeddings": with_embeddings,
            "total_conversations": total_convs,
            "total_turns": total_turns,
        }

    async def _prune_memories(
        self,
        max_keep: int | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Prune low-importance memories.

        Args:
            max_keep: Maximum memories to keep (uses config default if None)

        Returns:
            Prune result
        """
        max_keep = max_keep or self.config.max_memories
        cursor = self._db.cursor()

        # Count total
        total = cursor.execute("SELECT COUNT(*) FROM memories").fetchone()[0]

        if total <= max_keep:
            return {
                "pruned": 0,
                "remaining": total,
            }

        # Delete lowest importance, least accessed memories
        to_delete = total - max_keep

        deleted_ids = []
        rows = cursor.execute(
            """
            SELECT id FROM memories
            ORDER BY importance ASC, access_count ASC, timestamp ASC
            LIMIT ?
        """,
            (to_delete,),
        ).fetchall()

        for row in rows:
            deleted_ids.append(row[0])

        cursor.execute(
            f"""
            DELETE FROM memories
            WHERE id IN ({','.join('?' * len(deleted_ids))})
        """,
            deleted_ids,
        )

        self._db.commit()

        return {
            "pruned": len(deleted_ids),
            "remaining": total - len(deleted_ids),
        }

    # Convenience methods
    async def store(
        self,
        content: str,
        memory_type: str,
        **kwargs,
    ) -> CapabilityResult:
        """Store a memory."""
        return await self.execute(
            action="store",
            content=content,
            memory_type=memory_type,
            **kwargs,
        )

    async def search(self, query: str, **kwargs) -> CapabilityResult:
        """Search memories."""
        return await self.execute(action="search", query=query, **kwargs)

    async def recall(self, memory_id: str) -> CapabilityResult:
        """Recall a specific memory."""
        return await self.execute(action="recall", memory_id=memory_id)

    async def add_conversation_turn(
        self,
        conversation_id: str,
        role: str,
        content: str,
        **kwargs,
    ) -> CapabilityResult:
        """Add a conversation turn."""
        return await self.execute(
            action="add_turn",
            conversation_id=conversation_id,
            role=role,
            content=content,
            **kwargs,
        )

    async def get_stats(self) -> CapabilityResult:
        """Get statistics."""
        return await self.execute(action="stats")
