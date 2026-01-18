"""Tests for retry logic with exponential backoff."""

from unittest.mock import AsyncMock, patch

import pytest
from paracle_providers.exceptions import (
    LLMProviderError,
    ProviderConnectionError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from paracle_providers.retry import (
    RetryableProvider,
    RetryConfig,
    RetryResult,
    create_retry_decorator,
    retry_with_backoff,
)


class TestRetryConfig:
    """Test RetryConfig class."""

    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert config.jitter_factor == 0.1

    def test_custom_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=0.5,
            max_delay=30.0,
            exponential_base=3.0,
            jitter=False,
        )

        assert config.max_attempts == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0
        assert config.exponential_base == 3.0
        assert config.jitter is False

    def test_is_retryable_rate_limit(self):
        """Test that rate limit errors are retryable."""
        config = RetryConfig()
        exc = ProviderRateLimitError("Rate limited")

        assert config.is_retryable(exc) is True

    def test_is_retryable_timeout(self):
        """Test that timeout errors are retryable."""
        config = RetryConfig()
        exc = ProviderTimeoutError("Timeout")

        assert config.is_retryable(exc) is True

    def test_is_retryable_connection(self):
        """Test that connection errors are retryable."""
        config = RetryConfig()
        exc = ProviderConnectionError("Connection failed")

        assert config.is_retryable(exc) is True

    def test_is_not_retryable_generic_error(self):
        """Test that generic provider errors are not retryable."""
        config = RetryConfig()
        exc = LLMProviderError("Generic error")

        assert config.is_retryable(exc) is False

    def test_is_not_retryable_value_error(self):
        """Test that value errors are not retryable."""
        config = RetryConfig()
        exc = ValueError("Invalid input")

        assert config.is_retryable(exc) is False

    def test_calculate_delay_exponential(self):
        """Test exponential delay calculation."""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=False)

        assert config.calculate_delay(0) == 1.0  # 1 * 2^0
        assert config.calculate_delay(1) == 2.0  # 1 * 2^1
        assert config.calculate_delay(2) == 4.0  # 1 * 2^2
        assert config.calculate_delay(3) == 8.0  # 1 * 2^3

    def test_calculate_delay_max_cap(self):
        """Test that delay is capped at max_delay."""
        config = RetryConfig(
            base_delay=1.0,
            max_delay=5.0,
            exponential_base=2.0,
            jitter=False,
        )

        # 2^10 = 1024, but capped at 5
        assert config.calculate_delay(10) == 5.0

    def test_calculate_delay_with_jitter(self):
        """Test delay calculation with jitter adds variance."""
        config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            jitter=True,
            jitter_factor=0.5,
        )

        # Run multiple times to verify jitter adds variance
        delays = [config.calculate_delay(2) for _ in range(10)]
        unique_delays = set(delays)

        # With jitter, we expect some variance
        assert len(unique_delays) > 1


class TestRetryWithBackoff:
    """Test retry_with_backoff function."""

    @pytest.mark.asyncio
    async def test_success_first_attempt(self):
        """Test operation succeeds on first attempt."""
        mock_operation = AsyncMock(return_value="success")

        result = await retry_with_backoff(mock_operation)

        assert result == "success"
        assert mock_operation.call_count == 1

    @pytest.mark.asyncio
    async def test_success_after_retry(self):
        """Test operation succeeds after retries."""
        call_count = 0

        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ProviderTimeoutError("Timeout")
            return "success"

        config = RetryConfig(max_attempts=5, base_delay=0.01, jitter=False)
        result = await retry_with_backoff(flaky_operation, config)

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_exhausted_retries(self):
        """Test exception raised after exhausting retries."""
        mock_operation = AsyncMock(side_effect=ProviderTimeoutError("Timeout"))
        config = RetryConfig(max_attempts=3, base_delay=0.01, jitter=False)

        with pytest.raises(ProviderTimeoutError):
            await retry_with_backoff(mock_operation, config)

        assert mock_operation.call_count == 3

    @pytest.mark.asyncio
    async def test_non_retryable_exception_not_retried(self):
        """Test that non-retryable exceptions are not retried."""
        mock_operation = AsyncMock(side_effect=LLMProviderError("Non-retryable"))
        config = RetryConfig(max_attempts=3, base_delay=0.01)

        with pytest.raises(LLMProviderError):
            await retry_with_backoff(mock_operation, config)

        # Should fail immediately without retrying
        assert mock_operation.call_count == 1

    @pytest.mark.asyncio
    async def test_respects_retry_after_header(self):
        """Test that retry_after from rate limit is respected."""
        call_count = 0

        async def rate_limited_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ProviderRateLimitError("Rate limited", retry_after=0.1)
            return "success"

        config = RetryConfig(max_attempts=3, base_delay=0.01, jitter=False)

        with patch("paracle_providers.retry.asyncio.sleep") as mock_sleep:
            mock_sleep.return_value = None
            result = await retry_with_backoff(rate_limited_operation, config)

            assert result == "success"
            # Check that sleep was called with at least 0.1 (retry_after)
            if mock_sleep.call_args_list:
                delay = mock_sleep.call_args_list[0][0][0]
                assert delay >= 0.1


class TestRetryableProvider:
    """Test RetryableProvider mixin."""

    @pytest.mark.asyncio
    async def test_with_retry_success(self):
        """Test with_retry method succeeds."""
        provider = RetryableProvider()
        provider.retry_config = RetryConfig(
            max_attempts=3, base_delay=0.01, jitter=False
        )

        mock_operation = AsyncMock(return_value="success")
        result = await provider.with_retry(mock_operation, "test_operation")

        assert result == "success"
        assert mock_operation.call_count == 1

    @pytest.mark.asyncio
    async def test_with_retry_with_retries(self):
        """Test with_retry method retries on failure."""
        provider = RetryableProvider()
        provider.retry_config = RetryConfig(
            max_attempts=3, base_delay=0.01, jitter=False
        )

        call_count = 0

        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ProviderConnectionError("Connection failed")
            return "success"

        result = await provider.with_retry(flaky, "test_operation")

        assert result == "success"
        assert call_count == 2

    def test_configure_retry(self):
        """Test configure_retry method."""
        provider = RetryableProvider()
        new_config = RetryConfig(max_attempts=5, base_delay=2.0)

        provider.configure_retry(new_config)

        assert provider.retry_config.max_attempts == 5
        assert provider.retry_config.base_delay == 2.0


class TestRetryDecorator:
    """Test create_retry_decorator function."""

    @pytest.mark.asyncio
    async def test_decorator_success(self):
        """Test decorator on successful function."""
        config = RetryConfig(max_attempts=3, base_delay=0.01, jitter=False)

        @create_retry_decorator(config)
        async def my_function():
            return "success"

        result = await my_function()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_decorator_with_retries(self):
        """Test decorator retries on failure."""
        config = RetryConfig(max_attempts=3, base_delay=0.01, jitter=False)
        call_count = 0

        @create_retry_decorator(config)
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ProviderTimeoutError("Timeout")
            return "success"

        result = await flaky_function()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_decorator_preserves_function_name(self):
        """Test decorator preserves function name."""
        config = RetryConfig()

        @create_retry_decorator(config)
        async def my_named_function():
            return "success"

        assert my_named_function.__name__ == "my_named_function"

    @pytest.mark.asyncio
    async def test_decorator_with_arguments(self):
        """Test decorated function receives arguments."""
        config = RetryConfig(max_attempts=1)

        @create_retry_decorator(config)
        async def add_numbers(a: int, b: int) -> int:
            return a + b

        result = await add_numbers(2, 3)
        assert result == 5

    @pytest.mark.asyncio
    async def test_decorator_default_config(self):
        """Test decorator with default config."""

        @create_retry_decorator()
        async def my_function():
            return "success"

        result = await my_function()
        assert result == "success"


class TestRetryResult:
    """Test RetryResult class."""

    def test_success_result(self):
        """Test successful retry result."""
        result = RetryResult(
            success=True,
            result="data",
            attempts=1,
            total_delay=0.0,
        )

        assert result.success is True
        assert result.result == "data"
        assert result.attempts == 1
        assert result.total_delay == 0.0
        assert result.last_error is None

    def test_failure_result(self):
        """Test failed retry result."""
        error = ProviderTimeoutError("Timeout")
        result = RetryResult(
            success=False,
            attempts=3,
            total_delay=5.5,
            last_error=error,
        )

        assert result.success is False
        assert result.result is None
        assert result.attempts == 3
        assert result.total_delay == 5.5
        assert result.last_error == error


class TestRetryManagerMetrics:
    """Test RetryManager metrics tracking functionality."""

    @pytest.mark.asyncio
    async def test_get_retry_stats_empty(self):
        """Test retry stats with no executions."""
        from paracle_orchestration.retry import RetryManager

        manager = RetryManager()
        stats = manager.get_retry_stats()

        assert stats["total_contexts"] == 0
        assert stats["succeeded"] == 0
        assert stats["failed"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["total_attempts"] == 0
        assert stats["total_retries"] == 0
        assert stats["avg_retries_per_context"] == 0.0

        # Check new metrics
        assert "metrics" in stats
        metrics = stats["metrics"]
        assert metrics["avg_delay_seconds"] == 0.0
        assert metrics["max_delay_seconds"] == 0.0
        assert metrics["total_delay_seconds"] == 0.0
        assert metrics["success_after_retry"] == 0
        assert metrics["immediate_success"] == 0
        assert metrics["error_categories"] == {}

    @pytest.mark.asyncio
    async def test_get_retry_stats_immediate_success(self):
        """Test metrics for operations that succeed immediately."""
        from paracle_domain.models import BackoffStrategy, RetryPolicy
        from paracle_orchestration.retry import RetryManager

        manager = RetryManager()
        policy = RetryPolicy(
            max_attempts=3,
            backoff_strategy=BackoffStrategy.EXPONENTIAL,
            initial_delay=0.1,
        )

        # Execute 5 operations that succeed immediately
        for i in range(5):
            result = await manager.execute_with_retry(
                step_name=f"immediate_success_{i}",
                func=lambda: "success",
                policy=policy,
            )
            assert result == "success"

        stats = manager.get_retry_stats()

        assert stats["total_contexts"] == 5
        assert stats["succeeded"] == 5
        assert stats["failed"] == 0
        assert stats["success_rate"] == 1.0
        assert stats["total_retries"] == 0

        # Check metrics
        metrics = stats["metrics"]
        assert metrics["immediate_success"] == 5
        assert metrics["success_after_retry"] == 0

    @pytest.mark.asyncio
    async def test_get_retry_stats_with_retries(self):
        """Test metrics for operations requiring retries."""
        from paracle_domain.models import BackoffStrategy, RetryPolicy
        from paracle_orchestration.retry import RetryManager

        manager = RetryManager()
        policy = RetryPolicy(
            max_attempts=3,
            backoff_strategy=BackoffStrategy.EXPONENTIAL,
            initial_delay=0.1,  # Small delay for faster tests
        )

        # Create flaky function that fails first 2 times
        call_count = {"count": 0}

        async def flaky_func():
            call_count["count"] += 1
            if call_count["count"] < 3:
                raise RuntimeError("Transient error")
            return "success"

        result = await manager.execute_with_retry(
            step_name="flaky_operation",
            func=flaky_func,
            policy=policy,
        )

        assert result == "success"

        stats = manager.get_retry_stats()

        assert stats["total_contexts"] == 1
        assert stats["succeeded"] == 1
        assert stats["total_retries"] == 2  # Failed 2 times before success

        # Check metrics
        metrics = stats["metrics"]
        assert metrics["success_after_retry"] == 1
        assert metrics["immediate_success"] == 0
        assert metrics["avg_delay_seconds"] > 0
        assert metrics["max_delay_seconds"] > 0

    @pytest.mark.asyncio
    async def test_get_retry_stats_error_categories(self):
        """Test error category tracking in metrics."""
        from paracle_domain.models import BackoffStrategy, RetryPolicy
        from paracle_orchestration.retry import RetryManager

        manager = RetryManager()
        policy = RetryPolicy(
            max_attempts=2,
            backoff_strategy=BackoffStrategy.EXPONENTIAL,
            initial_delay=0.1,
        )

        # Execute operations with different error types
        errors = [
            ("timeout_op", RuntimeError("Request timeout")),
            ("rate_limit_op", RuntimeError("Rate limit exceeded")),
            ("validation_op", ValueError("Invalid input")),
        ]

        for name, error in errors:
            try:
                await manager.execute_with_retry(
                    step_name=name,
                    func=lambda e=error: (_ for _ in ()).throw(e),
                    policy=policy,
                )
            except Exception:
                pass  # Expected to fail

        stats = manager.get_retry_stats()

        # Check error categories
        metrics = stats["metrics"]
        assert "error_categories" in metrics
        categories = metrics["error_categories"]

        # Should have categorized the errors
        assert len(categories) > 0

    @pytest.mark.asyncio
    async def test_get_retry_stats_delay_calculations(self):
        """Test delay metric calculations."""
        from paracle_domain.models import BackoffStrategy, RetryPolicy
        from paracle_orchestration.retry import RetryManager

        manager = RetryManager()
        policy = RetryPolicy(
            max_attempts=4,
            backoff_strategy=BackoffStrategy.EXPONENTIAL,
            initial_delay=0.1,
            max_delay=1.0,
        )

        # Create function that fails first 3 times
        call_count = {"count": 0}

        async def retry_func():
            call_count["count"] += 1
            if call_count["count"] < 4:
                raise RuntimeError("Transient error")
            return "success"

        result = await manager.execute_with_retry(
            step_name="delay_test",
            func=retry_func,
            policy=policy,
        )

        assert result == "success"

        stats = manager.get_retry_stats()
        metrics = stats["metrics"]

        # Should have delay metrics
        assert metrics["avg_delay_seconds"] > 0
        assert metrics["max_delay_seconds"] >= metrics["avg_delay_seconds"]
        assert metrics["total_delay_seconds"] > 0

        # Total delay should be sum of all delays
        # With exponential backoff, delays increase
        assert metrics["max_delay_seconds"] > 0

    @pytest.mark.asyncio
    async def test_get_retry_stats_mixed_operations(self):
        """Test metrics with mixed successful and failed operations."""
        from paracle_domain.models import BackoffStrategy, RetryPolicy
        from paracle_orchestration.retry import RetryManager

        manager = RetryManager()
        policy = RetryPolicy(
            max_attempts=3,
            backoff_strategy=BackoffStrategy.EXPONENTIAL,
            initial_delay=0.1,
        )

        # 3 immediate successes
        for i in range(3):
            await manager.execute_with_retry(
                step_name=f"success_{i}",
                func=lambda: "success",
                policy=policy,
            )

        # 2 operations with retries
        for i in range(2):
            call_count = {"count": 0}

            async def retry_func():
                call_count["count"] += 1
                if call_count["count"] < 2:
                    raise RuntimeError("Transient")
                return "success"

            await manager.execute_with_retry(
                step_name=f"retry_{i}",
                func=retry_func,
                policy=policy,
            )

        # 1 complete failure
        try:
            await manager.execute_with_retry(
                step_name="failed",
                func=lambda: (_ for _ in ()).throw(RuntimeError("Fail")),
                policy=policy,
            )
        except Exception:
            pass

        stats = manager.get_retry_stats()

        assert stats["total_contexts"] == 6
        assert stats["succeeded"] == 5
        assert stats["failed"] == 1
        assert abs(stats["success_rate"] - 5 / 6) < 0.01

        metrics = stats["metrics"]
        assert metrics["immediate_success"] == 3
        assert metrics["success_after_retry"] == 2

    @pytest.mark.asyncio
    async def test_metrics_accumulation(self):
        """Test that metrics accumulate correctly across executions."""
        from paracle_domain.models import BackoffStrategy, RetryPolicy
        from paracle_orchestration.retry import RetryManager

        manager = RetryManager()
        policy = RetryPolicy(
            max_attempts=3,
            backoff_strategy=BackoffStrategy.EXPONENTIAL,
            initial_delay=0.1,
        )

        # First batch: 10 immediate successes
        for i in range(10):
            await manager.execute_with_retry(
                step_name=f"batch1_{i}",
                func=lambda: "success",
                policy=policy,
            )

        stats1 = manager.get_retry_stats()
        assert stats1["total_contexts"] == 10

        # Second batch: 5 more operations
        for i in range(5):
            await manager.execute_with_retry(
                step_name=f"batch2_{i}",
                func=lambda: "success",
                policy=policy,
            )

        stats2 = manager.get_retry_stats()

        # Stats should accumulate
        assert stats2["total_contexts"] == 15
        assert stats2["succeeded"] == 15
        assert stats2["metrics"]["immediate_success"] == 15
