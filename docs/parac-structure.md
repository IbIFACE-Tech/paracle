# Project Structure Reference

Complete structure of Paracle v0.0.1 after Phase 0.

## Root Structure

```
paracle-lite/
├── .parac/              # Paracle workspace (configuration, memory, policies)
├── .github/             # GitHub configuration (CI/CD)
├── packages/            # Source code (modular packages)
├── tests/               # Test suite
├── docs/                # Documentation
├── examples/            # Example code
├── pyproject.toml       # Project configuration
├── Makefile            # Developer commands
├── README.md           # Project README
├── CONTRIBUTING.md     # Contribution guidelines
├── LICENSE             # Apache 2.0 license
└── .gitignore         # Git ignore patterns
```

## Detailed Structure

### `.parac/` - Paracle Workspace

```
.parac/
├── project.yaml                      # Project configuration (MANUAL)
├── manifest.yaml                     # Workspace state (AUTO-GENERATED)
├── changelog.md                      # Project changelog
├── PHASE0_COMPLETE.md               # Phase 0 completion summary
├── GOVERNANCE.md                     # Governance rules
├── STRUCTURE.md                      # This file
├── MAINTENANCE.md                    # Maintenance guide
├── USING_PARAC.md                    # Complete usage guide
├── UNIVERSAL_AI_INSTRUCTIONS.md      # IDE-agnostic AI instructions
├── CONFIG_FILES.md                   # Explanation of config files
│
├── roadmap/                          # Project roadmap
│   ├── roadmap.yaml                 # Canonical roadmap
│   ├── constraints.yaml             # Technical/timeline constraints
│   └── decisions.md                 # Architecture Decision Records (ADRs)
│
├── agents/                           # Agent definitions
│   ├── manifest.yaml                # Agent registry (in workspace manifest.yaml)
│   ├── SKILL_ASSIGNMENTS.md         # Skills per agent
│   └── specs/                       # Detailed agent specifications
│       ├── architect.md             # System architect agent
│       ├── coder.md                 # Coder agent
│       ├── documenter.md            # Documenter agent
│       ├── pm.md                    # Project manager agent
│       ├── reviewer.md              # Reviewer agent
│       └── tester.md                # Tester agent
│
├── memory/                           # Project memory
│   ├── index.yaml                   # Memory index
│   ├── context/                     # Current context
│   │   ├── current_state.yaml       # Project state
│   │   └── open_questions.md        # Open questions
│   ├── knowledge/                   # Accumulated knowledge
│   │   ├── architecture.md
│   │   └── glossary.md
│   ├── logs/                        # Action logs
│   │   ├── agent_actions.log        # Agent actions
│   │   ├── decisions.log            # Important decisions
│   │   └── sessions/                # Session logs
│   └── summaries/                   # Periodic summaries
│
├── policies/                         # Project policies
│   ├── CODE_STYLE.md                # Code style guide
│   ├── TESTING.md                   # Testing policy
│   ├── SECURITY.md                  # Security policy
│   ├── policy-pack.yaml             # Active policies
│   ├── approvals.yaml               # Approval workflows
│   └── security.yaml                # Security policy (deprecated, use SECURITY.md)
│
├── integrations/                     # External integrations
│   ├── README.md                    # Integration guide
│   └── ide/                         # IDE configurations
│       ├── _manifest.yaml           # Generated configs manifest
│       ├── .cursorrules             # Cursor
│       ├── .clinerules              # Cline
│       ├── .windsurfrules           # Windsurf
│       ├── CLAUDE.md                # Claude Code
│       └── copilot-instructions.md  # GitHub Copilot
│
├── workflows/                        # Workflow definitions
│   ├── manifest.yaml                # Workflow registry
│   └── definitions/                 # YAML workflow definitions
│
├── tools/                            # Custom tools
│   └── manifest.yaml                # Tool registry
│
├── adapters/                         # Adapter configurations
│   ├── orchestrators.yaml           # Orchestrator adapters (MSAF, LangChain, etc.)
│   ├── model_providers.yaml         # LLM provider adapters
│   └── languages.yaml               # Language-specific configs
│
├── memory/                           # Project memory
│   ├── index.yaml                   # Memory index
│   ├── context/                     # Current context
│   │   ├── current_state.yaml      # Project state snapshot
│   │   └── open_questions.md       # Unresolved questions
│   ├── knowledge/                   # Durable knowledge
│   │   └── domain.md               # Domain knowledge
│   └── summaries/                   # Phase summaries
│       └── phase_0_completion.md   # Phase 0 summary
│
├── logs/                            # Logs d'exécution
│   ├── README.md                   # Documentation des logs
│   ├── .gitignore                  # Ignorer les fichiers de log
│   ├── agents/                     # Logs spécifiques aux agents
│   ├── workflows/                  # Logs des workflows
│   └── errors/                     # Logs d'erreurs
│
├── tools/                           # Outils et plugins
│   ├── README.md                   # Documentation des outils
│   ├── registry.yaml               # Registre des outils disponibles
│   └── custom/                     # Outils personnalisés
│
├── workflows/                       # Définitions de workflows
│   ├── README.md                   # Documentation des workflows
│   ├── catalog.yaml                # Catalogue des workflows
│   ├── templates/                  # Templates de workflows
│   │   └── hello_world.yaml       # Exemple de workflow
│   └── definitions/                # Workflows du projet
│
└── runs/                            # Execution history (future)
```

### `packages/` - Source Code

```
packages/
├── paracle_core/                    # Core utilities
│   └── __init__.py                 # Package init
│
├── paracle_domain/                  # Domain models (business logic)
│   ├── __init__.py
│   └── models.py                   # Agent, Workflow models
│
├── paracle_store/                   # Persistence layer (future)
│   └── __init__.py
│
├── paracle_events/                  # Event bus (future)
│   └── __init__.py
│
├── paracle_providers/               # LLM providers (future)
│   └── __init__.py
│
├── paracle_adapters/                # Framework adapters (future)
│   └── __init__.py
│
├── paracle_orchestration/           # Workflow orchestration (future)
│   └── __init__.py
│
├── paracle_tools/                   # Tool management (future)
│   └── __init__.py
│
├── paracle_api/                     # REST API (future)
│   └── __init__.py
│
└── paracle_cli/                     # Command-line interface
    ├── __init__.py
    └── main.py                     # CLI commands
```

### `tests/` - Test Suite

```
tests/
├── conftest.py                     # Pytest configuration & fixtures
├── unit/                           # Unit tests
│   ├── test_domain.py             # Domain model tests
│   └── test_cli.py                # CLI tests
└── integration/                    # Integration tests (future)
```

### `docs/` - Documentation

```
docs/
├── getting-started.md              # Getting started guide
└── architecture.md                 # Architecture documentation
```

### `examples/` - Example Code

```
examples/
├── README.md                       # Examples overview
├── hello_world_agent.py           # Basic agent example
└── agent_inheritance.py           # Inheritance example
```

### `.github/` - GitHub Configuration

```
.github/
└── workflows/
    ├── ci.yml                     # CI pipeline (test, lint, security)
    └── release.yml                # Release pipeline
```

### `.vscode/` - Visual Studio Code Configuration

```
.vscode/
├── settings.json                  # Workspace settings
├── launch.json                    # Debug configurations
├── tasks.json                     # Build and test tasks
├── extensions.json                # Recommended extensions
└── paracle.code-snippets          # Code snippets
```

### `.claude/` - Claude Desktop Configuration

```
.claude/
├── README.md                      # Configuration overview
├── project_context.md             # Project context and architecture
├── custom_instructions.md         # Coding guidelines and standards
├── code_snippets.md               # Ready-to-use code examples
└── prompts.md                     # Common task prompts
```

## File Counts

- **Total directories**: 35+
- **Total files**: 65+
- **Python packages**: 10
- **Documentation files**: 20+
- **Configuration files**: 25+
- **Test files**: 3 (with more coming)

## Key Files

### Configuration

- `pyproject.toml` - Project dependencies and configuration
- `Makefile` - Developer commands
- `.gitignore` - Git ignore patterns

### Documentation

- `README.md` - Project overview
- `CONTRIBUTING.md` - Contribution guidelines
- `LICENSE` - Apache 2.0 license

### Source Code

- `packages/paracle_domain/models.py` - Core domain models
- `packages/paracle_cli/main.py` - CLI implementation

### Tests

- `tests/unit/test_domain.py` - Domain model tests
- `tests/unit/test_cli.py` - CLI tests
- `tests/conftest.py` - Test fixtures

### Examples

- `examples/hello_world_agent.py` - Basic example
- `examples/agent_inheritance.py` - Inheritance example

## Size Estimate

- **Lines of code**: ~2,000+
- **Lines of documentation**: ~3,000+
- **Lines of configuration**: ~1,500+
- **Total**: ~6,500+ lines

## Navigation Tips

### Starting Points

1. **Learn**: `README.md` → `docs/getting-started.md`
2. **Develop**: `Makefile` → `packages/`
3. **Test**: `tests/` → `make test`
4. **Configure**: `.parac/project.yaml` → `.parac/roadmap/`

### Common Paths

- New feature: `packages/paracle_*`
- New test: `tests/unit/` or `tests/integration/`
- New example: `examples/`
- New documentation: `docs/`
- Configuration: `.parac/`

## Growth Path

### Phase 1 (Core Domain)

- More files in `packages/paracle_domain/`
- More files in `packages/paracle_store/`
- More files in `packages/paracle_events/`
- More tests in `tests/unit/`

### Phase 2 (Multi-Provider)

- More files in `packages/paracle_providers/`
- More files in `packages/paracle_adapters/`
- Integration tests in `tests/integration/`

### Phase 3 (Orchestration & API)

- More files in `packages/paracle_orchestration/`
- More files in `packages/paracle_api/`
- API documentation

---

**Last Updated**: 2025-12-24
**Phase**: 0 (Foundation) ✅
**Status**: Complete
