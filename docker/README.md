# Paracle Docker Setup

This directory contains Docker configuration for running Paracle in containerized environments.

## Quick Start

### Development Setup

1. **Copy environment file**

   ```bash
   cp docker/.env.example docker/.env
   ```

2. **Add your LLM API keys** to `docker/.env`:

   ```bash
   OPENAI_API_KEY=sk-your-key-here
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

3. **Start services**

   ```bash
   # From project root
   docker-compose -f docker/docker-compose.yaml -f docker/docker-compose.dev.yaml up
   ```

4. **Access the API**

   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Redis: localhost:6379

### Production Setup

1. **Copy and configure environment**

   ```bash
   cp docker/.env.example docker/.env
   # Edit docker/.env with production values
   ```

2. **Update security settings** in `docker/.env`:

   ```bash
   PARACLE_SECRET_KEY=<generate-random-secure-string>
   POSTGRES_PASSWORD=<strong-password>
   ```

3. **Start services**

   ```bash
   docker-compose -f docker/docker-compose.yaml up -d
   ```

4. **Check health**

   ```bash
   docker-compose ps
   docker-compose logs -f api
   ```

## Architecture

### Services

| Service | Description | Port |
|---------|-------------|------|
| **api** | FastAPI server | 8000 |
| **worker** | Background task worker | - |
| **postgres** | PostgreSQL database | 5432 |
| **redis** | Event bus & cache | 6379 |

### Volumes

| Volume | Purpose |
|--------|---------|
| `postgres-data` | PostgreSQL persistent storage |
| `redis-data` | Redis persistent storage |
| `paracle-data` | Paracle application data (agents, workflows) |

### Networks

All services run on the `paracle-network` bridge network.

## Configuration

### Environment Variables

See `docker/.env.example` for all available configuration options.

**Critical variables**:

```bash
# Database
POSTGRES_PASSWORD=<change-in-production>

# Security
PARACLE_SECRET_KEY=<change-in-production>

# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

### Development vs Production

| Feature | Development | Production |
|---------|-------------|------------|
| Database | SQLite (file-based) | PostgreSQL |
| Hot Reload | Enabled | Disabled |
| Code Mounting | Source code mounted | Code baked into image |
| Logging | DEBUG level | INFO level |
| User | Root (for dev tools) | Non-root user |

## Common Operations

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
```

### Execute Commands Inside Containers

```bash
# API container
docker-compose exec api bash
docker-compose exec api uv run paracle hello

# Run tests
docker-compose exec api uv run pytest

# Database migrations (when implemented)
docker-compose exec api uv run alembic upgrade head
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart api
```

### Stop and Remove

```bash
# Stop services
docker-compose down

# Stop and remove volumes (DELETES DATA)
docker-compose down -v
```

### Database Access

```bash
# PostgreSQL shell
docker-compose exec postgres psql -U paracle -d paracle

# Redis CLI
docker-compose exec redis redis-cli
```

## Development Workflow

### 1. Code Changes with Hot Reload

When using `docker-compose.dev.yaml`, source code is mounted into containers:

```bash
# Edit files in packages/
vim packages/paracle_api/main.py

# API server auto-reloads
# No need to restart containers
```

### 2. Running Tests

```bash
# Inside container
docker-compose exec api uv run pytest

# Or from host (if uv installed)
cd ..
uv run pytest
```

### 3. Adding Dependencies

```bash
# Update pyproject.toml
vim pyproject.toml

# Rebuild containers
docker-compose build

# Or install in running container (temporary)
docker-compose exec api uv add <package>
```

## Production Deployment

### 1. Build Production Images

```bash
docker-compose -f docker/docker-compose.yaml build
```

### 2. Tag and Push to Registry

```bash
# Tag
docker tag paracle-lite-api:latest registry.example.com/paracle/api:v0.0.1
docker tag paracle-lite-worker:latest registry.example.com/paracle/worker:v0.0.1

# Push
docker push registry.example.com/paracle/api:v0.0.1
docker push registry.example.com/paracle/worker:v0.0.1
```

### 3. Deploy to Server

```bash
# On production server
docker-compose -f docker/docker-compose.yaml pull
docker-compose -f docker/docker-compose.yaml up -d
```

### 4. Database Migrations

```bash
# Run migrations
docker-compose exec api uv run alembic upgrade head

# Or during deployment
docker-compose run --rm api uv run alembic upgrade head
docker-compose up -d
```

## Monitoring

### Health Checks

All services have health checks configured:

```bash
# Check service health
docker-compose ps

# Expected output:
# NAME                  STATUS
# paracle-api           Up (healthy)
# paracle-worker        Up (healthy)
# paracle-postgres      Up (healthy)
# paracle-redis         Up (healthy)
```

### Resource Usage

```bash
# View resource consumption
docker stats

# Limit resources in docker-compose.yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
```

## Troubleshooting

### API Won't Start

**Check logs**:

```bash
docker-compose logs api
```

**Common issues**:

- Database not ready → Wait for health check
- Missing API key → Check `docker/.env`
- Port conflict → Change port in `docker-compose.yaml`

### Database Connection Errors

**Verify connectivity**:

```bash
docker-compose exec api ping postgres
docker-compose exec api psql -h postgres -U paracle
```

**Reset database** (DELETES DATA):

```bash
docker-compose down -v
docker-compose up -d
```

### Worker Not Processing Tasks

**Check worker logs**:

```bash
docker-compose logs worker
```

**Verify Redis connection**:

```bash
docker-compose exec worker redis-cli -h redis ping
```

### Out of Disk Space

**Clean up Docker resources**:

```bash
# Remove unused containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune
```

## Security Considerations

### Production Checklist

- [ ] Change `PARACLE_SECRET_KEY` to random secure string
- [ ] Change `POSTGRES_PASSWORD` to strong password
- [ ] Use secrets management (Docker Secrets, Vault)
- [ ] Enable HTTPS with reverse proxy (nginx, Traefik)
- [ ] Restrict network access (firewalls)
- [ ] Set resource limits (CPU, memory)
- [ ] Enable audit logging
- [ ] Regular backups of `postgres-data` volume
- [ ] Keep base images updated

### Secrets Management

**Don't commit `.env` files**:

```bash
echo "docker/.env" >> .gitignore
```

**Use Docker Secrets** (Docker Swarm):

```yaml
services:
  api:
    secrets:
      - openai_api_key
      - postgres_password

secrets:
  openai_api_key:
    external: true
  postgres_password:
    external: true
```

## Advanced Configuration

### Using External Database

Override database URL:

```yaml
# docker-compose.override.yaml
services:
  api:
    environment:
      PARACLE_DATABASE_URL: postgresql://user:pass@external-db:5432/paracle

  postgres:
    profiles:
      - not-used
```

### Custom Networking

```yaml
networks:
  paracle-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

### Multi-Stage Builds

See `Dockerfile.api` for optimized multi-stage builds that reduce image size.

## Support

- **Documentation**: [docs/](../docs/)
- **Issues**: [GitHub Issues](https://github.com/anthropics/paracle/issues)
- **Roadmap**: [.roadmap/](../.roadmap/)
