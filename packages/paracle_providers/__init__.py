"""
LLM Provider abstraction layer.

This package provides a unified interface for interacting with different
LLM providers (OpenAI, Anthropic, Google, xAI, DeepSeek, Groq, Ollama, etc.).
"""

__version__ = "1.0.1"

# Auto-register available providers
from paracle_providers import auto_register  # noqa: F401
from paracle_providers.base import (
    ChatMessage,
    LLMConfig,
    LLMProvider,
    LLMResponse,
    StreamChunk,
)
from paracle_providers.capabilities import (
    ModelCapability,
    ModelCatalog,
    ModelInfo,
    ProviderInfo,
    get_model_catalog,
)
from paracle_providers.exceptions import (
    LLMProviderError,
    ProviderNotFoundError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from paracle_providers.openai_compatible import (
    OpenAICompatibleProvider,
    create_anyscale_provider,
    create_cloudflare_provider,
    create_jan_provider,
    create_llamacpp_provider,
    create_lmstudio_provider,
    create_localai_provider,
    create_perplexity_provider,
    create_text_generation_webui_provider,
    create_together_provider,
    create_vllm_provider,
)
from paracle_providers.registry import ProviderRegistry
from paracle_providers.retry import (
    RetryableProvider,
    RetryConfig,
    RetryResult,
    create_retry_decorator,
    retry_with_backoff,
)

__all__ = [
    # Base classes and models
    "ChatMessage",
    "LLMConfig",
    "LLMProvider",
    "LLMResponse",
    "StreamChunk",
    # Capabilities and catalog
    "ModelCapability",
    "ModelInfo",
    "ProviderInfo",
    "ModelCatalog",
    "get_model_catalog",
    # Exceptions
    "LLMProviderError",
    "ProviderNotFoundError",
    "ProviderRateLimitError",
    "ProviderTimeoutError",
    # Registry
    "ProviderRegistry",
    # Retry utilities
    "RetryConfig",
    "RetryResult",
    "RetryableProvider",
    "create_retry_decorator",
    "retry_with_backoff",
    # OpenAI-compatible providers
    "OpenAICompatibleProvider",
    "create_lmstudio_provider",
    "create_together_provider",
    "create_perplexity_provider",
    "create_vllm_provider",
    "create_text_generation_webui_provider",
    "create_llamacpp_provider",
    "create_localai_provider",
    "create_jan_provider",
    "create_anyscale_provider",
    "create_cloudflare_provider",
]
