---
name: cicd-devops
description: Manage GitHub Actions workflows, containerization, deployment pipelines, and release automation. Use when working with CI/CD, Docker, or deployment.
license: Apache-2.0
compatibility: GitHub Actions, Docker, Docker Compose
metadata:
  author: paracle-core-team
  version: "1.0.0"
  category: automation
  level: advanced
  display_name: "CI/CD & DevOps"
  tags:
    - cicd
    - github-actions
    - docker
    - deployment
    - automation
  capabilities:
    - ci_pipeline
    - docker_containerization
    - deployment_automation
    - release_management
allowed-tools: Read Write Bash(docker:*) Bash(git:*)
---

# CI/CD & DevOps Skill

## When to use this skill

Use this skill when:
- Creating or updating GitHub Actions workflows
- Building Docker containers
- Setting up deployment pipelines
- Automating releases
- Managing infrastructure as code
- Configuring environments

## Paracle CI/CD Structure

```
.github/
├── workflows/
│   ├── ci.yml              # Main CI pipeline
│   ├── release.yml         # Release automation
│   └── deploy.yml          # Deployment
├── actions/                # Custom actions
│   └── setup-python/
└── dependabot.yml          # Dependency updates

docker/
├── Dockerfile.api          # API container
├── Dockerfile.worker       # Worker container
├── docker-compose.yaml     # Local development
└── docker-compose.prod.yaml # Production
```

## GitHub Actions Patterns

### Pattern 1: CI Pipeline

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v1

      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync

      - name: Run linters
        run: |
          uv run ruff check .
          uv run black --check .
          uv run mypy packages/

      - name: Run tests
        run: uv run pytest --cov=packages --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Build package
        run: |
          uv build

      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: dist
          path: dist/
```

### Pattern 2: Release Automation

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4

      - name: Build package
        run: uv build

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/*
          generate_release_notes: true

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
```

### Pattern 3: Docker Build & Push

```yaml
# .github/workflows/docker.yml
name: Docker

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/Dockerfile.api
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## Docker Patterns

### Pattern 1: Multi-Stage Dockerfile

```dockerfile
# docker/Dockerfile.api
FROM python:3.11-slim as builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY packages/ ./packages/

# Set environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "paracle_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Pattern 2: Docker Compose

```yaml
# docker/docker-compose.yaml
version: '3.8'

services:
  api:
    build:
      context: ..
      dockerfile: docker/Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///data/paracle.db
      - LOG_LEVEL=info
    volumes:
      - api-data:/app/data
    depends_on:
      - redis
    networks:
      - paracle

  worker:
    build:
      context: ..
      dockerfile: docker/Dockerfile.worker
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    networks:
      - paracle

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - paracle

volumes:
  api-data:
  redis-data:

networks:
  paracle:
    driver: bridge
```

## Deployment Patterns

### Pattern 1: Environment Configuration

```yaml
# .parac/deployment/environments/production.yaml
environment: production

api:
  replicas: 3
  resources:
    limits:
      cpu: "1000m"
      memory: "1Gi"
    requests:
      cpu: "500m"
      memory: "512Mi"

database:
  url: ${DATABASE_URL}
  pool_size: 10

monitoring:
  enabled: true
  metrics_port: 9090
```

### Pattern 2: Health Checks

```python
# packages/paracle_api/health.py
from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(tags=["health"])

class HealthResponse(BaseModel):
    status: str
    version: str
    database: str

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        database="connected",
    )

@router.get("/ready")
async def readiness_check():
    """Readiness check for load balancers."""
    # Check dependencies (database, redis, etc.)
    return {"ready": True}
```

## Monitoring & Logging

### Pattern 1: Structured Logging

```python
# packages/paracle_core/logging/structured.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for aggregation."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

# Usage
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("paracle")
logger.addHandler(handler)
```

## Best Practices

### 1. Secrets Management

```yaml
# ❌ Bad: Hardcoded secrets
env:
  API_KEY: "sk-abc123"

# ✅ Good: GitHub Secrets
env:
  API_KEY: ${{ secrets.API_KEY }}
```

### 2. Caching

```yaml
# Cache dependencies
- name: Cache uv packages
  uses: actions/cache@v3
  with:
    path: ~/.cache/uv
    key: ${{ runner.os }}-uv-${{ hashFiles('**/uv.lock') }}
```

### 3. Matrix Testing

```yaml
strategy:
  matrix:
    python-version: ["3.10", "3.11", "3.12"]
    os: [ubuntu-latest, macos-latest, windows-latest]
```

## Common Pitfalls

❌ **Don't:**
- Commit secrets to repository
- Run CI on every file change
- Use `latest` tags in production
- Skip health checks
- Ignore resource limits

✅ **Do:**
- Use secrets management
- Optimize CI with caching
- Pin versions
- Implement health endpoints
- Set resource limits

## Resources

- [GitHub Actions Docs](https://docs.github.com/actions)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [12-Factor App](https://12factor.net/)
- Paracle CI/CD: `.github/workflows/`
