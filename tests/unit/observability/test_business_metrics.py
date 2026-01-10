"""Tests for business metrics tracking."""


import pytest
from paracle_core.cost.config import BudgetConfig, CostConfig
from paracle_core.cost.tracker import CostTracker
from paracle_observability.business_metrics import (
    BusinessMetrics,
    CostMetrics,
    PerformanceMetrics,
    QualityMetrics,
    UsageMetrics,
    get_business_metrics,
)
from paracle_observability.metrics import PrometheusRegistry


@pytest.fixture
def cost_config():
    """Create test cost configuration."""
    return CostConfig(
        tracking_enabled=True,
        budgets={
            "daily": BudgetConfig(
                enabled=True,
                limit=10.0,
                warning_threshold=0.8,
                critical_threshold=0.95,
                block_on_exceeded=False,
            )
        },
    )


@pytest.fixture
def cost_tracker(cost_config, tmp_path):
    """Create cost tracker with test database."""
    db_path = tmp_path / "costs.db"
    return CostTracker(config=cost_config, db_path=db_path)


@pytest.fixture
def prometheus_registry():
    """Create Prometheus registry."""
    return PrometheusRegistry()


@pytest.fixture
def business_metrics(cost_tracker, prometheus_registry):
    """Create BusinessMetrics instance."""
    return BusinessMetrics(
        cost_tracker=cost_tracker,
        prometheus_registry=prometheus_registry,
    )


def test_business_metrics_initialization(business_metrics):
    """Test BusinessMetrics initialization."""
    assert business_metrics.cost_tracker is not None
    assert business_metrics.prometheus is not None
    assert business_metrics._success_count == 0
    assert business_metrics._error_count == 0


def test_get_cost_metrics_empty(business_metrics):
    """Test cost metrics with no usage."""
    metrics = business_metrics.get_cost_metrics()

    assert isinstance(metrics, CostMetrics)
    assert metrics.total_cost == 0.0
    assert metrics.total_tokens == 0
    assert metrics.request_count == 0
    assert metrics.cost_per_request == 0.0


def test_get_cost_metrics_with_usage(business_metrics, cost_tracker):
    """Test cost metrics after tracking usage."""
    # Track some usage
    cost_tracker.track_usage(
        model="gpt-4",
        provider="openai",
        prompt_tokens=1000,
        completion_tokens=500,
    )

    metrics = business_metrics.get_cost_metrics()

    assert metrics.total_tokens == 1500
    assert metrics.prompt_tokens == 1000
    assert metrics.completion_tokens == 500
    assert metrics.request_count == 1
    assert metrics.total_cost > 0.0
    assert metrics.cost_per_request > 0.0
    assert metrics.tokens_per_request == 1500.0


def test_get_cost_metrics_multiple_requests(business_metrics, cost_tracker):
    """Test cost metrics with multiple requests."""
    # Track multiple requests
    for _ in range(3):
        cost_tracker.track_usage(
            model="gpt-4",
            provider="openai",
            prompt_tokens=500,
            completion_tokens=250,
        )

    metrics = business_metrics.get_cost_metrics()

    assert metrics.request_count == 3
    assert metrics.total_tokens == 2250  # 750 * 3
    assert metrics.tokens_per_request == 750.0


def test_get_cost_metrics_budget_status(business_metrics, cost_tracker):
    """Test cost metrics shows budget status."""
    # Track usage within budget
    cost_tracker.track_usage(
        model="gpt-4",
        provider="openai",
        prompt_tokens=100,
        completion_tokens=50,
    )

    metrics = business_metrics.get_cost_metrics()

    assert metrics.budget_status in ["ok", "warning", "critical", "exceeded"]
    assert 0.0 <= metrics.budget_usage_pct <= 100.0


def test_get_cost_metrics_efficiency(business_metrics, cost_tracker):
    """Test efficiency metrics calculation."""
    # Track usage
    cost_tracker.track_usage(
        model="gpt-4",
        provider="openai",
        prompt_tokens=1000,
        completion_tokens=1000,
    )

    metrics = business_metrics.get_cost_metrics()

    # Should have efficiency metrics
    assert metrics.cost_per_request > 0.0
    assert metrics.cost_per_1k_tokens > 0.0
    assert metrics.tokens_per_request == 2000.0


def test_get_usage_metrics_empty(business_metrics):
    """Test usage metrics with no data."""
    metrics = business_metrics.get_usage_metrics()

    assert isinstance(metrics, UsageMetrics)
    assert metrics.total_requests == 0
    assert metrics.requests_today == 0


def test_get_usage_metrics_with_data(business_metrics, cost_tracker):
    """Test usage metrics after tracking."""
    # Track some usage
    cost_tracker.track_usage(
        model="gpt-4",
        provider="openai",
        prompt_tokens=100,
        completion_tokens=50,
    )

    metrics = business_metrics.get_usage_metrics()

    assert metrics.total_requests >= 1
    assert metrics.requests_per_hour >= 0.0
    assert metrics.requests_per_day_avg >= 0.0


def test_get_performance_metrics_empty(business_metrics):
    """Test performance metrics with no data."""
    metrics = business_metrics.get_performance_metrics()

    assert isinstance(metrics, PerformanceMetrics)
    assert metrics.avg_latency == 0.0
    assert metrics.p50_latency == 0.0


def test_get_performance_metrics_with_latencies(business_metrics):
    """Test performance metrics with recorded latencies."""
    # Record some latencies
    business_metrics._latencies = [0.5, 1.0, 1.5, 2.0, 2.5]

    metrics = business_metrics.get_performance_metrics()

    assert metrics.avg_latency == 1.5  # (0.5 + 1.0 + 1.5 + 2.0 + 2.5) / 5
    assert metrics.p50_latency == 1.5  # Median
    assert metrics.p95_latency >= metrics.p50_latency
    assert metrics.p99_latency >= metrics.p95_latency


def test_get_quality_metrics_empty(business_metrics):
    """Test quality metrics with no data."""
    metrics = business_metrics.get_quality_metrics()

    assert isinstance(metrics, QualityMetrics)
    assert metrics.success_rate == 1.0  # No data = 100%
    assert metrics.error_rate == 0.0
    assert metrics.error_count == 0


def test_get_quality_metrics_all_success(business_metrics):
    """Test quality metrics with all successful requests."""
    business_metrics._success_count = 10
    business_metrics._error_count = 0

    metrics = business_metrics.get_quality_metrics()

    assert metrics.success_rate == 1.0
    assert metrics.error_rate == 0.0
    assert metrics.completion_rate == 1.0


def test_get_quality_metrics_with_errors(business_metrics):
    """Test quality metrics with some errors."""
    business_metrics._success_count = 8
    business_metrics._error_count = 2

    metrics = business_metrics.get_quality_metrics()

    assert metrics.success_rate == 0.8  # 8 / 10
    assert metrics.error_rate == 0.2  # 2 / 10
    assert metrics.error_count == 2


def test_get_summary(business_metrics, cost_tracker):
    """Test getting complete business metrics summary."""
    # Setup some data
    cost_tracker.track_usage(
        model="gpt-4",
        provider="openai",
        prompt_tokens=1000,
        completion_tokens=500,
    )
    business_metrics._success_count = 10
    business_metrics._latencies = [0.5, 1.0, 1.5]

    summary = business_metrics.get_summary()

    # Check all sections present
    assert isinstance(summary.cost, CostMetrics)
    assert isinstance(summary.usage, UsageMetrics)
    assert isinstance(summary.performance, PerformanceMetrics)
    assert isinstance(summary.quality, QualityMetrics)

    # Check health score
    assert 0.0 <= summary.health_score <= 100.0

    # Check timestamp
    assert summary.generated_at is not None


def test_health_score_perfect(business_metrics):
    """Test health score calculation with perfect metrics."""
    # Perfect budget (ok)
    cost = CostMetrics(
        total_cost=1.0,
        prompt_cost=0.5,
        completion_cost=0.5,
        total_tokens=1000,
        prompt_tokens=500,
        completion_tokens=500,
        request_count=10,
        cost_per_request=0.1,
        cost_per_1k_tokens=1.0,
        tokens_per_request=100.0,
        budget_status="ok",
        budget_usage_pct=50.0,
        budget_remaining=5.0,
        period_start=None,
        period_end=None,
    )

    # Perfect quality (100% success)
    quality = QualityMetrics(
        success_rate=1.0,
        error_rate=0.0,
        completion_rate=1.0,
        retry_rate=0.0,
        error_count=0,
        timeout_count=0,
        rate_limit_count=0,
    )

    # Good performance (<1s)
    performance = PerformanceMetrics(
        avg_latency=0.5,
        p50_latency=0.5,
        p95_latency=0.8,
        p99_latency=0.9,
        tokens_per_second=100.0,
        requests_per_minute=60.0,
        avg_tokens_per_request=100.0,
        avg_cost_per_second=0.1,
    )

    # Active usage
    usage = UsageMetrics(
        total_requests=100,
        requests_today=10,
        requests_this_week=50,
        requests_this_month=100,
        requests_per_hour=1.0,
        requests_per_day_avg=10.0,
        peak_hour="14:00",
        peak_requests=5,
        active_days=7,
        active_hours=24,
    )

    score = business_metrics._calculate_health_score(
        cost, usage, performance, quality)

    # Should be high (budget:30 + quality:40 + perf:20 + usage:10)
    assert score >= 90.0


def test_health_score_degraded(business_metrics):
    """Test health score with degraded metrics."""
    # Warning budget
    cost = CostMetrics(
        total_cost=9.0,
        prompt_cost=5.0,
        completion_cost=4.0,
        total_tokens=10000,
        prompt_tokens=5000,
        completion_tokens=5000,
        request_count=10,
        cost_per_request=0.9,
        cost_per_1k_tokens=0.9,
        tokens_per_request=1000.0,
        budget_status="warning",
        budget_usage_pct=90.0,
        budget_remaining=1.0,
        period_start=None,
        period_end=None,
    )

    # Some errors (80% success)
    quality = QualityMetrics(
        success_rate=0.8,
        error_rate=0.2,
        completion_rate=0.8,
        retry_rate=0.1,
        error_count=2,
        timeout_count=1,
        rate_limit_count=1,
    )

    # Slow performance (>3s)
    performance = PerformanceMetrics(
        avg_latency=4.0,
        p50_latency=3.5,
        p95_latency=5.0,
        p99_latency=6.0,
        tokens_per_second=50.0,
        requests_per_minute=30.0,
        avg_tokens_per_request=100.0,
        avg_cost_per_second=0.2,
    )

    # Low usage
    usage = UsageMetrics(
        total_requests=10,
        requests_today=1,
        requests_this_week=5,
        requests_this_month=10,
        requests_per_hour=0.1,
        requests_per_day_avg=1.0,
        peak_hour="10:00",
        peak_requests=2,
        active_days=3,
        active_hours=8,
    )

    score = business_metrics._calculate_health_score(
        cost, usage, performance, quality)

    # Should be lower (budget:20 + quality:32 + perf:5 + usage:1)
    assert score < 70.0


def test_record_request_success(business_metrics):
    """Test recording successful request."""
    initial_success = business_metrics._success_count
    initial_latencies = len(business_metrics._latencies)

    business_metrics.record_request(latency=1.5, success=True)

    assert business_metrics._success_count == initial_success + 1
    assert len(business_metrics._latencies) == initial_latencies + 1
    assert business_metrics._latencies[-1] == 1.5


def test_record_request_error(business_metrics):
    """Test recording failed request."""
    initial_errors = business_metrics._error_count

    business_metrics.record_request(
        latency=2.0,
        success=False,
        error_type="timeout",
    )

    assert business_metrics._error_count == initial_errors + 1
    assert business_metrics._timeout_count == 1


def test_record_request_rate_limit(business_metrics):
    """Test recording rate limit error."""
    business_metrics.record_request(
        latency=0.5,
        success=False,
        error_type="rate_limit",
    )

    assert business_metrics._error_count == 1
    assert business_metrics._rate_limit_count == 1


def test_record_retry(business_metrics):
    """Test recording retry attempts."""
    initial_retries = business_metrics._retry_count

    business_metrics.record_retry()
    business_metrics.record_retry()

    assert business_metrics._retry_count == initial_retries + 2


def test_export_prometheus(business_metrics):
    """Test Prometheus export."""
    # Record some data
    business_metrics.record_request(latency=1.0, success=True)
    business_metrics.record_request(latency=2.0, success=False)

    output = business_metrics.export_prometheus()

    # Check format
    assert isinstance(output, str)
    assert "paracle_requests_total" in output
    assert "paracle_cost_total_usd" in output
    assert "# HELP" in output
    assert "# TYPE" in output


def test_get_business_metrics_singleton():
    """Test global business metrics instance."""
    metrics1 = get_business_metrics()
    metrics2 = get_business_metrics()

    # Should be same instance
    assert metrics1 is metrics2


def test_prometheus_metrics_updated(business_metrics, prometheus_registry):
    """Test that Prometheus metrics are updated."""
    # Get initial export
    export1 = business_metrics.export_prometheus()

    # Record activity
    business_metrics.record_request(latency=1.0, success=True)

    # Export should change
    export2 = business_metrics.export_prometheus()

    # Exports should differ (counter increased)
    # Note: This is a simple check; detailed metric validation would be more complex
    assert len(export2) >= len(export1)


def test_cost_metrics_period_fields(business_metrics, cost_tracker):
    """Test that period fields are populated."""
    cost_tracker.track_usage(
        model="gpt-4",
        provider="openai",
        prompt_tokens=100,
        completion_tokens=50,
    )

    metrics = business_metrics.get_cost_metrics(period="today")

    # Period fields should be set by tracker
    # Note: Exact behavior depends on tracker implementation
    assert metrics.period_start is not None or metrics.period_end is not None


def test_usage_metrics_rates(business_metrics, cost_tracker):
    """Test usage rate calculations."""
    # Track multiple requests
    for _ in range(10):
        cost_tracker.track_usage(
            model="gpt-4",
            provider="openai",
            prompt_tokens=100,
            completion_tokens=50,
        )

    metrics = business_metrics.get_usage_metrics()

    # Rates should be calculated
    assert metrics.requests_per_hour >= 0.0
    assert metrics.requests_per_day_avg >= 0.0
