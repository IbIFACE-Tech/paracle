# Paracle - Multi-Agent AI Framework

## Project Overview

Paracle is a user-driven multi-agent framework for building AI-native applications. It provides:

- **Agent Inheritance**: Hierarchical agent specialization like class inheritance
- **Multi-Provider Support**: OpenAI, Anthropic, Google, and local models (Ollama, LM Studio)
- **Multi-Framework Support**: MSAF, LangChain, LlamaIndex with transparent integration
- **API-First Design**: RESTful API with FastAPI and WebSocket support
- **MCP Native**: Model Context Protocol integration for standardized tool management

## Architecture

- **Language**: Python 3.10+
- **Package Manager**: uv (modern, fast)
- **Structure**: Modular monolith with layered hexagonal architecture
- **Testing**: pytest with 80%+ coverage target
- **Patterns**: Hexagonal (ports & adapters), Repository, Event-driven, DDD

### Package Structure

```
packages/
├── paracle_core/        # Shared utilities (ID generation, config, errors)
├── paracle_domain/      # Pure business logic (agents, workflows, tools)
├── paracle_store/       # Persistence layer (SQLAlchemy, Alembic)
├── paracle_events/      # Event bus (Redis/Valkey)
├── paracle_providers/   # LLM provider abstraction
├── paracle_adapters/    # Framework integrations
├── paracle_orchestration/ # Workflow execution engine
├── paracle_tools/       # Tool management & MCP
├── paracle_api/         # REST API (FastAPI)
└── paracle_cli/         # CLI interface (Click)
```

### Architecture Layers

```
Clients (CLI, SDK, Web UI)
         ↓
    API Layer (REST, WebSocket, CLI)
         ↓
  Application Layer (Orchestration, Memory, Observability)
         ↓
    Domain Layer (Agents, Workflows, Tools - Pure Logic)
         ↓
Infrastructure Layer (Persistence, Events, Adapters)
```

## Development Commands

```bash
# Setup
uv sync                  # Install dependencies

# Development
make test                # Run tests
make coverage            # Test coverage report
make lint                # Lint code (ruff)
make format              # Format code (black)
make typecheck           # Type checking (mypy)

# CLI
paracle hello            # Test CLI
paracle agent create     # Create agent
paracle workflow run     # Run workflow
```

## Code Standards

See @.claude/rules/code-style.md for detailed code style guidelines.

### Quick Reference

- **Type hints**: Required on all function parameters and returns
- **Models**: Use Pydantic BaseModel for all domain models
- **Formatting**: Black with 88 char line limit
- **Docstrings**: Google-style for all public APIs
- **Testing**: pytest with arrange-act-assert pattern
- **Commits**: Conventional Commits format

## Key Files

When implementing features, reference:

- `.parac/roadmap/roadmap.yaml` - Project roadmap and phases
- `.parac/policies/policy-pack.yaml` - Active policies
- `.parac/memory/context/current_state.yaml` - Current project state
- `packages/paracle_domain/` - Core domain models
- `docs/architecture.md` - Architecture documentation

## Current Phase

**Phase 0: Foundation** ✅ Complete
- Modular packages structure
- Domain models (AgentSpec, Agent, Workflow)
- CLI with hello command
- CI/CD pipelines
- Unit tests & documentation

**Phase 1: Core Domain** (Next)
- Agent inheritance resolution algorithm
- Repository pattern + SQLite persistence
- Event bus implementation
- 80%+ test coverage
- CRUD operations

## Domain Models

### Agent

```python
from paracle_domain.models import AgentSpec, Agent

spec = AgentSpec(
    name="my-agent",
    model="gpt-4",
    temperature=0.7,
    system_prompt="You are a helpful assistant.",
    tools=["code_reader", "code_executor"],
    parent="base-agent"  # Optional inheritance
)
agent = Agent(spec=spec)
```

### Workflow

```python
from paracle_domain.models import WorkflowSpec, WorkflowStep

workflow = WorkflowSpec(
    name="code_review",
    steps=[
        WorkflowStep(name="analyze", agent="analyzer"),
        WorkflowStep(name="review", agent="reviewer", depends_on=["analyze"])
    ]
)
```

## Feature Implementation Workflow

1. Start with domain models in `packages/paracle_domain/`
2. Add repository interfaces in `packages/paracle_store/`
3. Implement use cases in application layer
4. Create API endpoints in `packages/paracle_api/`
5. Add CLI commands in `packages/paracle_cli/`
6. Write tests in `tests/unit/` and `tests/integration/`
7. Update documentation in `docs/`

## Governance

Before implementing features, check:

- `.parac/roadmap/roadmap.yaml` - Is it planned?
- `.parac/policies/policy-pack.yaml` - What policies apply?
- `.parac/roadmap/decisions.md` - Any relevant ADRs?

## Meta-Approach

We use Paracle concepts to build Paracle:
- `.parac` workspace guides development
- Agent specifications in `.parac/agents/manifest.yaml`
- Workflows for common tasks in `.parac/workflows/`
- Policies enforce code quality and security
