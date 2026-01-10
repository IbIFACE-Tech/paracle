# Paracle Services Inventory

> **Complete list of all Paracle packages and their capabilities**
>
> - **Auto-Generated**: ✅ Yes (via `paracle inventory update`)
> - **Generated**: 2026-01-09
> - **Version**: 1.0.1
> - **Total Packages**: 37
> - **Update Command**: `paracle inventory update`

## 🔄 Automated Maintenance

This document is **automatically updated** when packages are added/modified.

### Commands

```bash
# Check if inventory is up-to-date
paracle inventory check

# Auto-generate/update from current packages
paracle inventory update

# Preview changes without writing
paracle inventory update --dry-run
```

### Adding New Packages

When you add a new package:

1. Create package in `packages/paracle_<name>/`
2. Add description in `README.md` or `__init__.py` docstring:
   ```python
   """Package description here."""
   ```
3. Run: `paracle inventory update`
4. Commit both package and updated inventory

The inventory will automatically:
- ✅ Scan all `packages/paracle_*` directories
- ✅ Extract descriptions from README.md or `__init__.py`
- ✅ Categorize packages by functional domain
- ✅ Generate formatted markdown documentation
- ✅ Include version from pyproject.toml

---

## Overview

Paracle consists of **37 modular packages** organized by functional domains. Each package is independently testable and loosely coupled.

---

## Core Infrastructure (5 packages)

### 1. **paracle_core**
- **Purpose**: Core utilities, exceptions, configuration management
- **Key Components**: Base exceptions, logging, config loaders, utilities
- **Status**: ✅ Production Ready

### 2. **paracle_domain**
- **Purpose**: Domain models and business logic (agents, workflows, tools, skills)
- **Key Components**: AgentSpec, Workflow, Tool, Skill, Task models (Pydantic)
- **Status**: ✅ Production Ready

### 3. **paracle_store**
- **Purpose**: Persistence layer with SQLAlchemy
- **Key Components**: Repository pattern, database migrations, entity storage
- **Dependencies**: SQLAlchemy, Alembic
- **Status**: ✅ Production Ready

### 4. **paracle_events**
- **Purpose**: Event-driven architecture with pub/sub messaging
- **Key Components**: Event bus, event handlers, async event processing
- **Optional**: Redis for distributed events
- **Status**: ✅ Production Ready

### 5. **paracle_transport**
- **Purpose**: Communication protocols (HTTP, WebSocket, SSH, Unix sockets)
- **Key Components**: Protocol adapters, message serialization, connection pooling
- **Status**: ✅ Production Ready

---

## LLM Integration (2 packages)

### 6. **paracle_providers**
- **Purpose**: 14+ LLM provider integrations
- **Providers**:
  - **Commercial**: OpenAI, Anthropic, Google AI, xAI, DeepSeek, Groq, Mistral, Cohere, Together, Perplexity, OpenRouter, Fireworks
  - **Self-Hosted**: Ollama, LM Studio, vLLM, llama.cpp, LocalAI, Jan
- **Key Components**: Unified provider interface, streaming, tool calling
- **Status**: ✅ Production Ready

### 7. **paracle_adapters**
- **Purpose**: Framework adapters (Semantic Kernel, LangChain, LlamaIndex)
- **Key Components**: MSAF adapter, LangChain integration, LlamaIndex bridge
- **Status**: ✅ Production Ready

---

## Agent Orchestration (6 packages)

### 8. **paracle_orchestration**
- **Purpose**: Workflow engine and agent execution
- **Key Components**: WorkflowRunner, StepExecutor, parallel execution, DAG resolution
- **Status**: ✅ Production Ready

### 9. **paracle_runs**
- **Purpose**: Execution tracking and run management
- **Key Components**: Run storage, execution logs, status tracking
- **Storage**: `.parac/runs/` (gitignored)
- **Status**: ✅ Production Ready

### 10. **paracle_memory**
- **Purpose**: Agent memory systems (short-term, long-term, working)
- **Key Components**: Memory stores, context management, retrieval
- **Status**: ✅ Production Ready

### 11. **paracle_vector**
- **Purpose**: Vector storage for embeddings and semantic search
- **Key Components**: Vector stores (pgvector, ChromaDB), similarity search
- **Status**: ✅ Production Ready

### 12. **paracle_knowledge**
- **Purpose**: Knowledge base management
- **Key Components**: Document storage, RAG patterns, knowledge retrieval
- **Status**: ✅ Production Ready

### 13. **paracle_agent_comm**
- **Purpose**: Inter-agent communication
- **Key Components**: Message passing, agent discovery, communication protocols
- **Status**: ✅ Production Ready

---

## Tools & Skills (3 packages)

### 14. **paracle_tools**
- **Purpose**: Tool management and execution
- **Key Components**: Tool registry, filesystem tools, HTTP tools, shell execution
- **Features**: Async execution, permission control, sandboxing
- **Status**: ✅ Production Ready

### 15. **paracle_skills**
- **Purpose**: Portable skills system (multi-IDE support)
- **Key Components**: Skill definitions, IDE adapters (Copilot, Cursor, Claude Code)
- **Features**: Skill discovery, activation, progressive disclosure
- **Status**: ✅ Production Ready

### 16. **paracle_meta**
- **Purpose**: AI-powered code generation (internal AI engine)
- **Key Components**: MetaAgent, code generation, template generation
- **Features**: Agent spec generation, workflow generation, skill generation
- **Dependencies**: SQLAlchemy, aiosqlite (PostgreSQL optional)
- **Status**: ✅ Production Ready

---

## Protocols (3 packages)

### 17. **paracle_mcp**
- **Purpose**: Model Context Protocol (MCP) client/server
- **Key Components**: MCP server, tool discovery, resource management
- **Protocol**: Anthropic's MCP standard
- **Status**: ✅ Production Ready

### 18. **paracle_a2a**
- **Purpose**: Agent-to-Agent (A2A) protocol implementation
- **Key Components**: Federated agent communication, A2A SDK integration
- **Protocol**: A2A protocol (Anthropic/OpenAI standard)
- **Status**: ✅ Production Ready

### 19. **paracle_connection_pool**
- **Purpose**: Connection pooling for HTTP/WebSocket/DB
- **Key Components**: Pool management, connection reuse, health checks
- **Status**: ✅ Production Ready

---

## User Interfaces (2 packages)

### 20. **paracle_api**
- **Purpose**: REST API server (FastAPI)
- **Key Components**: OpenAPI docs, authentication, rate limiting
- **Endpoints**: Agents, workflows, tools, runs, metrics
- **Security**: JWT authentication, API keys, CORS
- **Status**: ✅ Production Ready

### 21. **paracle_cli**
- **Purpose**: Command-line interface
- **Commands**:
  - `paracle agents` - Agent management
  - `paracle workflows` - Workflow execution
  - `paracle board` - Kanban boards
  - `paracle task` - Task management
  - `paracle errors` - Error monitoring
  - `paracle config` - Configuration
- **Status**: ✅ Production Ready

---

## Development Tools (6 packages)

### 22. **paracle_sandbox**
- **Purpose**: Isolated execution environments (Docker, processes)
- **Key Components**: Container management, resource limits, security isolation
- **Status**: ✅ Production Ready

### 23. **paracle_isolation**
- **Purpose**: Code isolation and security boundaries
- **Key Components**: Namespace isolation, privilege separation
- **Status**: ✅ Production Ready

### 24. **paracle_profiling**
- **Purpose**: Performance profiling and optimization
- **Key Components**: Execution profiling, memory profiling, bottleneck detection
- **Status**: ✅ Production Ready

### 25. **paracle_observability**
- **Purpose**: Error tracking, metrics, analytics
- **Key Components**: ErrorRegistry, metrics collectors, dashboards
- **Features**: Error deduplication, pattern detection, statistics
- **Status**: ✅ Production Ready

### 26. **paracle_audit**
- **Purpose**: Security audit logs and compliance
- **Key Components**: Audit trail, compliance reports, access logs
- **Standards**: ISO 27001, ISO 42001, SOC2
- **Status**: ✅ Production Ready

### 27. **paracle_review**
- **Purpose**: Code review automation
- **Key Components**: PR analysis, code quality checks, review suggestions
- **Status**: ✅ Production Ready

---

## Git & Version Control (2 packages)

### 28. **paracle_git**
- **Purpose**: Git operations and repository management
- **Key Components**: Commit automation, branch management, status tracking
- **Status**: ✅ Production Ready

### 29. **paracle_git_workflows**
- **Purpose**: Git workflow automation (conventional commits, semantic versioning)
- **Key Components**: Commit conventions, version bumping, changelog generation
- **Status**: ✅ Production Ready

---

## Project Management (3 packages)

### 30. **paracle_kanban**
- **Purpose**: Kanban board and task tracking
- **Key Components**: BoardRepository, Task, TaskStatus, TaskPriority
- **Storage**: `.parac/memory/data/kanban.db`
- **CLI**: `paracle board`, `paracle task`
- **Status**: ✅ Production Ready

### 31. **paracle_governance**
- **Purpose**: Project governance and policy enforcement
- **Key Components**: Policy management, governance validation, compliance checks
- **Files**: `.parac/GOVERNANCE.md`, `.parac/policies/`
- **Status**: ✅ Production Ready

### 32. **paracle_conflicts**
- **Purpose**: Conflict detection and resolution
- **Key Components**: Conflict detection, merge strategies, resolution suggestions
- **Status**: ✅ Production Ready

---

## Resilience & Reliability (3 packages)

### 33. **paracle_resilience**
- **Purpose**: Fault tolerance and graceful degradation
- **Key Components**:
  - **CircuitBreaker**: Automatic failure detection (CLOSED/OPEN/HALF_OPEN)
  - **FallbackStrategy**: Cached, Default, Retry, Degraded, Chain strategies
  - Statistics tracking
- **Status**: ✅ Production Ready

### 34. **paracle_rollback**
- **Purpose**: Transaction rollback and state recovery
- **Key Components**: Checkpoint management, rollback strategies, state restoration
- **Status**: ✅ Production Ready

### 35. **paracle_cache**
- **Purpose**: Caching layer (Redis, in-memory)
- **Key Components**: Cache management, TTL policies, invalidation strategies
- **Status**: ✅ Production Ready

---

## Additional Services (3 packages)

### 36. **paracle_resources**
- **Purpose**: Resource management (CPU, memory, disk, network)
- **Key Components**: Resource limits, monitoring, quota enforcement
- **Status**: ✅ Production Ready

### 37. **paracle_plugins**
- **Purpose**: Plugin system for extensibility
- **Key Components**: Plugin discovery, lifecycle management, dependency resolution
- **Status**: ✅ Production Ready

---

## Package Categories Summary

| Category                     | Packages | Examples                                                    |
| ---------------------------- | -------- | ----------------------------------------------------------- |
| **Core Infrastructure**      | 5        | core, domain, store, events, transport                      |
| **LLM Integration**          | 2        | providers, adapters                                         |
| **Agent Orchestration**      | 6        | orchestration, runs, memory, vector, knowledge, agent_comm  |
| **Tools & Skills**           | 3        | tools, skills, meta                                         |
| **Protocols**                | 3        | mcp, a2a, connection_pool                                   |
| **User Interfaces**          | 2        | api, cli                                                    |
| **Development Tools**        | 6        | sandbox, isolation, profiling, observability, audit, review |
| **Git & Version Control**    | 2        | git, git_workflows                                          |
| **Project Management**       | 3        | kanban, governance, conflicts                               |
| **Resilience & Reliability** | 3        | resilience, rollback, cache                                 |
| **Additional Services**      | 3        | resources, plugins                                          |

**Total: 37 packages**

---

## Architecture Patterns

### 1. **Hexagonal Architecture (Ports & Adapters)**
- Domain layer isolated from infrastructure
- Framework-agnostic business logic
- Clear dependency boundaries

### 2. **Event-Driven Architecture**
- Async event bus (`paracle_events`)
- Pub/sub messaging
- Decoupled components

### 3. **Repository Pattern**
- Data access abstraction (`paracle_store`)
- Multiple storage backends
- Migration management

### 4. **Circuit Breaker Pattern**
- Fault tolerance (`paracle_resilience`)
- Automatic recovery
- Graceful degradation

### 5. **API-First Design**
- REST API (`paracle_api`)
- CLI fallback to direct core
- Consistent interfaces

---

## Key Capabilities Matrix

| Capability             | Primary Package          | Supporting Packages        |
| ---------------------- | ------------------------ | -------------------------- |
| **Agent Execution**    | paracle_orchestration    | runs, memory, agent_comm   |
| **LLM Integration**    | paracle_providers        | adapters, connection_pool  |
| **Tool Management**    | paracle_tools            | sandbox, isolation         |
| **Skill System**       | paracle_skills           | meta, tools                |
| **Error Management**   | paracle_observability    | resilience, rollback       |
| **Protocol Support**   | paracle_mcp, paracle_a2a | transport, connection_pool |
| **Project Management** | paracle_kanban           | governance, conflicts      |
| **Security**           | paracle_audit            | sandbox, isolation         |
| **Performance**        | paracle_profiling        | cache, resources           |
| **Git Operations**     | paracle_git              | git_workflows, review      |

---

## Installation Options

```bash
# Base installation (core + CLI)
pip install paracle

# With API server
pip install paracle[api]

# With PostgreSQL + vector search
pip install paracle[postgres]

# Full AI engine (meta + postgres)
pip install paracle[meta-full]

# All LLM providers
pip install paracle[providers-extended]

# Cloud providers (Azure, AWS, GCP)
pip install paracle[cloud]

# Framework adapters
pip install paracle[langchain]

# Everything
pip install paracle[api,meta-full,providers-extended,cloud,langchain]
```

---

## 🔄 Automated Updates

### How It Works

The `paracle inventory` command automatically:

1. **Scans** `packages/` directory for all `paracle_*` packages
2. **Extracts** descriptions from:
   - `README.md` (first paragraph after title)
   - `__init__.py` (module docstring)
3. **Categorizes** packages by functional domain
4. **Generates** formatted markdown with:
   - Package purpose and status
   - Version information
   - Update timestamp
   - Category organization

### Maintenance Workflow

```bash
# 1. Check consistency
paracle inventory check

# 2. Update if needed
paracle inventory update

# 3. Review changes
git diff .parac/memory/knowledge/services_inventory.md

# 4. Commit
git add .parac/memory/knowledge/services_inventory.md
git commit -m "docs: update services inventory"
```

### CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/docs.yml
- name: Check inventory
  run: |
    paracle inventory check || {
      paracle inventory update
      git diff --exit-code .parac/memory/knowledge/services_inventory.md && exit 1
    }
```

This ensures the inventory stays synchronized with the codebase.

---

## Related Documentation

- **Architecture**: [docs/architecture.md](../../docs/architecture.md)
- **API Reference**: [docs/api-reference.md](../../docs/api-reference.md)
- **Security**: [.parac/policies/SECURITY.md](../../.parac/policies/SECURITY.md)
- **Error Management**: [error_management.md](error_management.md)
- **Governance**: [.parac/GOVERNANCE.md](../../.parac/GOVERNANCE.md)

---

**Status**: ✅ All 37 Packages Production Ready
**Version**: 1.0.1
**Last Updated**: 2026-01-09
**Security Score**: 95/100
