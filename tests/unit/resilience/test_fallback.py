"""Tests for fallback strategies."""

import time

import pytest
from paracle_resilience.fallback import (
    CachedResponseFallback,
    DefaultValueFallback,
    DegradedServiceFallback,
    FallbackChain,
    FallbackError,
    RetryFallback,
)


class TestCachedResponseFallback:
    """Test cached response fallback strategy."""

    def test_cache_hit(self):
        """Test successful cache hit."""
        fallback = CachedResponseFallback(cache_ttl=300)

        def test_func():
            return "fresh"

        # Set cache
        cache_key = fallback._get_cache_key(test_func)
        fallback.set_cache(cache_key, "cached")

        # Should return cached value
        result = fallback.execute(test_func, ValueError("original"))
        assert result == "cached"
        assert fallback.success_count == 1

    def test_cache_miss(self):
        """Test cache miss raises error."""
        fallback = CachedResponseFallback()

        def test_func():
            return "result"

        # No cache entry
        with pytest.raises(FallbackError, match="No valid cache entry"):
            fallback.execute(test_func, ValueError("original"))

        assert fallback.failure_count == 1

    def test_cache_expiry(self):
        """Test cache entry expiration."""
        fallback = CachedResponseFallback(cache_ttl=0.1)  # 100ms TTL

        def test_func():
            return "result"

        # Set cache
        cache_key = fallback._get_cache_key(test_func)
        fallback.set_cache(cache_key, "cached")

        # Wait for expiry
        time.sleep(0.15)

        # Should fail (expired)
        with pytest.raises(FallbackError):
            fallback.execute(test_func, ValueError("original"))

    @pytest.mark.asyncio
    async def test_cache_async(self):
        """Test async cache fallback."""
        fallback = CachedResponseFallback()

        async def test_func():
            return "result"

        cache_key = fallback._get_cache_key(test_func)
        fallback.set_cache(cache_key, "cached")

        result = await fallback.execute_async(test_func, ValueError("original"))
        assert result == "cached"


class TestDefaultValueFallback:
    """Test default value fallback strategy."""

    def test_returns_default(self):
        """Test returns default value."""
        fallback = DefaultValueFallback(default={"status": "degraded"})

        result = fallback.execute(lambda: 1 / 0, ZeroDivisionError())
        assert result == {"status": "degraded"}
        assert fallback.success_count == 1

    def test_default_none(self):
        """Test default value can be None."""
        fallback = DefaultValueFallback(default=None)

        result = fallback.execute(lambda: "fail", ValueError())
        assert result is None

    def test_default_list(self):
        """Test default value as list."""
        fallback = DefaultValueFallback(default=[])

        result = fallback.execute(lambda: "fail", ValueError())
        assert result == []

    @pytest.mark.asyncio
    async def test_default_async(self):
        """Test async default value fallback."""
        fallback = DefaultValueFallback(default="default")

        result = await fallback.execute_async(lambda: 1 / 0, ZeroDivisionError())
        assert result == "default"


class TestRetryFallback:
    """Test retry fallback strategy."""

    def test_retry_success_first_attempt(self):
        """Test success on first retry."""
        fallback = RetryFallback(max_retries=3, base_delay=0.01)
        call_count = [0]

        def flaky_func():
            call_count[0] += 1
            if call_count[0] == 1:
                raise ValueError("first failure")
            return "success"

        result = fallback.execute(flaky_func, ValueError("original"))
        assert result == "success"
        assert call_count[0] == 2  # Original + 1 retry
        assert fallback.success_count == 1

    def test_retry_all_failures(self):
        """Test all retries fail."""
        fallback = RetryFallback(max_retries=3, base_delay=0.01)

        def always_fail():
            raise ValueError("fail")

        with pytest.raises(FallbackError, match="All 3 retries failed"):
            fallback.execute(always_fail, ValueError("original"))

        assert fallback.failure_count == 1

    def test_retry_exponential_backoff(self):
        """Test exponential backoff calculation."""
        fallback = RetryFallback(base_delay=1.0, max_delay=10.0)

        assert fallback._calculate_delay(0) == 1.0
        assert fallback._calculate_delay(1) == 2.0
        assert fallback._calculate_delay(2) == 4.0
        assert fallback._calculate_delay(3) == 8.0
        assert fallback._calculate_delay(4) == 10.0  # Capped at max_delay

    @pytest.mark.asyncio
    async def test_retry_async(self):
        """Test async retry fallback."""
        fallback = RetryFallback(max_retries=2, base_delay=0.01)
        call_count = [0]

        async def flaky_async():
            call_count[0] += 1
            if call_count[0] == 1:
                raise ValueError("first failure")
            return "async_success"

        result = await fallback.execute_async(flaky_async, ValueError("original"))
        assert result == "async_success"
        assert call_count[0] == 2


class TestDegradedServiceFallback:
    """Test degraded service fallback strategy."""

    def test_degraded_service_success(self):
        """Test degraded service returns result."""

        def degraded_func():
            return {"status": "degraded", "data": None}

        fallback = DegradedServiceFallback(degraded_func)

        result = fallback.execute(lambda: 1 / 0, ZeroDivisionError())
        assert result["status"] == "degraded"
        assert fallback.success_count == 1

    def test_degraded_service_failure(self):
        """Test degraded service can also fail."""

        def degraded_func():
            raise RuntimeError("degraded also failed")

        fallback = DegradedServiceFallback(degraded_func)

        with pytest.raises(FallbackError, match="Degraded service failed"):
            fallback.execute(lambda: "fail", ValueError("original"))

        assert fallback.failure_count == 1

    @pytest.mark.asyncio
    async def test_degraded_service_async(self):
        """Test async degraded service."""

        async def degraded_async():
            return "degraded_result"

        fallback = DegradedServiceFallback(degraded_async)

        result = await fallback.execute_async(lambda: 1 / 0, ZeroDivisionError())
        assert result == "degraded_result"

    @pytest.mark.asyncio
    async def test_degraded_service_sync_in_async(self):
        """Test sync degraded function in async context."""

        def degraded_sync():
            return "degraded_sync"

        fallback = DegradedServiceFallback(degraded_sync)

        result = await fallback.execute_async(lambda: 1 / 0, ZeroDivisionError())
        assert result == "degraded_sync"


class TestFallbackChain:
    """Test fallback chain strategy."""

    def test_chain_first_success(self):
        """Test first strategy in chain succeeds."""
        cache = CachedResponseFallback()
        cache.set_cache("test.func", "cached")

        default = DefaultValueFallback(default="default")

        chain = FallbackChain([cache, default])

        def test_func():
            return "result"

        cache_key = cache._get_cache_key(test_func)
        cache.cache[cache_key] = ("cached", time.time())

        result = chain.execute(test_func, ValueError("original"))
        assert result == "cached"
        assert cache.success_count == 1
        assert default.execution_count == 0  # Not tried

    def test_chain_fallback_to_second(self):
        """Test falls back to second strategy."""
        cache = CachedResponseFallback()  # No cache entries
        default = DefaultValueFallback(default="default")

        chain = FallbackChain([cache, default])

        result = chain.execute(lambda: "fail", ValueError("original"))
        assert result == "default"
        assert cache.failure_count == 1
        assert default.success_count == 1

    def test_chain_all_fail(self):
        """Test all strategies in chain fail."""
        cache = CachedResponseFallback()

        def failing_degraded():
            raise RuntimeError("degraded failed")

        degraded = DegradedServiceFallback(failing_degraded)

        chain = FallbackChain([cache, degraded])

        with pytest.raises(FallbackError, match="All 2 fallback strategies failed"):
            chain.execute(lambda: "fail", ValueError("original"))

    def test_chain_statistics(self):
        """Test chain statistics includes all strategies."""
        cache = CachedResponseFallback()
        default = DefaultValueFallback(default="default")
        chain = FallbackChain([cache, default])

        # Execute once
        chain.execute(lambda: "fail", ValueError())

        stats = chain.get_stats()
        assert stats["name"] == "chain"
        assert len(stats["strategies"]) == 2
        assert stats["strategies"][0]["name"] == "cached_response"
        assert stats["strategies"][1]["name"] == "default_value"

    @pytest.mark.asyncio
    async def test_chain_async(self):
        """Test async fallback chain."""
        cache = CachedResponseFallback()
        default = DefaultValueFallback(default="async_default")

        chain = FallbackChain([cache, default])

        result = await chain.execute_async(lambda: "fail", ValueError("original"))
        assert result == "async_default"


class TestFallbackStatistics:
    """Test fallback strategy statistics."""

    def test_execution_counts(self):
        """Test execution statistics tracking."""
        fallback = DefaultValueFallback(default="value")

        # Execute 3 times (all succeed)
        for _ in range(3):
            fallback.execute(lambda: "fail", ValueError())

        stats = fallback.get_stats()
        assert stats["executions"] == 3
        assert stats["successes"] == 3
        assert stats["failures"] == 0
        assert stats["success_rate"] == 1.0

    def test_failure_counts(self):
        """Test failure statistics tracking."""
        fallback = CachedResponseFallback()  # No cache

        # Execute 3 times (all fail)
        for _ in range(3):
            try:
                fallback.execute(lambda: "result", ValueError())
            except FallbackError:
                pass

        stats = fallback.get_stats()
        assert stats["executions"] == 3
        assert stats["successes"] == 0
        assert stats["failures"] == 3
        assert stats["success_rate"] == 0.0

    def test_mixed_results(self):
        """Test mixed success/failure statistics."""
        fallback = RetryFallback(max_retries=3, base_delay=0.01)
        call_count = [0]

        def flaky_func():
            call_count[0] += 1
            if call_count[0] <= 2:  # Fail first 2 attempts
                raise ValueError("fail")
            return "success"

        # First execution succeeds after retry
        fallback.execute(flaky_func, ValueError())
        assert fallback.success_count == 1

        # Second execution fails (reset counter)
        call_count[0] = 0

        def always_fail():
            raise ValueError("fail")

        try:
            fallback.execute(always_fail, ValueError())
        except FallbackError:
            pass

        assert fallback.failure_count == 1

        stats = fallback.get_stats()
        assert stats["executions"] == 2
        assert stats["successes"] == 1
        assert stats["failures"] == 1
        assert stats["success_rate"] == 0.5
