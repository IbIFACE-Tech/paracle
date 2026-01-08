# Agent Execution Quick Reference

## Running Workflows with Agents

### Basic Execution
```bash
# Run with mock fallback (no API keys needed)
paracle workflow run hello_world --sync

# Run with API server (if running)
paracle workflow run hello_world

# Specify inputs
paracle workflow run hello_world --input name=Alice --sync
```

### Using Real LLM Providers

#### 1. Self-Hosted (Ollama)
```bash
# Start Ollama
ollama serve

# Pull a model
ollama pull llama2

# Run workflow
paracle workflow run test_ollama --sync
```

#### 2. Commercial Providers (API Keys Required)

**OpenAI**:
```bash
export OPENAI_API_KEY="sk-your-key"
paracle workflow run hello_world --sync
```

**Anthropic**:
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key"
# Update workflow agent config: provider: anthropic, model: claude-3-sonnet
paracle workflow run my_workflow --sync
```

**DeepSeek** (Very Cheap):
```bash
export DEEPSEEK_API_KEY="your-key"
# Update workflow: provider: deepseek, model: deepseek-chat
paracle workflow run my_workflow --sync
```

**Groq** (Fast & Free Tier):
```bash
export GROQ_API_KEY="your-key"
# Update workflow: provider: groq, model: llama2-70b-4096
paracle workflow run my_workflow --sync
```

### Available Providers

| Provider   | Type        | Base URL                              | Models                           |
| ---------- | ----------- | ------------------------------------- | -------------------------------- |
| ollama     | Self-hosted | http://localhost:11434                | llama2, mistral, codellama, etc. |
| openai     | Commercial  | https://api.openai.com/v1             | gpt-4, gpt-3.5-turbo             |
| anthropic  | Commercial  | https://api.anthropic.com             | claude-3-sonnet, claude-3-opus   |
| xai        | Commercial  | https://api.x.ai/v1                   | grok-beta                        |
| deepseek   | Commercial  | https://api.deepseek.com              | deepseek-chat, deepseek-coder    |
| groq       | Commercial  | https://api.groq.com/openai/v1        | llama2-70b-4096, mixtral-8x7b    |
| mistral    | Commercial  | https://api.mistral.ai                | mistral-large, mistral-medium    |
| cohere     | Commercial  | https://api.cohere.ai                 | command, command-light           |
| together   | Commercial  | https://api.together.xyz              | various open models              |
| perplexity | Commercial  | https://api.perplexity.ai             | pplx-70b-online, pplx-7b-chat    |
| openrouter | Aggregator  | https://openrouter.ai/api/v1          | 100+ models from all providers   |
| fireworks  | Commercial  | https://api.fireworks.ai/inference/v1 | various models                   |

## Creating Workflows

### Minimal Workflow
```yaml
name: my_workflow
version: 1.0.0
description: My workflow

inputs:
  message:
    type: string
    default: "Hello"

steps:
  - id: step_1
    name: process
    agent: assistant
    config:
      provider: ollama  # or openai, anthropic, etc.
      model: llama2
      temperature: 0.7
    inputs:
      user_message: "{{ inputs.message }}"
    outputs:
      - response

outputs:
  result:
    source: steps.step_1.outputs.response
```

### Multi-Step Workflow with Dependencies
```yaml
name: complex_workflow
version: 1.0.0

steps:
  - id: step_1
    name: analyze
    agent: analyzer
    config:
      provider: openai
      model: gpt-4
    inputs:
      text: "{{ inputs.text }}"
    outputs:
      - analysis

  - id: step_2
    name: summarize
    agent: summarizer
    depends_on: [step_1]  # Waits for step_1
    config:
      provider: anthropic
      model: claude-3-sonnet
    inputs:
      analysis: "{{ steps.step_1.outputs.analysis }}"
    outputs:
      - summary

outputs:
  final_summary:
    source: steps.step_2.outputs.summary
```

## Agent Specs

### Creating Agent Specs
Create files in `.parac/agents/specs/`:

**Example**: `.parac/agents/specs/coder.md`
```markdown
---
name: Coder Agent
provider: openai
model: gpt-4
temperature: 0.2
max_tokens: 2000
---

# Coder Agent

You are an expert software engineer...
```

### Default Behavior
If agent spec not found:
- Uses default provider (openai)
- Uses default model (gpt-4)
- Temperature 0.7

## Output Display

### Rich Table Output
```
✓ Workflow completed successfully

📦 Workflow Outputs:
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ Output       ┃ Value             ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ result       │ Hello, World!     │
│ analysis     │ The text is...   │
└──────────────┴───────────────────┘

ℹ️  Execution Details:
┌───────────────┬──────────────┐
│ workflow_name │ my_workflow  │
│ total_steps   │ 2            │
└───────────────┴──────────────┘
```

### JSON Output
```bash
paracle workflow run hello_world --sync --output-format json

# Returns:
{
  "execution_id": "exec_...",
  "status": "completed",
  "outputs": {
    "result": "Hello, World!"
  },
  "metadata": {
    "duration": 1.23,
    "steps": 2
  }
}
```

## Troubleshooting

### Provider Not Found
**Error**: `Provider 'openai' not found in registry`

**Solutions**:
1. Set API key: `export OPENAI_API_KEY="sk-..."`
2. Use self-hosted: Change provider to `ollama`
3. Mock fallback: System will use mock automatically

### Agent Spec Not Found
**Warning**: `Agent spec not found for 'greeter', using default`

**Solutions**:
1. Create spec: `.parac/agents/specs/greeter.md`
2. Use default: Warning is informational, uses gpt-4
3. Ignore: Works fine with defaults

### Ollama Connection Error
**Error**: `Failed to connect to Ollama`

**Solutions**:
1. Start Ollama: `ollama serve`
2. Check port: Default is 11434
3. Pull model: `ollama pull llama2`

### Timeout
**Error**: `Workflow execution timeout`

**Solutions**:
1. Increase timeout in workflow YAML:
   ```yaml
   settings:
     timeout: 120  # seconds
   ```
2. Use smaller model (faster inference)
3. Reduce max_tokens in config

## Best Practices

### 1. Development
- Use Ollama for local testing (free, fast)
- Mock fallback allows testing without API keys
- Create minimal workflows first

### 2. Production
- Set up API keys in environment variables
- Use appropriate models for each task
- Configure timeouts and retries
- Monitor costs with token tracking

### 3. Cost Optimization
- Use DeepSeek (very cheap: $0.14/$0.28 per 1M tokens)
- Use Groq (free tier, very fast)
- Use smaller models (gpt-3.5-turbo vs gpt-4)
- Cache agent specs to reduce overhead

### 4. Performance
- Use parallel steps (no depends_on)
- Choose fast providers (Groq, Fireworks)
- Set appropriate timeouts
- Use streaming for long responses (future)

## Examples

### Example 1: Code Review
```yaml
name: code_review
steps:
  - id: review
    agent: reviewer
    config:
      provider: openai
      model: gpt-4
      temperature: 0.3
    inputs:
      code: "{{ inputs.code }}"
    outputs:
      - review
      - suggestions
```

### Example 2: Content Generation Pipeline
```yaml
name: content_pipeline
steps:
  - id: research
    agent: researcher
    config:
      provider: perplexity
      model: pplx-70b-online  # Has web access
    inputs:
      topic: "{{ inputs.topic }}"
    outputs:
      - research_notes

  - id: draft
    agent: writer
    depends_on: [research]
    config:
      provider: anthropic
      model: claude-3-sonnet
    inputs:
      research: "{{ steps.research.outputs.research_notes }}"
    outputs:
      - draft

  - id: edit
    agent: editor
    depends_on: [draft]
    config:
      provider: openai
      model: gpt-4
    inputs:
      draft: "{{ steps.draft.outputs.draft }}"
    outputs:
      - final_content
```

### Example 3: Multi-Provider Fallback
```yaml
# Uses cheap provider first, falls back to premium
name: smart_routing
steps:
  - id: process
    agent: assistant
    config:
      provider: deepseek  # Try cheap option first
      model: deepseek-chat
      fallback_provider: openai  # Fallback to GPT-4
      fallback_model: gpt-4
    inputs:
      query: "{{ inputs.query }}"
    outputs:
      - response
```

## See Also

- [Providers Guide](../../docs/providers.md) - Complete provider documentation
- [API Keys Setup](../../docs/api-keys.md) - API key management
- [Workflow Management](../../docs/workflow-management.md) - Advanced workflows
- [AgentExecutor Source](../packages/paracle_orchestration/agent_executor.py) - Implementation details

---

**Last Updated**: 2026-01-05
**Paracle Version**: 0.0.1 (Phase 4 - 95%)
