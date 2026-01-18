# Backup and Restore Procedures

**Last Updated**: 2026-01-18
**Version**: 1.0
**RPO Target**: ≤ 1 hour
**RTO Target**: ≤ 4 hours

---

## Overview

Detailed step-by-step procedures for backing up and restoring Paracle production data.

**Critical Data**:

- PostgreSQL database (agents, workflows, executions, audit logs)
- Redis cache (optional - session data, ephemeral state)
- Configuration files (.parac/, environment variables)
- TLS certificates
- Application logs (last 30 days)

---

## PostgreSQL Backup

### Automated Daily Backup

```bash
#!/bin/bash
# /opt/paracle/scripts/backup-postgres.sh

set -e

BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="paracle_backup_${TIMESTAMP}.sql.gz"
S3_BUCKET="s3://paracle-backups/postgres"
RETENTION_DAYS=30

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Dump database
echo "Starting PostgreSQL backup..."
PGPASSWORD=${DB_PASSWORD} pg_dump \
  -h ${DB_HOST} \
  -p ${DB_PORT} \
  -U ${DB_USER} \
  -d paracle \
  --format=custom \
  --verbose \
  --no-owner \
  --no-acl \
  | gzip > ${BACKUP_DIR}/${BACKUP_FILE}

# Verify backup
if [ $? -eq 0 ]; then
    SIZE=$(du -h ${BACKUP_DIR}/${BACKUP_FILE} | cut -f1)
    echo "✅ Backup created: ${BACKUP_FILE} (${SIZE})"
else
    echo "❌ Backup failed!"
    exit 1
fi

# Upload to S3
echo "Uploading to S3..."
aws s3 cp ${BACKUP_DIR}/${BACKUP_FILE} ${S3_BUCKET}/${BACKUP_FILE}

# Verify upload
aws s3 ls ${S3_BUCKET}/${BACKUP_FILE}
if [ $? -eq 0 ]; then
    echo "✅ Uploaded to S3"
else
    echo "❌ S3 upload failed!"
    exit 1
fi

# Clean up local backups older than 7 days
find ${BACKUP_DIR} -name "*.sql.gz" -mtime +7 -delete

# Clean up S3 backups older than retention period
aws s3 ls ${S3_BUCKET}/ | while read -r line; do
    DATE=$(echo $line | awk '{print $1" "$2}')
    FILE=$(echo $line | awk '{print $4}')
    FILE_DATE=$(date -d "$DATE" +%s)
    CUTOFF_DATE=$(date -d "-${RETENTION_DAYS} days" +%s)

    if [ $FILE_DATE -lt $CUTOFF_DATE ]; then
        echo "Deleting old backup: $FILE"
        aws s3 rm ${S3_BUCKET}/${FILE}
    fi
done

echo "✅ Backup complete!"
```

### Schedule with Cron

```bash
# Install cron job
crontab -e

# Daily backup at 2 AM
0 2 * * * /opt/paracle/scripts/backup-postgres.sh >> /var/log/paracle-backup.log 2>&1

# Weekly verification test (every Sunday at 3 AM)
0 3 * * 0 /opt/paracle/scripts/test-restore.sh >> /var/log/paracle-restore-test.log 2>&1
```

### Kubernetes CronJob

```yaml
# k8s/backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: paracle-prod
spec:
  schedule: "0 2 * * *" # Daily at 2 AM
  successfulJobsHistoryLimit: 7
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: backup
              image: postgres:16
              env:
                - name: PGHOST
                  value: postgres-primary
                - name: PGPORT
                  value: "5432"
                - name: PGUSER
                  value: paracle
                - name: PGPASSWORD
                  valueFrom:
                    secretKeyRef:
                      name: postgres-secret
                      key: password
                - name: AWS_ACCESS_KEY_ID
                  valueFrom:
                    secretKeyRef:
                      name: aws-credentials
                      key: access-key-id
                - name: AWS_SECRET_ACCESS_KEY
                  valueFrom:
                    secretKeyRef:
                      name: aws-credentials
                      key: secret-access-key
              command:
                - /bin/bash
                - -c
                - |
                  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
                  BACKUP_FILE="paracle_backup_${TIMESTAMP}.sql.gz"

                  # Dump database
                  pg_dump -d paracle --format=custom | gzip > /tmp/${BACKUP_FILE}

                  # Upload to S3
                  apt-get update && apt-get install -y awscli
                  aws s3 cp /tmp/${BACKUP_FILE} s3://paracle-backups/postgres/${BACKUP_FILE}

                  echo "✅ Backup complete: ${BACKUP_FILE}"
```

---

## WAL Archiving (Continuous Backup)

### Enable WAL Archiving

```bash
# PostgreSQL configuration (postgresql.conf)
wal_level = replica
archive_mode = on
archive_command = 'aws s3 cp %p s3://paracle-backups/wal/%f'
archive_timeout = 300  # Archive every 5 minutes
max_wal_senders = 3
```

### Restore with WAL (Point-in-Time Recovery)

```bash
#!/bin/bash
# /opt/paracle/scripts/restore-pitr.sh

TARGET_TIME="2026-01-18 14:30:00 UTC"
BACKUP_FILE="paracle_backup_20260118_020000.sql.gz"

# 1. Stop database
systemctl stop postgresql

# 2. Backup current data (just in case)
mv /var/lib/postgresql/16/main /var/lib/postgresql/16/main.old

# 3. Initialize new data directory
sudo -u postgres /usr/lib/postgresql/16/bin/initdb -D /var/lib/postgresql/16/main

# 4. Download base backup
aws s3 cp s3://paracle-backups/postgres/${BACKUP_FILE} /tmp/
gunzip < /tmp/${BACKUP_FILE} | sudo -u postgres pg_restore -d postgres

# 5. Create recovery configuration
cat > /var/lib/postgresql/16/main/recovery.conf <<EOF
restore_command = 'aws s3 cp s3://paracle-backups/wal/%f %p'
recovery_target_time = '${TARGET_TIME}'
recovery_target_action = 'promote'
EOF

# 6. Start database in recovery mode
systemctl start postgresql

# 7. Monitor recovery
tail -f /var/log/postgresql/postgresql-16-main.log

# 8. Verify recovery
sudo -u postgres psql -d paracle -c "SELECT now(), pg_last_xact_replay_timestamp();"
```

---

## Redis Backup

### RDB Snapshot

```bash
# /opt/paracle/scripts/backup-redis.sh
#!/bin/bash

BACKUP_DIR="/backups/redis"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="redis_${TIMESTAMP}.rdb"

# Trigger save
redis-cli BGSAVE

# Wait for save to complete
while [ $(redis-cli LASTSAVE) -eq $(redis-cli LASTSAVE) ]; do
    sleep 1
done

# Copy RDB file
cp /var/lib/redis/dump.rdb ${BACKUP_DIR}/${BACKUP_FILE}

# Compress
gzip ${BACKUP_DIR}/${BACKUP_FILE}

# Upload to S3
aws s3 cp ${BACKUP_DIR}/${BACKUP_FILE}.gz s3://paracle-backups/redis/${BACKUP_FILE}.gz

echo "✅ Redis backup complete: ${BACKUP_FILE}.gz"
```

### AOF Backup

```bash
# Redis configuration (redis.conf)
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec

# Backup AOF
cp /var/lib/redis/appendonly.aof /backups/redis/appendonly_$(date +%Y%m%d).aof
gzip /backups/redis/appendonly_*.aof
aws s3 cp /backups/redis/appendonly_*.aof.gz s3://paracle-backups/redis/
```

---

## Configuration Backup

### Backup .parac/ Directory

```bash
#!/bin/bash
# /opt/paracle/scripts/backup-config.sh

BACKUP_DIR="/backups/config"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PARAC_DIR="/opt/paracle/.parac"

# Create tarball
tar -czf ${BACKUP_DIR}/parac_${TIMESTAMP}.tar.gz -C /opt/paracle .parac

# Upload to S3
aws s3 cp ${BACKUP_DIR}/parac_${TIMESTAMP}.tar.gz s3://paracle-backups/config/

echo "✅ Config backup complete"
```

### Backup Environment Variables

```bash
# Backup secrets from Key Vault (Azure)
az keyvault secret list --vault-name paracle-prod-keys --query "[].name" -o tsv | while read secret; do
    az keyvault secret show --vault-name paracle-prod-keys --name $secret > /backups/secrets/${secret}.json
done

# Encrypt backup
tar -czf /backups/secrets_$(date +%Y%m%d).tar.gz /backups/secrets
openssl enc -aes-256-cbc -salt -in /backups/secrets_*.tar.gz -out /backups/secrets_*.tar.gz.enc -k ${ENCRYPTION_KEY}

# Upload
aws s3 cp /backups/secrets_*.tar.gz.enc s3://paracle-backups/secrets/
```

---

## Restore Procedures

### Full Database Restore

```bash
#!/bin/bash
# /opt/paracle/scripts/restore-postgres.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

echo "⚠️  WARNING: This will OVERWRITE the current database!"
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# 1. Download backup
echo "Downloading backup from S3..."
aws s3 cp s3://paracle-backups/postgres/${BACKUP_FILE} /tmp/${BACKUP_FILE}

# 2. Stop application
echo "Stopping Paracle API..."
kubectl scale deployment paracle-api --replicas=0 -n paracle-prod

# 3. Disconnect all clients
echo "Terminating database connections..."
PGPASSWORD=${DB_PASSWORD} psql -h ${DB_HOST} -U ${DB_USER} -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'paracle' AND pid <> pg_backend_pid();"

# 4. Drop and recreate database
echo "Dropping database..."
PGPASSWORD=${DB_PASSWORD} psql -h ${DB_HOST} -U ${DB_USER} -d postgres -c "DROP DATABASE IF EXISTS paracle;"
PGPASSWORD=${DB_PASSWORD} psql -h ${DB_HOST} -U ${DB_USER} -d postgres -c "CREATE DATABASE paracle OWNER paracle;"

# 5. Restore backup
echo "Restoring backup..."
gunzip < /tmp/${BACKUP_FILE} | PGPASSWORD=${DB_PASSWORD} pg_restore \
  -h ${DB_HOST} \
  -U ${DB_USER} \
  -d paracle \
  --verbose \
  --no-owner \
  --no-acl

# 6. Verify restore
echo "Verifying restore..."
ROW_COUNT=$(PGPASSWORD=${DB_PASSWORD} psql -h ${DB_HOST} -U ${DB_USER} -d paracle -t -c "SELECT COUNT(*) FROM agents;")
echo "Agents table: ${ROW_COUNT} rows"

# 7. Restart application
echo "Starting Paracle API..."
kubectl scale deployment paracle-api --replicas=3 -n paracle-prod

# 8. Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=paracle-api -n paracle-prod --timeout=300s

# 9. Health check
curl -f https://api.paracle.com/health || echo "❌ Health check failed!"

echo "✅ Restore complete!"
```

### Restore Redis

```bash
#!/bin/bash
# /opt/paracle/scripts/restore-redis.sh

BACKUP_FILE=$1

# 1. Stop Redis
systemctl stop redis

# 2. Download backup
aws s3 cp s3://paracle-backups/redis/${BACKUP_FILE} /tmp/${BACKUP_FILE}
gunzip /tmp/${BACKUP_FILE}

# 3. Replace RDB file
cp /tmp/${BACKUP_FILE%.gz} /var/lib/redis/dump.rdb
chown redis:redis /var/lib/redis/dump.rdb

# 4. Start Redis
systemctl start redis

# 5. Verify
redis-cli PING
redis-cli DBSIZE

echo "✅ Redis restore complete"
```

### Restore Configuration

```bash
#!/bin/bash
# /opt/paracle/scripts/restore-config.sh

BACKUP_FILE=$1

# 1. Download config backup
aws s3 cp s3://paracle-backups/config/${BACKUP_FILE} /tmp/

# 2. Backup current config
mv /opt/paracle/.parac /opt/paracle/.parac.backup_$(date +%Y%m%d_%H%M%S)

# 3. Extract backup
tar -xzf /tmp/${BACKUP_FILE} -C /opt/paracle/

# 4. Verify
ls -la /opt/paracle/.parac/

echo "✅ Config restore complete"
```

---

## Backup Verification

### Automated Restore Test

```bash
#!/bin/bash
# /opt/paracle/scripts/test-restore.sh

BACKUP_FILE=$(aws s3 ls s3://paracle-backups/postgres/ | sort | tail -n 1 | awk '{print $4}')
TEST_DB="paracle_restore_test"

echo "Testing restore of: ${BACKUP_FILE}"

# 1. Download backup
aws s3 cp s3://paracle-backups/postgres/${BACKUP_FILE} /tmp/

# 2. Create test database
PGPASSWORD=${DB_PASSWORD} psql -h ${DB_HOST} -U ${DB_USER} -d postgres -c "DROP DATABASE IF EXISTS ${TEST_DB};"
PGPASSWORD=${DB_PASSWORD} psql -h ${DB_HOST} -U ${DB_USER} -d postgres -c "CREATE DATABASE ${TEST_DB};"

# 3. Restore to test database
gunzip < /tmp/${BACKUP_FILE} | PGPASSWORD=${DB_PASSWORD} pg_restore \
  -h ${DB_HOST} \
  -U ${DB_USER} \
  -d ${TEST_DB} \
  --no-owner \
  --no-acl

# 4. Verify data
echo "Checking table counts..."
PGPASSWORD=${DB_PASSWORD} psql -h ${DB_HOST} -U ${DB_USER} -d ${TEST_DB} <<EOF
SELECT 'agents' AS table_name, COUNT(*) FROM agents
UNION ALL
SELECT 'workflows', COUNT(*) FROM workflows
UNION ALL
SELECT 'executions', COUNT(*) FROM executions;
EOF

# 5. Check data integrity
echo "Checking foreign key constraints..."
PGPASSWORD=${DB_PASSWORD} psql -h ${DB_HOST} -U ${DB_USER} -d ${TEST_DB} -c \
  "SELECT conname FROM pg_constraint WHERE contype = 'f';"

# 6. Clean up
PGPASSWORD=${DB_PASSWORD} psql -h ${DB_HOST} -U ${DB_USER} -d postgres -c "DROP DATABASE ${TEST_DB};"

echo "✅ Restore test complete!"
```

### Backup Validation Checklist

```yaml
# .parac/policies/backup-validation.yaml
backup_validation:
  daily_checks:
    - backup_file_exists: true
    - backup_size_minimum: 10MB
    - backup_uploaded_to_s3: true
    - local_backup_cleaned: true

  weekly_checks:
    - restore_test_passed: true
    - table_row_counts_match: true
    - foreign_keys_valid: true
    - indexes_intact: true

  monthly_checks:
    - full_restore_drill: true
    - rto_target_met: "<4 hours"
    - rpo_verified: "<1 hour"
    - documentation_updated: true
```

---

## Disaster Recovery Scenarios

### Scenario 1: Accidental Data Deletion

```bash
# User accidentally deleted agents table data at 14:30
# Last backup: 02:00 (same day)
# Need to restore to 14:29

# Use PITR (Point-in-Time Recovery)
./restore-pitr.sh "2026-01-18 14:29:00 UTC"

# Verify data
psql -d paracle -c "SELECT COUNT(*) FROM agents;"
psql -d paracle -c "SELECT * FROM agents WHERE updated_at > '2026-01-18 14:00:00';"
```

### Scenario 2: Database Corruption

```bash
# Database corruption detected
# Restore from last good backup

# 1. Identify last good backup
aws s3 ls s3://paracle-backups/postgres/ | grep "20260117"

# 2. Restore from backup
./restore-postgres.sh paracle_backup_20260117_020000.sql.gz

# 3. Replay WAL logs to current time
# (automatic with PITR configuration)

# 4. Verify
psql -d paracle -c "\dt+"
```

### Scenario 3: Complete Data Loss

```bash
# Server failure, all local data lost
# Restore from S3 backups

# 1. Provision new server
# 2. Install PostgreSQL + Redis
# 3. Restore database
./restore-postgres.sh paracle_backup_20260118_020000.sql.gz

# 4. Restore Redis
./restore-redis.sh redis_20260118_020000.rdb.gz

# 5. Restore configuration
./restore-config.sh parac_20260118_020000.tar.gz

# 6. Restore environment variables (manual from Key Vault)
az keyvault secret list --vault-name paracle-prod-keys

# 7. Deploy application
kubectl apply -f k8s/
```

---

## Backup Monitoring

### Prometheus Alerts

```yaml
# alerts/backup-alerts.yaml
groups:
  - name: backup_alerts
    rules:
      - alert: BackupFailed
        expr: paracle_backup_success == 0
        for: 1h
        labels:
          severity: critical
        annotations:
          summary: "Backup failed for {{ $labels.backup_type }}"

      - alert: BackupOld
        expr: (time() - paracle_backup_timestamp) > 86400
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Last backup is > 24 hours old"

      - alert: RestoreTestFailed
        expr: paracle_restore_test_success == 0
        for: 1h
        labels:
          severity: critical
        annotations:
          summary: "Weekly restore test failed"
```

### Backup Metrics

```python
# packages/paracle_observability/backup_metrics.py
from prometheus_client import Gauge, Counter

backup_timestamp = Gauge('paracle_backup_timestamp', 'Last backup timestamp', ['type'])
backup_size_bytes = Gauge('paracle_backup_size_bytes', 'Backup size in bytes', ['type'])
backup_duration_seconds = Gauge('paracle_backup_duration_seconds', 'Backup duration', ['type'])
backup_success = Gauge('paracle_backup_success', 'Backup success (1=success, 0=failure)', ['type'])
restore_test_success = Gauge('paracle_restore_test_success', 'Restore test success')

# Track backup
backup_timestamp.labels(type='postgres').set(time.time())
backup_size_bytes.labels(type='postgres').set(backup_file_size)
backup_duration_seconds.labels(type='postgres').set(duration)
backup_success.labels(type='postgres').set(1)
```

---

## Best Practices

### ✅ DO

- ✅ Test restores weekly (automated)
- ✅ Store backups in multiple regions
- ✅ Encrypt backups at rest
- ✅ Monitor backup success/failures
- ✅ Document restore procedures
- ✅ Verify backup integrity
- ✅ Keep 30-day retention minimum
- ✅ Automate backup rotation

### ❌ DON'T

- ❌ Never skip backup verification
- ❌ Never store backups only locally
- ❌ Never ignore backup failures
- ❌ Never assume backups work without testing
- ❌ Never delete backups manually
- ❌ Never restore to production without testing
- ❌ Never skip WAL archiving

---

## Related Documentation

- [disaster-recovery.md](disaster-recovery.md) - DR plan overview
- [monitoring-setup.md](monitoring-setup.md) - Backup monitoring
- [production-deployment.md](production-deployment.md) - Initial setup
