
# ChatGPT Instructions for Paracle Project
# Auto-generated from .parac/ - DO NOT EDIT MANUALLY
# Regenerate with: paracle ide sync --copy
# Generated: 2026-01-11T05:37:52.727081
#
# HOW TO USE:
# 1. Copy this entire file content
# 2. Paste at the start of your ChatGPT conversation
# 3. Or add to ChatGPT Custom Instructions
# 4. Or use in a ChatGPT GPT configuration


## Core Principle

> **`.parac/` is the single source of truth. Read it. Follow it. Log to it.**

## 🚨 MANDATORY: Pre-Flight Checklist

**Before ANY implementation task:**

📋 **Complete [.parac/PRE_FLIGHT_CHECKLIST.md](.parac/PRE_FLIGHT_CHECKLIST.md)** (~4 minutes)

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
6. Adopt agent persona from `.parac/agents/specs/{agent}.md`
7. Check policies (CODE_STYLE, TESTING, SECURITY)

**Before ANY action**, you MUST:
1. `.parac/GOVERNANCE.md` - Governance rules and dogfooding context
2. `.parac/agents/manifest.yaml` - Available agents
3. `.parac/memory/context/current_state.yaml` - Current project state
4. `.parac/roadmap/roadmap.yaml` - Phases and priorities
5. `.parac/PRE_FLIGHT_CHECKLIST.md` - Mandatory task validation
6. Adopt agent persona from `.parac/agents/specs/{agent_id}.md`



## Current Project State

- **Project**: paracle-lite v1.0.3
- **Phase**: phase_10 - Governance & v1.0 Release (0%)
- **Status**: in_progress



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

### QA Agent (Senior QA Architect) (`qa`)

- **Role**: Quality Assurance architecture, test strategy design, quality metrics tracking, and comprehensive quality validation across the entire software development lifecycle.
- **Capabilities**: quality strategy & architecture, test planning & design, quality assurance & validation, process improvement, team leadership & mentoring
- **Description**: Quality Assurance architecture, test strategy design, quality metrics tracking, and comprehensive quality validation across the entire software development lifecycle.

### Release Manager Agent (`releasemanager`)

- **Role**: Manages git workflows, semantic versioning, releases, changelogs, and deployment automation for the Paracle project.
- **Capabilities**: version management, git workflow, release process, bug/feature tracking
- **Description**: Manages git workflows, semantic versioning, releases, changelogs, and deployment automation for the Paracle project.

### Reviewer Agent (`reviewer`)

- **Role**: Code review, quality assurance, and ensuring adherence to project standards and best practices.
- **Capabilities**: code review, quality assurance, knowledge transfer
- **Description**: Code review, quality assurance, and ensuring adherence to project standards and best practices.

### Agent Specification Schema (`SCHEMA`)

- **Role**: One-paragraph description of what this agent does.
- **Capabilities**: category name
- **Description**: One-paragraph description of what this agent does.

### Security Agent (`security`)

- **Role**: Security auditing, vulnerability detection, threat modeling, compliance enforcement, and security standards implementation for Paracle framework and AI applications.
- **Capabilities**: core security, compliance, application security, supply chain security, secret management
- **Description**: Security auditing, vulnerability detection, threat modeling, compliance enforcement, and security standards implementation for Paracle framework and AI applications.

### Agent Specification Template (`TEMPLATE`)

- **Role**: [Describe the agent's primary function in 1-2 sentences]
- **Capabilities**: [primary category], [secondary category]
- **Description**: [Describe the agent's primary function in 1-2 sentences]

### Tester Agent (`tester`)

- **Role**: Test design, implementation, and quality validation ensuring comprehensive coverage and reliability.
- **Capabilities**: test design, test implementation, quality validation
- **Description**: Test design, implementation, and quality validation ensuring comprehensive coverage and reliability.



## Governance Rules

> **📖 Quick Reference**: See [STRUCTURE.md](STRUCTURE.md) for canonical `.parac/` folder structure and file placement rules.

## Contexte : Paracle conçoit Paracle

Ce projet utilise une approche **méta** : nous utilisons le framework Paracle pour concevoir Paracle lui-même.

```
┌─────────────────────────────────────────────────────────────┐
│                    PARACLE FRAMEWORK                        │
│                      packages/                              │
│                                                             │
│   Le PRODUIT que nous développons                          │
│   - Code source du framework                                │
│   - Génère les .parac/ pour les utilisateurs              │
└─────────────────────────────────────────────────────────────┘
                          ↓ génère
┌─────────────────────────────────────────────────────────────┐
│                   .parac/ WORKSPACE                         │
│                  (Côté utilisateur)                         │
│                                                             │
│   Ici : Notre propre utilisation du framework              │
│   - Gouvernance de notre développement                     │
│   - Source de vérité pour le projet Paracle lui-même      │
└─────────────────────────────────────────────────────────────┘
```

**Nous sommes à la fois développeurs ET utilisateurs du framework.**

---

## Principe Fondamental

> **Le répertoire `.parac/` est la source unique et immuable de vérité pour le projet.**

Ce `.parac/` est notre **dogfooding** - il représente ce qu'un utilisateur du framework aurait pour gérer son projet.

Toute information concernant l'état du projet, les décisions, les politiques, et la mémoire du projet DOIT être reflétée dans `.parac/`. Aucune information critique ne doit exister uniquement dans la mémoire d'un agent IA ou dans des conversations.

---

## Règles de Gouvernance

### Règle 1: Traçabilité Totale

Toute décision architecturale, tout changement de scope, toute modification de roadmap DOIT être documentée dans `.parac/`.




## Open Questions

- Q1: Agent Inheritance Depth Limit
- Q2: Event Store Implementation
- Q3: API Versioning Strategy
- Q13: Complexity vs Accessibility
- Q14: Learning Curve Reduction



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
   - New feature → `coder` (+ `architect` if design needed)
   - Bug fix → `coder` (+ `tester` for validation)
   - Documentation → `documenter`
   - Architecture → `architect`
   - Planning → `pm`
   - Review → `reviewer`
5. **Read Agent Spec**: Load full spec from `.parac/agents/specs/{agent_id}.md`
6. **Check Assigned Skills**: See `.parac/agents/SKILL_ASSIGNMENTS.md`

### During Work
1. **Follow Agent Standards**: Apply agent's responsibilities and guidelines
2. **Use Agent Skills**: Leverage assigned skills (see SKILL_ASSIGNMENTS.md)
3. **Check Policies**: Follow `.parac/policies/` (code style, testing, security)
4. **Update Memory Context**: Keep `.parac/memory/context/` current
5. **Track Progress**: Update task status in roadmap if applicable

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

| File | Purpose | When to Read |
| --- | --- | --- |
| **`.parac/GOVERNANCE.md`** | Governance rules, dogfooding context | ALWAYS first |
| **`.parac/PRE_FLIGHT_CHECKLIST.md`** | **NEW: Mandatory task validation** | **Before ANY implementation** |
| **`.parac/UNIVERSAL_AI_INSTRUCTIONS.md`** | Universal instructions (any IDE) | Setup / reference |
| **`.parac/USING_PARAC.md`** | Complete 20+ section guide | Deep understanding |
| **`.parac/CONFIG_FILES.md`** | project.yaml vs manifest.yaml | When confused about config |
| **`.parac/STRUCTURE.md`** | Complete .parac/ structure | Understanding organization |
| **`.parac/agents/manifest.yaml`** | Agent registry | Before selecting agent |
| **`.parac/agents/specs/{agent}.md`** | Agent detailed specs | After selecting agent |
| **`.parac/agents/SKILL_ASSIGNMENTS.md`** | Skills per agent | Understanding capabilities |
| **`.parac/memory/context/current_state.yaml`** | Project state | ALWAYS (before action) |
| **`.parac/memory/context/open_questions.md`** | Open questions | When blocked |
| **`.parac/memory/knowledge/architecture.md`** | Architecture knowledge | Design decisions |
| **`.parac/memory/knowledge/glossary.md`** | Project glossary | Term clarification |
| **`.parac/memory/logs/agent_actions.log`** | Action history | Understanding changes |
| **`.parac/memory/logs/decisions.log`** | Important decisions | Context for choices |
| **`.parac/roadmap/roadmap.yaml`** | Roadmap and phases | Understanding priorities |
| **`.parac/roadmap/decisions.md`** | ADRs (Architecture Decision Records) | Design rationale |
| **`.parac/policies/CODE_STYLE.md`** | Code style guide | Before coding |
| **`.parac/policies/TESTING.md`** | Testing policy | Before writing tests |
| **`.parac/policies/SECURITY.md`** | Security policy | Security-sensitive code |
| **`content/docs/api-keys.md`** | **NEW: API key management guide** | **Setting up LLM providers** |
| **`content/docs/roadmap-state-sync.md`** | **NEW: Roadmap sync guide** | **Understanding governance automation** |



## Rules

**DO:**

✅ **ALWAYS read `.parac/GOVERNANCE.md` first** - Understand dogfooding context
✅ **Check `.parac/memory/context/current_state.yaml`** - Know current state
✅ **Read agent spec** before adopting persona (`.parac/agents/specs/{agent}.md`)
✅ **Log EVERY significant action** to `.parac/memory/logs/agent_actions.log`
✅ **Include file paths** in log entries for code changes
✅ **Follow agent's assigned skills** (see `.parac/agents/SKILL_ASSIGNMENTS.md`)
✅ **Respect policies** in `.parac/policies/` (code style, testing, security)
✅ **Update current_state.yaml** after significant progress
✅ **Log decisions** to `.parac/memory/logs/decisions.log` for important choices
✅ **Track questions** in `.parac/memory/context/open_questions.md` when blocked
✅ **Edit project.yaml** for manual configuration changes
✅ **Use `paracle sync`** to regenerate manifest.yaml (never edit directly)

**DON'T:**

❌ **Never skip reading GOVERNANCE.md** - It's the foundation
❌ **Never edit manifest.yaml manually** - Use `paracle sync` instead
❌ **Never duplicate agent definitions** - Agents are defined in `.parac/agents/`
❌ **Never ignore current_state.yaml** - It's the source of truth for project status
❌ **Never skip logging actions** - Traceability is mandatory
❌ **Never create custom governance rules** - Follow existing governance
❌ **Never assume context** - Always read .parac/ files first
❌ **Never work on wrong phase** - Check roadmap.yaml for current priorities
❌ **Never mix agent personas** - One agent per task, clear boundaries


## ChatGPT Usage

This file is designed for copy-paste into ChatGPT conversations.

### Setup Options

**Option 1: Paste at conversation start**
Copy and paste as your first message in ChatGPT.

**Option 2: Custom Instructions**
1. Go to ChatGPT Settings → Personalization → Custom Instructions
2. Add key sections to "How would you like ChatGPT to respond?"

**Option 3: Create a GPT**
1. Go to Explore GPTs → Create
2. Add these instructions to the GPT configuration

### Project Context

When helping with this project:
- **Project**: paracle-lite v1.0.3
- **Current Phase**: Governance & v1.0 Release
- **Status**: in_progress

### Available Agents

**System Architect Agent** (`architect`): System architecture design, module structure, and technical decision making.
**Coder Agent** (`coder`): Implementation of features, writing production-quality code following project standards and best practices.
**Documenter Agent** (`documenter`): Technical documentation, API references, user guides, and knowledge management.
**Project Manager Agent** (`pm`): Project coordination, roadmap management, progress tracking, and stakeholder communication.
**QA Agent (Senior QA Architect)** (`qa`): Quality Assurance architecture, test strategy design, quality metrics tracking, and comprehensive quality validation across the entire software development lifecycle.
**Release Manager Agent** (`releasemanager`): Manages git workflows, semantic versioning, releases, changelogs, and deployment automation for the Paracle project.
**Reviewer Agent** (`reviewer`): Code review, quality assurance, and ensuring adherence to project standards and best practices.
**Agent Specification Schema** (`SCHEMA`): One-paragraph description of what this agent does.
**Security Agent** (`security`): Security auditing, vulnerability detection, threat modeling, compliance enforcement, and security standards implementation for Paracle framework and AI applications.
**Agent Specification Template** (`TEMPLATE`): [Describe the agent's primary function in 1-2 sentences]
**Tester Agent** (`tester`): Test design, implementation, and quality validation ensuring comprehensive coverage and reliability.

### Key Commands

```bash
paracle status          # Check project state
paracle mcp list        # List available tools
paracle ide sync        # Regenerate configurations
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

1. **Not reading GOVERNANCE.md first** → You miss the dogfooding context
2. **Skipping current_state.yaml** → You work on wrong phase/outdated info
3. **Not logging actions** → No traceability, breaks governance
4. **Editing manifest.yaml manually** → It's auto-generated! Use `paracle sync`
5. **Mixing agent personas** → Stick to one agent per task
6. **Ignoring roadmap.yaml** → You work on wrong priorities
7. **Not checking open_questions.md** → You duplicate questions or miss blockers

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

**Remember**: `.parac/` is your single source of truth. Always read it first. 🎯
