# Provider Guide

Complete guide to using LLM providers in Paracle.

## Overview

Paracle provides a unified interface for working with multiple LLM providers. This abstraction allows you to switch between providers seamlessly while using the same API.

## Supported Providers

### Official AI SDK Providers

| Provider      | Status | Models                  | Features                       |
| ------------- | ------ | ----------------------- | ------------------------------ |
| **OpenAI**    | ✅ Full | GPT-4, GPT-3.5          | Streaming, tools, vision       |
| **Anthropic** | ✅ Full | Claude 3.x              | Streaming, tools, long context |
| **Google**    | ✅ Full | Gemini                  | Streaming, tools, vision       |
| **xAI**       | ✅ Full | Grok                    | Streaming, tools, long context |
| **DeepSeek**  | ✅ Full | DeepSeek Chat, Reasoner | Streaming, tools, reasoning    |
| **Groq**      | ✅ Full | Llama, Mixtral, Gemma   | Ultra-fast inference           |
| **Ollama**    | ✅ Full | Local models            | Self-hosted, no API key        |

### OpenAI-Compatible

| Provider                      | Base URL                      | Models              |
| ----------------------------- | ----------------------------- | ------------------- |
| **LM Studio**                 | `http://localhost:1234/v1`    | Local models        |
| **Together.ai**               | `https://api.together.xyz/v1` | Various open-source |
| **Perplexity**                | `https://api.perplexity.ai`   | Perplexity models   |
| **Any OpenAI-compatible API** | Custom                        | Custom              |

## Quick Start

### Basic Usage

```python
from paracle_providers import ProviderRegistry, ChatMessage, LLMConfig

# Create a provider
provider = ProviderRegistry.create_provider(
    "openai",
    api_key="sk-..."
)

# Generate completion
messages = [
    ChatMessage(role="user", content="Hello!")
]
config = LLMConfig(temperature=0.7, max_tokens=100)

response = await provider.chat_completion(
    messages=messages,
    config=config,
    model="gpt-4"
)

print(response.content)
```

### Streaming

```python
# Stream responses
async for chunk in provider.stream_completion(
    messages=messages,
    config=config,
    model="gpt-4"
):
    print(chunk.content, end="", flush=True)
```

## Provider Setup

### OpenAI

```python
from paracle_providers import ProviderRegistry

provider = ProviderRegistry.create_provider(
    "openai",
    api_key="sk-..."  # or set OPENAI_API_KEY
)

# Available models
models = [
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo",
    "gpt-4-vision-preview",  # for images
]
```

**Environment Variables:**
- `OPENAI_API_KEY` - Your API key

**Features:**
- ✅ Streaming
- ✅ Tool calling
- ✅ Vision (gpt-4-vision)
- ✅ JSON mode

### Anthropic

```python
provider = ProviderRegistry.create_provider(
    "anthropic",
    api_key="sk-ant-..."  # or set ANTHROPIC_API_KEY
)

# Available models
models = [
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
]
```

**Environment Variables:**
- `ANTHROPIC_API_KEY` - Your API key

**Features:**
- ✅ Streaming
- ✅ Tool calling
- ✅ Long context (200k tokens)
- ✅ Vision

### Google (Gemini)

```python
provider = ProviderRegistry.create_provider(
    "google",
    api_key="..."  # or set GOOGLE_API_KEY
)

# Available models
models = [
    "gemini-2.0-flash-exp",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
]
```

**Environment Variables:**
- `GOOGLE_API_KEY` - Your API key

**Features:**
- ✅ Streaming
- ✅ Tool calling
- ✅ Vision
- ✅ Long context (1M+ tokens)

### xAI (Grok)

```python
provider = ProviderRegistry.create_provider(
    "xai",
    api_key="xai-..."  # or set XAI_API_KEY
)

# Available models
models = [
    "grok-2-1212",
    "grok-2-vision-1212",
    "grok-beta",
]
```

**Environment Variables:**
- `XAI_API_KEY` - Your API key

**Features:**
- ✅ Streaming
- ✅ Tool calling
- ✅ Vision (grok-2-vision)
- ✅ Extended context (131k tokens)

### DeepSeek

```python
provider = ProviderRegistry.create_provider(
    "deepseek",
    api_key="sk-..."  # or set DEEPSEEK_API_KEY
)

# Available models
models = [
    "deepseek-chat",      # General chat
    "deepseek-reasoner",  # Advanced reasoning
]
```

**Environment Variables:**
- `DEEPSEEK_API_KEY` - Your API key

**Features:**
- ✅ Streaming
- ✅ Tool calling
- ✅ Advanced reasoning (reasoner model)
- ✅ Long context (64k tokens)
- 💰 Very cost-effective

**Pricing:**
- Chat: $0.14/M input, $0.28/M output
- Reasoner: $0.55/M input, $2.19/M output

### Groq

```python
provider = ProviderRegistry.create_provider(
    "groq",
    api_key="gsk_..."  # or set GROQ_API_KEY
)

# Available models
models = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",  # Ultra-fast
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]
```

**Environment Variables:**
- `GROQ_API_KEY` - Your API key

**Features:**
- ✅ Streaming
- ✅ Ultra-fast inference (500+ tokens/sec)
- ✅ Cost-effective
- ✅ Open-source models

**Best For:**
- High-throughput applications
- Real-time chat
- Development and testing

### Ollama (Local)

```python
provider = ProviderRegistry.create_provider(
    "ollama",
    base_url="http://localhost:11434"  # default
)

# Available models (must be pulled first)
# Run: ollama pull llama3
models = [
    "llama3",
    "mistral",
    "codellama",
    "phi",
]
```

**Features:**
- ✅ Self-hosted (no API key needed)
- ✅ Privacy (data never leaves your machine)
- ✅ No cost
- ✅ Runs on CPU or GPU

**Setup:**
1. Install Ollama: https://ollama.com
2. Pull a model: `ollama pull llama3`
3. Start server: `ollama serve`

### OpenAI-Compatible APIs

For any service that implements the OpenAI API:

```python
from paracle_providers.openai_compatible import (
    OpenAICompatibleProvider,
    create_lmstudio_provider,
    create_together_provider,
    create_perplexity_provider,
)

# Generic usage
provider = OpenAICompatibleProvider(
    base_url="https://api.your-service.com/v1",
    api_key="your-key",
    provider_name="my-service"
)

# LM Studio (local)
provider = create_lmstudio_provider(port=1234)

# Together.ai
provider = create_together_provider(api_key="...")

# Perplexity
provider = create_perplexity_provider(api_key="...")
```

## Model Discovery

### Using Model Catalog

```python
from paracle_providers import get_model_catalog, ModelCapability

catalog = get_model_catalog()

# List all providers
for provider in catalog.list_providers():
    print(f"{provider.display_name}: {len(provider.models)} models")

# Find models with specific capability
results = catalog.search_models(
    capability=ModelCapability.TOOL_CALLING
)

for provider, model in results:
    print(f"{provider.display_name}/{model.model_id}")

# Find cost-effective models
results = catalog.search_models(
    max_cost=1.0  # Max $1 per million tokens
)

# Find a specific model
result = catalog.find_model("gpt-4")
if result:
    provider, model = result
    print(f"Found: {provider.display_name}/{model.model_id}")
    print(f"Capabilities: {model.capabilities}")
```

### Model Capabilities

```python
from paracle_providers import ModelCapability

# Available capabilities
capabilities = [
    ModelCapability.TEXT_GENERATION,
    ModelCapability.CHAT_COMPLETION,
    ModelCapability.OBJECT_GENERATION,    # Structured output
    ModelCapability.TOOL_CALLING,         # Functions
    ModelCapability.STREAMING,
    ModelCapability.JSON_MODE,
    ModelCapability.IMAGE_INPUT,          # Vision
    ModelCapability.IMAGE_OUTPUT,         # Generation
    ModelCapability.AUDIO_INPUT,          # Speech-to-text
    ModelCapability.AUDIO_OUTPUT,         # Text-to-speech
    ModelCapability.LONG_CONTEXT,         # >32k tokens
    ModelCapability.EXTENDED_CONTEXT,     # >128k tokens
    ModelCapability.CODE_GENERATION,
    ModelCapability.EMBEDDINGS,
    ModelCapability.REASONING,            # Chain-of-thought
]

# Check model capabilities
catalog = get_model_catalog()
result = catalog.find_model("gpt-4")
if result:
    provider, model = result

    if model.supports_vision():
        print("Model supports image input")

    if model.supports_tools():
        print("Model supports tool calling")

    if model.supports_streaming():
        print("Model supports streaming")
```

## Advanced Usage

### Retry Logic

```python
from paracle_providers.retry import (
    RetryableProvider,
    RetryConfig,
)

# Wrap provider with retry logic
base_provider = ProviderRegistry.create_provider("openai")
provider = RetryableProvider(
    base_provider,
    config=RetryConfig(
        max_retries=3,
        initial_delay=1.0,
        max_delay=10.0,
        exponential_base=2.0,
    )
)

# Automatically retries on transient errors
response = await provider.chat_completion(messages, config, model)
```

### Custom Provider

```python
from paracle_providers.base import LLMProvider, LLMResponse, ChatMessage

class MyCustomProvider(LLMProvider):
    async def chat_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs,
    ) -> LLMResponse:
        # Your implementation
        pass

    async def stream_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs,
    ):
        # Your streaming implementation
        pass

# Register it
ProviderRegistry.register("my-provider", MyCustomProvider)
```

## Cost Comparison

| Provider  | Model             | Input $/M | Output $/M | Context | Speed         |
| --------- | ----------------- | --------- | ---------- | ------- | ------------- |
| OpenAI    | gpt-4-turbo       | 10.00     | 30.00      | 128k    | Fast          |
| OpenAI    | gpt-3.5-turbo     | 0.50      | 1.50       | 16k     | Very Fast     |
| Anthropic | claude-3-opus     | 15.00     | 75.00      | 200k    | Fast          |
| Anthropic | claude-3-sonnet   | 3.00      | 15.00      | 200k    | Fast          |
| DeepSeek  | deepseek-chat     | 0.14      | 0.28       | 64k     | Fast          |
| DeepSeek  | deepseek-reasoner | 0.55      | 2.19       | 64k     | Medium        |
| Groq      | llama-3.3-70b     | 0.59      | 0.79       | 131k    | Ultra-Fast    |
| Groq      | llama-3.1-8b      | 0.05      | 0.08       | 131k    | Ultra-Fast    |
| Ollama    | Any               | 0.00      | 0.00       | Varies  | Depends on HW |

## Best Practices

### 1. Start with Cost-Effective Models

```python
# For development/testing
provider = ProviderRegistry.create_provider("groq")
model = "llama-3.1-8b-instant"

# For production (budget)
provider = ProviderRegistry.create_provider("deepseek")
model = "deepseek-chat"
```

### 2. Use Streaming for UX

```python
# Better user experience with streaming
async for chunk in provider.stream_completion(...):
    print(chunk.content, end="", flush=True)
```

### 3. Handle Errors Gracefully

```python
from paracle_providers import (
    LLMProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)

try:
    response = await provider.chat_completion(...)
except ProviderRateLimitError:
    # Wait and retry
    await asyncio.sleep(60)
except ProviderTimeoutError:
    # Use shorter timeout or simpler prompt
    pass
except LLMProviderError as e:
    # Generic error handling
    print(f"Provider error: {e}")
```

### 4. Monitor Token Usage

```python
response = await provider.chat_completion(...)
print(f"Tokens used: {response.usage.total_tokens}")
print(f"Prompt: {response.usage.prompt_tokens}")
print(f"Completion: {response.usage.completion_tokens}")

# Estimate cost
cost = (
    response.usage.prompt_tokens * INPUT_COST_PER_TOKEN +
    response.usage.completion_tokens * OUTPUT_COST_PER_TOKEN
)
```

### 5. Use the Right Model for the Job

- **Simple tasks**: Use smaller/cheaper models (gpt-3.5, llama-8b)
- **Complex reasoning**: Use advanced models (gpt-4, claude-opus, deepseek-reasoner)
- **Vision tasks**: Use multimodal models (gpt-4-vision, claude-3, gemini)
- **High throughput**: Use Groq for ultra-fast inference
- **Privacy/local**: Use Ollama for self-hosted

## Troubleshooting

### Provider Not Found

```python
# Check available providers
providers = ProviderRegistry.list_providers()
print(f"Available: {providers}")

# Ensure provider is registered
from paracle_providers.openai_provider import OpenAIProvider
ProviderRegistry.register("openai", OpenAIProvider)
```

### Import Errors

```bash
# Install provider dependencies
pip install openai  # For OpenAI
pip install anthropic  # For Anthropic
pip install google-generativeai  # For Google
pip install httpx  # For xAI, DeepSeek, Groq, Ollama
```

### API Key Issues

```python
# Check environment variables
import os
print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', 'Not set')}")

# Or pass explicitly
provider = ProviderRegistry.create_provider(
    "openai",
    api_key="sk-..."
)
```

## Next Steps

- See [examples/](../examples/) for complete working examples
- Check [API Reference](./api-reference.md) for detailed API docs
- Read [Architecture](./architecture.md) to understand provider design


---

## Additional Commercial Providers

### Mistral

**Website**: https://mistral.ai
**Best for**: Open-weight models, function calling, enterprise use

**Models**:
- `mistral-large-latest` - 131k context, powerful reasoning
- `mistral-medium-latest` - 32k context, balanced performance  
- `mistral-small-latest` - 32k context, cost-effective
- `pixtral-large-latest` - 131k context, vision + multimodal

**Setup**:
```python
import os
from paracle_providers.mistral_provider import MistralProvider

os.environ["MISTRAL_API_KEY"] = "your-api-key"
provider = MistralProvider()

response = await provider.chat_completion(...)
```

**Pricing**:
- Large: $2.00/M input, $6.00/M output
- Medium: $2.70/M input, $8.10/M output  
- Small: $0.20/M input, $0.60/M output

---

### Cohere

**Website**: https://cohere.com
**Best for**: Embeddings, reranking, chat with citations

**Models**:
- `command-r-plus` - 128k context, advanced reasoning
- `command-r` - 128k context, cost-effective
- `command` - 4k context, fast responses

**Setup**:
```python
import os
from paracle_providers.cohere_provider import CohereProvider

os.environ["COHERE_API_KEY"] = "your-api-key"
provider = CohereProvider()

response = await provider.chat_completion(...)
```

**Pricing**:
- Command R+: $2.50/M input, $10.00/M output
- Command R: $0.15/M input, $0.60/M output

---

### Together.ai

**Website**: https://together.ai
**Best for**: 100+ open-source models, fast inference

**Models**:
- `meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo` - Largest Llama
- `meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo` - Balanced
- `Qwen/Qwen2.5-72B-Instruct-Turbo` - Chinese + English

**Setup**:
```python
import os
from paracle_providers.together_provider import TogetherProvider

os.environ["TOGETHER_API_KEY"] = "your-api-key"
provider = TogetherProvider()

response = await provider.chat_completion(...)
```

**Pricing**:
- 405B: $3.50/M tokens (input + output)
- 70B: $0.88/M tokens

---

### Perplexity

**Website**: https://www.perplexity.ai
**Best for**: Search-enhanced responses, real-time web access, citations

**Models**:
- `llama-3.1-sonar-large-128k-online` - Web search enabled
- `llama-3.1-sonar-small-128k-online` - Cost-effective search
- `llama-3.1-sonar-large-128k-chat` - No search

**Setup**:
```python
import os
from paracle_providers.perplexity_provider import PerplexityProvider

os.environ["PERPLEXITY_API_KEY"] = "your-api-key"
provider = PerplexityProvider()

response = await provider.chat_completion(...)
# response.metadata['citations'] contains sources
```

**Pricing**:
- Large: $1.00/M tokens
- Small: $0.20/M tokens

**Unique Feature**: Responses include citations from web sources

---

### OpenRouter

**Website**: https://openrouter.ai
**Best for**: Unified gateway to 200+ models, fallback options

**Models**: Access to models from:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google (Gemini)
- Meta (Llama)
- Many others

**Setup**:
```python
import os
from paracle_providers.openrouter_provider import OpenRouterProvider

os.environ["OPENROUTER_API_KEY"] = "your-api-key"
provider = OpenRouterProvider()

# Use any model from any provider
response = await provider.chat_completion(
    messages=[...],
    model="anthropic/claude-3.5-sonnet"
)
```

**Pricing**: Varies by model (see https://openrouter.ai/models)

**Benefits**:
- Single API for all providers
- Automatic fallbacks
- Cost optimization
- No vendor lock-in

---

### Fireworks.ai

**Website**: https://fireworks.ai
**Best for**: Production-grade inference, competitive pricing

**Models**:
- `accounts/fireworks/models/llama-v3p1-405b-instruct` - Largest
- `accounts/fireworks/models/llama-v3p1-70b-instruct` - Balanced
- `accounts/fireworks/models/mixtral-8x22b-instruct` - MoE model

**Setup**:
```python
import os
from paracle_providers.fireworks_provider import FireworksProvider

os.environ["FIREWORKS_API_KEY"] = "your-api-key"
provider = FireworksProvider()

response = await provider.chat_completion(...)
```

**Pricing**:
- 405B: $3.00/M tokens
- 70B: $0.90/M tokens
- Mixtral 8x22B: $0.90/M tokens

---

## Self-Hosted & Open-Source Options

### LM Studio

**Website**: https://lmstudio.ai
**Best for**: Beginners, local development, GUI interface

**Setup**:
```python
from paracle_providers import create_lmstudio_provider

# LM Studio runs on port 1234 by default
provider = create_lmstudio_provider(port=1234)

response = await provider.chat_completion(
    messages=[...],
    model="local-model"  # Use loaded model
)
```

**Features**:
- ✅ Easy-to-use GUI
- ✅ Model discovery and download
- ✅ No API key required
- ✅ Windows/Mac/Linux support

---

### vLLM

**Website**: https://vllm.ai
**Best for**: Production deployments, high throughput, GPU optimization

**Setup**:
```python
from paracle_providers import create_vllm_provider

# Start vLLM server first:
# vllm serve meta-llama/Llama-3-8b-hf --port 8000

provider = create_vllm_provider(base_url="http://localhost:8000/v1")

response = await provider.chat_completion(
    messages=[...],
    model="meta-llama/Llama-3-8b-hf"
)
```

**Features**:
- ✅ Extremely fast inference
- ✅ PagedAttention for memory efficiency
- ✅ Continuous batching
- ✅ Production-ready

---

### llama.cpp

**Website**: https://github.com/ggerganov/llama.cpp
**Best for**: CPU inference, quantized models, low memory usage

**Setup**:
```python
from paracle_providers import create_llamacpp_provider

# Start llama.cpp server first:
# ./llama-server -m models/llama-3-8b.gguf --port 8080

provider = create_llamacpp_provider(base_url="http://localhost:8080/v1")

response = await provider.chat_completion(
    messages=[...],
    model="llama-3-8b"
)
```

**Features**:
- ✅ Runs on CPU
- ✅ GGUF quantized models
- ✅ Low memory footprint
- ✅ Cross-platform

---

### text-generation-webui (oobabooga)

**Website**: https://github.com/oobabooga/text-generation-webui
**Best for**: Experimentation, extensions, many features

**Setup**:
```python
from paracle_providers import create_text_generation_webui_provider

# Start with --api flag
provider = create_text_generation_webui_provider(
    base_url="http://localhost:5000/v1"
)

response = await provider.chat_completion(
    messages=[...],
    model="TheBloke/Llama-2-7B-Chat-GGUF"
)
```

**Features**:
- ✅ Rich web UI
- ✅ Many extensions
- ✅ LoRA support
- ✅ Multi-API modes

---

### LocalAI

**Website**: https://localai.io
**Best for**: Drop-in OpenAI replacement, Docker deployment

**Setup**:
```python
from paracle_providers import create_localai_provider

# Start with Docker:
# docker run -p 8080:8080 localai/localai:latest

provider = create_localai_provider(base_url="http://localhost:8080/v1")

response = await provider.chat_completion(
    messages=[...],
    model="gpt-3.5-turbo"  # LocalAI model alias
)
```

**Features**:
- ✅ OpenAI API compatible
- ✅ Easy Docker deployment
- ✅ Multiple backends
- ✅ Audio, image, embeddings

---

### Jan

**Website**: https://jan.ai
**Best for**: Privacy-focused, desktop app, easy setup

**Setup**:
```python
from paracle_providers import create_jan_provider

# Jan desktop app runs on port 1337
provider = create_jan_provider(base_url="http://localhost:1337/v1")

response = await provider.chat_completion(
    messages=[...],
    model="tinyllama-1.1b"  # Model installed in Jan
)
```

**Features**:
- ✅ Modern desktop app
- ✅ Privacy-first
- ✅ Model management
- ✅ Cross-platform

---

## Provider Comparison Matrix

| Provider | Type | Best For | Context | Cost | Key Feature |
|----------|------|----------|---------|------|-------------|
| **OpenAI** | Commercial | General purpose | 128k | -Line$ | GPT-4, most capable |
| **Anthropic** | Commercial | Safety, analysis | 200k | -Line$ | Long context, ethical AI |
| **Google** | Commercial | Multimodal, scale | 2M | -Line | Massive context window |
| **xAI** | Commercial | Real-time data | 131k | -Line | Grok models, X integration |
| **DeepSeek** | Commercial | Cost-effective | 64k | $ | Extremely cheap reasoning |
| **Groq** | Commercial | Speed | Various | $ | Ultra-fast inference |
| **Mistral** | Commercial | Open weights | 131k | -Line | Enterprise-grade |
| **Cohere** | Commercial | Search, rerank | 128k | -Line | RAG optimization |
| **Together** | Commercial | Open-source | 130k | -Line | 100+ models |
| **Perplexity** | Commercial | Search + AI | 127k | -Line | Web citations |
| **OpenRouter** | Gateway | Unified access | Various | Variable | 200+ models |
| **Fireworks** | Commercial | Production | 131k | -Line | Fast, reliable |
| **Ollama** | Self-hosted | Local models | Various | Free | Easy setup |
| **LM Studio** | Self-hosted | GUI interface | Various | Free | Beginner-friendly |
| **vLLM** | Self-hosted | High throughput | Various | Free | Production-grade |
| **llama.cpp** | Self-hosted | CPU inference | Various | Free | Resource-efficient |
| **LocalAI** | Self-hosted | OpenAI compat | Various | Free | Docker-ready |
| **Jan** | Self-hosted | Desktop app | Various | Free | Privacy-focused |

**Legend**:
- $ = Budget-friendly (<\/M tokens)
- -Line = Moderate (<\/M tokens)
- -Line$ = Premium (>\/M tokens)

---

## Choosing the Right Provider

### For Production Applications

1. **High reliability**: OpenAI, Anthropic
2. **Cost optimization**: DeepSeek, Groq, Together
3. **Speed critical**: Groq, Fireworks
4. **Long context**: Google (2M), Anthropic (200k)

### For Development

1. **Prototyping**: OpenRouter (try many models)
2. **Local testing**: LM Studio, Ollama
3. **Experimentation**: text-generation-webui

### For Self-Hosting

1. **Production**: vLLM (GPU), llama.cpp (CPU)
2. **Easy setup**: LM Studio, Jan
3. **Docker**: LocalAI
4. **Features**: text-generation-webui

### For Specialized Use Cases

1. **Search-enhanced**: Perplexity
2. **Vision**: GPT-4V, Pixtral, Gemini
3. **Reasoning**: DeepSeek Reasoner, Claude
4. **Code**: GPT-4, Claude 3.5

---

## Total Provider Count

**Paracle now supports 14+ providers with 50+ models:**

- **8 Commercial**: OpenAI, Anthropic, Google, xAI, DeepSeek, Groq, Mistral, Cohere, Together, Perplexity, OpenRouter, Fireworks
- **6 Self-Hosted**: Ollama, LM Studio, vLLM, llama.cpp, text-generation-webui, LocalAI, Jan
- **Plus**: Any OpenAI-compatible API via `OpenAICompatibleProvider`

