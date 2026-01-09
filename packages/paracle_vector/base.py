"""Base types and interfaces for vector storage.

This module defines the abstract interface for vector stores
and common types used across implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from paracle_core.compat import UTC, datetime
from pydantic import BaseModel, Field


class VectorStoreError(Exception):
    """Base exception for vector store errors."""

    pass


class ConnectionError(VectorStoreError):
    """Raised when connection to vector store fails."""

    pass


class CollectionNotFoundError(VectorStoreError):
    """Raised when a collection doesn't exist."""

    def __init__(self, collection: str):
        super().__init__(f"Collection not found: {collection}")
        self.collection = collection


class Document(BaseModel):
    """A document with vector embedding.

    Attributes:
        id: Unique document identifier
        content: Text content of the document
        embedding: Vector embedding (optional, computed on demand)
        metadata: Additional document metadata
        created_at: Creation timestamp
    """

    id: str
    content: str
    embedding: list[float] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def __repr__(self) -> str:
        return f"<Document(id={self.id!r}, content={self.content[:50]!r}...)>"


class SearchResult(BaseModel):
    """A search result with relevance score.

    Attributes:
        document: The matched document
        score: Similarity score (higher is more similar)
        distance: Distance metric (lower is more similar)
    """

    document: Document
    score: float
    distance: float | None = None

    def __repr__(self) -> str:
        return f"<SearchResult(id={self.document.id!r}, score={self.score:.4f})>"


class VectorStore(ABC):
    """Abstract base class for vector stores.

    All vector store implementations must implement this interface.
    """

    @abstractmethod
    async def create_collection(
        self,
        name: str,
        *,
        dimension: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Create a new collection.

        Args:
            name: Collection name (must be unique)
            dimension: Vector dimension (optional, inferred from first insert)
            metadata: Collection metadata
        """
        pass

    @abstractmethod
    async def delete_collection(self, name: str) -> None:
        """Delete a collection and all its documents.

        Args:
            name: Collection name
        """
        pass

    @abstractmethod
    async def list_collections(self) -> list[str]:
        """List all collection names.

        Returns:
            List of collection names
        """
        pass

    @abstractmethod
    async def collection_exists(self, name: str) -> bool:
        """Check if a collection exists.

        Args:
            name: Collection name

        Returns:
            True if collection exists
        """
        pass

    @abstractmethod
    async def add_documents(
        self,
        collection: str,
        documents: list[Document],
    ) -> list[str]:
        """Add documents to a collection.

        Args:
            collection: Collection name
            documents: Documents to add (must have embeddings)

        Returns:
            List of document IDs added
        """
        pass

    @abstractmethod
    async def get_document(
        self,
        collection: str,
        document_id: str,
    ) -> Document | None:
        """Get a document by ID.

        Args:
            collection: Collection name
            document_id: Document ID

        Returns:
            Document if found, None otherwise
        """
        pass

    @abstractmethod
    async def delete_document(
        self,
        collection: str,
        document_id: str,
    ) -> bool:
        """Delete a document by ID.

        Args:
            collection: Collection name
            document_id: Document ID

        Returns:
            True if document was deleted
        """
        pass

    @abstractmethod
    async def search(
        self,
        collection: str,
        query_embedding: list[float],
        *,
        top_k: int = 10,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for similar documents.

        Args:
            collection: Collection name
            query_embedding: Query vector
            top_k: Number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            List of search results ordered by relevance
        """
        pass

    @abstractmethod
    async def count_documents(self, collection: str) -> int:
        """Count documents in a collection.

        Args:
            collection: Collection name

        Returns:
            Number of documents
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the connection to the vector store."""
        pass
