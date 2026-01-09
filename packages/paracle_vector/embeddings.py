"""Embedding generation service.

This module provides embedding generation for text documents
using various providers (OpenAI, local models, etc.).
"""

from __future__ import annotations

import hashlib
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class EmbeddingProvider(str, Enum):
    """Available embedding providers."""

    OPENAI = "openai"
    LOCAL = "local"
    MOCK = "mock"


class EmbeddingConfig(BaseModel):
    """Configuration for embedding service.

    Attributes:
        provider: Embedding provider to use
        model: Model name (provider-specific)
        dimension: Expected embedding dimension
        batch_size: Maximum batch size for embedding requests
        api_key: Optional API key (can be from env)
    """

    provider: EmbeddingProvider = EmbeddingProvider.MOCK
    model: str = "text-embedding-3-small"
    dimension: int = 1536
    batch_size: int = 100
    api_key: str | None = None


class EmbeddingProviderBase(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    async def embed(
        self,
        texts: list[str],
        **kwargs: Any,
    ) -> list[list[float]]:
        """Generate embeddings for texts.

        Args:
            texts: List of texts to embed
            **kwargs: Provider-specific options

        Returns:
            List of embedding vectors
        """
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Get embedding dimension."""
        pass


class MockEmbeddingProvider(EmbeddingProviderBase):
    """Mock embedding provider for testing.

    Generates deterministic embeddings based on text hash.
    """

    def __init__(self, dimension: int = 1536):
        self._dimension = dimension

    async def embed(
        self,
        texts: list[str],
        **kwargs: Any,
    ) -> list[list[float]]:
        """Generate mock embeddings from text hash."""
        embeddings = []
        for text in texts:
            # Create deterministic embedding from hash
            hash_bytes = hashlib.sha256(text.encode()).digest()
            # Expand hash to fill dimension
            embedding = []
            for i in range(self._dimension):
                byte_idx = i % len(hash_bytes)
                # Normalize to [-1, 1] range
                value = (hash_bytes[byte_idx] / 255.0) * 2 - 1
                embedding.append(value)
            embeddings.append(embedding)
        return embeddings

    @property
    def dimension(self) -> int:
        return self._dimension


class OpenAIEmbeddingProvider(EmbeddingProviderBase):
    """OpenAI embedding provider.

    Uses OpenAI's text-embedding models.
    Requires OPENAI_API_KEY environment variable or explicit key.
    """

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: str | None = None,
        dimension: int = 1536,
    ):
        self._model = model
        self._api_key = api_key
        self._dimension = dimension
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError as e:
                raise ImportError(
                    "OpenAI package not installed. " "Install with: pip install openai"
                ) from e

            self._client = AsyncOpenAI(api_key=self._api_key)
        return self._client

    async def embed(
        self,
        texts: list[str],
        **kwargs: Any,
    ) -> list[list[float]]:
        """Generate embeddings using OpenAI API."""
        client = self._get_client()

        response = await client.embeddings.create(
            model=self._model,
            input=texts,
            **kwargs,
        )

        return [item.embedding for item in response.data]

    @property
    def dimension(self) -> int:
        return self._dimension


class LocalEmbeddingProvider(EmbeddingProviderBase):
    """Local embedding provider using sentence-transformers.

    Runs embeddings locally without API calls.
    Requires sentence-transformers package.
    """

    def __init__(
        self,
        model: str = "all-MiniLM-L6-v2",
    ):
        self._model_name = model
        self._model: Any = None
        self._dimension: int | None = None

    def _get_model(self) -> Any:
        """Lazy initialization of sentence-transformers model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as e:
                raise ImportError(
                    "sentence-transformers package not installed. "
                    "Install with: pip install sentence-transformers"
                ) from e

            self._model = SentenceTransformer(self._model_name)
            self._dimension = self._model.get_sentence_embedding_dimension()
        return self._model

    async def embed(
        self,
        texts: list[str],
        **kwargs: Any,
    ) -> list[list[float]]:
        """Generate embeddings using local model."""
        model = self._get_model()
        embeddings = model.encode(texts, **kwargs)
        return [emb.tolist() for emb in embeddings]

    @property
    def dimension(self) -> int:
        if self._dimension is None:
            self._get_model()
        return self._dimension or 384


class EmbeddingService:
    """High-level embedding service.

    Provides a unified interface for generating embeddings
    with automatic batching and caching.

    Usage:
        service = EmbeddingService(provider=EmbeddingProvider.OPENAI)
        embeddings = await service.embed(["hello", "world"])
    """

    def __init__(
        self,
        config: EmbeddingConfig | None = None,
        provider: EmbeddingProvider | None = None,
    ):
        """Initialize embedding service.

        Args:
            config: Full configuration
            provider: Shortcut to set provider (uses defaults for other settings)
        """
        if config is not None:
            self._config = config
        elif provider is not None:
            self._config = EmbeddingConfig(provider=provider)
        else:
            self._config = EmbeddingConfig()

        self._provider: EmbeddingProviderBase | None = None

    def _get_provider(self) -> EmbeddingProviderBase:
        """Get or create the embedding provider."""
        if self._provider is None:
            if self._config.provider == EmbeddingProvider.OPENAI:
                self._provider = OpenAIEmbeddingProvider(
                    model=self._config.model,
                    api_key=self._config.api_key,
                    dimension=self._config.dimension,
                )
            elif self._config.provider == EmbeddingProvider.LOCAL:
                self._provider = LocalEmbeddingProvider(
                    model=self._config.model,
                )
            else:
                self._provider = MockEmbeddingProvider(
                    dimension=self._config.dimension,
                )
        return self._provider

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self._get_provider().dimension

    async def embed(
        self,
        texts: list[str],
        **kwargs: Any,
    ) -> list[list[float]]:
        """Generate embeddings for texts.

        Automatically batches large requests.

        Args:
            texts: List of texts to embed
            **kwargs: Provider-specific options

        Returns:
            List of embedding vectors
        """
        provider = self._get_provider()

        # Handle batching
        if len(texts) <= self._config.batch_size:
            return await provider.embed(texts, **kwargs)

        # Batch large requests
        all_embeddings = []
        for i in range(0, len(texts), self._config.batch_size):
            batch = texts[i : i + self._config.batch_size]
            batch_embeddings = await provider.embed(batch, **kwargs)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    async def embed_single(
        self,
        text: str,
        **kwargs: Any,
    ) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed
            **kwargs: Provider-specific options

        Returns:
            Embedding vector
        """
        embeddings = await self.embed([text], **kwargs)
        return embeddings[0]
