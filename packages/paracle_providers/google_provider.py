"""Google Gemini provider implementation with retry support."""

import os
from collections.abc import AsyncIterator
from typing import Any

try:
    import google.genai as genai
except ImportError:
    raise ImportError(
        "google-genai package is required for Google provider. "
        "Install it with: pip install google-genai"
    )

from paracle_providers.base import (
    ChatMessage,
    LLMConfig,
    LLMProvider,
    LLMResponse,
    StreamChunk,
    TokenUsage,
)
from paracle_providers.exceptions import LLMProviderError, ProviderAuthenticationError
from paracle_providers.retry import RetryableProvider, RetryConfig


class GoogleProvider(LLMProvider, RetryableProvider):
    """
    Google Gemini LLM provider with automatic retry support.

    Supports Gemini Pro, Gemini Pro Vision, and other Google models.
    Includes exponential backoff with jitter for transient failures.
    """

    def __init__(
        self,
        api_key: str | None = None,
        retry_config: RetryConfig | None = None,
        **kwargs,
    ):
        """
        Initialize Google provider.

        Args:
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
            retry_config: Configuration for retry behavior (optional)
            **kwargs: Additional configuration
        """
        super().__init__(api_key=api_key, **kwargs)

        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)

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
        Generate a chat completion using Google Gemini with automatic retry.

        Uses exponential backoff with jitter for transient failures.

        Args:
            messages: List of chat messages
            config: LLM configuration
            model: Model name (e.g., "gemini-pro")
            **kwargs: Additional Google-specific parameters

        Returns:
            LLMResponse with generated content

        Raises:
            LLMProviderError: On Google API errors after retries exhausted
        """

        async def _make_request() -> LLMResponse:
            return await self._raw_chat_completion(messages, config, model, **kwargs)

        operation_name = f"google.chat_completion({model})"
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
            # Create model instance
            gen_model = genai.GenerativeModel(model)

            # Convert messages to Google format
            # Google uses a simpler format: just concatenate user messages
            # System message becomes part of the prompt
            full_prompt = ""
            for msg in messages:
                if msg.role == "system":
                    full_prompt += f"{msg.content}\n\n"
                elif msg.role == "user":
                    full_prompt += f"User: {msg.content}\n"
                elif msg.role == "assistant":
                    full_prompt += f"Assistant: {msg.content}\n"

            # Generate response
            generation_config = genai.GenerationConfig(
                temperature=config.temperature,
                max_output_tokens=config.max_tokens,
                top_p=config.top_p,
            )

            response = await gen_model.generate_content_async(
                full_prompt,
                generation_config=generation_config,
            )

            return LLMResponse(
                content=response.text,
                finish_reason="stop" if response.candidates else "unknown",
                usage=TokenUsage(
                    prompt_tokens=getattr(
                        response.usage_metadata, "prompt_token_count", 0
                    ),
                    completion_tokens=getattr(
                        response.usage_metadata, "candidates_token_count", 0
                    ),
                    total_tokens=getattr(
                        response.usage_metadata, "total_token_count", 0
                    ),
                ),
                model=model,
                metadata={
                    "candidates": (
                        len(response.candidates) if response.candidates else 0
                    ),
                },
            )

        except Exception as e:
            if "api_key" in str(e).lower():
                raise ProviderAuthenticationError(str(e), provider="google") from e
            raise LLMProviderError(
                str(e), provider="google", model=model, original_error=e
            ) from e

    async def stream_chat_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream a chat completion using Google Gemini.

        Args:
            messages: List of chat messages
            config: LLM configuration
            model: Model name
            **kwargs: Additional Google-specific parameters

        Yields:
            StreamChunk objects with incremental content

        Raises:
            LLMProviderError: On Google API errors
        """
        try:
            gen_model = genai.GenerativeModel(model)

            # Convert messages
            full_prompt = ""
            for msg in messages:
                if msg.role == "system":
                    full_prompt += f"{msg.content}\n\n"
                elif msg.role == "user":
                    full_prompt += f"User: {msg.content}\n"
                elif msg.role == "assistant":
                    full_prompt += f"Assistant: {msg.content}\n"

            generation_config = genai.GenerationConfig(
                temperature=config.temperature,
                max_output_tokens=config.max_tokens,
                top_p=config.top_p,
            )

            response = await gen_model.generate_content_async(
                full_prompt,
                generation_config=generation_config,
                stream=True,
            )

            async for chunk in response:
                if chunk.text:
                    yield StreamChunk(
                        content=chunk.text,
                        metadata={"model": model},
                    )

        except Exception as e:
            raise LLMProviderError(
                str(e), provider="google", model=model, original_error=e
            ) from e

    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate Google-specific configuration."""
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
        return "google"

    @property
    def supported_models(self) -> list[str]:
        """Return list of supported models."""
        return [
            "gemini-pro",
            "gemini-pro-vision",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]
