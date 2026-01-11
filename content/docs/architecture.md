# Paracle Architecture Overview

System design and architectural patterns for the Paracle multi-agent framework.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────────┐ │
│  │   CLI   │  │   API   │  │   MCP   │  │   IDE Integrations  │ │
│  └────┬────┘  └────┬────┘  └────┬────┘  └──────────┬──────────┘ │
└───────┼────────────┼────────────┼──────────────────┼────────────┘
        │            │            │                  │
        ▼            ▼            ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Application Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ Orchestration │  │   Workflows  │  │    Agent Execution     │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
        │            │            │                  │
        ▼            ▼            ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Domain Layer                              │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌───────────────────┐  │
│  │ Agents  │  │ Workflows │  │  Tools  │  │      Skills       │  │
│  └─────────┘  └──────────┘  └─────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
        │            │            │                  │
        ▼            ▼            ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐   │
│  │Providers │  │  Store   │  │  Events  │  │   Resilience   │   │
│  └──────────┘  └──────────┘  └──────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Core Design Principles

### 1. Hexagonal Architecture (Ports & Adapters)

Paracle follows hexagonal architecture to ensure:

- **Testability**: Core logic is isolated from external dependencies
- **Flexibility**: Swap implementations without changing business logic
- **Maintainability**: Clear boundaries between layers

```
                    ┌─────────────────┐
                    │     Domain      │
                    │   (Business     │
                    │     Logic)      │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
    │  Port   │         │  Port   │         │  Port   │
    │(Provider)│        │ (Store) │         │ (Event) │
    └────┬────┘         └────┬────┘         └────┬────┘
         │                   │                   │
    ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
    │ Adapter │         │ Adapter │         │ Adapter │
    │(Anthropic)│       │(SQLite) │         │(Redis)  │
    └─────────┘         └─────────┘         └─────────┘
```

### 2. API-First Design

All functionality is exposed through REST APIs first:

- CLI commands call API endpoints
- IDE integrations use the same APIs
- Consistent behavior across interfaces

### 3. Event-Driven Communication

Components communicate through domain events:

- Loose coupling between modules
- Audit trail built-in
- Easy extension points

## Package Structure

```
packages/
├── paracle_core/        # Core utilities, logging, governance
├── paracle_domain/      # Domain models (Pydantic)
├── paracle_store/       # Persistence (SQLAlchemy)
├── paracle_events/      # Event bus, webhooks
├── paracle_providers/   # LLM providers (Anthropic, OpenAI, etc.)
├── paracle_orchestration/ # Agent execution engine
├── paracle_tools/       # Built-in tools
├── paracle_skills/      # Skills system
├── paracle_api/         # REST API (FastAPI)
├── paracle_cli/         # CLI (Typer)
├── paracle_mcp/         # MCP server
├── paracle_meta/        # AI generation engine
├── paracle_kanban/      # Kanban board management
├── paracle_resilience/  # Circuit breakers, retry
├── paracle_vector/      # Vector search (pgvector)
├── paracle_observability/ # Metrics, tracing
└── paracle_transport/   # Remote execution
```

## Domain Model

### Agent

The fundamental unit of work:

```python
class AgentSpec(BaseModel):
    name: str                    # Unique identifier
    description: str             # What the agent does
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.7
    system_prompt: str | None
    parent: str | None           # Inheritance
    capabilities: list[str]
    tools: list[str]
    skills: list[str]
```

### Workflow

Orchestrates multiple agents:

```python
class Workflow(BaseModel):
    name: str
    description: str
    steps: list[WorkflowStep]
    inputs: list[WorkflowInput]
    outputs: list[WorkflowOutput]
```

### Tool

Executable capability:

```python
class Tool(BaseModel):
    name: str
    description: str
    category: str
    parameters: dict[str, ToolParameter]
    handler: Callable
```

## Execution Model

### Agent Execution Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Request    │────▶│   Resolve    │────▶│   Execute    │
│   (Task)     │     │ (Inheritance)│     │   (LLM)      │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
┌──────────────┐     ┌──────────────┐     ┌──────▼───────┐
│   Response   │◀────│    Log       │◀────│  Tool Calls  │
│              │     │   (Audit)    │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
```

### Workflow Execution

```
┌─────────────────────────────────────────────────────────┐
│                    Workflow Engine                       │
│  ┌─────────┐                                            │
│  │  Start  │                                            │
│  └────┬────┘                                            │
│       │                                                 │
│  ┌────▼────┐    ┌─────────┐    ┌─────────┐             │
│  │  Step 1 │───▶│  Step 2 │───▶│  Step 3 │──▶ ...      │
│  │(Agent A)│    │(Agent B)│    │(Agent C)│             │
│  └─────────┘    └─────────┘    └─────────┘             │
│       │              │              │                   │
│       ▼              ▼              ▼                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │                  Event Bus                       │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

### Request Processing

1. **Input**: User request via CLI/API/MCP
2. **Validation**: Pydantic model validation
3. **Resolution**: Agent inheritance, tool binding
4. **Execution**: LLM call with tools
5. **Logging**: Audit trail, metrics
6. **Response**: Formatted output

### State Management

```
┌─────────────────────────────────────────────────────────┐
│                   .parac/ Workspace                      │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Agents     │  │  Workflows   │  │    Tools     │  │
│  │   (specs/)   │  │   (*.yaml)   │  │  (registry)  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Memory     │  │   Roadmap    │  │   Policies   │  │
│  │  (context/)  │  │  (phases)    │  │   (rules)    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Security Architecture

### Authentication & Authorization

```
┌─────────────────────────────────────────────────────────┐
│                   Security Layer                         │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   API Keys   │  │    RBAC      │  │   Policies   │  │
│  │  (providers) │  │   (agents)   │  │   (tools)    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Audit Trail (ISO 42001)              │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Tool Permissions

```yaml
tools:
  read_file:
    requires_approval: false
  write_file:
    requires_approval: true
    sandbox: optional
  run_command:
    requires_approval: true
    sandbox: required
```

## Scalability

### Horizontal Scaling

```
┌─────────────┐     ┌─────────────────────────────────────┐
│   Load      │────▶│         API Instances               │
│  Balancer   │     │  ┌─────┐  ┌─────┐  ┌─────┐         │
└─────────────┘     │  │ API │  │ API │  │ API │         │
                    │  └──┬──┘  └──┬──┘  └──┬──┘         │
                    └─────┼───────┼───────┼──────────────┘
                          │       │       │
                    ┌─────▼───────▼───────▼──────────────┐
                    │           PostgreSQL                │
                    │         (with pgvector)             │
                    └─────────────────────────────────────┘
```

### Connection Pooling

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

## Extension Points

### Custom Providers

```python
class MyProvider(LLMProvider):
    async def complete(self, messages, model, temperature):
        # Custom implementation
        pass
```

### Custom Tools

```python
@tool(name="my_tool", category="custom")
def my_tool(param: str) -> str:
    """My custom tool."""
    return result
```

### Custom Skills

```yaml
# .parac/agents/skills/my-skill/skill.yaml
name: my-skill
description: "Custom skill"
prompts:
  main: |
    Custom prompt template
```

## Related Documentation

- [Synchronization Guide](synchronization-guide.md) - Async patterns
- [API-First CLI](api-first-cli.md) - CLI architecture
- [MCP Integration](mcp-integration.md) - MCP protocol
- [Security Audit](security-audit-report.md) - Security assessment
