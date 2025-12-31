# Architecture Decision Records (ADR)

This document captures key architectural decisions made during Paracle development.

## Format

Each decision follows this structure:

- **Date**: When the decision was made
- **Status**: Proposed | Accepted | Deprecated | Superseded
- **Context**: Why this decision was needed
- **Decision**: What was decided
- **Consequences**: Impact of the decision

---

## ADR-001: Python as Primary Language

**Date**: 2025-12-24
**Status**: Accepted
**Deciders**: Core Team

### Context

Need to choose primary implementation language for Paracle framework. Considerations include:

- AI/ML ecosystem maturity
- Developer community size
- Library availability
- Performance requirements

### Decision

Use Python 3.10+ as primary language.

### Consequences

**Positive:**

- Rich AI/ML ecosystem (OpenAI, Anthropic, LangChain, etc.)
- Large developer community
- Rapid prototyping and iteration
- Excellent type hints support (Pydantic)

**Negative:**

- Performance limitations for CPU-intensive tasks
- GIL for multi-threading
- Requires async/await for concurrency

**Mitigation:**

- Use async/await extensively
- Optimize hot paths
- Consider Rust extensions for performance-critical parts in future

---

## ADR-002: Modular Monolith Architecture

**Date**: 2025-12-24
**Status**: Accepted
**Deciders**: Core Team

### Context

Need to balance between:

- Simplicity for early adopters (monolith)
- Flexibility for future scaling (microservices)
- Development velocity

### Decision

Implement as modular monolith with clear package boundaries (17 packages).

### Consequences

**Positive:**

- Single deployment unit (simple)
- Clear module boundaries
- Easy to develop and test
- Can evolve to microservices later

**Negative:**

- Single point of failure initially
- Requires discipline for module boundaries

**Migration Path:**
Each package can be extracted to microservice if needed.

---

## ADR-003: Agent Inheritance System

**Date**: 2025-12-24
**Status**: Accepted
**Deciders**: Core Team

### Context

Agents often share common configurations (prompts, tools, models). Need mechanism for reusability without duplication.

### Decision

Implement functional inheritance system for agents:

- Agents can extend other agents
- Child agents inherit parent's config
- Override mechanism for specialization
- Validation of inheritance chain

### Consequences

**Positive:**

- DRY principle for agent configuration
- Easy specialization of agents
- Reduced configuration duplication
- Unique feature vs other frameworks

**Negative:**

- Added complexity in agent resolution
- Potential for deep inheritance chains

**Mitigation:**

- Limit inheritance depth (max 5 levels)
- Clear documentation and validation

---

## ADR-004: API-First Design

**Date**: 2025-12-24
**Status**: Accepted
**Deciders**: Core Team

### Context

Framework must be accessible via multiple interfaces (CLI, SDK, API, UI).

### Decision

Design API-first with FastAPI, then build CLI/SDK/UI on top of API.

### Consequences

**Positive:**

- Clear contract (OpenAPI)
- Easy integration
- Multiple client options
- Testable via HTTP

**Negative:**

- Additional layer of abstraction
- Network overhead for local usage

**Mitigation:**

- Provide SDK that can bypass API for local use
- Optimize API performance

---

## ADR-005: Multi-Provider Abstraction

**Date**: 2025-12-24
**Status**: Accepted
**Deciders**: Core Team

### Context

Users want freedom to choose LLM providers (OpenAI, Anthropic, Google, Local).

### Decision

Create provider abstraction layer with:

- Common interface for all providers
- Provider registry
- Runtime provider selection
- Bring Your Own Key (BYO)

### Consequences

**Positive:**

- Provider flexibility
- No vendor lock-in
- Easy to add new providers
- Cost optimization for users

**Negative:**

- Maintenance burden (multiple SDKs)
- Feature parity challenges

**Mitigation:**

- Focus on common features first
- Clear provider capability matrix

---

## ADR-006: Event-Driven Architecture

**Date**: 2025-12-24
**Status**: Accepted
**Deciders**: Core Team

### Context

Need audit trail, observability, and async processing.

### Decision

Implement event bus with:

- Append-only event log (NDJSON)
- Async event handlers
- Event replay capability
- Rollback support via snapshots

### Consequences

**Positive:**

- Complete audit trail
- Debugging and replay
- Async processing
- Rollback capability

**Negative:**

- Added complexity
- Storage requirements

**Mitigation:**

- Event retention policies
- Optional event storage

---

## ADR-007: MCP (Model Context Protocol) Support

**Date**: 2025-12-24
**Status**: Accepted
**Deciders**: Core Team

### Context

Tool ecosystem fragmentation. Need standard protocol for tool integration.

### Decision

Support MCP as primary tool protocol, alongside internal tools.

### Consequences

**Positive:**

- Interoperability with MCP ecosystem
- Standard tool interface
- Community tools
- Future-proof

**Negative:**

- Additional protocol to maintain
- MCP ecosystem still emerging

**Mitigation:**

- Also support internal tools
- Hybrid approach

---

## ADR-008: .parac Workspace Structure

**Date**: 2025-12-24
**Status**: Accepted
**Deciders**: Core Team

### Context

Projects need:

- Configuration management
- Memory and context
- Run history and rollback
- Policy enforcement

### Decision

Create `.parac/` workspace structure as local project configuration and state.

### Consequences

**Positive:**

- Clear project structure
- Version-controlled configuration (optional)
- Local state management
- Policy-first approach

**Negative:**

- Learning curve for structure
- Additional files to manage

**Mitigation:**

- Excellent documentation
- CLI commands to manage .parac
- Templates and examples

---

## ADR-009: .parac/ Governance in Framework

**Date**: 2025-12-24
**Status**: Accepted
**Deciders**: Core Team

### Context

The `.parac/` workspace needs to stay synchronized with project reality. Initial implementation used manual Python scripts in `.parac/hooks/`, but this approach has limitations:

- Scripts must be called manually
- Logic duplicated for each project
- No integration with framework lifecycle
- Users must maintain their own sync logic

### Decision

Move `.parac/` governance logic into the framework (`packages/`):

1. **`paracle_core/parac/`** - Core governance logic:
   - State synchronization
   - Validation
   - YAML parsing and updates

2. **`paracle_cli/commands/parac.py`** - CLI commands:
   - `paracle parac status` - Show current state
   - `paracle parac sync` - Synchronize with project
   - `paracle parac validate` - Validate consistency
   - `paracle parac session start` - Start work session
   - `paracle parac session end` - End session with updates

3. **Git hooks** (optional, installed via `paracle init`):
   - pre-commit: validate .parac/
   - post-commit: sync state

4. **User hooks** - Custom hooks in `.parac/hooks/` called by framework

### Consequences

**Positive:**

- Single implementation, reusable across all projects
- Integrated with CLI and framework lifecycle
- Automatic synchronization options
- Consistent behavior for all users
- Framework can evolve governance logic

**Negative:**

- More code in framework to maintain
- Users depend on framework for governance

**Migration:**

- Existing `.parac/hooks/` scripts remain as prototypes
- Framework commands replace manual script calls
- User custom hooks still supported via config

### Implementation Order

1. `paracle_core/parac/` - Core logic (Phase 1)
2. `paracle_cli/commands/parac.py` - CLI commands (Phase 1)
3. Git hooks integration (Phase 2)
4. `paracle_governance/` - Full governance package (v0.7.0)

---

## Future Decisions

### Under Consideration

- [ ] TypeScript SDK for web integration
- [ ] gRPC API alongside REST
- [ ] Plugin system architecture
- [ ] Multi-tenancy support
- [ ] Distributed tracing (OpenTelemetry)

### Deferred to Later Versions

- Microservices architecture (post v1.0)
- Kubernetes operators (post v1.0)
- Enterprise features (SSO, RBAC) (post v0.5)
- UI/Dashboard (post v0.3)

---

## ADR-008: Agent Discovery System for IDE/AI Assistant Integration

**Date**: 2025-12-25
**Status**: Proposed
**Deciders**: Architect Agent, PM Agent
**Consulted**: Coder Agent

### Context

Currently, integrating PARACLE agents with IDEs/AI assistants requires manual configuration for each tool:
- **Copilot**: Duplicate agent specs in `.github/copilot-instructions.md`
- **Cursor**: Custom `.cursorrules` file with embedded specs
- **Claude**: Separate `.claude-instructions.md` with specs
- **Cline, Windsurf**: Similar duplication pattern

**Problems**:
1. **Duplication**: Agent specs must be copied to each IDE configuration
2. **Maintenance**: Updating one agent requires updating 5+ files
3. **No Discovery**: IDEs cannot auto-discover agents from `.parac/`
4. **Not Scalable**: Adding new IDEs requires more duplication
5. **Framework Limitation**: This should be solved at framework level, not user level

### Decision

Implement a **standardized agent discovery system** in the PARACLE framework with 3 components:

#### 1. Agent Manifest (`.parac/manifest.yaml`)

Auto-generated metadata file that IDEs can read:

```yaml
schema_version: "1.0"
workspace:
  name: "paracle-lite"
  version: "0.0.1"
  parac_version: "0.0.1"

agents:
  - id: "pm"
    name: "PM Agent"
    role: "Project Manager"
    spec_file: ".parac/agents/specs/pm.md"
    capabilities: ["planning", "tracking", "coordination"]

  - id: "architect"
    name: "Architect Agent"
    role: "System Architect"
    spec_file: ".parac/agents/specs/architect.md"
    capabilities: ["design", "decisions", "documentation"]

  - id: "coder"
    name: "Coder Agent"
    role: "Developer"
    spec_file: ".parac/agents/specs/coder.md"
    capabilities: ["implementation", "refactoring", "bugfix"]
```

#### 2. CLI Introspection Commands

```bash
# List all agents
paracle agents list
paracle agents list --format=json

# Get specific agent spec
paracle agents get pm
paracle agents get coder --format=markdown

# Export all agents
paracle agents export --format=json > agents.json
```

#### 3. IDE Instructions Generator

```bash
# Generate instructions for specific IDE
paracle generate instructions --ide=copilot
paracle generate instructions --ide=cursor --output=.cursorrules
paracle generate instructions --ide=claude

# Generate for all supported IDEs
paracle generate instructions --all

# Regenerate when agents change
paracle generate instructions --ide=copilot --force
```

**Generated files**:
- `.github/copilot-instructions.md` (GitHub Copilot)
- `.cursorrules` (Cursor AI)
- `.claude-instructions.md` (Claude Projects)
- `.clinerules` (Cline)
- `.windsurfrules` (Windsurf)

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                 PARACLE FRAMEWORK                   │
│                   (packages/)                       │
│                                                     │
│  ┌──────────────────────────────────────────┐     │
│  │  paracle_core/parac/                     │     │
│  │    • agent_discovery.py                  │     │
│  │    • manifest_generator.py               │     │
│  │    • instruction_generator.py            │     │
│  └──────────────────────────────────────────┘     │
│                                                     │
│  ┌──────────────────────────────────────────┐     │
│  │  paracle_cli/commands/                   │     │
│  │    • agents.py (list, get, export)       │     │
│  │    • generate.py (instructions)          │     │
│  └──────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘
                      ↓ generates
┌─────────────────────────────────────────────────────┐
│                .parac/ WORKSPACE                    │
│                                                     │
│  • manifest.yaml (auto-generated)                  │
│  • agents/specs/*.md (user-defined)                │
└─────────────────────────────────────────────────────┘
                      ↓ reads
┌─────────────────────────────────────────────────────┐
│            IDE INSTRUCTION FILES                    │
│            (auto-generated)                         │
│                                                     │
│  • .github/copilot-instructions.md                 │
│  • .cursorrules                                     │
│  • .claude-instructions.md                          │
│  • etc.                                             │
└─────────────────────────────────────────────────────┘
```

### Implementation Plan

#### Phase 1: Core Discovery System

**Files to create**:
- `packages/paracle_core/parac/agent_discovery.py`
- `packages/paracle_core/parac/manifest_generator.py`
- `packages/paracle_cli/commands/agents.py`

**Functionality**:
- Scan `.parac/agents/specs/` directory
- Parse agent markdown files
- Generate `manifest.yaml`
- Expose via CLI: `paracle agents list/get/export`

#### Phase 2: Instructions Generator

**Files to create**:
- `packages/paracle_core/parac/instruction_generator.py`
- `packages/paracle_cli/commands/generate.py`
- `templates/ide-instructions/*.jinja2` (templates for each IDE)

**Functionality**:
- Read manifest and agent specs
- Use Jinja2 templates for each IDE
- Generate IDE-specific instruction files
- Support: Copilot, Cursor, Claude, Cline, Windsurf

#### Phase 3: Auto-Sync

**Functionality**:
- Watch `.parac/agents/specs/` for changes
- Auto-regenerate `manifest.yaml`
- Optional: Auto-regenerate IDE instructions
- Integrate with `paracle parac sync`

### Consequences

#### Positive

✅ **Single Source of Truth**: Agents defined once in `.parac/agents/specs/`
✅ **Zero Duplication**: IDE files auto-generated from specs
✅ **Easy Maintenance**: Update one agent → regenerate all IDE files
✅ **IDE Agnostic**: Add new IDEs with just a template
✅ **Framework-Level**: Solved at the right abstraction level
✅ **Discoverable**: `manifest.yaml` is machine-readable
✅ **Extensible**: New IDEs just need a Jinja2 template

#### Negative

⚠️ **Build Step**: Users must run `paracle generate instructions` after agent changes
⚠️ **Template Maintenance**: Each IDE needs its own template
⚠️ **Complexity**: Adds new framework components

#### Mitigations

- Auto-generate on `paracle parac sync`
- Provide git pre-commit hook
- Clear error messages if files out of sync
- Well-documented templates for community contributions

### Alternatives Considered

#### Alternative 1: MCP (Model Context Protocol) Server

**Pros**: Real-time, no file generation, IDE-agnostic protocol
**Cons**: Only supported by some IDEs, requires running server
**Decision**: Keep as future enhancement, not MVP

#### Alternative 2: HTTP API

**Pros**: RESTful, language-agnostic
**Cons**: Requires running service, overkill for local files
**Decision**: Not needed, CLI is sufficient

#### Alternative 3: Keep Manual Configuration

**Pros**: No framework changes
**Cons**: Doesn't scale, high maintenance, defeats PARAC purpose
**Decision**: Rejected - this is the problem we're solving

### References

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [GitHub Copilot Instructions](https://docs.github.com/en/copilot)
- [Cursor AI Rules](https://cursor.sh/docs)
- PARACLE Agent Specifications (`.parac/agents/specs/`)

### Related ADRs

- ADR-001: Python as Primary Language
- ADR-002: Hexagonal Architecture
- ADR-009: API First Architecture (Supersedes partial implementation)

---

## ADR-009: API First Architecture for Agent Discovery

**Date**: 2025-12-25
**Status**: Accepted
**Deciders**: Architect Agent

### Context

After implementing ADR-008 (Agent Discovery System), we discovered that the CLI commands (`paracle agents`) were directly calling `AgentDiscovery` and `ManifestGenerator` services, bypassing the API layer. This violated the project's "API First" principle stated in the architecture.

**Problem**: CLI should consume the REST API, not call services directly.

**Principle**: PARACLE is API First - every feature must be exposed via REST API before being consumed by clients (CLI, Web, IDE plugins).

### Decision

Refactor agent discovery to follow API First architecture:

1. **Create REST API endpoints** in `packages/paracle_api/routers/agents.py`:
   - `GET /agents` - List all agents
   - `GET /agents/{agent_id}` - Get agent metadata
   - `GET /agents/{agent_id}/spec` - Get agent specification
   - `GET /agents/manifest` - Get manifest as JSON
   - `POST /agents/manifest` - Generate and write manifest.yaml

2. **Create Pydantic schemas** in `packages/paracle_api/schemas/agents.py`:
   - `AgentMetadataResponse`
   - `AgentListResponse`
   - `AgentSpecResponse`
   - `ManifestResponse`
   - `ManifestWriteResponse`

3. **Refactor CLI** in `packages/paracle_cli/commands/agents.py`:
   - Replace direct service calls with HTTP requests via `httpx`
   - Add proper error handling for API connectivity
   - Keep Rich formatting for beautiful terminal output

4. **Add httpx dependency** to runtime dependencies (moved from dev-only)

5. **Create comprehensive tests** in `tests/unit/test_api_agents.py`

6. **Update documentation** in `docs/agent-discovery.md` with API usage

### Architecture

```
┌─────────────────────┐
│   REST API          │
│  (FastAPI)          │
│                     │
│  GET /agents        │  ← Single source of truth
│  GET /agents/{id}   │  ← All clients consume this
│  POST /manifest     │
└─────────┬───────────┘
          │
  ┌───────┼───────┐
  │       │       │
┌─▼──┐ ┌─▼──┐ ┌─▼──┐
│CLI │ │Web │ │IDE │
└────┘ └────┘ └────┘
```

**Benefits**:
- ✅ Consistency: One implementation shared by all clients
- ✅ Testability: API tested independently
- ✅ Extensibility: Easy to add new clients (web app, IDE plugins)
- ✅ Documentation: OpenAPI/Swagger automatic
- ✅ Separation: Clear boundaries between layers

### Consequences

#### Positive

✅ **Architectural Correctness**: Respects API First principle
✅ **Multi-Client Support**: Web, CLI, IDE plugins all use same API
✅ **Better Testing**: API can be tested independently
✅ **Auto-Documentation**: FastAPI generates OpenAPI/Swagger docs
✅ **Future-Proof**: Easy to add GraphQL, gRPC, WebSocket layers

#### Negative

⚠️ **Runtime Dependency**: CLI requires API to be running
⚠️ **Network Overhead**: HTTP calls add latency vs direct calls
⚠️ **Complexity**: More components (API server + CLI client)

#### Mitigations

- **For local use**: API can run embedded in CLI (future enhancement)
- **For development**: `uvicorn --reload` makes API startup instant
- **For production**: API runs as service, CLI is thin client
- **Error handling**: Clear messages when API is unreachable

### Implementation Details

**Files Created**:
- `packages/paracle_api/schemas/agents.py` (80 lines)
- `packages/paracle_api/routers/agents.py` (230 lines)
- `tests/unit/test_api_agents.py` (250 lines)

**Files Modified**:
- `packages/paracle_api/main.py` - Register agents router
- `packages/paracle_api/routers/__init__.py` - Export agents_router
- `packages/paracle_cli/commands/agents.py` - Refactored to use httpx
- `pyproject.toml` - Added httpx to runtime dependencies
- `docs/agent-discovery.md` - Added API documentation section

**Test Coverage**:
- ✅ GET /agents (list all)
- ✅ GET /agents/{id} (get one)
- ✅ GET /agents/{id}/spec (get spec content)
- ✅ GET /agents/manifest (manifest as JSON)
- ✅ POST /agents/manifest (write manifest.yaml)
- ✅ Error handling (404, 409, 500)

### Alternatives Considered

#### Alternative 1: Keep Direct Service Calls

**Pros**: Simpler, no API needed, faster
**Cons**: Violates API First principle, no web/IDE support, duplicates logic
**Decision**: Rejected - goes against core architectural principle

#### Alternative 2: Dual Mode (Direct + API)

**Pros**: Flexibility, works offline
**Cons**: Two code paths to maintain, inconsistency risk
**Decision**: Rejected - adds complexity without clear benefit

#### Alternative 3: Embedded API Mode

**Pros**: Best of both worlds, CLI can run API internally
**Cons**: Complex, requires process management
**Decision**: Consider for future enhancement (Phase 2)

### Migration Path

**For existing users**:
1. Start API server: `uvicorn paracle_api.main:app --reload`
2. Use CLI as before: `paracle agents list`

**For new users**:
- Quick start guide shows API + CLI setup
- Docker Compose file includes both services

### Success Metrics

✅ All CLI commands work via API
✅ API endpoints have 100% test coverage
✅ Documentation includes API usage examples
✅ OpenAPI docs accessible at `/docs`

### References

- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [API First Design](https://swagger.io/resources/articles/adopting-an-api-first-approach/)
- [RESTful API Design](https://restfulapi.net/)
- ADR-008: Agent Discovery System

### Related ADRs

- ADR-002: Hexagonal Architecture
- ADR-008: Agent Discovery System

---

## ADR-010: CLI Simplification - Remove `parac` Sub-command

**Date**: 2025-12-25
**Status**: Accepted
**Deciders**: Core Team

### Context

The CLI had a nested command structure where governance commands were under a `parac` sub-group:

```bash
# Old structure (verbose)
paracle parac status
paracle parac sync --manifest
paracle parac validate
paracle parac session start
```

This structure was redundant since:
1. `paracle` is the Paracle framework CLI
2. `.parac/` governance is a core feature, not a separate module
3. Users should interact with the framework naturally without extra nesting

### Decision

Promote governance commands to the root level:

```bash
# New structure (clean)
paracle status        # Show current project state
paracle sync          # Synchronize with project reality
paracle validate      # Validate workspace consistency
paracle session start # Start work session
paracle init          # Initialize new .parac/ workspace
```

**Backward Compatibility**: Keep the `parac` sub-group as hidden (deprecated) for existing scripts:

```bash
# Still works (deprecated, hidden from help)
paracle parac status  # → redirects to paracle status
```

### Implementation

1. **Commands promoted to root level**:
   - `status` - Show project state
   - `sync` - Synchronize with reality
   - `validate` - Validate consistency
   - `session` - Session management group
   - `init` - Initialize workspace (new)

2. **New command added**:
   - `paracle init [path]` - Creates `.parac/` structure

3. **Legacy support**:
   - `parac` group kept but hidden (`hidden=True`)
   - Same commands accessible via old path

4. **Hooks updated**:
   - All hooks now use `paracle sync` instead of `paracle parac sync`

### Consequences

#### Positive

✅ **Cleaner UX**: Less typing, more intuitive
✅ **Framework Identity**: Commands feel native to Paracle
✅ **Discoverability**: Root commands visible in `--help`
✅ **Backward Compatible**: Old scripts still work

#### Negative

⚠️ **Migration**: Users must update scripts (optional, old syntax works)
⚠️ **Documentation**: Must update all docs

#### Files Modified

- `packages/paracle_cli/commands/parac.py` - Restructured as standalone commands
- `packages/paracle_cli/main.py` - Register commands at root level
- `tests/unit/test_parac_cli.py` - Updated tests for new API + legacy tests
- `.git/hooks/pre-commit.ps1` - Use new command syntax
- `.parac/hooks/install-hooks.ps1` - Use new command syntax
- `.parac/hooks/install-hooks.sh` - Use new command syntax
- `.parac/hooks/pre-commit` - Use new command syntax
- `.parac/hooks/README.md` - Use new command syntax

### CLI Reference

| Old Command | New Command | Description |
|-------------|-------------|-------------|
| `paracle parac status` | `paracle status` | Show project state |
| `paracle parac sync` | `paracle sync` | Sync with reality |
| `paracle parac validate` | `paracle validate` | Validate workspace |
| `paracle parac session start` | `paracle session start` | Start session |
| `paracle parac session end` | `paracle session end` | End session |
| (none) | `paracle init` | Initialize workspace |

### Related ADRs

- ADR-009: .parac/ Governance in Framework

---

## ADR-011: LLM Provider Package Naming Convention

**Date**: 2025-12-31
**Status**: Accepted
**Deciders**: Core Team
**Phase**: Phase 2 - Multi-Provider & Multi-Framework

### Context

During Phase 2 implementation, we needed to decide on package naming for:
1. LLM provider abstractions (OpenAI, Anthropic, Google, Ollama)
2. Framework adapters (MSAF, LangChain, LlamaIndex)

**Conflicting Documentation:**
- `.roadmap/PHASE2_MULTI_PROVIDER.md` proposed: `paracle_llm/` and `paracle_frameworks/`
- `docs/architecture.md` (line 103) specified: `paracle_providers/` and `paracle_adapters/`
- Existing empty packages: `paracle_providers/` and `paracle_adapters/` already created

### Decision

**Use `paracle_providers` and `paracle_adapters`** (as per architecture.md).

**Rationale:**
1. **Consistency**: Aligns with existing architecture documentation
2. **Semantic Clarity**:
   - `providers` → LLM API providers (external services)
   - `adapters` → Framework adapters (hexagonal architecture pattern)
3. **Avoid Confusion**: Prevents potential conflict with future `paracle_llm` package for LLM-specific utilities
4. **Existing Structure**: Packages already exist in codebase

### Implementation

**Package Structure:**

```
packages/
├── paracle_providers/          # LLM Provider Abstraction
│   ├── base.py                 # LLMProvider protocol
│   ├── registry.py             # Provider registry
│   ├── exceptions.py           # Provider exceptions
│   ├── auto_register.py        # Auto-registration
│   ├── openai_provider.py      # OpenAI (GPT-4, GPT-3.5)
│   ├── anthropic_provider.py   # Anthropic (Claude 3.5, 3)
│   ├── google_provider.py      # Google (Gemini Pro)
│   └── ollama_provider.py      # Ollama (Local models)
│
└── paracle_adapters/           # Framework Adapters
    ├── base.py                 # FrameworkAdapter protocol
    ├── msaf_adapter.py         # Microsoft Agent Framework
    ├── langchain_adapter.py    # LangChain
    └── llamaindex_adapter.py   # LlamaIndex (optional)
```

**Provider Interface:**
- Protocol-based (`typing.Protocol`) for maximum flexibility
- Async-first design (all operations async)
- Streaming support as first-class citizen
- Graceful degradation (optional dependencies)

**Auto-Registration:**
- Providers register on import via `auto_register.py`
- Missing dependencies don't break imports
- Registry pattern for discovery

### Consequences

**Positive:**
- ✅ Clear separation: providers (external APIs) vs adapters (frameworks)
- ✅ Follows hexagonal architecture principles
- ✅ Consistent with existing documentation
- ✅ Extensible via Protocol (users can add providers)
- ✅ Graceful handling of missing dependencies

**Negative:**
- ⚠️ Requires updating `.roadmap/PHASE2_MULTI_PROVIDER.md` documentation
- ⚠️ Different from initial Phase 2 spec (but better aligned with architecture)

**Neutral:**
- Package naming is internal implementation detail
- Users interact via public API, not package names

### Metrics (Implementation)

**Phase 2 Progress (as of 2025-12-31):**
- ✅ Base protocol implemented (ChatMessage, LLMConfig, LLMResponse, StreamChunk)
- ✅ Provider registry with auto-registration
- ✅ 4 providers implemented (OpenAI, Anthropic, Google, Ollama)
- ✅ 30 unit tests (100% passing)
- ✅ UTC-aware datetime (no deprecation warnings)
- 📊 Test count: 255 total (+30 from Phase 1)

**Files Created:**
- `paracle_providers/base.py` (203 lines)
- `paracle_providers/registry.py` (115 lines)
- `paracle_providers/exceptions.py` (68 lines)
- `paracle_providers/auto_register.py` (49 lines)
- `paracle_providers/openai_provider.py` (289 lines)
- `paracle_providers/anthropic_provider.py` (242 lines)
- `paracle_providers/google_provider.py` (183 lines)
- `paracle_providers/ollama_provider.py` (248 lines)
- `tests/unit/test_provider_base.py` (154 lines)
- `tests/unit/test_provider_registry.py` (147 lines)

### Related ADRs

- ADR-002: Modular Monolith Architecture
- ADR-005: Hexagonal Architecture (Ports & Adapters)

### Next Steps

1. ✅ Implement framework adapters in `paracle_adapters/`
2. ✅ Implement MCP support in `paracle_tools/`
3. ✅ Update AgentFactory to use providers
4. ✅ Update Phase 2 documentation
5. ✅ Add integration tests with mocked API calls

---

## ADR-012: Agent Factory with Provider Integration

**Date**: 2025-12-31
**Status**: Accepted
**Deciders**: Core Team

### Context

Phase 2 requires integrating the provider registry with agent creation. Need to design how agents are instantiated with:
- Inheritance resolution (from Phase 1)
- Provider selection and instantiation (from Phase 2)
- Clean separation of concerns
- Flexibility for different use cases

Key requirements:
1. Agent creation should resolve inheritance before provider selection
2. Provider instantiation should be optional (for testing, dry-run, etc.)
3. Factory should provide utilities (validation, preview, chain inspection)
4. Temperature inheritance should handle default values correctly

### Decision

**Implement AgentFactory in `paracle_domain/factory.py`** with two creation modes:

1. **`create(spec)`**: Creates agent with resolved inheritance (no provider)
2. **`create_with_provider(spec, config)`**: Creates agent + provider instance

**Temperature Inheritance Fix:**
- Modified `_merge_specs()` in `inheritance.py` to detect default values
- Child temperature only overrides parent if != 0.7 (default)
- Same logic applied to all scalar fields with defaults

**Factory Features:**
- `validate_spec()`: Check inheritance without creating agent
- `get_inheritance_chain()`: Inspect inheritance chain
- `preview_resolved_spec()`: See final merged spec
- Metadata attachment: `_inheritance_chain`, `_inheritance_depth`, `_inheritance_warnings`

### Implementation

**Factory Constructor:**
```python
AgentFactory(
    spec_provider: Callable[[str], AgentSpec | None],  # Get parent specs
    provider_registry: Any | None = None,              # Optional provider registry
    max_inheritance_depth: int = 5,
    warn_depth: int = 3,
)
```

**Basic Usage:**
```python
# Without provider (testing, validation)
factory = AgentFactory(repository.get_spec)
agent = factory.create(spec)

# With provider (production)
factory = AgentFactory(repository.get_spec, ProviderRegistry)
agent, provider = factory.create_with_provider(spec, {"api_key": "..."})
```

**Temperature Inheritance Logic:**
```python
# Before (incorrect):
temperature = leaf.temperature  # Always uses child's default (0.7)

# After (correct):
merged_temperature = base.temperature
for child in specs[1:]:
    if child.temperature != 0.7:  # Not default
        merged_temperature = child.temperature
```

**Error Handling:**
- `InheritanceError`: Circular dependency, max depth, missing parent
- `ProviderNotAvailableError`: Provider not in registry
- `ValueError`: Provider registry not configured

### Consequences

**Positive:**
- ✅ Clean separation: inheritance resolution vs provider instantiation
- ✅ Flexible: can create agents without providers (testing)
- ✅ Utilities: validation, preview, chain inspection
- ✅ Correct inheritance: default values don't override parent values
- ✅ Well-tested: 16 unit tests covering all scenarios
- ✅ Type-safe: Full type hints with Protocol support

**Negative:**
- ⚠️ Complexity: Default value detection hardcoded for temperature (0.7)
- ⚠️ Coupling: Factory depends on ProviderRegistry (mitigated by Protocol)

**Neutral:**
- Factory follows existing patterns (Repository, Registry)
- Metadata attachment uses private attributes (future: proper metadata field)

### Metrics (Implementation)

**Files Created:**
- `paracle_domain/factory.py` (218 lines)
- `tests/unit/test_agent_factory.py` (413 lines)

**Files Modified:**
- `paracle_domain/__init__.py` (added exports)
- `paracle_domain/inheritance.py` (temperature inheritance fix)

**Test Coverage:**
- 16 new tests (100% passing)
- Scenarios covered:
  - Simple agent creation
  - Single-level inheritance
  - Multi-level inheritance (grandparent → parent → child)
  - Tools/metadata merging
  - Circular inheritance detection
  - Max depth enforcement
  - Missing parent detection
  - Provider selection and instantiation
  - Error conditions (provider unavailable, no registry)

**Phase 2 Completion:**
- Test count: 304 total (+79 from providers, adapters, MCP, factory)
- Python files: 67 (+3)
- Test files: 20 (+1)
- Code coverage: 87.5%
- **Phase 2: 100% COMPLETE** ✅

### Trade-offs

**Default Value Detection:**
- **Chosen**: Hardcode check `temperature != 0.7`
- **Alternative 1**: Store original Pydantic defaults in spec metadata
  - Pro: More robust
  - Con: Adds complexity, increases memory
- **Alternative 2**: Require explicit `temperature=None` to inherit
  - Pro: Explicit is better than implicit
  - Con: Breaking change, less ergonomic

**Rationale**: Pragmatic solution for v0.0.1. Can enhance with metadata in future.

### Related ADRs

- ADR-003: Agent Inheritance System
- ADR-011: LLM Provider Package Naming

### Next Steps

1. ✅ Phase 2 Complete
2. 📋 Begin Phase 3: Orchestration Engine
3. 📋 Consider enhancing inheritance with explicit field metadata (post-v0.0.1)
