# Compliance Guide

Paracle supports ISO/IEC 42001 AI Management System compliance through integrated governance, audit, and reporting capabilities.

## ISO 42001 Overview

ISO/IEC 42001 is the international standard for AI management systems. Paracle provides tools to help organizations achieve and maintain compliance.

## Key Controls Supported

| Control | Section | Paracle Feature |
|---------|---------|-----------------|
| 6.1 | Risk Assessment | Risk Scoring System |
| 6.2 | Risk Treatment | Policy Engine |
| 7.2 | Competence | Agent Trust Levels |
| 8.2 | AI System Development | Governance Policies |
| 9.1 | Monitoring | Audit Trail |
| 9.2 | Internal Audit | Compliance Reports |
| 10.1 | Nonconformity | Policy Violations |

## Quick Start

### Check Compliance Status

```bash
paracle compliance status
```

Output:
```
ISO 42001 Compliance Status

Section 6 - Planning
  [OK] 6.1 Risk Assessment    3 active risk policies
  [OK] 6.2 Risk Treatment     Risk thresholds configured

Section 7 - Support
  [~]  7.2 Competence         Agent trust levels defined

Section 8 - Operation
  [OK] 8.2 System Development 5 development policies

Section 9 - Performance Evaluation
  [OK] 9.1 Monitoring         Audit trail enabled
  [OK] 9.2 Internal Audit     2,450 events in audit trail
```

### Generate Compliance Report

```bash
paracle compliance report --output compliance_report.json
```

## Policy-to-Control Mapping

### Defining Control Mappings

```yaml
policies:
  - id: audit_all_actions
    name: Audit All Actions
    type: audit
    actions: ["*"]
    iso_control: "9.1"  # Maps to ISO 42001 Section 9.1
    risk_level: low

  - id: require_approval_high_risk
    name: Require Approval for High Risk
    type: require_approval
    conditions:
      - field: risk_score
        operator: gte
        value: 80
    iso_control: "6.2"  # Maps to Risk Treatment
    risk_level: high
    approval_required_by: ["admin", "security"]
```

### Viewing Control Mappings

```bash
# List controls and their policies
paracle compliance controls

# Export control mappings
paracle compliance export-controls --output controls.json
```

## Risk Assessment (Section 6.1)

### Configuring Risk Scoring

```python
from paracle_governance import RiskScorer
from paracle_governance.risk.thresholds import RiskThresholds

# Configure custom thresholds
thresholds = RiskThresholds(
    low_max=25,
    medium_max=50,
    high_max=75,
    # Above 75 is CRITICAL
)

scorer = RiskScorer(thresholds=thresholds)
```

### Risk Factors

| Factor | Description | Weight |
|--------|-------------|--------|
| Data Sensitivity | Classification level | 25% |
| Action Type | Read/Write/Delete/Execute | 20% |
| Agent Trust | Established trust level | 15% |
| Historical Behavior | Past compliance record | 10% |
| Time of Day | Business hours factor | 5% |
| Resource Scope | Impact breadth | 10% |
| External Dependency | Third-party involvement | 10% |
| Reversibility | Can action be undone | 5% |

### Risk Assessment CLI

```bash
# Calculate risk for an action
paracle governance risk coder delete_file \
    --target /app/database.py \
    --data-sensitivity confidential

# Output:
# Risk Score: 72.5 (HIGH)
# Recommended Action: REQUIRE_APPROVAL
```

## Audit Trail (Section 9.1)

### Required Audit Events

For ISO 42001 compliance, ensure these events are recorded:

1. **Agent Actions**: All actions taken by AI agents
2. **Policy Evaluations**: When policies are checked
3. **Policy Violations**: When actions are denied
4. **Approval Workflows**: Requests and decisions
5. **Risk Assessments**: Risk calculations
6. **System Changes**: Configuration modifications

### Audit Configuration

```python
from paracle_audit import AuditTrail

# Initialize with compliance mode
trail = AuditTrail(
    storage_path="./audit.db",
    retention_days=365,  # 1 year for compliance
    integrity_check_interval=3600,  # Hourly verification
)
```

### Integrity Verification

```bash
# Verify audit trail integrity
paracle audit verify

# Output:
# Verifying audit trail integrity...
# Total events: 2,450
# Chain verified: OK
# No tampering detected
```

## Compliance Reports

### Generating Reports

```python
from paracle_audit import AuditExporter

exporter = AuditExporter(storage)

# Generate compliance report
report = exporter.generate_compliance_report(
    start_time=datetime(2026, 1, 1),
    end_time=datetime(2026, 1, 31),
)

# Access report sections
print(f"Total Events: {report['summary']['total_events']}")
print(f"Violations: {report['compliance']['policy_violations_count']}")
print(f"High Risk: {report['compliance']['high_risk_actions_count']}")
```

### Report Structure

```json
{
    "report_time": "2026-01-07T12:00:00",
    "period": {
        "start": "2026-01-01",
        "end": "2026-01-31"
    },
    "summary": {
        "total_events": 2450,
        "by_type": {
            "agent_action": 2000,
            "policy_evaluated": 400,
            "policy_violated": 50
        },
        "by_outcome": {
            "success": 2300,
            "denied": 100,
            "pending": 50
        },
        "by_risk_level": {
            "low": 1500,
            "medium": 700,
            "high": 200,
            "critical": 50
        },
        "by_iso_control": {
            "6.1": 200,
            "6.2": 150,
            "8.2": 500,
            "9.1": 2450
        }
    },
    "compliance": {
        "policy_violations_count": 50,
        "policy_violations": [...],
        "high_risk_actions_count": 250,
        "high_risk_actions": [...]
    },
    "recommendations": [
        "50 policy violations detected. Review policy configurations.",
        "250 high-risk actions detected. Consider additional approval workflows."
    ]
}
```

### CLI Report Generation

```bash
# Generate JSON report
paracle compliance report --output report.json

# Generate with time range
paracle compliance report --since 30d --output monthly_report.json

# Check compliance gaps
paracle compliance gaps
```

## Compliance Gaps Analysis

### Identifying Gaps

```bash
paracle compliance gaps
```

Output:
```
ISO 42001 Compliance Gaps

Section 6.1 - Risk Assessment
  [!] No risk policies for 'execute_command' action
  [!] Risk thresholds not configured for agent 'untrusted'

Section 7.2 - Competence
  [!] 2 agents without defined trust levels

Section 9.1 - Monitoring
  [OK] All required event types being captured

Recommendations:
1. Add risk policy for 'execute_command' action
2. Define trust levels for all agents
```

### Addressing Gaps

1. **Missing Policies**: Create policies covering identified gaps
2. **Incomplete Configuration**: Update agent and risk configurations
3. **Audit Coverage**: Ensure all required events are captured

## Approval Workflows (Section 10.1)

### Configuring Approvals

```yaml
policies:
  - id: approval_external_api
    name: Approve External API Calls
    type: require_approval
    actions:
      - external_api
      - http_request
    approval_required_by:
      - security
      - admin
    iso_control: "6.2"
```

### Managing Approvals

```bash
# List pending approvals
paracle approvals list --status pending

# Approve request
paracle approvals approve <request_id> --approver admin

# Deny request
paracle approvals deny <request_id> --reason "Insufficient justification"
```

## Best Practices

### 1. Regular Audits

Schedule regular compliance checks:

```bash
# Weekly compliance check
0 9 * * 1 paracle compliance status --json >> /var/log/compliance.log
```

### 2. Retention Policies

Configure appropriate retention:

```bash
# Apply 1-year retention
paracle audit retention --days 365 --apply
```

### 3. Export for Archive

Archive audit data to immutable storage:

```bash
# Monthly archive
paracle audit export monthly_archive.jsonl \
    --format jsonl \
    --start $(date -d '1 month ago' +%Y-%m-01) \
    --end $(date +%Y-%m-01)
```

### 4. Integrity Monitoring

Schedule integrity verification:

```bash
# Daily integrity check
0 0 * * * paracle audit verify --alert-on-failure
```

### 5. Documentation

Maintain documentation of:
- Policy decisions and rationale
- Approval workflow outcomes
- Compliance report reviews
- Remediation actions taken

## Integration with External Systems

### SIEM Integration

Export to SIEM in Syslog format:

```bash
paracle audit export --format syslog | nc siem.example.com 514
```

### Compliance Management Tools

Export control mappings for GRC tools:

```bash
paracle compliance export-controls \
    --format json \
    --output controls_export.json
```

## See Also

- [Governance Guide](governance-guide.md)
- [Audit Trail Guide](audit-guide.md)
- [Risk Scoring Reference](risk-scoring-reference.md)
