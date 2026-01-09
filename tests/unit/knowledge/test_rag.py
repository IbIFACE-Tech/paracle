"""Tests for RAG engine."""

import pytest

from paracle_knowledge.base import Chunk, ChunkMetadata, KnowledgeBase
from paracle_knowledge.rag import RAGConfig, RAGContext, RAGEngine, RAGResponse


class MockVectorStore:
    """Mock vector store for testing."""

    def __init__(self) -> None:
        self._collections: dict[str, list] = {}

    async def create_collection(self, name: str, **kwargs) -> None:
        self._collections[name] = []

    async def collection_exists(self, name: str) -> bool:
        return name in self._collections

    async def add_documents(self, collection: str, docs: list) -> list[str]:
        if collection not in self._collections:
            self._collections[collection] = []
        self._collections[collection].extend(docs)
        return [d.id for d in docs]

    async def search(self, collection: str, query_embedding: list[float], **kwargs):
        from paracle_vector.base import Document, SearchResult

        # Return mock results
        top_k = kwargs.get("top_k", 10)
        results = []

        for i, doc in enumerate(self._collections.get(collection, [])[:top_k]):
            results.append(
                SearchResult(
                    document=Document(
                        id=doc.id,
                        content=doc.content,
                        embedding=doc.embedding,
                        metadata=doc.metadata,
                    ),
                    score=0.9 - (i * 0.1),
                )
            )

        return results

    async def close(self) -> None:
        self._collections.clear()


class MockEmbeddingService:
    """Mock embedding service for testing."""

    def __init__(self, dimension: int = 384) -> None:
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * self._dimension for _ in texts]

    async def embed_single(self, text: str) -> list[float]:
        return [0.1] * self._dimension


class TestRAGEngine:
    """Tests for RAGEngine."""

    @pytest.fixture
    def knowledge_base(self) -> KnowledgeBase:
        """Create a knowledge base with mock dependencies."""
        store = MockVectorStore()
        embedding = MockEmbeddingService()
        return KnowledgeBase(store, embedding)

    @pytest.fixture
    def rag_engine(self, knowledge_base: KnowledgeBase) -> RAGEngine:
        """Create RAG engine."""
        return RAGEngine(knowledge_base)

    @pytest.mark.asyncio
    async def test_query_empty_kb(self, rag_engine: RAGEngine) -> None:
        """Test querying empty knowledge base."""
        response = await rag_engine.query("What is Python?")

        assert isinstance(response, RAGResponse)
        assert response.query == "What is Python?"
        assert response.context == ""
        assert response.sources == []

    @pytest.mark.asyncio
    async def test_query_with_context(self, rag_engine: RAGEngine) -> None:
        """Test querying with context filters."""
        context = RAGContext(
            filters={"language": "python"},
            retrieval_top_k=5,
        )

        response = await rag_engine.query("How to define a function?", context)

        assert isinstance(response, RAGResponse)
        assert response.retrieval_time_ms >= 0

    @pytest.mark.asyncio
    async def test_multi_query(self, rag_engine: RAGEngine) -> None:
        """Test multiple queries."""
        questions = ["What is Python?", "What is JavaScript?"]
        responses = await rag_engine.multi_query(questions)

        assert len(responses) == 2
        assert all(isinstance(r, RAGResponse) for r in responses)


class TestRAGConfig:
    """Tests for RAGConfig."""

    def test_default_config(self) -> None:
        """Test default configuration."""
        config = RAGConfig()

        assert config.retrieval_top_k == 20
        assert config.final_top_k == 5
        assert config.min_relevance_score == 0.3
        assert config.include_sources is True

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = RAGConfig(
            retrieval_top_k=10,
            final_top_k=3,
            enable_reranking=False,
        )

        assert config.retrieval_top_k == 10
        assert config.final_top_k == 3
        assert config.enable_reranking is False


class TestRAGContext:
    """Tests for RAGContext."""

    def test_default_context(self) -> None:
        """Test default context."""
        context = RAGContext()

        assert context.filters is None
        assert context.namespace is None

    def test_context_with_filters(self) -> None:
        """Test context with filters."""
        context = RAGContext(
            filters={"language": "python", "type": "function"},
        )

        assert context.filters["language"] == "python"


class TestRAGResponse:
    """Tests for RAGResponse."""

    def test_response_format(self) -> None:
        """Test response formatting."""
        response = RAGResponse(
            context="Some context",
            query="What is Python?",
            confidence=0.85,
        )

        assert response.context == "Some context"
        assert response.query == "What is Python?"
        assert response.confidence == 0.85

    def test_format_with_sources(self) -> None:
        """Test formatting context with sources."""
        from paracle_knowledge.base import Source

        response = RAGResponse(
            context="Test context",
            query="test",
            sources=[
                Source(
                    document_id="doc1",
                    document_name="test.py",
                    file_path="test.py",
                    content="def hello(): pass",
                    line_start=1,
                    score=0.9,
                ),
            ],
        )

        formatted = response.format_context_with_sources()
        assert "[1]" in formatted
        assert "test.py" in formatted
