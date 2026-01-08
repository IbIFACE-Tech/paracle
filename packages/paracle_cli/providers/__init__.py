"""AI provider adapters package."""

__all__ = ["OpenAIProvider", "AnthropicProvider", "AzureProvider"]

# Optional imports
try:
    from paracle_cli.providers.openai_provider import OpenAIProvider
except ImportError:
    pass

try:
    from paracle_cli.providers.anthropic_provider import AnthropicProvider
except ImportError:
    pass

try:
    from paracle_cli.providers.azure_provider import AzureProvider
except ImportError:
    pass
