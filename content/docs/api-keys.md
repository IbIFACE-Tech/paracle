# API Keys and Secrets Management Guide

**Last Updated**: 2026-01-17
**Version**: 1.0
**Target Audience**: Developers, DevOps Engineers

---

## Overview

This guide explains how to securely configure API keys for 12+ LLM providers supported by Paracle.

**Security First**: Never commit API keys to version control. Always use environment variables or secrets management systems.

---

## Quick Start

### 1. Development Setup (Local)

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
nano .env
```

**`.env` file format**:

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
CLAUDE_API_KEY=sk-ant-...

# Google AI
GEMINI_API_KEY=...
```

**✅ VERIFICATION**: `.env` is in `.gitignore` (DO NOT REMOVE)

---

## Supported Providers

### OpenAI

**Sign up**: https://platform.openai.com/signup
**Get API key**: https://platform.openai.com/api-keys

```bash
OPENAI_API_KEY=sk-proj-...
```

**Usage in Paracle**:

```python
from paracle_cli.providers import OpenAIProvider

provider = OpenAIProvider()  # Auto-loads from env
```

---

### Anthropic (Claude)

**Sign up**: https://console.anthropic.com/
**Get API key**: https://console.anthropic.com/settings/keys

```bash
CLAUDE_API_KEY=sk-ant-api03-...
```

**Usage**:

```python
from paracle_cli.providers import AnthropicProvider

provider = AnthropicProvider()
```

---

### Google AI (Gemini)

**Sign up**: https://makersuite.google.com/
**Get API key**: https://makersuite.google.com/app/apikey

```bash
GEMINI_API_KEY=AIzaSy...
```

---

### Azure OpenAI

**Setup**: https://portal.azure.com/

```bash
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2023-12-01-preview
```

---

### AWS Bedrock

**Setup**: https://console.aws.amazon.com/bedrock/

```bash
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1
```

---

### Other Providers

| Provider         | Environment Variable | Sign-up URL                    |
| ---------------- | -------------------- | ------------------------------ |
| **xAI (Grok)**   | `XAI_API_KEY`        | https://x.ai/                  |
| **DeepSeek**     | `DEEPSEEK_API_KEY`   | https://platform.deepseek.com/ |
| **Groq**         | `GROQ_API_KEY`       | https://console.groq.com/      |
| **Mistral AI**   | `MISTRAL_API_KEY`    | https://console.mistral.ai/    |
| **Cohere**       | `COHERE_API_KEY`     | https://dashboard.cohere.com/  |
| **Together AI**  | `TOGETHER_API_KEY`   | https://api.together.xyz/      |
| **Perplexity**   | `PERPLEXITY_API_KEY` | https://www.perplexity.ai/     |
| **OpenRouter**   | `OPENROUTER_API_KEY` | https://openrouter.ai/         |
| **Fireworks AI** | `FIREWORKS_API_KEY`  | https://fireworks.ai/          |

---

## Production Deployment

### Option 1: Azure Key Vault (Recommended for Azure)

```bash
# Install Azure SDK
pip install paracle[azure]

# Configure Key Vault
az keyvault create --name paracle-keys --resource-group paracle-prod

# Store secrets
az keyvault secret set --vault-name paracle-keys --name OPENAI-API-KEY --value "sk-..."

# Grant access to application
az keyvault set-policy --name paracle-keys --object-id <app-id> --secret-permissions get list
```

**Python code**:

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://paracle-keys.vault.azure.net/", credential=credential)

openai_key = client.get_secret("OPENAI-API-KEY").value
```

---

### Option 2: AWS Secrets Manager

```bash
# Install AWS SDK
pip install paracle[aws]

# Create secret
aws secretsmanager create-secret \
  --name paracle/api-keys \
  --secret-string '{"OPENAI_API_KEY":"sk-..."}'

# Grant IAM permissions
aws secretsmanager get-secret-value --secret-id paracle/api-keys
```

**Python code**:

```python
import boto3
import json

client = boto3.client('secretsmanager', region_name='us-east-1')
response = client.get_secret_value(SecretId='paracle/api-keys')
secrets = json.loads(response['SecretString'])

openai_key = secrets['OPENAI_API_KEY']
```

---

### Option 3: HashiCorp Vault

```bash
# Install Vault
brew install vault  # macOS
apt-get install vault  # Ubuntu

# Start Vault server (dev mode)
vault server -dev

# Store secret
vault kv put secret/paracle OPENAI_API_KEY=sk-...

# Read secret
vault kv get secret/paracle
```

**Python code**:

```python
import hvac

client = hvac.Client(url='http://127.0.0.1:8200', token='dev-token')
secret = client.secrets.kv.v2.read_secret_version(path='paracle')

openai_key = secret['data']['data']['OPENAI_API_KEY']
```

---

## Docker Deployment

### Using Docker Secrets (Swarm)

```bash
# Create secret
echo "sk-..." | docker secret create openai_api_key -

# Deploy stack
docker stack deploy -c docker-compose.yml paracle
```

**docker-compose.yml**:

```yaml
version: "3.8"
services:
  paracle-api:
    image: ibiface/paracle-api:latest
    secrets:
      - openai_api_key
    environment:
      OPENAI_API_KEY_FILE: /run/secrets/openai_api_key

secrets:
  openai_api_key:
    external: true
```

---

### Using Docker Environment Variables

```bash
# Create .env file (DO NOT COMMIT)
cat > .env <<EOF
OPENAI_API_KEY=sk-...
CLAUDE_API_KEY=sk-ant-...
EOF

# Run container
docker run --env-file .env ibiface/paracle-api:latest
```

---

## Kubernetes Deployment

### Using Kubernetes Secrets

```bash
# Create secret
kubectl create secret generic paracle-api-keys \
  --from-literal=OPENAI_API_KEY=sk-... \
  --from-literal=CLAUDE_API_KEY=sk-ant-...

# Verify
kubectl get secret paracle-api-keys -o yaml
```

**Deployment YAML**:

```yaml
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
          image: ibiface/paracle-api:latest
          envFrom:
            - secretRef:
                name: paracle-api-keys
```

---

## CI/CD Secrets

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Test
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: pytest
```

**Add secret**: Settings → Secrets → Actions → New repository secret

---

### GitLab CI/CD

```yaml
# .gitlab-ci.yml
test:
  script:
    - pytest
  variables:
    OPENAI_API_KEY: $OPENAI_API_KEY
```

**Add secret**: Settings → CI/CD → Variables → Add variable

---

## Security Best Practices

### ✅ DO

- ✅ Use `.env` files locally (ensure `.gitignore` includes `.env`)
- ✅ Use secrets management systems in production (Key Vault, Secrets Manager, Vault)
- ✅ Rotate API keys every 30-90 days
- ✅ Use separate keys for dev/staging/prod
- ✅ Monitor API key usage for anomalies
- ✅ Revoke compromised keys immediately
- ✅ Use least-privilege IAM policies
- ✅ Enable audit logging for secrets access

### ❌ DON'T

- ❌ Never commit API keys to git
- ❌ Never share API keys in chat/email
- ❌ Never log API keys (even debug logs)
- ❌ Never hardcode API keys in source code
- ❌ Never use production keys in development
- ❌ Never store keys in container images
- ❌ Never expose keys in URLs or query parameters

---

## Key Rotation Procedure

### Step 1: Generate New Key

1. Log in to provider dashboard
2. Create new API key
3. Copy key to secure location

### Step 2: Update Secrets

**Development**:

```bash
# Update .env
nano .env
# Replace old key with new key
```

**Production**:

```bash
# Azure Key Vault
az keyvault secret set --vault-name paracle-keys --name OPENAI-API-KEY --value "new-key"

# AWS Secrets Manager
aws secretsmanager update-secret --secret-id paracle/api-keys --secret-string '{"OPENAI_API_KEY":"new-key"}'

# Kubernetes
kubectl create secret generic paracle-api-keys --from-literal=OPENAI_API_KEY=new-key --dry-run=client -o yaml | kubectl apply -f -
```

### Step 3: Restart Services

```bash
# Kubernetes
kubectl rollout restart deployment/paracle-api

# Docker Swarm
docker service update --force paracle_api

# Systemd
sudo systemctl restart paracle-api
```

### Step 4: Verify

```bash
# Test API with new key
curl -X POST http://localhost:8000/api/v1/agents/test \
  -H "Authorization: Bearer $NEW_KEY" \
  -d '{"message": "test"}'
```

### Step 5: Revoke Old Key

1. Return to provider dashboard
2. Delete/revoke old API key
3. Monitor for any failed requests

---

## Troubleshooting

### Error: `OPENAI_API_KEY not found`

**Solution**:

```bash
# Check environment variable is set
echo $OPENAI_API_KEY

# If empty, load from .env
export $(cat .env | xargs)

# Verify
python -c "import os; print(os.getenv('OPENAI_API_KEY'))"
```

---

### Error: `Invalid API key`

**Solution**:

1. Verify key is correct (no extra spaces/newlines)
2. Check key hasn't been revoked
3. Verify key has correct permissions
4. Test key directly with provider API

---

### Error: `Rate limit exceeded`

**Solution**:

1. Check provider dashboard for usage limits
2. Implement rate limiting in Paracle config
3. Upgrade to higher tier plan
4. Use multiple keys with load balancing

---

## Monitoring & Alerts

### Track API Key Usage

```python
from paracle_observability import track_api_call

@track_api_call(provider="openai")
async def generate_response(prompt: str):
    # Track usage, latency, errors
    pass
```

### Set Up Alerts

**Prometheus alerting rule**:

```yaml
groups:
  - name: api_keys
    rules:
      - alert: HighAPIUsage
        expr: rate(api_calls_total[5m]) > 100
        annotations:
          summary: "High API usage detected"
```

---

## Support

- **Documentation**: https://docs.paracles.com/
- **Security Issues**: security@ibiface.com
- **General Support**: dev@ibiface.com

---

## Related Guides

- [Production Deployment Guide](deployment/production-deployment.md)
- [Secrets Management in Production](deployment/secrets-management.md)
- [Security Best Practices](../SECURITY.md)
