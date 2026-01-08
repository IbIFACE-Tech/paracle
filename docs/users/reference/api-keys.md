# API Key Management

This guide explains how to configure and manage API keys for LLM providers in Paracle.

## 🔑 Overview

Paracle supports 14+ LLM providers (12 commercial + self-hosted). Each commercial provider requires an API key that you must obtain and configure.

## 📋 Quick Start

### 1. Get API Keys

Visit provider websites to obtain your API keys:

| Provider       | Website                                     | Cost             |
| -------------- | ------------------------------------------- | ---------------- |
| **OpenAI**     | https://platform.openai.com/api-keys        | Pay-per-use      |
| **Anthropic**  | https://console.anthropic.com/settings/keys | Pay-per-use      |
| **Google**     | https://makersuite.google.com/app/apikey    | Free tier + paid |
| **xAI**        | https://console.x.ai/                       | Pay-per-use      |
| **DeepSeek**   | https://platform.deepseek.com/              | Very cheap       |
| **Groq**       | https://console.groq.com/keys               | Free tier + paid |
| **Mistral**    | https://console.mistral.ai/                 | Pay-per-use      |
| **Cohere**     | https://dashboard.cohere.com/api-keys       | Free tier + paid |
| **Together**   | https://api.together.xyz/settings/api-keys  | Pay-per-use      |
| **Perplexity** | https://www.perplexity.ai/settings/api      | Pay-per-use      |
| **OpenRouter** | https://openrouter.ai/keys                  | Aggregator       |
| **Fireworks**  | https://fireworks.ai/api-keys               | Pay-per-use      |

### 2. Configure Keys

**Option A: Environment Variables (Recommended)**

```bash
# Linux/Mac - Add to ~/.bashrc or ~/.zshrc
export OPENAI_API_KEY="sk-your-key-here"
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Windows PowerShell
$env:OPENAI_API_KEY = "sk-your-key-here"

# Windows CMD
set OPENAI_API_KEY=sk-your-key-here
```

**Option B: .env File (Development)**

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your keys:
   ```dotenv
   OPENAI_API_KEY=sk-your-actual-key
   ANTHROPIC_API_KEY=sk-ant-your-actual-key
   ```

3. Load in your Python code:
   ```bash
   pip install python-dotenv
   ```

   ```python
   from dotenv import load_dotenv
   load_dotenv()

   # Now API keys are available
   from paracle_domain.models import AgentSpec

   agent = AgentSpec(
       name="my-agent",
       provider="openai",  # Uses OPENAI_API_KEY
       model="gpt-4"
   )
   ```

### 3. Verify Configuration

```python
import os

# Check if keys are loaded
providers = {
    "OpenAI": "OPENAI_API_KEY",
    "Anthropic": "ANTHROPIC_API_KEY",
    "Google": "GOOGLE_API_KEY",
}

for provider, key_name in providers.items():
    if os.getenv(key_name):
        print(f"✅ {provider} API key is configured")
    else:
        print(f"❌ {provider} API key is missing")
```

## 📁 File Locations

### Project Structure

```
my-project/
├── .env              # ← API keys HERE (DO NOT COMMIT)
├── .env.example      # Template (safe to commit)
├── .gitignore        # Must include .env
├── .parac/           # Paracle workspace (no keys here!)
├── agents/
└── requirements.txt
```

**Important**:
- ✅ API keys go in **project root** `.env`
- ❌ NOT in `.parac/` directory
- ❌ NOT in source code files

## 🔒 Security Best Practices

### 1. Never Commit Keys to Git

Add to `.gitignore`:
```gitignore
# API keys and secrets
.env
.env.local
.env.*.local
*.key
secrets/
```

### 2. Use Different Keys Per Environment

```bash
# Development
.env.development
OPENAI_API_KEY=sk-dev-key

# Production
.env.production
OPENAI_API_KEY=sk-prod-key
```

### 3. Rotate Keys Regularly

- Monthly for production
- After team member leaves
- If key is compromised
- After major security updates

### 4. Set Usage Limits

Configure spending limits in provider dashboards:

- **OpenAI**: https://platform.openai.com/account/billing/limits
- **Anthropic**: https://console.anthropic.com/settings/limits
- **Google**: https://console.cloud.google.com/billing

### 5. Monitor Usage

Track API consumption:

```python
from paracle_providers import OpenAIProvider

provider = OpenAIProvider()

# After API calls, check usage
response = await provider.chat_completion(...)
print(f"Tokens used: {response.usage.total_tokens}")
```

### 6. Use Environment-Specific Permissions

Restrict API key permissions:
- ✅ Read-only for development
- ✅ Limited rate for staging
- ✅ Full access only for production

## 🐳 Docker / Production

### Docker Compose

```yaml
# docker-compose.yaml
services:
  paracle-api:
    image: paracle:latest
    environment:
      # Pass from host environment
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    env_file:
      - .env  # Or load from file
```

### Docker Secrets

```yaml
services:
  paracle-api:
    secrets:
      - openai_api_key
      - anthropic_api_key
    environment:
      OPENAI_API_KEY_FILE: /run/secrets/openai_api_key

secrets:
  openai_api_key:
    external: true
  anthropic_api_key:
    external: true
```

### Kubernetes

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: paracle-api-keys
type: Opaque
data:
  openai-api-key: <base64-encoded-key>
  anthropic-api-key: <base64-encoded-key>
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: paracle-api
spec:
  template:
    spec:
      containers:
      - name: api
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: paracle-api-keys
              key: openai-api-key
```

## 🛠️ Provider-Specific Configuration

### OpenAI

```python
from paracle_providers import OpenAIProvider

# Environment variable (recommended)
provider = OpenAIProvider()  # Uses OPENAI_API_KEY

# Explicit key (not recommended)
provider = OpenAIProvider(api_key="sk-...")

# Custom base URL (for proxy)
provider = OpenAIProvider(base_url="https://proxy.example.com/v1")

# Organization ID
provider = OpenAIProvider(organization="org-xyz123")
```

### Anthropic

```python
from paracle_providers import AnthropicProvider

# Uses ANTHROPIC_API_KEY
provider = AnthropicProvider()

# Custom settings
provider = AnthropicProvider(
    api_key="sk-ant-...",
    timeout=60.0
)
```

### Self-Hosted (No API Key)

```python
from paracle_providers import OllamaProvider

# Local Ollama - no API key needed
provider = OllamaProvider(base_url="http://localhost:11434")

# Available models
models = await provider.list_models()
```

## 🚨 Troubleshooting

### "API key not found"

**Solution**: Set environment variable or create `.env` file

```bash
# Check if loaded
python -c "import os; print(os.getenv('OPENAI_API_KEY'))"
```

### ".env file not loading"

**Solution**: Install and use python-dotenv

```bash
pip install python-dotenv
```

```python
from dotenv import load_dotenv
load_dotenv()  # Must call before importing Paracle
```

### "Invalid API key"

**Solution**: Verify key format and permissions

```python
# OpenAI keys start with "sk-"
# Anthropic keys start with "sk-ant-"
# Check in provider dashboard
```

### "Rate limit exceeded"

**Solution**: Configure rate limits or upgrade plan

```python
# Add retry logic
from paracle_providers.retry import RetryableProvider

provider = RetryableProvider(
    OpenAIProvider(),
    max_retries=3,
    backoff_factor=2.0
)
```

## 📊 Cost Management

### Track Costs

```python
from paracle_providers import OpenAIProvider

provider = OpenAIProvider()
response = await provider.chat_completion(...)

# Calculate cost (approximate)
prompt_cost = response.usage.prompt_tokens * 0.00001  # $0.01 per 1K
completion_cost = response.usage.completion_tokens * 0.00003  # $0.03 per 1K
total_cost = prompt_cost + completion_cost

print(f"Cost: ${total_cost:.4f}")
```

### Set Budgets

Configure in `.env`:
```dotenv
PARACLE_MONTHLY_BUDGET=100.00
PARACLE_ALERT_THRESHOLD=80.00
```

## 🔗 Related Documentation

- [Providers Guide](providers.md) - Complete provider documentation
- [Security Guide](security-audit-report.md) - Security best practices
- [Getting Started](getting-started.md) - Quick start guide

## 📞 Support

Having issues with API keys?

1. Check provider status pages
2. Verify key format and permissions
3. Review logs: `.parac/logs/paracle.log`
4. File issue: https://github.com/IbIFACE-Tech/paracle-lite/issues

---

**Remember**: Keep your API keys secret and never commit them to version control! 🔐
