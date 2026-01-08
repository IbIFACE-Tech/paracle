# Governance Guide

Paracle provides a comprehensive governance layer for ISO 42001 AI Management System compliance.

## Overview

The governance system consists of:

- **Policy Engine**: Define and evaluate governance policies
- **Risk Scoring**: Calculate risk scores for agent actions
- **Audit Trail**: Tamper-evident audit logging
- **Compliance Reports**: Generate compliance reports

## Quick Start

```python
from paracle_governance import PolicyEngine, RiskScorer

# Initialize policy engine
engine = PolicyEngine(load_defaults=True)

# Evaluate an action
result = engine.evaluate(
    action="write_file",
    context={"path": "/app/config.py"},
    agent="coder"
)

if result.allowed:
    print("Action allowed")
else:
    print(f"Action denied: {result.reason}")
```

## Policy Types

| Type | Description |
|------|-------------|
| `ALLOW` | Permit specific actions |
| `DENY` | Block specific actions |
| `REQUIRE_APPROVAL` | Require human approval |
| `AUDIT` | Log action for compliance |
| `RATE_LIMIT` | Limit action frequency |
| `ESCALATE` | Escalate to higher authority |

## Defining Policies

### YAML Format

```yaml
policies:
  - id: deny_system_file_deletion
    name: Deny System File Deletion
    description: Prevent agents from deleting system files
    type: deny
    actions:
      - delete_file
    conditions:
      - field: context.path
        operator: matches
        value: "^/(etc|usr|bin|sbin).*"
    priority: 900
    iso_control: "8.2"
    risk_level: critical
```

### Loading Policies

```python
# Load from file
engine.load_policies("policies.yaml")

# Load from directory
engine.load_policies("./policies/")

# Load from string
engine.load_policies_from_string(yaml_content)
```

## Policy Conditions

Conditions support these operators:

| Operator | Description | Example |
|----------|-------------|---------|
| `eq` | Equal | `field == value` |
| `ne` | Not equal | `field != value` |
| `in` | In list | `field in [a, b, c]` |
| `not_in` | Not in list | `field not in [a, b]` |
| `contains` | Contains substring | `"test" in field` |
| `matches` | Regex match | `field matches pattern` |
| `gt`, `lt` | Greater/less than | `field > value` |
| `gte`, `lte` | Greater/less or equal | `field >= value` |

### Example Conditions

```yaml
conditions:
  # Check agent trust level
  - field: agent.trust_level
    operator: in
    value: ["untrusted", "low"]

  # Check file path
  - field: context.path
    operator: matches
    value: "^/sensitive/.*"

  # Check data classification
  - field: context.data_classification
    operator: eq
    value: "confidential"
```

## Risk Scoring

The risk scoring system evaluates actions based on multiple factors:

### Risk Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| Data Sensitivity | 25 | PUBLIC to RESTRICTED |
| Action Type | 20 | READ to DELETE |
| Agent Trust | 15 | LOW to HIGH |
| Historical Behavior | 10 | Past violations |
| Time of Day | 5 | Business hours vs off-hours |
| Resource Scope | 10 | Single file vs system-wide |
| External Dependency | 10 | Internal vs external |
| Reversibility | 5 | Reversible vs permanent |

### Risk Levels

| Level | Score Range | Recommended Action |
|-------|-------------|-------------------|
| LOW | 0-30 | Allow |
| MEDIUM | 31-60 | Allow with logging |
| HIGH | 61-80 | Require approval |
| CRITICAL | 81-100 | Deny |

### Usage

```python
from paracle_governance import RiskScorer
from paracle_governance.risk.factors import DataSensitivity

scorer = RiskScorer()

result = scorer.calculate({
    "actor": "coder",
    "action": "delete_file",
    "target": "/app/config.py",
    "data_sensitivity": DataSensitivity.CONFIDENTIAL,
})

print(f"Risk Score: {result.score}")
print(f"Risk Level: {result.level}")
print(f"Recommended Action: {result.action}")
```

## CLI Commands

### List Policies

```bash
# List enabled policies
paracle governance list

# List all policies (including disabled)
paracle governance list --all

# Filter by type
paracle governance list --type deny

# Output as JSON
paracle governance list --json
```

### Show Policy Details

```bash
paracle governance show <policy_id>
paracle governance show deny_system_file_deletion --json
```

### Evaluate Actions

```bash
# Evaluate an action
paracle governance evaluate coder write_file --target /app/main.py

# With context
paracle governance evaluate coder external_api \
    --context "url=https://api.example.com" \
    --context "method=POST"
```

### Calculate Risk

```bash
paracle governance risk coder delete_file \
    --target /app/config.py \
    --data-sensitivity confidential
```

### Load Custom Policies

```bash
# Validate only
paracle governance load ./policies.yaml --validate-only

# Load policies
paracle governance load ./policies.yaml
```

## Default Policies

Paracle includes several default policies:

1. **deny_delete_system_files**: Prevents deletion of system files
2. **require_approval_external_api**: Requires approval for external API calls
3. **audit_all_file_writes**: Logs all file write operations
4. **deny_secret_access_untrusted**: Blocks secret access for untrusted agents

View defaults:
```bash
paracle governance defaults
```

## Integration with Agents

### Automatic Policy Enforcement

```python
from paracle_governance import PolicyEngine

engine = PolicyEngine(load_defaults=True, default_allow=False)

# In agent execution
result = engine.enforce(
    action="write_file",
    context={"path": "/etc/passwd"},
    agent="coder"
)
# Raises PolicyViolationError if denied
```

### Manual Checks

```python
# Simple boolean check
if engine.can_perform("write_file", agent="coder"):
    # Perform action
    pass

# Check approval requirements
requires_approval, roles = engine.requires_approval(
    "external_api",
    context={"url": "https://api.example.com"}
)
```

## ISO 42001 Mapping

Policies can be mapped to ISO 42001 controls:

| Control | Description | Default Policy |
|---------|-------------|----------------|
| 6.1 | Risk Assessment | Risk scoring |
| 6.2 | External Dependencies | require_approval_external_api |
| 7.2 | Access Control | deny_secret_access_untrusted |
| 8.2 | System Protection | deny_delete_system_files |
| 9.1 | Audit Logging | audit_all_file_writes |

## Security Considerations

### Regex Pattern Safety

The policy engine includes protection against ReDoS attacks:

- Pattern length limits (max 1000 chars)
- Dangerous pattern detection (nested quantifiers)
- Timeout protection on Unix systems

### Path Validation

Export paths are validated to prevent:

- Path traversal attacks (`../`)
- Home directory expansion (`~`)
- Writing to system directories

## Best Practices

1. **Start with defaults**: Load default policies first, then add custom ones
2. **Use high priority for deny rules**: Set priority 800-1000 for critical denials
3. **Test policies**: Use `--validate-only` before deploying
4. **Monitor compliance**: Review audit logs regularly
5. **Document exceptions**: Keep records of policy overrides

## See Also

- [Audit Trail Guide](audit-guide.md)
- [Compliance Reports](compliance-guide.md)
- [Risk Scoring Reference](risk-scoring-reference.md)
