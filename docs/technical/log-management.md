# Log Management Guide

**Version**: 1.0
**Last Updated**: 2026-01-04
**Status**: Active

---

## Overview

Paracle implements enterprise-grade log management following CrowdStrike best practices. This guide covers everything you need to know about logging in Paracle.

### Quick Links

- [Log Architecture](#log-architecture)
- [Getting Started](#getting-started)
- [Search & Analysis](#search--analysis)
- [Configuration](#configuration)
- [CLI Commands](#cli-commands)
- [Compliance](#compliance)
- [Troubleshooting](#troubleshooting)

---

## Log Architecture

Paracle uses a **three-tier logging architecture**:

```
┌─────────────────────────────────────────────────────┐
│                  FRAMEWORK LOGS                     │
│           ~/.paracle/logs/                          │
│   • Core framework operations                       │
│   • LLM provider interactions                       │
│   • Workflow orchestration                          │
│   • Retention: 90 days                              │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                 GOVERNANCE LOGS                     │
│          .parac/memory/logs/                        │
│   • Development decisions                           │
│   • Agent actions (implementation, review)          │
│   • Architecture decisions (ADRs)                   │
│   • Retention: Permanent (version controlled)       │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                  RUNTIME LOGS                       │
│        .parac/memory/logs/runtime/                  │
│   • Agent execution                                 │
│   • Workflow runs                                   │
│   • Errors and exceptions                           │
│   • Retention: 30 days (security: 365 days)         │
└─────────────────────────────────────────────────────┘
```

### Why Three Tiers?

1. **Framework Logs**: System-level, shared across projects
2. **Governance Logs**: Project-specific, permanent audit trail
3. **Runtime Logs**: High-volume execution data, temporary

---

## Getting Started

### Basic Logging

```python
from paracle_core.logging import get_logger

logger = get_logger(__name__)

# Simple logging
logger.info("Operation started")
logger.warning("Resource usage high")
logger.error("Failed to connect")

# With context
logger.info(
    "Agent execution completed",
    extra={
        "agent_id": "coder",
        "workflow_id": "wf_123",
        "duration_ms": 1234.56,
        "cost": 0.05
    }
)
```

### Structured Logging (JSON)

```python
logger.info(
    "Workflow step completed",
    extra={
        "context": {
            "workflow_id": "wf_123",
            "step_name": "build",
            "step_index": 2,
            "agent_id": "coder"
        },
        "metadata": {
            "hostname": "prod-01",
            "region": "us-east-1"
        },
        "duration_ms": 5432.1,
        "cost": 0.10
    }
)
```

Output (JSON):
```json
{
  "timestamp": "2026-01-04T15:30:45.123456Z",
  "level": "INFO",
  "logger": "paracle.orchestration.engine",
  "correlation_id": "01HN8X3QGPZ9K2M1V0E4R5T6W7",
  "message": "Workflow step completed",
  "context": {
    "workflow_id": "wf_123",
    "step_name": "build",
    "step_index": 2,
    "agent_id": "coder"
  },
  "metadata": {
    "hostname": "prod-01",
    "region": "us-east-1"
  },
  "duration_ms": 5432.1,
  "cost": 0.10
}
```

### Correlation IDs (Tracing)

Correlation IDs allow you to trace a request across multiple operations:

```python
from paracle_core.logging import correlation_id, get_logger

logger = get_logger(__name__)

# Automatic correlation ID in context manager
with correlation_id() as cid:
    logger.info("Starting workflow")  # cid automatically included

    # Call other functions/services
    execute_step_1()  # Same cid
    execute_step_2()  # Same cid

    logger.info("Workflow completed")  # Same cid

# All logs from this execution have the same correlation_id
```

---

## Search & Analysis

### Using LogManager

```python
from paracle_core.logging.management import LogManager

manager = LogManager()

# Search by level
errors = manager.search(level="ERROR", limit=100)

# Search by time range
recent = manager.search(since="1h ago", until="now")

# Search by agent
agent_logs = manager.search(agent_id="coder", since="24h ago")

# Search by correlation ID (trace request)
trace = manager.search(correlation_id="01HN8X3QGPZ9K2M1V0E4R5T6W7")

# Full-text search
keyword_results = manager.search(keyword="authentication failed")

# Combined filters
results = manager.search(
    level="ERROR",
    agent_id="coder",
    since="6h ago",
    keyword="timeout",
    limit=50
)

# Print results
for entry in results:
    print(f"[{entry.timestamp}] {entry.level}: {entry.message}")
    if entry.context:
        print(f"  Agent: {entry.context.get('agent_id')}")
        print(f"  Workflow: {entry.context.get('workflow_id')}")
```

### Aggregation & Statistics

```python
# Count logs by agent
by_agent = manager.aggregate(group_by="agent_id", metric="count")
# Result: {"coder": 1234, "tester": 567, "reviewer": 890}

# Sum costs by agent
costs = manager.aggregate(
    group_by="agent_id",
    metric="sum",
    field="cost",
    since="24h ago"
)
# Result: {"coder": 5.67, "tester": 2.34, "reviewer": 1.23}

# Average duration by workflow
durations = manager.aggregate(
    group_by="workflow_id",
    metric="avg",
    field="duration_ms"
)

# Get overall statistics
stats = manager.stats(since="24h ago")
print(f"Total logs: {stats.total_count}")
print(f"Errors: {stats.error_count} ({stats.error_rate*100:.1f}%)")
print(f"Unique agents: {stats.unique_agents}")
print(f"Avg duration: {stats.avg_duration_ms:.0f}ms")
print(f"Total cost: ${stats.total_cost:.2f}")
```

### Anomaly Detection

```python
# Detect error rate spikes
anomalies = manager.detect_anomalies(metric="error_rate", threshold=2.0)

for anomaly in anomalies:
    print(f"Anomaly detected at {anomaly['timestamp']}")
    print(f"  {anomaly['metric']}: {anomaly['value']:.4f}")
    print(f"  Mean: {anomaly['mean']:.4f}")
    print(f"  Z-score: {anomaly['z_score']:.2f}")

# Detect log volume anomalies
volume_anomalies = manager.detect_anomalies(metric="log_volume", threshold=3.0)

# Detect performance degradation
perf_anomalies = manager.detect_anomalies(metric="duration_ms", threshold=2.0)
```

---

## CLI Commands

### Search Logs

```bash
# Search by level
paracle logs search --level ERROR

# Search by time range
paracle logs search --since "2026-01-04 14:00" --until "2026-01-04 15:00"
paracle logs search --since "1h ago"
paracle logs search --since "2d ago"

# Search by agent
paracle logs search --agent coder --level ERROR

# Search by correlation ID (trace)
paracle logs search --correlation-id 01HN8X3QGPZ9K2M1V0E4R5T6W7

# Search by keyword
paracle logs search "failed to authenticate"

# Combined filters
paracle logs search --level ERROR --agent coder --since "6h ago" --limit 100

# Export results
paracle logs search --level ERROR --format csv --output errors.csv
paracle logs search --since "24h ago" --format json --output logs.json
```

### Statistics

```bash
# Overall stats
paracle logs stats

# Stats for specific time range
paracle logs stats --since "24h ago"

# Stats by agent
paracle logs stats --group-by agent_id

# Stats by workflow
paracle logs stats --group-by workflow_id

# Cost analysis
paracle logs cost --since "7d ago" --group-by agent_id
```

### Anomaly Detection

```bash
# Detect anomalies in error rate
paracle logs anomalies --metric error_rate --threshold 2.0

# Detect anomalies in log volume
paracle logs anomalies --metric log_volume --threshold 3.0

# Detect performance issues
paracle logs anomalies --metric duration_ms --threshold 2.5
```

### Maintenance

```bash
# Check log health
paracle logs health

# Validate configuration
paracle logs validate-config

# Cleanup old logs (dry run)
paracle logs cleanup --dry-run

# Cleanup old logs (execute)
paracle logs cleanup

# Compress old logs
paracle logs compress --older-than 7d

# Reindex logs
paracle logs reindex
```

### Compliance

```bash
# Generate compliance report
paracle logs compliance-report --standard ISO42001
paracle logs compliance-report --standard ISO27001 --since "2025-01-01"
paracle logs compliance-report --standard GDPR --format pdf --output report.pdf
```

---

## Configuration

### Project Configuration (`.parac/project.yaml`)

```yaml
logging:
  # Global settings
  level: INFO
  format: json

  # Centralized aggregation
  centralized:
    enabled: true
    type: local  # or: elasticsearch, splunk, datadog

  # Rotation
  rotation:
    strategy: daily
    backup_count: 30
    compression: true

  # Retention (days)
  retention:
    framework: 90
    runtime: 30
    security: 365
    errors: 90

  # Monitoring
  monitoring:
    enabled: true
    error_threshold: 0.05  # 5%
    disk_warning: 0.80

  # Security
  security:
    pii_redaction: true
    access_control: true
    audit_logging: true
```

### Runtime Configuration (`.parac/memory/logs/runtime/config.yaml`)

Full configuration with 400+ options. See: `.parac/memory/logs/runtime/config.yaml`

Key sections:
- **Centralized aggregation**: Local + external (Elasticsearch, Splunk, etc.)
- **Levels**: Per-component and per-agent log levels
- **Format**: JSON vs plain text
- **Rotation**: Daily, weekly, size-based
- **Retention**: Per-category retention policies
- **Monitoring**: Thresholds and alerting
- **Security**: PII redaction, encryption, access control
- **Performance**: Async logging, batching, rate limiting

---

## Best Practices

### 1. Use Structured Logging

✅ **Good**:
```python
logger.info("User login successful", extra={"user_id": user.id, "ip": request.ip})
```

❌ **Bad**:
```python
logger.info(f"User {user.id} logged in from {request.ip}")
```

### 2. Add Context to All Logs

Always include relevant context:
```python
logger.error(
    "Failed to execute agent",
    extra={
        "agent_id": agent.id,
        "workflow_id": workflow.id,
        "error_type": type(e).__name__,
        "error_message": str(e)
    },
    exc_info=True  # Include stack trace
)
```

### 3. Use Correlation IDs

For any multi-step operation:
```python
with correlation_id() as cid:
    logger.info("Starting deployment")
    deploy_step_1()
    deploy_step_2()
    deploy_step_3()
    logger.info("Deployment completed")
```

### 4. Never Log Sensitive Data

❌ **Never log**:
- API keys
- Passwords
- PII (emails, names, addresses)
- Credit card numbers
- Health data

✅ **Instead**:
```python
# Hash sensitive data
api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:8]
logger.info("API authenticated", extra={"api_key_hash": api_key_hash})
```

### 5. Choose Appropriate Log Levels

- **DEBUG**: Detailed diagnostic info (disabled in production)
- **INFO**: General informational messages
- **WARNING**: Warning messages (potential issues)
- **ERROR**: Error messages (operation failed)
- **CRITICAL**: Critical errors (system failure)

### 6. Log Cost Information

For LLM operations:
```python
logger.info(
    "LLM request completed",
    extra={
        "provider": "openai",
        "model": "gpt-4",
        "tokens_input": 1234,
        "tokens_output": 567,
        "cost": 0.05  # USD
    }
)
```

---

## Compliance

### ISO 42001 (AI Management)

Required logging:
- ✅ Immutable audit trail (governance logs)
- ✅ Tamper-proof timestamps
- ✅ User action tracking
- ✅ Model decision logging
- ✅ Data lineage tracking

```python
# Generate compliance report
report = manager.compliance_report(standard="ISO42001", since="2025-01-01")
```

### ISO 27001 (Information Security)

Required logging:
- ✅ Security events (365-day retention)
- ✅ Access control auditing
- ✅ Incident response logging
- ✅ Change management

### GDPR (Data Protection)

Required controls:
- ✅ PII redaction in logs
- ✅ Right to erasure (log anonymization)
- ✅ Data breach logging
- ✅ Consent tracking

---

## Troubleshooting

### Issue: Can't Find Recent Logs

**Solution**: Reindex logs
```bash
paracle logs reindex
```

### Issue: Disk Space Full

**Solution**: Run cleanup
```bash
# Check what would be deleted
paracle logs cleanup --dry-run

# Execute cleanup
paracle logs cleanup

# Compress old logs
paracle logs compress --older-than 7d
```

### Issue: High Error Rate

**Solution**: Use anomaly detection and search
```bash
# Detect anomalies
paracle logs anomalies --metric error_rate

# Search recent errors
paracle logs search --level ERROR --since "1h ago" --limit 100

# Group errors by type
paracle logs stats --level ERROR --group-by error_type
```

### Issue: Slow Search Performance

**Solution**: Reindex and optimize
```bash
# Reindex all logs
paracle logs reindex

# Check index size
paracle logs health

# Optimize search by using filters
paracle logs search --agent coder --since "6h ago"  # Faster
paracle logs search --keyword "error"  # Slower (full-text)
```

---

## Integration Examples

### Elasticsearch

```yaml
# .parac/memory/logs/runtime/config.yaml
centralized:
  enabled: true
  type: elasticsearch
  elasticsearch:
    enabled: true
    endpoint: http://localhost:9200
    index_prefix: paracle-runtime
    username: elastic
    password: changeme
```

### Splunk

```yaml
centralized:
  enabled: true
  type: splunk
  splunk:
    enabled: true
    hec_endpoint: https://splunk.example.com:8088
    hec_token: your-hec-token
    index: paracle_runtime
```

### Datadog

```yaml
centralized:
  enabled: true
  type: datadog
  datadog:
    enabled: true
    api_key: your-datadog-api-key
    site: datadoghq.com
    service: paracle-runtime
```

---

## Advanced Topics

### Custom Log Handlers

```python
from paracle_core.logging import ParacleLogger, ParacleStreamHandler

# Create custom handler
handler = ParacleStreamHandler()
handler.setLevel("INFO")

# Add to logger
logger = ParacleLogger(__name__)
logger.addHandler(handler)
```

### Log Sampling

For high-volume scenarios:
```yaml
# config.yaml
performance:
  sampling:
    enabled: true
    debug_rate: 0.10   # Log only 10% of DEBUG messages
    info_rate: 1.0     # Log all INFO
    warning_rate: 1.0  # Log all WARNING
    error_rate: 1.0    # Log all ERROR
```

### Distributed Tracing (Future)

```python
from paracle_core.logging import with_tracing

@with_tracing
async def execute_workflow(workflow_id: str):
    # Automatic span creation and tracing
    logger.info("Workflow started")
    await step_1()
    await step_2()
    logger.info("Workflow completed")
```

---

## References

### Documentation
- [LOG_MANAGEMENT.md](../.parac/policies/LOG_MANAGEMENT.md) - Full policy
- [architecture.md](./architecture.md) - System architecture
- [SECURITY.md](../.parac/policies/SECURITY.md) - Security policy

### Standards
- [ISO 42001](https://www.iso.org/standard/81230.html) - AI Management
- [ISO 27001](https://www.iso.org/standard/27001) - Information Security
- [GDPR](https://gdpr.eu/) - Data Protection

### External Resources
- [CrowdStrike Log Management](https://www.crowdstrike.com/en-us/cybersecurity-101/next-gen-siem/log-management/)
- [12-Factor App: Logs](https://12factor.net/logs)
- [OpenTelemetry](https://opentelemetry.io/docs/specs/otel/logs/)

---

**Need Help?**
- GitHub Issues: https://github.com/IbIFACE-Tech/paracle-lite/issues
- Email: support@ibiface-tech.com
- Documentation: https://paracle.readthedocs.io
