"""ObservabilityCapability - Unified metrics, cost tracking, and monitoring.

This capability integrates with paracle_observability to provide:
- Business metrics tracking (cost, performance, quality)
- Prometheus metrics export
- Cost tracking and budgeting
- Health scoring
- Alerting integration

Architecture: INTEGRATION (not reimplementation)
- Leverages paracle_observability.business_metrics.BusinessMetrics
- Leverages paracle_core.cost.tracker.CostTracker
- Provides unified observability across paracle ecosystem
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from paracle_core.compat import UTC
from paracle_core.cost.tracker import CostTracker, get_cost_tracker
from paracle_meta.capabilities.base import BaseCapability, CapabilityResult

# Import paracle_observability components
try:
    from paracle_observability.business_metrics import (
        BusinessMetrics,
        BusinessMetricsSummary,
    )
    from paracle_observability.metrics import PrometheusRegistry

    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False


@dataclass
class ObservabilityConfig:
    """Configuration for ObservabilityCapability.

    Attributes:
        enable_prometheus: Enable Prometheus metrics export
        enable_cost_tracking: Enable cost tracking
        cost_budget_daily: Daily cost budget (USD)
        cost_budget_monthly: Monthly cost budget (USD)
        alert_on_budget_threshold: Alert when budget usage exceeds this % (0.0-1.0)
        track_capability_metrics: Track per-capability metrics
    """

    enable_prometheus: bool = True
    enable_cost_tracking: bool = True
    cost_budget_daily: float | None = None
    cost_budget_monthly: float | None = None
    alert_on_budget_threshold: float = 0.9
    track_capability_metrics: bool = True


class ObservabilityCapability(BaseCapability):
    """Observability capability integrating with paracle_observability.

    Provides unified metrics, cost tracking, and performance monitoring
    by leveraging existing paracle infrastructure.

    Integration Points:
    - paracle_observability.business_metrics.BusinessMetrics
    - paracle_core.cost.tracker.CostTracker
    - paracle_observability.metrics.PrometheusRegistry

    Methods:
    - track_capability_usage: Track capability execution metrics
    - track_llm_call: Track LLM API call metrics
    - get_summary: Get business metrics summary
    - get_cost_breakdown: Get detailed cost breakdown
    - get_performance_metrics: Get performance metrics (latency, throughput)
    - get_quality_metrics: Get quality metrics (success rate, errors)
    - get_health_score: Get overall system health score
    - export_prometheus: Export metrics in Prometheus format
    - check_budget: Check budget status and alerts
    """

    name = "observability"

    def __init__(self, config: ObservabilityConfig | None = None):
        """Initialize ObservabilityCapability.

        Args:
            config: Configuration for observability features
        """
        super().__init__(config or ObservabilityConfig())

        if not OBSERVABILITY_AVAILABLE:
            raise ImportError(
                "paracle_observability is required for ObservabilityCapability. "
                "Install with: pip install paracle[observability]"
            )

        # INTEGRATION: Use existing infrastructure
        self._cost_tracker: CostTracker = get_cost_tracker()
        self._business_metrics: BusinessMetrics = BusinessMetrics(
            cost_tracker=self._cost_tracker,
            prometheus_registry=(
                PrometheusRegistry() if self.config.enable_prometheus else None
            ),
        )

        # Capability-specific tracking
        self._capability_metrics: dict[str, dict[str, Any]] = {}
        self._start_time = datetime.now(UTC)

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute observability operation.

        Args:
            action: Operation (track, get_summary, get_cost_breakdown, etc.)
            **kwargs: Operation-specific parameters

        Returns:
            CapabilityResult with operation outcome

        Supported actions:
        - track_capability_usage: Track capability execution
        - track_llm_call: Track LLM API call
        - get_summary: Get complete business metrics
        - get_cost_breakdown: Get cost details
        - get_performance_metrics: Get performance stats
        - get_quality_metrics: Get quality stats
        - get_health_score: Get health score
        - get_capability_breakdown: Get per-capability metrics
        - export_prometheus: Export Prometheus metrics
        - check_budget: Check budget status
        - reset_metrics: Reset metrics (testing)
        """
        action_param = kwargs.pop("action", "get_summary")

        # Map action names to methods
        action_map = {
            "track_capability_usage": self.track_capability_usage,
            "track_llm_call": self.track_llm_call,
            "get_summary": self.get_summary,
            "get_cost_breakdown": self.get_cost_breakdown,
            "get_performance_metrics": self.get_performance_metrics,
            "get_quality_metrics": self.get_quality_metrics,
            "get_health_score": self.get_health_score,
            "get_capability_breakdown": self.get_capability_breakdown,
            "export_prometheus": self.export_prometheus,
            "check_budget": self.check_budget,
            "reset_metrics": self.reset_metrics,
        }

        # Execute action
        if action_param in action_map:
            return await action_map[action_param](**kwargs)

        # Unknown action
        return CapabilityResult(
            capability=self.name,
            success=False,
            output={
                "error": f"Unknown action: {action_param}",
                "available_actions": list(action_map.keys()),
            },
        )

    async def track_capability_usage(
        self,
        capability: str,
        operation: str,
        latency_ms: float,
        success: bool = True,
        tokens_used: int | None = None,
        cost: float | None = None,
        error_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CapabilityResult:
        """Track capability usage with business metrics.

        Args:
            capability: Name of the capability (e.g., "vector_search")
            operation: Operation name (e.g., "search", "add_vector")
            latency_ms: Operation latency in milliseconds
            success: Whether operation succeeded
            tokens_used: Number of tokens used (if applicable)
            cost: Cost in USD (if applicable)
            error_type: Type of error if failed
            metadata: Additional metadata

        Returns:
            CapabilityResult with tracking confirmation
        """
        # Record in BusinessMetrics
        self._business_metrics.record_request(
            latency=latency_ms / 1000,  # Convert to seconds
            success=success,
            error_type=error_type,
        )

        # Track capability-specific metrics
        if self.config.track_capability_metrics:
            if capability not in self._capability_metrics:
                self._capability_metrics[capability] = {
                    "operations": {},
                    "total_calls": 0,
                    "total_latency_ms": 0.0,
                    "success_count": 0,
                    "error_count": 0,
                }

            cap_metrics = self._capability_metrics[capability]
            cap_metrics["total_calls"] += 1
            cap_metrics["total_latency_ms"] += latency_ms

            if success:
                cap_metrics["success_count"] += 1
            else:
                cap_metrics["error_count"] += 1

            # Track per-operation metrics
            if operation not in cap_metrics["operations"]:
                cap_metrics["operations"][operation] = {
                    "count": 0,
                    "latency_sum": 0.0,
                    "success": 0,
                    "errors": 0,
                }

            op_metrics = cap_metrics["operations"][operation]
            op_metrics["count"] += 1
            op_metrics["latency_sum"] += latency_ms
            if success:
                op_metrics["success"] += 1
            else:
                op_metrics["errors"] += 1

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={
                "tracked": True,
                "capability": capability,
                "operation": operation,
                "timestamp": datetime.now(UTC).isoformat(),
                "metadata": {
                    "latency_ms": latency_ms,
                    "success": success,
                    "tokens_used": tokens_used,
                    "cost": cost,
                    **(metadata or {}),
                },
            },
        )

    async def track_llm_call(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        success: bool = True,
        cost: float | None = None,
    ) -> CapabilityResult:
        """Track LLM API call metrics.

        Args:
            provider: LLM provider (e.g., "openai", "anthropic")
            model: Model name (e.g., "gpt-4", "claude-3-opus")
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            latency_ms: API call latency in milliseconds
            success: Whether call succeeded
            cost: Cost in USD (if known)

        Returns:
            CapabilityResult with tracking confirmation
        """
        total_tokens = prompt_tokens + completion_tokens

        # Track as capability usage
        return await self.track_capability_usage(
            capability="llm_provider",
            operation=f"{provider}/{model}",
            latency_ms=latency_ms,
            success=success,
            tokens_used=total_tokens,
            cost=cost,
            metadata={
                "provider": provider,
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            },
        )

    async def get_summary(self) -> CapabilityResult:
        """Get business metrics summary.

        Returns:
            CapabilityResult with complete business metrics
        """
        summary: BusinessMetricsSummary = self._business_metrics.get_summary()

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={
                "cost": {
                    "total_cost": summary.cost.total_cost,
                    "prompt_cost": summary.cost.prompt_cost,
                    "completion_cost": summary.cost.completion_cost,
                    "total_tokens": summary.cost.total_tokens,
                    "cost_per_request": summary.cost.cost_per_request,
                    "cost_per_1k_tokens": summary.cost.cost_per_1k_tokens,
                    "budget_status": summary.cost.budget_status,
                    "budget_usage_pct": summary.cost.budget_usage_pct,
                    "budget_remaining": summary.cost.budget_remaining,
                },
                "performance": {
                    "latency_p50": summary.performance.p50_latency,
                    "latency_p95": summary.performance.p95_latency,
                    "latency_p99": summary.performance.p99_latency,
                    "avg_latency": summary.performance.avg_latency,
                    "throughput_rps": summary.performance.requests_per_minute / 60,
                    "tokens_per_second": summary.performance.tokens_per_second,
                },
                "quality": {
                    "success_rate": summary.quality.success_rate,
                    "error_rate": summary.quality.error_rate,
                    "error_count": summary.quality.error_count,
                    "timeout_count": summary.quality.timeout_count,
                    "rate_limit_count": summary.quality.rate_limit_count,
                },
                "health_score": summary.health_score,
                "generated_at": summary.generated_at.isoformat(),
            },
        )

    async def get_cost_breakdown(self) -> CapabilityResult:
        """Get detailed cost breakdown.

        Returns:
            CapabilityResult with cost breakdown by model/provider
        """
        summary = self._business_metrics.get_summary()

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={
                "total_cost": summary.cost.total_cost,
                "prompt_cost": summary.cost.prompt_cost,
                "completion_cost": summary.cost.completion_cost,
                "total_tokens": summary.cost.total_tokens,
                "prompt_tokens": summary.cost.prompt_tokens,
                "completion_tokens": summary.cost.completion_tokens,
                "cost_per_request": summary.cost.cost_per_request,
                "cost_per_1k_tokens": summary.cost.cost_per_1k_tokens,
                "tokens_per_request": summary.cost.tokens_per_request,
                "request_count": summary.cost.request_count,
            },
        )

    async def get_performance_metrics(self) -> CapabilityResult:
        """Get performance metrics (latency, throughput).

        Returns:
            CapabilityResult with performance metrics
        """
        summary = self._business_metrics.get_summary()

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={
                "latency": {
                    "p50": summary.performance.p50_latency,
                    "p95": summary.performance.p95_latency,
                    "p99": summary.performance.p99_latency,
                    "avg": summary.performance.avg_latency,
                },
                "throughput": {
                    "requests_per_minute": (
                        summary.performance.requests_per_minute
                    ),
                    "tokens_per_second": (
                        summary.performance.tokens_per_second
                    ),
                },
            },
        )

    async def get_quality_metrics(self) -> CapabilityResult:
        """Get quality metrics (success rate, errors).

        Returns:
            CapabilityResult with quality metrics
        """
        summary = self._business_metrics.get_summary()

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={
                "success_rate": summary.quality.success_rate,
                "error_rate": summary.quality.error_rate,
                "error_count": summary.quality.error_count,
                "timeout_count": summary.quality.timeout_count,
                "rate_limit_count": summary.quality.rate_limit_count,
            },
        )

    async def get_health_score(self) -> CapabilityResult:
        """Get overall system health score (0.0-1.0).

        Health score is calculated from:
        - Success rate (40%)
        - Performance (30%)
        - Budget status (30%)

        Returns:
            CapabilityResult with health score
        """
        summary = self._business_metrics.get_summary()

        # Normalize health_score from 0-100 to 0.0-1.0
        normalized_score = summary.health_score / 100.0

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={
                "health_score": normalized_score,
                "status": (
                    "healthy"
                    if normalized_score >= 0.8
                    else "degraded" if normalized_score >= 0.5 else "unhealthy"
                ),
                "components": {
                    "success_rate": summary.quality.success_rate,
                    "latency_p95": summary.performance.p95_latency,
                    "budget_usage": summary.cost.budget_usage_pct,
                },
            },
        )

    async def get_capability_breakdown(self) -> CapabilityResult:
        """Get metrics breakdown by capability.

        Returns:
            CapabilityResult with per-capability metrics
        """
        breakdown = {}

        for capability, metrics in self._capability_metrics.items():
            avg_latency = (
                metrics["total_latency_ms"] / metrics["total_calls"]
                if metrics["total_calls"] > 0
                else 0.0
            )

            breakdown[capability] = {
                "total_calls": metrics["total_calls"],
                "avg_latency_ms": avg_latency,
                "success_rate": (
                    metrics["success_count"] / metrics["total_calls"]
                    if metrics["total_calls"] > 0
                    else 0.0
                ),
                "error_count": metrics["error_count"],
                "operations": {},
            }

            # Add per-operation breakdown
            for operation, op_metrics in metrics["operations"].items():
                op_avg_latency = (
                    op_metrics["latency_sum"] / op_metrics["count"]
                    if op_metrics["count"] > 0
                    else 0.0
                )

                breakdown[capability]["operations"][operation] = {
                    "count": op_metrics["count"],
                    "avg_latency_ms": op_avg_latency,
                    "success_rate": (
                        op_metrics["success"] / op_metrics["count"]
                        if op_metrics["count"] > 0
                        else 0.0
                    ),
                }

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={
                "capabilities": breakdown,
                "total_capabilities": len(breakdown),
            },
        )

    async def export_prometheus(self) -> CapabilityResult:
        """Export metrics in Prometheus format.

        Returns:
            CapabilityResult with Prometheus metrics text
        """
        if not self.config.enable_prometheus:
            return CapabilityResult(
                capability=self.name,
                success=False,
                output={"error": "Prometheus export is disabled"},
            )

        # BusinessMetrics already integrates with PrometheusRegistry
        # The metrics are automatically exported
        prometheus_text = self._business_metrics.prometheus.export_text()

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={
                "prometheus_metrics": prometheus_text,
                "format": "text/plain; version=0.0.4",
            },
        )

    async def check_budget(self) -> CapabilityResult:
        """Check budget status and alerts.

        Returns:
            CapabilityResult with budget status and alerts
        """
        summary = self._business_metrics.get_summary()

        alerts = []

        # Check if budget threshold exceeded
        if summary.cost.budget_usage_pct >= self.config.alert_on_budget_threshold:
            alerts.append(
                {
                    "severity": "warning"
                    if summary.cost.budget_usage_pct < 1.0
                    else "critical",
                    "message": f"Budget usage at {summary.cost.budget_usage_pct * 100:.1f}%",
                    "threshold": self.config.alert_on_budget_threshold,
                    "current": summary.cost.budget_usage_pct,
                }
            )

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={
                "budget_status": summary.cost.budget_status,
                "usage_pct": summary.cost.budget_usage_pct,
                "remaining": summary.cost.budget_remaining,
                "total_cost": summary.cost.total_cost,
                "alerts": alerts,
                "needs_attention": len(alerts) > 0,
            },
        )

    async def reset_metrics(self) -> CapabilityResult:
        """Reset all metrics (for testing/debugging).

        Returns:
            CapabilityResult with reset confirmation
        """
        # Reset capability-specific metrics
        self._capability_metrics.clear()
        self._start_time = datetime.now(UTC)

        # Note: BusinessMetrics doesn't expose a reset method
        # This only resets capability-specific tracking
        return CapabilityResult(
            capability=self.name,
            success=True,
            output={
                "reset": True,
                "timestamp": self._start_time.isoformat(),
                "note": "Capability-specific metrics reset. BusinessMetrics state unchanged.",
            },
        )
