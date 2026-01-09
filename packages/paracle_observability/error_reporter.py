"""Automated error reporting and trend analysis.

This module provides automated error reporting, trend analysis, and
anomaly detection capabilities.

Example:
    >>> from paracle_observability import AutomatedErrorReporter, get_error_registry
    >>>
    >>> registry = get_error_registry()
    >>> reporter = AutomatedErrorReporter(registry)
    >>>
    >>> # Generate daily summary
    >>> summary = reporter.generate_daily_summary()
    >>>
    >>> # Generate weekly report
    >>> report = reporter.generate_weekly_report()
    >>>
    >>> # Check for anomalies
    >>> anomalies = reporter.detect_anomalies()
"""

import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from paracle_observability.error_registry import ErrorRegistry


class AutomatedErrorReporter:
    """Automated error reporting and trend analysis.

    Generates periodic reports, detects trends, and identifies anomalies
    in error patterns.

    Attributes:
        registry: ErrorRegistry instance
        baseline_window: Time window for baseline calculation (seconds)
    """

    def __init__(
        self,
        registry: ErrorRegistry,
        baseline_window: int = 3600 * 24 * 7,  # 1 week
    ):
        """Initialize automated error reporter.

        Args:
            registry: ErrorRegistry instance
            baseline_window: Baseline calculation window in seconds
        """
        self.registry = registry
        self.baseline_window = baseline_window

    def generate_daily_summary(self, date: datetime | None = None) -> dict[str, Any]:
        """Generate daily error summary.

        Args:
            date: Date for summary (default: today)

        Returns:
            Daily summary report
        """
        if date is None:
            date = datetime.now()

        # Get errors for the day
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        errors = self.registry.get_errors(since=start_of_day.timestamp())
        errors = [e for e in errors if e.timestamp < end_of_day.timestamp()]

        # Count by type
        error_counts: dict[str, int] = defaultdict(int)
        component_counts: dict[str, int] = defaultdict(int)
        severity_counts: dict[str, int] = defaultdict(int)

        for error in errors:
            error_counts[error.error_type] += 1
            component_counts[error.component] += 1
            severity_counts[error.severity.value] += 1

        # Top errors
        top_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Top components
        top_components = sorted(
            component_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]

        return {
            "report_type": "daily_summary",
            "date": date.date().isoformat(),
            "generated_at": datetime.now().isoformat(),
            "total_errors": len(errors),
            "unique_error_types": len(error_counts),
            "affected_components": len(component_counts),
            "severity_breakdown": dict(severity_counts),
            "top_errors": [{"error_type": t, "count": c} for t, c in top_errors],
            "top_components": [
                {"component": comp, "count": c} for comp, c in top_components
            ],
            "critical_errors": severity_counts.get("critical", 0),
            "warnings": severity_counts.get("warning", 0),
        }

    def generate_weekly_report(
        self,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Generate weekly error report.

        Args:
            end_date: End date for report (default: today)

        Returns:
            Weekly report with trends
        """
        if end_date is None:
            end_date = datetime.now()

        start_date = end_date - timedelta(days=7)

        errors = self.registry.get_errors(since=start_date.timestamp())

        # Daily breakdown
        daily_counts: dict[str, int] = defaultdict(int)
        for error in errors:
            date = datetime.fromtimestamp(error.timestamp).date().isoformat()
            daily_counts[date] += 1

        # Component analysis
        component_counts: dict[str, int] = defaultdict(int)
        for error in errors:
            component_counts[error.component] += 1

        # Error type analysis
        error_type_counts: dict[str, int] = defaultdict(int)
        for error in errors:
            error_type_counts[error.error_type] += 1

        # Severity analysis
        severity_counts: dict[str, int] = defaultdict(int)
        for error in errors:
            severity_counts[error.severity.value] += 1

        # Trend analysis
        trend = self._analyze_trend(daily_counts)

        return {
            "report_type": "weekly_report",
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat(),
            "generated_at": datetime.now().isoformat(),
            "total_errors": len(errors),
            "daily_average": len(errors) / 7.0,
            "daily_breakdown": [
                {"date": date, "count": count}
                for date, count in sorted(daily_counts.items())
            ],
            "trend": trend,
            "top_components": [
                {"component": comp, "count": count}
                for comp, count in sorted(
                    component_counts.items(), key=lambda x: x[1], reverse=True
                )[:10]
            ],
            "top_error_types": [
                {"error_type": etype, "count": count}
                for etype, count in sorted(
                    error_type_counts.items(), key=lambda x: x[1], reverse=True
                )[:10]
            ],
            "severity_breakdown": dict(severity_counts),
        }

    def _analyze_trend(self, daily_counts: dict[str, int]) -> dict[str, Any]:
        """Analyze error trend.

        Args:
            daily_counts: Daily error counts

        Returns:
            Trend analysis
        """
        if len(daily_counts) < 2:
            return {"direction": "stable", "change_percent": 0.0}

        sorted_dates = sorted(daily_counts.items())
        first_half_avg = sum(c for _, c in sorted_dates[:3]) / 3.0
        second_half_avg = sum(c for _, c in sorted_dates[-3:]) / 3.0

        if first_half_avg == 0:
            change_percent = 100.0 if second_half_avg > 0 else 0.0
        else:
            change_percent = ((second_half_avg - first_half_avg) / first_half_avg) * 100

        if change_percent > 20:
            direction = "increasing"
        elif change_percent < -20:
            direction = "decreasing"
        else:
            direction = "stable"

        return {
            "direction": direction,
            "change_percent": round(change_percent, 1),
            "first_half_avg": round(first_half_avg, 1),
            "second_half_avg": round(second_half_avg, 1),
        }

    def detect_anomalies(
        self,
        threshold_std_dev: float = 2.0,
        hours: int = 24,
    ) -> list[dict[str, Any]]:
        """Detect error rate anomalies using statistical analysis.

        Args:
            threshold_std_dev: Standard deviation threshold
            hours: Hours of history to analyze

        Returns:
            List of anomalies detected
        """
        cutoff_time = time.time() - (hours * 3600)
        errors = self.registry.get_errors(since=cutoff_time)

        # Calculate error rate per 5-minute window
        buckets: dict[int, int] = defaultdict(int)
        bucket_size = 300  # 5 minutes

        for error in errors:
            bucket = int(error.timestamp // bucket_size)
            buckets[bucket] += 1

        if len(buckets) < 2:
            return []

        # Calculate mean and standard deviation
        counts = list(buckets.values())
        mean = sum(counts) / len(counts)
        variance = sum((x - mean) ** 2 for x in counts) / len(counts)
        std_dev = variance**0.5

        threshold = mean + (threshold_std_dev * std_dev)

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
                        "baseline_mean": round(mean, 2),
                        "threshold": round(threshold, 2),
                        "std_dev_above": round((count - mean) / std_dev, 2),
                    }
                )

        return anomalies

    def generate_incident_report(
        self,
        start_time: float,
        end_time: float,
        title: str = "Error Incident",
    ) -> dict[str, Any]:
        """Generate incident report for a time period.

        Args:
            start_time: Incident start timestamp
            end_time: Incident end timestamp
            title: Incident title

        Returns:
            Incident report
        """
        # Get errors in time range
        all_errors = self.registry.get_errors(since=start_time)
        errors = [e for e in all_errors if e.timestamp <= end_time]

        # Analyze errors
        error_types: dict[str, int] = defaultdict(int)
        components: dict[str, int] = defaultdict(int)
        severity_counts: dict[str, int] = defaultdict(int)

        for error in errors:
            error_types[error.error_type] += 1
            components[error.component] += 1
            severity_counts[error.severity.value] += 1

        # Timeline (5-minute buckets)
        timeline: dict[int, int] = defaultdict(int)
        bucket_size = 300
        for error in errors:
            bucket = int(error.timestamp // bucket_size)
            timeline[bucket] += 1

        return {
            "report_type": "incident_report",
            "title": title,
            "start_time": datetime.fromtimestamp(start_time).isoformat(),
            "end_time": datetime.fromtimestamp(end_time).isoformat(),
            "duration_minutes": round((end_time - start_time) / 60, 1),
            "generated_at": datetime.now().isoformat(),
            "total_errors": len(errors),
            "peak_error_rate": max(timeline.values()) if timeline else 0,
            "affected_components": list(components.keys()),
            "primary_error_types": [
                {"error_type": t, "count": c}
                for t, c in sorted(
                    error_types.items(), key=lambda x: x[1], reverse=True
                )[:5]
            ],
            "severity_breakdown": dict(severity_counts),
            "timeline": [
                {
                    "timestamp": bucket * bucket_size,
                    "datetime": datetime.fromtimestamp(
                        bucket * bucket_size
                    ).isoformat(),
                    "count": count,
                }
                for bucket, count in sorted(timeline.items())
            ],
        }

    def generate_component_health_report(self) -> dict[str, Any]:
        """Generate health report for all components.

        Returns:
            Component health report
        """
        stats = self.registry.get_statistics()
        top_components = stats["top_components"]

        # Calculate health score per component
        component_health = []
        for item in top_components:
            component = item["component"]
            error_count = item["count"]

            # Get component errors
            component_errors = self.registry.get_errors_by_component(component)

            # Calculate health score (inverse of error rate)
            # 100 = no errors, 0 = many errors
            if error_count == 0:
                health_score = 100
            elif error_count < 10:
                health_score = 90
            elif error_count < 50:
                health_score = 70
            elif error_count < 100:
                health_score = 50
            else:
                health_score = max(0, 100 - error_count)

            # Check for recent errors (last hour)
            one_hour_ago = time.time() - 3600
            recent_errors = [e for e in component_errors if e.timestamp >= one_hour_ago]

            component_health.append(
                {
                    "component": component,
                    "health_score": health_score,
                    "total_errors": error_count,
                    "recent_errors_1h": len(recent_errors),
                    "status": self._health_status(health_score),
                }
            )

        return {
            "report_type": "component_health",
            "generated_at": datetime.now().isoformat(),
            "components": component_health,
        }

    def _health_status(self, score: int) -> str:
        """Convert health score to status.

        Args:
            score: Health score (0-100)

        Returns:
            Status string
        """
        if score >= 90:
            return "healthy"
        elif score >= 70:
            return "degraded"
        elif score >= 50:
            return "unhealthy"
        else:
            return "critical"

    def should_alert(
        self,
        error_rate_threshold: float = 5.0,
        critical_error_threshold: int = 1,
    ) -> dict[str, Any]:
        """Determine if alerts should be triggered.

        Args:
            error_rate_threshold: Errors per minute threshold
            critical_error_threshold: Critical error count threshold

        Returns:
            Alert decision and details
        """
        stats = self.registry.get_statistics()
        patterns = self.registry.get_patterns()

        alerts = []

        # Check error rate
        error_rate = stats.get("error_rate_per_minute", 0)
        if error_rate > error_rate_threshold:
            alerts.append(
                {
                    "type": "high_error_rate",
                    "severity": "warning",
                    "message": f"Error rate {error_rate:.1f}/min exceeds threshold {error_rate_threshold}/min",
                    "value": error_rate,
                }
            )

        # Check critical errors
        severity_breakdown = stats.get("severity_breakdown", {})
        critical_count = severity_breakdown.get("critical", 0)
        if critical_count >= critical_error_threshold:
            alerts.append(
                {
                    "type": "critical_errors",
                    "severity": "critical",
                    "message": f"{critical_count} critical error(s) detected",
                    "value": critical_count,
                }
            )

        # Check patterns
        if len(patterns) > 0:
            alerts.append(
                {
                    "type": "error_patterns",
                    "severity": "warning",
                    "message": f"{len(patterns)} error pattern(s) detected",
                    "patterns": patterns,
                }
            )

        return {
            "should_alert": len(alerts) > 0,
            "alert_count": len(alerts),
            "alerts": alerts,
        }
