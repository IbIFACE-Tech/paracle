"""Generic OpenAI-compatible provider wrapper."""

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
from paracle_providers.exceptions import LLMProviderError


class OpenAICompatibleProvider(LLMProvider):
    """
    Generic provider for OpenAI-compatible APIs.

    Works with any service that implements OpenAI's chat completions API,
    including LM Studio, Together.ai, Perplexity, and many others.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        provider_name: str = "openai-compatible",
        **kwargs: Any,
    ):
        """
        Initialize OpenAI-compatible provider.

        Args:
            api_key: API key (provider-specific)
            base_url: Base URL for the API (e.g., http://localhost:1234/v1)
            provider_name: Name identifier for this provider instance
            **kwargs: Additional configuration
        """
        if not base_url:
            raise ValueError(
                "base_url is required for OpenAI-compatible provider. "
                "Example: http://localhost:1234/v1"
            )

        # API key may be optional for local servers
        api_key = api_key or os.getenv("OPENAI_COMPATIBLE_API_KEY")

        super().__init__(api_key=api_key, **kwargs)
        self.base_url = base_url.rstrip("/")
        self.provider_name = provider_name

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=kwargs.get("timeout", 30.0),
        )

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate chat completion using OpenAI-compatible API."""
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
        if config.frequency_penalty:
            payload["frequency_penalty"] = config.frequency_penalty
        if config.presence_penalty:
            payload["presence_penalty"] = config.presence_penalty
        if config.stop_sequences:
            payload["stop"] = config.stop_sequences

        # Add any provider-specific parameters
        payload.update(kwargs)

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
                    "provider": self.provider_name,
                    "base_url": self.base_url,
                    "raw_response": data,
                },
            )

        except httpx.HTTPStatusError as e:
            raise LLMProviderError(
                f"{self.provider_name} API error: {e.response.status_code} - {e.response.text}"
            ) from e
        except Exception as e:
            raise LLMProviderError(f"{self.provider_name} provider error: {e}") from e

    async def stream_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream chat completion from OpenAI-compatible API."""
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

        # Add any provider-specific parameters
        payload.update(kwargs)

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

                        try:
                            data = json.loads(data_str)
                            choice = data["choices"][0]
                            delta = choice.get("delta", {})

                            if content := delta.get("content"):
                                yield StreamChunk(
                                    content=content,
                                    finish_reason=choice.get("finish_reason"),
                                )
                        except json.JSONDecodeError:
                            # Skip malformed lines
                            continue

        except httpx.HTTPStatusError as e:
            raise LLMProviderError(
                f"{self.provider_name} streaming error: {e.response.status_code}"
            ) from e
        except Exception as e:
            raise LLMProviderError(f"{self.provider_name} streaming error: {e}") from e

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()


# Factory functions for common providers


def create_lmstudio_provider(
    model: str = "local-model", port: int = 1234, **kwargs: Any
) -> OpenAICompatibleProvider:
    """
    Create provider for LM Studio.

    Args:
        model: Model name loaded in LM Studio
        port: LM Studio server port
        **kwargs: Additional configuration

    Returns:
        Configured provider
    """
    return OpenAICompatibleProvider(
        base_url=f"http://localhost:{port}/v1",
        provider_name="lmstudio",
        **kwargs,
    )


def create_together_provider(
    api_key: str | None = None, **kwargs: Any
) -> OpenAICompatibleProvider:
    """
    Create provider for Together.ai.

    Args:
        api_key: Together.ai API key
        **kwargs: Additional configuration

    Returns:
        Configured provider
    """
    return OpenAICompatibleProvider(
        api_key=api_key or os.getenv("TOGETHER_API_KEY"),
        base_url="https://api.together.xyz/v1",
        provider_name="together",
        **kwargs,
    )


def create_perplexity_provider(
    api_key: str | None = None, **kwargs: Any
) -> OpenAICompatibleProvider:
    """
    Create provider for Perplexity.

    Args:
        api_key: Perplexity API key
        **kwargs: Additional configuration

    Returns:
        Configured provider
    """
    return OpenAICompatibleProvider(
        api_key=api_key or os.getenv("PERPLEXITY_API_KEY"),
        base_url="https://api.perplexity.ai",
        provider_name="perplexity",
        **kwargs,
    )


def create_vllm_provider(
    base_url: str = "http://localhost:8000/v1", **kwargs: Any
) -> OpenAICompatibleProvider:
    """
    Create provider for vLLM self-hosted inference server.

    Args:
        base_url: vLLM server URL
        **kwargs: Additional configuration

    Returns:
        Configured provider

    Example:
        >>> provider = create_vllm_provider("http://localhost:8000/v1")
        >>> response = await provider.chat_completion(
        ...     messages=[ChatMessage(role="user", content="Hello")],
        ...     config=LLMConfig(),
        ...     model="meta-llama/Llama-3-8b-hf"
        ... )
    """
    return OpenAICompatibleProvider(
        base_url=base_url,
        provider_name="vllm",
        **kwargs,
    )


def create_text_generation_webui_provider(
    base_url: str = "http://localhost:5000/v1", **kwargs: Any
) -> OpenAICompatibleProvider:
    """
    Create provider for text-generation-webui (oobabooga).

    Args:
        base_url: text-generation-webui API URL
        **kwargs: Additional configuration

    Returns:
        Configured provider

    Example:
        >>> provider = create_text_generation_webui_provider()
        >>> response = await provider.chat_completion(...)
    """
    return OpenAICompatibleProvider(
        base_url=base_url,
        provider_name="text-generation-webui",
        **kwargs,
    )


def create_llamacpp_provider(
    base_url: str = "http://localhost:8080/v1", **kwargs: Any
) -> OpenAICompatibleProvider:
    """
    Create provider for llama.cpp server.

    Args:
        base_url: llama.cpp server URL
        **kwargs: Additional configuration

    Returns:
        Configured provider

    Example:
        >>> provider = create_llamacpp_provider()
        >>> response = await provider.chat_completion(...)
    """
    return OpenAICompatibleProvider(
        base_url=base_url,
        provider_name="llamacpp",
        **kwargs,
    )


def create_localai_provider(
    base_url: str = "http://localhost:8080/v1", **kwargs: Any
) -> OpenAICompatibleProvider:
    """
    Create provider for LocalAI.

    Args:
        base_url: LocalAI server URL
        **kwargs: Additional configuration

    Returns:
        Configured provider

    Example:
        >>> provider = create_localai_provider()
        >>> response = await provider.chat_completion(...)
    """
    return OpenAICompatibleProvider(
        base_url=base_url,
        provider_name="localai",
        **kwargs,
    )


def create_jan_provider(
    base_url: str = "http://localhost:1337/v1", **kwargs: Any
) -> OpenAICompatibleProvider:
    """
    Create provider for Jan (local AI desktop app).

    Args:
        base_url: Jan server URL
        **kwargs: Additional configuration

    Returns:
        Configured provider

    Example:
        >>> provider = create_jan_provider()
        >>> response = await provider.chat_completion(...)
    """
    return OpenAICompatibleProvider(
        base_url=base_url,
        provider_name="jan",
        **kwargs,
    )


def create_anyscale_provider(
    api_key: str | None = None, **kwargs: Any
) -> OpenAICompatibleProvider:
    """
    Create provider for Anyscale Endpoints.

    Args:
        api_key: Anyscale API key
        **kwargs: Additional configuration

    Returns:
        Configured provider

    Example:
        >>> provider = create_anyscale_provider()
        >>> response = await provider.chat_completion(...)
    """
    return OpenAICompatibleProvider(
        api_key=api_key or os.getenv("ANYSCALE_API_KEY"),
        base_url="https://api.endpoints.anyscale.com/v1",
        provider_name="anyscale",
        **kwargs,
    )


def create_cloudflare_provider(
    api_key: str | None = None, account_id: str | None = None, **kwargs: Any
) -> OpenAICompatibleProvider:
    """
    Create provider for Cloudflare Workers AI.

    Args:
        api_key: Cloudflare API key
        account_id: Cloudflare account ID
        **kwargs: Additional configuration

    Returns:
        Configured provider

    Example:
        >>> provider = create_cloudflare_provider(
        ...     api_key="your-key",
        ...     account_id="your-account-id"
        ... )
    """
    account_id = account_id or os.getenv("CLOUDFLARE_ACCOUNT_ID")
    if not account_id:
        raise ValueError(
            "Cloudflare account_id required. Set CLOUDFLARE_ACCOUNT_ID "
            "or pass account_id parameter."
        )

    return OpenAICompatibleProvider(
        api_key=api_key or os.getenv("CLOUDFLARE_API_KEY"),
        base_url=f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1",
        provider_name="cloudflare",
        **kwargs,
    )
