"""Embedding provider abstraction for paracle_meta.

Supports multiple embedding providers:
- OpenAI: text-embedding-3-small (1536 dims, $0.00002/1K tokens)
- Ollama: nomic-embed-text (768 dims, free/local)

Usage:
    from paracle_meta.embeddings import (
        get_embedding_provider,
        OpenAIEmbeddings,
        OllamaEmbeddings,
    )

    # Get provider based on config
    provider = get_embedding_provider("openai")
    embedding = await provider.embed("Hello world")

    # Or use specific provider
    openai = OpenAIEmbeddings()
    embeddings = await openai.embed_batch(["Hello", "World"])
"""

from __future__ import annotations

import asyncio
import os
from abc import ABC, abstractmethod

import httpx
from paracle_core.logging import get_logger
from pydantic import BaseModel, Field

logger = get_logger(__name__)


class EmbeddingError(Exception):
    """Base exception for embedding errors."""

    pass


class EmbeddingProviderError(EmbeddingError):
    """Raised when embedding provider fails."""

    pass


class EmbeddingConfig(BaseModel):
    """Configuration for embedding provider."""

    # OpenAI settings
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key (defaults to OPENAI_API_KEY env var)",
    )
    openai_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model",
    )
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API base URL",
    )

    # Ollama settings
    ollama_model: str = Field(
        default="nomic-embed-text",
        description="Ollama embedding model",
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL",
    )

    # Request settings
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_batch_size: int = Field(
        default=100, description="Maximum batch size for embedding"
    )
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    retry_delay: float = Field(
        default=1.0, description="Delay between retries in seconds"
    )


class EmbeddingProvider(ABC):
    """Abstract embedding provider interface."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        ...

    @property
    @abstractmethod
    def model(self) -> str:
        """Model identifier."""
        ...

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Embedding dimensions."""
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector as list of floats.

        Raises:
            EmbeddingProviderError: If embedding fails.
        """
        ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.

        Raises:
            EmbeddingProviderError: If embedding fails.
        """
        ...

    async def similarity(
        self, embedding1: list[float], embedding2: list[float]
    ) -> float:
        """Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector.
            embedding2: Second embedding vector.

        Returns:
            Cosine similarity score (0-1).
        """
        import math

        dot_product = sum(a * b for a, b in zip(embedding1, embedding2, strict=False))
        norm1 = math.sqrt(sum(a * a for a in embedding1))
        norm2 = math.sqrt(sum(b * b for b in embedding2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


class OpenAIEmbeddings(EmbeddingProvider):
    """OpenAI embedding provider.

    Uses text-embedding-3-small by default (1536 dimensions).
    Cost: ~$0.00002 per 1K tokens.

    Models:
    - text-embedding-3-small: 1536 dims, cheaper, good quality
    - text-embedding-3-large: 3072 dims, best quality
    - text-embedding-ada-002: 1536 dims, legacy
    """

    # Model dimensions mapping
    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "text-embedding-3-small",
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 30.0,
        max_batch_size: int = 100,
    ) -> None:
        """Initialize OpenAI embeddings.

        Args:
            api_key: OpenAI API key. Defaults to OPENAI_API_KEY env var.
            model: Embedding model to use.
            base_url: API base URL.
            timeout: Request timeout.
            max_batch_size: Maximum texts per batch request.
        """
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self._api_key:
            raise EmbeddingError("OpenAI API key not provided")

        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_batch_size = max_batch_size
        self._dimensions = self.MODEL_DIMENSIONS.get(model, 1536)

    @property
    def name(self) -> str:
        return "openai"

    @property
    def model(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        embeddings = await self.embed_batch([text])
        return embeddings[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Handles batching for large requests.
        """
        if not texts:
            return []

        # Process in batches
        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts), self._max_batch_size):
            batch = texts[i : i + self._max_batch_size]
            embeddings = await self._embed_batch_request(batch)
            all_embeddings.extend(embeddings)

        return all_embeddings

    async def _embed_batch_request(self, texts: list[str]) -> list[list[float]]:
        """Make a single batch embedding request."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "input": texts,
                },
            )

            if response.status_code != 200:
                raise EmbeddingProviderError(
                    f"OpenAI API error: {response.status_code} - {response.text}"
                )

            data = response.json()

            # Sort by index to maintain order
            sorted_data = sorted(data["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in sorted_data]


class OllamaEmbeddings(EmbeddingProvider):
    """Ollama embedding provider.

    Uses nomic-embed-text by default (768 dimensions).
    Free and runs locally.

    Models:
    - nomic-embed-text: 768 dims, fast, good quality
    - mxbai-embed-large: 1024 dims, larger model
    - all-minilm: 384 dims, very small and fast
    """

    # Model dimensions mapping
    MODEL_DIMENSIONS = {
        "nomic-embed-text": 768,
        "mxbai-embed-large": 1024,
        "all-minilm": 384,
        "snowflake-arctic-embed": 1024,
    }

    def __init__(
        self,
        model: str = "nomic-embed-text",
        base_url: str = "http://localhost:11434",
        timeout: float = 60.0,
    ) -> None:
        """Initialize Ollama embeddings.

        Args:
            model: Embedding model to use.
            base_url: Ollama server URL.
            timeout: Request timeout (longer for local processing).
        """
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._dimensions = self.MODEL_DIMENSIONS.get(model, 768)

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def model(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/api/embeddings",
                json={
                    "model": self._model,
                    "prompt": text,
                },
            )

            if response.status_code != 200:
                raise EmbeddingProviderError(
                    f"Ollama API error: {response.status_code} - {response.text}"
                )

            data = response.json()
            return data["embedding"]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Ollama doesn't support native batching, so we process concurrently.
        """
        if not texts:
            return []

        # Process concurrently with semaphore to limit parallelism
        semaphore = asyncio.Semaphore(5)  # Limit concurrent requests

        async def embed_with_semaphore(text: str) -> list[float]:
            async with semaphore:
                return await self.embed(text)

        tasks = [embed_with_semaphore(text) for text in texts]
        return await asyncio.gather(*tasks)

    async def is_available(self) -> bool:
        """Check if Ollama server is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    async def ensure_model(self) -> bool:
        """Ensure the model is pulled and available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url}/api/tags")
                if response.status_code != 200:
                    return False

                data = response.json()
                models = [m["name"] for m in data.get("models", [])]

                # Check if model is available (with or without :latest tag)
                model_name = self._model.split(":")[0]
                return any(m.startswith(model_name) for m in models)
        except Exception:
            return False


class MockEmbeddings(EmbeddingProvider):
    """Mock embedding provider for testing.

    Generates deterministic embeddings based on text hash.
    """

    def __init__(
        self,
        dimensions: int = 1536,
        model: str = "mock-embedding",
    ) -> None:
        """Initialize mock embeddings.

        Args:
            dimensions: Embedding dimensions.
            model: Model name for identification.
        """
        self._dimensions = dimensions
        self._model = model

    @property
    def name(self) -> str:
        return "mock"

    @property
    def model(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed(self, text: str) -> list[float]:
        """Generate deterministic embedding from text hash."""
        import hashlib

        # Generate deterministic seed from text
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        seed = int(text_hash[:8], 16)

        # Generate pseudo-random embedding
        import random

        rng = random.Random(seed)
        embedding = [rng.gauss(0, 1) for _ in range(self._dimensions)]

        # Normalize to unit vector
        import math

        norm = math.sqrt(sum(x * x for x in embedding))
        return [x / norm for x in embedding]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        return [await self.embed(text) for text in texts]


def get_embedding_provider(
    provider: str = "openai",
    config: EmbeddingConfig | None = None,
) -> EmbeddingProvider:
    """Get embedding provider by name.

    Args:
        provider: Provider name ("openai", "ollama", "mock").
        config: Optional configuration.

    Returns:
        EmbeddingProvider instance.

    Raises:
        ValueError: If provider is unknown.
    """
    config = config or EmbeddingConfig()

    if provider == "openai":
        return OpenAIEmbeddings(
            api_key=config.openai_api_key,
            model=config.openai_model,
            base_url=config.openai_base_url,
            timeout=config.timeout,
            max_batch_size=config.max_batch_size,
        )
    elif provider == "ollama":
        return OllamaEmbeddings(
            model=config.ollama_model,
            base_url=config.ollama_base_url,
            timeout=config.timeout,
        )
    elif provider == "mock":
        return MockEmbeddings()
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")


class EmbeddingCache:
    """Simple in-memory cache for embeddings.

    Reduces API calls for repeated texts.
    """

    def __init__(self, max_size: int = 1000) -> None:
        """Initialize cache.

        Args:
            max_size: Maximum number of embeddings to cache.
        """
        self._cache: dict[str, list[float]] = {}
        self._max_size = max_size
        self._access_order: list[str] = []

    def get(self, text: str) -> list[float] | None:
        """Get cached embedding."""
        return self._cache.get(text)

    def set(self, text: str, embedding: list[float]) -> None:
        """Cache an embedding."""
        if text in self._cache:
            # Move to end of access order
            self._access_order.remove(text)
            self._access_order.append(text)
            return

        # Evict oldest if at capacity
        while len(self._cache) >= self._max_size:
            oldest = self._access_order.pop(0)
            del self._cache[oldest]

        self._cache[text] = embedding
        self._access_order.append(text)

    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()
        self._access_order.clear()

    @property
    def size(self) -> int:
        """Current cache size."""
        return len(self._cache)


class CachedEmbeddingProvider(EmbeddingProvider):
    """Embedding provider with caching layer.

    Wraps another provider and caches results.
    """

    def __init__(
        self,
        provider: EmbeddingProvider,
        cache: EmbeddingCache | None = None,
    ) -> None:
        """Initialize cached provider.

        Args:
            provider: Underlying embedding provider.
            cache: Cache instance. Creates new if not provided.
        """
        self._provider = provider
        self._cache = cache or EmbeddingCache()

    @property
    def name(self) -> str:
        return f"cached_{self._provider.name}"

    @property
    def model(self) -> str:
        return self._provider.model

    @property
    def dimensions(self) -> int:
        return self._provider.dimensions

    async def embed(self, text: str) -> list[float]:
        """Get embedding with caching."""
        cached = self._cache.get(text)
        if cached is not None:
            return cached

        embedding = await self._provider.embed(text)
        self._cache.set(text, embedding)
        return embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings with caching."""
        results: list[list[float]] = []
        uncached_indices: list[int] = []
        uncached_texts: list[str] = []

        # Check cache for each text
        for i, text in enumerate(texts):
            cached = self._cache.get(text)
            if cached is not None:
                results.append(cached)
            else:
                results.append([])  # Placeholder
                uncached_indices.append(i)
                uncached_texts.append(text)

        # Fetch uncached embeddings
        if uncached_texts:
            embeddings = await self._provider.embed_batch(uncached_texts)
            for idx, embedding, text in zip(
                uncached_indices, embeddings, uncached_texts, strict=False
            ):
                results[idx] = embedding
                self._cache.set(text, embedding)

        return results
