# Security Policy

## Supported Versions

| Version | Supported          | Status                     |
| ------- | ------------------ | -------------------------- |
| 1.0.x   | :white_check_mark: | Active development         |
| 0.x     | :x:                | No longer supported        |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow these steps:

### 1. **DO NOT** Open a Public Issue

Security vulnerabilities should be reported privately to avoid exploitation.

### 2. Report via GitHub Security Advisories

1. Go to https://github.com/IbIFACE-Tech/paracle-lite/security/advisories
2. Click "Report a vulnerability"
3. Provide detailed information:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### 3. Alternative: Email Report

If you prefer email, send details to: **security@ibiface.com**

**Please include**:
- Subject: `[SECURITY] Paracle Vulnerability Report`
- Clear description of the issue
- Proof of concept (if applicable)
- Your contact information for follow-up

## Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 5 business days
- **Status Updates**: Every 7 days until resolution
- **Fix Timeline**: Depends on severity (see below)

## Severity Classification

| Severity | Response Time | Fix Target    | Example                           |
| -------- | ------------- | ------------- | --------------------------------- |
| Critical | < 24 hours    | < 7 days      | RCE, SQL injection, auth bypass   |
| High     | < 48 hours    | < 14 days     | XSS, CSRF, data exposure          |
| Medium   | < 5 days      | < 30 days     | DoS, information disclosure       |
| Low      | < 10 days     | Next release  | Minor information leaks           |

## Security Update Process

1. **Verification**: We verify and reproduce the issue
2. **Fix Development**: Develop and test the fix
3. **Advisory**: Create GitHub Security Advisory (if applicable)
4. **Release**: Publish patched version
5. **Disclosure**: Public disclosure after fix is available

## Known Security Considerations

### Current Open Issues

#### 1. ecdsa Timing Attack (CVE-2024-23342)
- **Status**: NO FIX AVAILABLE
- **Severity**: HIGH (7.4 CVSS)
- **Impact**: Minerva timing attack on P-256 curve
- **Mitigation**: python-ecdsa project considers side-channel attacks out-of-scope
- **Risk Assessment**: Requires local access + precise timing analysis
- **Recommendation**: Use alternative cryptography libraries for high-security contexts

### Resolved Issues (2026-01-18)

- ✅ pyasn1 CVE-2026-23490 (DoS) - Fixed v1.0.0
- ✅ azure-core CVE-2026-21226 (RCE) - Fixed v1.0.0
- ✅ filelock CVE-2026-22701 (TOCTOU) - Fixed v1.0.0
- ✅ virtualenv CVE-2026-22702 (TOCTOU) - Fixed v1.0.0
- ✅ urllib3 CVE-2026-21441 (Decompression bomb) - Fixed v1.0.0

## Security Features

### Built-in Security

- **Input Validation**: Pydantic v2 models with strict validation
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **YAML Safety**: Uses `yaml.safe_load()` throughout
- **SSRF Prevention**: Blocks internal IP ranges
- **Authentication**: bcrypt password hashing
- **API Security**: Rate limiting, CORS policies
- **Secrets Management**: Environment-based configuration

### Security Scanning

- **CodeQL**: Daily automated scans
- **Bandit**: Python security linter in CI/CD
- **Safety**: Dependency vulnerability scanning
- **pip-audit**: Alternative vulnerability checks
- **Dependabot**: Automatic dependency updates

## Compliance

- **OWASP Top 10**: Addressed in design
- **ISO 27001**: Information security management
- **ISO 42001**: AI system management
- **SOC2**: Security controls implemented

## Security Practices

### Dependency Management

We regularly scan dependencies for vulnerabilities using:
- `bandit` - Python security linter
- `safety` - Dependency vulnerability scanner
- `pip-audit` - Python package audit

### Code Quality

- All code changes require review
- Automated security scanning in CI/CD
- Type hints and Pydantic validation throughout

### Secrets Management

- Never commit secrets to the repository
- Use environment variables for API keys
- `.env` files are gitignored

## For Contributors

Before submitting code:

1. Run security linters locally:
   ```bash
   bandit -r packages/
   safety check
   ```

2. Ensure no secrets are committed:
   ```bash
   detect-secrets scan
   ```

3. Follow secure coding practices in [CONTRIBUTING.md](CONTRIBUTING.md)
