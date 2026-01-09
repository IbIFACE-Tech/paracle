"""ChromaDB vector store implementation.

ChromaDB is an open-source embedding database designed for
AI applications with local and persistent storage options.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from paracle_vector.base import (
    CollectionNotFoundError,
    Document,
    SearchResult,
    VectorStore,
    VectorStoreError,
)

logger = logging.getLogger(__name__)


class ChromaStore(VectorStore):
    """ChromaDB vector store implementation.

    Supports both in-memory and persistent storage modes.

    Usage:
        # In-memory (testing)
        store = ChromaStore()

        # Persistent (production)
        store = ChromaStore(persist_dir=".paracle/vectors")

        # Create collection and add documents
        await store.create_collection("knowledge")
        await store.add_documents("knowledge", documents)

        # Search
        results = await store.search("knowledge", query_embedding, top_k=5)
    """

    def __init__(
        self,
        persist_dir: str | Path | None = None,
        *,
        tenant: str = "default_tenant",
        database: str = "default_database",
    ):
        """Initialize ChromaDB store.

        Args:
            persist_dir: Directory for persistent storage (None for in-memory)
            tenant: ChromaDB tenant name
            database: ChromaDB database name
        """
        self._persist_dir = Path(persist_dir) if persist_dir else None
        self._tenant = tenant
        self._database = database
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazy initialization of ChromaDB client."""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings
            except ImportError as e:
                raise ImportError(
                    "ChromaDB package not installed. "
                    "Install with: pip install chromadb"
                ) from e

            if self._persist_dir:
                self._persist_dir.mkdir(parents=True, exist_ok=True)
                settings = Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=str(self._persist_dir),
                    anonymized_telemetry=False,
                )
                self._client = chromadb.Client(settings)
            else:
                self._client = chromadb.Client()

            logger.info(
                "ChromaDB client initialized (persist=%s)",
                self._persist_dir is not None,
            )

        return self._client

    async def create_collection(
        self,
        name: str,
        *,
        dimension: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Create a new collection."""
        client = self._get_client()

        collection_metadata = metadata or {}
        if dimension:
            collection_metadata["dimension"] = dimension

        try:
            client.create_collection(
                name=name,
                metadata=collection_metadata if collection_metadata else None,
            )
            logger.info("Created collection: %s", name)
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.debug("Collection already exists: %s", name)
            else:
                raise VectorStoreError(f"Failed to create collection: {e}") from e

    async def delete_collection(self, name: str) -> None:
        """Delete a collection and all its documents."""
        client = self._get_client()

        try:
            client.delete_collection(name=name)
            logger.info("Deleted collection: %s", name)
        except Exception as e:
            if "does not exist" in str(e).lower():
                raise CollectionNotFoundError(name) from e
            raise VectorStoreError(f"Failed to delete collection: {e}") from e

    async def list_collections(self) -> list[str]:
        """List all collection names."""
        client = self._get_client()
        collections = client.list_collections()
        return [c.name for c in collections]

    async def collection_exists(self, name: str) -> bool:
        """Check if a collection exists."""
        collections = await self.list_collections()
        return name in collections

    async def add_documents(
        self,
        collection: str,
        documents: list[Document],
    ) -> list[str]:
        """Add documents to a collection."""
        client = self._get_client()

        try:
            coll = client.get_collection(name=collection)
        except Exception as e:
            if "does not exist" in str(e).lower():
                raise CollectionNotFoundError(collection) from e
            raise VectorStoreError(f"Failed to get collection: {e}") from e

        ids = []
        contents = []
        embeddings = []
        metadatas = []

        for doc in documents:
            if doc.embedding is None:
                raise VectorStoreError(
                    f"Document {doc.id} has no embedding. "
                    "Use EmbeddingService to generate embeddings first."
                )
            ids.append(doc.id)
            contents.append(doc.content)
            embeddings.append(doc.embedding)
            # ChromaDB requires metadata values to be str, int, float, or bool
            clean_metadata = self._clean_metadata(doc.metadata)
            metadatas.append(clean_metadata)

        try:
            coll.add(
                ids=ids,
                documents=contents,
                embeddings=embeddings,
                metadatas=metadatas if any(metadatas) else None,
            )
            logger.debug("Added %d documents to collection %s", len(ids), collection)
        except Exception as e:
            raise VectorStoreError(f"Failed to add documents: {e}") from e

        return ids

    async def get_document(
        self,
        collection: str,
        document_id: str,
    ) -> Document | None:
        """Get a document by ID."""
        client = self._get_client()

        try:
            coll = client.get_collection(name=collection)
        except Exception as e:
            if "does not exist" in str(e).lower():
                raise CollectionNotFoundError(collection) from e
            raise VectorStoreError(f"Failed to get collection: {e}") from e

        try:
            result = coll.get(
                ids=[document_id],
                include=["documents", "embeddings", "metadatas"],
            )
        except Exception as e:
            raise VectorStoreError(f"Failed to get document: {e}") from e

        if not result["ids"]:
            return None

        return Document(
            id=result["ids"][0],
            content=result["documents"][0] if result["documents"] else "",
            embedding=result["embeddings"][0] if result["embeddings"] else None,
            metadata=result["metadatas"][0] if result["metadatas"] else {},
        )

    async def delete_document(
        self,
        collection: str,
        document_id: str,
    ) -> bool:
        """Delete a document by ID."""
        client = self._get_client()

        try:
            coll = client.get_collection(name=collection)
        except Exception as e:
            if "does not exist" in str(e).lower():
                raise CollectionNotFoundError(collection) from e
            raise VectorStoreError(f"Failed to get collection: {e}") from e

        # Check if document exists
        existing = await self.get_document(collection, document_id)
        if existing is None:
            return False

        try:
            coll.delete(ids=[document_id])
            logger.debug(
                "Deleted document %s from collection %s", document_id, collection
            )
            return True
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
        """Search for similar documents."""
        client = self._get_client()

        try:
            coll = client.get_collection(name=collection)
        except Exception as e:
            if "does not exist" in str(e).lower():
                raise CollectionNotFoundError(collection) from e
            raise VectorStoreError(f"Failed to get collection: {e}") from e

        # Build where clause from filter
        where = None
        if filter_metadata:
            where = self._build_where_clause(filter_metadata)

        try:
            result = coll.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
                include=["documents", "embeddings", "metadatas", "distances"],
            )
        except Exception as e:
            raise VectorStoreError(f"Failed to search: {e}") from e

        # Convert results
        results = []
        if result["ids"] and result["ids"][0]:
            for i, doc_id in enumerate(result["ids"][0]):
                distance = result["distances"][0][i] if result["distances"] else 0.0
                # Convert distance to similarity score (assuming L2 distance)
                score = 1.0 / (1.0 + distance)

                doc = Document(
                    id=doc_id,
                    content=result["documents"][0][i] if result["documents"] else "",
                    embedding=(
                        result["embeddings"][0][i] if result["embeddings"] else None
                    ),
                    metadata=result["metadatas"][0][i] if result["metadatas"] else {},
                )
                results.append(
                    SearchResult(document=doc, score=score, distance=distance)
                )

        return results

    async def count_documents(self, collection: str) -> int:
        """Count documents in a collection."""
        client = self._get_client()

        try:
            coll = client.get_collection(name=collection)
            return coll.count()
        except Exception as e:
            if "does not exist" in str(e).lower():
                raise CollectionNotFoundError(collection) from e
            raise VectorStoreError(f"Failed to count documents: {e}") from e

    async def close(self) -> None:
        """Close the connection to ChromaDB."""
        if self._client is not None and self._persist_dir:
            # Persist data before closing
            try:
                self._client.persist()
            except Exception:
                pass  # Newer versions auto-persist
        self._client = None
        logger.info("ChromaDB client closed")

    @staticmethod
    def _clean_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
        """Clean metadata for ChromaDB compatibility.

        ChromaDB only accepts str, int, float, or bool values.
        """
        cleaned = {}
        for key, value in metadata.items():
            if isinstance(value, str | int | float | bool):
                cleaned[key] = value
            elif value is None:
                continue  # Skip None values
            else:
                # Convert other types to string
                cleaned[key] = str(value)
        return cleaned

    @staticmethod
    def _build_where_clause(filter_metadata: dict[str, Any]) -> dict[str, Any]:
        """Build ChromaDB where clause from filter metadata."""
        if len(filter_metadata) == 1:
            key, value = next(iter(filter_metadata.items()))
            return {key: {"$eq": value}}

        # Multiple conditions with AND
        return {
            "$and": [{key: {"$eq": value}} for key, value in filter_metadata.items()]
        }
