"""Business metrics for cost, usage, performance, and quality tracking.

Provides high-level business KPIs by integrating cost tracking
with metrics export and operational observability.
"""

import logging
from dataclasses import dataclass

from paracle_core.compat import UTC, datetime, timedelta
from paracle_core.cost.models import CostUsage
from paracle_core.cost.tracker import CostTracker, get_cost_tracker

from paracle_observability.metrics import PrometheusRegistry

logger = logging.getLogger("paracle.business_metrics")


def _utcnow() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(UTC)


@dataclass
class CostMetrics:
    """Cost-related business metrics."""

    # Absolute costs
    total_cost: float
    prompt_cost: float
    completion_cost: float

    # Token usage
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int

    # Request counts
    request_count: int

    # Efficiency metrics
    cost_per_request: float
    cost_per_1k_tokens: float
    tokens_per_request: float

    # Budget status
    budget_status: str  # ok, warning, critical, exceeded
    budget_usage_pct: float  # 0.0 to 100.0
    budget_remaining: float

    # Time period
    period_start: datetime | None
    period_end: datetime | None


@dataclass
class UsageMetrics:
    """Usage pattern metrics."""

    # Request counts
    total_requests: int
    requests_today: int
    requests_this_week: int
    requests_this_month: int

    # Request rates (per hour)
    requests_per_hour: float
    requests_per_day_avg: float

    # Peak usage
    peak_hour: str  # e.g., "14:00"
    peak_requests: int

    # Active periods
    active_days: int
    active_hours: int


@dataclass
class PerformanceMetrics:
    """Performance-related metrics."""

    # Latency (seconds)
    avg_latency: float
    p50_latency: float
    p95_latency: float
    p99_latency: float

    # Throughput
    tokens_per_second: float
    requests_per_minute: float

    # Efficiency
    avg_tokens_per_request: float
    avg_cost_per_second: float


@dataclass
class QualityMetrics:
    """Quality and reliability metrics."""

    # Success rates
    success_rate: float  # 0.0 to 1.0
    error_rate: float  # 0.0 to 1.0

    # Response quality
    completion_rate: float  # Requests with completions
    retry_rate: float  # Requests that needed retries

    # Error breakdown
    error_count: int
    timeout_count: int
    rate_limit_count: int


@dataclass
class BusinessMetricsSummary:
    """Complete business metrics summary."""

    cost: CostMetrics
    usage: UsageMetrics
    performance: PerformanceMetrics
    quality: QualityMetrics

    # Overall score (0-100)
    health_score: float

    # Timestamp
    generated_at: datetime


class BusinessMetrics:
    """Business metrics tracking and reporting.

    Provides high-level business KPIs by integrating:
    - Cost tracking (from CostTracker)
    - Usage patterns (request counts, rates)
    - Performance metrics (latency, throughput)
    - Quality metrics (success rate, errors)

    Metrics are exported to Prometheus for monitoring and alerting.

    Example:
        >>> metrics = BusinessMetrics()
        >>> summary = metrics.get_summary()
        >>> print(f"Total cost: ${summary.cost.total_cost:.2f}")
        >>> print(f"Success rate: {summary.quality.success_rate:.1%}")
        >>> print(f"Health score: {summary.health_score}/100")
    """

    def __init__(
        self,
        cost_tracker: CostTracker | None = None,
        prometheus_registry: PrometheusRegistry | None = None,
    ):
        """Initialize business metrics.

        Args:
            cost_tracker: Cost tracker instance (uses global if None)
            prometheus_registry: Prometheus registry for metric export
        """
        self.cost_tracker = cost_tracker or get_cost_tracker()
        self.prometheus = prometheus_registry or PrometheusRegistry()

        # Initialize Prometheus metrics
        self._init_prometheus_metrics()

        # Performance tracking (simple in-memory for now)
        self._latencies: list[float] = []
        self._request_timestamps: list[datetime] = []

        # Quality tracking
        self._success_count = 0
        self._error_count = 0
        self._timeout_count = 0
        self._rate_limit_count = 0
        self._retry_count = 0

    def _init_prometheus_metrics(self) -> None:
        """Initialize Prometheus metrics for export."""
        # Cost metrics
        self._cost_gauge = self.prometheus.gauge(
            "paracle_cost_total_usd",
            "Total cost in USD",
            {"period": "total"},
        )
        self._tokens_gauge = self.prometheus.gauge(
            "paracle_tokens_total",
            "Total tokens used",
            {"type": "total"},
        )

        # Usage metrics
        self._requests_counter = self.prometheus.counter(
            "paracle_requests_total",
            "Total number of requests",
            {"status": "all"},
        )

        # Performance metrics
        self._latency_histogram = self.prometheus.histogram(
            "paracle_latency_seconds",
            "Request latency in seconds",
            {},
        )

        # Quality metrics
        self._success_counter = self.prometheus.counter(
            "paracle_requests_success_total",
            "Successful requests",
            {},
        )
        self._error_counter = self.prometheus.counter(
            "paracle_requests_error_total",
            "Failed requests",
            {"type": "error"},
        )

    def get_cost_metrics(
        self,
        period: str = "total",  # total, today, week, month
    ) -> CostMetrics:
        """Get cost-related metrics for a period.

        Args:
            period: Time period - total, today, week, month

        Returns:
            Cost metrics including spending, tokens, and budget status
        """
        # Get usage data from cost tracker
        if period == "today":
            usage = self.cost_tracker.get_daily_usage()
        elif period == "month":
            usage = self.cost_tracker.get_monthly_usage()
        elif period == "week":
            # Get usage for last 7 days
            usage = self._get_weekly_usage()
        else:  # total
            usage = self.cost_tracker.get_total_usage()

        # Calculate efficiency metrics
        cost_per_request = (
            usage.total_cost / usage.request_count if usage.request_count > 0 else 0.0
        )
        cost_per_1k_tokens = (
            (usage.total_cost / usage.total_tokens * 1000)
            if usage.total_tokens > 0
            else 0.0
        )
        tokens_per_request = (
            usage.total_tokens / usage.request_count if usage.request_count > 0 else 0.0
        )

        # Get budget status
        report = self.cost_tracker.get_report()
        budget_status = report.budget_status.value

        # Calculate budget usage percentage (simplified)
        # In a real scenario, we'd need the budget limit
        budget_usage_pct = 0.0
        budget_remaining = 0.0

        # Check if there are any budget alerts
        if report.budget_alerts:
            latest_alert = report.budget_alerts[-1]
            if "usage_percent" in latest_alert:
                budget_usage_pct = latest_alert["usage_percent"]
            if "budget_limit" in latest_alert and "current_usage" in latest_alert:
                budget_remaining = (
                    latest_alert["budget_limit"] - latest_alert["current_usage"]
                )

        # Update Prometheus metrics
        self._cost_gauge.set(usage.total_cost)
        self._tokens_gauge.set(usage.total_tokens)

        return CostMetrics(
            total_cost=usage.total_cost,
            prompt_cost=usage.prompt_cost,
            completion_cost=usage.completion_cost,
            total_tokens=usage.total_tokens,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            request_count=usage.request_count,
            cost_per_request=cost_per_request,
            cost_per_1k_tokens=cost_per_1k_tokens,
            tokens_per_request=tokens_per_request,
            budget_status=budget_status,
            budget_usage_pct=budget_usage_pct,
            budget_remaining=budget_remaining,
            period_start=usage.period_start,
            period_end=usage.period_end,
        )

    def _get_weekly_usage(self) -> CostUsage:
        """Get usage for the last 7 days."""
        now = _utcnow()
        weekly_usage = CostUsage(period_start=now - timedelta(days=7), period_end=now)

        # Sum up daily usage for last 7 days
        for days_ago in range(7):
            date = now - timedelta(days=days_ago)
            daily = self.cost_tracker.get_daily_usage(date)
            weekly_usage.total_cost += daily.total_cost
            weekly_usage.prompt_cost += daily.prompt_cost
            weekly_usage.completion_cost += daily.completion_cost
            weekly_usage.total_tokens += daily.total_tokens
            weekly_usage.prompt_tokens += daily.prompt_tokens
            weekly_usage.completion_tokens += daily.completion_tokens
            weekly_usage.request_count += daily.request_count

        return weekly_usage

    def get_usage_metrics(self) -> UsageMetrics:
        """Get usage pattern metrics.

        Returns:
            Usage metrics including request counts and rates
        """
        # Get usage from different periods
        total = self.cost_tracker.get_total_usage()
        today = self.cost_tracker.get_daily_usage()
        week = self._get_weekly_usage()
        month = self.cost_tracker.get_monthly_usage()

        # Calculate rates
        requests_per_day_avg = (
            week.request_count / 7.0 if week.request_count > 0 else 0.0
        )
        requests_per_hour = (
            today.request_count / 24.0 if today.request_count > 0 else 0.0
        )

        # Analyze request timestamps for peak detection
        peak_hour, peak_requests = self._find_peak_hour()

        # Calculate active periods (simplified)
        active_days = 7 if week.request_count > 0 else 0
        active_hours = 24 if today.request_count > 0 else 0

        # Update Prometheus metrics
        self._requests_counter.inc(0)  # Initialize if needed

        return UsageMetrics(
            total_requests=total.request_count,
            requests_today=today.request_count,
            requests_this_week=week.request_count,
            requests_this_month=month.request_count,
            requests_per_hour=requests_per_hour,
            requests_per_day_avg=requests_per_day_avg,
            peak_hour=peak_hour,
            peak_requests=peak_requests,
            active_days=active_days,
            active_hours=active_hours,
        )

    def _find_peak_hour(self) -> tuple[str, int]:
        """Find the peak hour for requests."""
        if not self._request_timestamps:
            return "00:00", 0

        # Group by hour
        hour_counts: dict[str, int] = {}
        for ts in self._request_timestamps:
            hour_key = f"{ts.hour:02d}:00"
            hour_counts[hour_key] = hour_counts.get(hour_key, 0) + 1

        # Find peak
        if not hour_counts:
            return "00:00", 0

        peak_hour = max(hour_counts.items(), key=lambda x: x[1])
        return peak_hour[0], peak_hour[1]

    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get performance metrics.

        Returns:
            Performance metrics including latency and throughput
        """
        # Calculate latency percentiles
        latencies_sorted = sorted(self._latencies) if self._latencies else [0.0]
        n = len(latencies_sorted)

        avg_latency = sum(self._latencies) / n if n > 0 else 0.0
        p50_latency = latencies_sorted[int(n * 0.50)] if n > 0 else 0.0
        p95_latency = latencies_sorted[int(n * 0.95)] if n > 0 else 0.0
        p99_latency = latencies_sorted[int(n * 0.99)] if n > 0 else 0.0

        # Calculate throughput
        total_usage = self.cost_tracker.get_total_usage()
        total_time = sum(self._latencies) if self._latencies else 1.0

        tokens_per_second = (
            total_usage.total_tokens / total_time if total_time > 0 else 0.0
        )
        requests_per_minute = (
            (total_usage.request_count / total_time * 60) if total_time > 0 else 0.0
        )

        # Efficiency
        avg_tokens_per_request = (
            total_usage.total_tokens / total_usage.request_count
            if total_usage.request_count > 0
            else 0.0
        )
        avg_cost_per_second = (
            total_usage.total_cost / total_time if total_time > 0 else 0.0
        )

        # Update Prometheus histogram
        for latency in self._latencies[-100:]:  # Last 100 samples
            self._latency_histogram.observe(latency)

        return PerformanceMetrics(
            avg_latency=avg_latency,
            p50_latency=p50_latency,
            p95_latency=p95_latency,
            p99_latency=p99_latency,
            tokens_per_second=tokens_per_second,
            requests_per_minute=requests_per_minute,
            avg_tokens_per_request=avg_tokens_per_request,
            avg_cost_per_second=avg_cost_per_second,
        )

    def get_quality_metrics(self) -> QualityMetrics:
        """Get quality and reliability metrics.

        Returns:
            Quality metrics including success rate and errors
        """
        total_requests = self._success_count + self._error_count

        success_rate = (
            self._success_count / total_requests if total_requests > 0 else 1.0
        )
        error_rate = self._error_count / total_requests if total_requests > 0 else 0.0

        completion_rate = (
            self._success_count / total_requests if total_requests > 0 else 1.0
        )
        retry_rate = self._retry_count / total_requests if total_requests > 0 else 0.0

        # Update Prometheus counters
        self._success_counter.inc(0)  # Initialize
        self._error_counter.inc(0)  # Initialize

        return QualityMetrics(
            success_rate=success_rate,
            error_rate=error_rate,
            completion_rate=completion_rate,
            retry_rate=retry_rate,
            error_count=self._error_count,
            timeout_count=self._timeout_count,
            rate_limit_count=self._rate_limit_count,
        )

    def get_summary(self) -> BusinessMetricsSummary:
        """Get complete business metrics summary.

        Returns:
            Complete summary with cost, usage, performance, and quality metrics
        """
        cost = self.get_cost_metrics()
        usage = self.get_usage_metrics()
        performance = self.get_performance_metrics()
        quality = self.get_quality_metrics()

        # Calculate overall health score (0-100)
        health_score = self._calculate_health_score(cost, usage, performance, quality)

        return BusinessMetricsSummary(
            cost=cost,
            usage=usage,
            performance=performance,
            quality=quality,
            health_score=health_score,
            generated_at=_utcnow(),
        )

    def _calculate_health_score(
        self,
        cost: CostMetrics,
        usage: UsageMetrics,
        performance: PerformanceMetrics,
        quality: QualityMetrics,
    ) -> float:
        """Calculate overall health score (0-100).

        Weighted scoring:
        - Budget health: 30%
        - Quality (success rate): 40%
        - Performance (latency): 20%
        - Usage patterns: 10%
        """
        # Budget health (0-30 points)
        budget_score = 30.0
        if cost.budget_status == "exceeded":
            budget_score = 0.0
        elif cost.budget_status == "critical":
            budget_score = 10.0
        elif cost.budget_status == "warning":
            budget_score = 20.0

        # Quality score (0-40 points)
        quality_score = quality.success_rate * 40.0

        # Performance score (0-20 points)
        # Good: <1s, Acceptable: <3s, Poor: >3s
        if performance.avg_latency < 1.0:
            perf_score = 20.0
        elif performance.avg_latency < 3.0:
            perf_score = 15.0
        elif performance.avg_latency < 5.0:
            perf_score = 10.0
        else:
            perf_score = 5.0

        # Usage score (0-10 points)
        # Active usage is good
        usage_score = min(10.0, usage.requests_today / 10.0)

        return budget_score + quality_score + perf_score + usage_score

    # Recording methods for tracking

    def record_request(
        self,
        latency: float,
        success: bool = True,
        error_type: str | None = None,
    ) -> None:
        """Record a request for metrics tracking.

        Args:
            latency: Request latency in seconds
            success: Whether request succeeded
            error_type: Type of error if failed (timeout, rate_limit, etc.)
        """
        # Record timestamp
        self._request_timestamps.append(_utcnow())

        # Record latency
        self._latencies.append(latency)

        # Record success/error
        if success:
            self._success_count += 1
            self._success_counter.inc()
        else:
            self._error_count += 1
            self._error_counter.inc()

            if error_type == "timeout":
                self._timeout_count += 1
            elif error_type == "rate_limit":
                self._rate_limit_count += 1

        # Update Prometheus
        self._requests_counter.inc()
        self._latency_histogram.observe(latency)

    def record_retry(self) -> None:
        """Record a retry attempt."""
        self._retry_count += 1

    def export_prometheus(self) -> str:
        """Export all metrics in Prometheus format.

        Returns:
            Prometheus-formatted metrics text
        """
        return self.prometheus.export_text()


# Global instance
_business_metrics: BusinessMetrics | None = None


def get_business_metrics() -> BusinessMetrics:
    """Get the global BusinessMetrics instance."""
    global _business_metrics
    if _business_metrics is None:
        _business_metrics = BusinessMetrics()
    return _business_metrics
