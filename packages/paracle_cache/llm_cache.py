"""LLM response caching with semantic key generation."""

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from paracle_cache.cache_manager import get_cache_manager


@dataclass
class CacheKey:
    """Semantic cache key for LLM requests."""

    provider: str
    model: str
    messages: list[dict[str, str]]
    temperature: float = 0.7
    max_tokens: int | None = None

    def to_string(self) -> str:
        """Generate cache key string."""
        # Create deterministic representation
        key_data = {
            "provider": self.provider,
            "model": self.model,
            "messages": self.messages,
            "temperature": round(self.temperature, 2),
            "max_tokens": self.max_tokens,
        }

        # Sort for consistency
        key_json = json.dumps(key_data, sort_keys=True)

        # Hash for compact key
        hash_obj = hashlib.sha256(key_json.encode())
        return hash_obj.hexdigest()


class LLMCache:
    """LLM response cache with hit/miss tracking."""

    def __init__(self, ttl: int = 3600):
        """Initialize LLM cache.

        Args:
            ttl: Time to live in seconds (default: 1 hour)
        """
        self.ttl = ttl
        self._cache = get_cache_manager()
        self._hits = 0
        self._misses = 0

    def get(self, key: CacheKey) -> dict[str, Any] | None:
        """Get cached LLM response.

        Args:
            key: Cache key

        Returns:
            Cached response or None if not found
        """
        key_str = key.to_string()
        response = self._cache.get(key_str)

        if response is not None:
            self._hits += 1
            return response

        self._misses += 1
        return None

    def set(
        self,
        key: CacheKey,
        response: dict[str, Any],
        ttl: int | None = None,
    ) -> bool:
        """Cache LLM response.

        Args:
            key: Cache key
            response: LLM response to cache
            ttl: Time to live (None = use default)

        Returns:
            True if cached successfully
        """
        key_str = key.to_string()
        return self._cache.set(key_str, response, ttl or self.ttl)

    def invalidate(self, key: CacheKey) -> bool:
        """Invalidate cached response.

        Args:
            key: Cache key

        Returns:
            True if invalidated
        """
        key_str = key.to_string()
        return self._cache.delete(key_str)

    def clear(self) -> int:
        """Clear all cached responses.

        Returns:
            Number of entries cleared
        """
        return self._cache.clear()

    def hit_rate(self) -> float | None:
        """Calculate cache hit rate.

        Returns:
            Hit rate (0.0-1.0) or None if no requests
        """
        total = self._hits + self._misses
        if total == 0:
            return None
        return self._hits / total

    def stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats including hits, misses, hit rate
        """
        cache_stats = self._cache.stats()

        return {
            **cache_stats,
            "hits": self._hits,
            "misses": self._misses,
            "total_requests": self._hits + self._misses,
            "hit_rate": self.hit_rate(),
        }


# Global LLM cache instance
_llm_cache: LLMCache | None = None


def get_llm_cache(ttl: int = 3600) -> LLMCache:
    """Get global LLM cache instance.

    Args:
        ttl: Time to live in seconds (only used on first call)

    Returns:
        LLMCache instance
    """
    global _llm_cache
    if _llm_cache is None:
        _llm_cache = LLMCache(ttl=ttl)
    return _llm_cache
