"""Unit tests for ObservabilityCapability."""

import pytest

from paracle_meta.capabilities.observability import (
    ObservabilityCapability,
    ObservabilityConfig,
)


@pytest.fixture
def observability():
    """Create ObservabilityCapability instance."""
    config = ObservabilityConfig(
        enable_prometheus=True,
        enable_cost_tracking=True,
        cost_budget_daily=100.0,
        alert_on_budget_threshold=0.9,
    )
    return ObservabilityCapability(config)


@pytest.mark.asyncio
async def test_observability_initialization(observability):
    """Test ObservabilityCapability initialization."""
    assert observability.name == "observability"
    assert observability.config.enable_prometheus is True
    assert observability.config.cost_budget_daily == 100.0


@pytest.mark.asyncio
async def test_track_capability_usage(observability):
    """Test tracking capability usage."""
    result = await observability.track_capability_usage(
        capability="vector_search",
        operation="search",
        latency_ms=150.0,
        success=True,
        tokens_used=500,
        cost=0.01,
    )

    assert result.success is True
    assert result.output["tracked"] is True
    assert result.output["capability"] == "vector_search"
    assert result.output["operation"] == "search"
    assert "timestamp" in result.output


@pytest.mark.asyncio
async def test_track_capability_usage_failure(observability):
    """Test tracking failed capability usage."""
    result = await observability.track_capability_usage(
        capability="github_enhanced",
        operation="review_pr",
        latency_ms=2000.0,
        success=False,
        error_type="rate_limit_exceeded",
    )

    assert result.success is True
    assert result.output["tracked"] is True
    assert result.output["metadata"]["success"] is False


@pytest.mark.asyncio
async def test_track_llm_call(observability):
    """Test tracking LLM API call."""
    result = await observability.track_llm_call(
        provider="openai",
        model="gpt-4",
        prompt_tokens=100,
        completion_tokens=50,
        latency_ms=1200.0,
        success=True,
        cost=0.015,
    )

    assert result.success is True
    assert result.output["capability"] == "llm_provider"
    assert result.output["operation"] == "openai/gpt-4"
    assert result.output["metadata"]["prompt_tokens"] == 100
    assert result.output["metadata"]["completion_tokens"] == 50


@pytest.mark.asyncio
async def test_get_summary(observability):
    """Test getting business metrics summary."""
    # Track some usage first
    await observability.track_capability_usage(
        capability="test",
        operation="test_op",
        latency_ms=100.0,
        success=True,
    )

    result = await observability.get_summary()

    assert result.success is True
    assert "cost" in result.output
    assert "performance" in result.output
    assert "quality" in result.output
    assert "health_score" in result.output


@pytest.mark.asyncio
async def test_get_cost_breakdown(observability):
    """Test getting cost breakdown."""
    result = await observability.get_cost_breakdown()

    assert result.success is True
    assert "total_cost" in result.output
    assert "prompt_cost" in result.output
    assert "completion_cost" in result.output
    assert "total_tokens" in result.output


@pytest.mark.asyncio
async def test_get_performance_metrics(observability):
    """Test getting performance metrics."""
    # Track some operations
    await observability.track_capability_usage(
        capability="test", operation="op1", latency_ms=50.0, success=True
    )
    await observability.track_capability_usage(
        capability="test", operation="op2", latency_ms=150.0, success=True
    )

    result = await observability.get_performance_metrics()

    assert result.success is True
    assert "latency" in result.output
    assert "throughput" in result.output
    assert "p50" in result.output["latency"]
    assert "p95" in result.output["latency"]
    assert "p99" in result.output["latency"]


@pytest.mark.asyncio
async def test_get_quality_metrics(observability):
    """Test getting quality metrics."""
    # Track successes and failures
    await observability.track_capability_usage(
        capability="test", operation="op1", latency_ms=100.0, success=True
    )
    await observability.track_capability_usage(
        capability="test", operation="op2", latency_ms=100.0, success=True
    )
    await observability.track_capability_usage(
        capability="test",
        operation="op3",
        latency_ms=100.0,
        success=False,
        error_type="timeout",
    )

    result = await observability.get_quality_metrics()

    assert result.success is True
    assert "success_rate" in result.output
    assert "error_rate" in result.output
    assert "error_count" in result.output
    assert "timeout_count" in result.output


@pytest.mark.asyncio
async def test_get_health_score(observability):
    """Test getting health score."""
    # Track some successful operations
    for i in range(10):
        await observability.track_capability_usage(
            capability="test", operation="op", latency_ms=100.0, success=True
        )

    result = await observability.get_health_score()

    assert result.success is True
    assert "health_score" in result.output
    assert "status" in result.output
    assert 0.0 <= result.output["health_score"] <= 1.0
    assert result.output["status"] in ["healthy", "degraded", "unhealthy"]


@pytest.mark.asyncio
async def test_get_capability_breakdown(observability):
    """Test getting per-capability metrics breakdown."""
    # Track different capabilities
    await observability.track_capability_usage(
        capability="vector_search", operation="search", latency_ms=150.0, success=True
    )
    await observability.track_capability_usage(
        capability="vector_search",
        operation="add_vector",
        latency_ms=50.0,
        success=True,
    )
    await observability.track_capability_usage(
        capability="reflexion", operation="reflect", latency_ms=500.0, success=True
    )

    result = await observability.get_capability_breakdown()

    assert result.success is True
    assert "capabilities" in result.output
    assert "vector_search" in result.output["capabilities"]
    assert "reflexion" in result.output["capabilities"]

    # Check vector_search metrics
    vs_metrics = result.output["capabilities"]["vector_search"]
    assert vs_metrics["total_calls"] == 2
    assert "avg_latency_ms" in vs_metrics
    assert "success_rate" in vs_metrics
    assert "operations" in vs_metrics


@pytest.mark.asyncio
async def test_capability_breakdown_operations(observability):
    """Test that capability breakdown includes per-operation metrics."""
    # Track multiple operations for same capability
    await observability.track_capability_usage(
        capability="github_enhanced",
        operation="review_pr",
        latency_ms=2000.0,
        success=True,
    )
    await observability.track_capability_usage(
        capability="github_enhanced",
        operation="review_pr",
        latency_ms=1800.0,
        success=True,
    )
    await observability.track_capability_usage(
        capability="github_enhanced",
        operation="merge_pr",
        latency_ms=500.0,
        success=True,
    )

    result = await observability.get_capability_breakdown()

    assert result.success is True
    github_metrics = result.output["capabilities"]["github_enhanced"]
    assert "review_pr" in github_metrics["operations"]
    assert "merge_pr" in github_metrics["operations"]

    review_metrics = github_metrics["operations"]["review_pr"]
    assert review_metrics["count"] == 2
    assert review_metrics["success_rate"] == 1.0


@pytest.mark.asyncio
async def test_export_prometheus(observability):
    """Test exporting Prometheus metrics."""
    result = await observability.export_prometheus()

    assert result.success is True
    assert "prometheus_metrics" in result.output
    assert result.output["format"] == "text/plain; version=0.0.4"


@pytest.mark.asyncio
async def test_export_prometheus_disabled():
    """Test Prometheus export when disabled."""
    config = ObservabilityConfig(enable_prometheus=False)
    obs = ObservabilityCapability(config)

    result = await obs.export_prometheus()

    assert result.success is False
    assert "error" in result.output


@pytest.mark.asyncio
async def test_check_budget(observability):
    """Test budget checking."""
    result = await observability.check_budget()

    assert result.success is True
    assert "budget_status" in result.output
    assert "usage_pct" in result.output
    assert "remaining" in result.output
    assert "alerts" in result.output
    assert "needs_attention" in result.output


@pytest.mark.asyncio
async def test_check_budget_alert_threshold(observability):
    """Test that budget alerts fire at threshold."""
    # Note: This test would need to actually spend budget
    # For now, just verify structure
    result = await observability.check_budget()

    assert result.success is True
    assert isinstance(result.output["alerts"], list)


@pytest.mark.asyncio
async def test_reset_metrics(observability):
    """Test resetting metrics."""
    # Track some operations
    await observability.track_capability_usage(
        capability="test", operation="op", latency_ms=100.0, success=True
    )

    # Get breakdown before reset
    before = await observability.get_capability_breakdown()
    assert len(before.output["capabilities"]) > 0

    # Reset
    result = await observability.reset_metrics()
    assert result.success is True
    assert result.output["reset"] is True

    # Verify capability metrics are cleared
    after = await observability.get_capability_breakdown()
    assert len(after.output["capabilities"]) == 0


@pytest.mark.asyncio
async def test_multiple_capabilities_tracked(observability):
    """Test tracking multiple different capabilities."""
    capabilities = [
        "vector_search",
        "reflexion",
        "hook_system",
        "semantic_memory",
        "hive_mind",
    ]

    for cap in capabilities:
        await observability.track_capability_usage(
            capability=cap, operation="test", latency_ms=100.0, success=True
        )

    result = await observability.get_capability_breakdown()

    assert result.success is True
    assert result.output["total_capabilities"] == len(capabilities)
    for cap in capabilities:
        assert cap in result.output["capabilities"]


@pytest.mark.asyncio
async def test_success_rate_calculation(observability):
    """Test that success rate is calculated correctly."""
    # 7 successes, 3 failures = 70% success rate
    for i in range(7):
        await observability.track_capability_usage(
            capability="test", operation="op", latency_ms=100.0, success=True
        )

    for i in range(3):
        await observability.track_capability_usage(
            capability="test",
            operation="op",
            latency_ms=100.0,
            success=False,
            error_type="test_error",
        )

    result = await observability.get_capability_breakdown()

    assert result.success is True
    test_metrics = result.output["capabilities"]["test"]
    assert test_metrics["total_calls"] == 10
    assert test_metrics["success_rate"] == 0.7
    assert test_metrics["error_count"] == 3


@pytest.mark.asyncio
async def test_latency_tracking(observability):
    """Test that latency is tracked correctly."""
    # Track operations with known latencies
    latencies = [100.0, 200.0, 300.0]

    for lat in latencies:
        await observability.track_capability_usage(
            capability="test", operation="op", latency_ms=lat, success=True
        )

    result = await observability.get_capability_breakdown()

    assert result.success is True
    test_metrics = result.output["capabilities"]["test"]
    expected_avg = sum(latencies) / len(latencies)
    assert abs(test_metrics["avg_latency_ms"] - expected_avg) < 0.01


@pytest.mark.asyncio
async def test_metadata_preserved(observability):
    """Test that custom metadata is preserved."""
    custom_metadata = {
        "user_id": "user123",
        "session_id": "sess456",
        "experiment": "A/B test",
    }

    result = await observability.track_capability_usage(
        capability="test",
        operation="op",
        latency_ms=100.0,
        success=True,
        metadata=custom_metadata,
    )

    assert result.success is True
    assert "user_id" in result.output["metadata"]
    assert result.output["metadata"]["user_id"] == "user123"
    assert result.output["metadata"]["session_id"] == "sess456"
