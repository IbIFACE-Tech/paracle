"""OpenAI provider implementation.

This provider uses the OpenAI SDK to interact with GPT models.

Example:
    >>> from paracle_meta.capabilities.providers import OpenAIProvider
    >>> from paracle_meta.capabilities.provider_protocol import LLMRequest
    >>>
    >>> provider = OpenAIProvider(api_key="sk-...")
    >>> await provider.initialize()
    >>>
    >>> request = LLMRequest(prompt="Explain Python decorators")
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


class GPTModels:
    """Available GPT model identifiers."""

    # GPT-4o models
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"

    # GPT-4 Turbo
    GPT_4_TURBO = "gpt-4-turbo"

    # GPT-4 models
    GPT_4 = "gpt-4"

    # GPT-3.5 models
    GPT_35_TURBO = "gpt-3.5-turbo"

    # o1 reasoning models
    O1 = "o1"
    O1_MINI = "o1-mini"
    O1_PREVIEW = "o1-preview"

    # Default
    DEFAULT = GPT_4O


class OpenAIProvider(BaseProvider):
    """OpenAI GPT provider.

    Uses the OpenAI SDK to interact with GPT models.
    Supports completion, streaming, and tool use.

    Attributes:
        api_key: OpenAI API key.
        model: Default model to use.
        base_url: Custom API base URL (for Azure, etc.).
        organization: OpenAI organization ID.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = GPTModels.DEFAULT,
        base_url: str | None = None,
        organization: str | None = None,
        timeout: float = 120.0,
        max_retries: int = 2,
    ):
        """Initialize OpenAI provider.

        Args:
            api_key: API key (defaults to OPENAI_API_KEY env var).
            model: Default model to use.
            base_url: Custom API base URL.
            organization: Organization ID.
            timeout: Request timeout in seconds.
            max_retries: Maximum retries for transient errors.
        """
        super().__init__(model=model)
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._base_url = base_url
        self._organization = organization
        self._timeout = timeout
        self._max_retries = max_retries
        self._client: Any = None

    @property
    def name(self) -> str:
        """Provider name."""
        return "openai"

    async def initialize(self) -> None:
        """Initialize the OpenAI client."""
        if not self._api_key:
            self._set_error("No API key provided")
            return

        try:
            from openai import AsyncOpenAI

            kwargs: dict[str, Any] = {
                "api_key": self._api_key,
                "timeout": self._timeout,
                "max_retries": self._max_retries,
            }
            if self._base_url:
                kwargs["base_url"] = self._base_url
            if self._organization:
                kwargs["organization"] = self._organization

            self._client = AsyncOpenAI(**kwargs)
            self._set_available()
        except ImportError:
            self._set_error("openai package not installed")
        except Exception as e:
            self._set_error(str(e))

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Generate completion using GPT.

        Args:
            request: The LLM request.

        Returns:
            LLM response with content and metadata.

        Raises:
            ProviderError: If completion fails.
        """
        if not self._client:
            raise ProviderUnavailableError(self.name, "Not initialized")

        start_time = time.time()

        try:
            from openai import APIError, AuthenticationError, RateLimitError

            params = self._build_params(request)
            response = await self._client.chat.completions.create(**params)
            return self._parse_response(response, start_time)

        except AuthenticationError as e:
            self._set_error("Authentication failed")
            raise ProviderAuthenticationError(self.name) from e
        except RateLimitError as e:
            self._set_rate_limited()
            raise ProviderRateLimitError(self.name) from e
        except APIError as e:
            raise ProviderAPIError(
                self.name, str(e), getattr(e, "status_code", None)
            ) from e
        except Exception as e:
            raise ProviderAPIError(self.name, str(e)) from e

    async def stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        """Stream completion from GPT.

        Args:
            request: The LLM request.

        Yields:
            Stream chunks with partial content.
        """
        if not self._client:
            raise ProviderUnavailableError(self.name, "Not initialized")

        try:
            from openai import APIError, AuthenticationError, RateLimitError

            params = self._build_params(request)
            params["stream"] = True
            params["stream_options"] = {"include_usage": True}

            accumulated_content = ""

            async for chunk in await self._client.chat.completions.create(**params):
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    accumulated_content += content
                    yield StreamChunk(content=content)

                if chunk.usage:
                    yield StreamChunk(
                        is_final=True,
                        usage=LLMUsage(
                            input_tokens=chunk.usage.prompt_tokens,
                            output_tokens=chunk.usage.completion_tokens,
                        ),
                    )

        except AuthenticationError as e:
            self._set_error("Authentication failed")
            raise ProviderAuthenticationError(self.name) from e
        except RateLimitError as e:
            self._set_rate_limited()
            raise ProviderRateLimitError(self.name) from e
        except APIError as e:
            raise ProviderAPIError(self.name, str(e)) from e

    def _build_params(self, request: LLMRequest) -> dict[str, Any]:
        """Build API request parameters."""
        messages: list[dict[str, Any]] = []

        # Add system prompt
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})

        # Add conversation messages
        for msg in request.get_messages():
            if msg.role == "system":
                continue  # Already handled

            content: Any = msg.content
            message: dict[str, Any] = {"role": msg.role, "content": content}

            # Handle tool calls from assistant
            if msg.tool_calls:
                message["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": (
                                tc.input if isinstance(tc.input, str) else str(tc.input)
                            ),
                        },
                    }
                    for tc in msg.tool_calls
                ]

            messages.append(message)

            # Handle tool results (OpenAI uses separate messages)
            if msg.tool_results:
                for tr in msg.tool_results:
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tr.tool_use_id,
                            "content": (
                                tr.content
                                if isinstance(tr.content, str)
                                else str(tr.content)
                            ),
                        }
                    )

        params: dict[str, Any] = {
            "model": self._model or GPTModels.DEFAULT,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }

        # Add tools
        if request.tools:
            params["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema,
                    },
                }
                for tool in request.tools
            ]

        # Add tool choice
        if request.tool_choice:
            if isinstance(request.tool_choice, str):
                if request.tool_choice == "any":
                    params["tool_choice"] = "required"
                else:
                    params["tool_choice"] = request.tool_choice
            else:
                params["tool_choice"] = request.tool_choice

        # Add optional parameters
        if request.stop_sequences:
            params["stop"] = request.stop_sequences
        if request.top_p is not None:
            params["top_p"] = request.top_p

        return params

    def _parse_response(self, response: Any, start_time: float) -> LLMResponse:
        """Parse OpenAI API response."""
        choice = response.choices[0]
        message = choice.message

        content = message.content or ""
        tool_calls: list[ToolCallRequest] = []

        if message.tool_calls:
            import json

            for tc in message.tool_calls:
                try:
                    input_data = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    input_data = {"raw": tc.function.arguments}

                tool_calls.append(
                    ToolCallRequest(
                        id=tc.id,
                        name=tc.function.name,
                        input=input_data,
                    )
                )

        return LLMResponse(
            content=content,
            tool_calls=tool_calls if tool_calls else None,
            usage=(
                LLMUsage(
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                )
                if response.usage
                else None
            ),
            provider=self.name,
            model=response.model,
            stop_reason=choice.finish_reason,
            latency_ms=(time.time() - start_time) * 1000,
        )

    async def shutdown(self) -> None:
        """Shutdown the provider."""
        if self._client:
            await self._client.close()
            self._client = None
        await super().shutdown()
