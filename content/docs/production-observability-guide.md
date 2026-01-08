"""Production Observability Guide.

Complete guide to implementing production-grade monitoring and observability
for Paracle using Prometheus, OpenTelemetry, Grafana, and alerting.

Phase 7 - Production Observability Implementation.
"""

# Phase 7: Production Observability - Complete Implementation Guide

## Overview

Production observability provides deep visibility into Paracle's runtime behavior through:
- **Prometheus metrics** - Performance counters, gauges, histograms
- **OpenTelemetry tracing** - Distributed request tracing
- **Grafana dashboards** - Visual monitoring and analysis
- **Intelligent alerting** - Proactive issue detection

## Installation

```bash
# Install observability package
pip install paracle[observability]

# Or install from source
cd packages/paracle_observability
pip install -e .
```

## 1. Prometheus Metrics

### Basic Usage

```python
from paracle_observability import (
    metric_counter,
    metric_gauge,
    metric_histogram,
    get_metrics_registry,
)

# Counter - monotonically increasing
requests_counter = metric_counter(
    "paracle_requests_total",
    "Total number of requests",
    labels={"method": "POST", "endpoint": "/api/agents"}
)
requests_counter.inc()

# Gauge - arbitrary value
active_agents = metric_gauge(
    "paracle_active_agents",
    "Number of currently active agents"
)
active_agents.set(5)
active_agents.inc()  # increment by 1
active_agents.dec(2)  # decrement by 2

# Histogram - distribution with buckets
request_duration = metric_histogram(
    "paracle_request_duration_seconds",
    "Request duration in seconds",
    labels={"method": "GET"},
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

# Manual observation
request_duration.observe(0.25)

# Time block of code
with request_duration.time():
    # Your code here
    process_request()
```

### Export Metrics

```python
from paracle_observability import MetricsExporter, get_metrics_registry

registry = get_metrics_registry()
exporter = MetricsExporter(registry)

# Prometheus text format (for /metrics endpoint)
prometheus_text = exporter.export_prometheus()
print(prometheus_text)

# JSON format (for logging/debugging)
json_data = exporter.export_json()
```

### Integrate with FastAPI

```python
from fastapi import FastAPI, Response
from paracle_observability import get_metrics_registry, MetricsExporter

app = FastAPI()

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    registry = get_metrics_registry()
    exporter = MetricsExporter(registry)
    content = exporter.export_prometheus()
    return Response(content=content, media_type="text/plain")

@app.middleware("http")
async def track_requests(request, call_next):
    """Track request metrics."""
    from paracle_observability import metric_counter, metric_histogram

    counter = metric_counter(
        "http_requests_total",
        labels={"method": request.method, "path": request.url.path}
    )
    counter.inc()

    histogram = metric_histogram(
        "http_request_duration_seconds",
        labels={"method": request.method}
    )

    with histogram.time():
        response = await call_next(request)

    return response
```

## 2. Distributed Tracing

### Basic Tracing

```python
from paracle_observability import get_tracer, SpanKind

tracer = get_tracer("my-service")

# Start a trace
with tracer.trace("process_request", kind=SpanKind.SERVER) as span:
    span.set_attribute("user.id", "123")
    span.set_attribute("request.size", 1024)

    # Nested span
    with tracer.trace("database_query", kind=SpanKind.CLIENT) as db_span:
        db_span.set_attribute("db.table", "users")
        db_span.set_attribute("db.operation", "SELECT")
        result = query_database()

    # Add event
    span.add_event("cache_miss", {"key": "user:123"})

    return result
```

### Tracing Decorators

```python
from paracle_observability import trace_span, trace_async, SpanKind

@trace_span("execute_agent", kind=SpanKind.INTERNAL)
def execute_agent(agent_id: str, task: str):
    """Execute agent with automatic tracing."""
    # Span automatically created
    # Function name, module added as attributes
    result = agent.execute(task)
    return result

@trace_async("async_operation", kind=SpanKind.SERVER)
async def async_operation(data: dict):
    """Async function with tracing."""
    result = await process(data)
    return result
```

### Error Tracking

```python
tracer = get_tracer()

with tracer.trace("risky_operation") as span:
    try:
        dangerous_operation()
    except Exception as e:
        # Automatically tracked in context manager
        # Or manually:
        span.set_status("error", str(e))
        span.add_event("exception", {
            "exception.type": type(e).__name__,
            "exception.message": str(e)
        })
        raise
```

### Export to Jaeger

```python
from paracle_observability import get_tracer

tracer = get_tracer("my-service")

# After executing traced operations
jaeger_data = tracer.export_jaeger()

# Send to Jaeger collector
import requests
requests.post(
    "http://jaeger:14268/api/traces",
    json=jaeger_data
)
```

## 3. Intelligent Alerting

### Define Alert Rules

```python
from paracle_observability import (
    AlertManager,
    AlertRule,
    AlertSeverity,
    metric_gauge,
)

manager = AlertManager()

# Create metric
error_rate = metric_gauge("error_rate_percent")

# Define rule
high_error_rule = AlertRule(
    name="high_error_rate",
    severity=AlertSeverity.ERROR,
    condition=lambda: error_rate.get() > 5.0,  # > 5%
    message="Error rate above 5%",
    labels={"service": "api", "env": "production"},
    annotations={
        "summary": "High error rate detected",
        "description": "Current error rate: {value}%"
    },
    for_duration=60.0  # Alert if true for 60 seconds
)

manager.add_rule(high_error_rule)
```

### Notification Channels

```python
from paracle_observability import (
    SlackChannel,
    EmailChannel,
    WebhookChannel,
)

# Slack
slack = SlackChannel(
    "slack-ops",
    {"webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"}
)
manager.add_channel(slack)

# Email
email = EmailChannel(
    "email-oncall",
    {
        "to": "oncall@example.com",
        "from": "alerts@example.com",
        "smtp_host": "smtp.example.com",
        "smtp_port": 587
    }
)
manager.add_channel(email)

# Generic webhook
webhook = WebhookChannel(
    "pagerduty",
    {"url": "https://events.pagerduty.com/v2/enqueue"}
)
manager.add_channel(webhook)
```

### Evaluate Rules

```python
import schedule
import time

def check_alerts():
    """Periodically evaluate alert rules."""
    new_alerts = manager.evaluate_rules()

    for alert in new_alerts:
        print(f"🚨 Alert fired: {alert.message}")
        print(f"   Severity: {alert.severity.value}")
        print(f"   Labels: {alert.labels}")

# Run every minute
schedule.every(1).minutes.do(check_alerts)

while True:
    schedule.run_pending()
    time.sleep(1)
```

### Silence Alerts

```python
# Silence specific alert for 1 hour
alert_fingerprint = "high_error_rate_service=api_env=production"
manager.silence(alert_fingerprint, duration=3600)

# Get active alerts
active_alerts = manager.get_active_alerts()
for alert in active_alerts:
    print(f"{alert.rule_name}: {alert.state.value}")

# Get alerts by severity
critical_alerts = manager.get_active_alerts(AlertSeverity.CRITICAL)
```

## 4. Production Deployment

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'paracle'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Paracle Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(paracle_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Request Duration (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(paracle_request_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Active Agents",
        "targets": [
          {
            "expr": "paracle_active_agents"
          }
        ]
      }
    ]
  }
}
```

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  paracle:
    image: paracle:latest
    ports:
      - "8000:8000"
    environment:
      - PROMETHEUS_ENABLED=true

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # Jaeger UI
      - "14268:14268"  # Jaeger collector

volumes:
  grafana-storage:
```

## 5. Best Practices

### Metric Naming

```python
# ✅ Good - Clear, prefixed, unit specified
metric_counter("paracle_agent_executions_total")
metric_histogram("paracle_request_duration_seconds")
metric_gauge("paracle_memory_usage_bytes")

# ❌ Bad - Unclear, no prefix, no unit
metric_counter("count")
metric_histogram("duration")
metric_gauge("memory")
```

### Label Cardinality

```python
# ✅ Good - Low cardinality labels
metric_counter("requests_total", labels={
    "method": "GET",      # ~10 values
    "status": "200",      # ~20 values
    "endpoint": "/api"    # ~50 values
})

# ❌ Bad - High cardinality (creates too many series)
metric_counter("requests_total", labels={
    "user_id": "12345",       # Thousands of values!
    "request_id": "uuid",     # Unique per request!
    "timestamp": "unix_time"  # Always different!
})
```

### Trace Sampling

```python
import random

def should_trace() -> bool:
    """Sample 10% of requests for tracing."""
    return random.random() < 0.1

if should_trace():
    with tracer.trace("expensive_operation"):
        process()
```

## 6. Common Metrics

```python
from paracle_observability import metric_counter, metric_gauge, metric_histogram

# Agent metrics
agent_executions = metric_counter("paracle_agent_executions_total",
    labels={"agent_type": "coder", "status": "success"})

agent_duration = metric_histogram("paracle_agent_duration_seconds",
    labels={"agent_type": "coder"})

# LLM metrics
llm_tokens = metric_counter("paracle_llm_tokens_total",
    labels={"provider": "openai", "model": "gpt-4"})

llm_latency = metric_histogram("paracle_llm_latency_seconds",
    labels={"provider": "openai"})

# System metrics
memory_usage = metric_gauge("paracle_memory_usage_bytes")
cpu_usage = metric_gauge("paracle_cpu_usage_percent")
active_connections = metric_gauge("paracle_active_connections")

# Cache metrics
cache_hits = metric_counter("paracle_cache_hits_total",
    labels={"cache_type": "response"})
cache_misses = metric_counter("paracle_cache_misses_total",
    labels={"cache_type": "response"})
```

## 7. Troubleshooting

### High Metric Cardinality

```python
# Check metric count
from paracle_observability import get_metrics_registry

registry = get_metrics_registry()
print(f"Total metrics: {len(registry._metrics)}")
print(f"Counters: {len(registry._counters)}")
print(f"Gauges: {len(registry._gauges)}")
```

### Trace Storage

```python
# Clear old traces
tracer = get_tracer()
tracer.clear()  # Removes all completed spans
```

### Alert Debugging

```python
manager = get_alert_manager()

# Get alert history
history = manager.get_alert_history(limit=50)
for alert in history:
    print(f"{alert.rule_name}: {alert.state.value}")
    print(f"  Duration: {alert.duration_seconds}s")
```

## References

- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [OpenTelemetry Specification](https://opentelemetry.io/docs/specs/otel/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/best-practices/)
- [Alerting Best Practices](https://prometheus.io/docs/practices/alerting/)
