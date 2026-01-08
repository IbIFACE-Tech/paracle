# Module Overview

Paracle is organized into 30+ focused modules, each with a specific responsibility.

## Module Map

```
paracle-lite/
└── packages/
    ├── Core Foundation
    │   ├── paracle_core          ← Utilities, config, IDs
    │   ├── paracle_domain        ← Business models
    │   └── paracle_store         ← Persistence layer
    │
    ├── Interfaces
    │   ├── paracle_cli           ← Command-line interface
    │   └── paracle_api           ← REST API server
    │
    ├── Orchestration & Execution
    │   ├── paracle_orchestration ← Workflow engine
    │   ├── paracle_sandbox       ← Safe execution
    │   ├── paracle_isolation     ← Network isolation
    │   ├── paracle_rollback      ← Rollback system
    │   └── paracle_review        ← Artifact review
    │
    ├── AI & Integration
    │   ├── paracle_providers     ← LLM providers
    │   ├── paracle_adapters      ← Framework adapters
    │   ├── paracle_mcp           ← Model Context Protocol
    │   └── paracle_a2a           ← Agent-to-Agent protocol
    │
    ├── Data & State
    │   ├── paracle_memory        ← Context & history
    │   ├── paracle_cache         ← Response caching
    │   ├── paracle_vector        ← Vector database
    │   └── paracle_knowledge     ← Knowledge engine
    │
    ├── Tools & Skills
    │   ├── paracle_tools         ← Tool management
    │   ├── paracle_skills        ← Agent skills
    │   └── paracle_resources     ← Resource management
    │
    ├── Operations & Monitoring
    │   ├── paracle_events        ← Event bus
    │   ├── paracle_audit         ← Audit logging
    │   ├── paracle_profiling     ← Performance profiling
    │   ├── paracle_governance    ← Governance rules
    │   └── paracle_conflicts     ← Conflict resolution
    │
    └── Collaboration
        ├── paracle_kanban        ← Task management
        ├── paracle_git           ← Git integration
        ├── paracle_git_workflows ← Git workflow automation
        ├── paracle_agent_comm    ← Agent communication
        ├── paracle_connection_pool ← Connection pooling
        └── paracle_plugins       ← Plugin system
```

## Layers

### 🔹 Layer 1: Core Foundation

**Purpose:** Base functionality required by all other modules

| Module            | Purpose                          | Dependencies |
| ----------------- | -------------------------------- | ------------ |
| `paracle_core`    | Utilities, config, ID generation | None         |
| `paracle_domain`  | Business models (Agent, Workflow)| core         |
| `paracle_store`   | Database access, repositories    | core, domain |

**When to use:** Every application needs these

---

### 🔹 Layer 2: Interfaces

**Purpose:** How users interact with Paracle

| Module         | Purpose                 | Port |
| -------------- | ----------------------- | ---- |
| `paracle_cli`  | Command-line interface  | -    |
| `paracle_api`  | REST API (FastAPI)      | 8000 |

**When to use:** Choose based on your needs (CLI for scripts, API for services)

---

### 🔹 Layer 3: Orchestration & Execution

**Purpose:** Run agents and workflows safely

| Module                  | Purpose                      | Key Feature        |
| ----------------------- | ---------------------------- | ------------------ |
| `paracle_orchestration` | Workflow engine              | DAG execution      |
| `paracle_sandbox`       | Isolated execution           | Docker containers  |
| `paracle_isolation`     | Network isolation            | Firewall rules     |
| `paracle_rollback`      | Undo changes on failure      | Snapshot/restore   |
| `paracle_review`        | Human approval gates         | Review workflows   |

**When to use:** Production deployments, untrusted code, high-risk operations

---

### 🔹 Layer 4: AI & Integration

**Purpose:** Connect to LLMs and external systems

| Module              | Purpose                     | Providers/Frameworks    |
| ------------------- | --------------------------- | ----------------------- |
| `paracle_providers` | LLM provider abstraction    | OpenAI, Anthropic, +12  |
| `paracle_adapters`  | Framework adapters          | LangChain, LlamaIndex   |
| `paracle_mcp`       | Model Context Protocol      | MCP-compatible tools    |
| `paracle_a2a`       | Agent-to-Agent communication| External agents         |

**When to use:** Multi-provider support, framework integration, agent collaboration

---

### 🔹 Layer 5: Data & State

**Purpose:** Manage application state and data

| Module              | Purpose                | Storage        |
| ------------------- | ---------------------- | -------------- |
| `paracle_memory`    | Context & history      | JSON/DB        |
| `paracle_cache`     | Response caching       | Redis/Memory   |
| `paracle_vector`    | Vector embeddings      | Qdrant/Chroma  |
| `paracle_knowledge` | Knowledge base         | Graph DB       |

**When to use:** Long-running agents, RAG applications, cost optimization

---

### 🔹 Layer 6: Tools & Skills

**Purpose:** Extend agent capabilities

| Module            | Purpose                  | Examples                |
| ----------------- | ------------------------ | ----------------------- |
| `paracle_tools`   | Tool management          | Filesystem, HTTP, Shell |
| `paracle_skills`  | Reusable agent skills    | Python expert, Security |
| `paracle_resources`| Resource management     | Files, APIs, DBs        |

**When to use:** Custom agent capabilities, skill sharing, resource control

---

### 🔹 Layer 7: Operations & Monitoring

**Purpose:** Observability and governance

| Module                | Purpose                  | Output                 |
| --------------------- | ------------------------ | ---------------------- |
| `paracle_events`      | Event bus                | Event streams          |
| `paracle_audit`       | Audit logging            | Audit trails           |
| `paracle_profiling`   | Performance profiling    | Metrics, traces        |
| `paracle_governance`  | Governance rules         | Policy enforcement     |
| `paracle_conflicts`   | Conflict resolution      | Merge strategies       |

**When to use:** Production, compliance, debugging, optimization

---

### 🔹 Layer 8: Collaboration

**Purpose:** Team collaboration and project management

| Module                   | Purpose                   | Integration           |
| ------------------------ | ------------------------- | --------------------- |
| `paracle_kanban`         | Task board                | GitHub Issues         |
| `paracle_git`            | Git operations            | Git CLI               |
| `paracle_git_workflows`  | Git workflow automation   | Conventional Commits  |
| `paracle_agent_comm`     | Agent messaging           | Event bus             |
| `paracle_connection_pool`| Connection pooling        | HTTP/DB pools         |
| `paracle_plugins`        | Plugin system             | Extension API         |

**When to use:** Team projects, automated workflows, custom extensions

---

## Dependency Graph

```
                    ┌──────────────┐
                    │paracle_core  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │paracle_domain│
                    └──────┬───────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐     ┌─────▼─────┐     ┌────▼────┐
    │ store   │     │providers  │     │  tools  │
    └────┬────┘     └─────┬─────┘     └────┬────┘
         │                │                 │
         └────────────────┼─────────────────┘
                          │
                   ┌──────▼──────────┐
                   │orchestration    │
                   └──────┬──────────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
         ┌────▼───┐  ┌───▼────┐  ┌──▼─────┐
         │sandbox │  │memory  │  │events  │
         └────────┘  └────────┘  └────────┘
```

## Module Categories

### Essential (Required)
- `paracle_core` - Always needed
- `paracle_domain` - Always needed
- `paracle_store` - Data persistence

### Interface (Choose One+)
- `paracle_cli` - For command-line
- `paracle_api` - For services

### Execution (Production)
- `paracle_orchestration` - Workflow engine
- `paracle_sandbox` - Safe execution (optional)
- `paracle_rollback` - Rollback (optional)

### Integration (As Needed)
- `paracle_providers` - LLM access
- `paracle_mcp` - MCP tools (optional)
- `paracle_adapters` - Frameworks (optional)

### Advanced (Optional)
- All other modules based on requirements

## Quick Start by Use Case

### Simple Script
```
paracle_core
paracle_domain
paracle_providers
paracle_cli
```

### Production API
```
paracle_core + paracle_domain + paracle_store
paracle_api + paracle_orchestration
paracle_sandbox + paracle_rollback + paracle_events
paracle_cache + paracle_memory
paracle_audit + paracle_profiling
```

### RAG Application
```
paracle_core + paracle_domain
paracle_vector + paracle_knowledge
paracle_cache + paracle_memory
paracle_providers
```

### Team Collaboration
```
paracle_core + paracle_domain
paracle_kanban + paracle_git_workflows
paracle_agent_comm
paracle_governance
```

## Next Steps

- [Explore each module](../modules/core.md)
- [Architecture patterns](patterns.md)
- [System architecture](../architecture.md)
