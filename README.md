<div align="center">

[![Paracle](assets/paracle_vis.png)](https://www.paracles.com)

### Multi-Agent Framework for AI-Native Applications

**Write Once, Deploy Everywhere**

<p>
  <a href="https://pypi.org/project/paracle/">
    <img src="https://img.shields.io/pypi/v/paracle.svg?style=flat-square&color=0078D4" alt="PyPI">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=flat-square" alt="License">
  </a>
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/python-3.10+-3776AB.svg?style=flat-square" alt="Python">
  </a>
  <a href="https://github.com/IbIFACE-Tech/paracle-lite/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/IbIFACE-Tech/paracle-lite/ci.yml?style=flat-square&label=build" alt="CI">
  </a>
  <a href="https://github.com/IbIFACE-Tech/paracle-lite">
    <img src="https://img.shields.io/github/stars/IbIFACE-Tech/paracle-lite?style=flat-square&color=FFB000" alt="Stars">
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/security-95%2F100-success?style=flat-square" alt="Security">
  </a>
  <a href=".parac/policies/OWASP_COMPLIANCE.md">
    <img src="https://img.shields.io/badge/OWASP-Compliant-success?style=flat-square&logo=owasp" alt="OWASP">
  </a>
  <a href="https://github.com/IbIFACE-Tech/paracle-lite/actions/workflows/security.yml">
    <img src="https://img.shields.io/badge/scans-daily-blue?style=flat-square" alt="Security Scans">
  </a>
</p>

[Quick Start](#quick-start) |
[Documentation](#documentation) |
[Architecture](#architecture) |
[Innovative Features](#more-features)

</div>

---

## Overview

Paracle is a framework for building production-ready multi-agent AI applications. Designed for scalability, security, and interoperability, Paracle enables organizations to develop sophisticated AI systems with confidence.

### Core Capabilities

<table>
<tr>
<td width="50%" valign="top">

#### Agent Inheritance

Implement sophisticated agent hierarchies using object-oriented principles. Inherit configurations, behaviors, and capabilities across agent families for maintainable, scalable systems.

#### Multi-Provider Architecture

Support for 14+ LLM providers ensures vendor flexibility:

- **Commercial**: OpenAI, Anthropic, Google AI, xAI, DeepSeek, Groq, Mistral AI, Cohere, Together AI, Perplexity, OpenRouter, Fireworks AI
- **Self-Hosted**: Ollama, LM Studio, vLLM, llama.cpp, LocalAI, Jan

#### Framework Agnostic

Seamless integration with leading AI frameworks: Microsoft Semantic Kernel (MSAF), LangChain, LlamaIndex. Choose the right tool for your use case.

#### Portable Skills System

Define agent capabilities once, deploy across platforms: GitHub Copilot, Cursor, Claude Code, OpenAI Codex, and custom IDEs.

</td>
<td width="50%" valign="top">

#### API-First Architecture

Production-grade RESTful API built with FastAPI. Comprehensive OpenAPI documentation, authentication, and rate limiting included.

#### Model Context Protocol (MCP)

Native support for the emerging MCP standard, enabling standardized tool discovery and interoperability across AI platforms.

#### Agent-to-Agent Protocol (A2A)

Federated agent communication protocol supporting distributed multi-agent systems and cross-organization collaboration.

#### Enterprise Flexibility

Bring Your Own (BYO) architecture: models, frameworks, tools, infrastructure. No vendor lock-in.

#### Security & Compliance

- 95/100 security score (Bandit, Safety, Semgrep)
- ISO 27001:2022 & ISO 42001:2023 aligned
- SOC2 Type II compliant controls
- OWASP Top 10 & GDPR compliant

</td>
</tr>
</table>

## Quick Start

### Installation

<table>
<tr>
<td>

**Using uv (Recommended)**

```bash
uv pip install paracle
```

</td>
<td>

**Using pip**

```bash
pip install paracle
```

</td>
</tr>
</table>

### Configuration

<table>
<tr>
<td>

**API Keys Setup**

```bash
# Copy example and add your keys
cp .env.example .env
# Edit .env with your API keys
```

📖 [API Keys Guide](content/docs/api-keys.md)

</td>
</tr>
</table>

### ✅ Step 3: Verify Installation

```bash
paracle hello
```

<details>
<summary><b>Interactive Tutorial</b> (30 minutes hands-on training)</summary>

```bash
paracle tutorial start
```

**Training Modules:**

1. Agent creation and configuration
2. Tool integration (filesystem, HTTP, shell)
3. Skills definition and deployment
4. Project template development
5. Local testing and validation
6. Workflow orchestration

Resume anytime: `paracle tutorial resume`

</details>

### 🎯 Step 4: Initialize & Run Your First Agent

```bash
# Initialize workspace
paracle init

# List available agents
paracle agents list

# Run an agent with a task
paracle agents run coder --task "Create a hello world script"
```

### 💻 Or Use the Python API

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
print(f"✅ Agent created: {agent.id}")
```

<div align="center">

**🎉 That's it! You're ready to build AI applications with Paracle!**

</div>

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
├── content/             # Documentation and templates
│   ├── docs/            # User documentation
│   └── templates/       # Project templates
└── content/examples/    # Example projects
```

## 🏗️ Architecture

Paracle follows a **modular monolith** architecture with clear boundaries:

- **Domain Layer**: Pure business logic (agents, workflows, tools)
- **Infrastructure Layer**: Persistence, events, providers
- **Application Layer**: Orchestration, API, CLI
- **Adapters**: External integrations (MSAF, LangChain, etc.)

See [Architecture Documentation](content/docs/architecture.md) for details.

## More Features

### Agent Inheritance System

<details open>
<summary><b>Hierarchical Agent Architecture</b></summary>

```python
# Base agent
base_agent = AgentSpec(
    name="base-coder",
    provider="openai",
    model="gpt-4",
    temperature=0.7
)

# Specialized agent (inherits from base) 🎯
python_expert = AgentSpec(
    name="python-expert",
    parent="base-coder",  # ← Inheritance magic!
    system_prompt="Expert in Python best practices",
    tools=["pytest", "pylint"]
)
```

</details>

<details>
<summary><b>🔌 Multi-Provider Support</b> - Switch providers instantly</summary>

```python
# OpenAI 🤖
agent1 = AgentSpec(provider="openai", model="gpt-4")

# Anthropic 🧠
agent2 = AgentSpec(provider="anthropic", model="claude-sonnet-4.5")

# Local (free!) 💻
agent3 = AgentSpec(provider="ollama", model="llama3")
```

**14+ providers supported** - Commercial + Self-hosted

</details>

<details>
<summary><b>Workflow Orchestration</b></summary>

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
            dependencies=["analyze"]  # ← Sequential execution
        )
    ]
)
```

</details>

## 📖 Documentation

<table>
<tr>
<td width="33%">

### 🎓 Getting Started

- [⚡ Getting Started Guide](content/docs/getting-started.md)
- [🔑 API Keys Configuration](content/docs/api-keys.md)
- [🔌 Providers Guide](content/docs/providers.md)

</td>
<td width="33%">

### 🏗️ Architecture & Design

- [🎯 Architecture Overview](content/docs/architecture.md)
- [🔄 Synchronization Guide](content/docs/synchronization-guide.md)
- [🌐 API-First CLI](content/docs/api-first-cli.md)

</td>
<td width="33%">

### ✨ Features

- [🎯 Skills System](content/docs/skills.md)
- [🔧 Built-in Tools](content/docs/builtin-tools.md)
- [📡 MCP Integration](content/docs/mcp-integration.md)
- [🔒 Security Audit](content/docs/security-audit-report.md)

</td>
</tr>
<tr>
<td colspan="3" align="center">

### 📚 Reference

[🗺️ Roadmap](.parac/roadmap/roadmap.yaml) •
[📝 Architecture Decisions](.parac/roadmap/decisions.md) •
[💡 Examples](content/examples/)

</td>
</tr>
</table>

## 🛠️ Development

<details>
<summary><b>🔧 Setup Development Environment</b></summary>

```bash
# Clone repository
git clone https://github.com/IbIFACE-Tech/paracle-lite.git
cd paracle-lite

# Install with dev dependencies
make install-dev

# Or with uv (recommended)
uv sync --all-extras
```

</details>

<details>
<summary><b>🧪 Running Tests</b></summary>

```bash
# Run all tests
make test

# With coverage report
make test-cov

# Watch mode (auto-reload)
make test-watch
```

**700+ tests** - Unit, integration, and end-to-end

</details>

<details>
<summary><b>✨ Code Quality</b></summary>

```bash
# Run all linters
make lint

# Auto-format code
make format
```

**Tools**: ruff, mypy, black, isort

</details>

### 🗺️ Roadmap

<div align="center">

**Paracle v1.0.1** is production-ready! 🎉

Current Phase: **Phase 10 - Governance & v1.0 Release** (95% complete)

[📋 View Full Roadmap](.parac/roadmap/roadmap.yaml) • [🎯 Current Phase Details](.parac/memory/context/current_state.yaml)

</div>

### Contributing

<div align="center">

We welcome contributions from the community.

<table>
<tr>
<td align="center" width="20%">
<b>1. Fork</b><br>
<a href="https://github.com/IbIFACE-Tech/paracle-lite/fork">Fork Repository</a>
</td>
<td align="center" width="20%">
<b>2. Branch</b><br>
Create Feature Branch
</td>
<td align="center" width="20%">
<b>3. Develop</b><br>
Implement Changes
</td>
<td align="center" width="20%">
<b>4. Test</b><br>
Validate Quality
</td>
<td align="center" width="20%">
<b>5. Submit</b><br>
<a href="https://github.com/IbIFACE-Tech/paracle-lite/pulls">Pull Request</a>
</td>
</tr>
</table>

[Contributing Guidelines](CONTRIBUTING.md) | [Code of Conduct](CODE_OF_CONDUCT.md)

</div>

### 📄 License

<div align="center">

Licensed under [Apache License 2.0](LICENSE)

**Free and open source** for personal and commercial use

</div>

---

### 🔗 Connect with Us

<div align="center">

<table>
<tr>
<td align="center">
<a href="https://github.com/IbIFACE-Tech/paracle-lite/issues">
<img src="https://img.shields.io/badge/GitHub-Issues-red?style=for-the-badge&logo=github" alt="Issues">
</a>
</td>
<td align="center">
<a href="https://github.com/IbIFACE-Tech/paracle-lite/discussions">
<img src="https://img.shields.io/badge/GitHub-Discussions-blue?style=for-the-badge&logo=github" alt="Discussions">
</a>
</td>
</tr>
</table>

### 💬 Get Support

**🐛 Bug Reports** • **✨ Feature Requests** • **❓ Questions** • **💡 Ideas**

All welcome on [GitHub Issues](https://github.com/IbIFACE-Tech/paracle-lite/issues) and [Discussions](https://github.com/IbIFACE-Tech/paracle-lite/discussions)

</div>

<div align="center">

---

### Paracle Framework

**Version 1.0.1**
700+ Tests | 95/100 Security Score | ISO/SOC2 Compliant

Built with ❤️ by [IbIFACE Team](https://www.ibiface.com)

[Back to top](#)

</div>
