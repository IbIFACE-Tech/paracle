# Incident Response Playbook

**Last Updated**: 2026-01-18
**Version**: 1.0
**24/7 On-Call**: +1-xxx-xxx-xxxx (PagerDuty)

---

## Overview

Comprehensive incident response procedures for Paracle production environment.

**Incident Severity Levels**:

- **P0 (Critical)**: Complete service outage, data loss
- **P1 (High)**: Major functionality impaired, <99% availability
- **P2 (Medium)**: Minor functionality impaired, degraded performance
- **P3 (Low)**: Cosmetic issues, no user impact

---

## Incident Classification

### P0 - Critical (Response Time: 15 minutes)

**Examples**:

- Complete API outage (all pods down)
- Database unavailable or corrupted
- Data loss or unauthorized access
- Security breach detected
- Payment system failure

**Response**:

- Page on-call engineer immediately
- Engage incident commander
- Notify stakeholders (CTO, customers if needed)
- All hands on deck

**SLA**:

- Response: 15 minutes
- Resolution: 4 hours
- Communication: Every 30 minutes

---

### P1 - High (Response Time: 30 minutes)

**Examples**:

- High error rate (>5%)
- Single AZ failure
- Primary database failover
- Significant performance degradation (p95 >2s)
- LLM provider outage

**Response**:

- Page on-call engineer
- Notify incident commander
- Update status page

**SLA**:

- Response: 30 minutes
- Resolution: 24 hours
- Communication: Every 2 hours

---

### P2 - Medium (Response Time: 2 hours)

**Examples**:

- Single pod crashes repeatedly
- Minor performance degradation
- Non-critical feature failure
- High resource usage (>80% CPU)

**Response**:

- Create ticket
- Assign to on-call engineer
- Monitor for escalation

**SLA**:

- Response: 2 hours
- Resolution: 72 hours
- Communication: Daily

---

### P3 - Low (Response Time: 24 hours)

**Examples**:

- UI bugs
- Documentation errors
- Non-urgent feature requests
- Minor logging issues

**Response**:

- Create ticket
- Assign to appropriate team
- Schedule for next sprint

**SLA**:

- Response: 24 hours
- Resolution: 2 weeks
- Communication: Weekly

---

## Escalation Matrix

```
┌─────────────────────────────────────────────────────────┐
│                   P0 CRITICAL                           │
│  ┌───────────┐  ┌───────────┐  ┌──────────────────┐   │
│  │ On-Call   │→ │ Incident  │→ │ Engineering Lead │   │
│  │ Engineer  │  │ Commander │  │      (CTO)       │   │
│  └───────────┘  └───────────┘  └──────────────────┘   │
│       ↓                ↓                  ↓            │
│  ┌─────────────────────────────────────────────────┐  │
│  │          Stakeholder Communication              │  │
│  │  - Customers (if external impact)               │  │
│  │  - Management                                   │  │
│  │  - Legal (if security breach)                   │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    P1 HIGH                              │
│  ┌───────────┐  ┌───────────┐                          │
│  │ On-Call   │→ │ Incident  │                          │
│  │ Engineer  │  │ Commander │                          │
│  └───────────┘  └───────────┘                          │
│       ↓                                                 │
│  ┌────────────────────────────┐                        │
│  │   Status Page Update       │                        │
│  └────────────────────────────┘                        │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  P2 MEDIUM                              │
│  ┌───────────┐                                          │
│  │ On-Call   │                                          │
│  │ Engineer  │                                          │
│  └───────────┘                                          │
│       ↓                                                 │
│  ┌────────────────────────────┐                        │
│  │   Ticket + Monitor         │                        │
│  └────────────────────────────┘                        │
└─────────────────────────────────────────────────────────┘
```

---

## Incident Response Workflow

### Phase 1: Detection (0-5 minutes)

**Sources**:

- AlertManager → PagerDuty
- User reports
- Monitoring dashboards
- Health check failures

**Actions**:

1. Acknowledge alert in PagerDuty
2. Check monitoring dashboards
3. Verify incident severity
4. Open incident channel (#incident-YYYYMMDD-NNN)

```bash
# Quick health check
kubectl get pods -n paracle-prod
curl -i https://api.paracle.com/health
kubectl logs -l app=paracle-api --tail=100

# Check metrics
curl http://prometheus:9090/api/v1/query?query=up{job="paracle-api"}
```

---

### Phase 2: Triage (5-15 minutes)

**Objectives**:

- Understand impact
- Identify root cause
- Determine severity
- Decide on response

**Triage Checklist**:

```yaml
impact_assessment:
  - users_affected: "All / Partial / None"
  - services_down: ["api", "database", "redis"]
  - data_at_risk: "Yes / No"
  - estimated_downtime: "< 1h / 1-4h / > 4h"

root_cause_analysis:
  - recent_deployments: "Check last 24h"
  - infrastructure_changes: "AWS, K8s, DNS"
  - external_dependencies: "OpenAI, Anthropic, payment gateway"
  - database_status: "Primary, replicas, connections"
  - resource_usage: "CPU, memory, disk, network"

response_decision:
  - immediate_action: "Rollback / Failover / Scale"
  - stakeholder_notification: "Yes / No"
  - incident_commander_needed: "Yes / No"
```

---

### Phase 3: Mitigation (15 minutes - 4 hours)

**Common Mitigations**:

#### API Pods Crashing

```bash
# Check pod status
kubectl get pods -n paracle-prod -l app=paracle-api

# Check recent logs
kubectl logs -l app=paracle-api --tail=200

# Check events
kubectl describe pod <pod-name> -n paracle-prod

# Check resource limits
kubectl top pods -n paracle-prod

# MITIGATION 1: Rollback deployment
kubectl rollout undo deployment/paracle-api -n paracle-prod

# MITIGATION 2: Scale up
kubectl scale deployment/paracle-api --replicas=10 -n paracle-prod

# MITIGATION 3: Restart pods
kubectl rollout restart deployment/paracle-api -n paracle-prod
```

#### Database Connection Exhaustion

```bash
# Check active connections
kubectl exec -it postgres-0 -- psql -U paracle -c "SELECT count(*) FROM pg_stat_activity;"

# Kill idle connections
kubectl exec -it postgres-0 -- psql -U paracle -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND state_change < now() - interval '10 minutes';"

# MITIGATION 1: Increase connection pool
kubectl set env deployment/paracle-api DB_POOL_SIZE=50 -n paracle-prod

# MITIGATION 2: Deploy PgBouncer
kubectl apply -f k8s/pgbouncer.yaml

# MITIGATION 3: Scale read replicas
kubectl scale statefulset postgres-replica --replicas=3 -n paracle-prod
```

#### High LLM API Latency

```bash
# Check LLM provider status
curl https://status.openai.com/api/v2/status.json
curl https://status.anthropic.com/api/v2/status.json

# MITIGATION 1: Switch to backup provider
kubectl set env deployment/paracle-api DEFAULT_LLM_PROVIDER=anthropic -n paracle-prod

# MITIGATION 2: Enable request queuing
kubectl set env deployment/paracle-api LLM_QUEUE_ENABLED=true -n paracle-prod

# MITIGATION 3: Increase timeout
kubectl set env deployment/paracle-api LLM_TIMEOUT=120 -n paracle-prod
```

#### Redis Out of Memory

```bash
# Check Redis memory
kubectl exec -it redis-0 -- redis-cli INFO memory

# MITIGATION 1: Clear non-critical keys
kubectl exec -it redis-0 -- redis-cli --scan --pattern "cache:*" | xargs redis-cli DEL

# MITIGATION 2: Increase memory limit
kubectl set resources statefulset redis --limits=memory=8Gi -n paracle-prod

# MITIGATION 3: Enable eviction policy
kubectl exec -it redis-0 -- redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

---

### Phase 4: Communication

#### Internal Communication (Slack)

```markdown
# #incident-20260118-001

🚨 **INCIDENT P0**: API Outage
**Status**: Investigating
**Impact**: All users unable to access API
**Started**: 2026-01-18 14:30 UTC
**Incident Commander**: @alice

**Timeline**:

- 14:30 UTC: Alert triggered (API pods CrashLoopBackOff)
- 14:32 UTC: Incident opened, on-call paged
- 14:35 UTC: Root cause identified (database connection pool exhausted)
- 14:40 UTC: Mitigation deployed (increased pool size)
- 14:45 UTC: Service recovering, monitoring

**Next Update**: 15:00 UTC
```

#### External Communication (Status Page)

```markdown
# Status Page Update

**Investigating** - We are investigating an issue with API availability. Our engineers are actively working to resolve the issue.
Posted: 2026-01-18 14:35 UTC

**Identified** - We have identified the root cause as database connection exhaustion and are deploying a fix.
Posted: 2026-01-18 14:40 UTC

**Monitoring** - The fix has been deployed and service is recovering. We are monitoring to ensure stability.
Posted: 2026-01-18 14:45 UTC

**Resolved** - The issue has been fully resolved. API is operating normally.
Posted: 2026-01-18 15:00 UTC
```

---

### Phase 5: Resolution

**Resolution Checklist**:

```yaml
verification:
  - all_pods_healthy: true
  - error_rate_normal: "< 0.1%"
  - latency_acceptable: "p95 < 500ms"
  - monitoring_green: true
  - user_reports_cleared: true

documentation:
  - incident_ticket_updated: true
  - timeline_documented: true
  - root_cause_identified: true
  - mitigation_steps_logged: true

handoff:
  - postmortem_scheduled: "Within 48h"
  - action_items_created: true
  - on_call_notified: true
```

---

## Postmortem Template

```markdown
# Incident Postmortem: [Title]

**Date**: 2026-01-18
**Duration**: 30 minutes (14:30 - 15:00 UTC)
**Severity**: P0 - Critical
**Incident Commander**: Alice
**Contributors**: Bob, Carol

---

## Executive Summary

Brief description of what happened, impact, and resolution.

---

## Timeline

| Time (UTC) | Event                                               |
| ---------- | --------------------------------------------------- |
| 14:30      | Alert triggered: API pods CrashLoopBackOff          |
| 14:32      | Incident opened, on-call paged                      |
| 14:35      | Root cause identified: DB connection pool exhausted |
| 14:40      | Mitigation deployed: Increased pool size to 50      |
| 14:45      | Service recovering, pods stable                     |
| 15:00      | Incident resolved, monitoring resumed               |

---

## Impact

- **Users Affected**: 100% of users
- **Downtime**: 30 minutes
- **Revenue Impact**: $XXX (estimated)
- **Data Loss**: None

---

## Root Cause

The database connection pool was exhausted due to:

1. Traffic spike (3x normal load)
2. Connection pool size too low (default 20)
3. Slow queries holding connections longer

---

## Resolution

**Immediate**:

- Increased connection pool size from 20 to 50
- Killed idle connections
- Scaled API pods from 3 to 5

**Longer-term**:

- Deploy PgBouncer for connection pooling
- Implement query timeout (30s)
- Add connection pool metrics to Grafana

---

## Action Items

| Action                     | Owner | Deadline   | Status        |
| -------------------------- | ----- | ---------- | ------------- |
| Deploy PgBouncer           | Bob   | 2026-01-20 | ⏳ In Progress |
| Add connection pool alerts | Carol | 2026-01-19 | ✅ Done        |
| Document runbook           | Alice | 2026-01-21 | ⏳ In Progress |
| Load test with 5x traffic  | Bob   | 2026-01-25 | ⏳ Planned     |

---

## Lessons Learned

**What Went Well**:

- ✅ Fast detection (2 minutes)
- ✅ Clear root cause identification
- ✅ Effective mitigation

**What Went Wrong**:

- ❌ Connection pool size not monitored
- ❌ No load testing before deployment
- ❌ No automatic scaling of pool size

**What We'll Improve**:

- Add connection pool metrics
- Implement automated load testing
- Create runbook for connection exhaustion
```

---

## Runbooks

### Runbook: API Pods CrashLoopBackOff

```bash
# 1. Check pod status
kubectl get pods -n paracle-prod -l app=paracle-api

# 2. Check logs
kubectl logs -l app=paracle-api --tail=100

# 3. Check recent events
kubectl get events --sort-by='.lastTimestamp' -n paracle-prod | head -20

# 4. Common causes:
# - OOM killed → Increase memory limit
# - Database connection failure → Check DB status
# - Config error → Check ConfigMap/Secret
# - Image pull error → Check registry

# 5. Mitigation:
# If OOM:
kubectl set resources deployment/paracle-api --limits=memory=4Gi

# If DB connection:
kubectl exec -it postgres-0 -- psql -c "SELECT 1"

# If config error:
kubectl get configmap paracle-config -o yaml
kubectl get secret paracle-secret -o yaml

# 6. Rollback if needed:
kubectl rollout undo deployment/paracle-api
```

### Runbook: High Error Rate

```bash
# 1. Check error rate
curl "http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~'5..'}[5m])"

# 2. Check recent logs for errors
kubectl logs -l app=paracle-api --since=10m | grep ERROR

# 3. Check external dependencies
curl https://status.openai.com/api/v2/status.json
curl https://api.paracle.com/health

# 4. Common causes:
# - LLM provider outage → Switch provider
# - Database slow queries → Check pg_stat_statements
# - Redis unavailable → Check Redis status
# - Rate limit exceeded → Increase rate limit

# 5. Mitigation:
# Switch LLM provider:
kubectl set env deployment/paracle-api DEFAULT_LLM_PROVIDER=anthropic

# Scale up:
kubectl scale deployment/paracle-api --replicas=10
```

---

## Contact Information

### On-Call Rotation

| Week       | Primary | Secondary | Escalation  |
| ---------- | ------- | --------- | ----------- |
| 2026-01-13 | Alice   | Bob       | Carol (CTO) |
| 2026-01-20 | Bob     | Carol     | Alice       |
| 2026-01-27 | Carol   | Alice     | Bob         |

### External Contacts

| Service         | Contact            | Phone                 | Status Page                    |
| --------------- | ------------------ | --------------------- | ------------------------------ |
| **AWS Support** | Enterprise         | +1-xxx-xxx-xxxx       | https://health.aws.amazon.com/ |
| **OpenAI**      | Enterprise Support | support@openai.com    | https://status.openai.com/     |
| **Anthropic**   | Enterprise Support | support@anthropic.com | https://status.anthropic.com/  |
| **PagerDuty**   | Support            | support@pagerduty.com | https://status.pagerduty.com/  |

---

## Tools & Access

### Required Access

- PagerDuty on-call schedule
- Kubernetes cluster (kubectl context)
- Grafana dashboards
- Prometheus queries
- AWS Console (production account)
- Slack (#incidents, #engineering)
- Status page admin

### Quick Links

- **Grafana**: https://grafana.paracle.com/
- **Prometheus**: https://prometheus.paracle.com/
- **Status Page**: https://status.paracle.com/
- **PagerDuty**: https://paracle.pagerduty.com/
- **Incident Docs**: https://docs.paracle.com/incidents/

---

## Related Documentation

- [disaster-recovery.md](disaster-recovery.md) - DR procedures
- [backup-restore.md](backup-restore.md) - Backup/restore
- [troubleshooting.md](troubleshooting.md) - Common issues
- [monitoring-setup.md](monitoring-setup.md) - Monitoring stack
