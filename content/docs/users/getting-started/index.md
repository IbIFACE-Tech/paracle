# Welcome to Paracle

**Paracle** is a comprehensive multi-agent framework for building production-ready AI applications with 30+ specialized modules.

<div class="grid cards" markdown>

-   :material-robot:{ .lg .middle } **Agent-First Design**

    ---

    Build autonomous agents with inheritance, tools, skills, and multi-provider support.

    [:octicons-arrow-right-24: Core Concepts](concepts/overview.md)

-   :material-workflow:{ .lg .middle } **Workflow Orchestration**

    ---

    DAG-based workflows with parallel execution, conditional logic, and error handling.

    [:octicons-arrow-right-24: Workflow Guide](workflow-guide.md)

-   :material-tools:{ .lg .middle } **30+ Modules**

    ---

    Modular architecture: orchestration, sandbox, memory, caching, vector store, and more.

    [:octicons-arrow-right-24: Module Overview](architecture/modules.md)

-   :material-cloud:{ .lg .middle } **14+ LLM Providers**

    ---

    OpenAI, Anthropic, Google, xAI, DeepSeek, Groq + self-hosted (Ollama, LM Studio).

    [:octicons-arrow-right-24: Providers](providers.md)

-   :material-shield-check:{ .lg .middle } **Safety & Isolation**

    ---

    Docker sandbox, network isolation, automatic rollback, artifact review workflows.

    [:octicons-arrow-right-24: Security Features](phase5-guide.md)

-   :material-api:{ .lg .middle } **REST API + CLI**

    ---

    Full-featured CLI and FastAPI server. Start with `paracle tutorial`.

    [:octicons-arrow-right-24: CLI Reference](cli-reference.md)

-   :material-school:{ .lg .middle } **Interactive Tutorial**

    ---

    30-minute guided tutorial: create agents, add tools, build workflows.

    [:octicons-arrow-right-24: Quick Start](quickstart.md)

-   :material-connection:{ .lg .middle } **Integration Ready**

    ---

    MCP protocol, A2A agent communication, LangChain/LlamaIndex adapters.

    [:octicons-arrow-right-24: Integrations](mcp-integration.md)

</div>

## Quick Start

Get started with Paracle in minutes:

```bash
# Install Paracle
pip install paracle

# Initialize workspace
paracle init --template lite

# Start interactive tutorial
paracle tutorial start
```

[Get Started →](getting-started.md){ .md-button .md-button--primary }
[View Architecture →](architecture.md){ .md-button }

## Why Paracle?

### 🎯 Production-Ready Architecture

Built for enterprise with modular design:

- **30+ Specialized Modules**: Core, orchestration, sandbox, memory, cache, vector, knowledge, audit, profiling, and more
- **Layered Architecture**: Clear separation - Core → Domain → Application → Infrastructure
- **Horizontal Scaling**: Redis event bus, PostgreSQL, Docker orchestration
- **Safety First**: Sandbox execution, rollback system, artifact review

### 🏗️ Comprehensive Feature Set

Everything you need for AI applications:

| Category          | Features                                          |
| ----------------- | ------------------------------------------------- |
| **Orchestration** | DAG workflows, parallel execution, conditionals   |
| **Execution**     | Docker sandbox, network isolation, auto-rollback  |
| **Data**          | Memory, cache, vector store, knowledge engine     |
| **Operations**    | Audit logs, profiling, events, governance         |
| **Collaboration** | Kanban board, Git workflows, agent communication  |
| **Integration**   | MCP protocol, A2A, LangChain, LlamaIndex         |

### 🔧 Developer Experience

Built for developers, by developers:

- **Type-safe** - Full Python type hints with Pydantic v2
- **Async-first** - Built on asyncio for high performance
- **API-first** - REST API + CLI for any integration
- **Modular** - Install only what you need
- **Testable** - Comprehensive test coverage

### 🚀 Complete Feature Set

#### Phase 1-3: Core Framework ✅

- Agent creation and management
- Workflow orchestration with DAGs
- Multi-provider LLM support
- Persistent storage with SQLite
- Event-driven architecture

#### Phase 4: API & CLI ✅

- REST API server with FastAPI
- Enhanced CLI commands
- Async/sync execution modes
- IDE integration templates
- Comprehensive documentation

#### Phase 5: Safety & Isolation ✅

- Docker-based agent sandboxing
- Resource limits (CPU, memory, timeout)
- Automatic rollback on failure
- Artifact review and approval
- Network isolation

#### Phase 6: Knowledge Engine ✅

- RAG (Retrieval Augmented Generation) engine
- Document ingestion (files, directories, git repos)
- Smart chunking (Text, Markdown, AST-aware Code, Semantic)
- Vector similarity search with filtering
- Reranking (Cross-encoder, LLM, Ensemble)
- Source attribution and confidence scoring

#### Phase 8: Performance & Scale ✅

- Performance profiling infrastructure
- Function and request profiling decorators
- Automatic bottleneck detection
- Caching layer with TTL support
- Memory tracking and optimization
- Performance target validation

#### Phase 10: Governance & v1.0 Release

- ISO 42001 AI Management System compliance
- Policy Engine for governance rules
- Risk Scoring System with 8 factors
- Tamper-evident Audit Trail
- Compliance Reports and analysis
- Security hardening (ReDoS protection, path validation)

## Core Concepts

### Agents

Agents are autonomous AI entities with:

- **Role & Capabilities** - Defined purpose and skills
- **Tools** - Actions they can perform
- **Memory** - Context and history
- **Inheritance** - Shared behavior from parent agents

```python
from paracle_domain import AgentSpec

agent = AgentSpec(
    name="code-reviewer",
    role="review",
    provider="openai",
    model="gpt-4",
    tools=["code_analysis", "git_operations"],
    system_prompt="You are an expert code reviewer..."
)
```

[Learn More →](user-guide/agents.md)

### Workflows

Orchestrate multiple agents in complex workflows:

```python
from paracle_domain import WorkflowSpec, WorkflowStep

workflow = WorkflowSpec(
    name="code-review-workflow",
    steps=[
        WorkflowStep(
            id="analyze",
            agent="code-analyzer",
            depends_on=[]
        ),
        WorkflowStep(
            id="review",
            agent="code-reviewer",
            depends_on=["analyze"]
        ),
        WorkflowStep(
            id="report",
            agent="report-generator",
            depends_on=["review"]
        )
    ]
)
```

[Learn More →](workflow-guide.md)

### Tools

Extend agent capabilities with tools:

```python
from paracle_tools import Tool, ToolSchema

@tool(
    name="search_code",
    description="Search codebase for patterns",
    schema=ToolSchema(
        parameters={
            "pattern": {"type": "string"},
            "directory": {"type": "string"}
        }
    )
)
async def search_code(pattern: str, directory: str) -> list[str]:
    # Implementation
    return results
```

[Learn More →](builtin-tools.md)

## Installation Options

### Minimal Installation

```bash
pip install paracle
```

### With API Server

```bash
pip install "paracle[api]"
```

### With Persistence

```bash
pip install "paracle[store]"
```

### Full Installation

```bash
pip install "paracle[all]"
```

[Installation Guide →](getting-started.md)

## Use Cases

### 🤖 AI Application Development

Build sophisticated AI applications with multiple specialized agents working together.

### 🔄 Workflow Automation

Automate complex multi-step processes with agent orchestration.

### 🧪 Research & Experimentation

Rapidly prototype and test different agent architectures and LLM providers.

### 🏢 Enterprise Solutions

Deploy production-ready AI systems with safety, isolation, and observability.

## Architecture

Paracle follows a **modular monolith** architecture with clear boundaries:

```
┌─────────────────────────────────────────┐
│          API Layer (FastAPI/CLI)        │
├─────────────────────────────────────────┤
│      Application Layer (Orchestration)  │
├─────────────────────────────────────────┤
│       Domain Layer (Pure Logic)         │
├─────────────────────────────────────────┤
│    Infrastructure (Store/Events/LLMs)   │
└─────────────────────────────────────────┘
```

[Architecture Details →](architecture.md)

## Community & Support

- [Documentation](https://paracle.readthedocs.io)
- [Knowledge Engine Guide](knowledge-engine-guide.md) - RAG capabilities
- [Vector Store Guide](vector-store-guide.md) - Embeddings and search
- [Memory System Guide](memory-system-guide.md) - Agent memory
- [Governance Guide](governance-guide.md) - ISO 42001 compliance
- [Audit Trail Guide](audit-guide.md) - Tamper-evident logging
- [Compliance Guide](compliance-guide.md) - Compliance reports
- [Performance Profiling Guide](performance-profiling-guide.md)
- [GitHub Discussions](https://github.com/IbIFACE-Tech/paracle-lite/discussions)
- [Issue Tracker](https://github.com/IbIFACE-Tech/paracle-lite/issues)
- Email: [team@ibiface-tech.com](mailto:team@ibiface-tech.com)

## Contributing

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details.

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

---

**Ready to build your first agent?** [Get Started →](getting-started.md){ .md-button .md-button--primary }
