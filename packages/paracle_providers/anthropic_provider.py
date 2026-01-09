"""Anthropic provider implementation with retry support."""

import os
from collections.abc import AsyncIterator
from typing import Any

try:
    from anthropic import AnthropicError, AsyncAnthropic, RateLimitError
except ImportError:
    raise ImportError(
        "anthropic package is required for Anthropic provider. "
        "Install it with: pip install anthropic"
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


class AnthropicProvider(LLMProvider, RetryableProvider):
    """
    Anthropic LLM provider with automatic retry support.

    Supports Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku, and more.
    Includes exponential backoff with jitter for transient failures.
    """

    def __init__(
        self,
        api_key: str | None = None,
        retry_config: RetryConfig | None = None,
        **kwargs,
    ):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            retry_config: Configuration for retry behavior (optional)
            **kwargs: Additional Anthropic client configuration
        """
        super().__init__(api_key=api_key, **kwargs)

        self.client = AsyncAnthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
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
        Generate a chat completion using Anthropic Claude with retry.

        Uses exponential backoff with jitter for transient failures.

        Args:
            messages: List of chat messages
            config: LLM configuration
            model: Model name (e.g., "claude-3-5-sonnet-20241022")
            **kwargs: Additional Anthropic-specific parameters

        Returns:
            LLMResponse with generated content

        Raises:
            LLMProviderError: On Anthropic API errors after retries
            ProviderRateLimitError: On rate limit exceeded after retries
        """

        async def _make_request() -> LLMResponse:
            return await self._raw_chat_completion(messages, config, model, **kwargs)

        operation_name = f"anthropic.chat_completion({model})"
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
            # Separate system message from conversation
            system_message = None
            conversation_messages = []

            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    conversation_messages.append(
                        {
                            "role": msg.role,
                            "content": msg.content,
                        }
                    )

            # Build request parameters
            params = {
                "model": model,
                "messages": conversation_messages,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens or 4096,  # Required for Anthropic
                "timeout": config.timeout,
            }

            if system_message:
                params["system"] = system_message

            if config.top_p is not None:
                params["top_p"] = config.top_p

            if config.stop_sequences:
                params["stop_sequences"] = config.stop_sequences

            # Add custom parameters
            params.update(kwargs)

            # Make API call
            response = await self.client.messages.create(**params)

            # Extract content
            content = ""
            if response.content:
                content = " ".join(
                    block.text for block in response.content if hasattr(block, "text")
                )

            return LLMResponse(
                content=content,
                finish_reason=response.stop_reason,
                usage=TokenUsage(
                    prompt_tokens=response.usage.input_tokens,
                    completion_tokens=response.usage.output_tokens,
                    total_tokens=response.usage.input_tokens
                    + response.usage.output_tokens,
                ),
                model=response.model,
                metadata={
                    "id": response.id,
                    "type": response.type,
                    "role": response.role,
                },
            )

        except RateLimitError as e:
            raise ProviderRateLimitError(
                str(e),
                provider="anthropic",
            ) from e
        except AnthropicError as e:
            if "authentication" in str(e).lower() or "api_key" in str(e).lower():
                raise ProviderAuthenticationError(str(e), provider="anthropic") from e
            if "timeout" in str(e).lower():
                raise ProviderTimeoutError(
                    str(e), provider="anthropic", timeout=config.timeout
                ) from e
            raise LLMProviderError(
                str(e), provider="anthropic", model=model, original_error=e
            ) from e

    async def stream_chat_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream a chat completion using Anthropic Claude.

        Args:
            messages: List of chat messages
            config: LLM configuration
            model: Model name
            **kwargs: Additional Anthropic-specific parameters

        Yields:
            StreamChunk objects with incremental content

        Raises:
            LLMProviderError: On Anthropic API errors
        """
        try:
            # Separate system message
            system_message = None
            conversation_messages = []

            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    conversation_messages.append(
                        {
                            "role": msg.role,
                            "content": msg.content,
                        }
                    )

            # Build request parameters
            params = {
                "model": model,
                "messages": conversation_messages,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens or 4096,
                "stream": True,
                "timeout": config.timeout,
            }

            if system_message:
                params["system"] = system_message

            if config.top_p is not None:
                params["top_p"] = config.top_p

            params.update(kwargs)

            # Stream response
            async with self.client.messages.stream(**params) as stream:
                async for event in stream:
                    # Handle different event types
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            yield StreamChunk(
                                content=event.delta.text,
                                metadata={"event_type": event.type},
                            )
                    elif event.type == "message_stop":
                        yield StreamChunk(
                            content="",
                            finish_reason="stop",
                            metadata={"event_type": event.type},
                        )

        except AnthropicError as e:
            raise LLMProviderError(
                str(e), provider="anthropic", model=model, original_error=e
            ) from e

    def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate Anthropic-specific configuration.

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
            if not isinstance(temp, int | float) or not 0 <= temp <= 1:
                raise ValueError("temperature must be between 0 and 1 for Anthropic")

        if "max_tokens" in config:
            max_tok = config["max_tokens"]
            if not isinstance(max_tok, int) or max_tok < 1:
                raise ValueError("max_tokens must be a positive integer")

        return True

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "anthropic"

    @property
    def supported_models(self) -> list[str]:
        """Return list of supported models."""
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-20240620",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2",
        ]
