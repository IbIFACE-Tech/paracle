"""Memory/Context Capability for MetaAgent.

Provides persistent memory and context management:
- Short-term memory (session-based)
- Long-term memory (persistent storage)
- Semantic memory with embeddings
- Context windowing for conversations
- Knowledge base integration

Example:
    >>> cap = MemoryCapability()
    >>> await cap.initialize()
    >>>
    >>> # Store information
    >>> await cap.store("user_preference", {"theme": "dark"})
    >>>
    >>> # Retrieve
    >>> result = await cap.retrieve("user_preference")
    >>>
    >>> # Semantic search
    >>> result = await cap.search("What are the user's preferences?")
"""

import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import Field

from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)


class MemoryConfig(CapabilityConfig):
    """Configuration for Memory capability."""

    storage_path: str | None = Field(
        default=None,
        description="Path for persistent storage (defaults to .parac/memory)",
    )
    max_short_term_items: int = Field(
        default=100, ge=10, le=10000, description="Maximum short-term memory items"
    )
    max_context_tokens: int = Field(
        default=100000, ge=1000, description="Maximum tokens in context window"
    )
    enable_persistence: bool = Field(
        default=True, description="Enable persistent storage"
    )
    enable_embeddings: bool = Field(
        default=False,
        description="Enable semantic embeddings (requires embedding model)",
    )
    ttl_hours: int = Field(
        default=24 * 7,  # 1 week
        ge=1,
        description="Default TTL for memory items in hours",
    )
    namespace: str = Field(
        default="default", description="Memory namespace for isolation"
    )


class MemoryItem:
    """A single memory item."""

    def __init__(
        self,
        key: str,
        value: Any,
        metadata: dict[str, Any] | None = None,
        ttl_hours: int | None = None,
    ):
        self.key = key
        self.value = value
        self.metadata = metadata or {}
        self.created_at = datetime.now(timezone.utc)
        self.accessed_at = self.created_at
        self.access_count = 0
        self.ttl_hours = ttl_hours

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key": self.key,
            "value": self.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "accessed_at": self.accessed_at.isoformat(),
            "access_count": self.access_count,
            "ttl_hours": self.ttl_hours,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryItem":
        """Create from dictionary."""
        item = cls(
            key=data["key"],
            value=data["value"],
            metadata=data.get("metadata", {}),
            ttl_hours=data.get("ttl_hours"),
        )
        item.created_at = datetime.fromisoformat(data["created_at"])
        item.accessed_at = datetime.fromisoformat(data["accessed_at"])
        item.access_count = data.get("access_count", 0)
        return item

    def is_expired(self) -> bool:
        """Check if item has expired."""
        if self.ttl_hours is None:
            return False
        age_hours = (
            datetime.now(timezone.utc) - self.created_at
        ).total_seconds() / 3600
        return age_hours > self.ttl_hours


class MemoryCapability(BaseCapability):
    """Memory and context management capability.

    Provides:
    - Key-value storage (short-term and long-term)
    - Conversation context management
    - Semantic search (when embeddings enabled)
    - Knowledge base integration
    - Memory consolidation and cleanup

    Example:
        >>> cap = MemoryCapability()
        >>> await cap.initialize()
        >>>
        >>> # Store and retrieve
        >>> await cap.store("api_key", "sk-...")
        >>> result = await cap.retrieve("api_key")
        >>>
        >>> # Context management
        >>> await cap.add_context("user", "I prefer Python")
        >>> context = await cap.get_context(max_tokens=4000)
    """

    name = "memory"
    description = "Persistent memory and context management"

    def __init__(self, config: MemoryConfig | None = None):
        """Initialize Memory capability."""
        super().__init__(config or MemoryConfig())
        self.config: MemoryConfig = self.config

        # Short-term memory (in-process)
        self._short_term: dict[str, MemoryItem] = {}

        # Context history
        self._context: list[dict[str, Any]] = []

        # Database connection for persistence
        self._db_path: Path | None = None
        self._conn: sqlite3.Connection | None = None

    async def initialize(self) -> None:
        """Initialize memory storage."""
        await super().initialize()

        if self.config.enable_persistence:
            # Set up storage path
            if self.config.storage_path:
                self._db_path = Path(self.config.storage_path)
            else:
                self._db_path = Path.cwd() / ".parac" / "memory" / "memory.db"

            self._db_path.parent.mkdir(parents=True, exist_ok=True)

            # Initialize database
            self._conn = sqlite3.connect(str(self._db_path))
            self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        cursor = self._conn.cursor()

        # Memory items table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                namespace TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL,
                accessed_at TEXT NOT NULL,
                access_count INTEGER DEFAULT 0,
                ttl_hours INTEGER,
                embedding BLOB,
                UNIQUE(namespace, key)
            )
        """
        )

        # Context history table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS context_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                namespace TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL,
                token_count INTEGER DEFAULT 0
            )
        """
        )

        # Create indexes
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_memory_namespace_key
            ON memory_items(namespace, key)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_context_namespace
            ON context_history(namespace, created_at)
        """
        )

        self._conn.commit()

    async def shutdown(self) -> None:
        """Cleanup and close connections."""
        if self._conn:
            self._conn.close()
            self._conn = None
        await super().shutdown()

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute memory operation.

        Actions:
            - store: Store a value
            - retrieve: Retrieve a value
            - delete: Delete a value
            - list_keys: List all keys
            - search: Search memory (text or semantic)
            - add_context: Add to context history
            - get_context: Get context window
            - clear_context: Clear context history
            - consolidate: Consolidate and cleanup memory
            - export: Export memory to file
            - import: Import memory from file
        """
        action = kwargs.get("action", "retrieve")
        start_time = time.time()

        try:
            if action == "store":
                result = await self._store(
                    key=kwargs.get("key", ""),
                    value=kwargs.get("value"),
                    metadata=kwargs.get("metadata"),
                    ttl_hours=kwargs.get("ttl_hours"),
                )
            elif action == "retrieve":
                result = await self._retrieve(kwargs.get("key", ""))
            elif action == "delete":
                result = await self._delete(kwargs.get("key", ""))
            elif action == "list_keys":
                result = await self._list_keys(
                    pattern=kwargs.get("pattern"),
                )
            elif action == "search":
                result = await self._search(
                    query=kwargs.get("query", ""),
                    limit=kwargs.get("limit", 10),
                )
            elif action == "add_context":
                result = await self._add_context(
                    role=kwargs.get("role", "user"),
                    content=kwargs.get("content", ""),
                    metadata=kwargs.get("metadata"),
                )
            elif action == "get_context":
                result = await self._get_context(
                    max_tokens=kwargs.get("max_tokens", self.config.max_context_tokens),
                    include_system=kwargs.get("include_system", True),
                )
            elif action == "clear_context":
                result = await self._clear_context()
            elif action == "consolidate":
                result = await self._consolidate()
            elif action == "export":
                result = await self._export(kwargs.get("path", "memory_export.json"))
            elif action == "import":
                result = await self._import(kwargs.get("path", ""))
            elif action == "stats":
                result = await self._get_stats()
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

    async def _store(
        self,
        key: str,
        value: Any,
        metadata: dict[str, Any] | None = None,
        ttl_hours: int | None = None,
    ) -> dict[str, Any]:
        """Store a value in memory."""
        if not key:
            raise ValueError("Key is required")

        # Create memory item
        item = MemoryItem(
            key=key,
            value=value,
            metadata=metadata,
            ttl_hours=ttl_hours or self.config.ttl_hours,
        )

        # Store in short-term memory
        self._short_term[key] = item

        # Enforce limit
        if len(self._short_term) > self.config.max_short_term_items:
            # Remove oldest accessed items
            sorted_items = sorted(
                self._short_term.items(), key=lambda x: x[1].accessed_at
            )
            for k, _ in sorted_items[
                : len(self._short_term) - self.config.max_short_term_items
            ]:
                del self._short_term[k]

        # Persist if enabled
        if self.config.enable_persistence and self._conn:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO memory_items
                (namespace, key, value, metadata, created_at, accessed_at, access_count, ttl_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    self.config.namespace,
                    key,
                    json.dumps(value),
                    json.dumps(metadata) if metadata else None,
                    item.created_at.isoformat(),
                    item.accessed_at.isoformat(),
                    item.access_count,
                    item.ttl_hours,
                ),
            )
            self._conn.commit()

        return {
            "key": key,
            "stored": True,
            "ttl_hours": item.ttl_hours,
        }

    async def _retrieve(self, key: str) -> dict[str, Any]:
        """Retrieve a value from memory."""
        if not key:
            raise ValueError("Key is required")

        # Check short-term first
        if key in self._short_term:
            item = self._short_term[key]
            if item.is_expired():
                del self._short_term[key]
            else:
                item.accessed_at = datetime.now(timezone.utc)
                item.access_count += 1
                return {
                    "key": key,
                    "value": item.value,
                    "metadata": item.metadata,
                    "source": "short_term",
                    "access_count": item.access_count,
                }

        # Check persistent storage
        if self.config.enable_persistence and self._conn:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                SELECT value, metadata, created_at, accessed_at, access_count, ttl_hours
                FROM memory_items
                WHERE namespace = ? AND key = ?
            """,
                (self.config.namespace, key),
            )

            row = cursor.fetchone()
            if row:
                (
                    value,
                    metadata_str,
                    created_at,
                    accessed_at,
                    access_count,
                    ttl_hours,
                ) = row

                # Check expiration
                created = datetime.fromisoformat(created_at)
                if ttl_hours:
                    age_hours = (
                        datetime.now(timezone.utc) - created
                    ).total_seconds() / 3600
                    if age_hours > ttl_hours:
                        # Delete expired item
                        cursor.execute(
                            """
                            DELETE FROM memory_items
                            WHERE namespace = ? AND key = ?
                        """,
                            (self.config.namespace, key),
                        )
                        self._conn.commit()
                        return {"key": key, "value": None, "found": False}

                # Update access info
                cursor.execute(
                    """
                    UPDATE memory_items
                    SET accessed_at = ?, access_count = access_count + 1
                    WHERE namespace = ? AND key = ?
                """,
                    (
                        datetime.now(timezone.utc).isoformat(),
                        self.config.namespace,
                        key,
                    ),
                )
                self._conn.commit()

                return {
                    "key": key,
                    "value": json.loads(value),
                    "metadata": json.loads(metadata_str) if metadata_str else None,
                    "source": "persistent",
                    "access_count": access_count + 1,
                }

        return {"key": key, "value": None, "found": False}

    async def _delete(self, key: str) -> dict[str, Any]:
        """Delete a value from memory."""
        deleted_from = []

        # Delete from short-term
        if key in self._short_term:
            del self._short_term[key]
            deleted_from.append("short_term")

        # Delete from persistent
        if self.config.enable_persistence and self._conn:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                DELETE FROM memory_items
                WHERE namespace = ? AND key = ?
            """,
                (self.config.namespace, key),
            )
            if cursor.rowcount > 0:
                deleted_from.append("persistent")
            self._conn.commit()

        return {
            "key": key,
            "deleted": bool(deleted_from),
            "deleted_from": deleted_from,
        }

    async def _list_keys(
        self,
        pattern: str | None = None,
    ) -> dict[str, Any]:
        """List all keys in memory."""
        keys = set()

        # Short-term keys
        for key in self._short_term:
            if pattern is None or pattern in key:
                keys.add(key)

        # Persistent keys
        if self.config.enable_persistence and self._conn:
            cursor = self._conn.cursor()
            if pattern:
                cursor.execute(
                    """
                    SELECT key FROM memory_items
                    WHERE namespace = ? AND key LIKE ?
                """,
                    (self.config.namespace, f"%{pattern}%"),
                )
            else:
                cursor.execute(
                    """
                    SELECT key FROM memory_items
                    WHERE namespace = ?
                """,
                    (self.config.namespace,),
                )

            for row in cursor.fetchall():
                keys.add(row[0])

        return {
            "keys": sorted(keys),
            "count": len(keys),
            "pattern": pattern,
        }

    async def _search(
        self,
        query: str,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Search memory for matching items."""
        results = []
        query_lower = query.lower()

        # Search short-term
        for key, item in self._short_term.items():
            if item.is_expired():
                continue
            score = self._calculate_relevance(query_lower, key, item.value)
            if score > 0:
                results.append(
                    {
                        "key": key,
                        "value": item.value,
                        "score": score,
                        "source": "short_term",
                    }
                )

        # Search persistent
        if self.config.enable_persistence and self._conn:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                SELECT key, value, metadata FROM memory_items
                WHERE namespace = ?
            """,
                (self.config.namespace,),
            )

            for row in cursor.fetchall():
                key, value_str, _ = row
                if key in [r["key"] for r in results]:
                    continue
                value = json.loads(value_str)
                score = self._calculate_relevance(query_lower, key, value)
                if score > 0:
                    results.append(
                        {
                            "key": key,
                            "value": value,
                            "score": score,
                            "source": "persistent",
                        }
                    )

        # Sort by relevance and limit
        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:limit]

        return {
            "query": query,
            "results": results,
            "count": len(results),
        }

    def _calculate_relevance(
        self,
        query: str,
        key: str,
        value: Any,
    ) -> float:
        """Calculate relevance score for search."""
        score = 0.0

        # Key match
        if query in key.lower():
            score += 2.0
        elif any(word in key.lower() for word in query.split()):
            score += 1.0

        # Value match
        value_str = (
            json.dumps(value).lower() if not isinstance(value, str) else value.lower()
        )
        if query in value_str:
            score += 1.5
        elif any(word in value_str for word in query.split()):
            score += 0.5

        return score

    async def _add_context(
        self,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Add to context history."""
        # Estimate token count (rough approximation)
        token_count = len(content.split()) * 1.3

        context_item = {
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "token_count": int(token_count),
        }

        self._context.append(context_item)

        # Persist if enabled
        if self.config.enable_persistence and self._conn:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                INSERT INTO context_history
                (namespace, role, content, metadata, created_at, token_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    self.config.namespace,
                    role,
                    content,
                    json.dumps(metadata) if metadata else None,
                    context_item["created_at"],
                    context_item["token_count"],
                ),
            )
            self._conn.commit()

        return {
            "added": True,
            "role": role,
            "token_count": context_item["token_count"],
            "total_items": len(self._context),
        }

    async def _get_context(
        self,
        max_tokens: int = 100000,
        include_system: bool = True,
    ) -> dict[str, Any]:
        """Get context window within token limit."""
        messages = []
        total_tokens = 0

        # Get from memory first (most recent)
        for item in reversed(self._context):
            if not include_system and item["role"] == "system":
                continue
            if total_tokens + item["token_count"] > max_tokens:
                break
            messages.insert(
                0,
                {
                    "role": item["role"],
                    "content": item["content"],
                },
            )
            total_tokens += item["token_count"]

        return {
            "messages": messages,
            "total_tokens": total_tokens,
            "message_count": len(messages),
            "truncated": len(messages) < len(self._context),
        }

    async def _clear_context(self) -> dict[str, Any]:
        """Clear context history."""
        count = len(self._context)
        self._context.clear()

        if self.config.enable_persistence and self._conn:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                DELETE FROM context_history
                WHERE namespace = ?
            """,
                (self.config.namespace,),
            )
            self._conn.commit()

        return {"cleared": True, "items_removed": count}

    async def _consolidate(self) -> dict[str, Any]:
        """Consolidate and cleanup memory."""
        expired_count = 0
        consolidated_count = 0

        # Remove expired items from short-term
        expired_keys = [
            key for key, item in self._short_term.items() if item.is_expired()
        ]
        for key in expired_keys:
            del self._short_term[key]
            expired_count += 1

        # Remove expired from persistent
        if self.config.enable_persistence and self._conn:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                DELETE FROM memory_items
                WHERE namespace = ? AND ttl_hours IS NOT NULL
                AND datetime(created_at, '+' || ttl_hours || ' hours') < datetime('now')
            """,
                (self.config.namespace,),
            )
            expired_count += cursor.rowcount
            self._conn.commit()

        return {
            "expired_removed": expired_count,
            "consolidated": consolidated_count,
        }

    async def _export(self, path: str) -> dict[str, Any]:
        """Export memory to file."""
        export_data = {
            "namespace": self.config.namespace,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "items": [],
            "context": self._context,
        }

        # Export short-term
        for key, item in self._short_term.items():
            export_data["items"].append(item.to_dict())

        # Export persistent
        if self.config.enable_persistence and self._conn:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                SELECT key, value, metadata, created_at, accessed_at, access_count, ttl_hours
                FROM memory_items
                WHERE namespace = ?
            """,
                (self.config.namespace,),
            )

            for row in cursor.fetchall():
                (
                    key,
                    value,
                    metadata,
                    created_at,
                    accessed_at,
                    access_count,
                    ttl_hours,
                ) = row
                if key not in self._short_term:
                    export_data["items"].append(
                        {
                            "key": key,
                            "value": json.loads(value),
                            "metadata": json.loads(metadata) if metadata else {},
                            "created_at": created_at,
                            "accessed_at": accessed_at,
                            "access_count": access_count,
                            "ttl_hours": ttl_hours,
                        }
                    )

        # Write to file
        export_path = Path(path)
        export_path.write_text(json.dumps(export_data, indent=2))

        return {
            "path": str(export_path),
            "items_exported": len(export_data["items"]),
            "context_exported": len(export_data["context"]),
        }

    async def _import(self, path: str) -> dict[str, Any]:
        """Import memory from file."""
        import_path = Path(path)
        if not import_path.exists():
            raise FileNotFoundError(f"Import file not found: {path}")

        data = json.loads(import_path.read_text())
        imported_count = 0

        for item_data in data.get("items", []):
            await self._store(
                key=item_data["key"],
                value=item_data["value"],
                metadata=item_data.get("metadata"),
                ttl_hours=item_data.get("ttl_hours"),
            )
            imported_count += 1

        return {
            "path": str(import_path),
            "items_imported": imported_count,
        }

    async def _get_stats(self) -> dict[str, Any]:
        """Get memory statistics."""
        stats = {
            "short_term_items": len(self._short_term),
            "context_items": len(self._context),
            "namespace": self.config.namespace,
        }

        if self.config.enable_persistence and self._conn:
            cursor = self._conn.cursor()

            cursor.execute(
                """
                SELECT COUNT(*) FROM memory_items WHERE namespace = ?
            """,
                (self.config.namespace,),
            )
            stats["persistent_items"] = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT COUNT(*) FROM context_history WHERE namespace = ?
            """,
                (self.config.namespace,),
            )
            stats["persistent_context"] = cursor.fetchone()[0]

        return stats

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    async def store(
        self,
        key: str,
        value: Any,
        **kwargs,
    ) -> CapabilityResult:
        """Store a value."""
        return await self.execute(action="store", key=key, value=value, **kwargs)

    async def retrieve(self, key: str) -> CapabilityResult:
        """Retrieve a value."""
        return await self.execute(action="retrieve", key=key)

    async def search(self, query: str, limit: int = 10) -> CapabilityResult:
        """Search memory."""
        return await self.execute(action="search", query=query, limit=limit)

    async def add_context(
        self,
        role: str,
        content: str,
        **kwargs,
    ) -> CapabilityResult:
        """Add to context history."""
        return await self.execute(
            action="add_context", role=role, content=content, **kwargs
        )

    async def get_context(self, max_tokens: int = 100000) -> CapabilityResult:
        """Get context window."""
        return await self.execute(action="get_context", max_tokens=max_tokens)
