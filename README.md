# Paracle

**User-driven multi-agent framework for AI-native applications**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/IbIFACE-Tech/paracle-lite/workflows/CI/badge.svg)](https://github.com/IbIFACE-Tech/paracle-lite/actions)

---

## 🎯 What is Paracle?

Paracle is a powerful framework for building **multi-agent AI applications** with unique features:

- **🧬 Agent Inheritance**: Reuse and specialize agents like classes
- **🔌 Multi-Provider**: OpenAI, Anthropic, Google, Local models
- **🎨 Multi-Framework**: MSAF, LangChain, LlamaIndex support
- **🌐 API-First**: RESTful API with FastAPI
- **📡 MCP Native**: Model Context Protocol support
- **🎭 BYO Philosophy**: Bring Your Own models, frameworks, tools

## 🚀 Quick Start

### Installation

```bash
# Using uv (recommended)
uv pip install paracle

# Using pip
pip install paracle
```

### Hello World

```bash
paracle hello
```

### Create Your First Agent

```python
from paracle_domain.models import AgentSpec, Agent

# Define an agent
agent_spec = AgentSpec(
    name="code-assistant",
    description="A helpful coding assistant",
    provider="openai",
    model="gpt-4",
    temperature=0.7,
    system_prompt="You are an expert Python developer."
)

agent = Agent(spec=agent_spec)
print(f"Agent created: {agent.id}")
```

## 📦 Project Structure

```
paracle-lite/
├── .parac/              # Project workspace (config, memory, runs)
├── packages/            # Modular packages
│   ├── paracle_core/           # Core utilities
│   ├── paracle_domain/         # Domain models
│   ├── paracle_store/          # Persistence
│   ├── paracle_events/         # Event bus
│   ├── paracle_providers/      # LLM providers
│   ├── paracle_adapters/       # Framework adapters
│   ├── paracle_orchestration/  # Workflow engine
│   ├── paracle_tools/          # Tool management
│   ├── paracle_api/            # REST API
│   └── paracle_cli/            # CLI
├── tests/               # Test suite
├── docs/                # Documentation
└── examples/            # Example projects
```

## 🏗️ Architecture

Paracle follows a **modular monolith** architecture with clear boundaries:

- **Domain Layer**: Pure business logic (agents, workflows, tools)
- **Infrastructure Layer**: Persistence, events, providers
- **Application Layer**: Orchestration, API, CLI
- **Adapters**: External integrations (MSAF, LangChain, etc.)

See [Architecture Documentation](docs/architecture.md) for details.

## 🌟 Key Features

### Agent Inheritance

```python
# Base agent
base_agent = AgentSpec(
    name="base-coder",
    provider="openai",
    model="gpt-4",
    temperature=0.7
)

# Specialized agent (inherits from base)
python_expert = AgentSpec(
    name="python-expert",
    parent="base-coder",  # Inheritance!
    system_prompt="Expert in Python best practices",
    tools=["pytest", "pylint"]
)
```

### Multi-Provider Support

```python
# OpenAI
agent1 = AgentSpec(provider="openai", model="gpt-4")

# Anthropic
agent2 = AgentSpec(provider="anthropic", model="claude-sonnet-4.5")

# Local
agent3 = AgentSpec(provider="ollama", model="llama3")
```

### Workflows

```python
from paracle_domain.models import Workflow, WorkflowStep

workflow = Workflow(
    name="code-review",
    steps=[
        WorkflowStep(
            id="analyze",
            agent_id="analyzer",
            prompt="Analyze this code"
        ),
        WorkflowStep(
            id="suggest",
            agent_id="advisor",
            prompt="Suggest improvements",
            dependencies=["analyze"]
        )
    ]
)
```

## 📖 Documentation

- [Getting Started](docs/getting-started.md)
- [Architecture](docs/architecture.md)
- [API Reference](docs/api.md)
- [Examples](examples/)
- [Roadmap](.roadmap/)

## 🛠️ Development

### Setup

```bash
# Clone repository
git clone https://github.com/IbIFACE-Tech/paracle-lite.git
cd paracle-lite

# Install with dev dependencies
make install-dev

# Or with uv
uv sync --all-extras
```

### Running Tests

```bash
# Run tests
make test

# With coverage
make test-cov

# Watch mode
make test-watch
```

### Linting

```bash
# Run all linters
make lint

# Format code
make format
```

## 🗺️ Roadmap

Paracle is being developed in **5 phases** over **17 weeks**:

- ✅ **Phase 0** (1 week): Foundation & Setup
- 🔄 **Phase 1** (3 weeks): Core Domain
- 📅 **Phase 2** (4 weeks): Multi-Provider & Multi-Framework
- 📅 **Phase 3** (4 weeks): Orchestration & API
- 📅 **Phase 4** (3 weeks): Production Scale
- 📅 **Phase 5** (2 weeks): Polish & Release

See [detailed roadmap](.roadmap/ROADMAP_V0.0.1.md) for more information.

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linters
5. Submit a pull request

## 📄 License

Paracle is licensed under the [Apache License 2.0](LICENSE).

## 🔗 Links

- **Repository**: [github.com/IbIFACE-Tech/paracle-lite](https://github.com/IbIFACE-Tech/paracle-lite)
- **Documentation**: Coming soon
- **Issues**: [github.com/IbIFACE-Tech/paracle-lite/issues](https://github.com/IbIFACE-Tech/paracle-lite/issues)

## 💬 Support

- GitHub Issues: For bugs and feature requests
- Discussions: For questions and community support

---

**Built with ❤️ by IbIFACE-Tech**

_Paracle v0.0.1 - Phase 0: Foundation ✅_
