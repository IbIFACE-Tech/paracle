"""Error dashboard for visualizing error trends and patterns.

This module provides error visualization, trend analysis, and dashboard
generation capabilities.

Example:
    >>> from paracle_observability import ErrorDashboard, get_error_registry
    >>>
    >>> registry = get_error_registry()
    >>> dashboard = ErrorDashboard(registry)
    >>>
    >>> # Generate error timeline
    >>> timeline = dashboard.generate_error_timeline(hours=24)
    >>>
    >>> # Get top errors chart data
    >>> top_errors = dashboard.generate_top_errors_chart(limit=10)
    >>>
    >>> # Component error distribution
    >>> distribution = dashboard.generate_component_distribution()
"""

import time
from collections import defaultdict
from datetime import datetime
from typing import Any

from paracle_observability.error_registry import ErrorRegistry


class ErrorDashboard:
    """Error visualization and dashboard generation.

    Generates charts, timelines, and visual representations of error data
    for monitoring and analysis.

    Attributes:
        registry: ErrorRegistry instance
        chart_data: Cached chart data
    """

    def __init__(self, registry: ErrorRegistry):
        """Initialize error dashboard.

        Args:
            registry: ErrorRegistry instance
        """
        self.registry = registry
        self.chart_data: dict[str, Any] = {}

    def generate_error_timeline(
        self,
        hours: int = 24,
        bucket_size_minutes: int = 60,
    ) -> dict[str, Any]:
        """Generate error timeline chart data.

        Args:
            hours: Hours of history to include
            bucket_size_minutes: Time bucket size in minutes

        Returns:
            Timeline chart data with timestamps and counts
        """
        cutoff_time = time.time() - (hours * 3600)
        errors = self.registry.get_errors(since=cutoff_time)

        # Create time buckets
        buckets: dict[int, int] = defaultdict(int)
        bucket_size_seconds = bucket_size_minutes * 60

        for error in errors:
            bucket = int(error.timestamp // bucket_size_seconds)
            buckets[bucket] += 1

        # Convert to sorted list
        timeline = [
            {
                "timestamp": bucket * bucket_size_seconds,
                "datetime": datetime.fromtimestamp(
                    bucket * bucket_size_seconds
                ).isoformat(),
                "count": count,
            }
            for bucket, count in sorted(buckets.items())
        ]

        return {
            "type": "timeline",
            "title": f"Error Timeline ({hours}h)",
            "bucket_size_minutes": bucket_size_minutes,
            "data": timeline,
            "total_errors": len(errors),
        }

    def generate_top_errors_chart(self, limit: int = 10) -> dict[str, Any]:
        """Generate top errors bar chart data.

        Args:
            limit: Number of top errors to include

        Returns:
            Top errors chart data
        """
        stats = self.registry.get_statistics()
        top_errors = stats["top_error_types"][:limit]

        return {
            "type": "bar_chart",
            "title": f"Top {limit} Errors",
            "data": [
                {"label": item["type"], "value": item["count"]} for item in top_errors
            ],
        }

    def generate_component_distribution(self) -> dict[str, Any]:
        """Generate component error distribution pie chart data.

        Returns:
            Component distribution chart data
        """
        stats = self.registry.get_statistics()
        top_components = stats["top_components"]

        return {
            "type": "pie_chart",
            "title": "Errors by Component",
            "data": [
                {"label": item["component"], "value": item["count"]}
                for item in top_components
            ],
        }

    def generate_severity_breakdown(self) -> dict[str, Any]:
        """Generate severity breakdown chart data.

        Returns:
            Severity breakdown chart data
        """
        stats = self.registry.get_statistics()
        severity_breakdown = stats["severity_breakdown"]

        return {
            "type": "pie_chart",
            "title": "Errors by Severity",
            "data": [
                {"label": severity, "value": count}
                for severity, count in severity_breakdown.items()
            ],
        }

    def generate_error_rate_trend(self, hours: int = 24) -> dict[str, Any]:
        """Generate error rate trend chart data.

        Args:
            hours: Hours of history to analyze

        Returns:
            Error rate trend data (errors per minute over time)
        """
        cutoff_time = time.time() - (hours * 3600)
        errors = self.registry.get_errors(since=cutoff_time)

        # Calculate error rate per 5-minute window
        buckets: dict[int, int] = defaultdict(int)
        bucket_size = 300  # 5 minutes in seconds

        for error in errors:
            bucket = int(error.timestamp // bucket_size)
            buckets[bucket] += 1

        # Convert to error rate (errors per minute)
        trend = [
            {
                "timestamp": bucket * bucket_size,
                "datetime": datetime.fromtimestamp(bucket * bucket_size).isoformat(),
                "error_rate": count / 5.0,  # errors per minute
            }
            for bucket, count in sorted(buckets.items())
        ]

        return {
            "type": "line_chart",
            "title": f"Error Rate Trend ({hours}h)",
            "unit": "errors/minute",
            "data": trend,
        }

    def generate_pattern_alerts(self) -> dict[str, Any]:
        """Generate pattern alerts data.

        Returns:
            Pattern alerts for display
        """
        patterns = self.registry.get_patterns()

        return {
            "type": "alerts",
            "title": "Error Pattern Alerts",
            "count": len(patterns),
            "data": [
                {
                    "pattern_type": p["pattern_type"],
                    "description": self._format_pattern_description(p),
                    "severity": self._pattern_severity(p),
                    "detected_at": datetime.fromtimestamp(p["detected_at"]).isoformat(),
                }
                for p in patterns
            ],
        }

    def _format_pattern_description(self, pattern: dict[str, Any]) -> str:
        """Format pattern description for display.

        Args:
            pattern: Pattern dictionary

        Returns:
            Formatted description
        """
        if pattern["pattern_type"] == "high_frequency":
            return (
                f"High frequency of {pattern['error_type']} errors: "
                f"{pattern['count']} in {pattern['time_window']}"
            )
        elif pattern["pattern_type"] == "cascading":
            return (
                f"Cascading errors in {pattern['component']}: "
                f"{pattern['count']} errors in {pattern['time_window']}"
            )
        return f"Unknown pattern: {pattern['pattern_type']}"

    def _pattern_severity(self, pattern: dict[str, Any]) -> str:
        """Determine pattern severity.

        Args:
            pattern: Pattern dictionary

        Returns:
            Severity level (warning, error, critical)
        """
        count = pattern.get("count", 0)

        if count >= 50:
            return "critical"
        elif count >= 20:
            return "error"
        else:
            return "warning"

    def generate_full_dashboard(
        self,
        hours: int = 24,
        top_errors_limit: int = 10,
    ) -> dict[str, Any]:
        """Generate complete dashboard data.

        Args:
            hours: Hours of history for timeline
            top_errors_limit: Number of top errors to show

        Returns:
            Complete dashboard data with all charts
        """
        return {
            "generated_at": datetime.now().isoformat(),
            "time_range_hours": hours,
            "summary": self.registry.get_statistics(),
            "charts": {
                "timeline": self.generate_error_timeline(hours=hours),
                "top_errors": self.generate_top_errors_chart(limit=top_errors_limit),
                "component_distribution": self.generate_component_distribution(),
                "severity_breakdown": self.generate_severity_breakdown(),
                "error_rate_trend": self.generate_error_rate_trend(hours=hours),
                "pattern_alerts": self.generate_pattern_alerts(),
            },
        }

    def get_anomalies(
        self,
        threshold_multiplier: float = 3.0,
        hours: int = 24,
    ) -> list[dict[str, Any]]:
        """Detect error rate anomalies.

        Args:
            threshold_multiplier: Multiplier for baseline (e.g., 3x normal)
            hours: Hours of history to analyze

        Returns:
            List of anomaly periods
        """
        cutoff_time = time.time() - (hours * 3600)
        errors = self.registry.get_errors(since=cutoff_time)

        # Calculate error rate per 5-minute window
        buckets: dict[int, int] = defaultdict(int)
        bucket_size = 300  # 5 minutes

        for error in errors:
            bucket = int(error.timestamp // bucket_size)
            buckets[bucket] += 1

        if not buckets:
            return []

        # Calculate baseline (average error rate)
        baseline = sum(buckets.values()) / len(buckets)
        threshold = baseline * threshold_multiplier

        # Find anomalies
        anomalies = []
        for bucket, count in sorted(buckets.items()):
            if count > threshold:
                anomalies.append(
                    {
                        "timestamp": bucket * bucket_size,
                        "datetime": datetime.fromtimestamp(
                            bucket * bucket_size
                        ).isoformat(),
                        "error_count": count,
                        "baseline": baseline,
                        "threshold": threshold,
                        "severity": "high" if count > threshold * 2 else "medium",
                    }
                )

        return anomalies

    def generate_health_score(self) -> dict[str, Any]:
        """Calculate system health score based on errors.

        Returns:
            Health score (0-100) and details
        """
        stats = self.registry.get_statistics()

        # Start with perfect score
        score = 100.0
        factors = []

        # Factor 1: Recent error rate
        error_rate = stats.get("error_rate_per_minute", 0)
        if error_rate > 10:
            deduction = min(30, error_rate * 2)
            score -= deduction
            factors.append(
                {
                    "factor": "high_error_rate",
                    "deduction": deduction,
                    "value": error_rate,
                }
            )
        elif error_rate > 5:
            deduction = error_rate
            score -= deduction
            factors.append(
                {
                    "factor": "elevated_error_rate",
                    "deduction": deduction,
                    "value": error_rate,
                }
            )

        # Factor 2: Critical errors
        severity_breakdown = stats.get("severity_breakdown", {})
        critical_count = severity_breakdown.get("critical", 0)
        if critical_count > 0:
            deduction = min(40, critical_count * 10)
            score -= deduction
            factors.append(
                {
                    "factor": "critical_errors",
                    "deduction": deduction,
                    "value": critical_count,
                }
            )

        # Factor 3: Patterns detected
        patterns_count = stats.get("patterns_detected", 0)
        if patterns_count > 0:
            deduction = min(20, patterns_count * 5)
            score -= deduction
            factors.append(
                {
                    "factor": "error_patterns",
                    "deduction": deduction,
                    "value": patterns_count,
                }
            )

        score = max(0, score)  # Clamp to 0

        # Determine health status
        if score >= 90:
            status = "excellent"
        elif score >= 70:
            status = "good"
        elif score >= 50:
            status = "fair"
        elif score >= 30:
            status = "poor"
        else:
            status = "critical"

        return {
            "score": round(score, 1),
            "status": status,
            "factors": factors,
            "recommendation": self._get_health_recommendation(status, factors),
        }

    def _get_health_recommendation(
        self,
        status: str,
        factors: list[dict[str, Any]],
    ) -> str:
        """Get health recommendation based on status.

        Args:
            status: Health status
            factors: Factors affecting score

        Returns:
            Recommendation message
        """
        if status == "excellent":
            return "System error health is excellent. Continue monitoring."

        if status == "critical":
            return "URGENT: System is experiencing critical errors. Immediate action required."

        # Build recommendation from factors
        recommendations = []
        for factor in factors:
            if factor["factor"] == "high_error_rate":
                recommendations.append(
                    "Reduce error rate by fixing high-frequency issues"
                )
            elif factor["factor"] == "critical_errors":
                recommendations.append("Address critical errors immediately")
            elif factor["factor"] == "error_patterns":
                recommendations.append("Investigate detected error patterns")

        if recommendations:
            return "Recommended actions: " + "; ".join(recommendations)

        return "Monitor error trends and address emerging issues."
