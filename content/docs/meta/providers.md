# Providers Guide

Configure and use different LLM providers with `paracle_meta`.

## Supported Providers

| Provider | Models | Features | Cost |
|----------|--------|----------|------|
| **Anthropic** | Claude 3.5/4 Sonnet, Opus, Haiku | Best reasoning, tool use | $3-15/1M tokens |
| **OpenAI** | GPT-4o, GPT-4 Turbo, GPT-3.5 | Versatile, fast | $0.5-30/1M tokens |
| **DeepSeek** | DeepSeek V3, Coder | Cost-effective, good for code | $0.14-0.28/1M tokens |
| **Ollama** | Llama 3.1, Mistral, CodeLlama | Local, free, private | Free (self-hosted) |

## Provider Configuration

### Anthropic

```yaml
providers:
  - name: anthropic
    model: claude-sonnet-4-20250514
    api_key: ${ANTHROPIC_API_KEY}
    max_tokens: 8192
    temperature: 0.7
    use_for:
      - agents
      - security
      - code
      - complex-reasoning
```

**Environment Variable:**
```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
```

**Available Models:**
| Model | Context | Best For |
|-------|---------|----------|
| `claude-sonnet-4-20250514` | 200K | General, balanced |
| `claude-opus-4-20250514` | 200K | Complex reasoning |
| `claude-3-5-haiku-20241022` | 200K | Fast, cheap |

### OpenAI

```yaml
providers:
  - name: openai
    model: gpt-4o
    api_key: ${OPENAI_API_KEY}
    max_tokens: 4096
    temperature: 0.7
    use_for:
      - documentation
      - embeddings
      - quick-tasks
```

**Environment Variable:**
```bash
OPENAI_API_KEY=sk-...
```

**Available Models:**
| Model | Context | Best For |
|-------|---------|----------|
| `gpt-4o` | 128K | General, vision |
| `gpt-4-turbo` | 128K | Long context |
| `gpt-4o-mini` | 128K | Fast, cheap |
| `gpt-3.5-turbo` | 16K | Very fast |

### DeepSeek

```yaml
providers:
  - name: deepseek
    model: deepseek-chat
    api_key: ${DEEPSEEK_API_KEY}
    base_url: "https://api.deepseek.com"
    max_tokens: 4096
    temperature: 0.7
    use_for:
      - code
      - documentation
```

**Environment Variable:**
```bash
DEEPSEEK_API_KEY=sk-...
```

**Available Models:**
| Model | Context | Best For |
|-------|---------|----------|
| `deepseek-chat` | 64K | General chat |
| `deepseek-coder` | 64K | Code generation |

### Ollama (Local)

```yaml
providers:
  - name: ollama
    model: llama3.1
    base_url: "http://localhost:11434"
    max_tokens: 4096
    temperature: 0.7
    use_for:
      - quick-tasks
      - private-data
```

**Setup:**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull models
ollama pull llama3.1
ollama pull codellama
ollama pull nomic-embed-text  # For embeddings

# Start server (usually auto-started)
ollama serve
```

**Available Models:**
| Model | Size | Best For |
|-------|------|----------|
| `llama3.1` | 8B/70B | General |
| `codellama` | 7B/13B/34B | Code |
| `mistral` | 7B | Fast general |
| `phi3` | 3.8B | Very fast |

## Provider Chain (Fallback)

Configure automatic fallback when providers fail:

```yaml
provider_chain:
  primary: anthropic
  fallback:
    - openai
    - ollama

  circuit_breaker:
    enabled: true
    failure_threshold: 5
    reset_timeout: 60.0
```

**How It Works:**

1. Request goes to primary provider (Anthropic)
2. If Anthropic fails 5 times, circuit breaker opens
3. Requests automatically route to fallback (OpenAI)
4. After 60s, circuit breaker half-opens to test Anthropic
5. If Anthropic works, circuit closes and returns to normal

## Provider Selection by Task

Configure which provider handles which task types:

```yaml
providers:
  - name: anthropic
    use_for:
      - agents        # Agent generation
      - security      # Security analysis
      - code          # Code generation
      - complex       # Complex reasoning

  - name: openai
    use_for:
      - documentation # Doc generation
      - embeddings    # Vector embeddings
      - quick         # Quick simple tasks

  - name: ollama
    use_for:
      - private       # Private/sensitive data
      - testing       # Development/testing
```

**Usage in Code:**

```python
from paracle_meta import load_config

config = load_config()

# Get provider for task type
security_provider = config.get_provider_for_task("security")
doc_provider = config.get_provider_for_task("documentation")
```

## Provider Protocol

All providers implement the `CapabilityProvider` protocol:

```python
from paracle_meta import CapabilityProvider, LLMRequest, LLMResponse

class CustomProvider(CapabilityProvider):
    """Custom LLM provider implementation."""

    @property
    def name(self) -> str:
        return "custom"

    @property
    def status(self) -> ProviderStatus:
        return self._status

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Generate completion."""
        # Implementation
        pass

    async def stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        """Stream completion."""
        # Implementation
        pass

    async def health_check(self) -> bool:
        """Check provider health."""
        return True
```

## Built-in Providers

### AnthropicProvider

```python
from paracle_meta.capabilities.providers import AnthropicProvider

provider = AnthropicProvider(
    api_key="sk-ant-...",
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
)

response = await provider.complete(LLMRequest(
    messages=[LLMMessage(role="user", content="Hello!")],
    temperature=0.7,
))
```

### OpenAIProvider

```python
from paracle_meta.capabilities.providers import OpenAIProvider

provider = OpenAIProvider(
    api_key="sk-...",
    model="gpt-4o",
)
```

### OllamaProvider

```python
from paracle_meta.capabilities.providers import OllamaProvider

provider = OllamaProvider(
    model="llama3.1",
    base_url="http://localhost:11434",
)
```

### MockProvider (Testing)

```python
from paracle_meta.capabilities.providers import MockProvider

provider = MockProvider(
    responses=["Hello!", "How can I help?"],
)
```

## Cost Tracking

Each provider tracks token usage and costs:

```python
from paracle_meta import CostOptimizer

optimizer = CostOptimizer(config.cost)

# Track usage
await optimizer.record_usage(
    provider="anthropic",
    model="claude-sonnet-4-20250514",
    input_tokens=1000,
    output_tokens=500,
)

# Check budget
if optimizer.at_warning_threshold():
    print("Approaching budget limit!")

if optimizer.at_limit():
    print("Budget exceeded!")
```

## Best Practices

1. **Start with Anthropic** - Best overall quality for complex tasks
2. **Use OpenAI for embeddings** - text-embedding-3-small is cost-effective
3. **Add Ollama as fallback** - Free local fallback for resilience
4. **Set cost limits** - Prevent runaway spending
5. **Monitor health** - Use `paracle meta health` regularly
6. **Use task routing** - Match providers to task types
