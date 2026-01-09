"""Cache statistics tracking and reporting."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CacheStats:
    """Cache statistics snapshot."""

    # Hit/miss metrics
    hits: int = 0
    misses: int = 0
    total_requests: int = 0

    # Performance metrics
    avg_cached_time_ms: float = 0.0
    avg_uncached_time_ms: float = 0.0

    # Cost metrics
    cached_tokens: int = 0
    uncached_tokens: int = 0
    estimated_cost_saved: float = 0.0

    # Capacity metrics
    cache_size: int = 0
    max_cache_size: int = 0
    evictions: int = 0

    # Temporal
    start_time: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    @property
    def hit_rate(self) -> float | None:
        """Calculate cache hit rate (0.0-1.0)."""
        if self.total_requests == 0:
            return None
        return self.hits / self.total_requests

    @property
    def miss_rate(self) -> float | None:
        """Calculate cache miss rate (0.0-1.0)."""
        if self.total_requests == 0:
            return None
        return self.misses / self.total_requests

    @property
    def speedup_factor(self) -> float | None:
        """Calculate speedup from caching (Nx faster)."""
        if self.avg_cached_time_ms == 0 or self.avg_uncached_time_ms == 0:
            return None
        return self.avg_uncached_time_ms / self.avg_cached_time_ms

    @property
    def utilization(self) -> float | None:
        """Calculate cache utilization (0.0-1.0)."""
        if self.max_cache_size == 0:
            return None
        return min(1.0, self.cache_size / self.max_cache_size)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": self.total_requests,
            "hit_rate": self.hit_rate,
            "miss_rate": self.miss_rate,
            "avg_cached_time_ms": self.avg_cached_time_ms,
            "avg_uncached_time_ms": self.avg_uncached_time_ms,
            "speedup_factor": self.speedup_factor,
            "cached_tokens": self.cached_tokens,
            "uncached_tokens": self.uncached_tokens,
            "estimated_cost_saved": self.estimated_cost_saved,
            "cache_size": self.cache_size,
            "max_cache_size": self.max_cache_size,
            "utilization": self.utilization,
            "evictions": self.evictions,
            "start_time": self.start_time.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }


class CacheStatsTracker:
    """Tracks cache statistics over time."""

    def __init__(self, max_cache_size: int = 1000):
        """Initialize stats tracker.

        Args:
            max_cache_size: Maximum cache size for utilization calculations
        """
        self._stats = CacheStats(max_cache_size=max_cache_size)
        self._cached_times: list[float] = []
        self._uncached_times: list[float] = []

    def record_hit(
        self,
        response_time_ms: float,
        tokens: int = 0,
    ) -> None:
        """Record a cache hit.

        Args:
            response_time_ms: Time taken to retrieve cached response
            tokens: Number of tokens in cached response
        """
        self._stats.hits += 1
        self._stats.total_requests += 1
        self._stats.cached_tokens += tokens
        self._cached_times.append(response_time_ms)
        self._update_averages()
        self._stats.last_updated = datetime.now()

    def record_miss(
        self,
        response_time_ms: float,
        tokens: int = 0,
        cost: float = 0.0,
    ) -> None:
        """Record a cache miss.

        Args:
            response_time_ms: Time taken for LLM call
            tokens: Number of tokens in response
            cost: Cost of LLM call in USD
        """
        self._stats.misses += 1
        self._stats.total_requests += 1
        self._stats.uncached_tokens += tokens
        self._uncached_times.append(response_time_ms)
        self._update_averages()
        self._stats.last_updated = datetime.now()

        # Estimate cost saved if this had been cached
        if self._stats.hits > 0:
            self._stats.estimated_cost_saved += cost

    def record_eviction(self) -> None:
        """Record a cache eviction."""
        self._stats.evictions += 1
        self._stats.last_updated = datetime.now()

    def update_cache_size(self, size: int) -> None:
        """Update current cache size.

        Args:
            size: Current number of items in cache
        """
        self._stats.cache_size = size
        self._stats.last_updated = datetime.now()

    def _update_averages(self) -> None:
        """Recalculate average times."""
        if self._cached_times:
            self._stats.avg_cached_time_ms = sum(self._cached_times) / len(
                self._cached_times
            )

        if self._uncached_times:
            self._stats.avg_uncached_time_ms = sum(self._uncached_times) / len(
                self._uncached_times
            )

    def get_stats(self) -> CacheStats:
        """Get current statistics snapshot.

        Returns:
            Current cache statistics
        """
        return self._stats

    def reset(self) -> None:
        """Reset all statistics."""
        max_size = self._stats.max_cache_size
        self._stats = CacheStats(max_cache_size=max_size)
        self._cached_times = []
        self._uncached_times = []

    def summary(self) -> str:
        """Generate human-readable summary.

        Returns:
            Formatted statistics summary
        """
        stats = self._stats
        lines = [
            "Cache Statistics:",
            f"  Requests: {stats.total_requests} ({stats.hits} hits, {stats.misses} misses)",
        ]

        if stats.hit_rate is not None:
            lines.append(f"  Hit Rate: {stats.hit_rate * 100:.1f}%")

        if stats.speedup_factor is not None:
            lines.append(f"  Speedup: {stats.speedup_factor:.1f}x faster (cached)")

        if stats.estimated_cost_saved > 0:
            lines.append(f"  Cost Saved: ${stats.estimated_cost_saved:.4f}")

        if stats.utilization is not None:
            lines.append(
                f"  Utilization: {stats.utilization * 100:.1f}% ({stats.cache_size}/{stats.max_cache_size})"
            )

        if stats.evictions > 0:
            lines.append(f"  Evictions: {stats.evictions}")

        return "\n".join(lines)


# Global stats tracker
_stats_tracker: CacheStatsTracker | None = None


def get_stats_tracker(max_cache_size: int = 1000) -> CacheStatsTracker:
    """Get global stats tracker instance.

    Args:
        max_cache_size: Maximum cache size (only used on first call)

    Returns:
        Global CacheStatsTracker instance
    """
    global _stats_tracker
    if _stats_tracker is None:
        _stats_tracker = CacheStatsTracker(max_cache_size=max_cache_size)
    return _stats_tracker
