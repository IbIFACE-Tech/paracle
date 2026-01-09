"""Model capabilities tracking and management."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ModelCapability(str, Enum):
    """Standard capabilities that models may support."""

    # Text generation
    TEXT_GENERATION = "text-generation"
    CHAT_COMPLETION = "chat-completion"

    # Advanced features
    OBJECT_GENERATION = "object-generation"  # Structured output
    TOOL_CALLING = "tool-calling"  # Function/tool calling
    STREAMING = "streaming"  # Token streaming
    JSON_MODE = "json-mode"  # Native JSON output

    # Multimodal
    IMAGE_INPUT = "image-input"  # Vision/image understanding
    IMAGE_OUTPUT = "image-output"  # Image generation
    AUDIO_INPUT = "audio-input"  # Speech recognition
    AUDIO_OUTPUT = "audio-output"  # Text-to-speech
    VIDEO_INPUT = "video-input"  # Video understanding

    # Context and memory
    LONG_CONTEXT = "long-context"  # >32k tokens
    EXTENDED_CONTEXT = "extended-context"  # >128k tokens

    # Specialized
    CODE_GENERATION = "code-generation"
    EMBEDDINGS = "embeddings"
    RERANKING = "reranking"
    REASONING = "reasoning"  # Chain-of-thought, planning


class ModelInfo(BaseModel):
    """Information about a specific model."""

    model_id: str = Field(..., description="Model identifier")
    provider: str = Field(..., description="Provider name")
    display_name: str = Field(..., description="Human-readable name")
    capabilities: list[ModelCapability] = Field(
        default_factory=list, description="Supported capabilities"
    )
    context_window: int | None = Field(
        default=None, description="Maximum context length in tokens"
    )
    max_output_tokens: int | None = Field(
        default=None, description="Maximum output tokens"
    )
    input_cost_per_million: float | None = Field(
        default=None, description="Input cost per million tokens (USD)"
    )
    output_cost_per_million: float | None = Field(
        default=None, description="Output cost per million tokens (USD)"
    )
    release_date: str | None = Field(default=None, description="Model release date")
    deprecated: bool = Field(default=False, description="Whether model is deprecated")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional model metadata"
    )

    def has_capability(self, capability: ModelCapability) -> bool:
        """Check if model has a specific capability."""
        return capability in self.capabilities

    def supports_vision(self) -> bool:
        """Check if model supports image input."""
        return self.has_capability(ModelCapability.IMAGE_INPUT)

    def supports_tools(self) -> bool:
        """Check if model supports tool/function calling."""
        return self.has_capability(ModelCapability.TOOL_CALLING)

    def supports_streaming(self) -> bool:
        """Check if model supports streaming responses."""
        return self.has_capability(ModelCapability.STREAMING)


class ProviderInfo(BaseModel):
    """Information about an LLM provider."""

    provider_id: str = Field(..., description="Provider identifier")
    display_name: str = Field(..., description="Human-readable name")
    description: str | None = Field(default=None, description="Provider description")
    website: str | None = Field(default=None, description="Provider website")
    api_docs: str | None = Field(default=None, description="API documentation URL")
    requires_api_key: bool = Field(
        default=True, description="Whether API key is required"
    )
    supports_streaming: bool = Field(
        default=False, description="Whether provider supports streaming"
    )
    models: list[ModelInfo] = Field(
        default_factory=list, description="Available models"
    )

    def get_model(self, model_id: str) -> ModelInfo | None:
        """Get model info by ID."""
        for model in self.models:
            if model.model_id == model_id:
                return model
        return None

    def list_models(self, capability: ModelCapability | None = None) -> list[ModelInfo]:
        """List models, optionally filtered by capability."""
        if capability is None:
            return self.models
        return [m for m in self.models if m.has_capability(capability)]


class ModelCatalog:
    """
    Central catalog of providers and models.

    Provides discovery and querying of available models across all providers.
    """

    def __init__(self):
        self._providers: dict[str, ProviderInfo] = {}

    def register_provider(self, provider: ProviderInfo) -> None:
        """Register a provider and its models."""
        self._providers[provider.provider_id] = provider

    def get_provider(self, provider_id: str) -> ProviderInfo | None:
        """Get provider info by ID."""
        return self._providers.get(provider_id)

    def list_providers(self) -> list[ProviderInfo]:
        """List all registered providers."""
        return list(self._providers.values())

    def find_model(self, model_id: str) -> tuple[ProviderInfo, ModelInfo] | None:
        """Find a model across all providers."""
        for provider in self._providers.values():
            model = provider.get_model(model_id)
            if model:
                return (provider, model)
        return None

    def search_models(
        self,
        capability: ModelCapability | None = None,
        provider: str | None = None,
        max_cost: float | None = None,
    ) -> list[tuple[ProviderInfo, ModelInfo]]:
        """
        Search for models matching criteria.

        Args:
            capability: Required capability
            provider: Filter by provider ID
            max_cost: Maximum input cost per million tokens

        Returns:
            List of (provider, model) tuples
        """
        results = []

        for prov in self._providers.values():
            if provider and prov.provider_id != provider:
                continue

            models = prov.list_models(capability)

            for model in models:
                if max_cost is not None:
                    if (
                        model.input_cost_per_million is None
                        or model.input_cost_per_million > max_cost
                    ):
                        continue

                results.append((prov, model))

        return results


# Global catalog instance
_global_catalog = ModelCatalog()


def get_model_catalog() -> ModelCatalog:
    """Get the global model catalog instance."""
    return _global_catalog
