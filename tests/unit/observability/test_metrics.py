"""Tests for Prometheus metrics integration."""

import time

from paracle_observability.metrics import (
    MetricsExporter,
    PrometheusRegistry,
    get_metrics_registry,
)


def test_counter():
    """Test counter metric."""
    registry = PrometheusRegistry()
    counter = registry.counter("test_counter", "Test counter", {"env": "test"})

    assert counter.get() == 0.0
    counter.inc()
    assert counter.get() == 1.0
    counter.inc(5)
    assert counter.get() == 6.0


def test_gauge():
    """Test gauge metric."""
    registry = PrometheusRegistry()
    gauge = registry.gauge("test_gauge", "Test gauge", {"env": "test"})

    assert gauge.get() == 0.0
    gauge.set(42.0)
    assert gauge.get() == 42.0
    gauge.inc(8)
    assert gauge.get() == 50.0
    gauge.dec(10)
    assert gauge.get() == 40.0


def test_histogram():
    """Test histogram metric."""
    registry = PrometheusRegistry()
    histogram = registry.histogram("test_histogram", "Test histogram", {"env": "test"})

    histogram.observe(0.1)
    histogram.observe(0.5)
    histogram.observe(1.0)
    histogram.observe(2.5)

    # Check histogram data
    key = "test_histogram_env=test"
    assert len(registry._histograms[key]) == 4


def test_histogram_time_context():
    """Test histogram timing context manager."""
    registry = PrometheusRegistry()
    histogram = registry.histogram("request_duration", "Request duration")

    with histogram.time():
        time.sleep(0.01)  # Simulate work

    key = "request_duration_"
    assert len(registry._histograms[key]) == 1
    assert registry._histograms[key][0] >= 0.01


def test_prometheus_export():
    """Test Prometheus text format export."""
    registry = PrometheusRegistry()

    counter = registry.counter("requests_total", "Total requests", {"method": "GET"})
    counter.inc(42)

    gauge = registry.gauge("active_connections", "Active connections")
    gauge.set(10)

    output = registry.export_text()

    assert "# HELP requests_total Total requests" in output
    assert "# TYPE requests_total counter" in output
    assert 'requests_total{method="GET"} 42' in output

    assert "# HELP active_connections Active connections" in output
    assert "# TYPE active_connections gauge" in output
    assert "active_connections 10" in output


def test_metrics_exporter_json():
    """Test JSON export."""
    registry = PrometheusRegistry()

    counter = registry.counter("test_counter", labels={"app": "paracle"})
    counter.inc(5)

    gauge = registry.gauge("test_gauge", labels={"app": "paracle"})
    gauge.set(100)

    histogram = registry.histogram("test_hist", labels={"app": "paracle"})
    histogram.observe(0.5)
    histogram.observe(1.0)

    exporter = MetricsExporter(registry)
    data = exporter.export_json()

    assert "counters" in data
    assert "gauges" in data
    assert "histograms" in data

    # Check values
    counter_key = "test_counter_app=paracle"
    assert data["counters"][counter_key] == 5.0

    gauge_key = "test_gauge_app=paracle"
    assert data["gauges"][gauge_key] == 100.0

    hist_key = "test_hist_app=paracle"
    assert data["histograms"][hist_key]["count"] == 2


def test_global_registry():
    """Test global registry functions."""
    from paracle_observability.metrics import (
        metric_counter,
        metric_gauge,
        metric_histogram,
    )

    counter = metric_counter("global_counter", "Global counter")
    counter.inc()
    assert counter.get() == 1.0

    gauge = metric_gauge("global_gauge", "Global gauge")
    gauge.set(50)
    assert gauge.get() == 50.0

    histogram = metric_histogram("global_histogram", "Global histogram")
    histogram.observe(0.5)

    registry = get_metrics_registry()
    assert len(registry._counters) > 0
    assert len(registry._gauges) > 0
    assert len(registry._histograms) > 0
