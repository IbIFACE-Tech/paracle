# Environment Configuration Guide

**Last Updated**: 2026-01-17
**Version**: 1.0

---

## Overview

This guide explains all environment variables required to configure Paracle in different environments.

---

## Configuration Files

### Development: `.env`

```bash
# Application
APP_ENV=development
APP_DEBUG=true
LOG_LEVEL=DEBUG

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/paracle_dev
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# LLM Providers
OPENAI_API_KEY=sk-...
CLAUDE_API_KEY=sk-ant-...
GEMINI_API_KEY=AIzaSy...

# Security
SECRET_KEY=dev-secret-key-change-in-production
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Observability
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
TRACING_ENABLED=false
```

### Production: Environment Variables

**DO NOT USE `.env` IN PRODUCTION**. Use secrets manager instead.

```bash
# Application
APP_ENV=production
APP_DEBUG=false
LOG_LEVEL=INFO
WORKERS=4

# Database (use managed service)
DATABASE_URL=postgresql://user:pass@prod-db.aws.com:5432/paracle
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_SSL_MODE=require

# Redis (use managed service)
REDIS_URL=redis://prod-redis.aws.com:6379/0
REDIS_SSL=true
REDIS_MAX_CONNECTIONS=100

# LLM Providers (from secrets manager)
OPENAI_API_KEY=${OPENAI_API_KEY}
CLAUDE_API_KEY=${CLAUDE_API_KEY}
GEMINI_API_KEY=${GEMINI_API_KEY}

# Security
SECRET_KEY=${SECRET_KEY}  # 32+ chars, cryptographically random
CORS_ORIGINS=https://app.paracle.com
ALLOWED_HOSTS=api.paracle.com,paracle.com

# TLS
SSL_CERT_PATH=/etc/ssl/certs/paracle.crt
SSL_KEY_PATH=/etc/ssl/private/paracle.key

# Observability
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
TRACING_ENABLED=true
JAEGER_ENDPOINT=http://jaeger:14268/api/traces
SENTRY_DSN=${SENTRY_DSN}
```

---

## Configuration by Component

### API Server

```bash
# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4  # CPU cores * 2
RELOAD=false  # true in dev only

# Timeouts
KEEPALIVE_TIMEOUT=65
GRACEFUL_TIMEOUT=30

# Limits
MAX_REQUEST_SIZE=10485760  # 10 MB
REQUEST_TIMEOUT=60

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

### Database

```bash
# Connection
DATABASE_URL=postgresql://user:pass@host:5432/dbname
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_PRE_PING=true
DATABASE_POOL_RECYCLE=3600

# SSL
DATABASE_SSL_MODE=require
DATABASE_SSL_CERT=/path/to/client-cert.pem
DATABASE_SSL_KEY=/path/to/client-key.pem
DATABASE_SSL_ROOT_CERT=/path/to/ca-cert.pem

# Query Optimization
DATABASE_STATEMENT_TIMEOUT=30000  # 30 seconds
DATABASE_IDLE_IN_TRANSACTION_TIMEOUT=60000  # 60 seconds
```

### Redis

```bash
# Connection
REDIS_URL=redis://host:6379/0
REDIS_MAX_CONNECTIONS=100
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5

# SSL
REDIS_SSL=true
REDIS_SSL_CERT_REQS=required
REDIS_SSL_CA_CERTS=/path/to/ca.crt

# Cluster (if using Redis Cluster)
REDIS_CLUSTER_ENABLED=false
REDIS_CLUSTER_NODES=node1:6379,node2:6379,node3:6379
```

### Storage (S3-compatible)

```bash
# AWS S3
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
AWS_REGION=us-east-1
S3_BUCKET=paracle-storage
S3_ENDPOINT=https://s3.amazonaws.com

# Azure Blob Storage
AZURE_STORAGE_ACCOUNT_NAME=${STORAGE_ACCOUNT}
AZURE_STORAGE_ACCOUNT_KEY=${STORAGE_KEY}
AZURE_STORAGE_CONTAINER=paracle-storage

# MinIO (self-hosted)
MINIO_ENDPOINT=https://minio.paracle.com
MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
MINIO_BUCKET=paracle-storage
MINIO_SECURE=true
```

---

## Secrets Management

### Azure Key Vault

```bash
# Azure authentication
AZURE_TENANT_ID=${TENANT_ID}
AZURE_CLIENT_ID=${CLIENT_ID}
AZURE_CLIENT_SECRET=${CLIENT_SECRET}

# Key Vault
AZURE_KEY_VAULT_NAME=paracle-keys
AZURE_KEY_VAULT_URI=https://paracle-keys.vault.azure.net/

# Usage in application
OPENAI_API_KEY=$(az keyvault secret show --vault-name paracle-keys --name OPENAI-API-KEY --query value -o tsv)
```

### AWS Secrets Manager

```bash
# AWS authentication (use IAM roles in production)
AWS_ACCESS_KEY_ID=${ACCESS_KEY}
AWS_SECRET_ACCESS_KEY=${SECRET_KEY}
AWS_REGION=us-east-1

# Secrets Manager
AWS_SECRETS_MANAGER_SECRET_ID=paracle/api-keys

# Usage in application
OPENAI_API_KEY=$(aws secretsmanager get-secret-value --secret-id paracle/api-keys --query SecretString --output text | jq -r .OPENAI_API_KEY)
```

### HashiCorp Vault

```bash
# Vault connection
VAULT_ADDR=https://vault.paracle.com
VAULT_TOKEN=${VAULT_TOKEN}  # Or use AppRole/K8s auth

# Secrets path
VAULT_SECRETS_PATH=secret/paracle

# Usage in application
OPENAI_API_KEY=$(vault kv get -field=OPENAI_API_KEY secret/paracle)
```

---

## Environment-Specific Overrides

### Docker Compose

```yaml
# docker-compose.yaml
services:
  api:
    environment:
      - APP_ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    env_file:
      - .env.production
```

### Kubernetes

```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
        - name: api
          env:
            - name: APP_ENV
              value: "production"
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: paracle-secrets
                  key: database-url
          envFrom:
            - secretRef:
                name: paracle-secrets
```

### Systemd

```ini
# /etc/systemd/system/paracle-api.service
[Service]
EnvironmentFile=/etc/paracle/production.env
Environment="APP_ENV=production"
Environment="LOG_LEVEL=INFO"
```

---

## Validation

### Check Configuration

```python
# scripts/validate_config.py
import os
import sys

required_vars = [
    "DATABASE_URL",
    "REDIS_URL",
    "OPENAI_API_KEY",
    "SECRET_KEY",
]

missing = [var for var in required_vars if not os.getenv(var)]

if missing:
    print(f"❌ Missing required environment variables: {', '.join(missing)}")
    sys.exit(1)

print("✅ All required environment variables are set")
```

Run:

```bash
python scripts/validate_config.py
```

---

## Security Best Practices

### ✅ DO

- ✅ Use secrets manager (Key Vault, Secrets Manager, Vault)
- ✅ Rotate secrets every 30-90 days
- ✅ Use separate credentials per environment
- ✅ Enable audit logging for secrets access
- ✅ Use managed identities/IAM roles (no hardcoded credentials)
- ✅ Encrypt sensitive data at rest and in transit

### ❌ DON'T

- ❌ Never commit `.env` to git
- ❌ Never log sensitive environment variables
- ❌ Never share production credentials
- ❌ Never use development keys in production
- ❌ Never store secrets in container images

---

## Troubleshooting

### Issue: Environment variables not loading

**Solution**:

```bash
# Check if variables are set
env | grep PARACLE

# Load from file
set -a
source .env
set +a

# Verify
echo $DATABASE_URL
```

### Issue: Secrets Manager connection fails

**Solution**:

```bash
# AWS
aws sts get-caller-identity  # Verify IAM credentials
aws secretsmanager list-secrets  # Test access

# Azure
az account show  # Verify authentication
az keyvault secret list --vault-name paracle-keys  # Test access
```

---

## Related Guides

- [production-deployment.md](production-deployment.md) - Deployment procedures
- [secrets-management.md](secrets-management.md) - Secrets best practices
- [security-hardening.md](security-hardening.md) - Security configuration
