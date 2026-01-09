# Health Checks Guide

Monitor and diagnose `paracle_meta` health.

## Overview

The health check system monitors:

- **Database** - Connection, pool health
- **Providers** - LLM provider availability
- **Learning Engine** - Template count, promotion status
- **Cost Tracker** - Budget usage and limits

## CLI Usage

```bash
# Quick health check
paracle meta health

# Detailed output
paracle meta health --verbose

# JSON output (for monitoring systems)
paracle meta health --json
```

## Health Status

| Status | Meaning |
|--------|---------|
| `HEALTHY` | All components operational |
| `DEGRADED` | Some components have issues but system works |
| `UNHEALTHY` | Critical components failing |

## Sample Output

### Healthy System

```
$ paracle meta health

Meta Engine Health Check
========================

Status: HEALTHY

Components:
  database: healthy (PostgreSQL, 5/10 connections)
  providers: healthy
    - anthropic: up (claude-sonnet-4-20250514)
    - openai: up (gpt-4o)
    - ollama: up (llama3.1)
  learning_engine: healthy (42 templates, 156 feedback entries)
  cost_tracker: healthy
    - daily: $2.50 / $10.00 (25%)
    - monthly: $45.00 / $100.00 (45%)

Version: 1.5.0
Uptime: 4h 23m 15s
```

### Degraded System

```
$ paracle meta health

Meta Engine Health Check
========================

Status: DEGRADED

Components:
  database: healthy (PostgreSQL)
  providers: degraded
    - anthropic: up
    - openai: DOWN (rate limited)
    - ollama: up
  learning_engine: healthy
  cost_tracker: warning (approaching daily limit)
    - daily: $8.50 / $10.00 (85%)
    - monthly: $92.00 / $100.00 (92%)

Warnings:
  - OpenAI rate limited, using fallback providers
  - Approaching daily budget limit (85%)

Version: 1.5.0
```

### Unhealthy System

```
$ paracle meta health

Meta Engine Health Check
========================

Status: UNHEALTHY

Components:
  database: DOWN (connection refused)
  providers: DOWN (no providers available)
  learning_engine: DOWN (database unavailable)
  cost_tracker: unknown

Errors:
  - Database connection failed: Connection refused
  - No LLM providers available
  - Cannot access learning engine

Action Required:
  - Check database connection string
  - Verify provider API keys
  - Run: paracle meta config validate

Version: 1.5.0
```

## JSON Output

For integration with monitoring systems:

```bash
paracle meta health --json
```

```json
{
  "status": "healthy",
  "version": "1.5.0",
  "uptime_seconds": 15795.5,
  "components": {
    "database": {
      "status": "healthy",
      "type": "postgresql",
      "pool_size": 10,
      "active_connections": 5
    },
    "providers": {
      "status": "healthy",
      "available": ["anthropic", "openai", "ollama"],
      "details": {
        "anthropic": {"status": "up", "model": "claude-sonnet-4-20250514"},
        "openai": {"status": "up", "model": "gpt-4o"},
        "ollama": {"status": "up", "model": "llama3.1"}
      }
    },
    "learning_engine": {
      "status": "healthy",
      "enabled": true,
      "template_count": 42,
      "feedback_count": 156
    },
    "cost_tracker": {
      "status": "healthy",
      "enabled": true,
      "daily_usage": 2.50,
      "daily_limit": 10.00,
      "daily_percentage": 25.0,
      "monthly_usage": 45.00,
      "monthly_limit": 100.00,
      "monthly_percentage": 45.0
    }
  },
  "warnings": [],
  "errors": []
}
```

## Python API

### Basic Health Check

```python
from paracle_meta import check_health, format_health_report
from paracle_meta.config import load_config

config = load_config()
health = await check_health(config)

print(f"Status: {health.status}")
print(f"Database: {health.database}")
print(f"Providers: {health.providers}")

# Formatted report
report = format_health_report(health)
print(report)
```

### HealthChecker Class

```python
from paracle_meta import HealthChecker

checker = HealthChecker(config)

# Full health check
health = await checker.check()

# Individual component checks
db_health = await checker.check_database()
provider_health = await checker.check_providers()
learning_health = await checker.check_learning_engine()
cost_health = await checker.check_cost_tracker()
```

### Health Status Model

```python
from paracle_meta import HealthCheck, HealthStatus

class HealthCheck:
    status: HealthStatus  # HEALTHY, DEGRADED, UNHEALTHY
    database: HealthStatus
    providers: dict[str, HealthStatus]
    learning_engine: HealthStatus
    cost_within_budget: bool
    version: str
    uptime_seconds: float
    warnings: list[str]
    errors: list[str]
```

## Component Health Details

### Database Health

Checks:
- Connection available
- Pool not exhausted
- Query latency acceptable (<100ms)

```python
db_health = await checker.check_database()
# Returns: HealthStatus with details about connection pool
```

### Provider Health

Checks:
- API key valid
- Provider responding
- Model available

```python
provider_health = await checker.check_providers()
# Returns: dict mapping provider name to status
```

### Learning Engine Health

Checks:
- Database accessible
- Template library loaded
- Feedback collection working

```python
learning_health = await checker.check_learning_engine()
# Returns: HealthStatus with template/feedback counts
```

### Cost Tracker Health

Checks:
- Budget tracking enabled
- Within daily limit
- Within monthly limit

```python
cost_health = await checker.check_cost_tracker()
# Returns: HealthStatus with usage percentages
```

## Alerts and Thresholds

### Cost Alerts

```yaml
cost:
  warning_threshold: 0.8  # Alert at 80%
  max_daily_budget: 10.0
  max_monthly_budget: 100.0
```

When approaching limits:
- **80%**: Warning status
- **100%**: Budget exceeded, fallback to cheaper models

### Connection Pool Alerts

```yaml
database:
  pool_size: 10
  pool_warning_threshold: 0.9  # Alert at 90% pool usage
```

## Monitoring Integration

### Prometheus Metrics

```python
# Expose metrics endpoint
from paracle_meta.health import get_metrics

metrics = get_metrics()
# Returns Prometheus-formatted metrics
```

### Health Endpoint

Add to your FastAPI app:

```python
from fastapi import FastAPI
from paracle_meta import check_health, load_config

app = FastAPI()
config = load_config()

@app.get("/health")
async def health():
    health = await check_health(config)
    return health.model_dump()

@app.get("/health/live")
async def liveness():
    return {"status": "ok"}

@app.get("/health/ready")
async def readiness():
    health = await check_health(config)
    if health.status == HealthStatus.UNHEALTHY:
        raise HTTPException(503, "Not ready")
    return {"status": "ready"}
```

## Troubleshooting

### Database Connection Failed

```bash
# Check connection string
paracle meta config show | grep postgres_url

# Test connection manually
psql "postgresql://user:pass@localhost/paracle_meta"
```

### Provider Down

```bash
# Check API key
echo $ANTHROPIC_API_KEY

# Test provider
paracle meta chat --provider anthropic
```

### Budget Exceeded

```bash
# Check current usage
paracle meta stats --period day

# Increase limit (temporary)
export PARACLE_META_MAX_DAILY_BUDGET=20.0
```

### Learning Engine Issues

```bash
# Check database tables
paracle meta db status

# Reset templates (careful!)
paracle meta templates reset --confirm
```

## Best Practices

1. **Monitor regularly** - Add to your CI/CD pipeline
2. **Set up alerts** - Use JSON output with monitoring tools
3. **Check before deployment** - Include in health checks
4. **Track trends** - Monitor cost and usage over time
5. **Have fallbacks** - Configure multiple providers
