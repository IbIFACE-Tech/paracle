# Paracle Project Template

This is the official template for creating new Paracle projects. Copy this directory structure to quickly set up a new multi-agent AI application.

## 📋 Template Contents

```
.parac-template/
├── project.yaml              # Main project configuration ⭐
├── README.md                 # Setup and usage guide
├── changelog.md              # Project changelog
├── .gitignore               # Git ignore rules for .parac
├── .env.example             # Environment variables template
│
├── agents/                   # Agent definitions
│   ├── manifest.yaml        # Agent registry
│   └── specs/               # Agent specifications
│       └── assistant.yaml   # Example agent
│
├── workflows/                # Workflow definitions
│   ├── catalog.yaml         # Workflow catalog
│   └── templates/           # Workflow templates
│       └── hello_world.yaml # Example workflow
│
├── tools/                    # Tools and plugins
│   └── registry.yaml        # Tool registry
│
├── policies/                 # Security and governance
│   ├── policy-pack.yaml     # Active policies
│   └── security.yaml        # Security policies
│
├── memory/                   # Project memory
│   ├── index.yaml           # Memory index
│   └── knowledge/           # Knowledge base
│       └── domain.md        # Domain knowledge
│
├── adapters/                 # External integrations
│   └── orchestrators.yaml   # Adapter configurations
│
└── logs/                     # Execution logs
    └── README.md            # Logging guide
```

## 🚀 Quick Start

### Option 1: Copy Template to New Project

```bash
# Create new project directory
mkdir my-paracle-project
cd my-paracle-project

# Copy template
cp -r path/to/paracle-lite/templates/.parac-template .parac

# Configure project
# Edit .parac/project.yaml with your project details

# Set up environment
cp .parac/.env.example .env
# Edit .env with your API keys
```

### Option 2: Use CLI (Future)

```bash
# Future CLI command
paracle init my-project --template default
```

## 📝 Configuration Steps

### 1. Edit Project Configuration

Edit [.parac/project.yaml](project.yaml):

```yaml
name: my-project              # ⬅️ Change this
version: 0.1.0
description: My awesome AI project  # ⬅️ Change this

defaults:
  model_provider: openai      # ⬅️ Configure provider
  default_model: gpt-4        # ⬅️ Configure model
```

### 2. Set Up Environment Variables

```bash
cp .parac/.env.example .env
```

Edit `.env` and add your API keys:

```bash
OPENAI_API_KEY=sk-...        # ⬅️ Add your key
```

### 3. Customize Agents

Edit [.parac/agents/specs/assistant.yaml](agents/specs/assistant.yaml) or create new agents:

```yaml
name: my-agent
provider: openai
model: gpt-4
system_prompt: |
  You are my custom agent...
```

### 4. Set Up Security

Review and customize [.parac/policies/security.yaml](policies/security.yaml):

```yaml
content_filtering:
  enabled: true
  filter_pii: true

rate_limiting:
  enabled: true
  requests_per_minute: 60
```

## 📚 What to Customize

### Essential
- ✅ `project.yaml` - Project name, version, defaults
- ✅ `.env` - API keys and credentials
- ✅ `agents/specs/` - Your agent definitions

### Recommended
- ⭐ `policies/security.yaml` - Security settings
- ⭐ `tools/registry.yaml` - Enable/disable tools
- ⭐ `memory/knowledge/domain.md` - Document your domain

### Optional
- `workflows/` - Custom workflows
- `adapters/` - External integrations
- `policies/policy-pack.yaml` - Additional policies

## 🔒 Security Checklist

Before deploying:

- [ ] Review `policies/security.yaml`
- [ ] Set up rate limiting
- [ ] Configure content filtering
- [ ] Add `.env` to `.gitignore`
- [ ] Never commit API keys
- [ ] Enable audit logging
- [ ] Review tool permissions

## 📖 Next Steps

1. **Read the documentation**: [Getting Started Guide](../../docs/getting-started.md)
2. **Explore examples**: [Example Projects](../../examples/)
3. **Customize your agents**: [Agent Documentation](../../docs/agents.md)
4. **Deploy your project**: [Deployment Guide](../../docs/deployment.md)

## 🛠️ Troubleshooting

### Template not working

Make sure you:
1. Copied all files and directories
2. Renamed `.parac-template` to `.parac`
3. Edited `project.yaml` with valid values
4. Set up `.env` with your API keys

### Import errors

Check that Paracle is installed:

```bash
pip show paracle
# or
uv pip show paracle
```

### API key errors

Verify environment variables are set:

```bash
echo $OPENAI_API_KEY
# or on Windows
echo %OPENAI_API_KEY%
```

## 💡 Tips

- **Start simple**: Use the default configuration first
- **Iterate**: Add complexity as needed
- **Document**: Keep `memory/knowledge/domain.md` updated
- **Version**: Use semantic versioning
- **Test**: Test agents before deployment

## 📜 License

This template is part of Paracle and is licensed under Apache 2.0.

## 🤝 Contributing

Found an issue? Want to improve the template?

- [Report issues](https://github.com/IbIFACE-Tech/paracle-lite/issues)
- [Submit PR](https://github.com/IbIFACE-Tech/paracle-lite/pulls)
- [Join discussions](https://github.com/IbIFACE-Tech/paracle-lite/discussions)

---

**Happy building! 🚀**
