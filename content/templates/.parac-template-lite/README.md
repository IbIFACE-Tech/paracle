# {{PROJECT_NAME}}

A Paracle project in **lite mode** - perfect for quick prototyping!

## 🚀 Quick Start

```bash
# Set your API key
export OPENAI_API_KEY=sk-...

# Run your agent
paracle agents run myagent --task "Your task here"
```

## 📁 Structure

```
.parac/
├── project.yaml          # Project config
├── agents/               # Agent definitions
│   ├── manifest.yaml     # Agent registry
│   └── specs/            # Agent specs
│       └── myagent.md    # Your first agent
├── memory/               # Project memory
│   ├── context/          # Current state
│   └── logs/             # Action logs
└── roadmap/              # Project roadmap
    └── roadmap.yaml      # Phases and goals
```

## 📝 Next Steps

1. **Customize your agent**: Edit `.parac/agents/specs/myagent.md`
2. **Add more agents**: Copy the spec file and modify
3. **Track progress**: Update `.parac/memory/context/current_state.yaml`
4. **Upgrade to full**: `paracle init --template standard --force`

## 📚 Documentation

- [Paracle Docs](https://github.com/IbIFACE-Tech/paracle)
- [Quick Reference](docs/quickstart.md)
- [Agent Guide](docs/agent-guide.md)

## 🆙 Upgrade to Full Mode

When you're ready for databases, Docker, and advanced features:

```bash
paracle init --template standard --force
```

This will add:
- Full `.parac/` structure with policies
- Advanced memory management
- Complete governance system
- Multi-agent workflows

---

**Created with**: Paracle Lite Template
**Date**: {{DATE}}
