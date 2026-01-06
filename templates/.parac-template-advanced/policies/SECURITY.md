# Security Policy

## Authentication

- JWT tokens for API authentication
- Token expiry: 1 hour
- Refresh tokens: 7 days
- Rate limiting: 100 requests/minute

## Secrets Management

- Never commit secrets to git
- Use environment variables (.env)
- Rotate secrets quarterly
- Use separate credentials per environment

## Dependency Security

### Automated Scanning
- `safety check` - Python vulnerabilities
- `bandit` - Code security issues
- `trivy` - Container scanning
- Daily automated scans in CI

### Update Policy
- Critical vulnerabilities: Immediate
- High severity: Within 7 days
- Medium severity: Within 30 days
- Low severity: Next release cycle

## Code Security

### Input Validation
- Validate all user inputs
- Sanitize database queries
- Use Pydantic for data validation

### SQL Injection Prevention
- Use parameterized queries
- Never concatenate SQL strings
- Use ORM (SQLAlchemy)

### XSS Prevention
- Escape HTML output
- Use Content Security Policy
- Sanitize user-generated content

## Infrastructure Security

### Network
- Use HTTPS only
- TLS 1.3 minimum
- Certificate rotation

### Database
- Encrypted connections
- Role-based access control
- Regular backups

### Containers
- Minimal base images
- Non-root users
- Security scanning

## Incident Response

1. **Detection**: Automated alerts
2. **Containment**: Isolate affected systems
3. **Eradication**: Remove threat
4. **Recovery**: Restore services
5. **Lessons Learned**: Post-mortem

## Compliance

- SOC 2 Type II
- GDPR compliance
- ISO 27001 aligned

## Security Contacts

- Security Team: security@example.com
- Report vulnerabilities: security@example.com
- PGP Key: [key-id]
