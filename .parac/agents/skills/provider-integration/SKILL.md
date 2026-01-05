---
name: provider-integration
description: Configure and switch between LLM providers (OpenAI, Anthropic, Azure, Ollama). Use when managing AI model providers.
license: Apache-2.0
compatibility: Python 3.10+, Multiple LLM APIs
metadata:
  author: paracle-core-team
  version: "1.0.0"
  category: integration
  level: intermediate
  display_name: "Provider Integration"
  tags:
    - providers
    - llm
    - openai
    - anthropic
    - azure
  capabilities:
    - provider_configuration
    - multi_provider_support
    - provider_switching
  requirements:
    - skill_name: paracle-development
      min_level: basic
allowed-tools: Read Write
---

# Provider Integration Skill

## When to use this skill

Use when:
- Configuring LLM providers
- Switching between providers
- Adding new provider support
- Testing with different models
- Managing API keys and credentials

## Provider Configuration

```yaml
# .parac/providers/providers.yaml
providers:
  openai:
    api_key: ${OPENAI_API_KEY}
    default_model: gpt-4
    models:
      - gpt-4
      - gpt-4-turbo
      - gpt-3.5-turbo

  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    default_model: claude-3-sonnet
    models:
      - claude-3-opus
      - claude-3-sonnet
      - claude-3-haiku

  azure:
    api_key: ${AZURE_API_KEY}
    endpoint: ${AZURE_ENDPOINT}
    api_version: \"2024-02-01\"
    deployments:
      gpt4: gpt-4-deployment-name

  ollama:
    base_url: http://localhost:11434
    models:
      - llama2
      - codellama
      - mistral

default_provider: openai
```

## Agent Provider Assignment

```yaml
# Specify provider per agent
name: openai-agent
model: gpt-4
provider: openai

# Or use different provider
name: claude-agent
model: claude-3-sonnet
provider: anthropic

# Use local model
name: local-agent
model: llama2
provider: ollama
```

## Provider Implementation

```python
# packages/paracle_providers/custom_provider.py
from paracle_providers.base import Provider
from typing import AsyncIterator

class CustomProvider(Provider):
    \"\"\"Custom LLM provider implementation.\"\"\"

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url

    async def generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        **kwargs,
    ) -> str:
        \"\"\"Generate completion.\"\"\"
        response = await self._call_api(
            prompt=prompt,
            model=model,
            temperature=temperature,
        )
        return response[\"text\"]

    async def stream(
        self,
        prompt: str,
        model: str,
        **kwargs,
    ) -> AsyncIterator[str]:
        \"\"\"Stream completion.\"\"\"
        async for chunk in self._stream_api(prompt, model):
            yield chunk[\"text\"]
```

## Best Practices

1. **Use environment variables** for API keys
2. **Test with multiple providers** for compatibility
3. **Implement retries** for API failures
4. **Monitor costs** across providers
5. **Cache responses** when appropriate

## Resources

- Providers: `packages/paracle_providers/`
- Configuration: `.parac/providers/providers.yaml`
