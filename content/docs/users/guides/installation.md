# Installation Guide

Complete guide for installing Paracle.

## Requirements

- **Python**: 3.10 or higher
- **OS**: Windows, macOS, or Linux
- **Memory**: 512 MB minimum
- **Storage**: 100 MB for base installation

## Installation Methods

### pip (Recommended)

```bash
# Basic installation
pip install paracle

# With API server
pip install paracle[api]

# With AI generation (paracle_meta)
pip install paracle[meta]

# Full installation
pip install paracle[all]
```

### uv (Fast)

```bash
# Install uv if needed
pip install uv

# Install paracle
uv pip install paracle
```

### From Source

```bash
# Clone repository
git clone https://github.com/IbIFACE-Tech/paracle.git
cd paracle

# Install in editable mode
pip install -e ".[dev]"
```

## Verify Installation

```bash
# Check version
paracle --version
# Output: paracle 1.0.0

# Check help
paracle --help
```

## Optional Dependencies

| Extra | Description | Install |
|-------|-------------|---------|
| `api` | REST API server | `pip install paracle[api]` |
| `meta` | AI generation engine | `pip install paracle[meta]` |
| `store` | Database support | `pip install paracle[store]` |
| `providers` | LLM providers | `pip install paracle[providers]` |
| `dev` | Development tools | `pip install paracle[dev]` |

## LLM Provider Setup

Paracle requires at least one LLM provider. Set up your preferred provider:

### Anthropic (Recommended)

```bash
export ANTHROPIC_API_KEY=sk-ant-api03-...
```

Get your key at [console.anthropic.com](https://console.anthropic.com/)

### OpenAI

```bash
export OPENAI_API_KEY=sk-...
```

Get your key at [platform.openai.com](https://platform.openai.com/)

### DeepSeek (Cost-effective)

```bash
export DEEPSEEK_API_KEY=sk-...
```

Get your key at [platform.deepseek.com](https://platform.deepseek.com/)

### Ollama (Local, Free)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3

# Verify running
ollama list
```

## Initialize a Project

```bash
# Create new project
mkdir my-project && cd my-project

# Initialize Paracle
paracle init

# This creates:
# .parac/
# ├── project.yaml
# ├── agents/
# ├── workflows/
# └── skills/
```

## Quick Test

```bash
# List agents
paracle agents list

# Run interactive chat
paracle meta chat

# Check health
paracle meta health
```

## Troubleshooting

### ModuleNotFoundError

```bash
# Ensure correct Python
python --version  # Should be 3.10+

# Reinstall
pip uninstall paracle
pip install paracle
```

### API Key Errors

```bash
# Check environment variable
echo $ANTHROPIC_API_KEY

# On Windows
echo %ANTHROPIC_API_KEY%

# Use .env file (create in project root)
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

### Permission Errors

```bash
# Use virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install paracle
```

## Next Steps

- [Quick Start Tutorial](quickstart.md)
- [First Agent Tutorial](../tutorials/tutorial.md)
- [API Keys Reference](../reference/api-keys.md)
