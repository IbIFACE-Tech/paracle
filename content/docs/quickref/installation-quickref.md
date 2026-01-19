# Installation Quick Reference

> **Copy-paste installation commands for common scenarios**

---

## Common Scenarios

### CLI User (Local Development)

```bash
pip install paracle
```

✅ CLI commands
❌ API server

---

### API Server User

```bash
pip install 'paracle[api]'
paracle serve
```

✅ CLI commands
✅ API server
✅ REST endpoints

**Access**: `http://localhost:8000/docs`

---

### Python Developer

```bash
pip install 'paracle[providers]'
```

```python
from paracle_domain.models import Agent, AgentSpec

agent = Agent(spec=AgentSpec(
    name="assistant",
    provider="openai",
    model="gpt-4"
))
```

---

### Production (Docker)

```bash
docker-compose up -d
```

✅ All services
✅ PostgreSQL
✅ Redis
✅ API server

---

### Full Installation

```bash
pip install 'paracle[all]'
```

✅ Everything enabled

---

## Provider-Specific

```bash
# OpenAI only
pip install paracle openai

# Anthropic only
pip install paracle anthropic

# Ollama (local)
pip install paracle
# (No extra dependencies needed)

# All commercial providers
pip install 'paracle[providers]'

# All cloud providers
pip install 'paracle[cloud]'
```

---

## Feature-Specific

```bash
# Database support
pip install 'paracle[store]'

# Redis events
pip install 'paracle[events]'

# Docker sandbox
pip install 'paracle[sandbox]'

# LangChain integration
pip install 'paracle[langchain]'

# AI generation engine
pip install 'paracle[meta]'
```

---

## Upgrade

```bash
pip install --upgrade paracle
pip install --upgrade 'paracle[all]'
```

---

## Verify

```bash
paracle --version
paracle hello
pip show paracle
```

---

## Troubleshooting

### Error: "uvicorn is not installed"

```bash
pip install 'paracle[api]'
```

### Error: "docker is not installed"

```bash
# 1. Install Docker Desktop
# 2. Then:
pip install 'paracle[sandbox]'
```

### Error: "ModuleNotFoundError: No module named 'anthropic'"

```bash
pip install anthropic
# OR
pip install 'paracle[providers]'
```

---

## Platform Commands

### Windows PowerShell

```powershell
pip install 'paracle[all]'
```

### Windows CMD

```cmd
pip install paracle[all]
```

### macOS/Linux

```bash
pip install 'paracle[all]'
```

---

## Related

- [Full Installation Guide](../installation.md)
- [API Keys Setup](../api-keys.md)
- [Getting Started](../getting-started.md)
