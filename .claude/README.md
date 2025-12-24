# Claude Code Configuration for Paracle

This directory contains configuration for Claude Code (CLI) when working with Paracle.

## Structure

```
.claude/
├── settings.json          # Permissions, environment, and tool configuration
├── CLAUDE.md              # Project memory and instructions (auto-loaded)
├── README.md              # This file
├── rules/                 # Modular instruction files
│   ├── code-style.md      # Python code style guidelines
│   ├── testing.md         # Testing patterns and conventions
│   └── architecture.md    # Architecture guidelines
└── legacy/                # Legacy Claude Desktop files (archived)
```

## Files

### settings.json
Project-level configuration including:
- **Permissions**: Allowed/denied/ask tools and file patterns
- **Environment**: Variables for all Claude Code sessions
- **Model**: Default model selection
- **Attribution**: Commit and PR message templates

### CLAUDE.md
Project memory automatically loaded by Claude Code. Contains:
- Project overview and architecture
- Development commands
- Code standards quick reference
- Domain model examples
- Feature implementation workflow

### rules/
Modular instruction files for specific concerns:
- **code-style.md**: Type hints, Pydantic, formatting, naming conventions
- **testing.md**: pytest patterns, fixtures, async testing, coverage
- **architecture.md**: Hexagonal architecture, repository pattern, events

## Integration with .parac Workspace

The `.claude/` directory complements the `.parac/` workspace:

| Directory | Purpose |
|-----------|---------|
| `.parac/` | Project governance (roadmap, policies, memory) |
| `.claude/` | Claude Code specific configuration |

Together they enable:
- IDE-agnostic project configuration (`.parac`)
- Claude Code optimized development experience (`.claude`)
- Consistent standards across tools

## Usage

Claude Code automatically reads:
1. `CLAUDE.md` - loaded at session start
2. `settings.json` - applied permissions and environment
3. `rules/*.md` - referenced via `@.claude/rules/` imports

## Related Documentation

- Project Overview: [README.md](../README.md)
- Architecture: [docs/architecture.md](../docs/architecture.md)
- Getting Started: [docs/getting-started.md](../docs/getting-started.md)
- Contributing: [CONTRIBUTING.md](../CONTRIBUTING.md)
- Roadmap: [.parac/roadmap/roadmap.yaml](../.parac/roadmap/roadmap.yaml)
