"""Together.ai provider implementation."""

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


class TogetherProvider(LLMProvider):
    """
    Together.ai provider implementation.

    Fast inference for open-source models.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.together.xyz/v1",
        **kwargs: Any,
    ):
        """
        Initialize Together.ai provider.

        Args:
            api_key: Together API key (or set TOGETHER_API_KEY env var)
            base_url: API base URL
            **kwargs: Additional configuration
        """
        api_key = api_key or os.getenv("TOGETHER_API_KEY")
        if not api_key:
            raise ValueError(
                "Together.ai API key required. Set TOGETHER_API_KEY or pass "
                "api_key parameter."
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
        """Generate chat completion using Together.ai."""
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
                metadata={"provider": "together", "raw_response": data},
            )

        except httpx.HTTPStatusError as e:
            raise LLMProviderError(
                f"Together.ai API error: {e.response.status_code} - "
                f"{e.response.text}"
            ) from e
        except Exception as e:
            raise LLMProviderError(f"Together.ai provider error: {e}") from e

    async def stream_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream chat completion from Together.ai."""
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
                f"Together.ai streaming error: {e.response.status_code}"
            ) from e
        except Exception as e:
            raise LLMProviderError(f"Together.ai streaming error: {e}") from e

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()


# Register provider in catalog
_together_provider = ProviderInfo(
    provider_id="together",
    display_name="Together.ai",
    description="Fast inference for 100+ open-source models",
    website="https://together.ai",
    api_docs="https://docs.together.ai",
    requires_api_key=True,
    supports_streaming=True,
    models=[
        ModelInfo(
            model_id="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
            provider="together",
            display_name="Llama 3.1 405B Turbo",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.TOOL_CALLING,
                ModelCapability.LONG_CONTEXT,
            ],
            context_window=130000,
            input_cost_per_million=3.5,
            output_cost_per_million=3.5,
        ),
        ModelInfo(
            model_id="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            provider="together",
            display_name="Llama 3.1 70B Turbo",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.TOOL_CALLING,
                ModelCapability.LONG_CONTEXT,
            ],
            context_window=130000,
            input_cost_per_million=0.88,
            output_cost_per_million=0.88,
        ),
        ModelInfo(
            model_id="Qwen/Qwen2.5-72B-Instruct-Turbo",
            provider="together",
            display_name="Qwen 2.5 72B Turbo",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.LONG_CONTEXT,
            ],
            context_window=32768,
            input_cost_per_million=0.88,
            output_cost_per_million=0.88,
        ),
    ],
)

get_model_catalog().register_provider(_together_provider)
