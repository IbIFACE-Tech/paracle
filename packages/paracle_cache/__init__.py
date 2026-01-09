"""Response caching for LLM providers.

Implements Redis/Valkey-based caching for LLM responses to reduce costs
and improve response times. Supports TTL, cache invalidation, and hit/miss tracking.
"""

from paracle_cache.cache_manager import CacheConfig, CacheManager
from paracle_cache.decorators import cached_llm_call
from paracle_cache.llm_cache import CacheKey, LLMCache
from paracle_cache.stats import CacheStats, CacheStatsTracker

__all__ = [
    "CacheManager",
    "CacheConfig",
    "LLMCache",
    "CacheKey",
    "cached_llm_call",
    "CacheStats",
    "CacheStatsTracker",
]

__version__ = "0.1.0"
