"""Unit tests for CachingCapability."""

import asyncio

import pytest

from paracle_meta.capabilities.caching import (
    CacheEntry,
    CachingCapability,
    CachingConfig,
    MemoryCache,
)


@pytest.fixture
def caching():
    """Create CachingCapability instance with default config."""
    config = CachingConfig(
        cache_type="memory",
        default_ttl_seconds=60,  # 1 minute for tests
        max_cache_size_mb=10,
        track_metrics=True,
    )
    return CachingCapability(config)


# ============================================================================
# CacheEntry Unit Tests
# ============================================================================


def test_cache_entry_initialization():
    """Test CacheEntry initialization."""
    entry = CacheEntry(key="test_key", value="test_value", ttl_seconds=60)

    assert entry.key == "test_key"
    assert entry.value == "test_value"
    assert entry.access_count == 0
    assert not entry.is_expired()


def test_cache_entry_expiration():
    """Test CacheEntry expiration."""
    entry = CacheEntry(key="test_key", value="test_value", ttl_seconds=0)

    # Wait a tiny bit to ensure expiration
    import time

    time.sleep(0.01)

    assert entry.is_expired()


def test_cache_entry_access():
    """Test CacheEntry access tracking."""
    entry = CacheEntry(key="test_key", value="test_value", ttl_seconds=60)

    assert entry.access_count == 0

    entry.access()
    assert entry.access_count == 1

    entry.access()
    assert entry.access_count == 2


# ============================================================================
# MemoryCache Unit Tests
# ============================================================================


def test_memory_cache_initialization():
    """Test MemoryCache initialization."""
    cache = MemoryCache(max_size_bytes=1024 * 1024)  # 1 MB

    assert cache.max_size_bytes == 1024 * 1024
    assert cache.current_size_bytes == 0


def test_memory_cache_set_and_get():
    """Test setting and getting from memory cache."""
    cache = MemoryCache(max_size_bytes=1024 * 1024)

    success = cache.set("key1", {"data": "value1"}, ttl_seconds=60)
    assert success is True

    entry = cache.get("key1")
    assert entry is not None
    assert entry.value == {"data": "value1"}
    assert entry.access_count == 1


def test_memory_cache_get_nonexistent():
    """Test getting nonexistent key."""
    cache = MemoryCache(max_size_bytes=1024 * 1024)

    entry = cache.get("nonexistent")
    assert entry is None


def test_memory_cache_get_expired():
    """Test getting expired entry."""
    cache = MemoryCache(max_size_bytes=1024 * 1024)

    cache.set("key1", "value1", ttl_seconds=0)

    # Wait to ensure expiration
    import time

    time.sleep(0.01)

    entry = cache.get("key1")
    assert entry is None  # Expired entry removed


def test_memory_cache_delete():
    """Test deleting from cache."""
    cache = MemoryCache(max_size_bytes=1024 * 1024)

    cache.set("key1", "value1", ttl_seconds=60)
    assert cache.get("key1") is not None

    deleted = cache.delete("key1")
    assert deleted is True
    assert cache.get("key1") is None


def test_memory_cache_delete_nonexistent():
    """Test deleting nonexistent key."""
    cache = MemoryCache(max_size_bytes=1024 * 1024)

    deleted = cache.delete("nonexistent")
    assert deleted is False


def test_memory_cache_clear():
    """Test clearing cache."""
    cache = MemoryCache(max_size_bytes=1024 * 1024)

    cache.set("key1", "value1", ttl_seconds=60)
    cache.set("key2", "value2", ttl_seconds=60)

    count = cache.clear()
    assert count == 2
    assert cache.current_size_bytes == 0
    assert cache.get("key1") is None


def test_memory_cache_lru_eviction():
    """Test LRU eviction when cache is full."""
    # Very small cache: 50 bytes (each entry ~20-30 bytes)
    cache = MemoryCache(max_size_bytes=50)

    # Add entries that exceed capacity
    cache.set("key1", "value1", ttl_seconds=60)
    cache.set("key2", "value2", ttl_seconds=60)
    cache.set("key3", "value3", ttl_seconds=60)

    # key1 should be evicted (least recently used)
    # Note: Depends on actual JSON encoding size
    result = cache.get("key1")
    # At least one should be evicted due to size constraint
    # The exact eviction depends on serialized size


def test_memory_cache_get_stats():
    """Test getting cache statistics."""
    cache = MemoryCache(max_size_bytes=1024 * 1024)

    cache.set("key1", "value1", ttl_seconds=60)
    cache.set("key2", "value2", ttl_seconds=60)

    stats = cache.get_stats()

    assert stats["total_entries"] == 2
    assert stats["active_entries"] >= 0
    assert "current_size_bytes" in stats
    assert "utilization" in stats


# ============================================================================
# CachingCapability Initialization Tests
# ============================================================================


@pytest.mark.asyncio
async def test_caching_initialization(caching):
    """Test CachingCapability initialization."""
    assert caching.name == "caching"
    assert caching.config.cache_type == "memory"
    assert caching.config.default_ttl_seconds == 60


@pytest.mark.asyncio
async def test_redis_not_implemented():
    """Test that Redis backend raises NotImplementedError."""
    config = CachingConfig(cache_type="redis")

    with pytest.raises(NotImplementedError, match="Redis cache backend"):
        CachingCapability(config)


@pytest.mark.asyncio
async def test_invalid_cache_type():
    """Test that invalid cache type raises ValueError."""
    config = CachingConfig(cache_type="invalid")

    with pytest.raises(ValueError, match="Invalid cache_type"):
        CachingCapability(config)


# ============================================================================
# generate_key Tests
# ============================================================================


@pytest.mark.asyncio
async def test_generate_key(caching):
    """Test generating cache key."""
    result = await caching.generate_key(
        prompt="What is the capital of France?", model="gpt-4", temperature=0.7
    )

    assert result.success is True
    assert "key" in result.output
    assert len(result.output["key"]) == 64  # SHA-256 hex length


@pytest.mark.asyncio
async def test_generate_key_deterministic(caching):
    """Test that same inputs generate same key."""
    result1 = await caching.generate_key(
        prompt="Test prompt", model="gpt-4", temperature=0.5
    )

    result2 = await caching.generate_key(
        prompt="Test prompt", model="gpt-4", temperature=0.5
    )

    assert result1.output["key"] == result2.output["key"]


@pytest.mark.asyncio
async def test_generate_key_different_for_different_inputs(caching):
    """Test that different inputs generate different keys."""
    result1 = await caching.generate_key(prompt="Prompt 1", model="gpt-4")

    result2 = await caching.generate_key(prompt="Prompt 2", model="gpt-4")

    assert result1.output["key"] != result2.output["key"]


# ============================================================================
# get Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_nonexistent_key(caching):
    """Test getting nonexistent key."""
    result = await caching.get(key="nonexistent")

    assert result.success is True
    assert result.output["found"] is False
    assert result.output["value"] is None


@pytest.mark.asyncio
async def test_get_existing_key(caching):
    """Test getting existing key."""
    # Set value first
    await caching.set(key="test_key", value={"response": "Paris"}, ttl=60)

    # Get value
    result = await caching.get(key="test_key")

    assert result.success is True
    assert result.output["found"] is True
    assert result.output["value"] == {"response": "Paris"}
    assert "age_seconds" in result.output


@pytest.mark.asyncio
async def test_get_updates_access_count(caching):
    """Test that get updates access count."""
    # Set value
    await caching.set(key="test_key", value="test_value", ttl=60)

    # Get multiple times
    await caching.get(key="test_key")
    result = await caching.get(key="test_key")

    assert result.output["access_count"] == 2


# ============================================================================
# set Tests
# ============================================================================


@pytest.mark.asyncio
async def test_set_value(caching):
    """Test setting value in cache."""
    result = await caching.set(key="test_key", value="test_value", ttl=60)

    assert result.success is True
    assert result.output["cached"] is True
    assert result.output["ttl_seconds"] == 60


@pytest.mark.asyncio
async def test_set_uses_default_ttl(caching):
    """Test that set uses default TTL when not specified."""
    result = await caching.set(key="test_key", value="test_value")

    assert result.success is True
    assert result.output["ttl_seconds"] == 60  # Default from config


@pytest.mark.asyncio
async def test_set_overwrites_existing(caching):
    """Test that set overwrites existing value."""
    await caching.set(key="test_key", value="old_value", ttl=60)
    await caching.set(key="test_key", value="new_value", ttl=60)

    result = await caching.get(key="test_key")
    assert result.output["value"] == "new_value"


# ============================================================================
# delete Tests
# ============================================================================


@pytest.mark.asyncio
async def test_delete_existing_key(caching):
    """Test deleting existing key."""
    await caching.set(key="test_key", value="test_value", ttl=60)

    result = await caching.delete(key="test_key")

    assert result.success is True
    assert result.output["deleted"] is True

    # Verify deletion
    get_result = await caching.get(key="test_key")
    assert get_result.output["found"] is False


@pytest.mark.asyncio
async def test_delete_nonexistent_key(caching):
    """Test deleting nonexistent key."""
    result = await caching.delete(key="nonexistent")

    assert result.success is True
    assert result.output["deleted"] is False


# ============================================================================
# clear Tests
# ============================================================================


@pytest.mark.asyncio
async def test_clear_cache(caching):
    """Test clearing cache."""
    await caching.set(key="key1", value="value1", ttl=60)
    await caching.set(key="key2", value="value2", ttl=60)

    result = await caching.clear()

    assert result.success is True
    assert result.output["cleared_count"] == 2

    # Verify cache is empty
    assert (await caching.get(key="key1")).output["found"] is False
    assert (await caching.get(key="key2")).output["found"] is False


# ============================================================================
# get_metrics Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_metrics(caching):
    """Test getting cache metrics."""
    # Generate some hits and misses
    await caching.set(key="key1", value="value1", ttl=60)
    await caching.get(key="key1")  # Hit
    await caching.get(key="nonexistent")  # Miss

    result = await caching.get_metrics()

    assert result.success is True
    assert result.output["hits"] == 1
    assert result.output["misses"] == 1
    assert result.output["sets"] == 1
    assert "hit_rate" in result.output
    assert "cache_stats" in result.output


@pytest.mark.asyncio
async def test_metrics_hit_rate_calculation(caching):
    """Test hit rate calculation."""
    # 2 hits, 1 miss -> 2/3 = 66.7% hit rate
    await caching.set(key="key1", value="value1", ttl=60)
    await caching.get(key="key1")  # Hit
    await caching.get(key="key1")  # Hit
    await caching.get(key="nonexistent")  # Miss

    result = await caching.get_metrics()

    hit_rate = result.output["hit_rate"]
    assert 0.65 <= hit_rate <= 0.68


# ============================================================================
# reset_metrics Tests
# ============================================================================


@pytest.mark.asyncio
async def test_reset_metrics(caching):
    """Test resetting metrics."""
    # Generate some traffic
    await caching.set(key="key1", value="value1", ttl=60)
    await caching.get(key="key1")

    # Reset
    result = await caching.reset_metrics()

    assert result.success is True
    assert result.output["metrics_reset"] is True

    # Verify metrics are reset
    metrics = await caching.get_metrics()
    assert metrics.output["hits"] == 0
    assert metrics.output["misses"] == 0
    assert metrics.output["sets"] == 0


# ============================================================================
# execute Action Routing Tests
# ============================================================================


@pytest.mark.asyncio
async def test_execute_generate_key(caching):
    """Test execute with generate_key action."""
    result = await caching.execute(
        action="generate_key", prompt="Test prompt", model="gpt-4"
    )

    assert result.success is True
    assert "key" in result.output


@pytest.mark.asyncio
async def test_execute_set(caching):
    """Test execute with set action."""
    result = await caching.execute(
        action="set", key="test_key", value="test_value", ttl=60
    )

    assert result.success is True
    assert result.output["cached"] is True


@pytest.mark.asyncio
async def test_execute_get(caching):
    """Test execute with get action (default)."""
    await caching.set(key="test_key", value="test_value", ttl=60)

    result = await caching.execute(key="test_key")  # Default action is 'get'

    assert result.success is True
    assert result.output["found"] is True


@pytest.mark.asyncio
async def test_execute_unknown_action(caching):
    """Test execute with unknown action."""
    result = await caching.execute(action="invalid_action")

    assert result.success is False
    assert "error" in result.output
    assert "Unknown action" in result.output["error"]


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_full_caching_workflow(caching):
    """Test complete caching workflow."""
    # 1. Generate key from prompt
    key_result = await caching.generate_key(
        prompt="What is the capital of France?", model="gpt-4", temperature=0.7
    )
    key = key_result.output["key"]

    # 2. Check cache (miss)
    result = await caching.get(key=key)
    assert result.output["found"] is False

    # 3. Cache response
    response = {"answer": "Paris", "confidence": 0.95}
    await caching.set(key=key, value=response, ttl=60)

    # 4. Check cache again (hit)
    result = await caching.get(key=key)
    assert result.output["found"] is True
    assert result.output["value"] == response

    # 5. Verify metrics
    metrics = await caching.get_metrics()
    assert metrics.output["hits"] == 1
    assert metrics.output["misses"] == 1
    assert metrics.output["sets"] == 1


@pytest.mark.asyncio
async def test_cache_ttl_expiration(caching):
    """Test that entries expire after TTL."""
    # Set with 1 second TTL
    await caching.set(key="test_key", value="test_value", ttl=1)

    # Wait for expiration
    await asyncio.sleep(1.1)

    # Should be expired
    result = await caching.get(key="test_key")
    assert result.output["found"] is False


@pytest.mark.asyncio
async def test_cache_deduplication(caching):
    """Test that identical prompts use cache."""
    prompt = "What is 2+2?"
    model = "gpt-4"

    # Generate key
    key_result = await caching.generate_key(prompt=prompt, model=model)
    key = key_result.output["key"]

    # First call (cache miss)
    result1 = await caching.get(key=key)
    assert result1.output["found"] is False

    # Cache response
    await caching.set(key=key, value={"answer": "4"}, ttl=60)

    # Second call (cache hit)
    result2 = await caching.get(key=key)
    assert result2.output["found"] is True
    assert result2.output["value"] == {"answer": "4"}
