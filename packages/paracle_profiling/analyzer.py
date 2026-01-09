"""Performance analyzer for identifying bottlenecks."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from paracle_profiling.profiler import Profiler

logger = logging.getLogger(__name__)


@dataclass
class BottleneckReport:
    """Report of performance bottlenecks."""

    name: str
    avg_time: float
    max_time: float
    p95_time: float
    calls: int
    total_time: float
    percentage_of_total: float
    severity: str  # "critical", "high", "medium", "low"

    def __str__(self) -> str:
        """String representation."""
        return (
            f"{self.name}: avg={self.avg_time:.3f}s, "
            f"p95={self.p95_time:.3f}s, calls={self.calls}, "
            f"severity={self.severity}"
        )


class PerformanceAnalyzer:
    """Analyze performance data and identify bottlenecks."""

    # Severity thresholds (in seconds)
    CRITICAL_THRESHOLD = 2.0  # > 2s average
    HIGH_THRESHOLD = 1.0  # > 1s average
    MEDIUM_THRESHOLD = 0.5  # > 500ms average
    LOW_THRESHOLD = 0.1  # > 100ms average

    @classmethod
    def analyze_bottlenecks(
        cls,
        top_n: int = 10,
        min_calls: int = 5,
    ) -> list[BottleneckReport]:
        """Identify performance bottlenecks.

        Args:
            top_n: Return top N bottlenecks
            min_calls: Minimum calls required for analysis

        Returns:
            List of bottleneck reports sorted by severity
        """
        stats = Profiler.get_stats()
        bottlenecks = []

        # Calculate total time across all profiled functions
        total_time = sum(sum(e.duration for e in entries) for entries in stats.values())

        if total_time == 0:
            return []

        # Analyze each function
        for name, entries in stats.items():
            if len(entries) < min_calls:
                continue

            durations = [e.duration for e in entries]
            avg_time = sum(durations) / len(durations)
            max_time = max(durations)
            sorted_durations = sorted(durations)
            p95_time = sorted_durations[int(len(durations) * 0.95)]
            function_total_time = sum(durations)
            percentage = (function_total_time / total_time) * 100

            # Determine severity
            if avg_time >= cls.CRITICAL_THRESHOLD:
                severity = "critical"
            elif avg_time >= cls.HIGH_THRESHOLD:
                severity = "high"
            elif avg_time >= cls.MEDIUM_THRESHOLD:
                severity = "medium"
            elif avg_time >= cls.LOW_THRESHOLD:
                severity = "low"
            else:
                continue  # Skip fast functions

            bottlenecks.append(
                BottleneckReport(
                    name=name,
                    avg_time=avg_time,
                    max_time=max_time,
                    p95_time=p95_time,
                    calls=len(entries),
                    total_time=function_total_time,
                    percentage_of_total=percentage,
                    severity=severity,
                )
            )

        # Sort by severity and then by total time
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        bottlenecks.sort(key=lambda x: (severity_order[x.severity], -x.total_time))

        return bottlenecks[:top_n]

    @classmethod
    def generate_report(
        cls,
        top_n: int = 10,
        min_calls: int = 5,
    ) -> str:
        """Generate a text report of bottlenecks.

        Args:
            top_n: Number of bottlenecks to include
            min_calls: Minimum calls for analysis

        Returns:
            Formatted text report
        """
        bottlenecks = cls.analyze_bottlenecks(top_n, min_calls)

        if not bottlenecks:
            return "No bottlenecks found. All operations are performing well!"

        report_lines = [
            "=" * 80,
            "PERFORMANCE BOTTLENECK REPORT",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total bottlenecks: {len(bottlenecks)}",
            "",
        ]

        # Group by severity
        for severity in ["critical", "high", "medium", "low"]:
            severity_bottlenecks = [b for b in bottlenecks if b.severity == severity]
            if not severity_bottlenecks:
                continue

            report_lines.append(
                f"\n{severity.upper()} SEVERITY ({len(severity_bottlenecks)}):"
            )
            report_lines.append("-" * 80)

            for bottleneck in severity_bottlenecks:
                report_lines.extend(
                    [
                        f"\nFunction: {bottleneck.name}",
                        f"  Average Time: {bottleneck.avg_time:.3f}s",
                        f"  P95 Time:     {bottleneck.p95_time:.3f}s",
                        f"  Max Time:     {bottleneck.max_time:.3f}s",
                        f"  Total Calls:  {bottleneck.calls}",
                        f"  Total Time:   {bottleneck.total_time:.3f}s ({bottleneck.percentage_of_total:.1f}% of total)",
                    ]
                )

        report_lines.extend(
            [
                "",
                "=" * 80,
                "RECOMMENDATIONS:",
                "=" * 80,
                "",
                "CRITICAL (> 2s avg):",
                "  - Immediate optimization required",
                "  - Consider caching, async processing, or algorithm improvement",
                "",
                "HIGH (> 1s avg):",
                "  - High priority optimization",
                "  - Profile to identify hotspots within function",
                "",
                "MEDIUM (> 500ms avg):",
                "  - Optimization recommended",
                "  - Check for database N+1 queries, API calls, or expensive computations",
                "",
                "LOW (> 100ms avg):",
                "  - Monitor for degradation",
                "  - Optimize if called frequently",
                "",
                "=" * 80,
            ]
        )

        return "\n".join(report_lines)

    @classmethod
    def get_slowest_endpoints(cls, top_n: int = 10) -> list[dict[str, Any]]:
        """Get slowest profiled functions.

        Args:
            top_n: Number of results to return

        Returns:
            List of slowest functions with stats
        """
        summaries = []
        for name in Profiler.get_stats().keys():
            summary = Profiler.get_summary(name)
            if summary:
                summaries.append(summary)

        # Sort by average time
        summaries.sort(key=lambda x: x.get("avg_time", 0), reverse=True)

        return summaries[:top_n]

    @classmethod
    def check_targets(cls) -> dict[str, bool]:
        """Check if performance targets are met.

        Targets (from Phase 8 roadmap):
        - API latency (p95): < 500ms
        - API latency (p99): < 1000ms
        - Throughput: > 1000 requests/second

        Returns:
            Dictionary of target checks
        """
        summaries = []
        for name in Profiler.get_stats().keys():
            summary = Profiler.get_summary(name)
            if summary and "p95_time" in summary:
                summaries.append(summary)

        if not summaries:
            return {
                "p95_under_500ms": None,
                "p99_under_1000ms": None,
                "avg_under_100ms": None,
            }

        # Calculate overall stats
        all_p95 = [s["p95_time"] for s in summaries]
        all_p99 = [s["p99_time"] for s in summaries]
        all_avg = [s["avg_time"] for s in summaries]

        return {
            "p95_under_500ms": max(all_p95) < 0.5 if all_p95 else None,
            "p99_under_1000ms": max(all_p99) < 1.0 if all_p99 else None,
            "avg_under_100ms": max(all_avg) < 0.1 if all_avg else None,
            "worst_p95": max(all_p95) if all_p95 else None,
            "worst_p99": max(all_p99) if all_p99 else None,
            "worst_avg": max(all_avg) if all_avg else None,
        }
