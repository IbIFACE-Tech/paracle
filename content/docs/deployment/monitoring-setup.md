# Monitoring Setup Guide

**Last Updated**: 2026-01-17
**Version**: 1.0

---

## Overview

This guide configures comprehensive monitoring for Paracle using:

- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Loki**: Log aggregation
- **Jaeger**: Distributed tracing
- **AlertManager**: Alert management

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ API Pod1 │  │ API Pod2 │  │ API Pod3 │                   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                   │
└───────┼─────────────┼─────────────┼─────────────────────────┘
        │ metrics     │ logs        │ traces
        ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────┐
│                  Observability Stack                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │Prometheus│  │   Loki   │  │  Jaeger  │                   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                   │
│       │             │              │                         │
│  ┌────▼─────────────▼──────────────▼────┐                    │
│  │            Grafana                   │                    │
│  └──────────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Prometheus Setup

### Installation (Kubernetes)

```bash
# Add Prometheus Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack (Prometheus + Grafana + AlertManager)
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.retention=30d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=100Gi \
  --set grafana.adminPassword=admin-change-me
```

### Configure Paracle Metrics

```python
# packages/paracle_observability/prometheus.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import FastAPI

app = FastAPI()

# Metrics
agent_executions = Counter('paracle_agent_executions_total', 'Total agent executions', ['agent', 'status'])
agent_duration = Histogram('paracle_agent_duration_seconds', 'Agent execution duration', ['agent'])
active_agents = Gauge('paracle_active_agents', 'Number of active agents')
llm_tokens = Counter('paracle_llm_tokens_total', 'LLM tokens consumed', ['provider', 'model'])
llm_cost = Counter('paracle_llm_cost_usd', 'LLM cost in USD', ['provider'])

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")

# Instrument agent execution
@track_execution
async def run_agent(agent_id: str, task: str):
    active_agents.inc()
    start_time = time.time()
    try:
        result = await _execute_agent(agent_id, task)
        agent_executions.labels(agent=agent_id, status='success').inc()
        return result
    except Exception as e:
        agent_executions.labels(agent=agent_id, status='failure').inc()
        raise
    finally:
        duration = time.time() - start_time
        agent_duration.labels(agent=agent_id).observe(duration)
        active_agents.dec()
```

### Prometheus Configuration

```yaml
# k8s/prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s

    scrape_configs:
      # Paracle API
      - job_name: 'paracle-api'
        kubernetes_sd_configs:
        - role: pod
          namespaces:
            names:
            - paracle-prod
        relabel_configs:
        - source_labels: [__meta_kubernetes_pod_label_app]
          action: keep
          regex: paracle-api
        - source_labels: [__meta_kubernetes_pod_ip]
          target_label: __address__
          replacement: ${1}:8000

      # PostgreSQL
      - job_name: 'postgres'
        static_configs:
        - targets: ['postgres-exporter:9187']

      # Redis
      - job_name: 'redis'
        static_configs:
        - targets: ['redis-exporter:9121']
```

---

## Grafana Dashboards

### Installation

```bash
# Access Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# Open browser: http://localhost:3000
# Login: admin / admin-change-me
```

### Paracle Dashboard (JSON)

```json
{
  "dashboard": {
    "title": "Paracle Overview",
    "panels": [
      {
        "title": "Agent Executions (Rate)",
        "targets": [
          {
            "expr": "rate(paracle_agent_executions_total[5m])"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Agent Success Rate",
        "targets": [
          {
            "expr": "sum(rate(paracle_agent_executions_total{status='success'}[5m])) / sum(rate(paracle_agent_executions_total[5m])) * 100"
          }
        ],
        "type": "singlestat",
        "format": "percent"
      },
      {
        "title": "Active Agents",
        "targets": [
          {
            "expr": "paracle_active_agents"
          }
        ],
        "type": "singlestat"
      },
      {
        "title": "LLM Token Usage",
        "targets": [
          {
            "expr": "rate(paracle_llm_tokens_total[5m])"
          }
        ],
        "type": "graph"
      },
      {
        "title": "LLM Cost ($/hour)",
        "targets": [
          {
            "expr": "rate(paracle_llm_cost_usd[1h]) * 3600"
          }
        ],
        "type": "singlestat",
        "format": "currencyUSD"
      },
      {
        "title": "API Latency (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(paracle_agent_duration_seconds_bucket[5m]))"
          }
        ],
        "type": "graph"
      }
    ]
  }
}
```

**Import Dashboard**:

1. Go to Grafana → Dashboards → Import
2. Paste JSON above
3. Select Prometheus data source
4. Click "Import"

---

## Log Aggregation (Loki)

### Installation

```bash
# Install Loki
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --set loki.persistence.enabled=true \
  --set loki.persistence.size=100Gi \
  --set promtail.enabled=true
```

### Configure Application Logging

```python
# packages/paracle_core/logging.py
import logging
from pythonjsonlogger import jsonlogger

def configure_logging():
    logger = logging.getLogger()
    handler = logging.StreamHandler()

    # JSON format for Loki
    formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s %(agent)s %(task_id)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Usage
logger.info("Agent execution started", extra={
    "agent": "coder",
    "task_id": "task-123",
    "user_id": "user-456"
})
```

### Loki Queries in Grafana

```logql
# All errors in last hour
{app="paracle-api"} |= "ERROR" | json

# Agent execution logs
{app="paracle-api", agent=~".+"} | json | line_format "{{.timestamp}} [{{.agent}}] {{.message}}"

# Failed agent executions
{app="paracle-api"} |= "status=failure" | json | agent != ""

# LLM API errors
{app="paracle-api"} |= "provider=" |= "error" | json
```

---

## Distributed Tracing (Jaeger)

### Installation

```bash
# Install Jaeger Operator
kubectl create namespace observability
kubectl apply -f https://github.com/jaegertracing/jaeger-operator/releases/download/v1.50.0/jaeger-operator.yaml

# Deploy Jaeger instance
cat <<EOF | kubectl apply -f -
apiVersion: jaegertracing.io/v1
kind: Jaeger
metadata:
  name: paracle-jaeger
  namespace: observability
spec:
  strategy: production
  storage:
    type: elasticsearch
    options:
      es:
        server-urls: http://elasticsearch:9200
EOF
```

### Instrument Application

```python
# packages/paracle_observability/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def configure_tracing():
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger-agent",
        agent_port=6831,
    )

    trace.set_tracer_provider(TracerProvider())
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )

tracer = trace.get_tracer(__name__)

# Usage
@tracer.start_as_current_span("agent_execution")
async def run_agent(agent_id: str):
    span = trace.get_current_span()
    span.set_attribute("agent.id", agent_id)
    span.set_attribute("agent.version", "1.0")

    # Nested spans
    with tracer.start_as_current_span("llm_call"):
        result = await call_llm(prompt)

    return result
```

---

## AlertManager Configuration

### Alert Rules

```yaml
# k8s/alert-rules.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-alerts
  namespace: monitoring
data:
  alerts.yml: |
    groups:
    - name: paracle
      interval: 30s
      rules:
      # High error rate
      - alert: HighAgentFailureRate
        expr: |
          (sum(rate(paracle_agent_executions_total{status="failure"}[5m]))
          / sum(rate(paracle_agent_executions_total[5m]))) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High agent failure rate (>10%)"
          description: "{{ $value }}% of agent executions are failing"

      # High latency
      - alert: HighAgentLatency
        expr: |
          histogram_quantile(0.95,
            rate(paracle_agent_duration_seconds_bucket[5m])
          ) > 60
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High agent latency (p95 > 60s)"

      # Database connection issues
      - alert: DatabaseConnectionFailure
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL is down"

      # High LLM cost
      - alert: HighLLMCost
        expr: rate(paracle_llm_cost_usd[1h]) > 100
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "LLM cost exceeds $100/hour"

      # Low API availability
      - alert: LowAPIAvailability
        expr: |
          (sum(rate(http_requests_total{status=~"5.."}[5m]))
          / sum(rate(http_requests_total[5m]))) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "API error rate >1%"
```

### AlertManager Configuration

```yaml
# k8s/alertmanager-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  namespace: monitoring
data:
  alertmanager.yml: |
    global:
      resolve_timeout: 5m

    route:
      group_by: ['alertname', 'severity']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 12h
      receiver: 'team-ops'
      routes:
      - match:
          severity: critical
        receiver: 'pagerduty'
      - match:
          severity: warning
        receiver: 'slack'

    receivers:
    - name: 'team-ops'
      email_configs:
      - to: 'ops@paracle.com'

    - name: 'pagerduty'
      pagerduty_configs:
      - service_key: $PAGERDUTY_SERVICE_KEY

    - name: 'slack'
      slack_configs:
      - api_url: $SLACK_WEBHOOK_URL
        channel: '#paracle-alerts'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}\n{{ end }}'
```

---

## Health Checks

### Application Health Endpoints

```python
# packages/paracle_api/health.py
from fastapi import APIRouter, status
from sqlalchemy import select
from redis import asyncio as aioredis

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "version": "1.0.3"}

@router.get("/health/ready")
async def readiness_check():
    """Readiness check (database, redis)"""
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "storage": await check_storage()
    }

    ready = all(checks.values())
    status_code = status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE

    return {"ready": ready, "services": checks}, status_code

async def check_database():
    try:
        async with db.engine.begin() as conn:
            await conn.execute(select(1))
        return True
    except Exception:
        return False

async def check_redis():
    try:
        redis = aioredis.from_url(REDIS_URL)
        await redis.ping()
        return True
    except Exception:
        return False
```

---

## Monitoring Checklist

### Week 1: Setup

- [ ] Install Prometheus + Grafana
- [ ] Configure application metrics
- [ ] Create basic dashboards
- [ ] Set up log aggregation (Loki)
- [ ] Configure health check endpoints

### Week 2: Alerts

- [ ] Define alert rules
- [ ] Configure AlertManager
- [ ] Test alert notifications (email, Slack, PagerDuty)
- [ ] Set up on-call rotation

### Week 3: Advanced

- [ ] Enable distributed tracing (Jaeger)
- [ ] Create custom dashboards
- [ ] Configure SLO/SLI tracking
- [ ] Load test with monitoring

---

## Troubleshooting

### Issue: Metrics not appearing

```bash
# Check Prometheus targets
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Visit: http://localhost:9090/targets

# Verify metrics endpoint
kubectl exec -it paracle-api-xxx -- curl localhost:8000/metrics
```

### Issue: Alerts not firing

```bash
# Check AlertManager status
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-alertmanager 9093:9093
# Visit: http://localhost:9093

# View alert rules
kubectl exec -it prometheus-xxx -n monitoring -- promtool check rules /etc/prometheus/rules.yml
```

---

## Related Documentation

- [disaster-recovery.md](disaster-recovery.md) - DR procedures
- [incident-response.md](incident-response.md) - Incident handling
- [performance-tuning.md](performance-tuning.md) - Performance optimization
