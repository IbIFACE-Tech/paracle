"""Example: Basic observability features.

Demonstrates:
- Prometheus metrics (counters, gauges, histograms)
- OpenTelemetry distributed tracing
- Intelligent alerting with multiple channels
"""

import time

from paracle_observability import (
    AlertManager,
    AlertRule,
    AlertSeverity,
    MetricsExporter,
    SlackChannel,
    get_metrics_registry,
    get_tracer,
    metric_counter,
    metric_gauge,
    metric_histogram,
    trace_span,
)

# ============================================================================
# 1. Prometheus Metrics
# ============================================================================


def metrics_example():
    """Demonstrate Prometheus metrics."""
    print("\n" + "=" * 60)
    print("1. PROMETHEUS METRICS")
    print("=" * 60)

    # Counter - monotonically increasing
    requests_counter = metric_counter(
        "example_requests_total",
        "Total number of requests",
        labels={"method": "GET", "endpoint": "/api/users"},
    )

    requests_counter.inc()
    requests_counter.inc(5)
    print(f"✅ Requests counter: {requests_counter.get()}")

    # Gauge - arbitrary value
    temperature_gauge = metric_gauge(
        "example_temperature_celsius",
        "Current temperature",
        labels={"location": "datacenter"},
    )

    temperature_gauge.set(22.5)
    temperature_gauge.inc(2.5)  # 25.0
    print(f"✅ Temperature gauge: {temperature_gauge.get()}°C")

    # Histogram - distribution
    latency_histogram = metric_histogram(
        "example_request_duration_seconds",
        "Request duration",
        labels={"service": "api"},
        buckets=[0.01, 0.05, 0.1, 0.5, 1.0],
    )

    # Observe some values
    latency_histogram.observe(0.03)
    latency_histogram.observe(0.15)
    latency_histogram.observe(0.45)

    # Time a block of code
    with latency_histogram.time():
        time.sleep(0.02)  # Simulate work

    print("✅ Histogram observations recorded")

    # Export metrics
    registry = get_metrics_registry()
    exporter = MetricsExporter(registry)

    print("\n📊 Prometheus Text Format:")
    print("-" * 60)
    print(exporter.export_prometheus())

    print("\n📊 JSON Format:")
    print("-" * 60)
    import json

    print(json.dumps(exporter.export_json(), indent=2))


# ============================================================================
# 2. Distributed Tracing
# ============================================================================


@trace_span("process_user_request")
def process_user_request(user_id: str):
    """Process user request with tracing."""
    tracer = get_tracer()

    with tracer.trace("validate_user") as span:
        span.set_attribute("user.id", user_id)
        span.set_attribute("validation.method", "jwt")
        time.sleep(0.01)  # Simulate validation
        span.add_event("validation_passed", {"timestamp": time.time()})

    with tracer.trace("fetch_user_data") as span:
        span.set_attribute("database.type", "postgresql")
        span.set_attribute("database.table", "users")
        time.sleep(0.02)  # Simulate DB query
        span.add_event("cache_miss", {"key": f"user:{user_id}"})

    with tracer.trace("format_response") as span:
        span.set_attribute("format", "json")
        time.sleep(0.005)  # Simulate formatting

    return {"user_id": user_id, "status": "success"}


def tracing_example():
    """Demonstrate distributed tracing."""
    print("\n" + "=" * 60)
    print("2. DISTRIBUTED TRACING")
    print("=" * 60)

    tracer = get_tracer("example-service")

    # Execute traced operation
    result = process_user_request("user-123")
    print(f"✅ Request processed: {result}")

    # Get completed spans
    spans = tracer.get_completed_spans()
    print(f"\n📈 Captured {len(spans)} spans")

    for span in spans:
        indent = "  " if span.parent_span_id else ""
        print(f"{indent}• {span.name}")
        print(f"{indent}  Duration: {span.duration_ms:.2f}ms")
        print(f"{indent}  Status: {span.status.value}")

        if span.events:
            print(f"{indent}  Events: {len(span.events)}")
            for event in span.events:
                print(f"{indent}    - {event['name']}")

    # Export to Jaeger
    jaeger_data = tracer.export_jaeger()
    print(f"\n✅ Jaeger export ready: {len(jaeger_data['data'])} trace(s)")


# ============================================================================
# 3. Intelligent Alerting
# ============================================================================


def alerting_example():
    """Demonstrate intelligent alerting."""
    print("\n" + "=" * 60)
    print("3. INTELLIGENT ALERTING")
    print("=" * 60)

    manager = AlertManager()

    # Create test metrics
    error_count = metric_gauge("example_errors_total")
    response_time = metric_gauge("example_response_time_ms")

    # Define alert rules
    high_error_rule = AlertRule(
        name="high_error_rate",
        severity=AlertSeverity.ERROR,
        condition=lambda: error_count.get() > 10,
        message="Error count above threshold",
        labels={"service": "api", "env": "production"},
        annotations={
            "summary": "High error rate detected",
            "description": "Current errors: {value}",
        },
        for_duration=1.0,  # Alert if true for 1 second
    )

    slow_response_rule = AlertRule(
        name="slow_response_time",
        severity=AlertSeverity.WARNING,
        condition=lambda: response_time.get() > 1000,  # > 1 second
        message="Response time above 1s",
        labels={"service": "api"},
        for_duration=2.0,
    )

    manager.add_rule(high_error_rule)
    manager.add_rule(slow_response_rule)

    # Add notification channels
    slack = SlackChannel(
        "slack-alerts", {"webhook_url": "https://hooks.slack.com/services/test"}
    )
    manager.add_channel(slack)

    print("✅ Alert rules configured:")
    for rule in [high_error_rule, slow_response_rule]:
        print(f"  • {rule.name} ({rule.severity.value})")

    # Simulate conditions
    print("\n📊 Simulating metrics...")
    error_count.set(5)
    response_time.set(500)

    alerts = manager.evaluate_rules()
    print("✅ No alerts triggered (conditions not met)")

    # Trigger alert
    error_count.set(15)  # Above threshold
    time.sleep(1.2)  # Wait for duration

    alerts = manager.evaluate_rules()
    if alerts:
        print(f"\n🚨 {len(alerts)} alert(s) fired:")
        for alert in alerts:
            print(f"  • {alert.rule_name}: {alert.message}")
            print(f"    Severity: {alert.severity.value}")
            print(f"    Labels: {alert.labels}")

    # Get active alerts
    active = manager.get_active_alerts()
    print(f"\n📋 Active alerts: {len(active)}")
    for alert in active:
        print(f"  • {alert.rule_name} ({alert.state.value})")
        print(f"    Duration: {alert.duration_seconds:.1f}s")

    # Silence alert
    if active:
        fingerprint = active[0].fingerprint
        manager.silence(fingerprint, duration=60)
        print("\n🔇 Alert silenced for 60 seconds")


# ============================================================================
# 4. Full Stack Example
# ============================================================================


@trace_span("api_request")
def api_request_handler(method: str, endpoint: str):
    """Full observability stack example."""
    # Increment request counter
    requests_counter = metric_counter(
        "api_requests_total", labels={"method": method, "endpoint": endpoint}
    )
    requests_counter.inc()

    # Track duration
    duration_histogram = metric_histogram(
        "api_request_duration_seconds", labels={"endpoint": endpoint}
    )

    tracer = get_tracer()

    with duration_histogram.time():
        with tracer.trace("process_request") as span:
            span.set_attribute("http.method", method)
            span.set_attribute("http.url", endpoint)

            # Simulate processing
            time.sleep(0.05)

            # Update gauge
            active_requests = metric_gauge("api_active_requests")
            active_requests.inc()

            try:
                # Simulate work
                time.sleep(0.02)
                span.set_status("ok")
            finally:
                active_requests.dec()

    return {"status": "success", "method": method, "endpoint": endpoint}


def full_stack_example():
    """Demonstrate full observability stack."""
    print("\n" + "=" * 60)
    print("4. FULL STACK EXAMPLE")
    print("=" * 60)

    # Execute multiple requests
    for i in range(5):
        result = api_request_handler("GET", f"/api/endpoint-{i % 3}")
        print(f"✅ Request {i+1} completed: {result['endpoint']}")
        time.sleep(0.1)

    # Show metrics summary
    print("\n📊 Metrics Summary:")
    registry = get_metrics_registry()
    exporter = MetricsExporter(registry)
    data = exporter.export_json()

    print(f"  Counters: {len(data['counters'])}")
    for key, value in list(data["counters"].items())[:3]:
        print(f"    • {key}: {value}")

    print(f"  Gauges: {len(data['gauges'])}")
    for key, value in list(data["gauges"].items())[:3]:
        print(f"    • {key}: {value}")

    # Show traces summary
    print("\n📈 Traces Summary:")
    tracer = get_tracer()
    spans = tracer.get_completed_spans()
    print(f"  Total spans: {len(spans)}")
    print(f"  Avg duration: {sum(s.duration_ms for s in spans) / len(spans):.2f}ms")


# ============================================================================
# Main
# ============================================================================


def main():
    """Run all observability examples."""
    print("\n" + "=" * 60)
    print("PARACLE OBSERVABILITY EXAMPLES")
    print("=" * 60)

    metrics_example()
    tracing_example()
    alerting_example()
    full_stack_example()

    print("\n" + "=" * 60)
    print("✅ All examples completed!")
    print("=" * 60)

    print("\n💡 Next steps:")
    print("  • View metrics: paracle metrics list")
    print("  • Export metrics: paracle metrics export --format prometheus")
    print("  • View traces: paracle trace list")
    print("  • Check alerts: paracle alerts list")


if __name__ == "__main__":
    main()
