"""Base types for the Knowledge Engine.

This module defines core data structures for documents, chunks, and the knowledge base.
"""

from __future__ import annotations

import hashlib
import logging
from enum import Enum
from typing import TYPE_CHECKING, Any

from paracle_core.compat import UTC, datetime
from paracle_core.ids import generate_ulid
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from paracle_vector import VectorStore
    from paracle_vector.embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class KnowledgeError(Exception):
    """Base exception for knowledge engine errors."""

    pass


class DocumentType(str, Enum):
    """Types of documents that can be ingested."""

    MARKDOWN = "markdown"
    CODE = "code"
    TEXT = "text"
    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    YAML = "yaml"


class ChunkMetadata(BaseModel):
    """Metadata for a document chunk.

    Attributes:
        document_id: ID of the source document
        chunk_index: Index of this chunk within the document
        start_line: Starting line number in source
        end_line: Ending line number in source
        start_char: Starting character offset
        end_char: Ending character offset
        language: Programming language (for code)
        section: Section heading (for markdown)
        tags: Additional tags
        custom: Custom metadata
    """

    document_id: str
    chunk_index: int = 0
    start_line: int | None = None
    end_line: int | None = None
    start_char: int | None = None
    end_char: int | None = None
    language: str | None = None
    section: str | None = None
    tags: list[str] = Field(default_factory=list)
    custom: dict[str, Any] = Field(default_factory=dict)


class Chunk(BaseModel):
    """A chunk of text from a document.

    Attributes:
        id: Unique chunk identifier
        content: Text content of the chunk
        embedding: Vector embedding (computed on demand)
        metadata: Chunk metadata
        created_at: Creation timestamp
    """

    id: str = Field(default_factory=generate_ulid)
    content: str
    embedding: list[float] | None = None
    metadata: ChunkMetadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def content_hash(self) -> str:
        """Get hash of content for deduplication."""
        return hashlib.sha256(self.content.encode()).hexdigest()[:16]

    def __repr__(self) -> str:
        return f"<Chunk(id={self.id!r}, len={len(self.content)})>"


class Document(BaseModel):
    """A document in the knowledge base.

    Attributes:
        id: Unique document identifier
        name: Document name/title
        file_path: Original file path (if from file)
        content: Full document content
        doc_type: Type of document
        chunks: Chunked content
        metadata: Document metadata
        content_hash: Hash of content for change detection
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: str = Field(default_factory=generate_ulid)
    name: str
    file_path: str | None = None
    content: str
    doc_type: DocumentType = DocumentType.TEXT
    chunks: list[Chunk] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    content_hash: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def compute_hash(self) -> str:
        """Compute content hash."""
        return hashlib.sha256(self.content.encode()).hexdigest()

    def model_post_init(self, __context: Any) -> None:
        """Compute hash after initialization."""
        if self.content_hash is None:
            self.content_hash = self.compute_hash()

    def __repr__(self) -> str:
        return (
            f"<Document(id={self.id!r}, name={self.name!r}, chunks={len(self.chunks)})>"
        )


class Source(BaseModel):
    """A source reference for citations.

    Attributes:
        document_id: ID of the source document
        document_name: Name of the source document
        file_path: File path (if available)
        chunk_id: ID of the specific chunk
        content: Relevant content excerpt
        line_start: Starting line number
        line_end: Ending line number
        score: Relevance score
    """

    document_id: str
    document_name: str
    file_path: str | None = None
    chunk_id: str | None = None
    content: str
    line_start: int | None = None
    line_end: int | None = None
    score: float = 0.0

    def to_citation(self) -> str:
        """Format as citation string."""
        if self.file_path and self.line_start:
            return f"{self.file_path}:{self.line_start}"
        elif self.file_path:
            return self.file_path
        else:
            return self.document_name


class KnowledgeBase:
    """Central knowledge base manager.

    Manages documents, chunks, and vector storage for the knowledge engine.

    Usage:
        kb = KnowledgeBase(
            vector_store=ChromaStore(persist_dir=".paracle/knowledge"),
            embedding_service=EmbeddingService()
        )

        # Add document
        doc = Document(name="readme", content="...")
        await kb.add_document(doc)

        # Search
        results = await kb.search("how to install?", top_k=5)
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        collection_name: str = "knowledge",
    ):
        """Initialize knowledge base.

        Args:
            vector_store: Vector store for embeddings
            embedding_service: Service for generating embeddings
            collection_name: Name of the vector collection
        """
        self._vector_store = vector_store
        self._embedding_service = embedding_service
        self._collection_name = collection_name
        self._documents: dict[str, Document] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the knowledge base (create collection if needed)."""
        if self._initialized:
            return

        if not await self._vector_store.collection_exists(self._collection_name):
            await self._vector_store.create_collection(
                self._collection_name,
                dimension=self._embedding_service.dimension,
            )

        self._initialized = True
        logger.info("Knowledge base initialized: %s", self._collection_name)

    async def add_document(self, document: Document) -> str:
        """Add a document to the knowledge base.

        Args:
            document: Document to add

        Returns:
            Document ID
        """
        await self.initialize()

        # Store document reference
        self._documents[document.id] = document

        # Generate embeddings for chunks
        if document.chunks:
            chunks_without_embeddings = [
                c for c in document.chunks if c.embedding is None
            ]
            if chunks_without_embeddings:
                contents = [c.content for c in chunks_without_embeddings]
                embeddings = await self._embedding_service.embed(contents)
                for chunk, embedding in zip(
                    chunks_without_embeddings, embeddings, strict=False
                ):
                    chunk.embedding = embedding

            # Convert to vector store documents
            from paracle_vector.base import Document as VectorDocument

            vector_docs = [
                VectorDocument(
                    id=chunk.id,
                    content=chunk.content,
                    embedding=chunk.embedding,
                    metadata={
                        "document_id": document.id,
                        "document_name": document.name,
                        "file_path": document.file_path or "",
                        "chunk_index": chunk.metadata.chunk_index,
                        "start_line": chunk.metadata.start_line or 0,
                        "end_line": chunk.metadata.end_line or 0,
                        "language": chunk.metadata.language or "",
                        "section": chunk.metadata.section or "",
                    },
                )
                for chunk in document.chunks
                if chunk.embedding is not None
            ]

            if vector_docs:
                await self._vector_store.add_documents(
                    self._collection_name, vector_docs
                )

        logger.debug(
            "Added document %s with %d chunks", document.id, len(document.chunks)
        )
        return document.id

    async def remove_document(self, document_id: str) -> bool:
        """Remove a document from the knowledge base.

        Args:
            document_id: ID of document to remove

        Returns:
            True if removed
        """
        await self.initialize()

        document = self._documents.pop(document_id, None)
        if document is None:
            return False

        # Remove chunks from vector store
        for chunk in document.chunks:
            await self._vector_store.delete_document(self._collection_name, chunk.id)

        logger.debug("Removed document %s", document_id)
        return True

    async def search(
        self,
        query: str,
        *,
        top_k: int = 10,
        filter_metadata: dict[str, Any] | None = None,
        min_score: float = 0.0,
    ) -> list[tuple[Chunk, float]]:
        """Search for relevant chunks.

        Args:
            query: Search query
            top_k: Number of results
            filter_metadata: Optional metadata filter
            min_score: Minimum similarity score

        Returns:
            List of (chunk, score) tuples
        """
        await self.initialize()

        # Generate query embedding
        query_embedding = await self._embedding_service.embed_single(query)

        # Search vector store
        results = await self._vector_store.search(
            self._collection_name,
            query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata,
        )

        # Convert to chunks with scores
        chunk_results = []
        for result in results:
            if result.score < min_score:
                continue

            # Reconstruct chunk from result
            metadata = ChunkMetadata(
                document_id=result.document.metadata.get("document_id", ""),
                chunk_index=result.document.metadata.get("chunk_index", 0),
                start_line=result.document.metadata.get("start_line"),
                end_line=result.document.metadata.get("end_line"),
                language=result.document.metadata.get("language"),
                section=result.document.metadata.get("section"),
            )

            chunk = Chunk(
                id=result.document.id,
                content=result.document.content,
                embedding=result.document.embedding,
                metadata=metadata,
            )

            chunk_results.append((chunk, result.score))

        return chunk_results

    async def get_document(self, document_id: str) -> Document | None:
        """Get a document by ID.

        Args:
            document_id: Document ID

        Returns:
            Document if found
        """
        return self._documents.get(document_id)

    async def list_documents(self) -> list[Document]:
        """List all documents.

        Returns:
            List of documents
        """
        return list(self._documents.values())

    async def get_stats(self) -> dict[str, Any]:
        """Get knowledge base statistics.

        Returns:
            Statistics dictionary
        """
        await self.initialize()

        total_chunks = sum(len(d.chunks) for d in self._documents.values())
        total_chars = sum(len(d.content) for d in self._documents.values())

        return {
            "collection": self._collection_name,
            "documents": len(self._documents),
            "chunks": total_chunks,
            "total_characters": total_chars,
            "embedding_dimension": self._embedding_service.dimension,
        }

    async def close(self) -> None:
        """Close the knowledge base."""
        await self._vector_store.close()
        self._documents.clear()
        self._initialized = False
