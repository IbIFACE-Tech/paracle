"""Unit tests for RateLimitCapability."""

import asyncio

import pytest

from paracle_meta.capabilities.rate_limit import (
    RateLimitCapability,
    RateLimitConfig,
    TokenBucket,
)


@pytest.fixture
def rate_limiter():
    """Create RateLimitCapability instance with default config."""
    config = RateLimitConfig(
        default_requests_per_minute=60,  # 1 per second
        default_burst_size=10,
        enable_metrics=True,
    )
    return RateLimitCapability(config)


@pytest.fixture
def custom_limiter():
    """Create RateLimitCapability with custom limits."""
    config = RateLimitConfig(
        default_requests_per_minute=60,
        default_burst_size=10,
        custom_limits={
            "openai/gpt-4": (20, 5),  # 20 RPM, burst 5
            "anthropic/claude": (100, 20),  # 100 RPM, burst 20
        },
    )
    return RateLimitCapability(config)


# ============================================================================
# TokenBucket Unit Tests
# ============================================================================


@pytest.mark.asyncio
async def test_token_bucket_initialization():
    """Test TokenBucket initialization."""
    bucket = TokenBucket(refill_rate=1.0, burst_size=10)

    assert bucket.refill_rate == 1.0
    assert bucket.burst_size == 10
    assert bucket.tokens == 10.0  # Starts full


@pytest.mark.asyncio
async def test_token_bucket_consume_success():
    """Test successful token consumption."""
    bucket = TokenBucket(refill_rate=1.0, burst_size=10)

    # Consume 5 tokens
    consumed = await bucket.consume(5)
    assert consumed is True

    # Check remaining (allow small timing variance)
    remaining = await bucket.peek()
    assert 4.9 <= remaining <= 5.1


@pytest.mark.asyncio
async def test_token_bucket_consume_failure():
    """Test token consumption failure when insufficient tokens."""
    bucket = TokenBucket(refill_rate=1.0, burst_size=10)

    # Try to consume more than available
    consumed = await bucket.consume(15)
    assert consumed is False

    # Tokens unchanged
    remaining = await bucket.peek()
    assert remaining == 10.0


@pytest.mark.asyncio
async def test_token_bucket_refill():
    """Test token refill over time."""
    bucket = TokenBucket(refill_rate=10.0, burst_size=10)  # 10 tokens/second

    # Consume all tokens
    await bucket.consume(10)
    remaining = await bucket.peek()
    assert remaining < 0.1  # Allow small timing variance

    # Wait 0.5 seconds -> should refill 5 tokens
    await asyncio.sleep(0.5)
    remaining = await bucket.peek()
    assert 4.0 <= remaining <= 6.0  # Allow some timing variance


@pytest.mark.asyncio
async def test_token_bucket_refill_capped_at_burst():
    """Test that refill doesn't exceed burst size."""
    bucket = TokenBucket(refill_rate=10.0, burst_size=10)

    # Wait 2 seconds (should add 20 tokens, but capped at 10)
    await asyncio.sleep(2.0)
    remaining = await bucket.peek()
    assert remaining == 10.0  # Capped at burst_size


@pytest.mark.asyncio
async def test_token_bucket_wait_time():
    """Test wait time calculation."""
    bucket = TokenBucket(refill_rate=1.0, burst_size=10)  # 1 token/second

    # Consume 8 tokens (2 remaining)
    await bucket.consume(8)

    # Need 5 tokens -> need 3 more -> 3 seconds wait
    wait = await bucket.wait_time(5)
    assert 2.5 <= wait <= 3.5  # Allow timing variance


@pytest.mark.asyncio
async def test_token_bucket_wait_time_zero_when_available():
    """Test wait time is zero when tokens available."""
    bucket = TokenBucket(refill_rate=1.0, burst_size=10)

    wait = await bucket.wait_time(5)
    assert wait == 0.0  # Tokens already available


# ============================================================================
# RateLimitCapability Initialization Tests
# ============================================================================


@pytest.mark.asyncio
async def test_rate_limiter_initialization(rate_limiter):
    """Test RateLimitCapability initialization."""
    assert rate_limiter.name == "rate_limit"
    assert rate_limiter.config.default_requests_per_minute == 60
    assert rate_limiter.config.default_burst_size == 10


@pytest.mark.asyncio
async def test_custom_limits_initialization(custom_limiter):
    """Test initialization with custom limits."""
    assert "openai/gpt-4" in custom_limiter.config.custom_limits
    assert custom_limiter.config.custom_limits["openai/gpt-4"] == (20, 5)


# ============================================================================
# check_limit Tests
# ============================================================================


@pytest.mark.asyncio
async def test_check_limit_allowed(rate_limiter):
    """Test check_limit when tokens available."""
    result = await rate_limiter.check_limit(resource="test-resource", tokens=5)

    assert result.success is True
    assert result.output["allowed"] is True
    assert result.output["available_tokens"] >= 5
    assert result.output["retry_after_seconds"] == 0.0
    assert result.output["resource"] == "test-resource"


@pytest.mark.asyncio
async def test_check_limit_denied(rate_limiter):
    """Test check_limit when insufficient tokens."""
    # Consume all tokens first
    await rate_limiter.consume(resource="test-resource", tokens=10)

    result = await rate_limiter.check_limit(resource="test-resource", tokens=5)

    assert result.success is True
    assert result.output["allowed"] is False
    assert result.output["retry_after_seconds"] > 0


@pytest.mark.asyncio
async def test_check_limit_does_not_consume(rate_limiter):
    """Test that check_limit doesn't consume tokens."""
    # Check limit
    result1 = await rate_limiter.check_limit(resource="test-resource", tokens=5)
    tokens_before = result1.output["available_tokens"]

    # Check again
    result2 = await rate_limiter.check_limit(resource="test-resource", tokens=5)
    tokens_after = result2.output["available_tokens"]

    # Tokens should be similar (allowing for minimal refill)
    assert abs(tokens_after - tokens_before) < 1.0


# ============================================================================
# consume Tests
# ============================================================================


@pytest.mark.asyncio
async def test_consume_success(rate_limiter):
    """Test successful token consumption."""
    result = await rate_limiter.consume(resource="test-resource", tokens=5)

    assert result.success is True
    assert result.output["consumed"] is True
    assert result.output["tokens_consumed"] == 5
    assert result.output["remaining_tokens"] < 10


@pytest.mark.asyncio
async def test_consume_failure(rate_limiter):
    """Test consumption failure when insufficient tokens."""
    # Consume all tokens
    await rate_limiter.consume(resource="test-resource", tokens=10)

    # Try to consume more
    result = await rate_limiter.consume(resource="test-resource", tokens=5)

    assert result.success is True
    assert result.output["consumed"] is False
    assert result.output["tokens_consumed"] == 0


@pytest.mark.asyncio
async def test_consume_updates_metrics(rate_limiter):
    """Test that consume updates metrics."""
    # Successful consumption
    await rate_limiter.consume(resource="test-resource", tokens=5)

    # Check metrics
    metrics = await rate_limiter.get_metrics(resource="test-resource")
    assert metrics.output["test-resource"]["allowed"] == 1
    assert metrics.output["test-resource"]["total"] == 1


# ============================================================================
# check_and_consume Tests
# ============================================================================


@pytest.mark.asyncio
async def test_check_and_consume_allowed(rate_limiter):
    """Test check_and_consume when allowed."""
    result = await rate_limiter.check_and_consume(
        resource="test-resource", tokens=5
    )

    assert result.success is True
    assert result.output["allowed"] is True
    assert result.output["tokens_consumed"] == 5
    assert result.output["retry_after_seconds"] == 0.0


@pytest.mark.asyncio
async def test_check_and_consume_denied(rate_limiter):
    """Test check_and_consume when denied."""
    # Consume all tokens
    await rate_limiter.consume(resource="test-resource", tokens=10)

    result = await rate_limiter.check_and_consume(
        resource="test-resource", tokens=5
    )

    assert result.success is True
    assert result.output["allowed"] is False
    assert result.output["tokens_consumed"] == 0
    assert result.output["retry_after_seconds"] > 0


@pytest.mark.asyncio
async def test_check_and_consume_updates_metrics(rate_limiter):
    """Test that check_and_consume updates metrics correctly."""
    # Allowed request
    await rate_limiter.check_and_consume(resource="test-resource", tokens=5)

    # Denied request (consume all remaining)
    await rate_limiter.consume(resource="test-resource", tokens=10)
    await rate_limiter.check_and_consume(resource="test-resource", tokens=5)

    # Check metrics
    metrics = await rate_limiter.get_metrics(resource="test-resource")
    assert metrics.output["test-resource"]["allowed"] >= 1
    assert metrics.output["test-resource"]["denied"] >= 1
    assert metrics.output["test-resource"]["total"] >= 2


# ============================================================================
# Custom Limits Tests
# ============================================================================


@pytest.mark.asyncio
async def test_custom_limit_applied(custom_limiter):
    """Test that custom limits are applied correctly."""
    # openai/gpt-4 has custom limit: 20 RPM, burst 5
    resource = "openai/gpt-4"

    # Should have burst_size = 5 tokens
    status = await custom_limiter.get_status(resource=resource)
    assert status.output["capacity"] == 5
    assert status.output["refill_rate"] == 20 / 60.0  # 20 RPM -> per second


@pytest.mark.asyncio
async def test_default_limit_when_no_custom(custom_limiter):
    """Test that default limit is used when no custom limit."""
    # unknown-resource should use default: 60 RPM, burst 10
    resource = "unknown-resource"

    status = await custom_limiter.get_status(resource=resource)
    assert status.output["capacity"] == 10
    assert status.output["refill_rate"] == 60 / 60.0  # 60 RPM -> per second


# ============================================================================
# Metrics Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_metrics_for_resource(rate_limiter):
    """Test getting metrics for specific resource."""
    # Generate some traffic
    await rate_limiter.check_and_consume(resource="test-resource", tokens=1)
    await rate_limiter.check_and_consume(resource="test-resource", tokens=1)

    metrics = await rate_limiter.get_metrics(resource="test-resource")

    assert metrics.success is True
    assert "test-resource" in metrics.output
    assert "allowed" in metrics.output["test-resource"]
    assert "denied" in metrics.output["test-resource"]
    assert "total" in metrics.output["test-resource"]
    assert "allow_rate" in metrics.output["test-resource"]


@pytest.mark.asyncio
async def test_get_metrics_for_all_resources(rate_limiter):
    """Test getting metrics for all resources."""
    # Generate traffic for multiple resources
    await rate_limiter.check_and_consume(resource="resource-1", tokens=1)
    await rate_limiter.check_and_consume(resource="resource-2", tokens=1)

    metrics = await rate_limiter.get_metrics()

    assert metrics.success is True
    assert "resource-1" in metrics.output
    assert "resource-2" in metrics.output


@pytest.mark.asyncio
async def test_metrics_allow_rate_calculation(rate_limiter):
    """Test that allow_rate is calculated correctly."""
    # 3 allowed, 1 denied -> 75% allow rate
    await rate_limiter.check_and_consume(resource="test-resource", tokens=1)
    await rate_limiter.check_and_consume(resource="test-resource", tokens=1)
    await rate_limiter.check_and_consume(resource="test-resource", tokens=1)

    # Consume all remaining to force denial
    await rate_limiter.consume(resource="test-resource", tokens=10)
    await rate_limiter.check_and_consume(resource="test-resource", tokens=1)

    metrics = await rate_limiter.get_metrics(resource="test-resource")
    allow_rate = metrics.output["test-resource"]["allow_rate"]

    # Should be 3/4 = 0.75
    assert 0.70 <= allow_rate <= 0.80  # Allow small variance


# ============================================================================
# Status Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_status(rate_limiter):
    """Test getting current status of rate limiter."""
    result = await rate_limiter.get_status(resource="test-resource")

    assert result.success is True
    assert "available_tokens" in result.output
    assert "capacity" in result.output
    assert "refill_rate" in result.output
    assert "estimated_wait_for_one" in result.output
    assert result.output["resource"] == "test-resource"


@pytest.mark.asyncio
async def test_status_shows_correct_capacity(rate_limiter):
    """Test that status shows correct bucket capacity."""
    result = await rate_limiter.get_status(resource="test-resource")

    assert result.output["capacity"] == 10  # default_burst_size
    assert result.output["refill_rate"] == 1.0  # 60 RPM / 60 seconds


# ============================================================================
# Reset Tests
# ============================================================================


@pytest.mark.asyncio
async def test_reset_bucket(rate_limiter):
    """Test resetting token bucket."""
    # Consume some tokens
    await rate_limiter.consume(resource="test-resource", tokens=8)

    # Reset
    result = await rate_limiter.reset_bucket(resource="test-resource")
    assert result.success is True
    assert result.output["reset"] is True

    # Check that bucket is full again
    status = await rate_limiter.get_status(resource="test-resource")
    assert status.output["available_tokens"] == 10.0


@pytest.mark.asyncio
async def test_reset_metrics(rate_limiter):
    """Test resetting metrics."""
    # Generate some traffic
    await rate_limiter.check_and_consume(resource="test-resource", tokens=1)

    # Reset metrics
    result = await rate_limiter.reset_metrics()
    assert result.success is True
    assert result.output["metrics_reset"] is True

    # Metrics should be empty
    metrics = await rate_limiter.get_metrics(resource="test-resource")
    assert metrics.output["test-resource"]["total"] == 0


# ============================================================================
# Execute Action Routing Tests
# ============================================================================


@pytest.mark.asyncio
async def test_execute_check_and_consume(rate_limiter):
    """Test execute with check_and_consume action."""
    result = await rate_limiter.execute(
        action="check_and_consume", resource="test-resource", tokens=1
    )

    assert result.success is True
    assert "allowed" in result.output


@pytest.mark.asyncio
async def test_execute_get_metrics(rate_limiter):
    """Test execute with get_metrics action."""
    result = await rate_limiter.execute(action="get_metrics")

    assert result.success is True


@pytest.mark.asyncio
async def test_execute_unknown_action(rate_limiter):
    """Test execute with unknown action."""
    result = await rate_limiter.execute(action="invalid_action")

    assert result.success is False
    assert "error" in result.output
    assert "Unknown action" in result.output["error"]


@pytest.mark.asyncio
async def test_execute_default_action(rate_limiter):
    """Test execute without action (should default to check_and_consume)."""
    result = await rate_limiter.execute(resource="test-resource", tokens=1)

    assert result.success is True
    assert "allowed" in result.output


# ============================================================================
# Concurrency Tests
# ============================================================================


@pytest.mark.asyncio
async def test_concurrent_requests(rate_limiter):
    """Test that concurrent requests are handled correctly."""

    async def make_request():
        return await rate_limiter.check_and_consume(
            resource="test-resource", tokens=1
        )

    # Make 15 concurrent requests (burst_size=10, so 5 should be denied)
    results = await asyncio.gather(*[make_request() for _ in range(15)])

    allowed = sum(1 for r in results if r.output["allowed"])
    denied = sum(1 for r in results if not r.output["allowed"])

    # Should have ~10 allowed (burst size) and ~5 denied
    assert allowed >= 9  # Allow 1 token variance
    assert denied >= 4


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_rate_limiting_with_wait(rate_limiter):
    """Test rate limiting with wait and retry."""
    # Consume all tokens
    await rate_limiter.consume(resource="test-resource", tokens=10)

    # Try to consume more (should be denied)
    result1 = await rate_limiter.check_and_consume(
        resource="test-resource", tokens=1
    )
    assert result1.output["allowed"] is False

    # Wait for refill
    retry_after = result1.output["retry_after_seconds"]
    await asyncio.sleep(retry_after + 0.1)  # Add buffer

    # Retry (should succeed now)
    result2 = await rate_limiter.check_and_consume(
        resource="test-resource", tokens=1
    )
    assert result2.output["allowed"] is True


@pytest.mark.asyncio
async def test_multiple_resources_isolated(rate_limiter):
    """Test that rate limits are isolated per resource."""
    # Exhaust resource-1
    await rate_limiter.consume(resource="resource-1", tokens=10)

    # resource-1 should be denied
    result1 = await rate_limiter.check_and_consume(resource="resource-1", tokens=1)
    assert result1.output["allowed"] is False

    # resource-2 should still be allowed
    result2 = await rate_limiter.check_and_consume(resource="resource-2", tokens=1)
    assert result2.output["allowed"] is True
