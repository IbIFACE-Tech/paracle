"""xAI Grok provider implementation."""

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


class XAIProvider(LLMProvider):
    """
    xAI Grok provider implementation.

    Uses OpenAI-compatible API at https://api.x.ai/v1
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.x.ai/v1",
        **kwargs: Any,
    ):
        """
        Initialize xAI provider.

        Args:
            api_key: xAI API key (or set XAI_API_KEY env var)
            base_url: API base URL
            **kwargs: Additional configuration
        """
        api_key = api_key or os.getenv("XAI_API_KEY")
        if not api_key:
            raise ValueError(
                "xAI API key required. Set XAI_API_KEY or pass api_key parameter."
            )

        super().__init__(api_key=api_key, **kwargs)
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=kwargs.get("timeout", 30.0),
        )

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate chat completion using xAI Grok."""
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
        if config.stop_sequences:
            payload["stop"] = config.stop_sequences

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
                metadata={"provider": "xai", "raw_response": data},
            )

        except httpx.HTTPStatusError as e:
            raise LLMProviderError(
                f"xAI API error: {e.response.status_code} - {e.response.text}"
            ) from e
        except Exception as e:
            raise LLMProviderError(f"xAI provider error: {e}") from e

    async def stream_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream chat completion from xAI Grok."""
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
                f"xAI streaming error: {e.response.status_code}"
            ) from e
        except Exception as e:
            raise LLMProviderError(f"xAI streaming error: {e}") from e

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()


# Register provider in catalog
_xai_provider = ProviderInfo(
    provider_id="xai",
    display_name="xAI",
    description="xAI's Grok language models with extended context and reasoning",
    website="https://x.ai",
    api_docs="https://docs.x.ai/api",
    requires_api_key=True,
    supports_streaming=True,
    models=[
        ModelInfo(
            model_id="grok-2-1212",
            provider="xai",
            display_name="Grok 2 (1212)",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.TOOL_CALLING,
                ModelCapability.LONG_CONTEXT,
            ],
            context_window=131072,
        ),
        ModelInfo(
            model_id="grok-2-vision-1212",
            provider="xai",
            display_name="Grok 2 Vision (1212)",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.IMAGE_INPUT,
                ModelCapability.TOOL_CALLING,
                ModelCapability.LONG_CONTEXT,
            ],
            context_window=131072,
        ),
        ModelInfo(
            model_id="grok-beta",
            provider="xai",
            display_name="Grok Beta",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.TOOL_CALLING,
            ],
            context_window=131072,
        ),
    ],
)

get_model_catalog().register_provider(_xai_provider)
