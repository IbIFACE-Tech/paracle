# Paracle Compliance & Governance

> **User Guide**: Understanding Paracle's compliance capabilities

---

## Overview

Paracle provides built-in compliance and governance features to help you build enterprise-grade AI agent applications.

### What Paracle Offers

- **Audit Trail**: Automatic logging of all agent actions
- **Policy Enforcement**: Define and enforce governance policies
- **Supply Chain Security**: SBOM generation and artifact signing
- **Privacy Controls**: Data handling and retention policies
- **Agent Governance**: Control agent capabilities and autonomy

This makes Paracle suitable for regulated environments and enterprise deployments.

---

## Compliance Features

### Audit Logging

All agent actions are automatically logged with immutable audit trails:

```python
# Automatic logging - no code needed
agent.run(task="Deploy application")
# → Logged to .parac/memory/logs/agent_actions.log
```

**What's logged**:

- Agent ID and task
- Timestamp and duration
- Actions taken
- Results and artifacts

### Policy Enforcement

Define policies to control agent behavior:

```yaml
# .parac/policies/policy-pack.yaml
policies:
  - id: require_approval
    description: "Human approval for sensitive actions"
    rules:
      - pattern: "production_deploy"
        require_approval: true
```

### Supply Chain Security

Generate Software Bill of Materials (SBOM) for your deployments:

```bash
# Generate SBOM
paracle build sbom --output sbom.spdx.json

# Sign artifacts
paracle build sign --artifact myapp.tar.gz
```

### Privacy Controls

Configure data retention and handling:

```yaml
# .parac/policies/retention.yaml
retention:
  agent_logs: 90_days
  user_data: 1_year
  artifacts: 6_months
```

---

## Getting Started

### 1. Enable Audit Logging

Audit logging is enabled by default. Logs are stored in:

```
.parac/memory/logs/agent_actions.log
```

### 2. Define Policies

Create your first policy:

```bash
paracle policy create --name my_policy --template basic
```

Edit `.parac/policies/policy-pack.yaml` to customize.

### 3. Review Compliance Status

Check your compliance posture:

```bash
paracle compliance status
```

---

## Configuration

### Audit Configuration

```yaml
# .parac/config/audit.yaml
audit:
  enabled: true
  log_level: INFO
  retention_days: 90
  immutable: true
```

### Policy Configuration

```yaml
# .parac/config/policies.yaml
policies:
  enforcement: strict  # strict | permissive | audit_only
  default_action: deny
```

---

## Best Practices

### For Development

- Use `audit_only` mode during development
- Review logs regularly
- Test policies before enforcing

### For Production

- Enable strict policy enforcement
- Set up log rotation and backup
- Regular compliance audits
- Monitor policy violations

---

## Compliance Reports

Generate compliance reports:

```bash
# Generate report
paracle compliance report --format pdf --output report.pdf

# Check specific standard
paracle compliance check --standard iso27001
```

---

## Resources

- **Documentation**: [docs.paracle.ai/compliance](https://docs.paracle.ai/compliance)
- **Policy Examples**: `examples/policies/`
- **Security Guide**: `docs/security.md`

---

## Support

For compliance-related questions:

- **Documentation**: https://docs.paracle.ai
- **Community**: https://discord.gg/paracle
- **Enterprise**: enterprise@paracle.ai

---

**Last Updated**: 2026-01-08  
**Version**: 1.0
