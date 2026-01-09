"""Anthropic provider implementation.

This provider uses the Anthropic SDK to interact with Claude models.

Example:
    >>> from paracle_meta.capabilities.providers import AnthropicProvider
    >>> from paracle_meta.capabilities.provider_protocol import LLMRequest
    >>>
    >>> provider = AnthropicProvider(api_key="sk-ant-...")
    >>> await provider.initialize()
    >>>
    >>> request = LLMRequest(
    ...     prompt="Explain Python decorators",
    ...     temperature=0.7
    ... )
    >>> response = await provider.complete(request)
    >>> print(response.content)
"""

from __future__ import annotations

import os
import time
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from paracle_meta.capabilities.provider_protocol import (
    BaseProvider,
    LLMRequest,
    LLMResponse,
    LLMUsage,
    ProviderAPIError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    StreamChunk,
    ToolCallRequest,
)

if TYPE_CHECKING:
    pass


class ClaudeModels:
    """Available Claude model identifiers."""

    # Claude 4 models
    OPUS = "claude-opus-4-20250514"
    SONNET = "claude-sonnet-4-20250514"

    # Claude 3.5 models
    SONNET_35 = "claude-3-5-sonnet-20241022"
    HAIKU_35 = "claude-3-5-haiku-20241022"

    # Claude 3 models (legacy)
    OPUS_3 = "claude-3-opus-20240229"
    SONNET_3 = "claude-3-sonnet-20240229"
    HAIKU_3 = "claude-3-haiku-20240307"

    # Default
    DEFAULT = SONNET


class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider.

    Uses the Anthropic SDK to interact with Claude models.
    Supports completion, streaming, and tool use.

    Attributes:
        api_key: Anthropic API key.
        model: Default model to use.
        timeout: Request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = ClaudeModels.DEFAULT,
        timeout: float = 120.0,
        max_retries: int = 2,
    ):
        """Initialize Anthropic provider.

        Args:
            api_key: API key (defaults to ANTHROPIC_API_KEY env var).
            model: Default model to use.
            timeout: Request timeout in seconds.
            max_retries: Maximum retries for transient errors.
        """
        super().__init__(model=model)
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._timeout = timeout
        self._max_retries = max_retries
        self._client: Any = None

    @property
    def name(self) -> str:
        """Provider name."""
        return "anthropic"

    async def initialize(self) -> None:
        """Initialize the Anthropic client."""
        if not self._api_key:
            self._set_error("No API key provided")
            return

        try:
            import anthropic

            self._client = anthropic.AsyncAnthropic(
                api_key=self._api_key,
                timeout=self._timeout,
                max_retries=self._max_retries,
            )
            self._set_available()
        except ImportError:
            self._set_error("anthropic package not installed")
        except Exception as e:
            self._set_error(str(e))

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Generate completion using Claude.

        Args:
            request: The LLM request.

        Returns:
            LLM response with content and metadata.

        Raises:
            ProviderUnavailableError: If provider not initialized.
            ProviderAuthenticationError: If API key is invalid.
            ProviderRateLimitError: If rate limited.
            ProviderAPIError: For other API errors.
        """
        if not self._client:
            raise ProviderUnavailableError(self.name, "Not initialized")

        start_time = time.time()

        try:
            import anthropic

            # Build request parameters
            params = self._build_params(request)

            # Make API call
            response = await self._client.messages.create(**params)

            # Parse response
            return self._parse_response(response, start_time)

        except anthropic.AuthenticationError as e:
            self._set_error("Authentication failed")
            raise ProviderAuthenticationError(self.name) from e
        except anthropic.RateLimitError as e:
            self._set_rate_limited()
            retry_after = getattr(e, "retry_after", None)
            raise ProviderRateLimitError(self.name, retry_after) from e
        except anthropic.APIError as e:
            raise ProviderAPIError(
                self.name, str(e), getattr(e, "status_code", None)
            ) from e
        except Exception as e:
            raise ProviderAPIError(self.name, str(e)) from e

    async def stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        """Stream completion from Claude.

        Args:
            request: The LLM request.

        Yields:
            Stream chunks with partial content.

        Raises:
            ProviderError: If streaming fails.
        """
        if not self._client:
            raise ProviderUnavailableError(self.name, "Not initialized")

        try:
            import anthropic

            params = self._build_params(request)

            async with self._client.messages.stream(**params) as stream:
                async for event in stream:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            yield StreamChunk(content=event.delta.text)
                    elif event.type == "message_stop":
                        # Get final message for usage
                        final = await stream.get_final_message()
                        yield StreamChunk(
                            is_final=True,
                            usage=LLMUsage(
                                input_tokens=final.usage.input_tokens,
                                output_tokens=final.usage.output_tokens,
                            ),
                        )

        except anthropic.AuthenticationError as e:
            self._set_error("Authentication failed")
            raise ProviderAuthenticationError(self.name) from e
        except anthropic.RateLimitError as e:
            self._set_rate_limited()
            raise ProviderRateLimitError(self.name) from e
        except anthropic.APIError as e:
            raise ProviderAPIError(self.name, str(e)) from e

    def _build_params(self, request: LLMRequest) -> dict[str, Any]:
        """Build API request parameters."""
        messages = []

        for msg in request.get_messages():
            if msg.role == "system":
                continue  # System handled separately

            content: Any = msg.content
            if msg.tool_results:
                content = [
                    {
                        "type": "tool_result",
                        "tool_use_id": tr.tool_use_id,
                        "content": (
                            tr.content
                            if isinstance(tr.content, str)
                            else str(tr.content)
                        ),
                        "is_error": tr.is_error,
                    }
                    for tr in msg.tool_results
                ]

            messages.append({"role": msg.role, "content": content})

        params: dict[str, Any] = {
            "model": self._model or ClaudeModels.DEFAULT,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }

        # Add system prompt
        if request.system_prompt:
            params["system"] = request.system_prompt

        # Add tools
        if request.tools:
            params["tools"] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                }
                for tool in request.tools
            ]

        # Add tool choice
        if request.tool_choice:
            if isinstance(request.tool_choice, str):
                params["tool_choice"] = {"type": request.tool_choice}
            else:
                params["tool_choice"] = request.tool_choice

        # Add optional parameters
        if request.stop_sequences:
            params["stop_sequences"] = request.stop_sequences
        if request.top_p is not None:
            params["top_p"] = request.top_p
        if request.top_k is not None:
            params["top_k"] = request.top_k

        return params

    def _parse_response(self, response: Any, start_time: float) -> LLMResponse:
        """Parse Anthropic API response."""
        content = ""
        tool_calls: list[ToolCallRequest] = []

        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCallRequest(
                        id=block.id,
                        name=block.name,
                        input=block.input,
                    )
                )

        return LLMResponse(
            content=content,
            tool_calls=tool_calls if tool_calls else None,
            usage=LLMUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            ),
            provider=self.name,
            model=response.model,
            stop_reason=response.stop_reason,
            latency_ms=(time.time() - start_time) * 1000,
        )

    async def shutdown(self) -> None:
        """Shutdown the provider."""
        if self._client:
            # AsyncAnthropic doesn't need explicit close
            self._client = None
        await super().shutdown()
