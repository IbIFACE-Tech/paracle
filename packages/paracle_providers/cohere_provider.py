"""Cohere provider implementation."""

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


class CohereProvider(LLMProvider):
    """
    Cohere provider implementation.

    Specializes in embeddings, reranking, and chat.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.cohere.com/v1",
        **kwargs: Any,
    ):
        """
        Initialize Cohere provider.

        Args:
            api_key: Cohere API key (or set COHERE_API_KEY env var)
            base_url: API base URL
            **kwargs: Additional configuration
        """
        api_key = api_key or os.getenv("COHERE_API_KEY")
        if not api_key:
            raise ValueError(
                "Cohere API key required. Set COHERE_API_KEY or pass "
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
        """Generate chat completion using Cohere."""
        # Cohere uses different message format
        cohere_messages = []
        system_message = None

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                cohere_messages.append(
                    {
                        "role": "USER" if msg.role == "user" else "CHATBOT",
                        "message": msg.content,
                    }
                )

        payload = {
            "model": model,
            "chat_history": cohere_messages[:-1] if len(cohere_messages) > 1 else [],
            "message": cohere_messages[-1]["message"] if cohere_messages else "",
            "temperature": config.temperature,
            "stream": False,
        }

        if system_message:
            payload["preamble"] = system_message
        if config.max_tokens:
            payload["max_tokens"] = config.max_tokens

        try:
            response = await self.client.post("/chat", json=payload)
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                content=data["text"],
                finish_reason=data.get("finish_reason", "complete"),
                usage=TokenUsage(
                    prompt_tokens=data.get("meta", {})
                    .get("billed_units", {})
                    .get("input_tokens", 0),
                    completion_tokens=data.get("meta", {})
                    .get("billed_units", {})
                    .get("output_tokens", 0),
                    total_tokens=0,  # Calculated later
                ),
                model=model,
                metadata={"provider": "cohere", "raw_response": data},
            )

        except httpx.HTTPStatusError as e:
            raise LLMProviderError(
                f"Cohere API error: {e.response.status_code} - " f"{e.response.text}"
            ) from e
        except Exception as e:
            raise LLMProviderError(f"Cohere provider error: {e}") from e

    async def stream_chat_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream chat completion from Cohere (required abstract method)."""
        async for chunk in self.stream_completion(messages, config, model, **kwargs):
            yield chunk

    async def stream_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream chat completion from Cohere."""
        # Prepare messages
        cohere_messages = []
        system_message = None

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                cohere_messages.append(
                    {
                        "role": "USER" if msg.role == "user" else "CHATBOT",
                        "message": msg.content,
                    }
                )

        payload = {
            "model": model,
            "chat_history": cohere_messages[:-1] if len(cohere_messages) > 1 else [],
            "message": cohere_messages[-1]["message"] if cohere_messages else "",
            "temperature": config.temperature,
            "stream": True,
        }

        if system_message:
            payload["preamble"] = system_message

        try:
            async with self.client.stream("POST", "/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue

                    import json

                    try:
                        data = json.loads(line)
                        if data.get("event_type") == "text-generation":
                            if text := data.get("text"):
                                yield StreamChunk(content=text)
                        elif data.get("event_type") == "stream-end":
                            yield StreamChunk(content="", finish_reason="complete")
                    except json.JSONDecodeError:
                        continue

        except httpx.HTTPStatusError as e:
            raise LLMProviderError(
                f"Cohere streaming error: {e.response.status_code}"
            ) from e
        except Exception as e:
            raise LLMProviderError(f"Cohere streaming error: {e}") from e

    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate Cohere configuration."""
        return True  # Basic validation, can be enhanced

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "cohere"

    @property
    def supported_models(self) -> list[str]:
        """Return list of supported models."""
        return [
            "command-r-plus",
            "command-r",
            "command",
            "command-light",
            "command-nightly",
        ]

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()


# Register provider in catalog
_cohere_provider = ProviderInfo(
    provider_id="cohere",
    display_name="Cohere",
    description="Cohere's models specialized in embeddings, reranking, and chat",
    website="https://cohere.com",
    api_docs="https://docs.cohere.com",
    requires_api_key=True,
    supports_streaming=True,
    models=[
        ModelInfo(
            model_id="command-r-plus",
            provider="cohere",
            display_name="Command R+",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.TOOL_CALLING,
                ModelCapability.LONG_CONTEXT,
            ],
            context_window=128000,
            input_cost_per_million=2.5,
            output_cost_per_million=10.0,
        ),
        ModelInfo(
            model_id="command-r",
            provider="cohere",
            display_name="Command R",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.STREAMING,
                ModelCapability.TOOL_CALLING,
                ModelCapability.LONG_CONTEXT,
            ],
            context_window=128000,
            input_cost_per_million=0.15,
            output_cost_per_million=0.6,
        ),
        ModelInfo(
            model_id="command",
            provider="cohere",
            display_name="Command",
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.STREAMING,
            ],
            context_window=4096,
            input_cost_per_million=1.0,
            output_cost_per_million=2.0,
        ),
    ],
)

get_model_catalog().register_provider(_cohere_provider)
