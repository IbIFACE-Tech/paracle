# Troubleshooting Guide

**Last Updated**: 2026-01-18
**Version**: 1.0
**Support**: <support@ibiface.com>

---

## Overview

Common issues and solutions for Paracle production deployments.

**Quick Diagnostic Commands**:

```bash
# Health check
curl -i https://api.paracle.com/health

# Pod status
kubectl get pods -n paracle-prod

# Logs
kubectl logs -l app=paracle-api --tail=100 -n paracle-prod

# Metrics
curl http://prometheus:9090/api/v1/query?query=up{job="paracle-api"}
```

---

## API Issues

### Issue: API Pods Crashing (CrashLoopBackOff)

**Symptoms**:

- Pods repeatedly restarting
- Error: `CrashLoopBackOff`
- Users unable to access API

**Diagnosis**:

```bash
# Check pod status
kubectl get pods -n paracle-prod -l app=paracle-api

# Check recent logs
kubectl logs <pod-name> --previous -n paracle-prod

# Check events
kubectl describe pod <pod-name> -n paracle-prod

# Check resource usage
kubectl top pod <pod-name> -n paracle-prod
```

**Common Causes & Solutions**:

#### 1. Out of Memory (OOM)

```bash
# Symptom: OOMKilled in describe output
kubectl describe pod <pod-name> | grep -i oom

# Solution: Increase memory limit
kubectl set resources deployment/paracle-api --limits=memory=4Gi -n paracle-prod

# Or edit deployment
kubectl edit deployment/paracle-api -n paracle-prod
# Change: resources.limits.memory: "4Gi"
```

#### 2. Database Connection Failure

```bash
# Check database connectivity
kubectl exec -it <pod-name> -n paracle-prod -- curl postgres-primary:5432

# Check database password
kubectl get secret paracle-secrets -o jsonpath='{.data.DATABASE_PASSWORD}' | base64 -d

# Test connection
kubectl exec -it postgres-0 -n paracle-prod -- psql -U paracle -c "SELECT 1"

# Solution: Update database URL
kubectl set env deployment/paracle-api DATABASE_URL="postgresql://user:newpass@host:5432/paracle"
```

#### 3. Missing Environment Variable

```bash
# Check environment variables
kubectl exec <pod-name> -- env | grep -E "OPENAI|CLAUDE|DATABASE"

# Solution: Add missing variable
kubectl set env deployment/paracle-api OPENAI_API_KEY="sk-..."
```

#### 4. Image Pull Error

```bash
# Check image status
kubectl describe pod <pod-name> | grep -i "image"

# Solution: Update image pull secret
kubectl create secret docker-registry regcred \
  --docker-server=<registry> \
  --docker-username=<username> \
  --docker-password=<password>

kubectl patch serviceaccount default -p '{"imagePullSecrets": [{"name": "regcred"}]}'
```

---

### Issue: High API Latency (p95 > 1s)

**Symptoms**:

- Slow response times
- Users complaining about performance
- Grafana showing high latency

**Diagnosis**:

```bash
# Check current latency
curl "http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"

# Check LLM provider latency
kubectl logs -l app=paracle-api --tail=100 | grep "llm_duration"

# Check database query time
kubectl exec postgres-0 -- psql -U paracle -c "SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
```

**Common Causes & Solutions**:

#### 1. Slow Database Queries

```bash
# Find slow queries
kubectl exec postgres-0 -- psql -U paracle <<EOF
SELECT
    calls,
    mean_exec_time,
    query
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC
LIMIT 10;
EOF

# Solution: Add indexes
kubectl exec postgres-0 -- psql -U paracle -c "CREATE INDEX CONCURRENTLY idx_agents_created_at ON agents(created_at);"
```

#### 2. LLM Provider Timeout

```bash
# Check LLM provider status
curl https://status.openai.com/api/v2/status.json
curl https://status.anthropic.com/api/v2/status.json

# Solution: Increase timeout or switch provider
kubectl set env deployment/paracle-api LLM_TIMEOUT=120 DEFAULT_LLM_PROVIDER=anthropic
```

#### 3. Redis Slow Response

```bash
# Check Redis latency
kubectl exec redis-0 -- redis-cli --latency

# Check Redis memory
kubectl exec redis-0 -- redis-cli INFO memory

# Solution: Clear cache or increase memory
kubectl exec redis-0 -- redis-cli FLUSHDB
kubectl set resources statefulset redis --limits=memory=8Gi
```

#### 4. Too Many Concurrent Requests

```bash
# Check active requests
kubectl exec <pod-name> -- ps aux | wc -l

# Solution: Scale up or add rate limiting
kubectl scale deployment/paracle-api --replicas=10
kubectl set env deployment/paracle-api RATE_LIMIT=100
```

---

### Issue: 500 Internal Server Errors

**Symptoms**:

- API returning 500 status codes
- Error logs showing exceptions
- Users seeing error messages

**Diagnosis**:

```bash
# Check error logs
kubectl logs -l app=paracle-api --tail=500 | grep -i "error\|exception"

# Check error rate
curl "http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status='500'}[5m])"

# Check Sentry (if integrated)
# Visit: https://sentry.io/organizations/paracle/issues/
```

**Common Causes & Solutions**:

#### 1. Unhandled Exception

```bash
# Find stack trace
kubectl logs <pod-name> --tail=200 | grep -A 20 "Traceback"

# Solution: Fix code or add error handling
# Deploy patched version
kubectl set image deployment/paracle-api api=paracle-api:v1.0.4
```

#### 2. Missing Dependency

```bash
# Check import errors
kubectl logs <pod-name> | grep "ImportError\|ModuleNotFoundError"

# Solution: Rebuild image with dependency
# docker build --tag paracle-api:v1.0.4 .
# docker push paracle-api:v1.0.4
```

#### 3. Configuration Error

```bash
# Check config
kubectl get configmap paracle-config -o yaml

# Solution: Fix and reload
kubectl edit configmap paracle-config
kubectl rollout restart deployment/paracle-api
```

---

## Database Issues

### Issue: Database Connection Pool Exhausted

**Symptoms**:

- Error: `remaining connection slots reserved`
- Error: `FATAL: too many connections`
- API slow or timing out

**Diagnosis**:

```bash
# Check active connections
kubectl exec postgres-0 -- psql -U paracle -c "SELECT count(*) FROM pg_stat_activity;"

# Check connection limit
kubectl exec postgres-0 -- psql -U paracle -c "SHOW max_connections;"

# Check connections by state
kubectl exec postgres-0 -- psql -U paracle -c "SELECT state, count(*) FROM pg_stat_activity GROUP BY state;"
```

**Solutions**:

#### 1. Increase Connection Limit

```bash
# PostgreSQL (requires restart)
kubectl exec postgres-0 -- psql -U paracle -c "ALTER SYSTEM SET max_connections = 200;"
kubectl delete pod postgres-0  # Restart
```

#### 2. Deploy PgBouncer

```bash
# Deploy PgBouncer
kubectl apply -f k8s/pgbouncer.yaml

# Update application to use PgBouncer
kubectl set env deployment/paracle-api DATABASE_URL="postgresql://user:pass@pgbouncer:6432/paracle"
```

#### 3. Kill Idle Connections

```bash
# Kill idle connections > 10 minutes
kubectl exec postgres-0 -- psql -U paracle <<EOF
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND state_change < now() - interval '10 minutes';
EOF
```

#### 4. Reduce Application Pool Size

```bash
kubectl set env deployment/paracle-api DB_POOL_SIZE=10 DB_MAX_OVERFLOW=5
```

---

### Issue: Slow Database Queries

**Symptoms**:

- High database CPU usage
- Long-running queries
- API timeouts on database operations

**Diagnosis**:

```bash
# Find slow queries (current)
kubectl exec postgres-0 -- psql -U paracle -c "SELECT pid, now() - query_start AS duration, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC;"

# Find slow queries (historical)
kubectl exec postgres-0 -- psql -U paracle -c "SELECT calls, mean_exec_time, query FROM pg_stat_statements WHERE mean_exec_time > 100 ORDER BY mean_exec_time DESC LIMIT 10;"

# Check for missing indexes
kubectl exec postgres-0 -- psql -U paracle -c "SELECT schemaname, tablename, attname FROM pg_stats WHERE n_distinct > 100 AND correlation < 0.1;"
```

**Solutions**:

#### 1. Add Indexes

```bash
# Create indexes
kubectl exec postgres-0 -- psql -U paracle <<EOF
CREATE INDEX CONCURRENTLY idx_agents_created_at ON agents(created_at);
CREATE INDEX CONCURRENTLY idx_executions_agent_status ON executions(agent_id, status);
EOF
```

#### 2. Kill Long-Running Queries

```bash
# Kill queries running > 5 minutes
kubectl exec postgres-0 -- psql -U paracle -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE now() - query_start > interval '5 minutes';"
```

#### 3. Optimize Query

```bash
# Analyze query plan
kubectl exec postgres-0 -- psql -U paracle -c "EXPLAIN ANALYZE SELECT * FROM agents WHERE created_at > '2026-01-01';"

# Rewrite query or add indexes based on plan
```

---

## Redis Issues

### Issue: Redis Out of Memory

**Symptoms**:

- Error: `OOM command not allowed`
- Redis refusing write operations
- Cache misses increasing

**Diagnosis**:

```bash
# Check memory usage
kubectl exec redis-0 -- redis-cli INFO memory

# Check eviction stats
kubectl exec redis-0 -- redis-cli INFO stats | grep evicted

# Check key count
kubectl exec redis-0 -- redis-cli DBSIZE
```

**Solutions**:

#### 1. Increase Memory Limit

```bash
kubectl set resources statefulset redis --limits=memory=8Gi -n paracle-prod
kubectl delete pod redis-0  # Restart
```

#### 2. Enable Eviction Policy

```bash
kubectl exec redis-0 -- redis-cli CONFIG SET maxmemory-policy allkeys-lru
kubectl exec redis-0 -- redis-cli CONFIG SET maxmemory 6gb
```

#### 3. Clear Non-Critical Keys

```bash
# Clear cache keys
kubectl exec redis-0 -- redis-cli --scan --pattern "cache:*" | xargs redis-cli DEL

# Clear old session keys
kubectl exec redis-0 -- redis-cli --scan --pattern "session:*" | xargs redis-cli DEL
```

#### 4. Reduce TTL

```bash
# Update application to use shorter TTLs
kubectl set env deployment/paracle-api CACHE_TTL=300  # 5 minutes
```

---

### Issue: Redis Connection Timeout

**Symptoms**:

- Error: `Connection timeout`
- Error: `Too many clients`
- Intermittent cache failures

**Diagnosis**:

```bash
# Check connected clients
kubectl exec redis-0 -- redis-cli CLIENT LIST | wc -l

# Check max clients
kubectl exec redis-0 -- redis-cli CONFIG GET maxclients

# Test connectivity
kubectl exec <api-pod> -- curl redis:6379
```

**Solutions**:

#### 1. Increase Max Clients

```bash
kubectl exec redis-0 -- redis-cli CONFIG SET maxclients 10000
```

#### 2. Use Connection Pooling

```python
# Application code
import redis
from redis.connection import ConnectionPool

pool = ConnectionPool(host='redis', port=6379, max_connections=50)
redis_client = redis.Redis(connection_pool=pool)
```

#### 3. Close Idle Connections

```bash
kubectl exec redis-0 -- redis-cli CONFIG SET timeout 300  # Close after 5min idle
```

---

## LLM Provider Issues

### Issue: OpenAI/Anthropic API Errors

**Symptoms**:

- Error: `Rate limit exceeded`
- Error: `Invalid API key`
- Error: `Service unavailable`

**Diagnosis**:

```bash
# Check API key
kubectl get secret paracle-secrets -o jsonpath='{.data.OPENAI_API_KEY}' | base64 -d | cut -c1-10

# Check provider status
curl https://status.openai.com/api/v2/status.json
curl https://status.anthropic.com/api/v2/status.json

# Check recent errors
kubectl logs -l app=paracle-api --tail=100 | grep -i "openai\|anthropic\|rate limit"
```

**Solutions**:

#### 1. Rate Limit Exceeded

```bash
# Enable rate limiting in application
kubectl set env deployment/paracle-api LLM_RATE_LIMIT=50

# Switch to backup provider
kubectl set env deployment/paracle-api DEFAULT_LLM_PROVIDER=anthropic
```

#### 2. Invalid API Key

```bash
# Update API key
kubectl create secret generic paracle-secrets \
  --from-literal=OPENAI_API_KEY=sk-new-key \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart pods to pick up new secret
kubectl rollout restart deployment/paracle-api
```

#### 3. Provider Outage

```bash
# Switch provider immediately
kubectl set env deployment/paracle-api DEFAULT_LLM_PROVIDER=gemini

# Enable fallback providers
kubectl set env deployment/paracle-api FALLBACK_PROVIDERS="anthropic,gemini,openai"
```

---

## Kubernetes Issues

### Issue: Pods Not Scheduling

**Symptoms**:

- Pods stuck in `Pending` state
- Error: `Insufficient cpu/memory`
- Pods not starting

**Diagnosis**:

```bash
# Check pod status
kubectl get pods -n paracle-prod

# Check events
kubectl get events --sort-by='.lastTimestamp' -n paracle-prod | tail -20

# Check node capacity
kubectl describe nodes | grep -A 5 "Allocated resources"
```

**Solutions**:

#### 1. Insufficient Resources

```bash
# Add more nodes
# AWS EKS
eksctl scale nodegroup --cluster=paracle-prod --name=ng-1 --nodes=5

# Or reduce resource requests
kubectl set resources deployment/paracle-api --requests=cpu=500m,memory=1Gi
```

#### 2. Node Selector Mismatch

```bash
# Check node labels
kubectl get nodes --show-labels

# Update deployment
kubectl patch deployment paracle-api -p '{"spec":{"template":{"spec":{"nodeSelector":null}}}}'
```

#### 3. Pod Disruption Budget

```bash
# Check PDB
kubectl get pdb -n paracle-prod

# Temporarily allow disruption
kubectl delete pdb paracle-api-pdb -n paracle-prod
```

---

### Issue: Service Not Accessible

**Symptoms**:

- Cannot access service from outside cluster
- Error: `Connection refused`
- Load balancer not provisioned

**Diagnosis**:

```bash
# Check service
kubectl get svc -n paracle-prod

# Check endpoints
kubectl get endpoints -n paracle-prod

# Check ingress
kubectl get ingress -n paracle-prod

# Test from within cluster
kubectl run -it --rm debug --image=busybox --restart=Never -- wget -O- http://paracle-api:8000/health
```

**Solutions**:

#### 1. Load Balancer Pending

```bash
# Check cloud provider events
kubectl describe svc paracle-api -n paracle-prod

# Wait or recreate service
kubectl delete svc paracle-api -n paracle-prod
kubectl apply -f k8s/service.yaml
```

#### 2. Ingress Not Working

```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress rules
kubectl describe ingress paracle-ingress -n paracle-prod

# Test backend
kubectl port-forward svc/paracle-api 8000:8000 -n paracle-prod
curl http://localhost:8000/health
```

#### 3. DNS Issues

```bash
# Check DNS
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup paracle-api.paracle-prod.svc.cluster.local

# Check CoreDNS
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns
```

---

## Diagnostic Tools

### Essential Commands

```bash
# Pod logs (last 100 lines)
kubectl logs <pod-name> --tail=100 -n paracle-prod

# Pod logs (follow)
kubectl logs -f <pod-name> -n paracle-prod

# Pod logs (previous container)
kubectl logs <pod-name> --previous -n paracle-prod

# Exec into pod
kubectl exec -it <pod-name> -n paracle-prod -- /bin/bash

# Port forward
kubectl port-forward <pod-name> 8000:8000 -n paracle-prod

# Describe resource
kubectl describe pod <pod-name> -n paracle-prod

# Get resource YAML
kubectl get pod <pod-name> -o yaml -n paracle-prod

# Top (resource usage)
kubectl top pods -n paracle-prod
kubectl top nodes
```

### Debugging Container

```bash
# Run debug pod
kubectl run -it --rm debug --image=nicolaka/netshoot --restart=Never -- /bin/bash

# Inside debug pod:
# - curl, wget, ping, dig, nslookup
# - tcpdump, nmap
# - iperf3 (network testing)
```

---

## Escalation Path

**If issue persists after 30 minutes**:

1. **Gather diagnostic data**:

   ```bash
   # Save logs
   kubectl logs -l app=paracle-api --tail=500 > /tmp/paracle-logs.txt

   # Save pod status
   kubectl get pods -n paracle-prod -o yaml > /tmp/pods.yaml

   # Save events
   kubectl get events -n paracle-prod > /tmp/events.txt
   ```

2. **Open incident**:
   - Create ticket in PagerDuty
   - Post in #incidents Slack channel
   - Email <support@ibiface.com> with logs

3. **Contact on-call engineer**:
   - See [incident-response.md](incident-response.md) for on-call schedule

---

## Related Documentation

- [incident-response.md](incident-response.md) - Incident procedures
- [monitoring-setup.md](monitoring-setup.md) - Monitoring stack
- [production-deployment.md](production-deployment.md) - Deployment guide
- [disaster-recovery.md](disaster-recovery.md) - DR procedures
