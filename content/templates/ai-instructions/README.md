# AI IDE Instructions for Paracle

Lightweight adapter files for AI-powered IDEs. All point to `.parac/` as the **single source of truth**.

## Architecture Principle

> **Write agents once in `.parac/`, use everywhere with any IDE.**

```
.parac/agents/specs/          ← SINGLE SOURCE (write once)
    ├── pm.md
    ├── architect.md
    ├── coder.md
    ├── tester.md
    ├── reviewer.md
    └── documenter.md

         ↑ referenced by

.cursorrules                  ← Adapter (Cursor)
.clinerules                   ← Adapter (Cline)
.windsurfrules                ← Adapter (Windsurf)
.github-copilot.md            ← Adapter (GitHub Copilot)
.paracle                      ← Universal adapter
```

**No duplication.** Change IDE = copy different adapter file.

## Available Adapters

| File | IDE/AI | Description |
|------|--------|-------------|
| `.cursorrules` | Cursor | Cursor IDE instructions |
| `.clinerules` | Cline | Cline extension |
| `.windsurfrules` | Windsurf | Windsurf IDE |
| `.github-copilot.md` | GitHub Copilot | Copilot Chat |
| `.google-gemini.md` | Google Gemini | Gemini AI |
| `.deepseek-coder.md` | DeepSeek | DeepSeek Coder |
| `.kimi-k2.md` | Kimi K2 | Bilingual CN/EN |
| `.mistral-codestral.md` | Mistral Codestral | Code-focused |
| `.paracle` | Universal | Any AI assistant |

## Usage

### For New Projects

1. Copy `.parac/` template to your project root
2. Copy the appropriate adapter file:

```bash
# For Cursor IDE
cp templates/ai-instructions/.cursorrules .cursorrules

# For Cline
cp templates/ai-instructions/.clinerules .clinerules

# For Windsurf
cp templates/ai-instructions/.windsurfrules .windsurfrules

# For GitHub Copilot (place in .github/)
cp templates/ai-instructions/.github-copilot.md .github/copilot-instructions.md
```

3. The AI assistant will automatically read `.parac/` for agents and context

### Switching IDEs

**No rewriting needed!** Just copy the new adapter:

```bash
# Switch from Cursor to Cline
rm .cursorrules
cp templates/ai-instructions/.clinerules .clinerules

# .parac/agents/specs/ remains unchanged!
```

## What Each Adapter Does

All adapters instruct the AI to:

1. **Read `.parac/`** - Find project context and state
2. **Load Agents** - Read specs from `.parac/agents/specs/`
3. **Follow Governance** - Apply rules from `.parac/GOVERNANCE.md`
4. **Log Actions** - Use `paracle_core.governance.log_action()`
5. **Update Memory** - Propose updates to `.parac/` files

## Governance Logging

All adapters include instructions for logging actions:

```python
from paracle_core.governance import log_action, agent_context

with agent_context("CoderAgent"):
    log_action("IMPLEMENTATION", "Added new feature X")
```

### Action Types

- `IMPLEMENTATION` - New code
- `TEST` - Tests
- `BUGFIX` - Bug fixes
- `REFACTORING` - Code improvements
- `REVIEW` - Code review
- `DOCUMENTATION` - Docs
- `DECISION` - Architecture decisions

## Benefits

### Write Once, Use Everywhere

Define agents in `.parac/agents/specs/` once. All IDEs use the same definitions.

### Easy Maintenance

```bash
# Edit agent definition once
vim .parac/agents/specs/coder.md

# All IDEs automatically use updated version
# No sync needed!
```

### Consistent Behavior

Same agents + same context = consistent behavior across all IDEs.

### Shared Memory

All assistants read from `.parac/`:

- Same project state
- Same roadmap
- Same decisions
- Same action history

## Dogfooding Context

This project uses Paracle to build Paracle:

```
packages/   ← Framework code (product)
.parac/     ← Project workspace (dogfooding)
```

## Contributing

When creating a new adapter:

**DO:**

- Point to `.parac/` as source of truth
- Include governance logging instructions
- Keep it short (< 100 lines ideal)
- Add IDE-specific features

**DON'T:**

- Duplicate agent definitions
- Copy governance rules
- Create custom standards

---

**Remember**: `.parac/` is the source, adapters are just pointers.
