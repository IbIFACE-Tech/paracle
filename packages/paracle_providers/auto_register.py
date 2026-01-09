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
        pass  # google-genai package not installed

    # Try to register Ollama provider
    try:
        from paracle_providers.ollama_provider import OllamaProvider

        ProviderRegistry.register("ollama", OllamaProvider)
    except ImportError:
        pass  # httpx package not installed

    # Try to register xAI provider
    try:
        from paracle_providers.xai_provider import XAIProvider

        ProviderRegistry.register("xai", XAIProvider)
    except ImportError:
        pass  # httpx package not installed

    # Try to register DeepSeek provider
    try:
        from paracle_providers.deepseek_provider import DeepSeekProvider

        ProviderRegistry.register("deepseek", DeepSeekProvider)
    except ImportError:
        pass  # httpx package not installed

    # Try to register Groq provider
    try:
        from paracle_providers.groq_provider import GroqProvider

        ProviderRegistry.register("groq", GroqProvider)
    except ImportError:
        pass  # httpx package not installed

    # Try to register OpenAI-compatible provider
    try:
        from paracle_providers.openai_compatible import OpenAICompatibleProvider

        ProviderRegistry.register("openai-compatible", OpenAICompatibleProvider)
    except ImportError:
        pass  # httpx package not installed

    # Try to register Mistral provider
    try:
        from paracle_providers.mistral_provider import MistralProvider

        ProviderRegistry.register("mistral", MistralProvider)
    except ImportError:
        pass

    # Try to register Cohere provider
    try:
        from paracle_providers.cohere_provider import CohereProvider

        ProviderRegistry.register("cohere", CohereProvider)
    except ImportError:
        pass

    # Try to register Together provider
    try:
        from paracle_providers.together_provider import TogetherProvider

        ProviderRegistry.register("together", TogetherProvider)
    except ImportError:
        pass

    # Try to register Perplexity provider
    try:
        from paracle_providers.perplexity_provider import PerplexityProvider

        ProviderRegistry.register("perplexity", PerplexityProvider)
    except ImportError:
        pass

    # Try to register OpenRouter provider
    try:
        from paracle_providers.openrouter_provider import OpenRouterProvider

        ProviderRegistry.register("openrouter", OpenRouterProvider)
    except ImportError:
        pass

    # Try to register Fireworks provider
    try:
        from paracle_providers.fireworks_provider import FireworksProvider

        ProviderRegistry.register("fireworks", FireworksProvider)
    except ImportError:
        pass


# Auto-register on module import
register_all_providers()
