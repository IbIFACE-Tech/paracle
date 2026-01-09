# AI Generation Quick Reference

## Quick Start

```bash
# Create AI-enhanced agent
paracle agents create my-agent --role "Python reviewer" --ai-enhance

# Create AI-enhanced skill
paracle agents skills create my-skill --description "Parse CSV" --ai-enhance

# Create AI-enhanced workflow
paracle workflow create my-workflow --description "CI/CD pipeline" --ai-enhance
```

## Generate Agent

```bash
# Basic (with AI)
paracle agents create code-reviewer \
  --role "Python code reviewer" \
  --ai-enhance

# With specific provider
paracle agents create docs-gen \
  --role "API docs generator" \
  --ai-enhance --ai-provider openai

# Without AI (template only)
paracle agents create test-gen \
  --role "Test generator"

# Custom capabilities
paracle agents create bug-fixer \
  --role "Bug fixer" \
  --capabilities "code_analysis,debugging,testing" \
  --ai-enhance
```

**Deprecated**: `paracle meta generate agent` (use above instead)

## Generate Skill

```bash
# Basic (with AI)
paracle agents skills create csv-parser \
  --description "Extract CSV data" \
  --ai-enhance

# With provider and category
paracle agents skills create slack-notifier \
  --description "Send Slack notifications" \
  --category communication \
  --ai-enhance --ai-provider meta

# With level
paracle agents skills create markdown-parser \
  --description "Parse markdown files" \
  --level intermediate \
  --ai-enhance
```

**Deprecated**: `paracle meta generate skill` (use above instead)

## Generate Workflow

```bash
# Basic sequential workflow
paracle workflow create code-review \
  --description "Code review with tests" \
  --ai-enhance

# Parallel workflow
paracle workflow create deployment \
  --description "Deploy to production" \
  --template parallel \
  --ai-enhance --ai-provider anthropic

# Conditional workflow
paracle workflow create cicd \
  --description "CI/CD pipeline with approval gates" \
  --template conditional \
  --ai-enhance
```

**Template types:**
- `sequential`: Steps run one after another (default)
- `parallel`: Steps run concurrently
- `conditional`: Steps with if/else logic

**Deprecated**: `paracle meta generate workflow` (use above instead)

## Generate Documentation

```bash
# For file
paracle generate docs packages/paracle_core/agent.py

# Save to file
paracle generate docs myfile.py -o docs/myfile.md
```

## Setup paracle_meta

```bash
pip install paracle[meta]
paracle meta activate
paracle generate status
```

## Setup OpenAI

```bash
pip install paracle[openai]
export OPENAI_API_KEY=sk-...
paracle config set ai.provider openai
paracle generate status
```

## Setup Anthropic

```bash
pip install paracle[anthropic]
export ANTHROPIC_API_KEY=sk-ant-...
paracle config set ai.provider anthropic
paracle generate status
```

## Disable AI

```bash
paracle config set ai.provider none
```

## Python API

```python
from paracle_cli.ai_helper import get_ai_provider

# Check availability
ai = get_ai_provider()
if ai:
    result = await ai.generate_agent("description")
else:
    print("AI not available")
```

## Configuration

```yaml
# .parac/config/ai.yaml
ai:
  provider: meta  # Options: none, meta, openai, anthropic, azure

  providers:
    meta:
      model: gpt-4-turbo
    openai:
      api_key: ${OPENAI_API_KEY}
      model: gpt-4-turbo
```

## Troubleshooting

**Problem**: "AI features not available"

```bash
paracle generate status            # Check what's installed
pip install paracle[meta]          # Install provider
paracle meta activate              # Activate (meta only)
```

**Problem**: "API key not found"

```bash
export OPENAI_API_KEY=sk-...       # Set API key
paracle config get ai.provider     # Verify provider
```

## Key Concepts

- **Core features work WITHOUT AI** - AI is optional enhancement
- **Multiple providers** - Choose meta, OpenAI, Anthropic, or Azure
- **Progressive enhancement** - Falls back gracefully when AI unavailable
- **Configuration-driven** - Control via `.parac/config/ai.yaml`

## Examples

See `examples/26_ai_generation.py` for 8 working examples.
