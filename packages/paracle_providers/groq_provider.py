"""Groq provider implementation."""

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


class GroqProvider(LLMProvider):
    """
    Groq provider implementation.

    Ultra-fast inference for open-source models.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.groq.com/openai/v1",
        **kwargs: Any,
    ):
        """
        Initialize Groq provider.

        Args:
            api_key: Groq API key (or set GROQ_API_KEY env var)
            base_url: API base URL
            **kwargs: Additional configuration
        """
        api_key = api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "Groq API key required. Set GROQ_API_KEY or pass api_key parameter."
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
        """Generate chat completion using Groq."""
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
                metadata={"provider": "groq", "raw_response": data},
            )

        except httpx.HTTPStatusError as e:
            raise LLMProviderError(
                f"Groq API error: {e.response.status_code} - {e.response.text}"
            ) from e
        except Exception as e:
            raise LLMProviderError(f"Groq provider error: {e}") from e

    async def stream_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream chat completion from Groq."""
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
                f"Groq streaming error: {e.response.status_code}"
            ) from e
        except Exception as e:
            raise LLMProviderError(f"Groq streaming error: {e}") from e

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()


# Register provider in catalog
_groq_provider = ProviderInfo(
    provider_id="groq",
    display_name="Groq",
    description="Lightning-fast inference for open-source LLMs",
    website="https://groq.com",
    api_docs="https://console.groq.com/docs",
    requires_api_key=True,
    supports_streaming=True,
    models=[
        ModelInfo(
            model_id="llama-3.3-70b-versatile",
            provider="groq",
            display_name="Llama 3.3 70B",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.TOOL_CALLING,
            ],
            context_window=131072,
            input_cost_per_million=0.59,
            output_cost_per_million=0.79,
        ),
        ModelInfo(
            model_id="llama-3.1-8b-instant",
            provider="groq",
            display_name="Llama 3.1 8B Instant",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.STREAMING,
            ],
            context_window=131072,
            input_cost_per_million=0.05,
            output_cost_per_million=0.08,
            metadata={"speed": "ultra-fast", "use_case": "high-throughput"},
        ),
        ModelInfo(
            model_id="mixtral-8x7b-32768",
            provider="groq",
            display_name="Mixtral 8x7B",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.STREAMING,
            ],
            context_window=32768,
            input_cost_per_million=0.24,
            output_cost_per_million=0.24,
        ),
        ModelInfo(
            model_id="gemma2-9b-it",
            provider="groq",
            display_name="Gemma 2 9B",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.STREAMING,
            ],
            context_window=8192,
            input_cost_per_million=0.20,
            output_cost_per_million=0.20,
        ),
    ],
)

get_model_catalog().register_provider(_groq_provider)
