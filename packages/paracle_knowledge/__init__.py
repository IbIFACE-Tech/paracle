"""Paracle Knowledge - Knowledge Engine with RAG.

This package provides the Knowledge Engine for Retrieval Augmented Generation:
- Document ingestion and chunking
- Vector store integration (ChromaDB, pgvector)
- RAG engine for context-aware queries
- Reranking for improved relevance
- Source attribution and citations

Usage:
    from paracle_knowledge import RAGEngine, DocumentIngestor, KnowledgeBase

    # Create knowledge base
    kb = KnowledgeBase(
        vector_store=ChromaStore(persist_dir=".paracle/knowledge"),
        embedding_service=EmbeddingService()
    )

    # Ingest documents
    ingestor = DocumentIngestor(knowledge_base=kb)
    await ingestor.ingest_directory("./docs", file_types=["md", "py"])

    # Create RAG engine
    rag = RAGEngine(knowledge_base=kb)

    # Query with context
    response = await rag.query(
        question="How does authentication work?",
        top_k=5
    )

    print(response.answer)
    for source in response.sources:
        print(f"  - {source.file_path}:{source.line_number}")
"""

from paracle_knowledge.base import (
    Chunk,
    ChunkMetadata,
    Document,
    KnowledgeBase,
    KnowledgeError,
    Source,
)
from paracle_knowledge.chunkers import (
    BaseChunker,
    CodeChunker,
    MarkdownChunker,
    SemanticChunker,
    TextChunker,
)
from paracle_knowledge.ingestion import DocumentIngestor, IngestResult
from paracle_knowledge.rag import RAGConfig, RAGContext, RAGEngine, RAGResponse
from paracle_knowledge.reranker import CrossEncoderReranker, Reranker

__version__ = "1.0.1"

__all__ = [
    # Base types
    "Document",
    "Chunk",
    "ChunkMetadata",
    "Source",
    "KnowledgeBase",
    "KnowledgeError",
    # Chunkers
    "BaseChunker",
    "TextChunker",
    "MarkdownChunker",
    "CodeChunker",
    "SemanticChunker",
    # Ingestion
    "DocumentIngestor",
    "IngestResult",
    # RAG
    "RAGEngine",
    "RAGConfig",
    "RAGContext",
    "RAGResponse",
    # Reranking
    "Reranker",
    "CrossEncoderReranker",
]
