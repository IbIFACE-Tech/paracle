"""Tests for vector store base types."""

from datetime import datetime

from paracle_vector.base import (
    CollectionNotFoundError,
    Document,
    SearchResult,
    VectorStoreError,
)


class TestDocument:
    """Tests for Document model."""

    def test_create_document(self) -> None:
        """Test creating a document."""
        doc = Document(
            id="doc1",
            content="Hello world",
        )

        assert doc.id == "doc1"
        assert doc.content == "Hello world"
        assert doc.embedding is None
        assert doc.metadata == {}
        assert isinstance(doc.created_at, datetime)

    def test_document_with_embedding(self) -> None:
        """Test document with embedding."""
        embedding = [0.1, 0.2, 0.3]
        doc = Document(
            id="doc1",
            content="Test",
            embedding=embedding,
        )

        assert doc.embedding == embedding

    def test_document_with_metadata(self) -> None:
        """Test document with metadata."""
        doc = Document(
            id="doc1",
            content="Test",
            metadata={"source": "test", "page": 1},
        )

        assert doc.metadata["source"] == "test"
        assert doc.metadata["page"] == 1

    def test_document_repr(self) -> None:
        """Test document string representation."""
        doc = Document(id="doc1", content="Short content here")
        repr_str = repr(doc)

        assert "doc1" in repr_str
        assert "Document" in repr_str


class TestSearchResult:
    """Tests for SearchResult model."""

    def test_create_search_result(self) -> None:
        """Test creating a search result."""
        doc = Document(id="doc1", content="Test")
        result = SearchResult(document=doc, score=0.95)

        assert result.document == doc
        assert result.score == 0.95
        assert result.distance is None

    def test_search_result_with_distance(self) -> None:
        """Test search result with distance."""
        doc = Document(id="doc1", content="Test")
        result = SearchResult(document=doc, score=0.95, distance=0.05)

        assert result.distance == 0.05

    def test_search_result_repr(self) -> None:
        """Test search result string representation."""
        doc = Document(id="doc1", content="Test")
        result = SearchResult(document=doc, score=0.9567)
        repr_str = repr(result)

        assert "doc1" in repr_str
        assert "0.9567" in repr_str


class TestExceptions:
    """Tests for exception classes."""

    def test_vector_store_error(self) -> None:
        """Test VectorStoreError."""
        error = VectorStoreError("Something went wrong")
        assert str(error) == "Something went wrong"

    def test_collection_not_found_error(self) -> None:
        """Test CollectionNotFoundError."""
        error = CollectionNotFoundError("my_collection")

        assert "my_collection" in str(error)
        assert error.collection == "my_collection"
