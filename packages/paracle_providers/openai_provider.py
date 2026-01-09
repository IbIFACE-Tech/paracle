"""OpenAI provider implementation with retry support."""

import os
from collections.abc import AsyncIterator
from typing import Any

try:
    from openai import AsyncOpenAI, OpenAIError, RateLimitError
except ImportError:
    raise ImportError(
        "openai package is required for OpenAI provider. "
        "Install it with: pip install openai"
    )

from paracle_providers.base import (
    ChatMessage,
    LLMConfig,
    LLMProvider,
    LLMResponse,
    StreamChunk,
    TokenUsage,
)
from paracle_providers.exceptions import (
    LLMProviderError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from paracle_providers.retry import RetryableProvider, RetryConfig


class OpenAIProvider(LLMProvider, RetryableProvider):
    """
    OpenAI LLM provider with automatic retry support.

    Supports GPT-4, GPT-3.5, and other OpenAI models.
    Includes exponential backoff with jitter for transient failures.

    Example:
        >>> provider = OpenAIProvider(api_key="sk-...")
        >>> # Configure retry behavior
        >>> provider.configure_retry(RetryConfig(max_attempts=5))
        >>> response = await provider.chat_completion(msgs, cfg, "gpt-4")
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        organization: str | None = None,
        retry_config: RetryConfig | None = None,
        **kwargs,
    ):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            base_url: Optional custom base URL
            organization: Optional organization ID
            retry_config: Configuration for retry behavior (optional)
            **kwargs: Additional OpenAI client configuration
        """
        super().__init__(api_key=api_key, **kwargs)

        self.client = AsyncOpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=base_url,
            organization=organization,
            **kwargs,
        )

        # Initialize retry configuration
        if retry_config:
            self.configure_retry(retry_config)

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs,
    ) -> LLMResponse:
        """
        Generate a chat completion using OpenAI with automatic retry.

        Uses exponential backoff with jitter for transient failures
        (rate limits, timeouts, connection errors).

        Args:
            messages: List of chat messages
            config: LLM configuration
            model: Model name (e.g., "gpt-4", "gpt-3.5-turbo")
            **kwargs: Additional OpenAI-specific parameters

        Returns:
            LLMResponse with generated content

        Raises:
            LLMProviderError: On OpenAI API errors after retries exhausted
            ProviderRateLimitError: On rate limit exceeded after retries
            ProviderTimeoutError: On timeout after retries
        """

        async def _make_request() -> LLMResponse:
            return await self._raw_chat_completion(messages, config, model, **kwargs)

        operation_name = f"openai.chat_completion({model})"
        return await self.with_retry(_make_request, operation_name)

    async def _raw_chat_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs,
    ) -> LLMResponse:
        """Raw chat completion without retry wrapper."""
        try:
            # Convert ChatMessage to OpenAI format
            openai_messages = [
                {
                    "role": msg.role,
                    "content": msg.content,
                    **({"name": msg.name} if msg.name else {}),
                    **({"tool_call_id": msg.tool_call_id} if msg.tool_call_id else {}),
                    **({"tool_calls": msg.tool_calls} if msg.tool_calls else {}),
                }
                for msg in messages
            ]

            # Build request parameters
            params = {
                "model": model,
                "messages": openai_messages,
                "temperature": config.temperature,
                "timeout": config.timeout,
            }

            if config.max_tokens is not None:
                params["max_tokens"] = config.max_tokens
            if config.top_p is not None:
                params["top_p"] = config.top_p
            if config.frequency_penalty is not None:
                params["frequency_penalty"] = config.frequency_penalty
            if config.presence_penalty is not None:
                params["presence_penalty"] = config.presence_penalty
            if config.stop_sequences:
                params["stop"] = config.stop_sequences

            # Add custom parameters
            params.update(kwargs)

            # Make API call
            response = await self.client.chat.completions.create(**params)

            # Extract response
            choice = response.choices[0]
            usage = response.usage

            return LLMResponse(
                content=choice.message.content or "",
                finish_reason=choice.finish_reason,
                usage=TokenUsage(
                    prompt_tokens=usage.prompt_tokens if usage else 0,
                    completion_tokens=usage.completion_tokens if usage else 0,
                    total_tokens=usage.total_tokens if usage else 0,
                ),
                model=response.model,
                tool_calls=(
                    choice.message.tool_calls
                    if hasattr(choice.message, "tool_calls")
                    else None
                ),
                metadata={
                    "id": response.id,
                    "created": response.created,
                    "system_fingerprint": getattr(response, "system_fingerprint", None),
                },
            )

        except RateLimitError as e:
            raise ProviderRateLimitError(
                str(e),
                provider="openai",
                retry_after=getattr(e, "retry_after", None),
            ) from e
        except OpenAIError as e:
            if "authentication" in str(e).lower():
                raise ProviderAuthenticationError(str(e), provider="openai") from e
            if "timeout" in str(e).lower():
                raise ProviderTimeoutError(
                    str(e), provider="openai", timeout=config.timeout
                ) from e
            raise LLMProviderError(
                str(e), provider="openai", model=model, original_error=e
            ) from e

    async def stream_chat_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream a chat completion using OpenAI.

        Args:
            messages: List of chat messages
            config: LLM configuration
            model: Model name
            **kwargs: Additional OpenAI-specific parameters

        Yields:
            StreamChunk objects with incremental content

        Raises:
            LLMProviderError: On OpenAI API errors
        """
        try:
            # Convert messages
            openai_messages = [
                {
                    "role": msg.role,
                    "content": msg.content,
                    **({"name": msg.name} if msg.name else {}),
                }
                for msg in messages
            ]

            # Build request parameters
            params = {
                "model": model,
                "messages": openai_messages,
                "temperature": config.temperature,
                "stream": True,
                "timeout": config.timeout,
            }

            if config.max_tokens is not None:
                params["max_tokens"] = config.max_tokens
            if config.top_p is not None:
                params["top_p"] = config.top_p

            params.update(kwargs)

            # Stream response
            stream = await self.client.chat.completions.create(**params)

            async for chunk in stream:
                delta = chunk.choices[0].delta
                finish_reason = chunk.choices[0].finish_reason

                tool_calls = delta.tool_calls if hasattr(delta, "tool_calls") else None
                yield StreamChunk(
                    content=delta.content or "",
                    finish_reason=finish_reason,
                    tool_calls=tool_calls,
                    metadata={"id": chunk.id, "model": chunk.model},
                )

        except OpenAIError as e:
            raise LLMProviderError(
                str(e), provider="openai", model=model, original_error=e
            ) from e

    def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate OpenAI-specific configuration.

        Args:
            config: Configuration dictionary

        Returns:
            True if valid

        Raises:
            ValueError: If configuration is invalid
        """
        if "model" in config and not isinstance(config["model"], str):
            raise ValueError("model must be a string")

        if "temperature" in config:
            temp = config["temperature"]
            if not isinstance(temp, int | float) or not 0 <= temp <= 2:
                raise ValueError("temperature must be between 0 and 2")

        return True

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "openai"

    @property
    def supported_models(self) -> list[str]:
        """Return list of supported models."""
        return [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            "gpt-4-0125-preview",
            "gpt-4-1106-preview",
            "gpt-4-32k",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-3.5-turbo-0125",
            "gpt-3.5-turbo-1106",
        ]
