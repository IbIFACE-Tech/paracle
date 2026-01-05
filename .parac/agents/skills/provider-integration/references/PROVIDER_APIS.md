# Provider API Reference

Detailed documentation for integrating with various LLM providers.

## OpenAI API

### Authentication

```python
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")
```

### Chat Completion

```python
response = await openai.ChatCompletion.acreate(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    temperature=0.7,
    max_tokens=1000,
)

content = response.choices[0].message.content
```

### Streaming

```python
async for chunk in await openai.ChatCompletion.acreate(
    model="gpt-4",
    messages=messages,
    stream=True,
):
    if chunk.choices[0].delta.content:
        yield chunk.choices[0].delta.content
```

### Function Calling

```python
functions = [{
    "name": "get_weather",
    "description": "Get current weather",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {"type": "string"}
        },
        "required": ["location"]
    }
}]

response = await openai.ChatCompletion.acreate(
    model="gpt-4",
    messages=messages,
    functions=functions,
)
```

## Anthropic API

### Authentication

```python
from anthropic import AsyncAnthropic

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
```

### Messages API

```python
response = await client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    system="You are a helpful assistant.",
)

content = response.content[0].text
```

### Streaming

```python
async with client.messages.stream(
    model="claude-3-sonnet-20240229",
    max_tokens=1024,
    messages=messages,
) as stream:
    async for text in stream.text_stream:
        yield text
```

### Tool Use

```python
tools = [{
    "name": "get_weather",
    "description": "Get current weather",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {"type": "string"}
        },
        "required": ["location"]
    }
}]

response = await client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1024,
    messages=messages,
    tools=tools,
)
```

## Azure OpenAI

### Authentication

```python
import openai

openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = "2024-02-01"
openai.api_key = os.getenv("AZURE_OPENAI_KEY")
```

### Chat Completion

```python
response = await openai.ChatCompletion.acreate(
    engine="gpt-4-deployment",  # Use deployment name, not model
    messages=messages,
    temperature=0.7,
)
```

## Ollama (Local)

### Setup

```python
import httpx

OLLAMA_BASE = "http://localhost:11434"
```

### Generate

```python
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{OLLAMA_BASE}/api/generate",
        json={
            "model": "llama2",
            "prompt": "Hello!",
            "stream": False,
        },
    )

    data = response.json()
    content = data["response"]
```

### Streaming

```python
async with httpx.AsyncClient() as client:
    async with client.stream(
        "POST",
        f"{OLLAMA_BASE}/api/generate",
        json={
            "model": "llama2",
            "prompt": prompt,
            "stream": True,
        },
    ) as response:
        async for line in response.aiter_lines():
            if line:
                data = json.loads(line)
                yield data.get("response", "")
```

## Error Handling

### OpenAI Errors

```python
from openai.error import (
    RateLimitError,
    APIError,
    InvalidRequestError,
)

try:
    response = await openai.ChatCompletion.acreate(...)
except RateLimitError:
    # Handle rate limit
    await asyncio.sleep(60)
    retry()
except APIError as e:
    # Handle API error
    logger.error(f"OpenAI API error: {e}")
except InvalidRequestError as e:
    # Handle invalid request
    logger.error(f"Invalid request: {e}")
```

### Anthropic Errors

```python
from anthropic import (
    RateLimitError,
    APIError,
)

try:
    response = await client.messages.create(...)
except RateLimitError:
    # Handle rate limit
    await asyncio.sleep(60)
except APIError as e:
    # Handle API error
    logger.error(f"Anthropic API error: {e}")
```

## Best Practices

1. **Always use environment variables** for API keys
2. **Implement retries** with exponential backoff
3. **Handle rate limits** gracefully
4. **Log API calls** for debugging
5. **Monitor costs** across providers
6. **Cache responses** when appropriate
7. **Use streaming** for long responses
8. **Validate inputs** before calling APIs

## Rate Limits

### OpenAI
- GPT-4: 10,000 TPM, 200 RPM (tier 1)
- GPT-3.5: 60,000 TPM, 3,500 RPM (tier 1)

### Anthropic
- Claude 3 Opus: 10,000 TPM, 50 RPM (free tier)
- Claude 3 Sonnet: 50,000 TPM, 200 RPM (free tier)

### Azure OpenAI
- Based on deployment configuration
- Typically 60K-240K TPM

## See Also

- [OpenAI API Docs](https://platform.openai.com/docs)
- [Anthropic API Docs](https://docs.anthropic.com/)
- [Azure OpenAI Docs](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Ollama Docs](https://github.com/ollama/ollama/blob/main/docs/api.md)
