# Audit Trail Guide

Paracle provides a tamper-evident audit trail for ISO 42001 compliance.

## Overview

The audit system provides:

- **Event Recording**: Log all agent actions and governance decisions
- **Hash Chain Integrity**: Tamper-evident storage using SHA-256
- **Export Formats**: JSON, CSV, JSONL, and Syslog (RFC 5424)
- **Compliance Reports**: Generate audit reports for compliance reviews

## Quick Start

```python
from paracle_audit import AuditTrail, AuditEventType

# Initialize audit trail
trail = AuditTrail()

# Record an event
event = trail.record(
    event_type=AuditEventType.AGENT_ACTION,
    actor="coder",
    action="write_file",
    target="/app/main.py",
    outcome="success",
)

print(f"Event ID: {event.event_id}")
print(f"Hash: {event.event_hash}")
```

## Event Types

| Type | Description |
|------|-------------|
| `AGENT_ACTION` | Agent performed an action |
| `POLICY_EVALUATED` | Policy was evaluated |
| `POLICY_VIOLATED` | Policy violation occurred |
| `APPROVAL_REQUESTED` | Human approval requested |
| `APPROVAL_GRANTED` | Approval was granted |
| `APPROVAL_DENIED` | Approval was denied |
| `RISK_ASSESSED` | Risk score calculated |
| `SYSTEM_EVENT` | System-level event |
| `ERROR` | Error occurred |

## Event Outcomes

| Outcome | Description |
|---------|-------------|
| `SUCCESS` | Action completed successfully |
| `FAILURE` | Action failed |
| `DENIED` | Action was denied by policy |
| `PENDING` | Action awaiting approval |
| `CANCELLED` | Action was cancelled |
| `ERROR` | Error during execution |

## Recording Events

### Basic Event

```python
event = trail.record(
    event_type=AuditEventType.AGENT_ACTION,
    actor="coder",
    action="write_file",
    target="/app/main.py",
    outcome="success",
)
```

### Event with Context

```python
event = trail.record(
    event_type=AuditEventType.AGENT_ACTION,
    actor="coder",
    actor_type="agent",
    action="write_file",
    target="/app/main.py",
    outcome="success",
    context={
        "file_size": 1024,
        "lines_changed": 50,
    },
    risk_score=35.5,
    risk_level="MEDIUM",
    policy_id="audit_all_file_writes",
    iso_control="9.1",
    correlation_id="req-12345",
    session_id="sess-67890",
)
```

## Querying Events

```python
# Query by time range
from datetime import datetime, timedelta

events = trail.query(
    start_time=datetime.utcnow() - timedelta(hours=24),
    end_time=datetime.utcnow(),
)

# Query by actor
events = trail.query(actor="coder")

# Query by event type
events = trail.query(event_type=AuditEventType.POLICY_VIOLATED)

# Query by outcome
events = trail.query(outcome=AuditOutcome.DENIED)

# Combined filters
events = trail.query(
    actor="coder",
    event_type=AuditEventType.AGENT_ACTION,
    start_time=datetime.utcnow() - timedelta(days=7),
    limit=100,
)
```

## Hash Chain Integrity

Events are linked using SHA-256 hash chains:

```python
from paracle_audit import IntegrityVerifier

verifier = IntegrityVerifier(trail.storage)

# Verify entire chain
result = verifier.verify_chain()
print(f"Valid: {result.valid}")
print(f"Events verified: {result.events_verified}")

# Verify specific event
event_result = verifier.verify_event(event_id)
print(f"Event valid: {event_result.valid}")
```

### Hash Chain Structure

```
Event N:
  event_hash = SHA256(event_id + timestamp + actor + action + ... + previous_hash)
  previous_hash = Event N-1 hash

Event N+1:
  event_hash = SHA256(... + previous_hash)
  previous_hash = Event N hash
```

## Export Formats

### JSON Export

```python
from paracle_audit import AuditExporter, ExportFormat

exporter = AuditExporter(trail.storage)

# Export to file
exporter.export_to_file(
    "audit_report.json",
    format=ExportFormat.JSON,
    start_time=datetime(2026, 1, 1),
)

# Export to string
data = exporter.export_to_string(format=ExportFormat.JSON)
```

### CSV Export

```python
exporter.export_to_file(
    "audit_report.csv",
    format=ExportFormat.CSV,
    actor="coder",
)
```

### JSON Lines (JSONL)

For SIEM integration:

```python
exporter.export_to_file(
    "audit_stream.jsonl",
    format=ExportFormat.JSONL,
)
```

### Syslog Format (RFC 5424)

```python
exporter.export_to_file(
    "audit.log",
    format=ExportFormat.SYSLOG,
)
```

Output format:
```
<86>1 2026-01-07T10:30:00.000000Z paracle audit evt-12345 - event_type=agent_action actor=coder action=write_file outcome=success
```

## CLI Commands

### Search Events

```bash
# Search by actor
paracle audit search --actor coder

# Search by event type
paracle audit search --type agent_action

# Search by time range
paracle audit search --since 24h
paracle audit search --since 7d
paracle audit search --start 2026-01-01 --end 2026-01-07

# Search by outcome
paracle audit search --outcome denied

# Combined search
paracle audit search --actor coder --type policy_violated --since 7d
```

### Show Event Details

```bash
paracle audit show <event_id>
paracle audit show evt-12345 --json
```

### Export Events

```bash
# Export to JSON
paracle audit export audit_report.json --format json

# Export to CSV
paracle audit export audit_report.csv --format csv

# Export with filters
paracle audit export report.json \
    --format json \
    --actor coder \
    --since 30d
```

### Verify Integrity

```bash
# Verify entire chain
paracle audit verify

# Verify specific event
paracle audit verify --event evt-12345
```

### View Statistics

```bash
paracle audit stats
paracle audit stats --since 7d
```

### Generate Compliance Report

```bash
paracle audit report
paracle audit report --since 30d --output compliance_report.json
```

## Storage Configuration

### SQLite Storage (Default)

```python
from paracle_audit import SQLiteAuditStorage, AuditTrail

storage = SQLiteAuditStorage("./audit.db")
trail = AuditTrail(storage=storage)
```

### Custom Storage

Implement the `AuditStorage` protocol:

```python
from paracle_audit import AuditStorage

class MyStorage(AuditStorage):
    def store(self, event: AuditEvent) -> None:
        # Store event
        pass

    def query(self, **filters) -> list[AuditEvent]:
        # Query events
        pass

    def get_latest_hash(self) -> str | None:
        # Get hash of most recent event
        pass
```

## Retention Policies

Configure retention in storage:

```python
# Apply retention policy (delete events older than 90 days)
deleted = storage.apply_retention(days=90)
print(f"Deleted {deleted} old events")
```

CLI:
```bash
paracle audit retention --days 90 --dry-run
paracle audit retention --days 90 --apply
```

## Security Considerations

### Path Traversal Protection

Export paths are validated to prevent:
- Path traversal attacks (`../`)
- Home directory expansion (`~`)
- Writing to system directories

### Tamper Detection

The hash chain allows detection of:
- Modified events
- Deleted events
- Inserted events
- Reordered events

## Compliance Reports

Generate structured compliance reports:

```python
report = exporter.generate_compliance_report(
    start_time=datetime(2026, 1, 1),
    end_time=datetime(2026, 1, 31),
)

print(f"Total Events: {report['summary']['total_events']}")
print(f"Policy Violations: {report['compliance']['policy_violations_count']}")
print(f"High Risk Actions: {report['compliance']['high_risk_actions_count']}")
```

Report structure:
```json
{
    "report_time": "2026-01-07T12:00:00",
    "period": {
        "start": "2026-01-01T00:00:00",
        "end": "2026-01-31T23:59:59"
    },
    "summary": {
        "total_events": 1500,
        "by_type": {"agent_action": 1200, "policy_evaluated": 250},
        "by_outcome": {"success": 1400, "denied": 50},
        "by_risk_level": {"low": 1000, "medium": 400, "high": 100}
    },
    "compliance": {
        "policy_violations_count": 15,
        "high_risk_actions_count": 100
    },
    "recommendations": [
        "15 policy violations detected. Review policy configurations."
    ]
}
```

## Best Practices

1. **Enable audit for all environments**: Not just production
2. **Set appropriate retention**: Balance compliance requirements with storage
3. **Regular integrity checks**: Schedule periodic verification
4. **Export for long-term storage**: Archive to immutable storage
5. **Monitor high-risk events**: Alert on critical outcomes

## See Also

- [Governance Guide](governance-guide.md)
- [Compliance Reports](compliance-guide.md)
- [ISO 42001 Mapping](iso-42001-mapping.md)
