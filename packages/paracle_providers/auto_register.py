"""Auto-registration of providers with graceful import handling."""

from paracle_providers.registry import ProviderRegistry


def register_all_providers() -> None:
    """
    Register all available providers.

    Providers are registered only if their dependencies are installed.
    This allows graceful degradation if optional packages are missing.
    """
    # Try to register OpenAI provider
    try:
        from paracle_providers.openai_provider import OpenAIProvider

        ProviderRegistry.register("openai", OpenAIProvider)
    except ImportError:
        pass  # openai package not installed

    # Try to register Anthropic provider
    try:
        from paracle_providers.anthropic_provider import AnthropicProvider

        ProviderRegistry.register("anthropic", AnthropicProvider)
    except ImportError:
        pass  # anthropic package not installed

    # Try to register Google provider
    try:
        from paracle_providers.google_provider import GoogleProvider

        ProviderRegistry.register("google", GoogleProvider)
    except ImportError:
        pass  # google-generativeai package not installed

    # Try to register Ollama provider
    try:
        from paracle_providers.ollama_provider import OllamaProvider

        ProviderRegistry.register("ollama", OllamaProvider)
    except ImportError:
        pass  # httpx package not installed


# Auto-register on module import
register_all_providers()
