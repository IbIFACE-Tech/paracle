"""Provider protocol for capability LLM operations.

This module defines the abstract interface for LLM providers used by capabilities.
It enables provider abstraction, allowing capabilities to work with any LLM backend
(Anthropic, OpenAI, Ollama, etc.) through a unified interface.

Example:
    >>> from paracle_meta.capabilities.provider_protocol import (
    ...     CapabilityProvider, LLMRequest, LLMResponse
    ... )
    >>>
    >>> request = LLMRequest(
    ...     prompt="Write a Python function",
    ...     temperature=0.7
    ... )
    >>> response = await provider.complete(request)
    >>> print(response.content)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class ProviderStatus(Enum):
    """Provider availability status."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    INITIALIZING = "initializing"


@dataclass
class ToolDefinitionSchema:
    """Tool definition for LLM tool use.

    Attributes:
        name: Tool name (identifier).
        description: Human-readable description.
        input_schema: JSON Schema for tool parameters.
    """

    name: str
    description: str
    input_schema: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


@dataclass
class ToolCallRequest:
    """A tool call request from the LLM.

    Attributes:
        id: Unique identifier for this tool call.
        name: Name of the tool to call.
        input: Tool input parameters.
    """

    id: str
    name: str
    input: dict[str, Any]


@dataclass
class ToolCallResult:
    """Result of a tool call execution.

    Attributes:
        tool_use_id: ID of the tool call this result corresponds to.
        content: Result content (string or structured).
        is_error: Whether this result represents an error.
    """

    tool_use_id: str
    content: str | dict[str, Any]
    is_error: bool = False


@dataclass
class LLMMessage:
    """A message in a conversation.

    Attributes:
        role: Message role (user, assistant, system).
        content: Message content.
        tool_calls: Tool calls made by assistant (if any).
        tool_results: Tool results provided by user (if any).
    """

    role: str  # user, assistant, system
    content: str | list[dict[str, Any]]
    tool_calls: list[ToolCallRequest] | None = None
    tool_results: list[ToolCallResult] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format for API calls."""
        result: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.tool_calls:
            result["tool_calls"] = [
                {"id": tc.id, "name": tc.name, "input": tc.input}
                for tc in self.tool_calls
            ]
        return result


@dataclass
class LLMRequest:
    """Request for LLM completion.

    Attributes:
        prompt: The user prompt (for single-turn).
        messages: Full conversation history (for multi-turn).
        system_prompt: System instructions.
        temperature: Sampling temperature (0.0-2.0).
        max_tokens: Maximum tokens in response.
        tools: Tool definitions for tool use.
        tool_choice: Tool choice strategy ("auto", "any", "none", or specific tool).
        stop_sequences: Sequences that stop generation.
        top_p: Nucleus sampling parameter.
        top_k: Top-k sampling parameter.
        metadata: Additional provider-specific parameters.
    """

    prompt: str | None = None
    messages: list[LLMMessage] | None = None
    system_prompt: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096
    tools: list[ToolDefinitionSchema] | None = None
    tool_choice: str | dict[str, Any] | None = None
    stop_sequences: list[str] | None = None
    top_p: float | None = None
    top_k: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate request."""
        if not self.prompt and not self.messages:
            raise ValueError("Either prompt or messages must be provided")

    def get_messages(self) -> list[LLMMessage]:
        """Get messages list, converting prompt if needed."""
        if self.messages:
            return self.messages
        return [LLMMessage(role="user", content=self.prompt or "")]


@dataclass
class LLMUsage:
    """Token usage information.

    Attributes:
        input_tokens: Tokens in the input.
        output_tokens: Tokens in the output.
        total_tokens: Total tokens used.
        cache_read_tokens: Tokens read from cache (if applicable).
        cache_write_tokens: Tokens written to cache (if applicable).
    """

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    def __post_init__(self) -> None:
        """Calculate total if not provided."""
        if self.total_tokens == 0:
            self.total_tokens = self.input_tokens + self.output_tokens


@dataclass
class LLMResponse:
    """Response from LLM completion.

    Attributes:
        content: The response content.
        tool_calls: Tool calls requested by the model.
        usage: Token usage information.
        provider: Name of the provider that generated this response.
        model: Model identifier used.
        stop_reason: Why generation stopped.
        raw_response: Original provider response (for debugging).
        latency_ms: Response latency in milliseconds.
        timestamp: When the response was generated.
    """

    content: str
    tool_calls: list[ToolCallRequest] | None = None
    usage: LLMUsage | None = None
    provider: str = ""
    model: str = ""
    stop_reason: str | None = None
    raw_response: dict[str, Any] | None = None
    latency_ms: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def has_tool_calls(self) -> bool:
        """Check if response contains tool calls."""
        return bool(self.tool_calls)


@dataclass
class StreamChunk:
    """A chunk from streaming response.

    Attributes:
        content: Text content of this chunk.
        is_final: Whether this is the final chunk.
        tool_call: Partial tool call information.
        usage: Usage info (typically in final chunk).
    """

    content: str = ""
    is_final: bool = False
    tool_call: ToolCallRequest | None = None
    usage: LLMUsage | None = None


@runtime_checkable
class CapabilityProvider(Protocol):
    """Protocol for LLM providers used by capabilities.

    This protocol defines the interface that all LLM providers must implement.
    It enables capabilities to work with any backend (Anthropic, OpenAI, etc.)
    through a unified interface.

    Example:
        >>> class MyProvider:
        ...     @property
        ...     def name(self) -> str:
        ...         return "my_provider"
        ...
        ...     @property
        ...     def is_available(self) -> bool:
        ...         return True
        ...
        ...     async def complete(self, request: LLMRequest) -> LLMResponse:
        ...         # Implementation
        ...         pass
    """

    @property
    def name(self) -> str:
        """Provider name identifier."""
        ...

    @property
    def is_available(self) -> bool:
        """Whether the provider is currently available."""
        ...

    @property
    def status(self) -> ProviderStatus:
        """Current provider status."""
        ...

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Generate a completion for the request.

        Args:
            request: The LLM request.

        Returns:
            The LLM response.

        Raises:
            ProviderError: If completion fails.
        """
        ...

    async def stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        """Stream a completion for the request.

        Args:
            request: The LLM request.

        Yields:
            Stream chunks with partial content.

        Raises:
            ProviderError: If streaming fails.
        """
        ...


class BaseProvider(ABC):
    """Abstract base class for LLM providers.

    Provides common functionality and enforces the CapabilityProvider protocol.
    """

    def __init__(self, model: str | None = None):
        """Initialize the provider.

        Args:
            model: Default model to use.
        """
        self._model = model
        self._status = ProviderStatus.INITIALIZING
        self._last_error: str | None = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier."""
        ...

    @property
    def is_available(self) -> bool:
        """Whether the provider is currently available."""
        return self._status == ProviderStatus.AVAILABLE

    @property
    def status(self) -> ProviderStatus:
        """Current provider status."""
        return self._status

    @property
    def last_error(self) -> str | None:
        """Last error message if any."""
        return self._last_error

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider (check API key, connectivity, etc.)."""
        ...

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Generate a completion."""
        ...

    @abstractmethod
    async def stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        """Stream a completion."""
        ...

    async def shutdown(self) -> None:
        """Shutdown the provider and release resources."""
        self._status = ProviderStatus.UNAVAILABLE

    def _set_available(self) -> None:
        """Mark provider as available."""
        self._status = ProviderStatus.AVAILABLE
        self._last_error = None

    def _set_error(self, error: str) -> None:
        """Mark provider as errored."""
        self._status = ProviderStatus.ERROR
        self._last_error = error

    def _set_rate_limited(self) -> None:
        """Mark provider as rate limited."""
        self._status = ProviderStatus.RATE_LIMITED


class ProviderError(Exception):
    """Base exception for provider errors."""

    def __init__(
        self,
        message: str,
        provider: str = "",
        recoverable: bool = True,
        retry_after: float | None = None,
    ):
        """Initialize provider error.

        Args:
            message: Error message.
            provider: Provider name.
            recoverable: Whether the error is recoverable (retry possible).
            retry_after: Seconds to wait before retry (if rate limited).
        """
        super().__init__(message)
        self.provider = provider
        self.recoverable = recoverable
        self.retry_after = retry_after


class ProviderUnavailableError(ProviderError):
    """Provider is not available."""

    def __init__(self, provider: str, reason: str = ""):
        super().__init__(
            f"Provider '{provider}' is unavailable: {reason}",
            provider=provider,
            recoverable=True,
        )


class ProviderRateLimitError(ProviderError):
    """Provider rate limit exceeded."""

    def __init__(self, provider: str, retry_after: float | None = None):
        super().__init__(
            f"Provider '{provider}' rate limit exceeded",
            provider=provider,
            recoverable=True,
            retry_after=retry_after,
        )


class ProviderAuthenticationError(ProviderError):
    """Provider authentication failed."""

    def __init__(self, provider: str):
        super().__init__(
            f"Provider '{provider}' authentication failed - check API key",
            provider=provider,
            recoverable=False,
        )


class ProviderAPIError(ProviderError):
    """Provider API error."""

    def __init__(self, provider: str, message: str, status_code: int | None = None):
        super().__init__(
            f"Provider '{provider}' API error: {message}",
            provider=provider,
            recoverable=True,
        )
        self.status_code = status_code
