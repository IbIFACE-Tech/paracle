"""Tests for embedding service."""

import pytest
from paracle_vector.embeddings import (
    EmbeddingConfig,
    EmbeddingProvider,
    EmbeddingService,
    MockEmbeddingProvider,
)


class TestMockEmbeddingProvider:
    """Tests for MockEmbeddingProvider."""

    @pytest.mark.asyncio
    async def test_embed_returns_correct_dimension(self) -> None:
        """Test that embeddings have correct dimension."""
        provider = MockEmbeddingProvider(dimension=384)
        embeddings = await provider.embed(["hello", "world"])

        assert len(embeddings) == 2
        assert len(embeddings[0]) == 384
        assert len(embeddings[1]) == 384

    @pytest.mark.asyncio
    async def test_embed_is_deterministic(self) -> None:
        """Test that same text produces same embedding."""
        provider = MockEmbeddingProvider()
        emb1 = await provider.embed(["test"])
        emb2 = await provider.embed(["test"])

        assert emb1[0] == emb2[0]

    @pytest.mark.asyncio
    async def test_different_texts_produce_different_embeddings(self) -> None:
        """Test that different texts produce different embeddings."""
        provider = MockEmbeddingProvider()
        embeddings = await provider.embed(["hello", "goodbye"])

        assert embeddings[0] != embeddings[1]

    def test_dimension_property(self) -> None:
        """Test dimension property."""
        provider = MockEmbeddingProvider(dimension=768)
        assert provider.dimension == 768


class TestEmbeddingService:
    """Tests for EmbeddingService."""

    @pytest.mark.asyncio
    async def test_embed_with_mock_provider(self) -> None:
        """Test embedding with mock provider."""
        service = EmbeddingService(provider=EmbeddingProvider.MOCK)
        embeddings = await service.embed(["test text"])

        assert len(embeddings) == 1
        assert len(embeddings[0]) == 1536  # Default dimension

    @pytest.mark.asyncio
    async def test_embed_single(self) -> None:
        """Test single text embedding."""
        service = EmbeddingService(provider=EmbeddingProvider.MOCK)
        embedding = await service.embed_single("test")

        assert len(embedding) == 1536

    @pytest.mark.asyncio
    async def test_batch_embedding(self) -> None:
        """Test batched embedding for large inputs."""
        config = EmbeddingConfig(
            provider=EmbeddingProvider.MOCK,
            batch_size=2,
        )
        service = EmbeddingService(config=config)

        texts = ["text1", "text2", "text3", "text4", "text5"]
        embeddings = await service.embed(texts)

        assert len(embeddings) == 5

    def test_dimension_property(self) -> None:
        """Test dimension property."""
        service = EmbeddingService(provider=EmbeddingProvider.MOCK)
        assert service.dimension == 1536

    @pytest.mark.asyncio
    async def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = EmbeddingConfig(
            provider=EmbeddingProvider.MOCK,
            dimension=384,
        )
        service = EmbeddingService(config=config)

        embedding = await service.embed_single("test")
        assert len(embedding) == 384
