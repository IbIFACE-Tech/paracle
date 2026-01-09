"""Prometheus metrics integration for Paracle.

Provides Prometheus-compatible metrics export for monitoring:
- Counters (monotonically increasing values)
- Gauges (arbitrary values that can go up/down)
- Histograms (distributions with buckets)
- Summary (quantiles)
"""

import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any


class MetricType:
    """Prometheus metric types."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """Base metric class."""

    name: str
    type: MetricType
    help: str
    labels: dict[str, str]
    value: float
    timestamp: float


class PrometheusRegistry:
    """Registry for Prometheus metrics.

    Stores all metrics and provides export functionality.
    """

    def __init__(self):
        self._metrics: dict[str, dict[str, Any]] = defaultdict(dict)
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)

    def counter(
        self,
        name: str,
        help: str = "",
        labels: dict[str, str] | None = None,
    ) -> "Counter":
        """Create or get a counter metric."""
        labels = labels or {}
        key = f"{name}_{self._label_key(labels)}"
        if key not in self._metrics:
            self._metrics[key] = {
                "name": name,
                "type": MetricType.COUNTER,
                "help": help,
                "labels": labels,
            }
        return Counter(self, name, labels)

    def gauge(
        self,
        name: str,
        help: str = "",
        labels: dict[str, str] | None = None,
    ) -> "Gauge":
        """Create or get a gauge metric."""
        labels = labels or {}
        key = f"{name}_{self._label_key(labels)}"
        if key not in self._metrics:
            self._metrics[key] = {
                "name": name,
                "type": MetricType.GAUGE,
                "help": help,
                "labels": labels,
            }
        return Gauge(self, name, labels)

    def histogram(
        self,
        name: str,
        help: str = "",
        labels: dict[str, str] | None = None,
        buckets: list[float] | None = None,
    ) -> "Histogram":
        """Create or get a histogram metric."""
        labels = labels or {}
        buckets = buckets or [
            0.005,
            0.01,
            0.025,
            0.05,
            0.1,
            0.25,
            0.5,
            1.0,
            2.5,
            5.0,
            10.0,
        ]
        key = f"{name}_{self._label_key(labels)}"
        if key not in self._metrics:
            self._metrics[key] = {
                "name": name,
                "type": MetricType.HISTOGRAM,
                "help": help,
                "labels": labels,
                "buckets": buckets,
            }
        return Histogram(self, name, labels, buckets)

    def _label_key(self, labels: dict[str, str]) -> str:
        """Generate key from labels."""
        return "_".join(f"{k}={v}" for k, v in sorted(labels.items()))

    def export_text(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []

        for key, meta in self._metrics.items():
            name = meta["name"]
            metric_type = meta["type"]
            help_text = meta["help"]
            labels = meta["labels"]

            # Add help and type
            lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} {metric_type}")

            # Add metric value
            label_str = self._format_labels(labels)
            if metric_type == MetricType.COUNTER:
                value = self._counters.get(key, 0.0)
                lines.append(f"{name}{label_str} {value}")
            elif metric_type == MetricType.GAUGE:
                value = self._gauges.get(key, 0.0)
                lines.append(f"{name}{label_str} {value}")
            elif metric_type == MetricType.HISTOGRAM:
                values = self._histograms.get(key, [])
                buckets = meta.get("buckets", [])
                lines.extend(self._format_histogram(name, label_str, values, buckets))

        return "\n".join(lines) + "\n"

    def _format_labels(self, labels: dict[str, str]) -> str:
        """Format labels for Prometheus output."""
        if not labels:
            return ""
        label_pairs = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{{{label_pairs}}}"

    def _format_histogram(
        self,
        name: str,
        label_str: str,
        values: list[float],
        buckets: list[float],
    ) -> list[str]:
        """Format histogram for Prometheus output."""
        lines = []
        count = len(values)
        total = sum(values)

        # Buckets
        for bucket in buckets:
            bucket_count = sum(1 for v in values if v <= bucket)
            lines.append(f'{name}_bucket{label_str},le="{bucket}"}} {bucket_count}')

        # +Inf bucket
        lines.append(f'{name}_bucket{label_str},le="+Inf"}} {count}')

        # Sum and count
        lines.append(f"{name}_sum{label_str} {total}")
        lines.append(f"{name}_count{label_str} {count}")

        return lines


class Counter:
    """Counter metric (monotonically increasing)."""

    def __init__(self, registry: PrometheusRegistry, name: str, labels: dict[str, str]):
        self.registry = registry
        self.name = name
        self.labels = labels
        self.key = f"{name}_{registry._label_key(labels)}"

    def inc(self, amount: float = 1.0):
        """Increment counter."""
        self.registry._counters[self.key] += amount

    def get(self) -> float:
        """Get current value."""
        return self.registry._counters.get(self.key, 0.0)


class Gauge:
    """Gauge metric (arbitrary value)."""

    def __init__(self, registry: PrometheusRegistry, name: str, labels: dict[str, str]):
        self.registry = registry
        self.name = name
        self.labels = labels
        self.key = f"{name}_{registry._label_key(labels)}"

    def set(self, value: float):
        """Set gauge value."""
        self.registry._gauges[self.key] = value

    def inc(self, amount: float = 1.0):
        """Increment gauge."""
        current = self.registry._gauges.get(self.key, 0.0)
        self.registry._gauges[self.key] = current + amount

    def dec(self, amount: float = 1.0):
        """Decrement gauge."""
        current = self.registry._gauges.get(self.key, 0.0)
        self.registry._gauges[self.key] = current - amount

    def get(self) -> float:
        """Get current value."""
        return self.registry._gauges.get(self.key, 0.0)


class Histogram:
    """Histogram metric (distribution with buckets)."""

    def __init__(
        self,
        registry: PrometheusRegistry,
        name: str,
        labels: dict[str, str],
        buckets: list[float],
    ):
        self.registry = registry
        self.name = name
        self.labels = labels
        self.buckets = buckets
        self.key = f"{name}_{registry._label_key(labels)}"

    def observe(self, value: float):
        """Record observation."""
        self.registry._histograms[self.key].append(value)

    @contextmanager
    def time(self):
        """Time a block of code."""
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            self.observe(duration)


class MetricsExporter:
    """Exports metrics to various backends."""

    def __init__(self, registry: PrometheusRegistry):
        self.registry = registry

    def export_prometheus(self) -> str:
        """Export in Prometheus text format."""
        return self.registry.export_text()

    def export_json(self) -> dict[str, Any]:
        """Export as JSON."""
        return {
            "counters": dict(self.registry._counters),
            "gauges": dict(self.registry._gauges),
            "histograms": {
                k: {
                    "values": v,
                    "count": len(v),
                    "sum": sum(v),
                    "min": min(v) if v else 0,
                    "max": max(v) if v else 0,
                }
                for k, v in self.registry._histograms.items()
            },
        }


# Global registry
_global_registry: PrometheusRegistry | None = None


def get_metrics_registry() -> PrometheusRegistry:
    """Get global metrics registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = PrometheusRegistry()
    return _global_registry


def metric_counter(
    name: str, help: str = "", labels: dict[str, str] | None = None
) -> Counter:
    """Create counter metric."""
    return get_metrics_registry().counter(name, help, labels)


def metric_gauge(
    name: str, help: str = "", labels: dict[str, str] | None = None
) -> Gauge:
    """Create gauge metric."""
    return get_metrics_registry().gauge(name, help, labels)


def metric_histogram(
    name: str,
    help: str = "",
    labels: dict[str, str] | None = None,
    buckets: list[float] | None = None,
) -> Histogram:
    """Create histogram metric."""
    return get_metrics_registry().histogram(name, help, labels, buckets)
