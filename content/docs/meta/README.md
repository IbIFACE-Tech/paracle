# Paracle Meta-Agent Engine

> Intelligent AI-powered generation system that creates Paracle artifacts from natural language descriptions.

## Overview

`paracle_meta` is the AI brain of the Paracle framework. It generates agents, workflows, skills, and policies using multi-provider LLM support with learning, cost optimization, and quality scoring.

**Version**: 1.5.0

## Key Features

- **Multi-Provider LLM Support**: Anthropic Claude, OpenAI GPT, DeepSeek, Ollama (local)
- **Learning Engine**: Continuous improvement from feedback
- **Cost Optimization**: Budget limits with automatic fallback to cheaper models
- **Quality Scoring**: Automatic quality assessment with retry on low scores
- **Template Evolution**: Promote high-quality generations to reusable templates
- **Best Practices Database**: Searchable knowledge base for code patterns
- **Interactive Sessions**: Chat and Plan modes for conversational AI
- **Health Monitoring**: Built-in health checks for all components

## Installation

```bash
# Basic installation (core features only)
pip install paracle

# With database support (SQLAlchemy + repositories)
pip install paracle[meta]

# With PostgreSQL + pgvector for production
pip install paracle[meta-full]
```

## Quick Start

### Generate an Agent

```python
from paracle_meta import MetaAgent

async with MetaAgent() as meta:
    agent = await meta.generate_agent(
        name="SecurityAuditor",
        description="Reviews Python code for security vulnerabilities"
    )
    print(agent.spec)
```

### Interactive Chat Session

```bash
# Start a chat session
paracle meta chat

# With specific provider
paracle meta chat --provider anthropic

# Resume previous session
paracle meta chat --resume
```

### Plan Complex Tasks

```bash
# Start planning mode
paracle meta plan "Build a REST API with user authentication"

# Execute the plan
paracle meta plan --execute
```

## Architecture

```
paracle_meta/
├── engine.py              # MetaAgent - main entry point
├── config.py              # Configuration with validation
├── database.py            # SQLAlchemy database layer
├── repositories.py        # Repository pattern implementations
├── health.py              # Health check system
├── embeddings.py          # OpenAI/Ollama embedding providers
├── learning.py            # Learning engine with feedback
├── optimizer.py           # Cost optimizer & quality scorer
├── templates.py           # Template library & evolution
├── knowledge.py           # Best practices database
├── generators/            # Artifact generators
│   ├── agent_generator.py
│   ├── workflow_generator.py
│   ├── skill_generator.py
│   └── policy_generator.py
├── capabilities/          # Extended capabilities
│   ├── providers/         # LLM provider implementations
│   ├── provider_chain.py  # Fallback chain with circuit breaker
│   ├── web_capabilities.py
│   ├── code_execution.py
│   └── ...
└── sessions/              # Interactive sessions
    ├── chat.py            # Chat mode
    ├── plan.py            # Plan mode
    └── edit.py            # Edit mode
```

## Documentation

| Document | Description |
|----------|-------------|
| [Configuration Guide](./configuration.md) | Setup providers, database, and features |
| [CLI Reference](./cli-reference.md) | Command-line interface documentation |
| [Providers Guide](./providers.md) | LLM provider configuration |
| [Database Guide](./database.md) | PostgreSQL + pgvector setup |
| [Sessions Guide](./sessions.md) | Chat, Plan, and Edit modes |
| [Health Checks](./health.md) | Monitoring and diagnostics |
| [API Reference](./api-reference.md) | Python API documentation |

## Environment Variables

```bash
# LLM Provider API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...

# Database (optional, for persistent storage)
PARACLE_META_POSTGRES_URL=postgresql://user:pass@localhost/paracle_meta

# Embedding provider
PARACLE_META_EMBEDDING_PROVIDER=openai  # or "ollama"

# Cost limits
PARACLE_META_MAX_DAILY_BUDGET=10.0
PARACLE_META_MAX_MONTHLY_BUDGET=100.0
```

## Health Check

```bash
# Check system health
paracle meta health

# Output:
# Meta Engine Health Check
# ========================
# Status: HEALTHY
#
# Components:
#   database: healthy
#   providers: healthy (anthropic: up, openai: up)
#   learning_engine: healthy
#   cost_tracker: healthy (daily: $2.50/$10.00)
```

## License

Apache 2.0 - See LICENSE file for details.
