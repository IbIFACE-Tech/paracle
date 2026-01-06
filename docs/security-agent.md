# Security Agent - Documentation

## Overview

The **Security Agent** is a specialized agent in Paracle designed for comprehensive security auditing, vulnerability detection, threat modeling, and security compliance enforcement. It ensures that your AI applications and the Paracle framework itself maintain high security standards.

## Quick Start

### Using the Security Agent

```python
from paracle_domain.factory import AgentFactory
from paracle_domain.models import AgentSpec
from paracle_store import AgentRepository

# Create security agent
repo = AgentRepository()
factory = AgentFactory(spec_provider=repo.get_spec)

security_agent = AgentSpec(
    name="security",
    description="Security auditing and vulnerability detection",
    provider="openai",
    model="gpt-4",
    temperature=0.2,  # Strict for security
    tools=[
        "bandit",
        "safety",
        "semgrep",
        "detect_secrets",
        "pip_audit",
        "trivy",
    ],
    skills=[
        "security-hardening",
        "testing-qa",
        "paracle-development",
    ],
)

repo.register_spec(security_agent)
agent = factory.create(security_agent)
```

### Run Security Audit

```bash
# Full security audit
paracle agent run security --task "Perform full security audit"

# Quick dependency scan
paracle agent run security --task "Scan dependencies for vulnerabilities"

# Check for secrets
paracle agent run security --task "Scan for exposed secrets"

# OWASP compliance check
paracle agent run security --task "Verify OWASP Top 10 compliance"
```

## Core Capabilities

### 1. Vulnerability Detection

- **Dependency Scanning**: pip-audit, safety, trivy
- **Static Analysis**: bandit, semgrep, pylint-secure-coding
- **Secret Detection**: detect-secrets
- **Container Security**: trivy for Docker images

### 2. Security Testing

- **SAST** (Static Application Security Testing)
- **DAST** (Dynamic Application Security Testing)
- **Penetration Testing**
- **Fuzz Testing**
- **Security Regression Testing**

### 3. Compliance Checking

- **OWASP Top 10** compliance
- **CWE/CVE** tracking
- **GDPR** data protection checks
- **SOC 2** requirements validation
- **PCI-DSS** compliance (if applicable)

### 4. Threat Modeling

- Attack vector identification
- Risk assessment
- Data flow security analysis
- Privilege escalation detection
- Authentication bypass scenarios

## Security Tools

### Static Analysis Tools

| Tool                     | Purpose                          | Usage                            |
| ------------------------ | -------------------------------- | -------------------------------- |
| **bandit**               | Python security linter           | Code vulnerability scanning      |
| **safety**               | Dependency vulnerability checker | Package security audit           |
| **semgrep**              | Pattern-based analysis           | Custom security rule enforcement |
| **pylint-secure-coding** | Secure coding checks             | Python best practices            |
| **detect-secrets**       | Secret detection                 | Find exposed credentials         |

### Dynamic Testing Tools

| Tool           | Purpose                   | Usage                             |
| -------------- | ------------------------- | --------------------------------- |
| **owasp-zap**  | Web app security scanner  | API and web vulnerability testing |
| **sqlmap**     | SQL injection testing     | Database security validation      |
| **burp-suite** | Web vulnerability scanner | Comprehensive security testing    |
| **nikto**      | Web server scanner        | Server configuration audit        |

### Dependency Analysis

| Tool                 | Purpose                        | Usage                          |
| -------------------- | ------------------------------ | ------------------------------ |
| **pip-audit**        | Python package scanner         | Find known vulnerabilities     |
| **dependency-check** | OWASP dependency checker       | Cross-language support         |
| **snyk**             | Continuous security monitoring | Real-time vulnerability alerts |
| **trivy**            | Container/dependency scanner   | Docker image security          |

## Specialized Security Agents

### Python Security Specialist

Inherits from base security agent with Python-specific focus:

```python
python_security = AgentSpec(
    name="python-security-specialist",
    parent="security",  # Inherits tools and skills
    temperature=0.15,  # Stricter
    tools=["pylint_secure_coding"],  # Python-specific
    skills=["python-security"],
    metadata={"language": "python"}
)
```

**Focus Areas**:
- Pickle deserialization vulnerabilities
- eval/exec injection
- Subprocess injection
- Path traversal
- Regex DoS
- Python-specific OWASP issues

### API Security Specialist

Inherits from base security agent with API focus:

```python
api_security = AgentSpec(
    name="api-security-specialist",
    parent="security",
    tools=["owasp_zap", "burp_suite"],  # API scanners
    skills=["api-security"],
    metadata={"standards": ["rest", "graphql", "grpc"]}
)
```

**Focus Areas**:
- Authentication bypass
- Broken authorization
- Rate limiting
- Mass assignment
- API injection
- REST/GraphQL security

## Security Workflows

### Pre-Commit Security Check

Fast security check on changed files:

```yaml
workflow:
  name: pre-commit-security
  steps:
    - agent: security
      task: quick_scan
      tools: [bandit, detect-secrets]
      fail_on: [CRITICAL, HIGH]
      timeout: 60s
```

### Full Security Audit

Comprehensive security review:

```yaml
workflow:
  name: full-security-audit
  steps:
    - agent: security
      task: dependency_scan
      tools: [pip-audit, safety, trivy]

    - agent: security
      task: code_scan
      tools: [bandit, semgrep]

    - agent: security
      task: secret_scan
      tools: [detect-secrets]

    - agent: python-security-specialist
      task: python_specific_review

    - agent: api-security-specialist
      task: api_security_test

    - agent: security
      task: generate_report
      output: security_report.json
```

### CI/CD Integration

Automated security in CI/CD pipeline:

```yaml
# .github/workflows/security.yml
name: Security Audit

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Security Agent
        run: |
          paracle agent run security \
            --task "Full security audit" \
            --mode yolo \
            --output security_report.json

      - name: Check Results
        run: |
          # Fail if CRITICAL or HIGH vulnerabilities
          python scripts/check_security_report.py security_report.json
```

## Security Metrics & KPIs

### Key Metrics

1. **Vulnerability Count**: By severity (CRITICAL, HIGH, MEDIUM, LOW)
2. **Time to Patch**: Average time from discovery to fix
3. **Test Coverage**: % of security tests in suite
4. **Dependency Age**: Days since last update
5. **Failed Audits**: Count of failed security scans
6. **Secret Exposures**: Number of leaked secrets
7. **Attack Surface**: Exposed endpoints/ports

### Severity Levels

- **CRITICAL**: Immediate action required, system compromise possible
- **HIGH**: Significant risk, patch within days
- **MEDIUM**: Moderate risk, patch within weeks
- **LOW**: Minor risk, patch in regular cycle
- **INFO**: No immediate risk, informational

## Pre-Release Security Checklist

Before releasing, ensure:

- [ ] All dependencies scanned (no HIGH/CRITICAL)
- [ ] No secrets in code/git history
- [ ] Authentication tested
- [ ] Authorization validated
- [ ] Input validation on all endpoints
- [ ] SQL injection tests passed
- [ ] XSS prevention verified
- [ ] CSRF protection enabled
- [ ] Rate limiting configured
- [ ] Security headers set
- [ ] HTTPS enforced
- [ ] Error messages sanitized
- [ ] No PII in logs
- [ ] Security tests in CI/CD
- [ ] Penetration testing completed

## Integration with Other Agents

### With Coder Agent

- Security review before merge
- Secure coding suggestions
- Security-focused code snippets

### With Reviewer Agent

- Complement general review
- Deep security focus
- Validate security test coverage

### With Tester Agent

- Security test case design
- Penetration test scenarios
- Security regression tests

### With Release Manager

- Security sign-off before release
- Verify no vulnerabilities
- Security changelog updates

## Best Practices

1. **Security by Design**: Consider security from day one
2. **Defense in Depth**: Multiple security layers
3. **Least Privilege**: Minimal permissions
4. **Fail Securely**: Errors don't compromise security
5. **Keep it Simple**: Complexity hurts security
6. **Secure Defaults**: Safe out-of-the-box config
7. **Regular Updates**: Keep dependencies current
8. **Continuous Monitoring**: Always watch for issues
9. **Security Training**: Keep team informed
10. **Incident Response**: Be ready for breaches

## Configuration

```yaml
# .parac/agents/security-config.yaml
security:
  scanner:
    bandit:
      severity_threshold: medium
      confidence_threshold: medium

    safety:
      check_dependencies: true
      ignore_ids: []  # Known acceptable issues

    semgrep:
      rules: [p/owasp-top-ten, p/security-audit]

  compliance:
    owasp_top_10: true
    gdpr: false
    soc2: false

  enforcement:
    block_on_critical: true
    require_security_review: true
    max_high_vulnerabilities: 0
```

## Examples

See [`examples/security_agent.py`](../examples/security_agent.py) for:
- Creating security agent
- Running security scans
- Creating specialized agents
- Security workflow integration
- Metrics and reporting

## Resources

- [Security Agent Spec](.parac/agents/specs/security.md)
- [Security Hardening Skill](.parac/agents/skills/security-hardening/SKILL.md)
- [Security Policy](../policies/SECURITY.md)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)

## Security Contact

For security vulnerabilities, please report to: **security@paracle.dev**

Follow responsible disclosure process.

---

**Last Updated**: 2026-01-06
**Version**: 1.0
**Maintainer**: Paracle Security Team

