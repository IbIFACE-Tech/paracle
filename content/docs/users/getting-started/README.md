# Paracle Documentation

> Comprehensive, well-organized documentation for the Paracle multi-agent framework

## 📚 Documentation Structure

The documentation is organized into 8 main sections:

### 1. 🚀 Getting Started
**For new users - everything you need to begin**

- [Installation](getting-started.md) - Setup and prerequisites
- [Interactive Tutorial](tutorial.md) - 30-minute guided experience ⭐
- [Quick Start](quickstart.md) - Fast track to first agent
- [Configuration](configuration-guide.md) - Project setup
- [API Keys](api-keys.md) - LLM provider configuration

**Start here:** [Interactive Tutorial](tutorial.md)

---

### 2. 📚 Core Concepts
**Understanding the foundations**

- [Overview](concepts/overview.md) - The four pillars ⭐
- **Agents**
  - [Introduction](concepts/agents.md)
  - [Inheritance](agent-inheritance-example.md)
  - [Discovery](agent-discovery.md)
  - [Skills](agent-skills.md)
- **Workflows**
  - [Introduction](workflow-guide.md)
  - [Execution Modes](execution-modes.md)
- **Tools**
  - [Built-in Tools](builtin-tools.md)
  - [Custom Tools](concepts/custom-tools.md)
- **Providers**
  - [Overview](providers.md)
  - [Multi-Provider](concepts/multi-provider.md)

**Best for:** Understanding how Paracle works

---

### 3. 🏗️ Architecture & Modules
**Deep dive into system design**

- [System Architecture](architecture.md) - High-level design ⭐
- [Module Overview](architecture/modules.md) - 30+ modules explained ⭐
- [Design Patterns](architecture/patterns.md)

**Core Modules:**
- [paracle_core](modules/core.md) - Foundation
- [paracle_domain](modules/domain.md) - Business models
- [paracle_cli](modules/cli.md) - Command-line
- [paracle_api](modules/api.md) - REST API

**Orchestration:**
- [paracle_orchestration](modules/orchestration.md) - Workflow engine
- [paracle_workflows](modules/workflows.md) - Workflow management

**Data & State:**
- [paracle_store](modules/store.md) - Persistence
- [paracle_memory](modules/memory.md) - Context & history
- [paracle_cache](modules/cache.md) - Response caching
- [paracle_vector](modules/vector.md) - Vector database

**Integration:**
- [paracle_providers](modules/providers.md) - LLM providers
- [paracle_adapters](modules/adapters.md) - Framework adapters
- [paracle_mcp](modules/mcp.md) - Model Context Protocol
- [paracle_a2a](modules/a2a.md) - Agent-to-Agent

**Execution & Safety:**
- [paracle_sandbox](modules/sandbox.md) - Safe execution
- [paracle_isolation](modules/isolation.md) - Network isolation
- [paracle_rollback](modules/rollback.md) - Rollback system
- [paracle_review](modules/review.md) - Artifact review

**Advanced:**
- [paracle_skills](modules/skills.md) - Agent skills
- [paracle_tools](modules/tools.md) - Tool management
- [paracle_knowledge](modules/knowledge.md) - Knowledge engine
- [paracle_kanban](modules/kanban.md) - Task management
- [paracle_git_workflows](modules/git-workflows.md) - Git automation

**Monitoring:**
- [paracle_events](modules/events.md) - Event bus
- [paracle_audit](modules/audit.md) - Audit logging
- [paracle_profiling](modules/profiling.md) - Performance profiling
- [paracle_governance](modules/governance.md) - Governance rules

**Best for:** Understanding internals and extensibility

---

### 4. 📖 User Guides
**Practical how-to guides**

**Agent Development:**
- [Creating Agents](guides/creating-agents.md)
- [Agent Patterns](guides/agent-patterns.md)
- [Testing Agents](guides/testing-agents.md)

**Workflow Development:**
- [Creating Workflows](guides/creating-workflows.md)
- [Workflow Patterns](guides/workflow-patterns.md)

**Tools & Skills:**
- [Using Tools](guides/using-tools.md)
- [Custom Tools](guides/custom-tools.md)
- [Developing Skills](guides/developing-skills.md)

**Memory & Knowledge:**
- [Memory System](memory-system-guide.md)
- [Knowledge Engine](knowledge-engine-guide.md)
- [Vector Store](vector-store-guide.md)

**Integration:**
- [MCP Integration](mcp-integration.md)
- [A2A Protocol](a2a-integration.md)
- [IDE Integration](ide-integration.md)

**Operations:**
- [Kanban Board](kanban-guide.md)
- [Git Workflows](modules/git-workflows.md)
- [Cost Tracking](cost-tracking-status.md)
- [Performance Profiling](performance-profiling-guide.md)

**Best for:** Step-by-step instructions

---

### 5. 🔧 Advanced Topics
**Production features and optimization**

**Execution & Safety:**
- [Sandbox Execution](phase5-guide.md)
- [Rollback System](guides/rollback.md)
- [Artifact Review](guides/artifact-review.md)
- [Network Isolation](guides/isolation.md)

**Performance:**
- [Response Caching](response-caching-guide.md)
- [Connection Pooling](guides/connection-pooling.md)
- [Profiling](performance-profiling-guide.md)

**State Management:**
- [Concurrency](state-management-concurrency.md)
- [File Locking](file-locking-implementation.md)
- [Conflict Resolution](guides/conflict-resolution.md)

**Security & Compliance:**
- [Security Agent](security-agent.md)
- [Audit System](audit-guide.md)
- [Compliance](compliance-guide.md)
- [Governance](governance-guide.md)

**Best for:** Production deployments

---

### 6. 📡 API & CLI Reference
**Complete command and API reference**

- [CLI Commands](cli-reference.md) - All CLI commands ⭐
- [REST API](api-reference.md) - HTTP endpoints ⭐
- [Configuration](config-commands.md) - Config commands

**Python SDK:**
- [Core API](api/core.md)
- [Domain Models](api/domain.md)
- [Providers](api/providers.md)
- [Orchestration](api/orchestration.md)
- [Tools](api/tools.md)
- [Events](api/events.md)

**Best for:** API reference lookup

---

### 7. 🚢 Deployment & Operations
**Production deployment guides**

- [Docker Setup](deployment/docker.md)
- [Production Deployment](deployment/production.md)
- [Monitoring](deployment/monitoring.md)
- [Scaling](deployment/scaling.md)

**Publishing:**
- [Overview](publishing-guide.md)
- [Setup](publishing-setup-summary.md)
- [Windows](windows-publishing-guide.md)
- [Action Items](publishing-action-items.md)

**Best for:** DevOps and deployment

---

### 8. 🤝 Development
**Contributing to Paracle**

- [Contributing](CONTRIBUTING.md) - How to contribute ⭐
- [Development Setup](development/setup.md)
- [Testing Strategy](development/testing.md)
- [Release Process](development/releases.md)

**Phase Guides:**
- [Phase 5](phase5-guide.md) - Safety features
- [Phase 7](phase7-integration-guide.md) - IDE integration
- [Phase 9](phase9-integration-guide.md) - Advanced features

**Best for:** Contributors

---

## 🎯 Quick Navigation

### By Role

**👨‍💻 Developer (First Time)**
1. [Interactive Tutorial](tutorial.md) ← Start here
2. [Core Concepts](concepts/overview.md)
3. [Creating Agents](guides/creating-agents.md)

**🏗️ Architect**
1. [System Architecture](architecture.md)
2. [Module Overview](architecture/modules.md)
3. [Design Patterns](architecture/patterns.md)

**🚀 DevOps Engineer**
1. [Docker Setup](deployment/docker.md)
2. [Production Deployment](deployment/production.md)
3. [Monitoring](deployment/monitoring.md)

**🔧 Advanced Developer**
1. [Sandbox Execution](phase5-guide.md)
2. [Performance Profiling](performance-profiling-guide.md)
3. [Custom Tools](guides/custom-tools.md)

**🤝 Contributor**
1. [Contributing Guide](CONTRIBUTING.md)
2. [Development Setup](development/setup.md)
3. [Architecture](architecture.md)

### By Task

**Creating Your First Agent**
→ [Interactive Tutorial](tutorial.md) or [Quick Start](quickstart.md)

**Building Workflows**
→ [Workflow Guide](workflow-guide.md)

**Adding Custom Tools**
→ [Custom Tools Guide](guides/custom-tools.md)

**Production Deployment**
→ [Deployment Guide](deployment/production.md)

**Performance Optimization**
→ [Caching](response-caching-guide.md), [Profiling](performance-profiling-guide.md)

**Security & Compliance**
→ [Security Agent](security-agent.md), [Audit Guide](audit-guide.md)

---

## 📊 Documentation Quality

### Coverage

✅ **100% Module Coverage** - All 30+ modules documented
✅ **Complete API Reference** - CLI + REST API + Python SDK
✅ **Interactive Tutorial** - 30-minute hands-on guide
✅ **Architecture Docs** - System design and patterns
✅ **Deployment Guides** - Docker, production, scaling

### Organization

✅ **8 Clear Sections** - Easy navigation
✅ **Progressive Complexity** - Basics → Advanced
✅ **Role-Based Paths** - Developer, DevOps, Architect
✅ **Task-Based Index** - Find by what you want to do

### Maintenance

- **Auto-Generated**: API docs from docstrings
- **Version Control**: Tracked in Git
- **CI/CD**: Built on every commit
- **Regular Updates**: Synced with code changes

---

## 🔨 Building the Docs

### Prerequisites

```bash
pip install mkdocs mkdocs-material pymdown-extensions
```

### Local Development

```bash
# Serve docs locally
mkdocs serve

# Open http://127.0.0.1:8000
```

### Build Static Site

```bash
# Build to site/
mkdocs build

# Deploy to GitHub Pages
mkdocs gh-deploy
```

---

## 🎨 Documentation Style

### Principles

1. **Progressive Disclosure** - Start simple, add complexity
2. **Show, Don't Tell** - Code examples for everything
3. **Multiple Paths** - Tutorial, quick start, deep dive
4. **Visual** - Diagrams, tables, code blocks
5. **Searchable** - Good titles, keywords, structure

### Format

- **Markdown** - Easy to write and maintain
- **YAML Frontmatter** - Metadata for navigation
- **Code Blocks** - Syntax highlighted
- **Tables** - For structured data
- **Admonitions** - Notes, warnings, tips

### Voice

- **Clear** - Simple language
- **Direct** - Get to the point
- **Helpful** - Anticipate questions
- **Professional** - But not stuffy

---

## 📝 Contributing to Docs

See [Contributing Guide](CONTRIBUTING.md)

**Quick Tips:**
- One concept per page
- Code examples for every feature
- Link related pages
- Keep navigation up to date
- Test all code examples

---

## 🔗 External Resources

- [GitHub Repository](https://github.com/IbIFACE-Tech/paracle-lite)
- [PyPI Package](https://pypi.org/project/paracle/)
- [Issue Tracker](https://github.com/IbIFACE-Tech/paracle-lite/issues)
- [Discussions](https://github.com/IbIFACE-Tech/paracle-lite/discussions)

---

**Last Updated:** 2026-01-07
**Documentation Version:** 2.0.0
**Framework Version:** 0.0.1
