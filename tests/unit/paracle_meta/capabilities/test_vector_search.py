"""Unit tests for VectorSearchCapability."""

import pytest
import numpy as np
import tempfile
from pathlib import Path

from paracle_meta.capabilities.vector_search import (
    VectorSearchCapability,
    VectorSearchConfig,
    IndexType,
    DistanceMetric,
    QuantizationType,
)


@pytest.fixture
def temp_db():
    """Create temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def vector_search(temp_db):
    """Create VectorSearchCapability instance."""
    config = VectorSearchConfig(
        db_path=temp_db,
        dimension=128,
        index_type=IndexType.HNSW,
        distance_metric=DistanceMetric.COSINE,
    )
    return VectorSearchCapability(config)


@pytest.mark.asyncio
async def test_vector_search_initialization(vector_search):
    """Test VectorSearchCapability initialization."""
    assert vector_search.name == "vector_search"
    assert vector_search.config.dimension == 128
    assert vector_search.config.index_type == IndexType.HNSW


@pytest.mark.asyncio
async def test_add_vector(vector_search):
    """Test adding a vector to the index."""
    vector = np.random.rand(128).astype(np.float32)

    result = await vector_search.add(
        id="doc1",
        vector=vector,
        content="Test document",
        metadata={"type": "test"},
        namespace="default",
    )

    assert result.success is True
    assert result.output["id"] == "doc1"
    assert result.output["dimension"] == 128


@pytest.mark.asyncio
async def test_search_vectors(vector_search):
    """Test searching for similar vectors."""
    # Add some vectors
    vectors = [np.random.rand(128).astype(np.float32) for _ in range(5)]

    for i, vec in enumerate(vectors):
        await vector_search.add(
            id=f"doc{i}",
            vector=vec,
            content=f"Document {i}",
            metadata={"index": i},
            namespace="default",
        )

    # Search
    query_vector = vectors[0]  # Should find doc0 as most similar
    result = await vector_search.search(
        query_vector=query_vector, top_k=3, namespace="default"
    )

    assert result.success is True
    assert len(result.output["results"]) <= 3
    # First result should be doc0 (exact match)
    assert result.output["results"][0]["id"] == "doc0"
    assert result.output["results"][0]["distance"] < 0.01  # Very close to 0


@pytest.mark.asyncio
async def test_search_with_filter(vector_search):
    """Test searching with metadata filter."""
    # Add vectors with different metadata
    for i in range(5):
        vector = np.random.rand(128).astype(np.float32)
        await vector_search.add(
            id=f"doc{i}",
            vector=vector,
            content=f"Document {i}",
            metadata={"category": "A" if i < 3 else "B"},
            namespace="default",
        )

    # Search with filter
    query_vector = np.random.rand(128).astype(np.float32)
    result = await vector_search.search(
        query_vector=query_vector,
        top_k=10,
        namespace="default",
        filter={"category": "A"},
    )

    assert result.success is True
    # Should only return category A documents
    for item in result.output["results"]:
        assert item["metadata"]["category"] == "A"


@pytest.mark.asyncio
async def test_namespace_isolation(vector_search):
    """Test namespace isolation."""
    vector = np.random.rand(128).astype(np.float32)

    # Add to namespace1
    await vector_search.add(
        id="doc1",
        vector=vector,
        content="Document 1",
        metadata={},
        namespace="namespace1",
    )

    # Search in namespace2 (should find nothing)
    result = await vector_search.search(
        query_vector=vector, top_k=10, namespace="namespace2"
    )

    assert result.success is True
    assert len(result.output["results"]) == 0


@pytest.mark.asyncio
async def test_delete_vector(vector_search):
    """Test deleting a vector."""
    vector = np.random.rand(128).astype(np.float32)

    # Add vector
    await vector_search.add(
        id="doc1", vector=vector, content="Document 1", metadata={}, namespace="default"
    )

    # Delete vector
    result = await vector_search.delete(id="doc1", namespace="default")
    assert result.success is True

    # Search should not find it
    search_result = await vector_search.search(
        query_vector=vector, top_k=10, namespace="default"
    )
    assert len(search_result.output["results"]) == 0


@pytest.mark.asyncio
async def test_get_stats(vector_search):
    """Test getting index statistics."""
    # Add some vectors
    for i in range(5):
        vector = np.random.rand(128).astype(np.float32)
        await vector_search.add(
            id=f"doc{i}",
            vector=vector,
            content=f"Document {i}",
            metadata={},
            namespace="default",
        )

    result = await vector_search.get_stats(namespace="default")

    assert result.success is True
    assert result.output["count"] == 5
    assert result.output["dimension"] == 128
    assert result.output["namespace"] == "default"


@pytest.mark.asyncio
async def test_quantization():
    """Test vector quantization."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        config = VectorSearchConfig(
            db_path=db_path,
            dimension=128,
            quantization=QuantizationType.SCALAR,
        )
        capability = VectorSearchCapability(config)

        vector = np.random.rand(128).astype(np.float32)
        result = await capability.add(
            id="doc1", vector=vector, content="Test", metadata={}, namespace="default"
        )

        assert result.success is True
        # Quantized vectors should be stored

    finally:
        Path(db_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_invalid_dimension(vector_search):
    """Test adding vector with wrong dimension."""
    vector = np.random.rand(64).astype(np.float32)  # Wrong dimension

    result = await vector_search.add(
        id="doc1", vector=vector, content="Test", metadata={}, namespace="default"
    )

    assert result.success is False
    assert "dimension" in result.error.lower()


@pytest.mark.asyncio
async def test_persistence(temp_db):
    """Test index persistence across instances."""
    vector = np.random.rand(128).astype(np.float32)

    # First instance - add vector
    config1 = VectorSearchConfig(db_path=temp_db, dimension=128)
    cap1 = VectorSearchCapability(config1)

    await cap1.add(
        id="doc1", vector=vector, content="Test", metadata={}, namespace="default"
    )

    # Second instance - should load existing index
    config2 = VectorSearchConfig(db_path=temp_db, dimension=128)
    cap2 = VectorSearchCapability(config2)

    result = await cap2.search(query_vector=vector, top_k=1, namespace="default")

    assert result.success is True
    assert len(result.output["results"]) == 1
    assert result.output["results"][0]["id"] == "doc1"
