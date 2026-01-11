# Security Checklist

Comprehensive security checklist for Paracle applications.

## Authentication & Authorization

### JWT Authentication

- [ ] JWT secret key stored securely (not in code)
- [ ] Token expiration configured (24 hours max)
- [ ] Refresh token mechanism implemented
- [ ] Token signature validated on every request
- [ ] User ID extracted from validated token
- [ ] Invalid tokens return 401 Unauthorized

### Authorization (RBAC)

- [ ] User roles defined (admin, user, viewer)
- [ ] Permissions mapped to roles
- [ ] Permission checks on protected endpoints
- [ ] Authorization failures return 403 Forbidden
- [ ] Principle of least privilege applied
- [ ] Service accounts have minimal permissions

### Password Security

- [ ] Passwords hashed with bcrypt (cost factor ≥12)
- [ ] Minimum password length enforced (12+ chars)
- [ ] Password complexity requirements enforced
- [ ] Password reset tokens expire (1 hour)
- [ ] Failed login attempts tracked and limited
- [ ] No passwords logged or exposed in errors

## Input Validation

### Request Validation

- [ ] All inputs validated with Pydantic
- [ ] String length limits enforced
- [ ] Numeric ranges validated (min/max)
- [ ] Email format validated
- [ ] URL format validated
- [ ] File upload size limited
- [ ] File types whitelisted

### SQL Injection Prevention

- [ ] Parameterized queries used (no string interpolation)
- [ ] SQLAlchemy ORM used correctly
- [ ] No raw SQL with user input
- [ ] Input sanitized before database queries
- [ ] Database user has minimal privileges

### XSS Prevention

- [ ] Output escaped in templates
- [ ] Content-Type headers set correctly
- [ ] User-generated content sanitized
- [ ] No `innerHTML` with user data (if using JS)

### CSRF Prevention

- [ ] CSRF tokens on state-changing requests
- [ ] SameSite cookie attribute set
- [ ] Origin/Referer header validation

## API Security

### Rate Limiting

- [ ] Rate limiting implemented on all endpoints
- [ ] Different limits for auth vs public endpoints
- [ ] 429 Too Many Requests returned when exceeded
- [ ] Rate limit headers included (X-RateLimit-*)
- [ ] IP-based and user-based limiting

### CORS Configuration

- [ ] CORS origins explicitly whitelisted
- [ ] No `*` wildcard in production
- [ ] Credentials allowed only for trusted origins
- [ ] Preflight requests handled correctly
- [ ] CORS headers validated

### Security Headers

- [ ] `X-Content-Type-Options: nosniff`
- [ ] `X-Frame-Options: DENY`
- [ ] `X-XSS-Protection: 1; mode=block`
- [ ] `Strict-Transport-Security` (HTTPS only)
- [ ] `Content-Security-Policy` configured

## Data Protection

### Sensitive Data

- [ ] No secrets in code or version control
- [ ] Environment variables used for secrets
- [ ] Secret management system used (Vault, Key Vault)
- [ ] Database connections encrypted (SSL/TLS)
- [ ] API keys rotated regularly
- [ ] Secrets not logged

### PII Protection

- [ ] PII encrypted at rest
- [ ] PII encrypted in transit (HTTPS)
- [ ] PII access logged and monitored
- [ ] Data retention policy enforced
- [ ] GDPR compliance (if applicable)
- [ ] Right to deletion implemented

### Database Security

- [ ] Database credentials not hardcoded
- [ ] Database user has minimal privileges
- [ ] Connection pooling configured
- [ ] SSL/TLS for database connections
- [ ] Database backups encrypted
- [ ] Access to backups restricted

## Infrastructure Security

### HTTPS/TLS

- [ ] HTTPS enforced (HTTP redirects to HTTPS)
- [ ] Valid TLS certificate installed
- [ ] TLS 1.2+ required (TLS 1.0/1.1 disabled)
- [ ] Strong cipher suites configured
- [ ] Certificate expiration monitored

### Docker Security

- [ ] Non-root user in containers
- [ ] Minimal base images used
- [ ] No secrets in Docker images
- [ ] Image scanning enabled
- [ ] Container resource limits set
- [ ] Read-only filesystems where possible

### Network Security

- [ ] Firewall rules configured
- [ ] Only necessary ports exposed
- [ ] Internal services not publicly accessible
- [ ] Network segmentation implemented
- [ ] VPC/private networks used

## Dependency Security

### Dependencies

- [ ] Dependencies kept up to date
- [ ] Security advisories monitored
- [ ] Vulnerability scanning enabled (Dependabot)
- [ ] No known vulnerable dependencies
- [ ] Dependency versions pinned
- [ ] Lock files committed (requirements.txt, uv.lock)

### Supply Chain

- [ ] Packages verified from trusted sources
- [ ] Package signatures validated
- [ ] Private package registry used (if applicable)
- [ ] CI/CD pipeline secured
- [ ] Code signing implemented

## Logging & Monitoring

### Security Logging

- [ ] Authentication attempts logged
- [ ] Authorization failures logged
- [ ] API access logged
- [ ] Security events logged
- [ ] Logs centralized and monitored
- [ ] Alerts configured for anomalies

### Sensitive Data in Logs

- [ ] No passwords in logs
- [ ] No API keys in logs
- [ ] No PII in logs (or redacted)
- [ ] No credit card numbers in logs
- [ ] Request/response bodies sanitized

## Error Handling

### Error Messages

- [ ] Generic error messages to users
- [ ] No stack traces exposed
- [ ] No internal paths exposed
- [ ] No database errors exposed
- [ ] Detailed errors logged server-side only

### Exception Handling

- [ ] All endpoints have error handlers
- [ ] Uncaught exceptions handled globally
- [ ] 500 errors don't leak information
- [ ] Errors categorized by severity
- [ ] Critical errors trigger alerts

## Testing

### Security Testing

- [ ] Authentication tests written
- [ ] Authorization tests written
- [ ] Input validation tests written
- [ ] SQL injection tests written
- [ ] XSS tests written (if applicable)
- [ ] Rate limiting tests written

### Penetration Testing

- [ ] Regular security audits scheduled
- [ ] Penetration testing performed
- [ ] Findings remediated
- [ ] Re-testing after fixes

## Compliance

### Regulatory

- [ ] GDPR compliance (if applicable)
- [ ] SOC 2 compliance (if applicable)
- [ ] HIPAA compliance (if applicable)
- [ ] Privacy policy published
- [ ] Terms of service published
- [ ] Data processing agreements in place

### Documentation

- [ ] Security architecture documented
- [ ] Incident response plan documented
- [ ] Access control policies documented
- [ ] Security training provided
- [ ] Security audit trail maintained

## Incident Response

### Preparation

- [ ] Incident response plan exists
- [ ] Team roles defined
- [ ] Contact information current
- [ ] Escalation procedures defined
- [ ] Communication plan ready
- [ ] Backup and recovery tested

### Detection

- [ ] Security monitoring active
- [ ] Alerts configured
- [ ] Log aggregation working
- [ ] Anomaly detection enabled
- [ ] Threat intelligence integrated

### Response

- [ ] Incident reporting mechanism
- [ ] Containment procedures
- [ ] Evidence preservation
- [ ] Root cause analysis process
- [ ] Post-mortem template

## Maintenance

### Regular Tasks

- [ ] Security patches applied monthly
- [ ] Access reviews quarterly
- [ ] Penetration tests annually
- [ ] Security training annually
- [ ] Disaster recovery drills semi-annually
- [ ] Policy reviews annually

### Continuous Improvement

- [ ] Security metrics tracked
- [ ] Vulnerabilities tracked and remediated
- [ ] Security roadmap maintained
- [ ] Threat model updated
- [ ] Lessons learned documented

## See Also

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks/)
- `docs/security-audit-report.md` in project root
