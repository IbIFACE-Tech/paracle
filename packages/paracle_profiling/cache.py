"""Multi-level caching layer for performance optimization.

Phase 8 - Performance & Scale deliverable: Multi-Level Caching
Provides three specialized cache layers:
- Response Cache: API response caching (short TTL)
- Query Cache: Database/store query caching (medium TTL)
- LLM Cache: LLM completion caching (long TTL, expensive operations)

Target: 50% latency reduction on cached operations.
"""

import hashlib
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class CacheLayer(Enum):
    """Cache layer types for multi-level caching."""

    RESPONSE = "response"  # API responses (short TTL: 60s)
    QUERY = "query"  # Store/DB queries (medium TTL: 300s)
    LLM = "llm"  # LLM completions (long TTL: 3600s)


# Default TTLs per layer (in seconds)
DEFAULT_TTLS = {
    CacheLayer.RESPONSE: 60,  # 1 minute
    CacheLayer.QUERY: 300,  # 5 minutes
    CacheLayer.LLM: 3600,  # 1 hour
}

# Default max sizes per layer
DEFAULT_MAX_SIZES = {
    CacheLayer.RESPONSE: 500,  # Frequent, small responses
    CacheLayer.QUERY: 1000,  # Medium frequency queries
    CacheLayer.LLM: 200,  # Large, expensive completions
}


@dataclass
class CacheEntry:
    """Cache entry with value and metadata."""

    value: Any
    created_at: float
    expires_at: float | None
    hit_count: int = 0

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def is_valid(self) -> bool:
        """Check if entry is still valid."""
        return not self.is_expired()


class CacheManager:
    """In-memory cache with TTL support.

    Features:
    - Time-to-live (TTL) expiration
    - Hit count tracking
    - LRU eviction (when max_size reached)
    - Cache statistics

    Future: Can be backed by Redis for distributed caching
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """Initialize cache manager.

        Args:
            max_size: Maximum cache entries (LRU eviction)
            default_ttl: Default TTL in seconds (0 = no expiration)
        """
        self._cache: dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl

        # Stats
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def _make_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        # Create deterministic string representation
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items()),
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        entry = self._cache.get(key)

        if entry is None:
            self._misses += 1
            return None

        if entry.is_expired():
            self._cache.pop(key)
            self._misses += 1
            return None

        # Update hit count
        entry.hit_count += 1
        self._hits += 1
        return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = use default)
        """
        # Evict if at capacity
        if len(self._cache) >= self._max_size:
            self._evict_lru()

        # Calculate expiration
        ttl = ttl if ttl is not None else self._default_ttl
        expires_at = time.time() + ttl if ttl > 0 else None

        self._cache[key] = CacheEntry(
            value=value,
            created_at=time.time(),
            expires_at=expires_at,
        )

    def delete(self, key: str) -> bool:
        """Delete entry from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        if key in self._cache:
            self._cache.pop(key)
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return

        # Find entry with lowest hit count (simple LRU approximation)
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].hit_count)
        self._cache.pop(lru_key)
        self._evictions += 1

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "hit_rate": f"{hit_rate:.1f}%",
            "total_requests": total_requests,
        }

    def cached(
        self,
        ttl: int | None = None,
        key_func: Callable | None = None,
    ):
        """Decorator to cache function results.

        Args:
            ttl: Time-to-live in seconds
            key_func: Custom key generation function

        Example:
            @cache.cached(ttl=60)
            def expensive_operation(arg1, arg2):
                ...
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = f"{func.__module__}.{func.__name__}:{self._make_key(*args, **kwargs)}"

                # Check cache
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit: {func.__name__}")
                    return cached_value

                # Call function
                logger.debug(f"Cache miss: {func.__name__}")
                result = func(*args, **kwargs)

                # Store in cache
                self.set(cache_key, result, ttl=ttl)

                return result

            return wrapper

        return decorator


class MultiLevelCache:
    """Multi-level caching system with specialized layers.

    Provides three cache layers optimized for different use cases:
    - Response: Fast, short-lived API response cache
    - Query: Medium-duration database/store query cache
    - LLM: Long-lived cache for expensive LLM completions

    Example:
        cache = MultiLevelCache()

        # Cache API response
        @cache.response(ttl=30)
        def get_agent_list():
            ...

        # Cache database query
        @cache.query()
        def get_agent_by_id(agent_id: str):
            ...

        # Cache LLM completion
        @cache.llm()
        async def generate_code(prompt: str):
            ...
    """

    def __init__(
        self,
        response_ttl: int | None = None,
        query_ttl: int | None = None,
        llm_ttl: int | None = None,
        response_max_size: int | None = None,
        query_max_size: int | None = None,
        llm_max_size: int | None = None,
    ):
        """Initialize multi-level cache.

        Args:
            response_ttl: TTL for response cache (default: 60s)
            query_ttl: TTL for query cache (default: 300s)
            llm_ttl: TTL for LLM cache (default: 3600s)
            response_max_size: Max entries for response cache
            query_max_size: Max entries for query cache
            llm_max_size: Max entries for LLM cache
        """
        self._layers: dict[CacheLayer, CacheManager] = {
            CacheLayer.RESPONSE: CacheManager(
                max_size=response_max_size or DEFAULT_MAX_SIZES[CacheLayer.RESPONSE],
                default_ttl=response_ttl or DEFAULT_TTLS[CacheLayer.RESPONSE],
            ),
            CacheLayer.QUERY: CacheManager(
                max_size=query_max_size or DEFAULT_MAX_SIZES[CacheLayer.QUERY],
                default_ttl=query_ttl or DEFAULT_TTLS[CacheLayer.QUERY],
            ),
            CacheLayer.LLM: CacheManager(
                max_size=llm_max_size or DEFAULT_MAX_SIZES[CacheLayer.LLM],
                default_ttl=llm_ttl or DEFAULT_TTLS[CacheLayer.LLM],
            ),
        }

        # Track cache performance per layer
        self._layer_latency_savings: dict[CacheLayer, float] = {
            layer: 0.0 for layer in CacheLayer
        }

    def get_layer(self, layer: CacheLayer) -> CacheManager:
        """Get specific cache layer."""
        return self._layers[layer]

    def response(
        self,
        ttl: int | None = None,
        key_func: Callable | None = None,
    ):
        """Decorator for caching API responses.

        Short TTL (default 60s), optimized for frequent API calls.

        Args:
            ttl: Override default TTL
            key_func: Custom key generation function
        """
        return self._layers[CacheLayer.RESPONSE].cached(ttl=ttl, key_func=key_func)

    def query(
        self,
        ttl: int | None = None,
        key_func: Callable | None = None,
    ):
        """Decorator for caching database/store queries.

        Medium TTL (default 300s), optimized for query results.

        Args:
            ttl: Override default TTL
            key_func: Custom key generation function
        """
        return self._layers[CacheLayer.QUERY].cached(ttl=ttl, key_func=key_func)

    def llm(
        self,
        ttl: int | None = None,
        key_func: Callable | None = None,
    ):
        """Decorator for caching LLM completions.

        Long TTL (default 3600s), optimized for expensive LLM calls.
        Uses content-based hashing to identify identical prompts.

        Args:
            ttl: Override default TTL
            key_func: Custom key generation function
        """
        return self._layers[CacheLayer.LLM].cached(ttl=ttl, key_func=key_func)

    def llm_async(
        self,
        ttl: int | None = None,
        key_func: Callable | None = None,
    ):
        """Async decorator for caching LLM completions.

        Same as llm() but for async functions.

        Args:
            ttl: Override default TTL
            key_func: Custom key generation function
        """
        cache = self._layers[CacheLayer.LLM]
        effective_ttl = ttl if ttl is not None else cache._default_ttl

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = f"{func.__module__}.{func.__name__}:{cache._make_key(*args, **kwargs)}"

                # Check cache
                cached_value = cache.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"LLM cache hit: {func.__name__}")
                    return cached_value

                # Call async function
                logger.debug(f"LLM cache miss: {func.__name__}")
                result = await func(*args, **kwargs)

                # Store in cache
                cache.set(cache_key, result, ttl=effective_ttl)

                return result

            return wrapper

        return decorator

    def get(self, layer: CacheLayer, key: str) -> Any | None:
        """Get value from specific layer."""
        return self._layers[layer].get(key)

    def set(
        self,
        layer: CacheLayer,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """Set value in specific layer."""
        self._layers[layer].set(key, value, ttl=ttl)

    def delete(self, layer: CacheLayer, key: str) -> bool:
        """Delete from specific layer."""
        return self._layers[layer].delete(key)

    def clear(self, layer: CacheLayer | None = None) -> None:
        """Clear cache layer(s).

        Args:
            layer: Specific layer to clear, or None for all layers
        """
        if layer:
            self._layers[layer].clear()
        else:
            for cache_layer in self._layers.values():
                cache_layer.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get statistics for all cache layers."""
        stats = {}
        total_hits = 0
        total_misses = 0

        for layer, cache in self._layers.items():
            layer_stats = cache.get_stats()
            stats[layer.value] = layer_stats
            total_hits += layer_stats["hits"]
            total_misses += layer_stats["misses"]

        # Calculate overall hit rate
        total_requests = total_hits + total_misses
        overall_hit_rate = (
            (total_hits / total_requests * 100) if total_requests > 0 else 0
        )

        stats["summary"] = {
            "total_hits": total_hits,
            "total_misses": total_misses,
            "total_requests": total_requests,
            "overall_hit_rate": f"{overall_hit_rate:.1f}%",
            "layers": len(self._layers),
        }

        return stats

    def get_layer_stats(self, layer: CacheLayer) -> dict[str, Any]:
        """Get statistics for a specific layer."""
        return self._layers[layer].get_stats()


# Global cache instances
_global_cache: CacheManager | None = None
_multi_level_cache: MultiLevelCache | None = None


def get_cache() -> CacheManager:
    """Get global single-layer cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheManager()
    return _global_cache


def get_multi_level_cache() -> MultiLevelCache:
    """Get global multi-level cache instance."""
    global _multi_level_cache
    if _multi_level_cache is None:
        _multi_level_cache = MultiLevelCache()
    return _multi_level_cache


def cached(ttl: int = 300, key_func: Callable | None = None):
    """Convenience decorator using global cache.

    Args:
        ttl: Time-to-live in seconds
        key_func: Custom key generation function

    Example:
        @cached(ttl=60)
        def get_agent_spec(agent_id: str):
            ...
    """
    cache = get_cache()
    return cache.cached(ttl=ttl, key_func=key_func)


def cache_response(ttl: int | None = None, key_func: Callable | None = None):
    """Cache API response (short TTL).

    Example:
        @cache_response(ttl=30)
        def list_agents():
            ...
    """
    return get_multi_level_cache().response(ttl=ttl, key_func=key_func)


def cache_query(ttl: int | None = None, key_func: Callable | None = None):
    """Cache database/store query (medium TTL).

    Example:
        @cache_query()
        def get_agent_by_id(agent_id: str):
            ...
    """
    return get_multi_level_cache().query(ttl=ttl, key_func=key_func)


def cache_llm(ttl: int | None = None, key_func: Callable | None = None):
    """Cache LLM completion (long TTL).

    Example:
        @cache_llm()
        def generate_response(prompt: str):
            ...
    """
    return get_multi_level_cache().llm(ttl=ttl, key_func=key_func)


def cache_llm_async(ttl: int | None = None, key_func: Callable | None = None):
    """Cache async LLM completion (long TTL).

    Example:
        @cache_llm_async()
        async def generate_response(prompt: str):
            ...
    """
    return get_multi_level_cache().llm_async(ttl=ttl, key_func=key_func)
