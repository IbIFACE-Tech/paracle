# Paracle Architecture

## Overview

Paracle follows a **modular monolith** architecture with clear boundaries between layers. This document explains the high-level architecture and design decisions.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     Clients                             │
│  (CLI, SDK, Web UI, External Applications)              │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                  API Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  REST API    │  │  WebSocket   │  │     CLI      │  │
│  │  (FastAPI)   │  │              │  │   (Click)    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              Application Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │Orchestration │  │   Memory     │  │Observability │  │
│  │   Engine     │  │  Management  │  │   & Metrics  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                 Domain Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │    Agents    │  │   Workflows  │  │    Tools     │  │
│  │ (Pure Logic) │  │ (Pure Logic) │  │ (Pure Logic) │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│            Infrastructure Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Persistence  │  │  Event Bus   │  │   Adapters   │  │
│  │  (SQLite)    │  │(Redis/valkey)│  │(LLM/Frameworks) │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Layers

### 1. API Layer

**Responsibility**: External interfaces

**Components**:

- **REST API** (FastAPI): HTTP endpoints for CRUD operations
- **WebSocket**: Real-time streaming and events
- **CLI** (Click): Command-line interface

**Packages**: `paracle_api`, `paracle_cli`

### 2. Application Layer

**Responsibility**: Orchestration and coordination

**Components**:

- **Orchestration Engine**: Executes workflows, manages agent lifecycle
- **Memory Management**: Context, history, knowledge base
- **Observability**: Metrics, tracing, logging

**Packages**: `paracle_orchestration`, `paracle_memory`, `paracle_observability`

### 3. Domain Layer

**Responsibility**: Pure business logic

**Components**:

- **Agents**: Agent models, inheritance, validation
- **Workflows**: Workflow definitions, DAG processing
- **Tools**: Tool definitions, schemas, permissions

**Packages**: `paracle_domain`

**Principles**:

- No dependencies on infrastructure
- Framework-agnostic
- Pure Python with Pydantic
- 100% testable without mocks

### 4. Infrastructure Layer

**Responsibility**: External integrations

**Components**:

- **Persistence**: Database access, repositories
- **Event Bus**: Asynchronous messaging
- **Adapters**: LLM providers, frameworks

**Packages**: `paracle_store`, `paracle_events`, `paracle_providers`, `paracle_adapters`

## Design Patterns

### Hexagonal Architecture (Ports & Adapters)

```
Domain (Core)
    ↓
  Ports (Interfaces)
    ↓
Adapters (Implementations)
```

**Benefits**:

- Testability
- Flexibility
- Decoupling

### Repository Pattern

```python
class AgentRepository(ABC):
    @abstractmethod
    async def save(self, agent: Agent) -> None: ...

    @abstractmethod
    async def get(self, agent_id: str) -> Agent: ...
```

**Benefits**:

- Abstracted persistence
- Easy testing
- Swappable backends

### Event-Driven Architecture

```python
# Events are emitted for all state changes
await event_bus.publish(Event(
    type="agent.created",
    data={"agent_id": agent.id}
))
```

**Benefits**:

- Audit trail
- Asynchronous processing
- Loose coupling

### Factory Pattern

```python
# Agent Factory resolves inheritance and creates instances
agent = agent_factory.create(agent_spec)
```

**Benefits**:

- Centralized creation logic
- Inheritance resolution
- Validation

## Key Modules

### paracle_core

**Purpose**: Shared utilities

**Contents**:

- ID generation (ULID)
- Configuration (Pydantic Settings)
- Error types
- Common types

### paracle_domain

**Purpose**: Business logic

**Contents**:

- Agent models
- Workflow models
- Tool models
- Business rules

### paracle_providers

**Purpose**: LLM abstraction

**Contents**:

- Provider interface
- OpenAI adapter
- Anthropic adapter
- Provider registry

### paracle_adapters

**Purpose**: Framework integration

**Contents**:

- MSAF adapter
- LangChain adapter
- LlamaIndex adapter

### paracle_orchestration

**Purpose**: Workflow execution

**Contents**:

- Orchestrator engine
- Step executor
- Dependency resolver

## Data Flow

### Agent Execution Flow

```
1. CLI/API receives request
2. Request validated
3. Agent spec retrieved from repository
4. Inheritance chain resolved
5. Agent instance created
6. LLM provider called
7. Response processed
8. Event emitted
9. Result returned
```

### Workflow Execution Flow

```
1. Workflow spec loaded
2. Dependency graph built
3. Steps executed in topological order
4. Context passed between steps
5. Results aggregated
6. Events emitted
7. Final result returned
```

## Scalability

### Phase 1-3 (Monolith)

- Single process
- SQLite persistence
- In-memory events

### Phase 4+ (Distributed)

- Horizontal scaling
- PostgreSQL/MySQL
- Redis/NATS for events
- Kubernetes deployment

## Security

### Principles

1. **Least Privilege**: Minimal permissions by default
2. **Defense in Depth**: Multiple security layers
3. **Secure by Default**: Safe defaults
4. **Audit Trail**: All operations logged

### Mechanisms

- API authentication (JWT)
- Rate limiting
- Secret management (env vars)
- Input validation (Pydantic)
- Output sanitization

## Testing Strategy

### Unit Tests

- Domain logic (100% coverage)
- Pure functions
- No external dependencies

### Integration Tests

- API endpoints
- Database operations
- Event flows

### E2E Tests

- Full workflows
- Multi-agent scenarios
- Provider integrations

## Performance

### Targets

- Time to First Agent: < 5 minutes
- API Response (p95): < 500ms
- Concurrent Agents: > 100

### Optimizations

- Async/await throughout
- Connection pooling
- Response caching
- Lazy loading

## Monitoring

### Metrics

- Request latency
- Error rates
- Agent execution time
- Token usage
- Cost tracking

### Logging

- Structured logs (JSON)
- Log levels
- Correlation IDs
- No PII in logs

## Decision Records

See [ADRs](../.parac/roadmap/decisions.md) for architecture decisions.

## Future Evolution

### Short Term (Phase 2-3)

- Multi-provider support
- MCP protocol
- API expansion

### Medium Term (Phase 4-5)

- Distributed deployment
- Advanced observability
- Performance optimization

### Long Term (Post v1.0)

- Microservices option
- Multi-tenancy
- Enterprise features

---

**Last Updated**: 2025-12-24
**Version**: 1.0
**Status**: Active
