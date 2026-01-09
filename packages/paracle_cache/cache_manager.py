"""Cache manager with Redis/Valkey and in-memory fallback."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


@dataclass
class CacheConfig:
    """Cache configuration."""

    enabled: bool = True
    backend: str = "memory"  # "redis", "valkey", "memory"
    redis_url: str = "redis://localhost:6379/0"
    default_ttl: int = 3600  # 1 hour
    max_memory_size: int = 1000  # Max items in memory cache
    key_prefix: str = "paracle:llm:"

    @classmethod
    def from_env(cls) -> "CacheConfig":
        """Create config from environment variables."""
        import os

        return cls(
            enabled=os.getenv("PARACLE_CACHE_ENABLED", "true").lower() == "true",
            backend=os.getenv("PARACLE_CACHE_BACKEND", "memory"),
            redis_url=os.getenv("PARACLE_CACHE_REDIS_URL", "redis://localhost:6379/0"),
            default_ttl=int(os.getenv("PARACLE_CACHE_TTL", "3600")),
            max_memory_size=int(os.getenv("PARACLE_CACHE_MAX_SIZE", "1000")),
            key_prefix=os.getenv("PARACLE_CACHE_PREFIX", "paracle:llm:"),
        )


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime | None = None
    hit_count: int = 0

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def touch(self) -> None:
        """Increment hit count."""
        self.hit_count += 1


class CacheManager:
    """Manages caching with Redis/Valkey or in-memory fallback."""

    def __init__(self, config: CacheConfig | None = None):
        """Initialize cache manager.

        Args:
            config: Cache configuration. If None, loads from environment.
        """
        self.config = config or CacheConfig.from_env()
        self._redis_client: Any | None = None
        self._memory_cache: dict[str, CacheEntry] = {}

        if self.config.enabled and self.config.backend in ("redis", "valkey"):
            self._init_redis()

    def _init_redis(self) -> None:
        """Initialize Redis connection."""
        if not REDIS_AVAILABLE:
            print("Warning: redis package not installed, falling back to memory cache")
            self.config.backend = "memory"
            return

        try:
            self._redis_client = redis.from_url(
                self.config.redis_url,
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
            )
            # Test connection
            self._redis_client.ping()
            print(f"✅ Connected to {self.config.backend} at {self.config.redis_url}")
        except Exception as e:
            print(
                f"Warning: Could not connect to Redis ({e}), falling back to memory cache"
            )
            self._redis_client = None
            self.config.backend = "memory"

    def _make_key(self, key: str) -> str:
        """Create full cache key with prefix."""
        return f"{self.config.key_prefix}{key}"

    def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if not self.config.enabled:
            return None

        if self.config.backend == "memory":
            return self._get_memory(key)
        else:
            return self._get_redis(key)

    def _get_memory(self, key: str) -> Any | None:
        """Get from memory cache."""
        entry = self._memory_cache.get(key)
        if entry is None:
            return None

        if entry.is_expired():
            del self._memory_cache[key]
            return None

        entry.touch()
        return entry.value

    def _get_redis(self, key: str) -> Any | None:
        """Get from Redis."""
        if self._redis_client is None:
            return None

        try:
            full_key = self._make_key(key)
            value_json = self._redis_client.get(full_key)
            if value_json is None:
                return None

            return json.loads(value_json)
        except Exception as e:
            print(f"Warning: Redis get error ({e})")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None = use default)

        Returns:
            True if cached successfully
        """
        if not self.config.enabled:
            return False

        ttl = ttl or self.config.default_ttl

        if self.config.backend == "memory":
            return self._set_memory(key, value, ttl)
        else:
            return self._set_redis(key, value, ttl)

    def _set_memory(self, key: str, value: Any, ttl: int) -> bool:
        """Set in memory cache."""
        # Evict oldest if at capacity
        if len(self._memory_cache) >= self.config.max_memory_size:
            self._evict_lru()

        expires_at = datetime.now() + timedelta(seconds=ttl)
        self._memory_cache[key] = CacheEntry(
            value=value,
            expires_at=expires_at,
        )
        return True

    def _set_redis(self, key: str, value: Any, ttl: int) -> bool:
        """Set in Redis."""
        if self._redis_client is None:
            return False

        try:
            full_key = self._make_key(key)
            value_json = json.dumps(value)
            self._redis_client.setex(full_key, ttl, value_json)
            return True
        except Exception as e:
            print(f"Warning: Redis set error ({e})")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted
        """
        if not self.config.enabled:
            return False

        if self.config.backend == "memory":
            return self._memory_cache.pop(key, None) is not None
        else:
            if self._redis_client is None:
                return False
            try:
                full_key = self._make_key(key)
                return self._redis_client.delete(full_key) > 0
            except Exception as e:
                print(f"Warning: Redis delete error ({e})")
                return False

    def clear(self) -> int:
        """Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        if not self.config.enabled:
            return 0

        if self.config.backend == "memory":
            count = len(self._memory_cache)
            self._memory_cache.clear()
            return count
        else:
            if self._redis_client is None:
                return 0
            try:
                pattern = f"{self.config.key_prefix}*"
                keys = list(self._redis_client.scan_iter(match=pattern))
                if keys:
                    return self._redis_client.delete(*keys)
                return 0
            except Exception as e:
                print(f"Warning: Redis clear error ({e})")
                return 0

    def _evict_lru(self) -> None:
        """Evict least recently used entry from memory cache."""
        if not self._memory_cache:
            return

        # Find entry with lowest hit count
        lru_key = min(
            self._memory_cache.keys(),
            key=lambda k: self._memory_cache[k].hit_count,
        )
        del self._memory_cache[lru_key]

    def stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        if self.config.backend == "memory":
            return {
                "backend": "memory",
                "enabled": self.config.enabled,
                "entries": len(self._memory_cache),
                "max_size": self.config.max_memory_size,
                "utilization": len(self._memory_cache) / self.config.max_memory_size,
            }
        else:
            if self._redis_client is None:
                return {"backend": "redis", "enabled": False, "connected": False}

            try:
                pattern = f"{self.config.key_prefix}*"
                keys = list(self._redis_client.scan_iter(match=pattern))
                info = self._redis_client.info("stats")

                return {
                    "backend": self.config.backend,
                    "enabled": self.config.enabled,
                    "connected": True,
                    "entries": len(keys),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                    "hit_rate": self._calculate_hit_rate(info),
                }
            except Exception as e:
                return {
                    "backend": self.config.backend,
                    "enabled": self.config.enabled,
                    "connected": False,
                    "error": str(e),
                }

    def _calculate_hit_rate(self, info: dict) -> float | None:
        """Calculate cache hit rate from Redis stats."""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses

        if total == 0:
            return None

        return hits / total


# Global cache manager instance
_cache_manager: CacheManager | None = None


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
