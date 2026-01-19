# Scaling Guide

**Last Updated**: 2026-01-18
**Version**: 1.0
**Target**: Production deployments handling 1000+ req/s

---

## Overview

Comprehensive guide for scaling Paracle from single-instance to high-availability multi-node deployment.

**Scaling Targets**:

- **Small**: 100-500 req/s, 2-5 API replicas
- **Medium**: 500-2000 req/s, 5-10 API replicas
- **Large**: 2000-10000+ req/s, 10-50 API replicas

---

## Architecture Tiers

### Tier 1: Single Instance (Development)

```
┌────────────────────────────────┐
│       Single Server            │
│  ┌──────────┐  ┌──────────┐   │
│  │   API    │  │ Postgres │   │
│  │  (1 pod) │  │  Redis   │   │
│  └──────────┘  └──────────┘   │
└────────────────────────────────┘
    ↓ 10-100 req/s
```

**Specs**: 4 CPU, 8GB RAM
**Cost**: ~$50-100/month

### Tier 2: Basic HA (Staging)

```
┌─────────────────────────────────────┐
│      Load Balancer (Nginx)          │
└───────────┬─────────────────────────┘
            ↓
    ┌───────┴───────┐
    ↓               ↓
┌─────────┐     ┌─────────┐
│ API Pod1│     │ API Pod2│
└────┬────┘     └────┬────┘
     │               │
     └───────┬───────┘
             ↓
    ┌────────────────┐
    │ PostgreSQL (RDS)│
    │ Redis (managed) │
    └────────────────┘
    ↓ 100-500 req/s
```

**Specs**: 3 API pods (2 CPU, 4GB each), managed DB/Redis
**Cost**: ~$300-500/month

### Tier 3: Production HA (Multi-AZ)

```
                ┌─────────────────┐
                │  Global LB      │
                │ (Cloud LB/CF)   │
                └────────┬────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    ┌───▼───┐        ┌───▼───┐       ┌───▼───┐
    │ AZ-A  │        │ AZ-B  │       │ AZ-C  │
    │ 5 pods│        │ 5 pods│       │ 5 pods│
    └───┬───┘        └───┬───┘       └───┬───┘
        │                │                │
        └────────────────┼────────────────┘
                         ↓
            ┌────────────────────────┐
            │ PostgreSQL Multi-AZ    │
            │ - Primary (write)      │
            │ - 2 Read Replicas      │
            │                        │
            │ Redis Cluster (6 nodes)│
            └────────────────────────┘
    ↓ 1000-10000+ req/s
```

**Specs**: 15 API pods (4 CPU, 8GB each), PostgreSQL Multi-AZ + read replicas, Redis cluster
**Cost**: ~$2000-5000/month

---

## Horizontal Pod Autoscaling (HPA)

### Kubernetes HPA Configuration

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: paracle-api-hpa
  namespace: paracle-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: paracle-api
  minReplicas: 3
  maxReplicas: 50
  metrics:
    # CPU-based scaling
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70

    # Memory-based scaling
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80

    # Custom metrics (requests per second)
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "100"

  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 100
          periodSeconds: 30
        - type: Pods
          value: 5
          periodSeconds: 30
      selectPolicy: Max
```

### Custom Metrics (Prometheus Adapter)

```yaml
# Install Prometheus Adapter
helm install prometheus-adapter prometheus-community/prometheus-adapter \
  --namespace monitoring \
  --set prometheus.url=http://prometheus-server.monitoring.svc

# Custom metrics config
apiVersion: v1
kind: ConfigMap
metadata:
  name: adapter-config
data:
  config.yaml: |
    rules:
    - seriesQuery: 'http_requests_total{namespace="paracle-prod"}'
      resources:
        overrides:
          namespace: {resource: "namespace"}
          pod: {resource: "pod"}
      name:
        matches: "^(.*)_total"
        as: "${1}_per_second"
      metricsQuery: 'sum(rate(<<.Series>>{<<.LabelMatchers>>}[1m])) by (<<.GroupBy>>)'
```

### Test HPA

```bash
# Check HPA status
kubectl get hpa paracle-api-hpa -n paracle-prod

# Watch scaling events
kubectl get hpa -w

# Generate load
kubectl run -it --rm load-generator --image=busybox --restart=Never -- /bin/sh
while true; do wget -q -O- http://paracle-api.paracle-prod.svc/health; done
```

---

## Load Balancing

### Option 1: Kubernetes Ingress (NGINX)

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: paracle-ingress
  namespace: paracle-prod
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/limit-rps: "100"
    nginx.ingress.kubernetes.io/upstream-hash-by: "$remote_addr"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - api.paracle.com
      secretName: paracle-tls
  rules:
    - host: api.paracle.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: paracle-api
                port:
                  number: 8000
```

### Option 2: Cloud Load Balancer (AWS ALB)

```yaml
# k8s/service-alb.yaml
apiVersion: v1
kind: Service
metadata:
  name: paracle-api-alb
  namespace: paracle-prod
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-scheme: "internet-facing"
    service.beta.kubernetes.io/aws-load-balancer-nlb-target-type: "ip"
    service.beta.kubernetes.io/aws-load-balancer-healthcheck-path: "/health"
    service.beta.kubernetes.io/aws-load-balancer-healthcheck-interval: "10"
spec:
  type: LoadBalancer
  selector:
    app: paracle-api
  ports:
    - port: 443
      targetPort: 8000
      protocol: TCP
```

### Option 3: External Nginx (VM)

```nginx
# /etc/nginx/nginx.conf
upstream paracle_api {
    least_conn;  # Load balancing algorithm

    server api-1.internal:8000 max_fails=3 fail_timeout=30s;
    server api-2.internal:8000 max_fails=3 fail_timeout=30s;
    server api-3.internal:8000 max_fails=3 fail_timeout=30s;

    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name api.paracle.com;

    ssl_certificate /etc/letsencrypt/live/api.paracle.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.paracle.com/privkey.pem;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s;
    limit_req zone=api_limit burst=200 nodelay;

    location / {
        proxy_pass http://paracle_api;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Connection "";

        # Timeouts
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Health checks
        proxy_next_upstream error timeout http_502 http_503 http_504;
    }
}
```

---

## Database Scaling

### Read Replicas (PostgreSQL)

```yaml
# k8s/postgres-replica.yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres-read-replica
spec:
  selector:
    app: postgres
    role: replica
  ports:
    - port: 5432

---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres-replica
spec:
  serviceName: postgres-read-replica
  replicas: 2
  selector:
    matchLabels:
      app: postgres
      role: replica
  template:
    metadata:
      labels:
        app: postgres
        role: replica
    spec:
      containers:
        - name: postgres
          image: postgres:16
          env:
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata
          command:
            - postgres
            - -c
            - hot_standby=on
            - -c
            - wal_level=replica
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 100Gi
```

### Connection Pooling (PgBouncer)

```ini
# pgbouncer.ini
[databases]
paracle = host=postgres-primary port=5432 dbname=paracle

[pgbouncer]
listen_port = 6432
listen_addr = *
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt

# Pool configuration
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
reserve_pool_size = 5
reserve_pool_timeout = 3

# Timeouts
server_idle_timeout = 600
server_connect_timeout = 15
query_wait_timeout = 120
```

```yaml
# k8s/pgbouncer.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pgbouncer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pgbouncer
  template:
    metadata:
      labels:
        app: pgbouncer
    spec:
      containers:
        - name: pgbouncer
          image: edoburu/pgbouncer:1.21.0
          ports:
            - containerPort: 6432
          volumeMounts:
            - name: config
              mountPath: /etc/pgbouncer
      volumes:
        - name: config
          configMap:
            name: pgbouncer-config
```

### Application-Level Read/Write Splitting

```python
# packages/paracle_store/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class DatabaseRouter:
    def __init__(self):
        # Write connection (primary)
        self.write_engine = create_engine(
            "postgresql://user:pass@primary.db:5432/paracle",
            pool_size=20,
            max_overflow=10
        )

        # Read connections (replicas)
        self.read_engines = [
            create_engine(
                "postgresql://user:pass@replica1.db:5432/paracle",
                pool_size=30,
                max_overflow=20
            ),
            create_engine(
                "postgresql://user:pass@replica2.db:5432/paracle",
                pool_size=30,
                max_overflow=20
            )
        ]
        self.read_index = 0

    def get_write_session(self):
        """Get session for write operations"""
        Session = sessionmaker(bind=self.write_engine)
        return Session()

    def get_read_session(self):
        """Get session for read operations (round-robin)"""
        engine = self.read_engines[self.read_index]
        self.read_index = (self.read_index + 1) % len(self.read_engines)
        Session = sessionmaker(bind=engine)
        return Session()

# Usage
router = DatabaseRouter()

# Write
with router.get_write_session() as session:
    session.add(new_agent)
    session.commit()

# Read
with router.get_read_session() as session:
    agents = session.query(Agent).all()
```

---

## Redis Scaling

### Redis Cluster (6 nodes minimum)

```yaml
# k8s/redis-cluster.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis-cluster
spec:
  serviceName: redis-cluster
  replicas: 6
  selector:
    matchLabels:
      app: redis-cluster
  template:
    metadata:
      labels:
        app: redis-cluster
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          ports:
            - containerPort: 6379
            - containerPort: 16379
          command:
            - redis-server
            - /conf/redis.conf
          volumeMounts:
            - name: conf
              mountPath: /conf
            - name: data
              mountPath: /data
      volumes:
        - name: conf
          configMap:
            name: redis-cluster-config
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 20Gi
```

```bash
# Initialize cluster
kubectl exec -it redis-cluster-0 -- redis-cli --cluster create \
  $(kubectl get pods -l app=redis-cluster -o jsonpath='{range.items[*]}{.status.podIP}:6379 {end}') \
  --cluster-replicas 1
```

### Redis Sentinel (HA)

```yaml
# k8s/redis-sentinel.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-sentinel-config
data:
  sentinel.conf: |
    sentinel monitor mymaster redis-master 6379 2
    sentinel down-after-milliseconds mymaster 5000
    sentinel parallel-syncs mymaster 1
    sentinel failover-timeout mymaster 10000

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-sentinel
spec:
  replicas: 3
  selector:
    matchLabels:
      app: redis-sentinel
  template:
    metadata:
      labels:
        app: redis-sentinel
    spec:
      containers:
        - name: sentinel
          image: redis:7-alpine
          command: ["redis-sentinel", "/conf/sentinel.conf"]
          ports:
            - containerPort: 26379
          volumeMounts:
            - name: config
              mountPath: /conf
      volumes:
        - name: config
          configMap:
            name: redis-sentinel-config
```

---

## Caching Strategies

### Multi-Layer Caching

```python
# packages/paracle_cache/multi_layer.py
from functools import wraps
import redis
import pickle

class MultiLayerCache:
    def __init__(self):
        # L1: In-memory (per-pod)
        self.memory_cache = {}
        self.memory_ttl = 60  # 1 minute

        # L2: Redis (shared)
        self.redis = redis.Redis(
            host='redis-cluster',
            port=6379,
            decode_responses=False
        )
        self.redis_ttl = 3600  # 1 hour

    def get(self, key: str):
        # Try L1 (memory)
        if key in self.memory_cache:
            return self.memory_cache[key]

        # Try L2 (Redis)
        value = self.redis.get(key)
        if value:
            deserialized = pickle.loads(value)
            # Populate L1
            self.memory_cache[key] = deserialized
            return deserialized

        return None

    def set(self, key: str, value, ttl: int = None):
        # Store in L1
        self.memory_cache[key] = value

        # Store in L2
        self.redis.setex(
            key,
            ttl or self.redis_ttl,
            pickle.dumps(value)
        )

def cached(ttl: int = 3600):
    """Decorator for caching function results"""
    cache = MultiLayerCache()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"

            # Try cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Cache miss - execute function
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        return wrapper
    return decorator

# Usage
@cached(ttl=600)
def get_agent_spec(agent_id: str):
    # Expensive operation (DB query, file I/O)
    return load_agent_from_db(agent_id)
```

---

## Scaling Checklist

### Pre-Scale Validation

```bash
# 1. Check current resource usage
kubectl top nodes
kubectl top pods -n paracle-prod

# 2. Verify database connections
kubectl exec -it postgres-0 -- psql -U paracle -c "SELECT count(*) FROM pg_stat_activity;"

# 3. Check Redis memory
kubectl exec -it redis-0 -- redis-cli INFO memory

# 4. Review metrics
curl http://prometheus:9090/api/v1/query?query=rate(http_requests_total[5m])
```

### Scaling Steps

1. **Scale API pods**:

   ```bash
   kubectl scale deployment paracle-api --replicas=10 -n paracle-prod
   ```

2. **Add read replicas**:

   ```bash
   kubectl scale statefulset postgres-replica --replicas=3 -n paracle-prod
   ```

3. **Scale Redis**:

   ```bash
   kubectl scale statefulset redis-cluster --replicas=9 -n paracle-prod
   ```

4. **Update HPA limits**:

   ```bash
   kubectl patch hpa paracle-api-hpa -p '{"spec":{"maxReplicas":50}}'
   ```

5. **Verify**:
   ```bash
   kubectl get pods -n paracle-prod
   kubectl get hpa -n paracle-prod
   ```

---

## Load Testing

### Using Locust

```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class ParacleUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def health_check(self):
        self.client.get("/health")

    @task(2)
    def list_agents(self):
        self.client.get("/api/v1/agents")

    @task(1)
    def run_agent(self):
        self.client.post("/api/v1/agents/run", json={
            "agent": "coder",
            "task": "Generate hello world"
        })

# Run
locust -f tests/load/locustfile.py --host=https://api.paracle.com --users=1000 --spawn-rate=10
```

### Target Metrics

| Metric            | Target     | Critical  |
| ----------------- | ---------- | --------- |
| **Throughput**    | 1000 req/s | 500 req/s |
| **Latency (p50)** | <200ms     | <500ms    |
| **Latency (p95)** | <500ms     | <1000ms   |
| **Latency (p99)** | <1000ms    | <2000ms   |
| **Error Rate**    | <0.1%      | <1%       |
| **Availability**  | >99.9%     | >99%      |

---

## Cost Optimization

### Right-Sizing

```bash
# Analyze resource usage
kubectl top pods -n paracle-prod --containers

# Adjust resource requests/limits
kubectl set resources deployment paracle-api \
  --requests=cpu=500m,memory=1Gi \
  --limits=cpu=2000m,memory=4Gi
```

### Spot Instances (AWS)

```yaml
# Use spot instances for non-critical workloads
nodeSelector:
  node.kubernetes.io/instance-type: t3.medium
  karpenter.sh/capacity-type: spot
```

### Auto-Shutdown (Dev/Staging)

```bash
# Scale down at night
0 22 * * * kubectl scale deployment paracle-api --replicas=1 -n paracle-staging
0 6 * * * kubectl scale deployment paracle-api --replicas=3 -n paracle-staging
```

---

## Monitoring Scaling

### Grafana Dashboard

```json
{
  "panels": [
    {
      "title": "API Replicas",
      "targets": [
        {
          "expr": "count(up{job='paracle-api'} == 1)"
        }
      ]
    },
    {
      "title": "Requests per Pod",
      "targets": [
        {
          "expr": "rate(http_requests_total[5m]) / count(up{job='paracle-api'} == 1)"
        }
      ]
    },
    {
      "title": "HPA Target vs Current",
      "targets": [
        { "expr": "kube_horizontalpodautoscaler_status_desired_replicas" },
        { "expr": "kube_horizontalpodautoscaler_status_current_replicas" }
      ]
    }
  ]
}
```

---

## Related Documentation

- [production-deployment.md](production-deployment.md) - Deployment procedures
- [monitoring-setup.md](monitoring-setup.md) - Monitoring stack
- [performance-tuning.md](performance-tuning.md) - Performance optimization
