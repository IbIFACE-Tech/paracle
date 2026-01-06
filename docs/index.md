# Welcome to Paracle

**Paracle** is a user-driven multi-agent framework for building AI-native applications. Design, orchestrate, and deploy autonomous AI agents with ease.

<div class="grid cards" markdown>

-   :material-robot:{ .lg .middle } __Agent-First Design__

    ---

    Build autonomous agents with clear roles, capabilities, and inheritance.

    [:octicons-arrow-right-24: Learn about Agents](user-guide/agents.md)

-   :material-workflow:{ .lg .middle } __Workflow Orchestration__

    ---

    Coordinate multiple agents in complex workflows with dependency management.

    [:octicons-arrow-right-24: Explore Workflows](workflow-guide.md)

-   :material-tools:{ .lg .middle } __Extensible Tools__

    ---

    Rich ecosystem of built-in tools for filesystem, HTTP, shell operations, and more.

    [:octicons-arrow-right-24: Discover Tools](builtin-tools.md)

-   :material-cloud:{ .lg .middle } __Multi-Provider Support__

    ---

    Works with OpenAI, Anthropic, Azure, Google, xAI, DeepSeek, Groq, Ollama, and more.

    [:octicons-arrow-right-24: View Providers](providers.md)

-   :material-shield-check:{ .lg .middle } __Safety & Isolation__

    ---

    Docker-based sandboxing, automatic rollback, and artifact review workflows.

    [:octicons-arrow-right-24: Phase 5 Features](phase5-guide.md)

-   :material-api:{ .lg .middle } __REST API + CLI__

    ---

    Full-featured REST API server and comprehensive command-line interface.

    [:octicons-arrow-right-24: API Reference](api-reference.md)

</div>

## Quick Start

Get started with Paracle in minutes:

```bash
# Install Paracle
pip install paracle

# Create your first agent
paracle init my-agent

# Run the agent
paracle agent run my-agent
```

[Get Started →](getting-started.md){ .md-button .md-button--primary }
[View Examples →](examples/hello-world.md){ .md-button }

## Why Paracle?

### 🎯 User-Driven Philosophy

Paracle puts developers in control. Unlike black-box frameworks, you define:

- What agents can do (tools and permissions)
- How agents collaborate (workflows and orchestration)
- When agents need approval (review and rollback)

### 🏗️ Production-Ready Architecture

Built with enterprise needs in mind:

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

- 📖 [Documentation](https://paracle.readthedocs.io)
- 💬 [GitHub Discussions](https://github.com/IbIFACE-Tech/paracle-lite/discussions)
- 🐛 [Issue Tracker](https://github.com/IbIFACE-Tech/paracle-lite/issues)
- 📧 Email: team@ibiface-tech.com

## Contributing

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details.

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

---

**Ready to build your first agent?** [Get Started →](getting-started.md){ .md-button .md-button--primary }
