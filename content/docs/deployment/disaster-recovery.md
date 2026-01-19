# Disaster Recovery Plan

**Last Updated**: 2026-01-17
**Version**: 1.0
**Status**: Active
**Review Cycle**: Quarterly

---

## Executive Summary

This Disaster Recovery (DR) plan ensures Paracle services can be restored with minimal downtime in the event of system failures, data loss, or catastrophic events.

**Recovery Objectives**:

- **RPO (Recovery Point Objective)**: ≤ 1 hour
- **RTO (Recovery Time Objective)**: ≤ 4 hours

---

## Scope

### In Scope

- PostgreSQL database (primary data store)
- Redis cache (session/state data)
- Application configuration (`.parac/`, environment variables)
- Docker images and Kubernetes manifests
- TLS certificates and secrets
- Monitoring dashboards and alert configurations

### Out of Scope

- Third-party services (LLM providers, cloud infrastructure)
- User workstations and development environments
- Source code (covered by Git/GitHub)

---

## Recovery Objectives

| Component           | RPO      | RTO     | Priority          |
| ------------------- | -------- | ------- | ----------------- |
| PostgreSQL Database | 15 min   | 2 hours | **P0 - Critical** |
| Redis Cache         | 1 hour   | 30 min  | **P1 - High**     |
| API Service         | N/A      | 30 min  | **P0 - Critical** |
| Monitoring          | N/A      | 1 hour  | **P2 - Medium**   |
| Documentation       | 24 hours | 2 hours | **P3 - Low**      |

---

## Backup Strategy

### Database Backups

#### Automated Backups (PostgreSQL)

```bash
# Daily full backup + continuous WAL archiving
# Location: S3/Azure Blob Storage
# Retention: 30 days

# Backup script (runs daily at 02:00 UTC)
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="paracle_db_${TIMESTAMP}.sql.gz"
S3_BUCKET="s3://paracle-backups/database/"

# Full backup
pg_dump -h $DB_HOST -U $DB_USER -d paracle | gzip > /tmp/$BACKUP_FILE

# Upload to S3
aws s3 cp /tmp/$BACKUP_FILE ${S3_BUCKET}

# Verify upload
aws s3 ls ${S3_BUCKET}${BACKUP_FILE}

# Cleanup local file
rm /tmp/$BACKUP_FILE

# Log success
echo "[$(date)] Database backup completed: $BACKUP_FILE" >> /var/log/paracle-backups.log
```

**Kubernetes CronJob**:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
spec:
  schedule: "0 2 * * *" # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: backup
              image: postgres:16
              env:
                - name: PGPASSWORD
                  valueFrom:
                    secretKeyRef:
                      name: paracle-secrets
                      key: postgres-password
              command:
                - /bin/sh
                - -c
                - |
                  pg_dump -h postgres -U postgres paracle | gzip > /backup/paracle_$(date +%Y%m%d_%H%M%S).sql.gz
                  aws s3 sync /backup/ s3://paracle-backups/database/
              volumeMounts:
                - name: backup-storage
                  mountPath: /backup
          restartPolicy: OnFailure
          volumes:
            - name: backup-storage
              emptyDir: {}
```

#### WAL (Write-Ahead Log) Archiving

```bash
# postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'aws s3 cp %p s3://paracle-backups/wal/%f'
archive_timeout = 300  # 5 minutes

# Enables point-in-time recovery (PITR)
```

#### Backup Verification

```bash
# Weekly backup restoration test (Sundays at 03:00)
#!/bin/bash

# Download latest backup
LATEST_BACKUP=$(aws s3 ls s3://paracle-backups/database/ | sort | tail -n 1 | awk '{print $4}')
aws s3 cp s3://paracle-backups/database/$LATEST_BACKUP /tmp/

# Restore to test database
gunzip < /tmp/$LATEST_BACKUP | psql -h test-db -U postgres -d paracle_test

# Verify row count
PROD_COUNT=$(psql -h prod-db -U postgres -d paracle -t -c "SELECT COUNT(*) FROM agents")
TEST_COUNT=$(psql -h test-db -U postgres -d paracle_test -t -c "SELECT COUNT(*) FROM agents")

if [ "$PROD_COUNT" -eq "$TEST_COUNT" ]; then
  echo "✅ Backup verification PASSED"
  exit 0
else
  echo "❌ Backup verification FAILED: Row count mismatch"
  # Send alert
  exit 1
fi
```

---

### Redis Backups

```bash
# Redis persistence (RDB snapshots + AOF)
# redis.conf
save 900 1       # Save after 900 sec if 1 key changed
save 300 10      # Save after 300 sec if 10 keys changed
save 60 10000    # Save after 60 sec if 10000 keys changed

appendonly yes   # Enable AOF
appendfsync everysec  # Sync every second

# Backup script
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
redis-cli BGSAVE
sleep 10
aws s3 cp /var/lib/redis/dump.rdb s3://paracle-backups/redis/dump_${TIMESTAMP}.rdb
```

---

### Configuration Backups

```bash
# Backup .parac/ workspace (hourly)
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
tar -czf /tmp/parac_${TIMESTAMP}.tar.gz .parac/
aws s3 cp /tmp/parac_${TIMESTAMP}.tar.gz s3://paracle-backups/config/
rm /tmp/parac_${TIMESTAMP}.tar.gz
```

---

## Recovery Procedures

### Scenario 1: Complete Database Loss

**Estimated Recovery Time**: 2 hours

#### Step 1: Identify Latest Backup

```bash
# List available backups
aws s3 ls s3://paracle-backups/database/ --recursive | sort

# Identify latest full backup + WAL files needed
LATEST_BACKUP=$(aws s3 ls s3://paracle-backups/database/ | sort | tail -n 1 | awk '{print $4}')
echo "Latest backup: $LATEST_BACKUP"
```

#### Step 2: Provision New Database

```bash
# Kubernetes
kubectl apply -f k8s/postgres.yaml

# Wait for ready
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s

# Verify connectivity
kubectl exec -it postgres-0 -- psql -U postgres -c "SELECT version()"
```

#### Step 3: Restore Base Backup

```bash
# Download backup
aws s3 cp s3://paracle-backups/database/$LATEST_BACKUP /tmp/

# Stop application
kubectl scale deployment paracle-api --replicas=0

# Restore backup
gunzip < /tmp/$LATEST_BACKUP | kubectl exec -i postgres-0 -- psql -U postgres -d paracle

# Verify restoration
kubectl exec -it postgres-0 -- psql -U postgres -d paracle -c "SELECT COUNT(*) FROM agents"
```

#### Step 4: Apply WAL Files (Point-in-Time Recovery)

```bash
# Create recovery.conf
cat > recovery.conf <<EOF
restore_command = 'aws s3 cp s3://paracle-backups/wal/%f %p'
recovery_target_time = '$(date -u +"%Y-%m-%d %H:%M:%S")'
EOF

# Copy to PostgreSQL data directory
kubectl cp recovery.conf postgres-0:/var/lib/postgresql/data/

# Restart PostgreSQL
kubectl delete pod postgres-0
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s
```

#### Step 5: Verify and Resume

```bash
# Verify data integrity
kubectl exec -it postgres-0 -- psql -U postgres -d paracle <<EOF
SELECT COUNT(*) FROM agents;
SELECT COUNT(*) FROM workflows;
SELECT COUNT(*) FROM agent_executions;
EOF

# Scale up application
kubectl scale deployment paracle-api --replicas=3

# Monitor logs
kubectl logs -f -l app=paracle-api

# Health check
curl https://api.paracle.com/health
```

**Total Time**: ~2 hours (30 min provisioning + 1 hour restore + 30 min verification)

---

### Scenario 2: Region Failure (Multi-Region Failover)

**Estimated Recovery Time**: 1 hour

#### Prerequisites

- Multi-region deployment (primary: us-east-1, secondary: us-west-2)
- Database replication (PostgreSQL streaming replication)
- Global load balancer (Route 53, Cloudflare)

#### Step 1: Detect Region Failure

```bash
# Automated health check (every 60 seconds)
curl -f https://api-us-east-1.paracle.com/health || echo "Region us-east-1 DOWN"
```

#### Step 2: Promote Secondary Database

```bash
# Connect to secondary region
aws configure set region us-west-2

# Promote read replica to primary
aws rds promote-read-replica --db-instance-identifier paracle-secondary

# Wait for promotion (5-10 minutes)
aws rds wait db-instance-available --db-instance-identifier paracle-secondary
```

#### Step 3: Update DNS

```bash
# Route 53 failover (automated with health checks)
aws route53 change-resource-record-sets --hosted-zone-id Z1234567890ABC --change-batch '{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "api.paracle.com",
      "Type": "CNAME",
      "TTL": 60,
      "ResourceRecords": [{"Value": "api-us-west-2.paracle.com"}]
    }
  }]
}'

# Wait for DNS propagation (1-5 minutes)
```

#### Step 4: Verify Failover

```bash
# Test from multiple locations
curl https://api.paracle.com/health
dig api.paracle.com  # Should point to us-west-2

# Monitor application logs
kubectl logs -f -l app=paracle-api -n paracle-prod
```

**Total Time**: ~1 hour (10 min detection + 10 min promotion + 5 min DNS + 5 min verification + 30 min monitoring)

---

### Scenario 3: Data Corruption

**Estimated Recovery Time**: 3 hours

#### Step 1: Identify Corruption Point

```bash
# Check application logs for errors
kubectl logs -l app=paracle-api --since=24h | grep -i "error\|corruption"

# Identify last known good state
# Example: Corruption detected at 2026-01-17 14:30:00 UTC
RECOVERY_TARGET="2026-01-17 14:25:00"
```

#### Step 2: Point-in-Time Recovery

```bash
# Create new database instance
kubectl apply -f k8s/postgres-recovery.yaml

# Restore base backup + WAL files up to recovery target
# (See Scenario 1, Step 3-4 with recovery_target_time=$RECOVERY_TARGET)
```

#### Step 3: Data Validation

```bash
# Run data integrity checks
python scripts/validate_database.py --connection $RECOVERY_DB_URL

# Compare with production (before corruption)
python scripts/compare_databases.py --source $RECOVERY_DB_URL --target $PROD_DB_URL
```

#### Step 4: Cutover

```bash
# Schedule maintenance window
# Stop application
kubectl scale deployment paracle-api --replicas=0

# Swap databases
kubectl set env deployment/paracle-api DATABASE_URL=$RECOVERY_DB_URL

# Start application
kubectl scale deployment paracle-api --replicas=3

# Verify functionality
curl https://api.paracle.com/health
```

---

## Failover Procedures

### Automated Failover (Kubernetes)

```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  template:
    spec:
      containers:
        - name: api
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
            failureThreshold: 2
```

**Result**: Kubernetes automatically restarts unhealthy pods

---

## Testing Schedule

| Test Type              | Frequency | Last Tested | Next Test  |
| ---------------------- | --------- | ----------- | ---------- |
| **Backup Restoration** | Weekly    | 2026-01-15  | 2026-01-22 |
| **Failover Drill**     | Monthly   | 2026-01-10  | 2026-02-10 |
| **Full DR Simulation** | Quarterly | 2025-12-15  | 2026-03-15 |
| **Runbook Review**     | Quarterly | 2026-01-01  | 2026-04-01 |

---

## Contact Information

### On-Call Rotation

| Role                   | Primary                     | Secondary                 |
| ---------------------- | --------------------------- | ------------------------- |
| **Incident Commander** | John Doe (+1-555-0100)      | Jane Smith (+1-555-0101)  |
| **Database Admin**     | Bob Wilson (+1-555-0102)    | Alice Brown (+1-555-0103) |
| **DevOps Engineer**    | Charlie Davis (+1-555-0104) | Diana Evans (+1-555-0105) |

### Escalation Matrix

1. **Level 1** (0-15 min): On-call engineer investigates
2. **Level 2** (15-30 min): Escalate to incident commander
3. **Level 3** (30-60 min): Escalate to VP Engineering
4. **Level 4** (60+ min): Escalate to CTO

---

## Post-Incident Procedures

### Incident Report Template

```markdown
# Incident Report: [YYYY-MM-DD] - [Brief Description]

## Summary

- **Incident Start**: [Timestamp]
- **Incident End**: [Timestamp]
- **Duration**: [Hours]
- **Severity**: [P0/P1/P2/P3]
- **Impact**: [Description]

## Timeline

- [Timestamp]: [Event description]
- [Timestamp]: [Event description]

## Root Cause

[Detailed root cause analysis]

## Resolution

[Steps taken to resolve]

## Preventive Measures

1. [Action item 1]
2. [Action item 2]

## Lessons Learned

- [Lesson 1]
- [Lesson 2]
```

---

## Compliance

This DR plan satisfies:

- **SOC 2 Type II**: Business continuity requirements
- **ISO 27001**: A.17 (Business Continuity)
- **GDPR**: Art. 32 (Security of Processing)

---

## Related Documentation

- [production-deployment.md](production-deployment.md) - Deployment procedures
- [monitoring-setup.md](monitoring-setup.md) - Monitoring configuration
- [incident-response.md](incident-response.md) - Incident response procedures
