# Paracle Project Template

This template provides a starting point for creating a new Paracle multi-agent project.

## 🚀 Quick Start

### 1. Copy this template

```bash
# Copy the template to your project root
cp -r templates/.parac-template/.parac .
```

Or manually create the `.parac` directory structure in your project root.

### 2. Read Essential Documentation

**Before configuring, read these files to understand .parac/:**

| File                             | Purpose                       | When to Read         |
| -------------------------------- | ----------------------------- | -------------------- |
| **UNIVERSAL_AI_INSTRUCTIONS.md** | IDE-agnostic AI instructions  | Setup, any IDE       |
| **USING_PARAC.md**               | Complete 20+ section guide    | Deep understanding   |
| **CONFIG_FILES.md**              | project.yaml vs manifest.yaml | Configuration        |
| **GOVERNANCE.md**                | Governance rules              | Before ANY action    |
| **STRUCTURE.md**                 | Complete .parac/ structure    | Understanding layout |

### 3. Configure your project

Edit `.parac/project.yaml` (see CONFIG_FILES.md for details):

- **Basic Info**: `name`, `version`, `description`
- **Identity**: Organization and repository details
- **Defaults**: Python version, model provider, default model
- **Features**: Enable/disable features as needed

**Note**: `manifest.yaml` is AUTO-GENERATED. Use `paracle sync` to regenerate it.

### 4. Set up environment variables

Create a `.env` file in your project root:

```bash
# LLM Provider API Keys
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GOOGLE_API_KEY=your-google-api-key

# Optional: Custom configurations
# DATABASE_URL=postgresql://localhost/mydb
# REDIS_URL=redis://localhost:6379
```

### 4. Initialize agents

Create your first agent in `.parac/agents/specs/`:

```yaml
# .parac/agents/specs/assistant.yaml
name: assistant
description: A helpful AI assistant
provider: openai
model: gpt-4
temperature: 0.7
system_prompt: |
  You are a helpful AI assistant.
  Be concise and professional.
```

Update `.parac/agents/manifest.yaml`:

```yaml
agents:
  - name: assistant
    spec_file: specs/assistant.yaml
    enabled: true
    version: 1.0.0
```

## 📁 Directory Structure

The `.parac` directory contains all project configuration and runtime data:

```
.parac/
├── project.yaml          # Main project configuration (required)
├── changelog.md          # Project changelog
│
├── agents/               # Agent definitions
│   ├── manifest.yaml    # Agent registry
│   └── specs/           # Agent specifications
│
├── workflows/            # Workflow definitions
│   ├── catalog.yaml     # Workflow catalog
│   ├── templates/       # Workflow templates
│   └── definitions/     # Custom workflows
│
├── tools/                # Custom tools and plugins
│   ├── registry.yaml    # Tool registry
│   └── custom/          # Custom tool implementations
│
├── policies/             # Security and approval policies
│   ├── policy-pack.yaml # Active policies
│   ├── security.yaml    # Security rules
│   └── approvals.yaml   # Approval workflows
│
├── memory/               # Project memory and context
│   ├── index.yaml       # Memory index
│   ├── context/         # Current context
│   └── knowledge/       # Persistent knowledge
│
├── logs/                 # Execution logs (auto-generated)
│   ├── agents/          # Agent-specific logs
│   ├── workflows/       # Workflow logs
│   └── errors/          # Error logs
│
└── adapters/             # External adapter configurations
    ├── orchestrators.yaml    # Orchestrator adapters
    ├── model_providers.yaml  # Model provider configs
    └── languages.yaml        # Language-specific configs
```

## ⚙️ Configuration Guide

### Essential Configuration

The minimum required configuration in `project.yaml`:

```yaml
name: my-project
version: 0.1.0
description: My Paracle project
schema_version: "1.0"

defaults:
  python_version: "3.10"
  model_provider: openai
  default_model: gpt-4
```

### Advanced Features

#### Enable API

```yaml
features:
  enable_api: true

# Optional API configuration
security:
  require_api_key: true
  allowed_origins:
    - http://localhost:3000
```

#### Enable Tracing

```yaml
features:
  enable_tracing: true
  enable_observability: true

# Configure tracing backend
integrations:
  opentelemetry:
    enabled: true
    endpoint: http://localhost:4317
```

#### Custom Storage

```yaml
storage:
  provider: s3
  s3:
    bucket: my-paracle-data
    region: us-east-1
```

## 🔑 Environment Variables

Common environment variables used by Paracle:

### Required
- `OPENAI_API_KEY` - OpenAI API key (if using OpenAI)
- `ANTHROPIC_API_KEY` - Anthropic API key (if using Claude)
- `GOOGLE_API_KEY` - Google AI API key (if using Gemini)

### Optional
- `PARACLE_ENV` - Environment (development, production)
- `PARACLE_LOG_LEVEL` - Override log level
- `PARACLE_API_PORT` - API server port (default: 8000)
- `PARACLE_API_HOST` - API server host (default: 0.0.0.0)

## 📝 Best Practices

### 1. Version Control

Add to `.gitignore`:

```gitignore
# Paracle runtime
.parac/logs/
.parac/runs/
.parac/memory/context/

# Sensitive data
.env
.env.*
!.env.example

# API keys (double-check!)
*.key
*.secret
```

### 2. Environment-Specific Configs

Use multiple config files:

```
.parac/
├── project.yaml           # Base configuration
├── project.dev.yaml       # Development overrides
├── project.prod.yaml      # Production overrides
```

### 3. Agent Organization

Group related agents:

```
.parac/agents/specs/
├── coding/
│   ├── code-reviewer.yaml
│   ├── code-generator.yaml
│   └── debugger.yaml
├── data/
│   ├── analyst.yaml
│   └── reporter.yaml
```

### 4. Security

- Never commit API keys
- Use environment variables for secrets
- Enable security policies in production
- Review `.parac/policies/security.yaml` regularly

## 🐛 Troubleshooting

### Configuration not loading

Check YAML syntax:
```bash
# Validate YAML
python -c "import yaml; yaml.safe_load(open('.parac/project.yaml'))"
```

### Agent not found

Verify agent is registered in `.parac/agents/manifest.yaml`

### API key errors

Ensure environment variables are set:
```bash
# Check environment variables
echo $OPENAI_API_KEY
# or
printenv | grep API_KEY
```

## 📚 Next Steps

1. **Read the docs**: [Paracle Documentation](../docs/)
2. **Explore examples**: [Example Projects](../examples/)
3. **Join community**: [GitHub Discussions](https://github.com/IbIFACE-Tech/paracle/discussions)
4. **Report issues**: [GitHub Issues](https://github.com/IbIFACE-Tech/paracle/issues)

## 🤝 Contributing

Found an issue with this template? Please open an issue or submit a pull request!

## 📄 License

This template is part of the Paracle project, licensed under Apache 2.0.
