# AI-Powered Generation Features

Paracle supports optional AI-powered generation of agents, skills, workflows, and documentation.

## Architecture

**Core Principle**: AI features are **optional enhancements** - Paracle works fully without them.

- ✅ **Core functionality** (running agents, workflows, tools) works WITHOUT AI
- ✅ **AI features** are opt-in enhancements for generating configurations
- ✅ **Progressive enhancement** - use AI if available, skip if not
- ✅ **Provider flexibility** - use paracle_meta, OpenAI, Anthropic, or Azure

## Feature Matrix

### Without AI Provider

| Feature               | Available | Notes                                     |
| --------------------- | --------- | ----------------------------------------- |
| Run agents            | ✅         | Manually configured agents work fully     |
| Execute workflows     | ✅         | No AI required for workflow execution     |
| Use tools             | ✅         | All tools work without AI                 |
| Remote development    | ✅         | SSH/WebSocket transport independent of AI |
| Manual agent creation | ✅         | Write YAML specs manually                 |
| Manual skill creation | ✅         | Write Python skills manually              |

### With AI Provider

| Feature                 | Available | Provider     |
| ----------------------- | --------- | ------------ |
| Generate agents         | ✅         | Any provider |
| Generate skills         | ✅         | Any provider |
| Generate workflows      | ✅         | Any provider |
| Generate documentation  | ✅         | Any provider |
| Suggest improvements    | ✅         | paracle_meta |
| Debug assistance        | ✅         | paracle_meta |
| Code review enhancement | ✅         | paracle_meta |

## Quick Start

### Option 1: paracle_meta (Recommended)

Built-in AI engine with optimized Paracle knowledge:

```bash
# Install
pip install paracle[meta]

# Activate
paracle meta activate

# Use
paracle agents create code-reviewer \
  --role "Python code reviewer" \
  --ai-enhance --ai-provider meta
```

### Option 2: External Provider (OpenAI)

```bash
# Install
pip install paracle[openai]

# Configure
export OPENAI_API_KEY=sk-...
paracle config set ai.provider openai

# Use
paracle agents create code-reviewer \
  --role "Python code reviewer" \
  --ai-enhance --ai-provider openai
```

### Option 3: No AI (Manual Configuration)

```bash
# Create agent manually
cat > .parac/agents/specs/reviewer.md << EOF
# Reviewer Agent
...
EOF

# Works perfectly without AI
paracle agents run reviewer --task "Review code"
```

## AI Provider Configuration

**Configuration file**: `.parac/config/ai.yaml`

```yaml
# Select provider
ai:
  provider: meta  # Options: none, meta, openai, anthropic, azure

  providers:
    # paracle_meta (internal AI)
    meta:
      model: gpt-4-turbo
      temperature: 0.7

    # OpenAI
    openai:
      api_key: ${OPENAI_API_KEY}
      model: gpt-4-turbo

    # Anthropic
    anthropic:
      api_key: ${ANTHROPIC_API_KEY}
      model: claude-3-opus-20240229

    # Azure OpenAI
    azure:
      endpoint: ${AZURE_OPENAI_ENDPOINT}
      api_key: ${AZURE_OPENAI_KEY}
```

## CLI Commands

### Generate Agent

**New Command**: `paracle agents create --ai-enhance`

```bash
# Basic usage with AI enhancement
paracle agents create code-reviewer \
  --role "Python code reviewer with security focus" \
  --ai-enhance

# Specific provider
paracle agents create docs-generator \
  --role "API docs generator" \
  --ai-enhance --ai-provider openai

# Without AI (template only)
paracle agents create tester \
  --role "Test automation specialist"

# With custom name
paracle agents create bug-fixer \
  --name "Bug Fixer Pro" \
  --role "Automated bug detection and fixing" \
  --ai-enhance
```

**Output**: Agent specification in `.parac/agents/specs/<agent_id>.md`

**Deprecated**: `paracle meta generate agent` (use above instead)

### Generate Skill

**New Command**: `paracle agents skills create --ai-enhance`

```bash
# Generate skill with AI enhancement
paracle agents skills create csv-extractor \
  --description "Extract data from CSV files" \
  --ai-enhance

# With specific provider
paracle agents skills create slack-notifier \
  --description "Send Slack notifications" \
  --ai-enhance --ai-provider meta

# Without AI (template only)
paracle agents skills create markdown-parser \
  --category analysis --level intermediate

# With additional directories
paracle agents skills create api-client \
  --description "REST API client wrapper" \
  --ai-enhance --with-scripts --with-references
```

**Output**:
- Skill directory in `.parac/agents/skills/<name>/`
- SKILL.md with metadata and instructions
- Optional scripts/, references/, assets/ directories

### Generate Workflow

**New Command**: `paracle workflow create --ai-enhance`

```bash
# Generate workflow with AI enhancement
paracle workflow create code-review-security \
  --description "Code review with security scan" \
  --ai-enhance

# Sequential workflow (default)
paracle workflow create deploy \
  --description "Deploy to production" \
  --template sequential \
  --ai-enhance --ai-provider openai

# Parallel workflow
paracle workflow create test-suite \
  --description "Run unit and integration tests in parallel" \
  --template parallel \
  --ai-enhance

# Conditional workflow
paracle workflow create release \
  --description "Test and release with approval gates" \
  --template conditional \
  --ai-enhance

# Without AI (template only)
paracle workflow create build-test \
  --template sequential
```

**Template Types**:
- `sequential`: Steps run one after another (default)
- `parallel`: Steps run concurrently where possible
- `conditional`: Steps with conditions and branches

**Output**: Workflow YAML in `.parac/workflows/<workflow_id>.yaml`

**Deprecated**: `paracle meta generate workflow` (use above instead)

## Migration Guide

### Migrating from Deprecated Commands

The `paracle meta generate` commands are **deprecated** and will be removed in a future version. Please migrate to the new consolidated commands:

#### Agent Generation

**Old (Deprecated):**
```bash
paracle meta generate agent SecurityAuditor \
  --desc "Reviews code for security vulnerabilities" \
  --provider anthropic
```

**New (Recommended):**
```bash
paracle agents create security-auditor \
  --role "Reviews code for security vulnerabilities" \
  --ai-enhance --ai-provider anthropic
```

**Key Changes:**
- Use `paracle agents create` instead of `paracle meta generate agent`
- Option `--desc` → `--role`
- Option `--provider` → `--ai-provider`
- Add `--ai-enhance` flag explicitly
- Agent ID must be lowercase-with-hyphens

#### Workflow Generation

**Old (Deprecated):**
```bash
paracle meta generate workflow review-pipeline \
  --desc "Multi-stage code review process" \
  --provider openai
```

**New (Recommended):**
```bash
paracle workflow create review-pipeline \
  --description "Multi-stage code review process" \
  --ai-enhance --ai-provider openai
```

**Key Changes:**
- Use `paracle workflow create` instead of `paracle meta generate workflow`
- Option `--desc` → `--description`
- Option `--provider` → `--ai-provider`
- Add `--ai-enhance` flag explicitly
- Can specify `--template` type (sequential/parallel/conditional)

#### Benefits of New Commands

1. **Better Organization**: Commands in logical groups (agents, workflow)
2. **Consistent Interface**: Same `--ai-enhance` pattern across all commands
3. **Template Fallback**: Works without AI configuration
4. **More Options**: Template types for workflows, category/level for skills
5. **Better Discoverability**: Commands where users expect them

### Generate Documentation

```bash
# Generate docs for file
paracle generate docs packages/paracle_core/agent.py

# Save to file
paracle generate docs myfile.py -o docs/myfile.md
```

**Output**: Markdown documentation

### Check Status

```bash
# Check which providers are available
paracle generate status
```

**Output**:
```
AI Provider Status

✓ AI provider active: meta

Available Providers
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Provider  ┃ Status        ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ meta      │ ✓ Installed   │
│ openai    │ ✗ Not installed │
│ anthropic │ ✗ Not installed │
│ azure     │ ✗ Not installed │
└───────────┴───────────────┘
```

## Python API

```python
from paracle_cli.ai_helper import get_ai_provider

# Check if AI available
ai = get_ai_provider()
if ai is None:
    print("AI not available, using manual configuration")
    # Continue with manual workflow
else:
    # Use AI for generation
    result = await ai.generate_agent("Python code reviewer")
    print(result["yaml"])
```

## Architecture Pattern

### Progressive Enhancement

```python
from paracle_cli.ai_helper import get_ai_provider, AIProviderNotAvailable

def create_agent(description: str):
    """Create agent - with or without AI."""

    # Try AI generation first
    ai = get_ai_provider()
    if ai:
        result = await ai.generate_agent(description)
        save_agent(result)
        return result

    # Fall back to manual template
    print("AI not available - using template")
    result = create_from_template(description)
    return result
```

### Optional Import Pattern

```python
# Core functionality - no AI dependency
from paracle_core.agent import Agent

agent = Agent.from_file(".parac/agents/specs/coder.md")
result = agent.run("Fix bug")  # ✅ Works without AI

# Optional AI enhancement
try:
    from paracle_cli.ai_helper import get_ai_provider

    ai = get_ai_provider()
    if ai:
        # Generate agent with AI
        spec = await ai.generate_agent("Bug fixer")
        agent = Agent.from_yaml(spec["yaml"])
except ImportError:
    # paracle_meta not installed - continue without AI
    pass
```

## Provider Comparison

| Feature                | paracle_meta              | OpenAI                      | Anthropic                      | Azure                      |
| ---------------------- | ------------------------- | --------------------------- | ------------------------------ | -------------------------- |
| **Installation**       | pip install paracle[meta] | pip install paracle[openai] | pip install paracle[anthropic] | pip install paracle[azure] |
| **API Key Required**   | No                        | Yes                         | Yes                            | Yes                        |
| **Paracle-Optimized**  | ✅ Yes                     | ❌ No                        | ❌ No                           | ❌ No                       |
| **Cost**               | Bundled                   | Pay-per-use                 | Pay-per-use                    | Pay-per-use                |
| **Offline Mode**       | ✅ Yes                     | ❌ No                        | ❌ No                           | ❌ No                       |
| **Privacy**            | ✅ Local                   | ⚠ Cloud                     | ⚠ Cloud                        | ⚠ Cloud                    |
| **Generate Agents**    | ✅                         | ✅                           | ✅                              | ✅                          |
| **Generate Skills**    | ✅                         | ✅                           | ✅                              | ✅                          |
| **Generate Workflows** | ✅                         | ✅                           | ✅                              | ✅                          |
| **Debug Assistance**   | ✅                         | ❌                           | ❌                              | ❌                          |
| **Code Review**        | ✅                         | ❌                           | ❌                              | ❌                          |

## Setup Guides

### paracle_meta Setup

```bash
# 1. Install
pip install paracle[meta]

# 2. Activate
paracle meta activate

# 3. Configure (optional)
paracle meta config --model gpt-4-turbo

# 4. Test
paracle generate status
```

### OpenAI Setup

```bash
# 1. Install
pip install paracle[openai]

# 2. Get API key
# Visit: https://platform.openai.com/api-keys

# 3. Configure
export OPENAI_API_KEY=sk-...
paracle config set ai.provider openai

# 4. Test
paracle generate status
```

### Anthropic Setup

```bash
# 1. Install
pip install paracle[anthropic]

# 2. Get API key
# Visit: https://console.anthropic.com/

# 3. Configure
export ANTHROPIC_API_KEY=sk-ant-...
paracle config set ai.provider anthropic

# 4. Test
paracle generate status
```

### Azure OpenAI Setup

```bash
# 1. Install
pip install paracle[azure]

# 2. Set up Azure OpenAI service
# Follow: https://azure.microsoft.com/en-us/products/cognitive-services/openai-service

# 3. Configure
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
export AZURE_OPENAI_KEY=...
paracle config set ai.provider azure

# 4. Test
paracle generate status
```

## Troubleshooting

### AI Not Available

**Problem**: "AI features not available"

**Solution**:
```bash
# Check status
paracle generate status

# Install provider
pip install paracle[meta]  # or [openai], [anthropic], [azure]

# Activate paracle_meta
paracle meta activate

# Or configure external provider
export OPENAI_API_KEY=sk-...
paracle config set ai.provider openai
```

### Import Error

**Problem**: "ModuleNotFoundError: No module named 'paracle_meta'"

**Solution**:
```bash
# Install with AI support
pip install paracle[meta]

# Or disable AI in config
paracle config set ai.provider none
```

### API Key Error

**Problem**: "API key not found"

**Solution**:
```bash
# For OpenAI
export OPENAI_API_KEY=sk-...

# For Anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# For Azure
export AZURE_OPENAI_ENDPOINT=https://...
export AZURE_OPENAI_KEY=...

# Verify in config
paracle config get ai.providers.openai.api_key
```

### Wrong Provider

**Problem**: Using wrong provider or outdated model

**Solution**:
```bash
# Check current provider
paracle config get ai.provider

# Change provider
paracle config set ai.provider meta

# Update model
paracle config set ai.providers.meta.model gpt-4-turbo
```

## Best Practices

### 1. Start with paracle_meta

```bash
pip install paracle[meta]
paracle meta activate
```

**Why**: Optimized for Paracle, no API keys, works offline.

### 2. Use Templates for Common Patterns

```bash
# Generate once
paracle generate agent "Code reviewer" -o .parac/templates/reviewer.md

# Reuse template
cp .parac/templates/reviewer.md .parac/agents/specs/my_reviewer.md
```

### 3. Version Control Generated Files

```bash
# Commit generated configurations
git add .parac/agents/specs/
git commit -m "Add AI-generated agent specs"
```

**Why**: Generated configs are source code, not build artifacts.

### 4. Disable AI for CI/CD

```yaml
# .parac/config/ai.yaml
ai:
  provider: none  # Disable in CI
```

**Why**: CI should use pre-configured agents, not generate on-the-fly.

### 5. Track Costs

```yaml
# .parac/config/ai.yaml
limits:
  track_costs: true
  daily_request_limit: 100
```

```bash
# Check costs
paracle cost report --ai-only
```

## Examples

### Example 1: Generate Code Review Agent

```bash
paracle generate agent "Python code reviewer focusing on security, performance, and best practices. Should check for SQL injection, XSS vulnerabilities, and suggest optimizations."
```

**Output**: `.parac/agents/specs/python_code_reviewer.md`

### Example 2: Generate CSV Processing Skill

```bash
paracle generate skill "Read CSV files, validate data types, handle missing values, and export to JSON format"
```

**Output**:
- `.parac/agents/skills/csv_processor/csv_processor.yaml`
- `.parac/agents/skills/csv_processor/csv_processor.py`

### Example 3: Generate CI/CD Workflow

```bash
paracle generate workflow "Run tests, check code coverage, perform security scan with Bandit, and deploy to staging if all checks pass"
```

**Output**: `.parac/workflows/ci_cd_pipeline.yaml`

### Example 4: Batch Generation

```bash
# Generate multiple agents
for desc in "bug fixer" "test generator" "docs writer"; do
    paracle generate agent "$desc"
done

# Generate multiple skills
for desc in "email sender" "file uploader" "data validator"; do
    paracle generate skill "$desc"
done
```

## Migration from Manual Configuration

### Before (Manual)

```yaml
# .parac/agents/specs/reviewer.md
# Reviewer Agent

## Role
Reviews Python code for quality issues.

## Skills
- code_analysis
- style_checking
```

### After (AI-Generated)

```bash
paracle generate agent "Python code reviewer"
```

**Result**: Same functionality, faster creation, consistent format.

## Security Considerations

### API Keys

**Never commit API keys to git**:

```bash
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# .gitignore
.env
```

### Privacy

**Local processing with paracle_meta**:

```yaml
# .parac/config/ai.yaml
ai:
  provider: meta  # Runs locally

privacy:
  send_analytics: false
  share_anonymized_data: false
```

### Cost Control

```yaml
# .parac/config/ai.yaml
limits:
  max_tokens_per_request: 4000
  daily_request_limit: 50
  track_costs: true
```

## See Also

- [Agents Guide](agents.md) - Manual agent creation
- [Skills Guide](skills.md) - Manual skill creation
- [Workflows Guide](workflows.md) - Manual workflow creation
- [paracle_meta Documentation](paracle-meta.md) - Internal AI engine
