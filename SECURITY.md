# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Paracle, please report it responsibly by emailing **security@ibiface.com**.

**Please do NOT open a public GitHub issue for security vulnerabilities.**

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Any suggested fixes (optional)

### Response Timeline

- **Initial acknowledgment**: Within 48 hours
- **Status update**: Within 7 days
- **Resolution target**: Within 30-90 days depending on severity

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

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
