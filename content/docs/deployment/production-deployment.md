# Production Deployment Guide

**Last Updated**: 2026-01-17
**Version**: 1.0
**Target Audience**: DevOps Engineers, SREs

---

## Overview

This guide provides step-by-step instructions for deploying Paracle v1.0+ to production environments.

**Supported Platforms**:

- Docker + Docker Compose
- Kubernetes (EKS, AKS, GKE)
- VM-based deployments (Ubuntu 22.04+, RHEL 9+)

---

## Prerequisites

### Infrastructure Requirements

**Minimum** (Development/Staging):

- **Compute**: 2 vCPU, 4 GB RAM
- **Storage**: 20 GB SSD
- **Network**: 1 Gbps
- **Database**: PostgreSQL 14+ with pgvector extension
- **Cache**: Redis 7+

**Recommended** (Production):

- **Compute**: 4 vCPU, 16 GB RAM (per instance)
- **Storage**: 100 GB SSD (NVMe preferred)
- **Network**: 10 Gbps, load balancer
- **Database**: PostgreSQL 16+ (managed service: RDS, Azure Database, Cloud SQL)
- **Cache**: Redis 7+ (managed service: ElastiCache, Azure Cache, Memorystore)
- **Replicas**: 3+ instances for high availability

### Software Requirements

- **Python**: 3.10+ (3.13 recommended)
- **Docker**: 24.0+ (if using containers)
- **PostgreSQL**: 14+ with pgvector extension
- **Redis**: 7+
- **Reverse Proxy**: Nginx 1.24+ or Traefik 2.10+

### Access Requirements

- **Git**: Access to repository
- **Secrets**: API keys for LLM providers (stored in secrets manager)
- **TLS Certificates**: Valid SSL/TLS certificates
- **DNS**: Domain name configured

---

## Deployment Options

### Option 1: Docker Compose (Quick Start)

**Use Case**: Small deployments, staging environments

```bash
# 1. Clone repository
git clone https://github.com/IbIFACE-Tech/paracle-lite.git
cd paracle-lite

# 2. Set up environment
cp .env.example .env
# Edit .env with production secrets (use Azure Key Vault/AWS Secrets Manager)

# 3. Build and start services
docker-compose -f docker/docker-compose.yaml up -d

# 4. Verify deployment
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

**Services Started**:

- `paracle-api`: FastAPI application (port 8000)
- `postgres`: PostgreSQL 16 + pgvector
- `redis`: Redis 7 for caching/events
- `nginx`: Reverse proxy (port 80/443)

---

### Option 2: Kubernetes (Production)

**Use Case**: Production, high availability, auto-scaling

#### Step 1: Create Namespace

```bash
kubectl create namespace paracle-prod
kubectl config set-context --current --namespace=paracle-prod
```

#### Step 2: Configure Secrets

```bash
# Option A: From .env file (not recommended for production)
kubectl create secret generic paracle-secrets --from-env-file=.env

# Option B: From secrets manager (recommended)
# Azure Key Vault
kubectl create secret generic paracle-secrets \
  --from-literal=OPENAI_API_KEY=$(az keyvault secret show --vault-name paracle-keys --name OPENAI-API-KEY --query value -o tsv) \
  --from-literal=CLAUDE_API_KEY=$(az keyvault secret show --vault-name paracle-keys --name CLAUDE-API-KEY --query value -o tsv)

# AWS Secrets Manager
kubectl create secret generic paracle-secrets \
  --from-literal=OPENAI_API_KEY=$(aws secretsmanager get-secret-value --secret-id paracle/api-keys --query SecretString --output text | jq -r .OPENAI_API_KEY)
```

#### Step 3: Deploy PostgreSQL

```yaml
# k8s/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: pgvector/pgvector:pg16
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_DB
              value: paracle
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: paracle-secrets
                  key: POSTGRES_PASSWORD
          volumeMounts:
            - name: postgres-data
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: postgres-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 100Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  ports:
    - port: 5432
  selector:
    app: postgres
  clusterIP: None
```

Apply:

```bash
kubectl apply -f k8s/postgres.yaml
```

#### Step 4: Deploy Redis

```yaml
# k8s/redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          ports:
            - containerPort: 6379
          command: ["redis-server", "--appendonly", "yes"]
          volumeMounts:
            - name: redis-data
              mountPath: /data
      volumes:
        - name: redis-data
          persistentVolumeClaim:
            claimName: redis-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: redis
spec:
  ports:
    - port: 6379
  selector:
    app: redis
```

Apply:

```bash
kubectl apply -f k8s/redis.yaml
```

#### Step 5: Deploy Paracle API

```yaml
# k8s/api.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: paracle-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: paracle-api
  template:
    metadata:
      labels:
        app: paracle-api
    spec:
      containers:
        - name: api
          image: ibiface/paracle-api:1.0.3
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              value: postgresql://postgres:password@postgres:5432/paracle
            - name: REDIS_URL
              value: redis://redis:6379
          envFrom:
            - secretRef:
                name: paracle-secrets
          resources:
            requests:
              memory: "4Gi"
              cpu: "2"
            limits:
              memory: "8Gi"
              cpu: "4"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: paracle-api
spec:
  type: LoadBalancer
  ports:
    - port: 80
      targetPort: 8000
  selector:
    app: paracle-api
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: paracle-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: paracle-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

Apply:

```bash
kubectl apply -f k8s/api.yaml
```

#### Step 6: Configure Ingress (TLS)

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: paracle-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - api.paracle.example.com
      secretName: paracle-tls
  rules:
    - host: api.paracle.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: paracle-api
                port:
                  number: 80
```

Apply:

```bash
kubectl apply -f k8s/ingress.yaml
```

---

### Option 3: VM Deployment (Ubuntu)

**Use Case**: Bare metal, private clouds

#### Step 1: System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.13
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt install python3.13 python3.13-venv python3.13-dev -y

# Install PostgreSQL 16
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update
sudo apt install postgresql-16 postgresql-16-pgvector -y

# Install Redis
sudo apt install redis-server -y

# Install Nginx
sudo apt install nginx -y
```

#### Step 2: Configure PostgreSQL

```bash
# Create database and user
sudo -u postgres psql <<EOF
CREATE DATABASE paracle;
CREATE USER paracle WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE paracle TO paracle;
\c paracle
CREATE EXTENSION vector;
EOF

# Configure PostgreSQL for remote access (if needed)
sudo nano /etc/postgresql/16/main/postgresql.conf
# Set: listen_addresses = '*'

sudo nano /etc/postgresql/16/main/pg_hba.conf
# Add: host all all 0.0.0.0/0 md5

sudo systemctl restart postgresql
```

#### Step 3: Install Paracle

```bash
# Create application user
sudo useradd -m -s /bin/bash paracle
sudo su - paracle

# Clone repository
git clone https://github.com/IbIFACE-Tech/paracle-lite.git
cd paracle-lite

# Create virtual environment
python3.13 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[api,store,events]"

# Configure environment
cp .env.example .env
nano .env  # Edit with production values
```

#### Step 4: Create Systemd Service

```bash
# Exit paracle user
exit

# Create systemd service
sudo nano /etc/systemd/system/paracle-api.service
```

```ini
[Unit]
Description=Paracle API Server
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=paracle
WorkingDirectory=/home/paracle/paracle-lite
Environment="PATH=/home/paracle/paracle-lite/venv/bin"
EnvironmentFile=/home/paracle/paracle-lite/.env
ExecStart=/home/paracle/paracle-lite/venv/bin/uvicorn paracle_api.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable paracle-api
sudo systemctl start paracle-api
sudo systemctl status paracle-api
```

#### Step 5: Configure Nginx Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/paracle
```

```nginx
upstream paracle_api {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.paracle.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.paracle.example.com;

    # TLS Configuration
    ssl_certificate /etc/letsencrypt/live/api.paracle.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.paracle.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    location / {
        proxy_pass http://paracle_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

Enable and reload:

```bash
sudo ln -s /etc/nginx/sites-available/paracle /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Post-Deployment Verification

### Health Checks

```bash
# API health
curl https://api.paracle.example.com/health
# Expected: {"status": "healthy", "database": "connected", "redis": "connected"}

# Detailed health
curl https://api.paracle.example.com/health/ready
# Expected: {"ready": true, "services": {"database": true, "redis": true, "storage": true}}

# Metrics endpoint
curl https://api.paracle.example.com/metrics
# Expected: Prometheus metrics
```

### Functional Tests

```bash
# List agents
curl https://api.paracle.example.com/api/v1/agents

# Run simple agent
curl -X POST https://api.paracle.example.com/api/v1/agents/run \
  -H "Content-Type: application/json" \
  -d '{"agent": "coder", "task": "Hello world"}'
```

---

## Monitoring Setup

See [monitoring-setup.md](monitoring-setup.md) for:

- Prometheus + Grafana configuration
- Log aggregation (ELK/Loki)
- APM (Application Performance Monitoring)
- Alert rules

---

## Troubleshooting

See [troubleshooting.md](troubleshooting.md) for common issues:

- Database connection failures
- Redis connection issues
- API performance problems
- Memory/CPU issues

---

## Next Steps

1. **Configure Monitoring**: Set up Prometheus/Grafana
2. **Enable Backups**: Configure automated database backups
3. **Disaster Recovery**: Test restore procedures
4. **Load Testing**: Verify performance under load
5. **Security Hardening**: Apply additional security measures

---

## Support

- **Documentation**: <https://docs.paracles.com/>/>
- **Issues**: <https://github.com/IbIFACE-Tech/paracle-lite/issues>s>
- **Email**: <support@ibiface.com>m>
