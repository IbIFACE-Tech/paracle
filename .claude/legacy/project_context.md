# Paracle Project - Claude Desktop Configuration

## Project Context

Paracle is a powerful multi-agent AI framework with unique features:

- **Agent Inheritance**: Hierarchical agent specialization
- **Multi-Framework Support**: MSAF, LangChain, LlamaIndex
- **Multi-Provider**: OpenAI, Anthropic, Google, Local LLMs
- **API-First Design**: FastAPI with RESTful endpoints
- **MCP Protocol**: Model Context Protocol support
- **.parac Workspace**: Governance and configuration structure

## Architecture

- **Language**: Python 3.10+
- **Package Manager**: uv (modern, fast)
- **Structure**: Modular monolith with 17 packages
- **Testing**: pytest with 80%+ coverage target
- **Patterns**: Hexagonal architecture, Repository, Event-driven

## Key Directories

### Source Code
- `packages/paracle_domain/` - Core business logic (AgentSpec, Agent, Workflow)
- `packages/paracle_cli/` - Command-line interface
- `packages/paracle_api/` - FastAPI REST API (future)
- `packages/paracle_store/` - Persistence layer (future)

### Configuration
- `.parac/` - Workspace governance (roadmap, agents, policies, memory)
- `pyproject.toml` - Project dependencies and tools
- `Makefile` - Developer commands

### Documentation
- `docs/` - Architecture, getting started, API reference
- `examples/` - Working code examples
- `README.md` - Project overview

## Current Phase

**Phase 0: Foundation** ✅ Complete (100%)
- Modular packages structure
- Domain models (AgentSpec, Agent, Workflow)
- CLI with hello command
- CI/CD pipelines
- Unit tests
- Documentation

**Phase 1: Core Domain** (Next - 3 weeks)
- Agent inheritance resolution algorithm
- Repository pattern + SQLite persistence
- Event bus implementation
- 80%+ test coverage
- CRUD operations

## Development Commands

```bash
# Setup
uv sync                  # Install dependencies

# Development
make test                # Run tests
make coverage            # Test coverage report
make lint                # Lint code
make format              # Format code
make typecheck           # Type checking

# CLI
paracle hello            # Test CLI
paracle agent create     # Create agent (placeholder)
paracle workflow run     # Run workflow (placeholder)
```

## Code Standards

- **Python**: Type hints, Pydantic models, 88 chars (Black)
- **Testing**: Pytest with arrange-act-assert pattern
- **Documentation**: Docstrings for all public APIs
- **Commits**: Conventional Commits format

## Important Files

When implementing features, always consider:
- `.parac/roadmap/roadmap.yaml` - Project roadmap and phases
- `.parac/policies/policy-pack.yaml` - Active policies
- `.parac/memory/context/current_state.yaml` - Current project state
- `packages/paracle_domain/models.py` - Core domain models

## Meta-Approach

We're using Paracle concepts to build Paracle itself:
- `.parac` workspace guides development
- Agent specifications in `.parac/agents/manifest.yaml`
- Workflows for common tasks in `.parac/workflows/`
- Policies enforce code quality and security

## Next Steps

Focus areas for Phase 1:
1. Implement agent inheritance resolution algorithm
2. Add SQLite persistence with Repository pattern
3. Create event bus for domain events
4. Achieve 80%+ test coverage
5. Implement full CRUD for agents and workflows
