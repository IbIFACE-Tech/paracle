# AI IDE Instructions for Paracle

This directory contains **lightweight adapter files** for various AI-powered IDEs. These files are designed to point assistants to `.parac/` as the single source of truth.

## 🎯 Architecture Principle

> **Write agents once in `.parac/`, use everywhere with any IDE.**

```
.parac/agents/specs/          ← SINGLE SOURCE (write once)
    ├── pm.md
    ├── architect.md
    ├── coder.md
    └── ...

         ↑ referenced by

.cursorrules                  ← Lightweight adapter (Cursor)
.clinerules                   ← Lightweight adapter (Cline)
.windsurfrules                ← Lightweight adapter (Windsurf)
.github-copilot.md           ← Lightweight adapter (Copilot)
.claude-instructions.md      ← Lightweight adapter (Claude)
```

**No duplication.** Change IDE = change adapter file only.

## 📋 Available Adapters

### New Lightweight Templates (Recommended)

- `.cursorrules-new` - Cursor IDE (points to `.parac/`)
- `.clinerules-new` - Cline (points to `.parac/`)
- `.windsurfrules-new` - Windsurf (points to `.parac/`)
- `.claude-instructions-new.md` - Claude (points to `.parac/`)

### Legacy Templates (Framework-Specific)

- `.cursorrules` - Old format with duplicated definitions
- `.clinerules` - Old format
- `.windsurfrules` - Old format
- `.github-copilot.md` - Old format
- `.deepseek-coder.md` - Old format

**Note**: Legacy templates will be deprecated. Use new templates that reference `.parac/`.

## 🎯 Purpose

These adapter files help AI assistants:

1. **Find `.parac/`** - Know where to read project context
2. **Load Agents** - Read agent specs from `.parac/agents/specs/`
3. **Follow Governance** - Apply rules from `.parac/GOVERNANCE.md`
4. **Access Memory** - Use project memory from `.parac/memory/`
5. **Log Actions** - Write to `.parac/memory/logs/`

**They do NOT duplicate agent definitions.**

## 🚀 Usage

### For New Projects

1. Copy `.parac/` template to your project root
2. Copy the appropriate adapter file:

```bash
# For Cursor IDE
cp templates/ai-instructions/.cursorrules-new .cursorrules

# For Cline
cp templates/ai-instructions/.clinerules-new .clinerules

# For Windsurf
cp templates/ai-instructions/.windsurfrules-new .windsurfrules

# For Claude
cp templates/ai-instructions/.claude-instructions-new.md .claude/instructions.md
```

3. The AI assistant will automatically read `.parac/` for agents and context

### Switching IDEs

**No rewriting needed!** Just copy the new adapter:

```bash
# Switch from Cursor to Copilot
rm .cursorrules
cp .github/copilot-instructions.md .github/copilot-instructions.md

# .parac/agents/specs/ remains unchanged
```

## 💡 Key Benefits

### ✅ Write Once, Use Everywhere

Define agents in `.parac/agents/specs/` once:

- `pm.md` - Project Manager
- `architect.md` - System Architect
- `coder.md` - Developer
- `tester.md` - QA Engineer
- `reviewer.md` - Code Reviewer
- `documenter.md` - Technical Writer

**All IDEs use the same definitions.**

### ✅ Easy Maintenance

Update an agent:

```bash
# Edit agent definition once
vim .parac/agents/specs/coder.md

# All IDEs automatically use updated version
# No sync needed!
```

### ✅ Consistent Behavior

Same agents + same context = consistent behavior across:

- Cursor
- Cline
- Windsurf
- GitHub Copilot
- Claude
- Any future IDE

### ✅ Shared Memory

All assistants read from `.parac/`:

- Same project state
- Same roadmap
- Same decisions
- Same action history

## 📖 How It Works

### Traditional Approach (❌ Bad)

```
.cursorrules       ← 500 lines with agent definitions
.copilot.md        ← 500 lines with SAME agent definitions
.claude.md         ← 500 lines with SAME agent definitions

Result: 3x duplication, hard to maintain
```

### PARACLE Approach (✅ Good)

```
.parac/agents/specs/coder.md    ← SINGLE definition (100 lines)
    ↑
    Referenced by:
    - .cursorrules              ← Adapter (50 lines)
    - .copilot.md              ← Adapter (50 lines)
    - .claude.md               ← Adapter (50 lines)

Result: No duplication, easy maintenance
```

## 🎓 For IDE Adapter Developers

When creating a new adapter file:

### ✅ DO

- Point to `.parac/` as source of truth
- Explain how to read `.parac/agents/specs/`
- Include IDE-specific features (shortcuts, commands)
- Keep it short (< 200 lines)
- Reference `.github/copilot-instructions.md` for details

### ❌ DON'T

- Duplicate agent definitions
- Copy governance rules
- Replicate roadmap or memory
- Create your own standards
- Make it IDE-agnostic (be specific!)

## 📚 Resources

- **Architecture Guide**: `.github/instructions/ai-instructions-architecture.md`
- **Dogfooding Context**: `.github/instructions/dogfooding-clarification.md`
- **Complete Instructions**: `.github/copilot-instructions.md`
- **Governance**: `.parac/GOVERNANCE.md`

## 🔄 Migration from Old Templates

If you have old-style instructions with duplicated agents:

1. Move agent definitions to `.parac/agents/specs/`
2. Replace old instructions with new adapter template
3. Test that AI reads `.parac/` correctly
4. Delete old duplicated content

See `.github/instructions/ai-instructions-architecture.md` for migration guide.

---

**Remember**: `.parac/` is the source, adapters are just pointers.

- **Cursor**: Looks for `.cursorrules`
- **Cline**: Looks for `.clinerules`
- **Windsurf**: Looks for `.windsurfrules`
- **GitHub Copilot**: Reference `.github-copilot.md` in your docs
- **Others**: Use the markdown files as reference documentation

## 📝 What's Included

Each instruction file covers:

### 1. `.parac` Structure Understanding
- Directory organization
- File purposes and relationships
- Schema versions and validation

### 2. Configuration Management
- Project settings (`project.yaml`)
- Agent specifications (`agents/`)
- Workflow definitions (`workflows/`)
- Tool registry (`tools/`)
- Security policies (`policies/`)

### 3. Best Practices
- Naming conventions
- YAML formatting
- Security considerations
- Version control

### 4. Common Operations
- Creating new agents
- Defining workflows
- Configuring providers
- Managing tools and policies

### 5. Validation Rules
- Schema compliance
- Required fields
- Value constraints
- Cross-reference validation

## 🔧 Customization

You can customize these files for your specific project:

1. Copy the file to your project root
2. Edit to add project-specific rules
3. Add custom conventions or requirements
4. Reference internal documentation

Example additions:

```yaml
# In .cursorrules or similar
custom_rules:
  - "All agents must have a 'cost_tier' field"
  - "Use 'gpt-4' for production, 'gpt-3.5-turbo' for development"
  - "Security policies must be reviewed by @security-team"
```

## 🎓 Learning Resources

For more information about `.parac` configuration:

- [Template Documentation](../.parac-template/README.md)
- [Getting Started Guide](../../docs/getting-started.md)
- [Architecture Documentation](../../docs/architecture.md)

## 🤝 Contributing

Improvements to these AI instructions are welcome:

1. Test with your AI IDE
2. Identify gaps or issues
3. Submit improvements via PR
4. Share your customizations

## 📜 License

These instruction files are part of Paracle and licensed under Apache 2.0.

---

**Note**: AI assistants are helpers, not replacements for understanding Paracle's architecture. Always review AI-generated code and configurations.
