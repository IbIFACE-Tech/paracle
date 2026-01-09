"""AI provider abstraction for optional AI-powered features.

This module provides a clean abstraction for AI providers, allowing Paracle
to work with paracle_meta (internal AI) or external providers (OpenAI, Anthropic, etc.)
while maintaining full functionality when AI is not available.

Architecture:
    - Core CLI/API functions work WITHOUT AI
    - AI-powered generation features are optional enhancements
    - Users choose their preferred AI provider
    - Graceful degradation when AI unavailable
"""

import logging
from typing import Any, Protocol

import yaml
from paracle_core.parac.state import find_parac_root

logger = logging.getLogger(__name__)


class AIProvider(Protocol):
    """Protocol for AI providers.

    All AI providers (paracle_meta, OpenAI, Anthropic, etc.) must implement
    this interface to be used by Paracle.
    """

    @property
    def name(self) -> str:
        """Provider name (e.g., 'meta', 'openai', 'anthropic')."""
        ...

    async def generate_agent(self, description: str, **kwargs: Any) -> dict[str, Any]:
        """Generate agent specification from natural language description.

        Args:
            description: Natural language description of agent.
            **kwargs: Provider-specific options.

        Returns:
            dict with keys:
                - name: Agent name
                - yaml: Agent YAML specification
                - description: Generated description
        """
        ...

    async def generate_skill(self, description: str, **kwargs: Any) -> dict[str, Any]:
        """Generate skill from natural language description.

        Args:
            description: Natural language description of skill.
            **kwargs: Provider-specific options.

        Returns:
            dict with keys:
                - name: Skill name
                - yaml: Skill YAML specification
                - code: Optional Python implementation
        """
        ...

    async def generate_workflow(
        self, description: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Generate workflow from natural language description.

        Args:
            description: Natural language description of workflow.
            **kwargs: Provider-specific options.

        Returns:
            dict with keys:
                - name: Workflow name
                - yaml: Workflow YAML specification
        """
        ...

    async def enhance_documentation(self, code: str, **kwargs: Any) -> str:
        """Generate documentation for code.

        Args:
            code: Source code to document.
            **kwargs: Provider-specific options.

        Returns:
            Generated documentation (markdown).
        """
        ...


class AIProviderError(Exception):
    """AI provider error."""

    pass


class AIProviderNotAvailable(AIProviderError):
    """AI provider is not available or not configured."""

    pass


def get_ai_provider(provider_name: str | None = None) -> AIProvider | None:
    """Get AI provider instance.

    Priority:
        1. Specified provider name (if given)
        2. paracle_meta (if installed and activated)
        3. User-configured provider from .parac/config/ai.yaml
        4. None (AI features disabled)

    Args:
        provider_name: Optional specific provider to use.

    Returns:
        AIProvider instance or None if no AI available.

    Example:
        ```python
        ai = get_ai_provider()
        if ai:
            result = await ai.generate_agent("Code reviewer")
        else:
            print("AI not available")
        ```
    """
    # If specific provider requested
    if provider_name:
        return _get_specific_provider(provider_name)

    # Try paracle_meta first (internal AI)
    try:
        from paracle_meta import MetaEngine

        if MetaEngine.is_activated():
            logger.info("Using paracle_meta as AI provider")
            return MetaEngine()
    except ImportError:
        logger.debug("paracle_meta not installed")
    except Exception as e:
        logger.warning(f"paracle_meta not available: {e}")

    # Try user-configured provider
    try:
        config = _load_ai_config()
        if config and config.get("ai", {}).get("provider"):
            provider = config["ai"]["provider"]
            if provider != "none":
                logger.info(f"Using configured provider: {provider}")
                return _get_specific_provider(provider)
    except Exception as e:
        logger.debug(f"Could not load AI config: {e}")

    # No AI available
    logger.debug("No AI provider available")
    return None


def _get_specific_provider(name: str) -> AIProvider | None:
    """Get specific AI provider by name.

    Args:
        name: Provider name (meta, openai, anthropic, azure, etc.).

    Returns:
        AIProvider instance or None.

    Raises:
        AIProviderNotAvailable: If provider not installed/configured.
    """
    if name == "meta":
        try:
            from paracle_meta import MetaEngine

            if not MetaEngine.is_activated():
                raise AIProviderNotAvailable(
                    "paracle_meta is installed but not activated.\n"
                    "Activate with: paracle meta activate"
                )
            return MetaEngine()
        except ImportError:
            raise AIProviderNotAvailable(
                "paracle_meta not installed.\n"
                "Install with: pip install paracle[meta]"
            )

    elif name == "openai":
        try:
            from paracle_providers.openai_provider import (
                OpenAIProvider as BaseOpenAIProvider,
            )

            from paracle_cli.generation_adapter import GenerationAdapter

            base_provider = BaseOpenAIProvider()
            return GenerationAdapter(base_provider, "openai")
        except ImportError as e:
            raise AIProviderNotAvailable(
                f"OpenAI provider not installed: {e}\n"
                "Install with: pip install paracle[openai]"
            )

    elif name == "anthropic":
        try:
            from paracle_providers.anthropic_provider import (
                AnthropicProvider as BaseAnthropicProvider,
            )

            from paracle_cli.generation_adapter import GenerationAdapter

            base_provider = BaseAnthropicProvider()
            return GenerationAdapter(base_provider, "anthropic")
        except ImportError as e:
            raise AIProviderNotAvailable(
                f"Anthropic provider not installed: {e}\n"
                "Install with: pip install paracle[anthropic]"
            )

    elif name == "azure":
        try:
            # Azure uses OpenAI SDK
            from paracle_providers.openai_provider import (
                OpenAIProvider as BaseOpenAIProvider,
            )

            from paracle_cli.generation_adapter import GenerationAdapter

            # Azure OpenAI is configured via environment variables
            # AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY
            base_provider = BaseOpenAIProvider()
            return GenerationAdapter(base_provider, "azure")
        except ImportError as e:
            raise AIProviderNotAvailable(
                f"Azure provider not installed: {e}\n"
                "Install with: pip install paracle[azure]"
            )

    else:
        raise AIProviderNotAvailable(f"Unknown provider: {name}")


def _load_ai_config() -> dict | None:
    """Load AI configuration from .parac/config/ai.yaml.

    Returns:
        Config dict or None if not found.
    """
    try:
        parac_root = find_parac_root()
        config_path = parac_root / "config" / "ai.yaml"

        if not config_path.exists():
            return None

        with open(config_path) as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.debug(f"Could not load AI config: {e}")
        return None


def require_ai(func):
    """Decorator to require AI provider for a function.

    Usage:
        ```python
        @require_ai
        async def generate_something(description: str, ai: AIProvider):
            return await ai.generate_agent(description)
        ```
    """

    def wrapper(*args, **kwargs):
        ai = get_ai_provider()
        if ai is None:
            raise AIProviderNotAvailable(
                f"{func.__name__} requires AI support.\n\n"
                "Options:\n"
                "  1. Install paracle_meta: pip install paracle[meta]\n"
                "  2. Configure: paracle config set ai.provider openai\n"
                "  3. Set API key: export OPENAI_API_KEY=sk-..."
            )
        return func(*args, ai=ai, **kwargs)

    return wrapper


def is_ai_available() -> bool:
    """Check if any AI provider is available.

    Returns:
        True if AI provider available, False otherwise.
    """
    return get_ai_provider() is not None


def list_available_providers() -> list[str]:
    """List all available AI providers.

    Returns:
        List of provider names that can be used.
    """
    available = []

    # Check paracle_meta
    try:
        from paracle_meta import MetaEngine

        if MetaEngine.is_activated():
            available.append("meta")
    except ImportError:
        pass

    # Check OpenAI
    try:
        from paracle_cli.providers.openai_provider import OpenAIProvider

        if OpenAIProvider:  # Use the import
            available.append("openai")
    except ImportError:
        pass

    # Check Anthropic
    try:
        from paracle_cli.providers.anthropic_provider import AnthropicProvider

        if AnthropicProvider:  # Use the import
            available.append("anthropic")
    except ImportError:
        pass

    # Check Azure
    try:
        from paracle_cli.providers.azure_provider import AzureProvider

        if AzureProvider:  # Use the import
            available.append("azure")
    except ImportError:
        pass

    return available


def get_setup_instructions(provider: str) -> str:
    """Get setup instructions for a provider.

    Args:
        provider: Provider name.

    Returns:
        Setup instructions as string.
    """
    instructions = {
        "meta": """
Setup paracle_meta:

1. Install package:
   pip install paracle[meta]

2. Activate meta engine:
   paracle meta activate

3. (Optional) Configure model:
   paracle meta config --model gpt-4
""",
        "openai": """
Setup OpenAI:

1. Install package:
   pip install paracle[openai]

2. Get API key from: https://platform.openai.com/api-keys

3. Set environment variable:
   export OPENAI_API_KEY=sk-...

4. Configure in Paracle:
   paracle config set ai.provider openai
   paracle config set ai.providers.openai.model gpt-4-turbo
""",
        "anthropic": """
Setup Anthropic:

1. Install package:
   pip install paracle[anthropic]

2. Get API key from: https://console.anthropic.com/

3. Set environment variable:
   export ANTHROPIC_API_KEY=sk-ant-...

4. Configure in Paracle:
   paracle config set ai.provider anthropic
   paracle config set ai.providers.anthropic.model claude-3-opus-20240229
""",
        "azure": """
Setup Azure OpenAI:

1. Install package:
   pip install paracle[azure]

2. Set up Azure OpenAI service

3. Set environment variables:
   export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   export AZURE_OPENAI_KEY=...

4. Configure in Paracle:
   paracle config set ai.provider azure
""",
    }

    return instructions.get(provider, f"Unknown provider: {provider}")
