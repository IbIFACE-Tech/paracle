"""Paracle Vector - Vector Database Integration.

This package provides vector database support for embeddings and RAG:
- ChromaDB integration for local/persistent vector storage
- pgvector support for PostgreSQL with vector extensions
- Embedding generation and management
- Semantic search capabilities

Usage:
    # ChromaDB (local development)
    from paracle_vector import ChromaStore, EmbeddingService

    store = ChromaStore(persist_dir=".paracle/vectors")
    embeddings = EmbeddingService()

    # Index documents
    store.add_documents(
        collection="agent_knowledge",
        documents=["doc1", "doc2"],
        embeddings=embeddings.embed(["doc1", "doc2"]),
        ids=["id1", "id2"]
    )

    # Semantic search
    results = store.search(
        collection="agent_knowledge",
        query_embedding=embeddings.embed(["query"])[0],
        top_k=5
    )

    # pgvector (production)
    from paracle_vector import PgVectorStore

    store = PgVectorStore(connection_url="postgresql://...")
"""

from paracle_vector.base import Document, SearchResult, VectorStore, VectorStoreError
from paracle_vector.chroma import ChromaStore
from paracle_vector.embeddings import EmbeddingProvider, EmbeddingService
from paracle_vector.pgvector import PgVectorStore

__version__ = "1.0.1"

__all__ = [
    # Base types
    "VectorStore",
    "VectorStoreError",
    "Document",
    "SearchResult",
    # Implementations
    "ChromaStore",
    "PgVectorStore",
    # Embeddings
    "EmbeddingService",
    "EmbeddingProvider",
]
