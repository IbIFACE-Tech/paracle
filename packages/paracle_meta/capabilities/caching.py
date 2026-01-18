"""CachingCapability for LLM call deduplication and cost optimization.

This capability implements intelligent caching for LLM API calls, reducing
duplicate requests and optimizing costs.

Integration Points:
- Uses paracle_core utilities for hashing and time handling
- Can integrate with Redis for distributed caching (optional)
- Falls back to in-memory cache for development

Example:
    >>> from paracle_meta.capabilities import CachingCapability, CachingConfig
    >>>
    >>> config = CachingConfig(
    ...     cache_type="memory",
    ...     default_ttl_seconds=3600,
    ...     max_cache_size_mb=100
    ... )
    >>> cache = CachingCapability(config)
    >>>
    >>> # Check if cached
    >>> result = await cache.get(key="prompt_hash_123")
    >>> if result.output["found"]:
    ...     return result.output["value"]
    >>>
    >>> # Cache response
    >>> await cache.set(key="prompt_hash_123", value=response, ttl=3600)
"""

import hashlib
import json
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from paracle_core.compat import UTC
from paracle_meta.capabilities.base import BaseCapability, CapabilityResult


@dataclass
class CachingConfig:
    """Configuration for caching capability.

    Attributes:
        cache_type: Type of cache ("memory", "redis").
        default_ttl_seconds: Default time-to-live in seconds (3600 = 1 hour).
        max_cache_size_mb: Maximum cache size in MB (memory only).
        redis_url: Redis connection URL (for redis cache type).
        enable_compression: Whether to compress cached values.
        track_metrics: Whether to track cache hit/miss metrics.
    """

    cache_type: str = "memory"  # "memory" or "redis"
    default_ttl_seconds: int = 3600  # 1 hour
    max_cache_size_mb: int = 100
    redis_url: str | None = None
    enable_compression: bool = False
    track_metrics: bool = True


class CacheEntry:
    """Cache entry with expiration tracking."""

    def __init__(
        self,
        key: str,
        value: Any,
        ttl_seconds: int,
        size_bytes: int = 0,
    ):
        """Initialize cache entry.

        Args:
            key: Cache key.
            value: Cached value.
            ttl_seconds: Time-to-live in seconds.
            size_bytes: Approximate size in bytes.
        """
        self.key = key
        self.value = value
        self.expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
        self.created_at = datetime.now(UTC)
        self.size_bytes = size_bytes
        self.access_count = 0
        self.last_accessed = datetime.now(UTC)

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        return datetime.now(UTC) >= self.expires_at

    def access(self) -> None:
        """Record access for LRU tracking."""
        self.access_count += 1
        self.last_accessed = datetime.now(UTC)


class MemoryCache:
    """In-memory LRU cache with TTL support."""

    def __init__(self, max_size_bytes: int):
        """Initialize memory cache.

        Args:
            max_size_bytes: Maximum cache size in bytes.
        """
        self.max_size_bytes = max_size_bytes
        self.current_size_bytes = 0
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()

    def get(self, key: str) -> CacheEntry | None:
        """Get value from cache.

        Args:
            key: Cache key.

        Returns:
            CacheEntry if found and not expired, None otherwise.
        """
        if key not in self._cache:
            return None

        entry = self._cache[key]

        # Check expiration
        if entry.is_expired():
            self._remove_entry(key)
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        entry.access()

        return entry

    def set(self, key: str, value: Any, ttl_seconds: int) -> bool:
        """Set value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl_seconds: Time-to-live in seconds.

        Returns:
            True if set successfully, False if eviction failed.
        """
        # Estimate size
        value_str = json.dumps(value, default=str)
        size_bytes = len(value_str.encode("utf-8"))

        # Remove existing entry if present
        if key in self._cache:
            self._remove_entry(key)

        # Evict if necessary
        while (
            self.current_size_bytes + size_bytes > self.max_size_bytes and self._cache
        ):
            self._evict_lru()

        # Check if value fits
        if size_bytes > self.max_size_bytes:
            return False  # Value too large

        # Add entry
        entry = CacheEntry(key, value, ttl_seconds, size_bytes)
        self._cache[key] = entry
        self.current_size_bytes += size_bytes

        return True

    def delete(self, key: str) -> bool:
        """Delete entry from cache.

        Args:
            key: Cache key.

        Returns:
            True if deleted, False if not found.
        """
        if key not in self._cache:
            return False

        self._remove_entry(key)
        return True

    def clear(self) -> int:
        """Clear all entries from cache.

        Returns:
            Number of entries cleared.
        """
        count = len(self._cache)
        self._cache.clear()
        self.current_size_bytes = 0
        return count

    def _remove_entry(self, key: str) -> None:
        """Remove entry and update size."""
        entry = self._cache.pop(key)
        self.current_size_bytes -= entry.size_bytes

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if self._cache:
            # OrderedDict maintains insertion order, pop first item
            key, entry = self._cache.popitem(last=False)
            self.current_size_bytes -= entry.size_bytes

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats.
        """
        total_entries = len(self._cache)
        expired_entries = sum(1 for entry in self._cache.values() if entry.is_expired())

        return {
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "active_entries": total_entries - expired_entries,
            "current_size_bytes": self.current_size_bytes,
            "max_size_bytes": self.max_size_bytes,
            "utilization": (
                self.current_size_bytes / self.max_size_bytes
                if self.max_size_bytes > 0
                else 0.0
            ),
        }


class CachingCapability(BaseCapability):
    """Caching capability for LLM call deduplication.

    Provides intelligent caching with TTL, LRU eviction, and optional
    Redis backend for distributed caching.

    Features:
    - In-memory LRU cache with TTL
    - Optional Redis backend for distributed caching
    - Automatic key generation from prompts
    - Cache hit/miss metrics tracking
    - Size-based eviction
    - Compression support (optional)

    Example:
        >>> config = CachingConfig(cache_type="memory", default_ttl_seconds=3600)
        >>> cache = CachingCapability(config)
        >>>
        >>> # Generate cache key from prompt
        >>> key_result = await cache.generate_key(
        ...     prompt="What is the capital of France?",
        ...     model="gpt-4",
        ...     temperature=0.7
        ... )
        >>> key = key_result.output["key"]
        >>>
        >>> # Check cache
        >>> result = await cache.get(key=key)
        >>> if result.output["found"]:
        ...     return result.output["value"]
        >>>
        >>> # Call LLM and cache response
        >>> response = call_llm(...)
        >>> await cache.set(key=key, value=response)
    """

    name = "caching"

    def __init__(self, config: CachingConfig | None = None):
        """Initialize caching capability.

        Args:
            config: Caching configuration (uses defaults if None).
        """
        super().__init__(config or CachingConfig())

        # Initialize cache backend
        if self.config.cache_type == "memory":
            max_bytes = self.config.max_cache_size_mb * 1024 * 1024
            self._cache = MemoryCache(max_bytes)
        elif self.config.cache_type == "redis":
            # Redis integration (would require redis client)
            raise NotImplementedError(
                "Redis cache backend not yet implemented. Use cache_type='memory'."
            )
        else:
            raise ValueError(
                f"Invalid cache_type: {self.config.cache_type}. "
                "Supported: 'memory', 'redis'"
            )

        # Metrics tracking
        self._metrics = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0,
        }

    def _generate_cache_key(
        self, prompt: str, model: str = "", temperature: float = 0.0, **kwargs: Any
    ) -> str:
        """Generate cache key from prompt and parameters.

        Args:
            prompt: User prompt.
            model: Model name.
            temperature: Temperature parameter.
            **kwargs: Additional parameters to include in key.

        Returns:
            Hexadecimal cache key (SHA-256).
        """
        # Create deterministic key from inputs
        key_data = {
            "prompt": prompt,
            "model": model,
            "temperature": temperature,
            **kwargs,
        }

        # Sort keys for deterministic ordering
        key_str = json.dumps(key_data, sort_keys=True)

        # Hash to fixed-length key
        return hashlib.sha256(key_str.encode("utf-8")).hexdigest()

    async def generate_key(
        self, prompt: str, model: str = "", temperature: float = 0.0, **kwargs: Any
    ) -> CapabilityResult:
        """Generate cache key from prompt and parameters.

        Args:
            prompt: User prompt.
            model: Model name.
            temperature: Temperature parameter.
            **kwargs: Additional parameters to include in key.

        Returns:
            CapabilityResult with:
            - key: Generated cache key (SHA-256 hex).
        """
        start = datetime.now(UTC)
        key = self._generate_cache_key(prompt, model, temperature, **kwargs)
        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={"key": key},
            duration_ms=duration,
        )

    async def get(self, key: str) -> CapabilityResult:
        """Get value from cache.

        Args:
            key: Cache key.

        Returns:
            CapabilityResult with:
            - found: bool (True if key exists and not expired).
            - value: Cached value (if found).
            - age_seconds: Age of cached entry (if found).
        """
        start = datetime.now(UTC)

        entry = self._cache.get(key)

        if entry is None:
            # Cache miss
            if self.config.track_metrics:
                self._metrics["misses"] += 1

            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            return CapabilityResult(
                capability=self.name,
                success=True,
                output={"found": False, "value": None},
                duration_ms=duration,
            )

        # Cache hit
        if self.config.track_metrics:
            self._metrics["hits"] += 1

        age = (datetime.now(UTC) - entry.created_at).total_seconds()
        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={
                "found": True,
                "value": entry.value,
                "age_seconds": age,
                "access_count": entry.access_count,
            },
            duration_ms=duration,
        )

    async def set(
        self, key: str, value: Any, ttl: int | None = None
    ) -> CapabilityResult:
        """Set value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds (uses default if None).

        Returns:
            CapabilityResult with:
            - cached: bool (True if successfully cached).
        """
        start = datetime.now(UTC)
        ttl_seconds = ttl or self.config.default_ttl_seconds

        success = self._cache.set(key, value, ttl_seconds)

        if self.config.track_metrics and success:
            self._metrics["sets"] += 1

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={"cached": success, "ttl_seconds": ttl_seconds},
            duration_ms=duration,
        )

    async def delete(self, key: str) -> CapabilityResult:
        """Delete entry from cache.

        Args:
            key: Cache key.

        Returns:
            CapabilityResult with:
            - deleted: bool (True if deleted).
        """
        start = datetime.now(UTC)
        deleted = self._cache.delete(key)

        if self.config.track_metrics and deleted:
            self._metrics["deletes"] += 1

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={"deleted": deleted},
            duration_ms=duration,
        )

    async def clear(self) -> CapabilityResult:
        """Clear all entries from cache.

        Returns:
            CapabilityResult with:
            - cleared_count: Number of entries cleared.
        """
        start = datetime.now(UTC)
        count = self._cache.clear()
        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={"cleared_count": count},
            duration_ms=duration,
        )

    async def get_metrics(self) -> CapabilityResult:
        """Get cache metrics.

        Returns:
            CapabilityResult with:
            - hits: Total cache hits.
            - misses: Total cache misses.
            - hit_rate: Cache hit rate (0.0-1.0).
            - sets: Total cache sets.
            - deletes: Total cache deletes.
            - cache_stats: Backend-specific statistics.
        """
        start = datetime.now(UTC)

        total_accesses = self._metrics["hits"] + self._metrics["misses"]
        hit_rate = self._metrics["hits"] / total_accesses if total_accesses > 0 else 0.0

        cache_stats = self._cache.get_stats()

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={
                "hits": self._metrics["hits"],
                "misses": self._metrics["misses"],
                "hit_rate": hit_rate,
                "sets": self._metrics["sets"],
                "deletes": self._metrics["deletes"],
                "cache_stats": cache_stats,
            },
            duration_ms=duration,
        )

    async def reset_metrics(self) -> CapabilityResult:
        """Reset cache metrics (testing/admin).

        Returns:
            CapabilityResult indicating success.
        """
        start = datetime.now(UTC)

        self._metrics = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0,
        }

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={"metrics_reset": True},
            duration_ms=duration,
        )

    async def execute(self, **kwargs: Any) -> CapabilityResult:
        """Execute caching operation with action routing.

        Args:
            **kwargs: Must include 'action' and action-specific parameters.

        Supported actions:
        - generate_key: Generate cache key from prompt.
        - get: Get value from cache.
        - set: Set value in cache.
        - delete: Delete entry from cache.
        - clear: Clear all entries.
        - get_metrics: Get cache metrics.
        - reset_metrics: Reset metrics (testing).

        Returns:
            CapabilityResult from the executed action.

        Example:
            >>> result = await cache.execute(
            ...     action="set",
            ...     key="prompt_hash_123",
            ...     value={"response": "Paris"},
            ...     ttl=3600
            ... )
        """
        action_param = kwargs.pop("action", "get")

        action_map = {
            "generate_key": self.generate_key,
            "get": self.get,
            "set": self.set,
            "delete": self.delete,
            "clear": self.clear,
            "get_metrics": self.get_metrics,
            "reset_metrics": self.reset_metrics,
        }

        if action_param in action_map:
            return await action_map[action_param](**kwargs)

        return CapabilityResult(
            capability=self.name,
            success=False,
            output={"error": f"Unknown action: {action_param}"},
        )
