# Claude Code Configuration for Paracle

This directory contains **production-grade** Claude Code configuration optimized for designing and building the Paracle multi-agent framework.

## Design Philosophy

This configuration transforms Claude into a **senior architecture committee** with:

- Framework Architect perspective (API design, extensibility)
- Security & Compliance Engineer perspective (ISO 42001, audit)
- Runtime & Performance Engineer perspective (scalability, operations)

## Structure

```text
.claude/
├── settings.json              # Permissions, environment, model config
├── CLAUDE.md                  # Project memory (auto-loaded)
├── README.md                  # This file
├── rules/                     # Modular instruction files
│   ├── code-style.md          # Python code standards
│   ├── testing.md             # Testing patterns
│   ├── architecture.md        # Hexagonal architecture
│   ├── framework-design.md    # Framework design principles
│   ├── anti-hallucination.md  # Cognitive rigor protocol
│   ├── multi-perspective.md   # 3-perspective analysis
│   └── session-protocol.md    # Session management
└── legacy/                    # Archived Claude Desktop files
```

## Key Files

### CLAUDE.md

Project memory automatically loaded. Contains:

- Senior architect role definition
- Project vision and roadmap overview
- Architecture diagrams
- Cognitive framework (9 thinking layers)
- Multi-perspective analysis protocol
- Quality gates and anti-hallucination rules

### settings.json

Extended permissions for framework development:

- **Allow**: All dev tools (uv, pytest, ruff, black, mypy, git read ops)
- **Deny**: Secrets, credentials, destructive commands
- **Ask**: Git writes, dependency changes, governance files

### rules/

Modular instructions imported via `@.claude/rules/`:

| File | Purpose |
| ---- | ------- |
| code-style.md | Type hints, Pydantic, formatting |
| testing.md | pytest patterns, coverage targets |
| architecture.md | Hexagonal architecture, DDD |
| framework-design.md | Long-lived framework principles |
| anti-hallucination.md | Uncertainty handling, verification |
| multi-perspective.md | 3-role analysis protocol |
| session-protocol.md | Session start/end rituals |

## Cognitive Framework

### 9 Thinking Layers

1. Vision - Problem and purpose
2. Invariants - What must always be true
3. Abstract Model - Conceptual entities
4. Logical Architecture - Components and boundaries
5. API/Interfaces - Contracts and protocols
6. Runtime/Orchestration - Execution flow
7. Security & Policies - Access and compliance
8. Observability - Metrics and tracing
9. Evolution - Extensibility and compatibility

### 3-Perspective Analysis

For significant decisions:

1. **Framework Architect**: API stability, extensibility, maintenance
2. **Security Engineer**: ISO 42001, audit trails, access control
3. **Runtime Engineer**: Performance, scalability, operations

Then synthesize into a unified decision.

## Anti-Hallucination Protocol

When uncertain:

1. State explicitly: "I am uncertain about X because Y"
2. Provide options with trade-offs
3. Never invent APIs or capabilities
4. Verify before claiming

## Session Protocol

### Start

```text
I am continuing from the current project state.
Source of truth: .parac/ and .roadmap/
I will not reintroduce rejected decisions.
```

### End

Produce summary with:

- Decisions taken
- Rejected options (with reasons)
- Open questions
- Next logical step

## Integration with .parac/

| Directory | Purpose |
| --------- | ------- |
| .parac/ | Project governance (roadmap, policies, memory) |
| .roadmap/ | Complete roadmap v0.0.1 to v1.0.0 |
| .claude/ | Claude Code configuration |

## Authoritative Sources

| File | Purpose |
| ---- | ------- |
| .roadmap/ROADMAP_GLOBALE.yaml | Complete 50-week roadmap |
| .parac/roadmap/decisions.md | Architecture Decision Records |
| .parac/policies/policy-pack.yaml | Active policies |
| .parac/memory/context/current_state.yaml | Current state |

## Quality Standards

- Test coverage: >90%
- Documentation: 100%
- Security: ISO 42001 compliant
- API stability: Semantic versioning
- All decisions traceable to requirements
