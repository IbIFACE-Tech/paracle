# Paracle Documentation

> **Paracle** - User-driven multi-agent framework for AI-native applications.

Welcome to the Paracle documentation. This guide covers everything from getting started to advanced features.

## Documentation Structure

```
content/docs/
├── README.md              # This file - documentation index
├── users/                 # User-facing documentation (public)
│   ├── getting-started/   # Installation and first steps
│   ├── guides/            # How-to guides
│   ├── tutorials/         # Step-by-step tutorials
│   └── reference/         # Reference documentation
├── technical/             # Technical documentation (NOT committed)
│   ├── architecture/      # System architecture
│   ├── concepts/          # Core concepts
│   └── modules/           # Package documentation
├── meta/                  # Paracle Meta Engine docs
├── api/                   # API documentation
└── quickref/              # Quick reference cards
```

## Quick Links

### Getting Started

| Guide | Description |
|-------|-------------|
| [Installation](users/getting-started/README.md) | Install Paracle |
| [Quick Start](users/getting-started/quickstart.md) | 5-minute tutorial |
| [First Project](users/tutorials/tutorial.md) | Build your first agent |

### User Guides

| Guide | Description |
|-------|-------------|
| [Installation](installation.md) | Complete installation guide with all options |
| [Installation Quick Ref](quickref/installation-quickref.md) | Copy-paste installation commands |
| [Working with Agents](users/guides/agents.md) | Create and run agents |
| [Working with Workflows](users/guides/workflows.md) | Orchestrate multiple agents |
| [Working with Skills](users/guides/skills.md) | Reusable agent capabilities |
| [.parac/ Structure](users/reference/parac-structure.md) | Workspace folder reference |
| [AI Generation](users/ai-generation.md) | Generate agents with AI |
| [Remote Development](users/remote-development.md) | Run Paracle on remote servers |
| [API Keys](users/reference/api-keys.md) | Configure LLM providers |

### Technical Documentation

> **Note**: Technical docs are in `content/docs/technical/` (gitignored for internal use).

| Guide | Description |
|-------|-------------|
| [Architecture Overview](technical/architecture/overview.md) | System architecture |
| [CLI Reference](technical/cli-reference.md) | Complete CLI documentation (42 commands) |
| [API Reference](technical/api-reference.md) | REST API documentation |
| [Developer Guide](technical/developer-guide.md) | Contributing to Paracle |
| [Deployment Guide](technical/deployment-guide.md) | Docker, Kubernetes, Cloud |
| [Packages Reference](technical/modules/packages.md) | All 20+ packages |
| [Agents Guide](technical/agents-guide.md) | Agent system deep dive |

### MCP & Tools Documentation

| Guide | Description |
|-------|-------------|
| [MCP Quick Reference](mcp-quick-reference.md) | 66 MCP tools overview |
| [MCP Full Coverage](mcp-full-coverage.md) | Complete MCP implementation guide |
| [IDE Tools](tools/ide-tools.md) | VS Code, Cursor, Windsurf integration |
| [GitHub CLI Tool](tools/github-cli-tool.md) | GitHub operations via MCP |

### Paracle Meta Engine

| Guide | Description |
|-------|-------------|
| [Meta Overview](meta/README.md) | AI generation engine |
| [Configuration](meta/configuration.md) | Configure providers and settings |
| [Providers](meta/providers.md) | LLM provider setup |
| [Sessions](meta/sessions.md) | Chat, Plan, Edit modes |

## What is Paracle?

> **📖 For a comprehensive overview**: See [OVERVIEW.md](OVERVIEW.md) - Complete capabilities, strengths, and comparisons

Paracle is an open-source multi-agent framework that enables:

- **Agent Orchestration**: Define agents with YAML, execute with AI
- **Workflow Automation**: DAG-based workflow execution
- **Governance & Compliance**: Built-in ISO 42001 compliance support
- **Multi-Provider Support**: Anthropic, OpenAI, DeepSeek, Ollama
- **IDE Integration**: VS Code, Cursor, Claude Code support

## Core Concepts

### Agents

Agents are the fundamental building blocks:

```yaml
# .parac/agents/specs/coder.yaml
name: coder
description: "Python coding assistant"
model: claude-sonnet-4-20250514
temperature: 0.7
capabilities:
  - code_generation
  - code_review
```

### Workflows

Orchestrate multiple agents:

```yaml
# .parac/workflows/review-pipeline.yaml
name: review-pipeline
steps:
  - name: analyze
    agent: analyzer
  - name: review
    agent: reviewer
    depends_on: [analyze]
```

### Skills

Reusable capabilities:

```yaml
# .parac/skills/git-commit.yaml
name: git-commit
description: "Commit changes with proper message"
parameters:
  - name: message
    type: string
```

## Installation

```bash
# Install with pip
pip install paracle

# Or with optional features
pip install paracle[api,meta]

# Verify installation
paracle --version
```

## Quick Start

```bash
# Initialize a new project
paracle init

# List available agents
paracle agents list

# Run an agent
paracle agent run coder --task "Create a hello world script"

# Start interactive chat
paracle meta chat
```

## Project Status

**Current Version**: 1.0.0

| Feature | Status |
|---------|--------|
| Core Framework | ✅ Stable |
| CLI | ✅ Stable |
| REST API | ✅ Stable |
| Meta Engine | ✅ Stable |
| MCP Integration | ✅ Stable |
| Remote SSH | 🚧 In Progress |

## Contributing

We welcome contributions! See:

- [Contributing Guide](../../CONTRIBUTING.md)
- [Code Style](../../.parac/policies/CODE_STYLE.md)
- [GitHub Issues](https://github.com/IbIFACE-Tech/paracle-lite/issues)

## License

Apache 2.0 - See [LICENSE](../../LICENSE) for details.

---

**Last Updated**: 2026-01-08
