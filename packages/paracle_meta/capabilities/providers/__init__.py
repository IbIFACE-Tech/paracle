"""LLM Provider implementations for paracle_meta capabilities.

This module provides concrete implementations of the CapabilityProvider protocol
for various LLM backends.

Available Providers:
    - AnthropicProvider: Claude models via Anthropic API
    - OpenAIProvider: GPT models via OpenAI API
    - OllamaProvider: Local models via Ollama
    - MockProvider: Mock provider for testing

Example:
    >>> from paracle_meta.capabilities.providers import (
    ...     AnthropicProvider,
    ...     OpenAIProvider,
    ...     MockProvider,
    ... )
    >>>
    >>> # Use Anthropic
    >>> provider = AnthropicProvider(api_key="sk-...")
    >>> await provider.initialize()
    >>>
    >>> # Use Mock for testing
    >>> mock = MockProvider()
    >>> await mock.initialize()
"""

from paracle_meta.capabilities.providers.anthropic import AnthropicProvider
from paracle_meta.capabilities.providers.mock import MockProvider
from paracle_meta.capabilities.providers.ollama import OllamaProvider
from paracle_meta.capabilities.providers.openai import OpenAIProvider

__all__ = [
    "AnthropicProvider",
    "OpenAIProvider",
    "OllamaProvider",
    "MockProvider",
]
