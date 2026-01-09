"""Base protocol and models for LLM providers."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from paracle_core.compat import UTC, datetime
from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(UTC)


class ChatMessage(BaseModel):
    """Standardized chat message across all providers."""

    model_config = ConfigDict(frozen=True)

    role: str = Field(..., description="Message role: system, user, assistant, tool")
    content: str = Field(..., description="Message content")
    name: str | None = Field(default=None, description="Optional name for the message")
    tool_call_id: str | None = Field(
        default=None, description="ID of the tool call (for tool role)"
    )
    tool_calls: list[dict[str, Any]] | None = Field(
        default=None, description="Tool calls made by the assistant"
    )


class LLMConfig(BaseModel):
    """Configuration for LLM requests."""

    model_config = ConfigDict(frozen=False)

    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_tokens: int | None = Field(
        default=None, ge=1, description="Maximum tokens to generate"
    )
    top_p: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Nucleus sampling parameter"
    )
    frequency_penalty: float | None = Field(
        default=None, ge=-2.0, le=2.0, description="Frequency penalty"
    )
    presence_penalty: float | None = Field(
        default=None, ge=-2.0, le=2.0, description="Presence penalty"
    )
    stop_sequences: list[str] | None = Field(
        default=None, description="Sequences where the API will stop generating"
    )
    timeout: float = Field(default=30.0, gt=0, description="Request timeout in seconds")


class TokenUsage(BaseModel):
    """Token usage information."""

    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)


class LLMResponse(BaseModel):
    """Standardized response from LLM providers."""

    model_config = ConfigDict(frozen=True)

    content: str = Field(..., description="Generated text content")
    finish_reason: str | None = Field(
        default=None, description="Reason for completion: stop, length, content_filter"
    )
    usage: TokenUsage = Field(
        default_factory=TokenUsage, description="Token usage information"
    )
    model: str | None = Field(default=None, description="Model used for generation")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Provider-specific metadata"
    )
    tool_calls: list[dict[str, Any]] | None = Field(
        default=None, description="Tool calls made by the model"
    )
    created_at: datetime = Field(
        default_factory=_utcnow, description="Response timestamp"
    )


class StreamChunk(BaseModel):
    """Chunk from streaming response."""

    model_config = ConfigDict(frozen=True)

    content: str = Field(default="", description="Incremental content")
    finish_reason: str | None = Field(
        default=None, description="Finish reason if last chunk"
    )
    tool_calls: list[dict[str, Any]] | None = Field(
        default=None, description="Tool calls in this chunk"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All provider implementations must implement this interface to ensure
    consistent behavior across different LLM backends.
    """

    def __init__(self, api_key: str | None = None, **kwargs):
        """
        Initialize the provider.

        Args:
            api_key: API key for authentication (if required)
            **kwargs: Provider-specific configuration
        """
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod
    async def chat_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs,
    ) -> LLMResponse:
        """
        Generate a chat completion.

        Args:
            messages: List of chat messages
            config: LLM configuration parameters
            model: Model identifier (provider-specific)
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse with generated content and metadata

        Raises:
            LLMProviderError: On provider-specific errors
            ProviderTimeoutError: On timeout
            ProviderRateLimitError: On rate limit exceeded
        """
        pass

    @abstractmethod
    async def stream_chat_completion(
        self,
        messages: list[ChatMessage],
        config: LLMConfig,
        model: str,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream a chat completion.

        Args:
            messages: List of chat messages
            config: LLM configuration parameters
            model: Model identifier (provider-specific)
            **kwargs: Additional provider-specific parameters

        Yields:
            StreamChunk objects with incremental content

        Raises:
            LLMProviderError: On provider-specific errors
            ProviderTimeoutError: On timeout
            ProviderRateLimitError: On rate limit exceeded
        """
        pass

    @abstractmethod
    def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate provider-specific configuration.

        Args:
            config: Configuration dictionary to validate

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name identifier."""
        pass

    @property
    @abstractmethod
    def supported_models(self) -> list[str]:
        """Return list of supported model identifiers."""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(provider={self.provider_name})"
