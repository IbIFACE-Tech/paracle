# Paracle AI Instructions for GitHub Copilot

# Auto-generated from .parac/ - DO NOT EDIT MANUALLY

# Regenerate with: paracle ide sync --copy

# Generated: 2026-01-05T14:09:10.710168

#

# Read First: .parac/UNIVERSAL_AI_INSTRUCTIONS.md (works with ANY IDE)

## MANDATORY PRE-FLIGHT CHECKLIST

**Before ANY implementation task**, complete the checklist:

**READ THIS FIRST: [.parac/PRE_FLIGHT_CHECKLIST.md](../.parac/PRE_FLIGHT_CHECKLIST.md)**

**Quick version (4 minutes):**

```
1. Read GOVERNANCE.md
2. Check current_state.yaml (phase, progress, in_progress)
3. Consult roadmap.yaml (phase focus, deliverables, priorities)
4. Check open_questions.md (blockers, related questions)
5. VALIDATE: Task in roadmap? Current phase? Priority? Dependencies?
6. Select agent to run (see specs/{agent}.md for capabilities)
7. Check policies (CODE_STYLE, TESTING, SECURITY)
8. AFTER: Log to agent_actions.log
9. AFTER: Update current_state.yaml if milestone reached
```

**This ensures you work on THE RIGHT THING at the RIGHT TIME.**

## Core Principle

> **`.parac/` is the single source of truth. Read it. Follow it. Log to it.**

## File Organization

> **Before creating ANY file in `.parac/`, consult [.parac/STRUCTURE.md](.parac/STRUCTURE.md) for correct placement.**

**Key Rules**:

- Operational data (databases) -> `.parac/memory/data/*.db`
- Logs -> `.parac/memory/logs/*.log`
- Knowledge -> `.parac/memory/knowledge/*.md`
- Decisions (ADRs) -> `.parac/roadmap/decisions.md`
- Agent specs -> `.parac/agents/specs/*.md`
- Config -> `.parac/project.yaml` or `.parac/config/`
- Execution artifacts -> `.parac/runs/` (gitignored)

**See [.parac/STRUCTURE.md](.parac/STRUCTURE.md) for complete structure and validation rules.**

## MANDATORY: Pre-Flight Checklist

**Before ANY implementation task:**

**Complete [.parac/PRE_FLIGHT_CHECKLIST.md](.parac/PRE_FLIGHT_CHECKLIST.md)** (~4 minutes)

This checklist ensures:

- You're working on the RIGHT task
- At the RIGHT phase
- With the RIGHT priority
- In the RIGHT sequence

**Quick version:**

1. Read `.parac/GOVERNANCE.md` - Governance rules
2. Check `.parac/memory/context/current_state.yaml` - Current state
3. Consult `.parac/roadmap/roadmap.yaml` - Phase & priorities
4. Verify `.parac/memory/context/open_questions.md` - Blockers
5. **VALIDATE**: Task in roadmap? Correct phase? Priority? Dependencies?
6. Select which agent to run (see `.parac/agents/specs/{agent}.md`)
7. Check policies (CODE_STYLE, TESTING, SECURITY)

**If Task NOT in Roadmap**: STOP - Add to roadmap first via PM Agent before proceeding.

**Before ANY action**, you MUST:

1. `.parac/GOVERNANCE.md` - Governance rules and dogfooding context
2. `.parac/agents/manifest.yaml` - Available agents
3. `.parac/memory/context/current_state.yaml` - Current project state
4. `.parac/roadmap/roadmap.yaml` - Phases and priorities
5. `.parac/PRE_FLIGHT_CHECKLIST.md` - Mandatory task validation
6. Determine which agent to run (see `.parac/agents/specs/{agent_id}.md`)

## Current Project State

- **Project**: paracle-lite v0.0.1
- **Phase**: phase_4 - API Server & CLI Enhancement (75%)
- **Status**: in_progress
- **Focus**: REST API server with uvicorn, Workflow execution endpoints (async/sync), CLI command enhancements, MCP tool integration, Command-line workflow management, IDE integration and templates

## Available Agents

### System Architect Agent (`architect`)

- **Role**: System architecture design, module structure, and technical decision making.
- **Capabilities**: architecture design, technical decisions, documentation
- **Description**: System architecture design, module structure, and technical decision making.

### Coder Agent (`coder`)

- **Role**: Implementation of features, writing production-quality code following project standards and best practices.
- **Capabilities**: code implementation, code quality, integration
- **Description**: Implementation of features, writing production-quality code following project standards and best practices.

### Documenter Agent (`documenter`)

- **Role**: Technical documentation, API references, user guides, and knowledge management.
- **Capabilities**: documentation creation, knowledge management, quality assurance
- **Description**: Technical documentation, API references, user guides, and knowledge management.

### Project Manager Agent (`pm`)

- **Role**: Project coordination, roadmap management, progress tracking, and stakeholder communication.
- **Capabilities**: project planning, progress tracking, risk management, team coordination
- **Description**: Project coordination, roadmap management, progress tracking, and stakeholder communication.

### Reviewer Agent (`reviewer`)

- **Role**: Code review, quality assurance, and ensuring adherence to project standards and best practices.
- **Capabilities**: code review, quality assurance, knowledge transfer
- **Description**: Code review, quality assurance, and ensuring adherence to project standards and best practices.

### Tester Agent (`tester`)

- **Role**: Test design, implementation, and quality validation ensuring comprehensive coverage and reliability.
- **Capabilities**: test design, test implementation, quality validation
- **Description**: Test design, implementation, and quality validation ensuring comprehensive coverage and reliability.

### Release Manager Agent (`releasemanager`)

- **Role**: Git workflows, versioning, releases, and deployment automation.
- **Capabilities**: semantic versioning, git management, changelog generation, CI/CD integration, package publishing
- **Description**: Manages git workflows, conventional commits enforcement, semantic versioning, changelog generation, PyPI/Docker publishing, and release orchestration from commit to production.

## Governance Rules

## Contexte : Paracle concoit Paracle

Ce projet utilise une approche **meta** : nous utilisons le framework Paracle pour concevoir Paracle lui-meme.

```
+-------------------------------------------------------------+
|                    PARACLE FRAMEWORK                        |
|                      packages/                              |
|                                                             |
|   Le PRODUIT que nous developpons                          |
|   - Code source du framework                                |
|   - Genere les .parac/ pour les utilisateurs              |
+-------------------------------------------------------------+
                          v genere
+-------------------------------------------------------------+
|                   .parac/ WORKSPACE                         |
|                  (Cote utilisateur)                         |
|                                                             |
|   Ici : Notre propre utilisation du framework              |
|   - Gouvernance de notre developpement                     |
|   - Source de verite pour le projet Paracle lui-meme      |
+-------------------------------------------------------------+
```

**Nous sommes a la fois developpeurs ET utilisateurs du framework.**

---

## Principe Fondamental

> **Le repertoire `.parac/` est la source unique et immuable de verite pour le projet.**

Ce `.parac/` est notre **dogfooding** - il represente ce qu'un utilisateur du framework aurait pour gerer son projet.

Toute information concernant l'etat du projet, les decisions, les politiques, et la memoire du projet DOIT etre refletee dans `.parac/`. Aucune information critique ne doit exister uniquement dans la memoire d'un agent IA ou dans des conversations.

---

## Regles de Gouvernance

### Regle 1: Tracabilite Totale

Toute decision architecturale, tout changement de scope, toute modification de roadmap DOIT etre documentee dans `.parac/`.

| Type de Changement | Fichier a Mettre a Jour |

## Open Questions

- Q1: Agent Inheritance Depth Limit
- Q2: Event Store Implementation
- Q3: API Versioning Strategy
- Q4: Tool Calling Interface
- Q5: Memory Management Strategy

## Logging Actions

**MANDATORY**: After EVERY significant action, log to `.parac/memory/logs/agent_actions.log`:

**Format**: `[TIMESTAMP] [AGENT] [ACTION] Description`

**Example**:

```
[2026-01-04 15:30:00] [CoderAgent] [IMPLEMENTATION] Implemented webhook system in packages/paracle_events/webhooks.py
[2026-01-04 15:45:00] [TesterAgent] [TEST] Added unit tests for webhook delivery
[2026-01-04 16:00:00] [ReviewerAgent] [REVIEW] Reviewed PR #42 - webhook implementation
```

**Action Types**:

- `IMPLEMENTATION` - Code implementation
- `TEST` - Test creation/modification
- `BUGFIX` - Bug correction
- `REFACTORING` - Code refactoring
- `REVIEW` - Code review
- `DOCUMENTATION` - Documentation update
- `DECISION` - Important decision (also log to `.parac/memory/logs/decisions.log`)
- `PLANNING` - Planning/roadmap updates
- `UPDATE` - .parac/ file updates

**Python Logging (optional)**:

```python
from paracle_core.governance import log_action, agent_context

with agent_context("CoderAgent"):
    log_action("IMPLEMENTATION", "Description of work done")
```

## Standard Workflow

### Before ANY Action

1. **Read GOVERNANCE.md**: Understand dogfooding context (Paracle develops Paracle)
2. **Check current_state.yaml**: Get current phase, status, progress
3. **Read roadmap.yaml**: Understand current phase priorities
4. **Identify Agent**: Select agent for task type
   - New feature -> `coder` (+ `architect` if design needed)
   - Bug fix -> `coder` (+ `tester` for validation)
   - Documentation -> `documenter`
   - Architecture -> `architect`
   - Planning -> `pm`
   - Review -> `reviewer`
5. **Read Agent Spec**: Load full spec from `.parac/agents/specs/{agent_id}.md`
6. **Check Assigned Skills**: See `.parac/agents/SKILL_ASSIGNMENTS.md`
7. **Run Agent**: Use `paracle agent run {agent} --task "description"` command

### During Work

1. **Agent Execution**: Agents are RUN via CLI (`paracle agent run`), not role-played
2. **AI Assistant Role**: Help users select the right agent and prepare execution
3. **Follow Agent Standards**: Understand agent's responsibilities from specs
4. **Check Policies**: Follow `.parac/policies/` (code style, testing, security)
5. **Update Memory Context**: Keep `.parac/memory/context/` current
6. **Track Progress**: Update task status in roadmap if applicable

### After Action (MANDATORY)

1. **Log Action**: Add entry to `.parac/memory/logs/agent_actions.log`
   - Format: `[TIMESTAMP] [AGENT] [ACTION] Description`
   - ALWAYS include file paths for code changes
2. **Update State**: Modify `.parac/memory/context/current_state.yaml` if needed
3. **Log Decisions**: Important decisions go to `.parac/memory/logs/decisions.log`
4. **Update Knowledge**: Add learnings to `.parac/memory/knowledge/*.md`
5. **Track Questions**: Unresolved issues go to `.parac/memory/context/open_questions.md`

### Configuration Files

- **project.yaml** (MANUAL): Project config - YOU can edit this
- **manifest.yaml** (AUTO-GENERATED): Workspace state - CLI generates, DON'T edit
- See `.parac/CONFIG_FILES.md` for complete explanation

## Agent Execution Options

### Option 1: Run Agent via CLI (Recommended)

**When to use**:

- Complex, multi-step tasks
- Need consistent agent behavior
- Automated workflows (CI/CD)
- Want agent's specialized skills executed

**How**:

```bash
# Run agent with task
paracle agent run coder --task "Implement user authentication"

# With options
paracle agent run coder --task "Fix bug #123" --mode safe --verbose

# See all options
paracle agent run --help
```

**Available modes**:

- `--mode safe` (default): Manual approvals, production-ready
- `--mode yolo`: Auto-approve all gates, CI/CD friendly
- `--mode sandbox`: Isolated execution environment
- `--mode review`: Mandatory human approval

**See**: [content/docs/agent-run-quickref.md](../content/docs/agent-run-quickref.md) for complete guide

### Option 2: Manual Implementation Following Agent Standards

**When to use**:

- Simple, straightforward tasks
- Agent execution not available
- Real-time AI assistant help
- Rapid prototyping

**How**:

1. Read agent spec: `.parac/agents/specs/{agent}.md`
2. Understand agent's responsibilities
3. Follow agent's assigned skills
4. Implement according to standards
5. Log action as that agent

**Example**:

```python
# Read .parac/agents/specs/coder.md first
# Then implement following CoderAgent standards:
# - Python 3.10+ with type hints
# - Pydantic v2 for models
# - Google-style docstrings
# - pytest for testing

# After implementation, log:
# [2026-01-06 10:30:00] [CoderAgent] [IMPLEMENTATION] Implemented auth in packages/paracle_api/auth.py
```

**Key**: Even when implementing manually, **follow agent standards** from `.parac/agents/specs/{agent}.md`

## Governance Tools & Commands

### Roadmap-State Synchronization

**Check alignment between roadmap and current state:**

```bash
paracle sync --roadmap
```

This detects:

- Phase name/status mismatches
- Completion % differences
- Missing/extra deliverables
- Metric inconsistencies

**See [content/docs/roadmap-state-sync.md](../content/docs/roadmap-state-sync.md) for details.**

### Governance Validation

**Validate all .parac/ files:**

```bash
paracle validate
```

Checks:

- YAML syntax
- Required files exist
- Roadmap-state alignment
- File permissions

### Session Management

**Start a session:**

```bash
paracle session start "Feature: Add X"
```

**End session and checkpoint:**

```bash
paracle session end
```

### API Keys Configuration

**Configure LLM provider API keys** for your project:

1. Copy example: `cp .env.example .env`
2. Add keys to `.env`: `OPENAI_API_KEY=sk-...`
3. Never commit `.env` to git!

**See [content/docs/api-keys.md](../content/docs/api-keys.md) for:**

- 12+ provider setup guides
- Security best practices
- Docker/production deployment
- Troubleshooting

## Essential .parac/ Files

| File                                           | Purpose                              | When to Read                            |
| ---------------------------------------------- | ------------------------------------ | --------------------------------------- |
| **`.parac/GOVERNANCE.md`**                     | Governance rules, dogfooding context | ALWAYS first                            |
| **`.parac/PRE_FLIGHT_CHECKLIST.md`**           | **NEW: Mandatory task validation**   | **Before ANY implementation**           |
| **`.parac/UNIVERSAL_AI_INSTRUCTIONS.md`**      | Universal instructions (any IDE)     | Setup / reference                       |
| **`.parac/USING_PARAC.md`**                    | Complete 20+ section guide           | Deep understanding                      |
| **`.parac/CONFIG_FILES.md`**                   | project.yaml vs manifest.yaml        | When confused about config              |
| **`.parac/STRUCTURE.md`**                      | Complete .parac/ structure           | Understanding organization              |
| **`.parac/agents/manifest.yaml`**              | Agent registry                       | Before selecting agent                  |
| **`.parac/agents/specs/{agent}.md`**           | Agent detailed specs                 | After selecting agent                   |
| **`.parac/agents/SKILL_ASSIGNMENTS.md`**       | Skills per agent                     | Understanding capabilities              |
| **`.parac/memory/context/current_state.yaml`** | Project state                        | ALWAYS (before action)                  |
| **`.parac/memory/context/open_questions.md`**  | Open questions                       | When blocked                            |
| **`.parac/memory/knowledge/architecture.md`**  | Architecture knowledge               | Design decisions                        |
| **`.parac/memory/knowledge/glossary.md`**      | Project glossary                     | Term clarification                      |
| **`.parac/memory/logs/agent_actions.log`**     | Action history                       | Understanding changes                   |
| **`.parac/memory/logs/decisions.log`**         | Important decisions                  | Context for choices                     |
| **`.parac/roadmap/roadmap.yaml`**              | Roadmap and phases                   | Understanding priorities                |
| **`.parac/roadmap/decisions.md`**              | ADRs (Architecture Decision Records) | Design rationale                        |
| **`.parac/policies/CODE_STYLE.md`**            | Code style guide                     | Before coding                           |
| **`.parac/policies/TESTING.md`**               | Testing policy                       | Before writing tests                    |
| **`.parac/policies/SECURITY.md`**              | Security policy                      | Security-sensitive code                 |
| **`content/docs/api-keys.md`**                 | **NEW: API key management guide**    | **Setting up LLM providers**            |
| **`content/docs/roadmap-state-sync.md`**       | **NEW: Roadmap sync guide**          | **Understanding governance automation** |

## Rules

**DO:**

- **ALWAYS read `.parac/GOVERNANCE.md` first** - Understand dogfooding context
- **Check `.parac/memory/context/current_state.yaml`** - Know current state
- **Read agent spec** to understand capabilities (`.parac/agents/specs/{agent}.md`)
- **Run agent via CLI**: `paracle agent run {agent} --task "..."`
- **Understand agent's skills** (see `.parac/agents/SKILL_ASSIGNMENTS.md`)
- **Log EVERY significant action** to `.parac/memory/logs/agent_actions.log`
- **Include file paths** in log entries for code changes
- **Respect policies** in `.parac/policies/` (code style, testing, security)
- **Update current_state.yaml** after significant progress
- **Log decisions** to `.parac/memory/logs/decisions.log` for important choices
- **Track questions** in `.parac/memory/context/open_questions.md` when blocked
- **Edit project.yaml** for manual configuration changes
- **Use `paracle sync`** to regenerate manifest.yaml (never edit directly)

**DON'T:**

- **Never skip reading GOVERNANCE.md** - It's the foundation
- **Never edit manifest.yaml manually** - Use `paracle sync` instead
- **Never duplicate agent definitions** - Agents are defined in `.parac/agents/`
- **Never ignore current_state.yaml** - It's the source of truth for project status
- **Never skip logging actions** - Traceability is mandatory
- **Never create custom governance rules** - Follow existing governance
- **Never assume context** - Always read .parac/ files first
- **Never work on wrong phase** - Check roadmap.yaml for current priorities
- **Never roleplay as agents** - Agents are executable programs, not personas to adopt

## GitHub Copilot Features for .parac/ Integration

### Chat Commands

**Use Copilot Chat for context-aware assistance:**

- **`/explain`** - Explain selected code
- **`/fix`** - Fix issues in code
- **`/tests`** - Generate tests for code
- **`/doc`** - Add documentation
- **`@workspace`** - Reference workspace files

### Leveraging .parac/ with @workspace

**Before starting ANY task - Check governance:**

```
@workspace Open .parac/GOVERNANCE.md and explain the governance rules
@workspace What's the current state in .parac/memory/context/current_state.yaml?
@workspace What phase are we in? Check .parac/roadmap/roadmap.yaml
```

**When adopting agent persona:**

```
@workspace Which agent in .parac/agents/manifest.yaml should I use for [task]?
@workspace Show me .parac/agents/specs/coder.md agent responsibilities
@workspace What skills does this agent have? Check .parac/agents/SKILL_ASSIGNMENTS.md
```

**For implementation guidance:**

```
@workspace .parac/policies/CODE_STYLE.md - What's the code style?
@workspace .parac/policies/TESTING.md - What's the testing policy?
@workspace content/docs/architecture.md - Show me the architecture
```

**After actions - MANDATORY logging:**

```
User: "Add to .parac/memory/logs/agent_actions.log:
[2026-01-04 15:30:00] [CoderAgent] [IMPLEMENTATION] Implemented [feature] in packages/[path]"
```

### Code Generation with .parac/ Context

**1. Check current context:**

```
User: "Before implementing [feature], check:
- @workspace .parac/memory/context/current_state.yaml
- @workspace .parac/agents/specs/coder.md
- @workspace .parac/policies/CODE_STYLE.md"
```

**2. Generate code following standards:**

- Python 3.10+ with type hints
- Pydantic v2 for all models
- Hexagonal architecture (ports & adapters)
- Google-style docstrings
- pytest for testing

**3. After generation - LOG IT:**

```
User: "Log this implementation to .parac/memory/logs/agent_actions.log"
```

### Complete Workflow with Copilot Chat

**Step 1: Pre-work**

```
User: "I want to work on [task]. First, show me:
@workspace .parac/GOVERNANCE.md
@workspace .parac/memory/context/current_state.yaml
@workspace .parac/roadmap/roadmap.yaml

What should I know?"
```

**Step 2: Agent Selection**

```
User: "@workspace Which agent from .parac/agents/manifest.yaml should I run for [task type]?
Show me the spec from .parac/agents/specs/{agent}.md and how to run it"
```

**Step 3: Implementation**

```
User: "Run CoderAgent for [feature]:
paracle agent run coder --task 'Implement [feature]'

Or help me implement following:
- @workspace .parac/policies/CODE_STYLE.md
- @workspace content/docs/architecture.md"
```

**Step 4: Testing**

```
User: "/tests Generate tests following @workspace .parac/policies/TESTING.md"
```

**Step 5: Post-work (MANDATORY)**

```
User: "Add to @workspace .parac/memory/logs/agent_actions.log:
[TIMESTAMP] [AGENT] [ACTION] Description with file paths

Update @workspace .parac/memory/context/current_state.yaml if needed"
```

### Inline Suggestions Tips

**When Copilot suggests code:**

1. Check if it follows agent standards (see .parac/agents/specs/)
2. Verify code style compliance (see .parac/policies/CODE_STYLE.md)
3. Ensure architectural patterns (hexagonal architecture)
4. After accepting, log the change

**Use inline comments to guide Copilot:**

```python
# Following CoderAgent standards from .parac/agents/specs/coder.md
# Using Pydantic v2 as per .parac/policies/CODE_STYLE.md
class MyModel(BaseModel):
    # Copilot will suggest fields following these standards
```

### Chat Slash Commands for .parac/

- **`/explain @workspace .parac/agents/specs/coder.md`** - Understand agent responsibilities
- **`/fix`** (with context from .parac/policies/) - Fix code following policies
- **`/tests @workspace .parac/policies/TESTING.md`** - Generate tests per policy
- **`/doc`** (Google-style) - Add docstrings as per CODE_STYLE.md

### .parac/ Quick Reference for Copilot

| What You Need            | Use @workspace                                        |
| ------------------------ | ----------------------------------------------------- |
| Governance rules         | `@workspace .parac/GOVERNANCE.md`                     |
| Current project state    | `@workspace .parac/memory/context/current_state.yaml` |
| Current phase/priorities | `@workspace .parac/roadmap/roadmap.yaml`              |
| Available agents         | `@workspace .parac/agents/manifest.yaml`              |
| Agent responsibilities   | `@workspace .parac/agents/specs/{agent}.md`           |
| Agent skills             | `@workspace .parac/agents/SKILL_ASSIGNMENTS.md`       |
| Code style               | `@workspace .parac/policies/CODE_STYLE.md`            |
| Testing policy           | `@workspace .parac/policies/TESTING.md`               |
| Security policy          | `@workspace .parac/policies/SECURITY.md`              |
| Action log               | `@workspace .parac/memory/logs/agent_actions.log`     |
| Open questions           | `@workspace .parac/memory/context/open_questions.md`  |
| Architecture             | `@workspace content/docs/architecture.md`             |
| Config files explained   | `@workspace .parac/CONFIG_FILES.md`                   |

### Multi-Turn Conversation Pattern

```
User: "Let's work on [feature] following .parac/ governance"

Copilot: "I'll check the necessary files first..."
[Copilot reads GOVERNANCE.md, current_state.yaml, roadmap.yaml]

User: "Which agent should I adopt?"

Copilot: "Based on [task type], you should adopt CoderAgent"
[Copilot references .parac/agents/manifest.yaml and specs/coder.md]

User: "Show me the implementation plan"

Copilot: "Here's the plan following CoderAgent standards..."

User: "Implement it"

Copilot: [Generates code following all standards]

User: "Log this action"

Copilot: [Adds entry to agent_actions.log]
```

### Common Patterns

**Pattern 1: New Feature**

```
1. @workspace .parac/memory/context/current_state.yaml - Check state
2. @workspace .parac/agents/specs/coder.md - Adopt CoderAgent
3. @workspace .parac/policies/CODE_STYLE.md - Follow style
4. Implement feature
5. /tests - Generate tests
6. Log to agent_actions.log
```

**Pattern 2: Bug Fix**

```
1. @workspace .parac/GOVERNANCE.md - Understand dogfooding
2. /explain - Understand buggy code
3. @workspace .parac/agents/specs/coder.md - Follow CoderAgent
4. /fix - Fix the bug
5. /tests - Add regression test
6. Log to agent_actions.log
```

**Pattern 3: Documentation**

```
1. @workspace .parac/agents/specs/documenter.md - Adopt Documenter
2. @workspace .parac/policies/CODE_STYLE.md - Google-style docstrings
3. /doc - Generate documentation
4. Log to agent_actions.log
```

---

## Quick Start Checklist

Before your first action:

- [ ] Read `.parac/GOVERNANCE.md`
- [ ] Read `.parac/UNIVERSAL_AI_INSTRUCTIONS.md` (works with ANY IDE)
- [ ] Check `.parac/memory/context/current_state.yaml`
- [ ] Review `.parac/roadmap/roadmap.yaml` (current phase)
- [ ] Identify agent for task type
- [ ] Read agent spec from `.parac/agents/specs/{agent_id}.md`

During work:

- [ ] Follow agent standards and assigned skills
- [ ] Check `.parac/policies/` for guidelines
- [ ] Update memory context as needed

After action (MANDATORY):

- [ ] Log action to `.parac/memory/logs/agent_actions.log`
- [ ] Update `.parac/memory/context/current_state.yaml` if progress made
- [ ] Log decisions to `.parac/memory/logs/decisions.log` if applicable

---

## Common Errors to Avoid

1. **Not reading GOVERNANCE.md first** -> You miss the dogfooding context
2. **Skipping current_state.yaml** -> You work on wrong phase/outdated info
3. **Not logging actions** -> No traceability, breaks governance
4. **Editing manifest.yaml manually** -> It's auto-generated! Use `paracle sync`
5. **Confusing AI assistant with agents** -> Agents are programs to RUN, not roles to play
6. **Ignoring roadmap.yaml** -> You work on wrong priorities
7. **Not checking open_questions.md** -> You duplicate questions or miss blockers

---

## Related Documentation

- **[.parac/UNIVERSAL_AI_INSTRUCTIONS.md](../.parac/UNIVERSAL_AI_INSTRUCTIONS.md)** - Works with ANY IDE
- **[.parac/USING_PARAC.md](../.parac/USING_PARAC.md)** - Complete 20+ section guide
- **[.parac/CONFIG_FILES.md](../.parac/CONFIG_FILES.md)** - Configuration files explained
- **[.parac/GOVERNANCE.md](../.parac/GOVERNANCE.md)** - Governance rules
- **[.parac/STRUCTURE.md](../.parac/STRUCTURE.md)** - Complete structure
- **[.parac/agents/SKILL_ASSIGNMENTS.md](../.parac/agents/SKILL_ASSIGNMENTS.md)** - Skills per agent
- **[content/docs/architecture.md](../content/docs/architecture.md)** - Technical architecture

---

**Remember**: `.parac/` is your single source of truth. Always read it first.
