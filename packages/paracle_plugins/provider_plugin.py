"""Provider plugin interface for custom LLM providers."""

from abc import abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel

from paracle_plugins.base import BasePlugin, PluginCapability


class Message(BaseModel):
    """Chat message."""

    role: str  # system, user, assistant
    content: str


class ChatCompletionRequest(BaseModel):
    """Request for chat completion."""

    messages: list[Message]
    model: str
    temperature: float = 0.7
    max_tokens: int | None = None
    stop: list[str] | None = None
    stream: bool = False


class ChatCompletionResponse(BaseModel):
    """Response from chat completion."""

    content: str
    model: str
    finish_reason: str
    usage: dict[str, int]  # {prompt_tokens, completion_tokens, total_tokens}


class ProviderPlugin(BasePlugin):
    """
    Base class for LLM provider plugins.

    Implement this to add custom LLM providers to Paracle.

    Required capabilities: At least one of
    - PluginCapability.TEXT_GENERATION
    - PluginCapability.CHAT_COMPLETION

    Example:
        >>> class CustomProviderPlugin(ProviderPlugin):
        ...     @property
        ...     def metadata(self) -> PluginMetadata:
        ...         return PluginMetadata(
        ...             name="custom-llm",
        ...             version="1.0.0",
        ...             description="My custom LLM provider",
        ...             author="Me",
        ...             plugin_type=PluginType.PROVIDER,
        ...             capabilities=[
        ...                 PluginCapability.CHAT_COMPLETION,
        ...                 PluginCapability.STREAMING
        ...             ],
        ...             dependencies=["custom-llm-sdk"]
        ...         )
        ...
        ...     async def initialize(self, config: Dict[str, Any]) -> None:
        ...         self.api_key = config["api_key"]
        ...         self.base_url = config.get("base_url")
        ...
        ...     async def chat_completion(
        ...         self, request: ChatCompletionRequest
        ...     ) -> ChatCompletionResponse:
        ...         # Call custom LLM API
        ...         response = await self._call_api(request)
        ...         return ChatCompletionResponse(
        ...             content=response["content"],
        ...             model=request.model,
        ...             finish_reason="stop",
        ...             usage=response["usage"]
        ...         )
    """

    @abstractmethod
    async def chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """
        Generate chat completion.

        Args:
            request: Chat completion request

        Returns:
            Chat completion response

        Raises:
            ValueError: If request is invalid
            ConnectionError: If unable to reach provider
            RateLimitError: If rate limit exceeded
        """
        pass

    async def chat_completion_stream(
        self, request: ChatCompletionRequest
    ) -> AsyncIterator[str]:
        """
        Generate streaming chat completion.

        Args:
            request: Chat completion request (stream=True)

        Yields:
            Content chunks as they arrive

        Raises:
            NotImplementedError: If streaming not supported
        """
        if PluginCapability.STREAMING not in self.metadata.capabilities:
            raise NotImplementedError(
                f"Streaming not supported by {self.metadata.name}"
            )

        # Default implementation: call non-streaming and yield once
        response = await self.chat_completion(request)
        yield response.content

    async def list_models(self) -> list[str]:
        """
        List available models for this provider.

        Returns:
            List of model names/IDs
        """
        return []

    async def get_model_info(self, model: str) -> dict[str, Any]:
        """
        Get information about a specific model.

        Args:
            model: Model name/ID

        Returns:
            Model information (context length, pricing, capabilities, etc.)
        """
        return {
            "model": model,
            "context_length": 4096,
            "supports_streaming": PluginCapability.STREAMING
            in self.metadata.capabilities,
            "supports_function_calling": PluginCapability.FUNCTION_CALLING
            in self.metadata.capabilities,
        }
