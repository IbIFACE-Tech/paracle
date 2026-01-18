# Secrets Management Guide

**Last Updated**: 2026-01-17
**Version**: 1.0

---

## Overview

Comprehensive guide for managing secrets (API keys, passwords, certificates) in Paracle deployments.

**Key Principles**:

- ❌ Never commit secrets to git
- ✅ Use secrets managers (Azure Key Vault, AWS Secrets Manager, HashiCorp Vault)
- ✅ Rotate secrets every 30-90 days
- ✅ Separate credentials per environment (dev/staging/prod)
- ✅ Enable audit logging for all secret access

---

## Secrets Inventory

### Production Secrets Required

| Secret                | Purpose        | Rotation | Priority |
| --------------------- | -------------- | -------- | -------- |
| **OPENAI_API_KEY**    | LLM provider   | 90 days  | P0       |
| **CLAUDE_API_KEY**    | LLM provider   | 90 days  | P0       |
| **GEMINI_API_KEY**    | LLM provider   | 90 days  | P1       |
| **DATABASE_PASSWORD** | PostgreSQL     | 90 days  | P0       |
| **REDIS_PASSWORD**    | Redis cache    | 90 days  | P0       |
| **SECRET_KEY**        | JWT signing    | 180 days | P0       |
| **TLS_CERTIFICATE**   | HTTPS          | 365 days | P0       |
| **AWS_ACCESS_KEY**    | S3 storage     | 90 days  | P1       |
| **SENTRY_DSN**        | Error tracking | N/A      | P2       |
| **SLACK_WEBHOOK**     | Notifications  | N/A      | P3       |

---

## Option 1: Azure Key Vault (Recommended for Azure)

### Setup

```bash
# Create Key Vault
az keyvault create \
  --name paracle-prod-keys \
  --resource-group paracle-prod \
  --location eastus \
  --enable-rbac-authorization

# Grant access to application
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee <app-managed-identity-id> \
  --scope /subscriptions/<sub-id>/resourceGroups/paracle-prod/providers/Microsoft.KeyVault/vaults/paracle-prod-keys
```

### Store Secrets

```bash
# Store API keys
az keyvault secret set \
  --vault-name paracle-prod-keys \
  --name OPENAI-API-KEY \
  --value "sk-proj-..."

az keyvault secret set \
  --vault-name paracle-prod-keys \
  --name CLAUDE-API-KEY \
  --value "sk-ant-..."

# Store database password
az keyvault secret set \
  --vault-name paracle-prod-keys \
  --name DATABASE-PASSWORD \
  --value "$(openssl rand -base64 32)"
```

### Retrieve Secrets (Python)

```python
# packages/paracle_core/secrets.py
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class AzureSecretsManager:
    def __init__(self, vault_url: str):
        credential = DefaultAzureCredential()
        self.client = SecretClient(vault_url=vault_url, credential=credential)
        self._cache = {}

    def get_secret(self, name: str) -> str:
        """Get secret with caching"""
        if name not in self._cache:
            secret = self.client.get_secret(name)
            self._cache[name] = secret.value
        return self._cache[name]

# Usage
secrets = AzureSecretsManager("https://paracle-prod-keys.vault.azure.net/")
openai_key = secrets.get_secret("OPENAI-API-KEY")
```

### Kubernetes Integration

```yaml
# k8s/secretsprovider.yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: paracle-secrets
spec:
  provider: azure
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "true"
    userAssignedIdentityID: "<managed-identity-client-id>"
    keyvaultName: "paracle-prod-keys"
    objects: |
      array:
        - |
          objectName: OPENAI-API-KEY
          objectType: secret
          objectVersion: ""
        - |
          objectName: CLAUDE-API-KEY
          objectType: secret
        - |
          objectName: DATABASE-PASSWORD
          objectType: secret
    tenantId: "<tenant-id>"

---
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      volumes:
        - name: secrets-store
          csi:
            driver: secrets-store.csi.k8s.io
            readOnly: true
            volumeAttributes:
              secretProviderClass: "paracle-secrets"

      containers:
        - name: api
          volumeMounts:
            - name: secrets-store
              mountPath: "/mnt/secrets"
              readOnly: true
          env:
            - name: OPENAI_API_KEY
              valueFrom:
                secretKeyRef:
                  name: paracle-secrets
                  key: OPENAI-API-KEY
```

---

## Option 2: AWS Secrets Manager

### Setup

```bash
# Create secret
aws secretsmanager create-secret \
  --name paracle/prod/api-keys \
  --description "LLM provider API keys" \
  --secret-string '{
    "OPENAI_API_KEY": "sk-proj-...",
    "CLAUDE_API_KEY": "sk-ant-...",
    "GEMINI_API_KEY": "AIzaSy..."
  }'

# Create database credentials
aws secretsmanager create-secret \
  --name paracle/prod/database \
  --secret-string '{
    "username": "paracle",
    "password": "generated-password",
    "host": "paracle-db.aws.com",
    "port": "5432",
    "database": "paracle"
  }'
```

### Retrieve Secrets (Python)

```python
import boto3
import json

class AWSSecretsManager:
    def __init__(self, region: str = "us-east-1"):
        self.client = boto3.client('secretsmanager', region_name=region)
        self._cache = {}

    def get_secret(self, secret_id: str) -> dict:
        """Get secret JSON"""
        if secret_id not in self._cache:
            response = self.client.get_secret_value(SecretId=secret_id)
            self._cache[secret_id] = json.loads(response['SecretString'])
        return self._cache[secret_id]

# Usage
secrets = AWSSecretsManager()
api_keys = secrets.get_secret("paracle/prod/api-keys")
openai_key = api_keys['OPENAI_API_KEY']
```

### IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"],
      "Resource": ["arn:aws:secretsmanager:us-east-1:123456789012:secret:paracle/prod/*"]
    }
  ]
}
```

### Kubernetes Integration (External Secrets Operator)

```yaml
# Install operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets --create-namespace

# Configure SecretStore
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: paracle-sa

---
# ExternalSecret
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: paracle-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets
    kind: SecretStore
  target:
    name: paracle-secrets
    creationPolicy: Owner
  data:
  - secretKey: OPENAI_API_KEY
    remoteRef:
      key: paracle/prod/api-keys
      property: OPENAI_API_KEY
```

---

## Option 3: HashiCorp Vault

### Setup

```bash
# Start Vault server
vault server -config=/etc/vault/config.hcl

# Initialize and unseal
vault operator init -key-shares=5 -key-threshold=3
vault operator unseal <key1>
vault operator unseal <key2>
vault operator unseal <key3>

# Login
vault login <root-token>

# Enable KV secrets engine
vault secrets enable -path=secret kv-v2

# Store secrets
vault kv put secret/paracle/prod \
  OPENAI_API_KEY=sk-proj-... \
  CLAUDE_API_KEY=sk-ant-... \
  DATABASE_PASSWORD=generated-password
```

### Retrieve Secrets (Python)

```python
import hvac

class VaultSecretsManager:
    def __init__(self, url: str, token: str):
        self.client = hvac.Client(url=url, token=token)
        self._cache = {}

    def get_secret(self, path: str, key: str) -> str:
        """Get secret value"""
        cache_key = f"{path}:{key}"
        if cache_key not in self._cache:
            secret = self.client.secrets.kv.v2.read_secret_version(path=path)
            self._cache[cache_key] = secret['data']['data'][key]
        return self._cache[cache_key]

# Usage
secrets = VaultSecretsManager("https://vault.paracle.com", token=token)
openai_key = secrets.get_secret("paracle/prod", "OPENAI_API_KEY")
```

### Kubernetes Integration (Vault Agent Injector)

```yaml
# Enable Vault Kubernetes auth
vault auth enable kubernetes
vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"

# Create policy
vault policy write paracle-policy - <<EOF
path "secret/data/paracle/prod" {
  capabilities = ["read"]
}
EOF

# Create Kubernetes role
vault write auth/kubernetes/role/paracle \
  bound_service_account_names=paracle-sa \
  bound_service_account_namespaces=paracle-prod \
  policies=paracle-policy \
  ttl=24h

# Deployment with annotations
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    metadata:
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "paracle"
        vault.hashicorp.com/agent-inject-secret-api-keys: "secret/data/paracle/prod"
        vault.hashicorp.com/agent-inject-template-api-keys: |
          {{ with secret "secret/data/paracle/prod" -}}
          export OPENAI_API_KEY="{{ .Data.data.OPENAI_API_KEY }}"
          export CLAUDE_API_KEY="{{ .Data.data.CLAUDE_API_KEY }}"
          {{- end }}
```

---

## Secret Rotation

### Automated Rotation (Example: AWS)

```python
# scripts/rotate_secrets.py
import boto3
import anthropic
import openai

def rotate_api_key(provider: str):
    """Rotate LLM provider API key"""
    if provider == "openai":
        # Generate new OpenAI key (manual - visit dashboard)
        print("Visit https://platform.openai.com/api-keys to generate new key")
        new_key = input("Enter new OpenAI API key: ")

        # Test new key
        client = openai.OpenAI(api_key=new_key)
        client.models.list()  # Test call

    elif provider == "anthropic":
        print("Visit https://console.anthropic.com/settings/keys for new key")
        new_key = input("Enter new Anthropic API key: ")

        # Test new key
        client = anthropic.Anthropic(api_key=new_key)
        client.messages.create(model="claude-3-sonnet", max_tokens=10, messages=[])

    # Update secret
    sm = boto3.client('secretsmanager')
    secret = sm.get_secret_value(SecretId='paracle/prod/api-keys')
    keys = json.loads(secret['SecretString'])

    # Store old key for rollback
    keys[f'{provider.upper()}_API_KEY_OLD'] = keys[f'{provider.upper()}_API_KEY']
    keys[f'{provider.upper()}_API_KEY'] = new_key

    sm.update_secret(
        SecretId='paracle/prod/api-keys',
        SecretString=json.dumps(keys)
    )

    print(f"✅ {provider} API key rotated successfully")

# Run
if __name__ == "__main__":
    rotate_api_key("openai")
```

### Rotation Schedule

```bash
# Cron job (weekly check)
0 2 * * 1 /opt/paracle/scripts/check_secret_age.py

# check_secret_age.py
import boto3
from datetime import datetime, timedelta

sm = boto3.client('secretsmanager')
secrets = sm.list_secrets()

for secret in secrets['SecretList']:
    if secret['Name'].startswith('paracle/'):
        created = secret.get('LastChangedDate', secret['CreatedDate'])
        age_days = (datetime.now(tz=created.tzinfo) - created).days

        if age_days > 90:
            print(f"⚠️  SECRET EXPIRED: {secret['Name']} ({age_days} days old)")
            # Send alert
```

---

## Audit Logging

### Enable Audit Logs (Azure)

```bash
# Enable Key Vault diagnostic settings
az monitor diagnostic-settings create \
  --name paracle-audit \
  --resource /subscriptions/<sub-id>/resourceGroups/paracle-prod/providers/Microsoft.KeyVault/vaults/paracle-prod-keys \
  --logs '[{"category": "AuditEvent", "enabled": true}]' \
  --workspace /subscriptions/<sub-id>/resourcegroups/paracle-prod/providers/microsoft.operationalinsights/workspaces/paracle-logs
```

### Query Audit Logs

```kusto
// Azure Log Analytics
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.KEYVAULT"
| where OperationName == "SecretGet"
| project TimeGenerated, CallerIPAddress, identity_claim_http_schemas_microsoft_com_identity_claims_objectidentifier_g, ResultSignature, Resource
| order by TimeGenerated desc
```

---

## Security Best Practices

### ✅ DO

- ✅ Use managed identities/IAM roles (no hardcoded credentials)
- ✅ Enable MFA for secrets manager access
- ✅ Rotate secrets every 30-90 days
- ✅ Use separate secrets per environment
- ✅ Enable audit logging
- ✅ Implement least-privilege access
- ✅ Encrypt secrets at rest and in transit
- ✅ Test secret rotation in staging first

### ❌ DON'T

- ❌ Never commit secrets to git
- ❌ Never log secret values (even debug logs)
- ❌ Never share secrets via email/chat
- ❌ Never use production secrets in dev/test
- ❌ Never store secrets in container images
- ❌ Never use default passwords
- ❌ Never skip audit logging

---

## Emergency Procedures

### Compromised Secret

```bash
# 1. Immediately revoke old key at provider
# OpenAI: https://platform.openai.com/api-keys
# Anthropic: https://console.anthropic.com/settings/keys

# 2. Generate new key

# 3. Update secret
az keyvault secret set \
  --vault-name paracle-prod-keys \
  --name OPENAI-API-KEY \
  --value "<new-key>"

# 4. Restart applications (Kubernetes will auto-reload)
kubectl rollout restart deployment/paracle-api -n paracle-prod

# 5. Monitor for errors
kubectl logs -f -l app=paracle-api -n paracle-prod

# 6. Document incident
echo "[$(date)] INCIDENT: OPENAI_API_KEY compromised and rotated" >> /var/log/security-incidents.log
```

---

## Testing

### Verify Secret Access

```python
# scripts/test_secrets.py
from paracle_core.secrets import get_secrets_manager

def test_secrets():
    sm = get_secrets_manager()

    required_secrets = [
        "OPENAI-API-KEY",
        "CLAUDE-API-KEY",
        "DATABASE-PASSWORD",
        "REDIS-PASSWORD",
        "SECRET-KEY"
    ]

    for secret_name in required_secrets:
        try:
            value = sm.get_secret(secret_name)
            print(f"✅ {secret_name}: OK (length: {len(value)})")
        except Exception as e:
            print(f"❌ {secret_name}: FAILED - {e}")
            return False

    return True

if __name__ == "__main__":
    success = test_secrets()
    exit(0 if success else 1)
```

---

## Related Documentation

- [api-keys.md](../api-keys.md) - API key setup guide
- [environment-configuration.md](environment-configuration.md) - Environment variables
- [production-deployment.md](production-deployment.md) - Deployment procedures
