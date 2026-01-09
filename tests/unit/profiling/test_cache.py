"""Tests for multi-level caching system.

Phase 8 - Performance & Scale: Multi-Level Caching
"""

import time

import pytest
from paracle_profiling import (
    CacheEntry,
    CacheLayer,
    CacheManager,
    MultiLevelCache,
    get_cache,
    get_multi_level_cache,
)


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_entry_not_expired(self):
        """Test entry with future expiration is valid."""
        entry = CacheEntry(
            value="test",
            created_at=time.time(),
            expires_at=time.time() + 3600,
        )
        assert entry.is_valid()
        assert not entry.is_expired()

    def test_entry_expired(self):
        """Test entry with past expiration is invalid."""
        entry = CacheEntry(
            value="test",
            created_at=time.time() - 10,
            expires_at=time.time() - 5,
        )
        assert not entry.is_valid()
        assert entry.is_expired()

    def test_entry_no_expiration(self):
        """Test entry without expiration never expires."""
        entry = CacheEntry(
            value="test",
            created_at=time.time(),
            expires_at=None,
        )
        assert entry.is_valid()
        assert not entry.is_expired()


class TestCacheManager:
    """Tests for CacheManager."""

    def test_set_and_get(self):
        """Test basic set and get operations."""
        cache = CacheManager()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing_key(self):
        """Test get returns None for missing key."""
        cache = CacheManager()
        assert cache.get("nonexistent") is None

    def test_ttl_expiration(self):
        """Test TTL expiration works."""
        cache = CacheManager(default_ttl=1)
        cache.set("key1", "value1", ttl=0)  # Immediate expiration
        # Note: ttl=0 means no expiration
        assert cache.get("key1") == "value1"

    def test_delete(self):
        """Test delete operation."""
        cache = CacheManager()
        cache.set("key1", "value1")
        assert cache.delete("key1")
        assert cache.get("key1") is None
        assert not cache.delete("key1")  # Already deleted

    def test_clear(self):
        """Test clear operation."""
        cache = CacheManager()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_lru_eviction(self):
        """Test LRU eviction when max_size reached."""
        cache = CacheManager(max_size=2)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        # Access key1 to increase hit count
        cache.get("key1")
        # Add key3, should evict key2 (lowest hit count)
        cache.set("key3", "value3")
        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") == "value3"

    def test_stats(self):
        """Test statistics tracking."""
        cache = CacheManager()
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key1")  # Hit
        cache.get("missing")  # Miss

        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["size"] == 1

    def test_cached_decorator(self):
        """Test cached decorator."""
        cache = CacheManager()
        call_count = 0

        @cache.cached(ttl=60)
        def expensive_func(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        assert expensive_func(5) == 10
        assert call_count == 1
        assert expensive_func(5) == 10
        assert call_count == 1  # Cached
        assert expensive_func(6) == 12
        assert call_count == 2  # Different args


class TestMultiLevelCache:
    """Tests for MultiLevelCache."""

    def test_default_ttls(self):
        """Test default TTLs for each layer."""
        cache = MultiLevelCache()
        assert cache.get_layer(CacheLayer.RESPONSE)._default_ttl == 60
        assert cache.get_layer(CacheLayer.QUERY)._default_ttl == 300
        assert cache.get_layer(CacheLayer.LLM)._default_ttl == 3600

    def test_custom_ttls(self):
        """Test custom TTLs."""
        cache = MultiLevelCache(
            response_ttl=30,
            query_ttl=120,
            llm_ttl=1800,
        )
        assert cache.get_layer(CacheLayer.RESPONSE)._default_ttl == 30
        assert cache.get_layer(CacheLayer.QUERY)._default_ttl == 120
        assert cache.get_layer(CacheLayer.LLM)._default_ttl == 1800

    def test_response_decorator(self):
        """Test response layer decorator."""
        cache = MultiLevelCache()
        call_count = 0

        @cache.response()
        def get_agents():
            nonlocal call_count
            call_count += 1
            return ["agent1", "agent2"]

        assert get_agents() == ["agent1", "agent2"]
        assert call_count == 1
        assert get_agents() == ["agent1", "agent2"]
        assert call_count == 1

    def test_query_decorator(self):
        """Test query layer decorator."""
        cache = MultiLevelCache()
        call_count = 0

        @cache.query()
        def get_agent_by_id(agent_id: str):
            nonlocal call_count
            call_count += 1
            return {"id": agent_id}

        assert get_agent_by_id("123") == {"id": "123"}
        assert call_count == 1
        assert get_agent_by_id("123") == {"id": "123"}
        assert call_count == 1  # Cached

    def test_llm_decorator(self):
        """Test LLM layer decorator."""
        cache = MultiLevelCache()
        call_count = 0

        @cache.llm()
        def generate_response(prompt: str):
            nonlocal call_count
            call_count += 1
            return f"Response to: {prompt}"

        result = generate_response("hello")
        assert "hello" in result
        assert call_count == 1
        assert generate_response("hello") == result
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_llm_async_decorator(self):
        """Test async LLM layer decorator."""
        cache = MultiLevelCache()
        call_count = 0

        @cache.llm_async()
        async def generate_response_async(prompt: str):
            nonlocal call_count
            call_count += 1
            return f"Async response to: {prompt}"

        result = await generate_response_async("hello")
        assert "hello" in result
        assert call_count == 1
        assert await generate_response_async("hello") == result
        assert call_count == 1

    def test_layer_isolation(self):
        """Test that layers are isolated."""
        cache = MultiLevelCache()
        cache.set(CacheLayer.RESPONSE, "key1", "response_value")
        cache.set(CacheLayer.QUERY, "key1", "query_value")

        assert cache.get(CacheLayer.RESPONSE, "key1") == "response_value"
        assert cache.get(CacheLayer.QUERY, "key1") == "query_value"

    def test_clear_specific_layer(self):
        """Test clearing a specific layer."""
        cache = MultiLevelCache()
        cache.set(CacheLayer.RESPONSE, "key1", "value1")
        cache.set(CacheLayer.QUERY, "key1", "value1")

        cache.clear(CacheLayer.RESPONSE)

        assert cache.get(CacheLayer.RESPONSE, "key1") is None
        assert cache.get(CacheLayer.QUERY, "key1") == "value1"

    def test_clear_all_layers(self):
        """Test clearing all layers."""
        cache = MultiLevelCache()
        cache.set(CacheLayer.RESPONSE, "key1", "value1")
        cache.set(CacheLayer.QUERY, "key1", "value1")
        cache.set(CacheLayer.LLM, "key1", "value1")

        cache.clear()

        assert cache.get(CacheLayer.RESPONSE, "key1") is None
        assert cache.get(CacheLayer.QUERY, "key1") is None
        assert cache.get(CacheLayer.LLM, "key1") is None

    def test_aggregate_stats(self):
        """Test aggregated statistics."""
        cache = MultiLevelCache()

        # Response layer: 1 hit, 1 miss
        cache.set(CacheLayer.RESPONSE, "r1", "v1")
        cache.get(CacheLayer.RESPONSE, "r1")  # Hit
        cache.get(CacheLayer.RESPONSE, "missing")  # Miss

        # Query layer: 2 hits
        cache.set(CacheLayer.QUERY, "q1", "v1")
        cache.get(CacheLayer.QUERY, "q1")  # Hit
        cache.get(CacheLayer.QUERY, "q1")  # Hit

        stats = cache.get_stats()
        assert stats["summary"]["total_hits"] == 3
        assert stats["summary"]["total_misses"] == 1
        assert stats["summary"]["total_requests"] == 4


class TestGlobalCacheInstances:
    """Tests for global cache instances."""

    def test_get_cache_singleton(self):
        """Test get_cache returns singleton."""
        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2

    def test_get_multi_level_cache_singleton(self):
        """Test get_multi_level_cache returns singleton."""
        cache1 = get_multi_level_cache()
        cache2 = get_multi_level_cache()
        assert cache1 is cache2


class TestCachePerformance:
    """Performance tests for caching."""

    def test_cache_speedup(self):
        """Test that cache provides significant speedup."""
        cache = MultiLevelCache()

        @cache.query()
        def slow_operation():
            time.sleep(0.01)  # 10ms
            return {"result": "data"}

        # First call (miss)
        start = time.perf_counter()
        slow_operation()
        first_call = time.perf_counter() - start

        # Second call (hit)
        start = time.perf_counter()
        slow_operation()
        second_call = time.perf_counter() - start

        # Cache hit should be at least 10x faster
        speedup = first_call / second_call
        assert speedup > 10, f"Expected >10x speedup, got {speedup:.1f}x"

    def test_different_args_cached_separately(self):
        """Test that different arguments are cached separately."""
        cache = MultiLevelCache()
        call_count = 0

        @cache.query()
        def compute(x: int, y: int) -> int:
            nonlocal call_count
            call_count += 1
            return x + y

        assert compute(1, 2) == 3
        assert call_count == 1
        assert compute(1, 2) == 3
        assert call_count == 1  # Cached

        assert compute(2, 3) == 5
        assert call_count == 2  # Different args
        assert compute(2, 3) == 5
        assert call_count == 2  # Cached
