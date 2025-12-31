"""
LLM Provider abstraction layer.

This package provides a unified interface for interacting with different
LLM providers (OpenAI, Anthropic, Google, Ollama, etc.).
"""

__version__ = "0.0.1"

from paracle_providers.base import (
    ChatMessage,
    LLMConfig,
    LLMProvider,
    LLMResponse,
    StreamChunk,
)
from paracle_providers.exceptions import (
    LLMProviderError,
    ProviderNotFoundError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from paracle_providers.registry import ProviderRegistry

# Auto-register available providers
from paracle_providers import auto_register  # noqa: F401

__all__ = [
    "ChatMessage",
    "LLMConfig",
    "LLMProvider",
    "LLMResponse",
    "StreamChunk",
    "LLMProviderError",
    "ProviderNotFoundError",
    "ProviderRateLimitError",
    "ProviderTimeoutError",
    "ProviderRegistry",
]
