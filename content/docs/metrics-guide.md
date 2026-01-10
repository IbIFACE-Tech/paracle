# Paracle Metrics Guide

Comprehensive guide to monitoring and observability metrics in the Paracle framework.

**Version**: 1.0
**Date**: 2026-01-10
**Status**: Active

## Overview

Paracle provides comprehensive metrics for monitoring resilience patterns, retry behavior, and system health. This guide covers all available metrics, how to access them, and best practices for monitoring production deployments.

## Table of Contents

1. [Circuit Breaker Metrics](#circuit-breaker-metrics)
2. [Retry Manager Metrics](#retry-manager-metrics)
3. [Usage Examples](#usage-examples)
4. [Monitoring Best Practices](#monitoring-best-practices)
5. [Integration with Observability Tools](#integration-with-observability-tools)
6. [Troubleshooting](#troubleshooting)

---

## Circuit Breaker Metrics

Circuit breakers track failures and automatically prevent cascading failures by "opening" when error thresholds are exceeded.

### Available Metrics

#### State Information

| Field           | Type         | Description                                     |
| --------------- | ------------ | ----------------------------------------------- |
| `name`          | string       | Circuit breaker identifier                      |
| `state`         | string       | Current state: `closed`, `open`, or `half_open` |
| `failure_count` | int          | Consecutive failures in current state           |
| `success_count` | int          | Consecutive successes (in half-open state)      |
| `opened_at`     | string\|null | ISO timestamp when circuit opened               |
| `last_failure`  | string\|null | ISO timestamp of most recent failure            |

#### Configuration

| Field               | Type  | Description                              |
| ------------------- | ----- | ---------------------------------------- |
| `failure_threshold` | int   | Failures before circuit opens            |
| `success_threshold` | int   | Successes needed to close from half-open |
| `timeout`           | float | Seconds before attempting reset          |

#### Metrics

| Metric            | Type  | Formula                       | Description                                |
| ----------------- | ----- | ----------------------------- | ------------------------------------------ |
| `total_calls`     | int   | -                             | Total attempted calls (excluding rejected) |
| `total_successes` | int   | -                             | Total successful calls                     |
| `total_failures`  | int   | -                             | Total failed calls                         |
| `total_rejected`  | int   | -                             | Calls rejected while circuit open          |
| `success_rate`    | float | successes / total_calls       | Success ratio (0.0-1.0)                    |
| `failure_rate`    | float | failures / total_calls        | Failure ratio (0.0-1.0)                    |
| `rejection_rate`  | float | rejected / (calls + rejected) | Rejection ratio (0.0-1.0)                  |

### Accessing Circuit Breaker Metrics

```python
from paracle_resilience.circuit_breaker import CircuitBreaker

# Create circuit breaker
circuit = CircuitBreaker(
    name="api_service",
    failure_threshold=5,
    timeout=60.0,
)

# Execute protected calls
for i in range(100):
    try:
        result = circuit.call(make_api_call)
    except Exception as e:
        logger.error(f"Call failed: {e}")

# Get comprehensive state and metrics
state = circuit.get_state()

print(f"Circuit: {state['name']}")
print(f"State: {state['state']}")
print(f"Metrics:")
print(f"  Total Calls: {state['metrics']['total_calls']}")
print(f"  Success Rate: {state['metrics']['success_rate']:.2%}")
print(f"  Failure Rate: {state['metrics']['failure_rate']:.2%}")
print(f"  Rejections: {state['metrics']['total_rejected']}")
```

### Example Output

```python
{
    "name": "api_service",
    "state": "half_open",
    "failure_count": 0,
    "success_count": 1,
    "opened_at": "2026-01-10T10:30:00",
    "last_failure": "2026-01-10T10:29:55",
    "config": {
        "failure_threshold": 5,
        "success_threshold": 2,
        "timeout": 60.0
    },
    "metrics": {
        "total_calls": 1523,
        "total_successes": 1498,
        "total_failures": 25,
        "total_rejected": 12,
        "success_rate": 0.98357,
        "failure_rate": 0.01642,
        "rejection_rate": 0.00781
    }
}
```

### Interpreting Circuit Breaker Metrics

#### State Transitions

```
CLOSED → [failures ≥ threshold] → OPEN
  ↑                                 ↓
  |                          [timeout elapsed]
  |                                 ↓
  └── [successes ≥ threshold] ← HALF_OPEN
```

#### Health Indicators

| Metric           | Healthy | Warning    | Critical |
| ---------------- | ------- | ---------- | -------- |
| `success_rate`   | > 0.99  | 0.95-0.99  | < 0.95   |
| `failure_rate`   | < 0.01  | 0.01-0.05  | > 0.05   |
| `rejection_rate` | < 0.001 | 0.001-0.01 | > 0.01   |
| `state`          | closed  | half_open  | open     |

---

## Retry Manager Metrics

The Retry Manager tracks retry behavior across workflow steps, providing insights into error patterns and retry effectiveness.

### Available Metrics

#### Context Statistics

| Field                     | Type  | Description                                 |
| ------------------------- | ----- | ------------------------------------------- |
| `total_contexts`          | int   | Total execution contexts tracked            |
| `succeeded`               | int   | Contexts that eventually succeeded          |
| `failed`                  | int   | Contexts that exhausted all retries         |
| `success_rate`            | float | succeeded / total_contexts (0.0-1.0)        |
| `total_attempts`          | int   | Sum of all attempts across contexts         |
| `total_retries`           | int   | Sum of retry attempts (attempts - contexts) |
| `avg_retries_per_context` | float | Average retries per context                 |

#### Enhanced Metrics

| Metric                | Type  | Description                              |
| --------------------- | ----- | ---------------------------------------- |
| `avg_delay_seconds`   | float | Average delay between retry attempts     |
| `max_delay_seconds`   | float | Maximum delay encountered                |
| `total_delay_seconds` | float | Cumulative delay time across all retries |
| `success_after_retry` | int   | Contexts succeeding after ≥1 retry       |
| `immediate_success`   | int   | Contexts succeeding on first attempt     |
| `error_categories`    | dict  | Error distribution by category           |

#### Error Categories

| Category     | Description                | Examples                              |
| ------------ | -------------------------- | ------------------------------------- |
| `TIMEOUT`    | Timeout-related failures   | Connection timeout, read timeout      |
| `TRANSIENT`  | Temporary/transient errors | Network issues, rate limits, 502/503  |
| `VALIDATION` | Input/validation errors    | Invalid parameters, bad request (400) |
| `RESOURCE`   | Resource exhaustion        | Out of memory, quota exceeded         |
| `PERMANENT`  | Non-retryable errors       | Auth failures (401), not found (404)  |
| `UNKNOWN`    | Uncategorized errors       | Other unclassified errors             |

### Accessing Retry Manager Metrics

```python
from paracle_orchestration.retry import RetryManager
from paracle_domain.models import RetryPolicy, BackoffStrategy

# Create retry manager
manager = RetryManager()

# Define retry policy
policy = RetryPolicy(
    max_attempts=3,
    backoff_strategy=BackoffStrategy.EXPONENTIAL,
    initial_delay=1.0,
    max_delay=60.0,
)

# Execute operations with retries
for i in range(50):
    try:
        result = await manager.execute_with_retry(
            step_name=f"operation_{i}",
            func=make_api_call,
            policy=policy,
        )
    except Exception as e:
        logger.error(f"Operation failed: {e}")

# Get comprehensive statistics
stats = manager.get_retry_stats()

print(f"Retry Statistics:")
print(f"  Total Contexts: {stats['total_contexts']}")
print(f"  Success Rate: {stats['success_rate']:.2%}")
print(f"  Avg Retries: {stats['avg_retries_per_context']:.2f}")
print(f"  Avg Delay: {stats['metrics']['avg_delay_seconds']:.2f}s")
print(f"  Max Delay: {stats['metrics']['max_delay_seconds']:.2f}s")
print(f"  Immediate Success: {stats['metrics']['immediate_success']}")
print(f"  Success After Retry: {stats['metrics']['success_after_retry']}")

print(f"\nError Categories:")
for category, count in stats['metrics']['error_categories'].items():
    print(f"  {category}: {count} errors")
```

### Example Output

```python
{
    "total_contexts": 250,
    "succeeded": 238,
    "failed": 12,
    "success_rate": 0.952,
    "total_attempts": 312,
    "total_retries": 62,
    "avg_retries_per_context": 0.248,
    "metrics": {
        "avg_delay_seconds": 3.47,
        "max_delay_seconds": 60.0,
        "total_delay_seconds": 215.14,
        "success_after_retry": 50,
        "immediate_success": 188,
        "error_categories": {
            "TRANSIENT": 45,
            "TIMEOUT": 12,
            "RATE_LIMIT": 5
        }
    }
}
```

### Interpreting Retry Manager Metrics

#### Success Patterns

```python
# Calculate retry effectiveness
immediate_pct = stats['metrics']['immediate_success'] / stats['total_contexts']
retry_success_pct = stats['metrics']['success_after_retry'] / stats['total_contexts']
failure_pct = stats['failed'] / stats['total_contexts']

print(f"Immediate Success: {immediate_pct:.2%}")  # Operations that work first try
print(f"Retry Success: {retry_success_pct:.2%}")  # Operations fixed by retries
print(f"Final Failure: {failure_pct:.2%}")        # Operations that exhaust retries
```

#### Health Indicators

| Metric                    | Healthy | Warning   | Critical |
| ------------------------- | ------- | --------- | -------- |
| `success_rate`            | > 0.95  | 0.90-0.95 | < 0.90   |
| `avg_retries_per_context` | < 0.5   | 0.5-1.0   | > 1.0    |
| `avg_delay_seconds`       | < 5.0   | 5.0-15.0  | > 15.0   |
| Immediate success rate    | > 0.80  | 0.70-0.80 | < 0.70   |

---

## Usage Examples

### Example 1: Monitoring a Critical Service

```python
from paracle_resilience.circuit_breaker import CircuitBreaker
import logging

logger = logging.getLogger(__name__)

# Create circuit breaker for critical service
payment_circuit = CircuitBreaker(
    name="payment_service",
    failure_threshold=3,
    timeout=30.0,
)

def check_payment_health():
    """Monitor payment service health using circuit breaker metrics."""
    state = payment_circuit.get_state()
    metrics = state['metrics']

    # Alert on high failure rate
    if metrics['failure_rate'] > 0.05:
        logger.warning(
            f"Payment service failure rate high: {metrics['failure_rate']:.2%}"
        )

    # Alert if circuit is open
    if state['state'] == 'open':
        logger.critical(
            f"Payment circuit OPEN! {metrics['total_rejected']} calls rejected"
        )

    # Log metrics for monitoring
    logger.info(
        f"Payment Health: {metrics['success_rate']:.2%} success, "
        f"{metrics['total_calls']} calls, state={state['state']}"
    )

    return metrics

# Run periodic health checks
import asyncio

async def monitor_loop():
    while True:
        check_payment_health()
        await asyncio.sleep(60)  # Check every minute
```

### Example 2: Analyzing Retry Patterns

```python
from paracle_orchestration.retry import RetryManager

def analyze_retry_patterns(manager: RetryManager):
    """Analyze retry behavior to optimize retry policies."""
    stats = manager.get_retry_stats()
    metrics = stats['metrics']

    print("\n=== Retry Analysis ===")
    print(f"Total Operations: {stats['total_contexts']}")
    print(f"Overall Success Rate: {stats['success_rate']:.2%}")

    # Analyze success patterns
    immediate = metrics['immediate_success']
    after_retry = metrics['success_after_retry']
    total_success = stats['succeeded']

    print(f"\nSuccess Breakdown:")
    print(f"  Immediate: {immediate} ({immediate/total_success:.1%})")
    print(f"  After Retry: {after_retry} ({after_retry/total_success:.1%})")

    # Analyze delays
    print(f"\nDelay Analysis:")
    print(f"  Average: {metrics['avg_delay_seconds']:.2f}s")
    print(f"  Maximum: {metrics['max_delay_seconds']:.2f}s")
    print(f"  Total Wait Time: {metrics['total_delay_seconds']:.2f}s")

    # Error distribution
    print(f"\nError Distribution:")
    total_errors = sum(metrics['error_categories'].values())
    for category, count in sorted(
        metrics['error_categories'].items(),
        key=lambda x: x[1],
        reverse=True
    ):
        pct = count / total_errors if total_errors > 0 else 0
        print(f"  {category}: {count} ({pct:.1%})")

    # Recommendations
    print(f"\nRecommendations:")

    # High retry rate suggests policy adjustment needed
    if stats['avg_retries_per_context'] > 1.0:
        print("  ⚠️  High retry rate - consider increasing initial_delay")

    # Low immediate success suggests upstream issues
    immediate_rate = immediate / stats['total_contexts']
    if immediate_rate < 0.7:
        print("  ⚠️  Low immediate success - investigate upstream reliability")

    # High transient errors suggest rate limiting
    transient = metrics['error_categories'].get('TRANSIENT', 0)
    if transient / total_errors > 0.5:
        print("  ⚠️  High transient errors - consider rate limiting or backpressure")

    return stats
```

### Example 3: Dashboard Data Export

```python
import json
from datetime import datetime

def export_metrics_for_dashboard(circuit, retry_manager):
    """Export metrics in format suitable for dashboards (Grafana, etc.)."""
    timestamp = datetime.utcnow().isoformat()

    circuit_state = circuit.get_state()
    retry_stats = retry_manager.get_retry_stats()

    metrics = {
        "timestamp": timestamp,
        "circuit_breaker": {
            "name": circuit_state['name'],
            "state": circuit_state['state'],
            "total_calls": circuit_state['metrics']['total_calls'],
            "success_rate": circuit_state['metrics']['success_rate'],
            "failure_rate": circuit_state['metrics']['failure_rate'],
            "rejection_rate": circuit_state['metrics']['rejection_rate'],
            "total_rejected": circuit_state['metrics']['total_rejected'],
        },
        "retry_manager": {
            "total_contexts": retry_stats['total_contexts'],
            "success_rate": retry_stats['success_rate'],
            "avg_retries": retry_stats['avg_retries_per_context'],
            "avg_delay_seconds": retry_stats['metrics']['avg_delay_seconds'],
            "max_delay_seconds": retry_stats['metrics']['max_delay_seconds'],
            "immediate_success": retry_stats['metrics']['immediate_success'],
            "success_after_retry": retry_stats['metrics']['success_after_retry'],
            "error_categories": retry_stats['metrics']['error_categories'],
        }
    }

    return json.dumps(metrics, indent=2)

# Usage
metrics_json = export_metrics_for_dashboard(payment_circuit, retry_manager)
print(metrics_json)

# Or send to monitoring system
# await send_to_prometheus(metrics_json)
# await send_to_datadog(metrics_json)
```

---

## Monitoring Best Practices

### 1. Establish Baselines

Before setting alerts, establish baseline metrics:

```python
def establish_baseline(circuit, duration_hours=24):
    """Collect baseline metrics over a period."""
    import time

    samples = []
    interval = 300  # 5 minutes

    for _ in range(duration_hours * 12):  # 12 samples per hour
        state = circuit.get_state()
        samples.append({
            'timestamp': time.time(),
            'success_rate': state['metrics']['success_rate'],
            'failure_rate': state['metrics']['failure_rate'],
            'rejection_rate': state['metrics']['rejection_rate'],
        })
        time.sleep(interval)

    # Calculate baseline statistics
    success_rates = [s['success_rate'] for s in samples]
    avg_success = sum(success_rates) / len(success_rates)

    print(f"Baseline Success Rate: {avg_success:.2%}")
    print(f"Min: {min(success_rates):.2%}")
    print(f"Max: {max(success_rates):.2%}")

    return samples
```

### 2. Set Meaningful Alerts

```python
# Alert thresholds based on baseline
ALERT_THRESHOLDS = {
    'circuit_breaker': {
        'success_rate_min': 0.99,  # Alert if < 99%
        'failure_rate_max': 0.01,   # Alert if > 1%
        'rejection_rate_max': 0.001, # Alert if > 0.1%
    },
    'retry_manager': {
        'success_rate_min': 0.95,  # Alert if < 95%
        'avg_retries_max': 1.0,     # Alert if > 1 retry/context
        'avg_delay_max': 10.0,      # Alert if avg delay > 10s
    }
}

def check_alerts(circuit_state, retry_stats):
    """Check metrics against alert thresholds."""
    alerts = []

    # Circuit breaker alerts
    cb_metrics = circuit_state['metrics']
    if cb_metrics['success_rate'] < ALERT_THRESHOLDS['circuit_breaker']['success_rate_min']:
        alerts.append({
            'severity': 'WARNING',
            'component': 'circuit_breaker',
            'message': f"Success rate low: {cb_metrics['success_rate']:.2%}",
        })

    # Retry manager alerts
    if retry_stats['success_rate'] < ALERT_THRESHOLDS['retry_manager']['success_rate_min']:
        alerts.append({
            'severity': 'CRITICAL',
            'component': 'retry_manager',
            'message': f"Retry success rate low: {retry_stats['success_rate']:.2%}",
        })

    return alerts
```

### 3. Correlate Metrics

```python
def correlate_metrics(circuit_state, retry_stats):
    """Find correlations between circuit breaker and retry patterns."""

    # High rejections + high retry delays = cascading failure
    rejections = circuit_state['metrics']['total_rejected']
    avg_delay = retry_stats['metrics']['avg_delay_seconds']

    if rejections > 100 and avg_delay > 15.0:
        print("⚠️  ALERT: Cascading failure detected!")
        print(f"   Rejections: {rejections}")
        print(f"   Avg Retry Delay: {avg_delay:.2f}s")
        print("   Recommendation: Scale up resources or implement backpressure")

    # Low immediate success + high transient errors = upstream issues
    immediate_rate = (
        retry_stats['metrics']['immediate_success'] /
        retry_stats['total_contexts']
    )
    transient_count = retry_stats['metrics']['error_categories'].get('TRANSIENT', 0)

    if immediate_rate < 0.70 and transient_count > 50:
        print("⚠️  ALERT: Upstream service instability detected!")
        print(f"   Immediate Success Rate: {immediate_rate:.2%}")
        print(f"   Transient Errors: {transient_count}")
        print("   Recommendation: Investigate upstream service health")
```

### 4. Periodic Reporting

```python
import asyncio
from datetime import datetime, timedelta

async def generate_daily_report(circuit, retry_manager):
    """Generate daily metrics report."""

    circuit_state = circuit.get_state()
    retry_stats = retry_manager.get_retry_stats()

    report = f"""
    === Daily Metrics Report ===
    Date: {datetime.now().strftime('%Y-%m-%d')}

    Circuit Breaker: {circuit_state['name']}
      State: {circuit_state['state']}
      Total Calls: {circuit_state['metrics']['total_calls']:,}
      Success Rate: {circuit_state['metrics']['success_rate']:.4f}
      Failure Rate: {circuit_state['metrics']['failure_rate']:.4f}
      Rejections: {circuit_state['metrics']['total_rejected']:,}

    Retry Manager:
      Total Operations: {retry_stats['total_contexts']:,}
      Success Rate: {retry_stats['success_rate']:.4f}
      Avg Retries: {retry_stats['avg_retries_per_context']:.2f}
      Avg Delay: {retry_stats['metrics']['avg_delay_seconds']:.2f}s
      Immediate Success: {retry_stats['metrics']['immediate_success']:,}
      Success After Retry: {retry_stats['metrics']['success_after_retry']:,}

    Top Error Categories:
    """

    for category, count in sorted(
        retry_stats['metrics']['error_categories'].items(),
        key=lambda x: x[1],
        reverse=True
    )[:3]:
        report += f"      {category}: {count:,}\n"

    print(report)

    # Email or post to Slack
    # await send_email(report)
    # await post_to_slack(report)

# Schedule daily at 9 AM
async def schedule_daily_report():
    while True:
        now = datetime.now()
        next_run = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)

        await asyncio.sleep((next_run - now).total_seconds())
        await generate_daily_report(circuit, retry_manager)
```

---

## Integration with Observability Tools

### Prometheus Export (Coming in v1.2.0)

```python
# Future implementation
from paracle_observability.prometheus import PrometheusExporter

exporter = PrometheusExporter(port=9090)
exporter.register_circuit_breaker(payment_circuit)
exporter.register_retry_manager(retry_manager)
exporter.start()

# Metrics will be available at http://localhost:9090/metrics
```

### Grafana Dashboards (Coming in v1.2.0)

Pre-built dashboards will be available:
- Circuit Breaker Overview
- Retry Patterns Analysis
- Error Distribution
- Performance Metrics

### OpenTelemetry Integration (Planned v1.3.0)

```python
# Future implementation
from paracle_observability.otel import OpenTelemetryExporter

otel = OpenTelemetryExporter(endpoint="http://jaeger:4318")
otel.instrument_circuit_breaker(payment_circuit)
otel.instrument_retry_manager(retry_manager)
```

---

## Troubleshooting

### High Failure Rate

**Symptoms**: `failure_rate` > 0.05

**Diagnosis**:
```python
state = circuit.get_state()
print(f"Last Failure: {state['last_failure']}")
print(f"Failure Count: {state['failure_count']}")
print(f"State: {state['state']}")
```

**Solutions**:
1. Check upstream service health
2. Review error logs for patterns
3. Consider increasing timeout thresholds
4. Implement fallback mechanisms

### Circuit Constantly Opening

**Symptoms**: Circuit state frequently `open`

**Diagnosis**:
```python
# Check rejection rate
rejection_rate = state['metrics']['rejection_rate']
if rejection_rate > 0.01:
    print(f"High rejection rate: {rejection_rate:.2%}")
    print(f"Total rejected: {state['metrics']['total_rejected']}")
```

**Solutions**:
1. Increase `failure_threshold`
2. Increase `timeout` duration
3. Implement circuit breaker hierarchy
4. Add request queuing/buffering

### High Retry Delays

**Symptoms**: `avg_delay_seconds` > 10.0

**Diagnosis**:
```python
stats = manager.get_retry_stats()
print(f"Avg Delay: {stats['metrics']['avg_delay_seconds']:.2f}s")
print(f"Max Delay: {stats['metrics']['max_delay_seconds']:.2f}s")
print(f"Avg Retries: {stats['avg_retries_per_context']:.2f}")
```

**Solutions**:
1. Reduce `max_delay` in retry policy
2. Use linear backoff instead of exponential
3. Reduce `max_attempts`
4. Implement timeout on retry operations

### Low Immediate Success Rate

**Symptoms**: `immediate_success` / `total_contexts` < 0.70

**Diagnosis**:
```python
stats = manager.get_retry_stats()
immediate_rate = stats['metrics']['immediate_success'] / stats['total_contexts']
print(f"Immediate Success Rate: {immediate_rate:.2%}")

# Check error categories
errors = stats['metrics']['error_categories']
for category, count in sorted(errors.items(), key=lambda x: x[1], reverse=True):
    print(f"{category}: {count}")
```

**Solutions**:
1. Investigate upstream service reliability
2. Check for rate limiting issues
3. Review timeout configurations
4. Consider caching frequently accessed data

---

## Related Documentation

- [Production Observability Guide](production-observability-guide.md) - Comprehensive observability setup
- [Architecture Overview](architecture.md) - System architecture
- [Security Audit Report](security-audit-report.md) - Security assessment

## API References

- [`CircuitBreaker.get_state()`](../packages/paracle_resilience/circuit_breaker.py) - Circuit breaker metrics API
- [`RetryManager.get_retry_stats()`](../packages/paracle_orchestration/retry.py) - Retry manager metrics API

---

**Last Updated**: 2026-01-10
**Version**: 1.0
**Status**: Active
