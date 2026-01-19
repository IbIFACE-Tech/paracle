# Installation Guide

> **Complete guide to installing Paracle with the right dependencies for your use case**

---

## Quick Start

### Minimal Installation (CLI only)

```bash
pip install paracle
```

This installs:
- ✅ Core CLI commands (`paracle init`, `paracle agents`, etc.)
- ✅ Agent management and orchestration
- ✅ Workflow execution
- ✅ Basic tools and utilities
- ❌ API server (FastAPI/uvicorn)
- ❌ Advanced features (sandbox, vector storage, etc.)

**Use this if**: You only need the command-line interface.

---

### Full Installation (All features)

```bash
pip install 'paracle[all]'
```

This installs everything:
- ✅ API server (FastAPI + uvicorn)
- ✅ Database support (SQLAlchemy + PostgreSQL drivers)
- ✅ Event streaming (Redis)
- ✅ Sandbox execution (Docker SDK)
- ✅ LLM providers (OpenAI, Anthropic, Cohere)
- ✅ Cloud integrations (Azure, AWS, GCP)
- ✅ Framework adapters (LangChain, LlamaIndex, etc.)
- ✅ Observability (Prometheus, OpenTelemetry)

**Use this if**: You want all features enabled immediately.

---

## Installation by Use Case

### 1. CLI User (Local Development)

**Scenario**: You want to use Paracle from the command line to manage agents and workflows.

```bash
# Install core
pip install paracle

# Verify installation
paracle --version
paracle hello
```

**Commands available**:
- `paracle init` - Initialize workspace
- `paracle agents list/create/run` - Agent management
- `paracle workflow execute` - Run workflows
- `paracle tools list` - List available tools
- `paracle cost track` - Cost tracking

---

### 2. API Server User (REST API)

**Scenario**: You want to run the Paracle REST API server for programmatic access.

```bash
# Install with API support
pip install 'paracle[api]'

# Start the server
paracle serve

# Or with options
paracle serve --host 0.0.0.0 --port 8000 --workers 4
```

**What you get**:
- ✅ FastAPI server with OpenAPI docs
- ✅ JWT authentication
- ✅ Full CRUD operations (agents, workflows, tools)
- ✅ Health checks and metrics
- ✅ CORS and security middleware

**Access**:
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- OpenAPI: `http://localhost:8000/openapi.json`

---

### 3. Production Deployment (Docker)

**Scenario**: You want to deploy Paracle in production with all services.

```bash
# Clone the repository
git clone https://github.com/IbIFACE-Tech/paracle.git
cd paracle

# Start with Docker Compose
docker-compose up -d
```

**What you get**:
- ✅ API server (FastAPI)
- ✅ PostgreSQL database
- ✅ Redis cache
- ✅ All dependencies included
- ✅ Health checks and monitoring
- ✅ Production-ready configuration

**Services**:
- API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

---

### 4. Python Developer (Programmatic API)

**Scenario**: You want to use Paracle as a Python library in your application.

```bash
# Install with LLM providers
pip install 'paracle[providers]'

# Or with specific provider
pip install paracle anthropic  # Anthropic only
pip install paracle openai     # OpenAI only
```

**Example usage**:

```python
from paracle_domain.models import AgentSpec, Agent
from paracle_providers.anthropic import AnthropicProvider

# Create agent
agent_spec = AgentSpec(
    name="assistant",
    provider="anthropic",
    model="claude-3-5-sonnet-20241022",
    temperature=0.7
)

agent = Agent(spec=agent_spec)

# Execute task
result = await agent.execute({
    "task": "Write a Python function to calculate fibonacci numbers"
})

print(result)
```

---

### 5. Advanced User (Custom Setup)

**Scenario**: You want fine-grained control over dependencies.

```bash
# Core + specific features
pip install paracle

# Add API server
pip install 'paracle[api]'

# Add database support
pip install 'paracle[store]'

# Add specific providers
pip install anthropic openai

# Add framework adapter
pip install 'paracle[langchain]'
```

---

## Optional Dependencies Reference

### Core Features

| Extra | Installs | Use Case |
|-------|----------|----------|
| `[api]` | FastAPI, uvicorn | REST API server |
| `[store]` | SQLAlchemy, Alembic | Database persistence |
| `[events]` | Redis | Event streaming |
| `[sandbox]` | Docker SDK, psutil | Isolated execution |
| `[transport]` | asyncssh, websockets | Remote development |

### LLM Providers

| Extra | Installs | Providers |
|-------|----------|-----------|
| `[providers]` | openai, anthropic, cohere | Commercial providers |
| `[providers-extended]` | + google-genai, groq | Extended providers |
| `[azure]` | azure-identity | Azure OpenAI |
| `[aws]` | boto3 | AWS Bedrock |
| `[gcp]` | google-cloud-aiplatform | Vertex AI |
| `[cloud]` | All cloud providers | Enterprise clouds |

### Framework Adapters

| Extra | Installs | Framework |
|-------|----------|-----------|
| `[langchain]` | langchain, langgraph | LangChain |
| `[llamaindex]` | llama-index | LlamaIndex |
| `[crewai]` | crewai | CrewAI |
| `[autogen]` | autogen-agentchat | AutoGen |
| `[msaf]` | agent-framework | Microsoft Semantic Kernel |
| `[adapters]` | All adapters | All frameworks |

### Advanced Features

| Extra | Installs | Feature |
|-------|----------|---------|
| `[meta]` | SQLite backend | AI generation engine |
| `[meta-full]` | PostgreSQL + pgvector | Production AI engine |
| `[postgres]` | asyncpg, psycopg2, pgvector | PostgreSQL support |
| `[observability]` | prometheus-client, opentelemetry | Metrics & tracing |

### Development

| Extra | Installs | Purpose |
|-------|----------|---------|
| `[dev]` | pytest, black, ruff, mypy, etc. | Development tools |
| `[docs]` | mkdocs, mkdocs-material | Documentation |

### Combinations

| Extra | Equivalent To | Use Case |
|-------|--------------|----------|
| `[all]` | `[api,store,events,sandbox,providers,cloud,adapters,observability]` | Everything |

---

## Platform-Specific Notes

### Windows

```powershell
# PowerShell
pip install 'paracle[all]'

# Command Prompt (quotes not needed)
pip install paracle[all]
```

### macOS/Linux

```bash
# Bash/Zsh (quotes required)
pip install 'paracle[all]'
```

### Docker

```bash
# Use official image (includes all dependencies)
docker run -it ibiface/paracle:latest paracle --version

# Or build locally
docker build -t paracle .
docker run -it paracle paracle --version
```

---

## Verification

### Check Installation

```bash
# Version
paracle --version

# Available commands
paracle --help

# Run hello world
paracle hello

# Check installed packages
pip show paracle
```

### Check Optional Features

```bash
# API server
paracle serve --help

# If not installed, you'll see:
# Error: API server dependencies not installed.
# Install with: pip install 'paracle[api]'
```

---

## Troubleshooting

### "uvicorn is not installed"

**Problem**: Running `paracle serve` fails.

**Solution**:

```bash
pip install 'paracle[api]'
```

### "docker is not installed"

**Problem**: Sandbox features fail.

**Solution**:

```bash
# 1. Install Docker Desktop
# https://www.docker.com/products/docker-desktop

# 2. Install Python dependencies
pip install 'paracle[sandbox]'
```

### "ModuleNotFoundError: No module named 'anthropic'"

**Problem**: Provider not installed.

**Solution**:

```bash
# Install specific provider
pip install anthropic

# Or install all providers
pip install 'paracle[providers]'
```

### Version Conflicts

**Problem**: Dependency conflicts.

**Solution**:

```bash
# Use virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install fresh
pip install 'paracle[all]'
```

---

## Upgrade

### Upgrade to Latest Version

```bash
# Core
pip install --upgrade paracle

# With extras
pip install --upgrade 'paracle[all]'
```

### Upgrade Specific Package

```bash
# Upgrade just the API server components
pip install --upgrade fastapi uvicorn
```

---

## Uninstall

```bash
# Uninstall Paracle
pip uninstall paracle

# Clean up dependencies (optional)
pip uninstall fastapi uvicorn anthropic openai
```

---

## Next Steps

After installation:

1. **Initialize workspace**: `paracle init`
2. **Configure API keys**: See [API Keys Guide](api-keys.md)
3. **Run your first agent**: `paracle agents run --help`
4. **Start API server**: `paracle serve` (if installed with `[api]`)
5. **Read tutorials**: [Getting Started](getting-started.md)

---

## Related Documentation

- [API Keys Configuration](api-keys.md)
- [Getting Started Guide](getting-started.md)
- [Architecture Overview](architecture.md)
- [Docker Deployment](docker-deployment.md)

---

**Last Updated**: 2026-01-11
**Version**: 1.0.3
