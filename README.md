# Paracle

**User-driven multi-agent framework for AI-native applications**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/IbIFACE-Tech/paracle-lite/workflows/CI/badge.svg)](https://github.com/IbIFACE-Tech/paracle-lite/actions)

---

## 🎯 What is Paracle?

Paracle is a powerful framework for building **multi-agent AI applications** with unique features:

- **🧬 Agent Inheritance**: Reuse and specialize agents like classes
- **🔌 Multi-Provider**: 14+ providers - Commercial (OpenAI, Anthropic, Google, xAI, DeepSeek, Groq, Mistral, Cohere, Together, Perplexity, OpenRouter, Fireworks) + Self-hosted (Ollama, LM Studio, vLLM, llama.cpp, LocalAI, Jan)
- **🎨 Multi-Framework**: MSAF, LangChain, LlamaIndex support
- **🎯 Write Once Skills**: Define skills once, export to Copilot, Cursor, Claude, Codex
- **🌐 API-First**: RESTful API with FastAPI
- **📡 MCP Native**: Model Context Protocol support
- **🤝 A2A Protocol**: Agent-to-Agent interoperability with external agents
- **🎭 BYO Philosophy**: Bring Your Own models, frameworks, tools

## 🚀 Quick Start

### Installation

```bash
# Using uv (recommended)
uv pip install paracle

# Using pip
pip install paracle
```

### Configure API Keys

```bash
# Copy example and add your keys
cp .env.example .env
# Edit .env with your API keys (OPENAI_API_KEY, etc.)
```

📖 **See [API Keys Guide](docs/api-keys.md) for detailed setup**

### Verify Installation

```bash
paracle hello
```

### Interactive Tutorial (Recommended for Beginners)

New to Paracle? Start with our 30-minute interactive tutorial:

```bash
paracle tutorial start
```

The tutorial guides you through:
1. Creating your first agent
2. Adding tools (filesystem, http, shell)
3. Adding skills for specialized capabilities
4. Creating project templates
5. Testing your agent locally
6. Building your first workflow

Resume anytime with `paracle tutorial resume`

### Initialize & Run Your First Agent

```bash
# Initialize workspace
paracle init

# List available agents
paracle agents list

# Run an agent with a task
paracle agents run coder --task "Create a hello world script"
```

### Or Use the Python API

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
│   ├── paracle_skills/         # Skills system (multi-platform)
│   ├── paracle_mcp/            # MCP protocol client
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

### Getting Started

- [Getting Started Guide](docs/getting-started.md) - Quick start in 5 minutes
- [API Keys Configuration](docs/api-keys.md) - Set up LLM provider API keys
- [Providers Guide](docs/providers.md) - All 14+ supported providers

### Architecture & Design

- [Architecture Overview](docs/architecture.md) - System design and patterns
- [Synchronization Guide](docs/synchronization-guide.md) - Sync/async patterns
- [API-First CLI](docs/api-first-cli.md) - CLI architecture with API fallback

### Features

- [Skills System](docs/skills.md) - Write once, export to all AI platforms
- [Built-in Tools](docs/builtin-tools.md) - 9 native tools (filesystem, HTTP, shell)
- [MCP Integration](docs/mcp-integration.md) - Model Context Protocol support
- [Security Audit Report](docs/security-audit-report.md) - Security assessment
- [Examples](examples/) - 11 code examples and tutorials

### Reference

- [Roadmap](.parac/roadmap/roadmap.yaml) - Development roadmap
- [Architecture Decisions](.parac/roadmap/decisions.md) - ADRs

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

Paracle is under active development. See [roadmap](.parac/roadmap/roadmap.yaml) for details.

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

_Paracle v0.0.1 - 700+ tests passing_
