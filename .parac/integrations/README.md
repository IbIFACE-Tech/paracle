# Integrations

External system integrations for the Paracle workspace.

## Philosophy: IDE-Agnostic Instructions

**Important**: The `.parac/` content is **IDE-agnostic**. Only the file format changes for different IDEs.

### Core Principle

All AI assistants (regardless of IDE) must:
1. **READ** `.parac/` before any action
2. **FOLLOW** governance rules
3. **LOG** all significant actions
4. **UPDATE** memory after changes

### Universal Instructions

📖 **[UNIVERSAL_AI_INSTRUCTIONS.md](../UNIVERSAL_AI_INSTRUCTIONS.md)** - Works with ANY IDE/assistant

This file contains instructions that work universally across:
- Cursor, Cline, Windsurf, Claude Code, GitHub Copilot
- ChatGPT, Claude, Gemini
- Any future AI assistant

**Use this as the base for all IDE integrations.**

---

## Structure

```
integrations/
├── README.md              # This file
└── ide/                   # IDE-specific configurations
    ├── _manifest.yaml     # Generated configs tracking
    ├── .cursorrules       # Cursor format
    ├── .clinerules        # Cline format
    ├── .windsurfrules     # Windsurf format
    ├── CLAUDE.md          # Claude Code format
    └── copilot-instructions.md  # GitHub Copilot format
```

---

## IDE Integration

The `ide/` folder contains generated configuration files for various AI-powered IDEs.

These files are **auto-generated** from `.parac/` content by `paracle ide init` and can be copied to the project root with `paracle ide init --copy`.

### Supported IDEs

| IDE                | File                      | Location          | Format                        |
| ------------------ | ------------------------- | ----------------- | ----------------------------- |
| **Cursor**         | `.cursorrules`            | Project root      | Plain text                    |
| **Cline**          | `.clinerules`             | Project root      | Plain text                    |
| **Windsurf**       | `.windsurfrules`          | Project root      | Plain text                    |
| **Claude Code**    | `CLAUDE.md`               | `.claude/` folder | Markdown                      |
| **GitHub Copilot** | `copilot-instructions.md` | `.github/` folder | Markdown (instructions block) |
| **ChatGPT/Claude** | Via context               | Manual paste      | Markdown                      |

### Content is the Same

All IDE-specific files contain **the same core instructions**:
1. Read `.parac/GOVERNANCE.md`
2. Check `.parac/memory/context/current_state.yaml`
3. Adopt agent persona from `.parac/agents/specs/`
4. Follow `.parac/policies/`
5. Log actions to `.parac/memory/logs/agent_actions.log`

**Only the file format differs** (plain text vs markdown, etc.)

---

## Usage

### Generate IDE Instructions

```bash
# Generate instructions for all supported IDEs
paracle ide init

# Copy to project root (for IDE detection)
paracle ide init --copy

# Sync after .parac/ changes
paracle ide sync --copy
```

### Manual Integration

If your IDE is not supported yet:

1. Read **[UNIVERSAL_AI_INSTRUCTIONS.md](../UNIVERSAL_AI_INSTRUCTIONS.md)**
2. Copy its content to your IDE's config file
3. Adjust format if needed (e.g., XML, JSON, etc.)
4. The **content remains the same**

Example for a hypothetical IDE "MyIDE":

```bash
# .myide/config.md
# Copy content from .parac/UNIVERSAL_AI_INSTRUCTIONS.md
# Format: MyIDE's expected format (markdown, JSON, etc.)
```

---

## Portability

### Switching IDEs

When you change IDE, you **DON'T need to rewrite instructions**:

```bash
# 1. Generate for new IDE
paracle ide sync --copy

# 2. Done! The content is the same, only format differs
```

### Adding New IDE Support

To add support for a new IDE:

1. Create a template in `packages/paracle_cli/templates/ide/`
2. Use Jinja2 to generate from `.parac/` data
3. Register in `packages/paracle_cli/commands/ide.py`

**Template variables available:**
- `{{ agents }}` - List of agents from `.parac/agents/manifest.yaml`
- `{{ current_state }}` - From `.parac/memory/context/current_state.yaml`
- `{{ roadmap }}` - From `.parac/roadmap/roadmap.yaml`
- `{{ governance }}` - Content of `.parac/GOVERNANCE.md`

Example template:

```jinja2
# Instructions for {{ ide_name }}
# Generated: {{ timestamp }}

## Core Principle
.parac/ is the source of truth

## Agents
{% for agent in agents %}
- {{ agent.id }}: {{ agent.role }}
{% endfor %}

## Current State
Phase: {{ current_state.phase }}
Status: {{ current_state.status }}
```

---

## File Contents

### What's in Each IDE File?

All files contain (in their respective format):

1. **Header**
   - Auto-generated warning
   - Regeneration command
   - Timestamp

2. **Core Principle**
   - `.parac/` is source of truth

3. **Current Project State**
   - Phase, status, progress
   - From `.parac/memory/context/current_state.yaml`

4. **Available Agents**
   - List of agents with roles and capabilities
   - From `.parac/agents/manifest.yaml`

5. **Governance Rules**
   - Dogfooding explanation (Paracle develops Paracle)
   - Fundamental principles
   - From `.parac/GOVERNANCE.md`

6. **Workflow Instructions**
   - Read → Adopt → Execute → Log → Update
   - Standard workflow for all assistants

7. **Logging Format**
   - `[TIMESTAMP] [AGENT] [ACTION] Description`
   - Destination: `.parac/memory/logs/agent_actions.log`

8. **References**
   - Links to key `.parac/` files
   - Documentation links

---

## Best Practices

### For Users

1. **Generate once, sync regularly**
   ```bash
   paracle ide init --copy  # Initial setup
   paracle ide sync --copy  # After .parac/ changes
   ```

2. **Don't edit generated files manually**
   - Edit `.parac/` content instead
   - Regenerate with `paracle ide sync`

3. **Version control**
   - Commit `.parac/integrations/ide/` (source)
   - Optionally commit root IDE files (`.cursorrules`, etc.)

### For AI Assistants

1. **Read UNIVERSAL_AI_INSTRUCTIONS.md first**
   - Works with any IDE
   - Complete instructions

2. **Follow the workflow**
   - Read → Adopt → Execute → Log → Update

3. **Log everything**
   - Format: `[TIMESTAMP] [AGENT] [ACTION] Description`
   - Destination: `.parac/memory/logs/agent_actions.log`

---

## Examples

### Example 1: Using Cursor

```bash
# 1. Generate .cursorrules
paracle ide init --copy

# 2. Cursor reads .cursorrules automatically
# 3. AI assistant follows instructions from .parac/

# 4. AI logs actions
[2026-01-04 15:00:00] [CoderAgent] [IMPLEMENTATION] Added new feature
```

### Example 2: Using Claude Desktop

```bash
# 1. Generate CLAUDE.md
paracle ide init --copy

# 2. Copy .parac/integrations/ide/CLAUDE.md to .claude/CLAUDE.md
cp .parac/integrations/ide/CLAUDE.md .claude/CLAUDE.md

# 3. Claude reads .claude/CLAUDE.md
# 4. AI follows same workflow as Cursor
```

### Example 3: Using ChatGPT (Manual)

```markdown
User:
I'm working on a Paracle project. Here are the instructions:

[Paste content from .parac/UNIVERSAL_AI_INSTRUCTIONS.md]

Now, help me implement feature X.

ChatGPT:
Let me first read .parac/memory/context/current_state.yaml to understand the current state...
```

---

## Validation

### Check if IDE Instructions are Working

```bash
# 1. Ask AI assistant to read .parac/GOVERNANCE.md
# Expected: AI reads and summarizes governance

# 2. Ask AI to log an action
# Expected: Entry in .parac/memory/logs/agent_actions.log

# 3. Check current state understanding
# Expected: AI knows current phase and progress

# 4. Verify agent adoption
# Expected: AI adopts correct persona for task type
```

---

## Troubleshooting

### AI Doesn't Follow Instructions

1. **Check if IDE file exists**
   ```bash
   # Cursor
   ls -la .cursorrules

   # Claude Code
   ls -la .claude/CLAUDE.md

   # GitHub Copilot
   ls -la .github/copilot-instructions.md
   ```

2. **Regenerate instructions**
   ```bash
   paracle ide sync --copy --force
   ```

3. **Verify .parac/ content**
   ```bash
   cat .parac/GOVERNANCE.md
   cat .parac/memory/context/current_state.yaml
   ```

4. **Manually guide AI**
   ```
   User: "Please read .parac/GOVERNANCE.md first"
   ```

### Instructions Out of Date

```bash
# After updating .parac/ content
paracle ide sync --copy

# This regenerates all IDE files with latest content
```

---

## Future Integrations

Planned integrations:

- `ci/` - CI/CD pipeline configurations (GitHub Actions, GitLab CI)
- `git/` - Git hooks and workflows
- `notifications/` - Slack, Discord, webhooks
- `monitoring/` - Prometheus, Grafana configs
- `deployment/` - Docker, Kubernetes manifests

---

## Contributing

To add support for a new IDE:

1. Create template in `packages/paracle_cli/templates/ide/{ide_name}.jinja2`
2. Add to `IDE_CONFIGS` in `packages/paracle_cli/commands/ide.py`
3. Test generation: `paracle ide init`
4. Submit PR with example

---

## Related Documentation

- **[UNIVERSAL_AI_INSTRUCTIONS.md](../UNIVERSAL_AI_INSTRUCTIONS.md)** - IDE-agnostic instructions
- **[USING_PARAC.md](../USING_PARAC.md)** - Complete .parac/ usage guide
- **[GOVERNANCE.md](../GOVERNANCE.md)** - Project governance rules
- **[STRUCTURE.md](../STRUCTURE.md)** - .parac/ structure documentation

---

**Remember: The content is IDE-agnostic. Only the format changes.** 🎯
