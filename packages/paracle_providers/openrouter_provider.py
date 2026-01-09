"""OpenRouter provider implementation."""

import os
from collections.abc import AsyncIterator
from typing import Any

import httpx

from paracle_providers.base import (
    ChatMessage,
    LLMConfig,
    LLMProvider,
    LLMResponse,
    StreamChunk,
    TokenUsage,
)
from paracle_providers.capabilities import (
    ModelCapability,
    ModelInfo,
    ProviderInfo,
    get_model_catalog,
)
from paracle_providers.exceptions import LLMProviderError


class OpenRouterProvider(LLMProvider):
    """
    OpenRouter provider implementation.

    Unified access to 200+ models from multiple providers.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://openrouter.ai/api/v1",
        **kwargs: Any,
    ):
        """
        Initialize OpenRouter provider.

        Args:
            api_key: OpenRouter API key (or set OPENROUTER_API_KEY env var)
            base_url: API base URL
            **kwargs: Additional configuration
        """
        api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenRouter API key required. Set OPENROUTER_API_KEY or "
                "pass api_key parameter."
            )

        super().__init__(api_key=api_key, **kwargs)
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": kwargs.get("referer", "https://paracle.ai"),
                "X-Title": kwargs.get("app_name", "Paracle"),
            },
            timeout=kwargs.get("timeout", 60.0),
        )

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate chat completion using OpenRouter."""
        formatted_messages = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]

        payload = {
            "model": model,
            "messages": formatted_messages,
            "temperature": config.temperature,
            "stream": False,
        }

        if config.max_tokens:
            payload["max_tokens"] = config.max_tokens
        if config.top_p:
            payload["top_p"] = config.top_p

        try:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            choice = data["choices"][0]
            usage_data = data.get("usage", {})

            return LLMResponse(
                content=choice["message"]["content"],
                finish_reason=choice.get("finish_reason"),
                usage=TokenUsage(
                    prompt_tokens=usage_data.get("prompt_tokens", 0),
                    completion_tokens=usage_data.get("completion_tokens", 0),
                    total_tokens=usage_data.get("total_tokens", 0),
                ),
                model=data.get("model", model),
                metadata={
                    "provider": "openrouter",
                    "raw_response": data,
                },
            )

        except httpx.HTTPStatusError as e:
            raise LLMProviderError(
                f"OpenRouter API error: {e.response.status_code} - "
                f"{e.response.text}"
            ) from e
        except Exception as e:
            raise LLMProviderError(f"OpenRouter provider error: {e}") from e

    async def stream_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream chat completion from OpenRouter."""
        formatted_messages = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]

        payload = {
            "model": model,
            "messages": formatted_messages,
            "temperature": config.temperature,
            "stream": True,
        }

        if config.max_tokens:
            payload["max_tokens"] = config.max_tokens

        try:
            async with self.client.stream(
                "POST", "/chat/completions", json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break

                        import json

                        data = json.loads(data_str)
                        choice = data["choices"][0]
                        delta = choice.get("delta", {})

                        if content := delta.get("content"):
                            yield StreamChunk(
                                content=content,
                                finish_reason=choice.get("finish_reason"),
                            )

        except httpx.HTTPStatusError as e:
            raise LLMProviderError(
                f"OpenRouter streaming error: {e.response.status_code}"
            ) from e
        except Exception as e:
            raise LLMProviderError(f"OpenRouter streaming error: {e}") from e

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()


# Register provider in catalog
_openrouter_provider = ProviderInfo(
    provider_id="openrouter",
    display_name="OpenRouter",
    description="Unified gateway to 200+ models from multiple providers",
    website="https://openrouter.ai",
    api_docs="https://openrouter.ai/docs",
    requires_api_key=True,
    supports_streaming=True,
    models=[
        ModelInfo(
            model_id="anthropic/claude-3.5-sonnet",
            provider="openrouter",
            display_name="Claude 3.5 Sonnet (via OpenRouter)",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.TOOL_CALLING,
                ModelCapability.LONG_CONTEXT,
            ],
            context_window=200000,
            metadata={"gateway": True, "underlying_provider": "anthropic"},
        ),
        ModelInfo(
            model_id="openai/gpt-4-turbo",
            provider="openrouter",
            display_name="GPT-4 Turbo (via OpenRouter)",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.TOOL_CALLING,
                ModelCapability.IMAGE_INPUT,
            ],
            context_window=128000,
            metadata={"gateway": True, "underlying_provider": "openai"},
        ),
        ModelInfo(
            model_id="google/gemini-pro-1.5",
            provider="openrouter",
            display_name="Gemini Pro 1.5 (via OpenRouter)",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.LONG_CONTEXT,
            ],
            context_window=2000000,
            metadata={"gateway": True, "underlying_provider": "google"},
        ),
    ],
)

get_model_catalog().register_provider(_openrouter_provider)
