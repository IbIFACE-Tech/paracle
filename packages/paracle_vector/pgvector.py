"""PostgreSQL pgvector implementation.

pgvector is a PostgreSQL extension for vector similarity search,
providing unified relational and vector storage in production.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from paracle_vector.base import (
    CollectionNotFoundError,
    ConnectionError,
    Document,
    SearchResult,
    VectorStore,
    VectorStoreError,
)

logger = logging.getLogger(__name__)


class PgVectorStore(VectorStore):
    """PostgreSQL pgvector implementation.

    Provides vector storage using PostgreSQL with the pgvector extension.
    Best for production use with unified relational and vector data.

    Prerequisites:
        - PostgreSQL with pgvector extension installed
        - CREATE EXTENSION IF NOT EXISTS vector;

    Usage:
        store = PgVectorStore("postgresql://user:pass@localhost/db")
        await store.create_collection("knowledge", dimension=1536)
        await store.add_documents("knowledge", documents)
        results = await store.search("knowledge", query_embedding)
    """

    def __init__(
        self,
        connection_url: str,
        *,
        pool_size: int = 5,
        schema: str = "public",
    ):
        """Initialize pgvector store.

        Args:
            connection_url: PostgreSQL connection URL
            pool_size: Connection pool size
            schema: Database schema to use
        """
        self._connection_url = connection_url
        self._pool_size = pool_size
        self._schema = schema
        self._engine: Any = None
        self._async_engine: Any = None

    async def _get_engine(self) -> Any:
        """Get or create async database engine."""
        if self._async_engine is None:
            try:
                from sqlalchemy.ext.asyncio import create_async_engine
            except ImportError as e:
                raise ImportError(
                    "SQLAlchemy with async support not installed. "
                    "Install with: pip install sqlalchemy[asyncio] asyncpg"
                ) from e

            # Convert URL to async format
            async_url = self._connection_url.replace(
                "postgresql://", "postgresql+asyncpg://"
            )

            try:
                self._async_engine = create_async_engine(
                    async_url,
                    pool_size=self._pool_size,
                    echo=False,
                )
                # Test connection and ensure pgvector extension
                async with self._async_engine.begin() as conn:
                    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                logger.info("pgvector engine initialized")
            except Exception as e:
                raise ConnectionError(f"Failed to connect to PostgreSQL: {e}") from e

        return self._async_engine

    def _table_name(self, collection: str) -> str:
        """Get fully qualified table name for collection."""
        # Sanitize collection name for SQL
        safe_name = "".join(c if c.isalnum() or c == "_" else "_" for c in collection)
        return f"{self._schema}.vec_{safe_name}"

    async def create_collection(
        self,
        name: str,
        *,
        dimension: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Create a new collection (table)."""
        if dimension is None:
            dimension = 1536  # Default to OpenAI dimension

        engine = await self._get_engine()
        table_name = self._table_name(name)

        sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id VARCHAR(255) PRIMARY KEY,
                content TEXT NOT NULL,
                embedding vector({dimension}),
                metadata JSONB DEFAULT '{{}}',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """

        try:
            async with engine.begin() as conn:
                await conn.execute(sql)
                # Create index for vector similarity search
                index_name = f"idx_{name.replace('-', '_')}_embedding"
                await conn.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS {index_name}
                    ON {table_name}
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100)
                """
                )

            # Store collection metadata
            if metadata:
                await self._store_collection_metadata(name, dimension, metadata)

            logger.info("Created pgvector collection: %s (dim=%d)", name, dimension)
        except Exception as e:
            raise VectorStoreError(f"Failed to create collection: {e}") from e

    async def delete_collection(self, name: str) -> None:
        """Delete a collection (table)."""
        engine = await self._get_engine()
        table_name = self._table_name(name)

        try:
            async with engine.begin() as conn:
                await conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            logger.info("Deleted pgvector collection: %s", name)
        except Exception as e:
            raise VectorStoreError(f"Failed to delete collection: {e}") from e

    async def list_collections(self) -> list[str]:
        """List all collection names."""
        engine = await self._get_engine()

        sql = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = :schema
            AND table_name LIKE 'vec_%'
        """

        try:
            async with engine.begin() as conn:
                result = await conn.execute(sql, {"schema": self._schema})
                rows = result.fetchall()
                return [row[0].replace("vec_", "") for row in rows]
        except Exception as e:
            raise VectorStoreError(f"Failed to list collections: {e}") from e

    async def collection_exists(self, name: str) -> bool:
        """Check if a collection exists."""
        collections = await self.list_collections()
        # Normalize name for comparison
        safe_name = "".join(c if c.isalnum() or c == "_" else "_" for c in name)
        return safe_name in collections

    async def add_documents(
        self,
        collection: str,
        documents: list[Document],
    ) -> list[str]:
        """Add documents to a collection."""
        if not await self.collection_exists(collection):
            raise CollectionNotFoundError(collection)

        engine = await self._get_engine()
        table_name = self._table_name(collection)

        sql = f"""
            INSERT INTO {table_name} (id, content, embedding, metadata, created_at)
            VALUES (:id, :content, :embedding, :metadata, :created_at)
            ON CONFLICT (id) DO UPDATE SET
                content = EXCLUDED.content,
                embedding = EXCLUDED.embedding,
                metadata = EXCLUDED.metadata
        """

        ids = []
        try:
            async with engine.begin() as conn:
                for doc in documents:
                    if doc.embedding is None:
                        raise VectorStoreError(f"Document {doc.id} has no embedding")
                    await conn.execute(
                        sql,
                        {
                            "id": doc.id,
                            "content": doc.content,
                            "embedding": str(doc.embedding),  # pgvector format
                            "metadata": json.dumps(doc.metadata),
                            "created_at": doc.created_at,
                        },
                    )
                    ids.append(doc.id)

            logger.debug("Added %d documents to %s", len(ids), collection)
        except Exception as e:
            raise VectorStoreError(f"Failed to add documents: {e}") from e

        return ids

    async def get_document(
        self,
        collection: str,
        document_id: str,
    ) -> Document | None:
        """Get a document by ID."""
        if not await self.collection_exists(collection):
            raise CollectionNotFoundError(collection)

        engine = await self._get_engine()
        table_name = self._table_name(collection)

        sql = f"""
            SELECT id, content, embedding::text, metadata, created_at
            FROM {table_name}
            WHERE id = :id
        """

        try:
            async with engine.begin() as conn:
                result = await conn.execute(sql, {"id": document_id})
                row = result.fetchone()

                if row is None:
                    return None

                embedding = self._parse_vector(row[2]) if row[2] else None
                metadata = (
                    row[3] if isinstance(row[3], dict) else json.loads(row[3] or "{}")
                )

                return Document(
                    id=row[0],
                    content=row[1],
                    embedding=embedding,
                    metadata=metadata,
                    created_at=row[4],
                )
        except Exception as e:
            raise VectorStoreError(f"Failed to get document: {e}") from e

    async def delete_document(
        self,
        collection: str,
        document_id: str,
    ) -> bool:
        """Delete a document by ID."""
        if not await self.collection_exists(collection):
            raise CollectionNotFoundError(collection)

        engine = await self._get_engine()
        table_name = self._table_name(collection)

        sql = f"DELETE FROM {table_name} WHERE id = :id"

        try:
            async with engine.begin() as conn:
                result = await conn.execute(sql, {"id": document_id})
                deleted = result.rowcount > 0

            if deleted:
                logger.debug("Deleted document %s from %s", document_id, collection)
            return deleted
        except Exception as e:
            raise VectorStoreError(f"Failed to delete document: {e}") from e

    async def search(
        self,
        collection: str,
        query_embedding: list[float],
        *,
        top_k: int = 10,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for similar documents using cosine similarity."""
        if not await self.collection_exists(collection):
            raise CollectionNotFoundError(collection)

        engine = await self._get_engine()
        table_name = self._table_name(collection)

        # Build filter clause
        where_clause = ""
        params: dict[str, Any] = {
            "query": str(query_embedding),
            "limit": top_k,
        }

        if filter_metadata:
            conditions = []
            for i, (key, value) in enumerate(filter_metadata.items()):
                param_name = f"filter_{i}"
                conditions.append(f"metadata->>'{key}' = :{param_name}")
                params[param_name] = str(value)
            where_clause = "WHERE " + " AND ".join(conditions)

        # Use cosine distance (1 - similarity)
        sql = f"""
            SELECT id, content, embedding::text, metadata, created_at,
                   1 - (embedding <=> :query::vector) as score,
                   embedding <=> :query::vector as distance
            FROM {table_name}
            {where_clause}
            ORDER BY distance
            LIMIT :limit
        """

        try:
            async with engine.begin() as conn:
                result = await conn.execute(sql, params)
                rows = result.fetchall()

                results = []
                for row in rows:
                    embedding = self._parse_vector(row[2]) if row[2] else None
                    metadata = (
                        row[3]
                        if isinstance(row[3], dict)
                        else json.loads(row[3] or "{}")
                    )

                    doc = Document(
                        id=row[0],
                        content=row[1],
                        embedding=embedding,
                        metadata=metadata,
                        created_at=row[4],
                    )
                    results.append(
                        SearchResult(
                            document=doc,
                            score=float(row[5]),
                            distance=float(row[6]),
                        )
                    )

                return results
        except Exception as e:
            raise VectorStoreError(f"Failed to search: {e}") from e

    async def count_documents(self, collection: str) -> int:
        """Count documents in a collection."""
        if not await self.collection_exists(collection):
            raise CollectionNotFoundError(collection)

        engine = await self._get_engine()
        table_name = self._table_name(collection)

        sql = f"SELECT COUNT(*) FROM {table_name}"

        try:
            async with engine.begin() as conn:
                result = await conn.execute(sql)
                row = result.fetchone()
                return row[0] if row else 0
        except Exception as e:
            raise VectorStoreError(f"Failed to count documents: {e}") from e

    async def close(self) -> None:
        """Close database connections."""
        if self._async_engine is not None:
            await self._async_engine.dispose()
            self._async_engine = None
            logger.info("pgvector engine closed")

    async def _store_collection_metadata(
        self,
        name: str,
        dimension: int,
        metadata: dict[str, Any],
    ) -> None:
        """Store collection metadata in a dedicated table."""
        engine = await self._get_engine()

        # Create metadata table if not exists
        await engine.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self._schema}.vec_collections (
                name VARCHAR(255) PRIMARY KEY,
                dimension INTEGER NOT NULL,
                metadata JSONB DEFAULT '{{}}',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """
        )

        await engine.execute(
            f"""
            INSERT INTO {self._schema}.vec_collections (name, dimension, metadata)
            VALUES (:name, :dimension, :metadata)
            ON CONFLICT (name) DO UPDATE SET
                dimension = EXCLUDED.dimension,
                metadata = EXCLUDED.metadata
            """,
            {
                "name": name,
                "dimension": dimension,
                "metadata": json.dumps(metadata),
            },
        )

    @staticmethod
    def _parse_vector(vector_str: str) -> list[float]:
        """Parse pgvector string representation to list."""
        # pgvector format: [1.0,2.0,3.0]
        clean = vector_str.strip("[]")
        return [float(x) for x in clean.split(",")]
