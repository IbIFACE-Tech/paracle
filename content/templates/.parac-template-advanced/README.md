# {{PROJECT_NAME}} - Advanced Paracle Project

Enterprise-ready Paracle workspace with all features enabled.

## Features

- **All 8 Agent Types**: architect, coder, tester, reviewer, pm, documenter, releasemanager, security
- **PostgreSQL Database**: Production-grade persistence
- **Redis Event Bus**: Asynchronous event processing
- **Docker Compose**: Complete infrastructure stack
- **CI/CD Templates**: GitHub Actions workflows
- **Complete Policy Pack**: CODE_STYLE, TESTING, SECURITY, GIT_WORKFLOW
- **Observability**: OpenTelemetry tracing, Prometheus metrics
- **Security**: Rate limiting, JWT auth, secrets management

## Quick Start

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your API keys and credentials

# 2. Start infrastructure
docker-compose up -d

# 3. Initialize database
paracle db migrate

# 4. Check status
paracle status

# 5. List agents
paracle agents list

# 6. Run your first workflow
paracle workflows run feature_development --inputs feature_name=auth
```

## Infrastructure

### Services
- PostgreSQL (port 5432)
- Redis/Valkey (port 6379)
- Paracle API (port 8000)
- Prometheus (port 9090)
- Grafana (port 3000)

### Start all services
```bash
docker-compose up -d
```

### Stop all services
```bash
docker-compose down
```

## Agent Roster

| Agent          | Purpose                                  | Model       |
| -------------- | ---------------------------------------- | ----------- |
| architect      | System design, architecture decisions    | gpt-4o      |
| coder          | Feature implementation                   | gpt-4o-mini |
| tester         | Test creation and execution              | gpt-4o-mini |
| reviewer       | Code review and quality assurance        | gpt-4o      |
| pm             | Project management, coordination         | gpt-4o-mini |
| documenter     | Documentation generation                 | gpt-4o-mini |
| releasemanager | Versioning, releases, deployment         | gpt-4o-mini |
| security       | Security audits, vulnerability detection | gpt-4o      |

## Workflows

- `feature_development` - Full feature cycle (design → code → test → review → docs)
- `bugfix` - Streamlined bug fixing
- `code_review` - Comprehensive code review
- `security_audit` - Security scanning and compliance
- `release` - Version bump, changelog, publish

## CI/CD

GitHub Actions workflows are configured in `.github/workflows/`:
- `ci.yml` - Continuous integration (test, lint, security scan)
- `cd.yml` - Continuous deployment (staging, production)
- `security.yml` - Security scanning (daily)

## Documentation

- [Architecture](docs/architecture.md)
- [Deployment Guide](docs/deployment.md)
- [Security Policy](.parac/policies/SECURITY.md)
- [Contributing](.parac/policies/GIT_WORKFLOW.md)

## Support

- Documentation: https://paracle.dev/templates/advanced
- Issues: https://github.com/IbIFACE-Tech/paracle-lite/issues
- Discord: https://discord.gg/paracle

---

Created: {{DATE}}
Mode: Advanced
Version: 0.0.1
