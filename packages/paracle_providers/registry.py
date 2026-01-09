"""Provider registry for managing LLM providers."""

from typing import Any

from paracle_providers.base import LLMProvider
from paracle_providers.exceptions import ProviderNotFoundError


class ProviderRegistry:
    """
    Registry for LLM providers.

    Allows registration and retrieval of provider classes,
    and instantiation of provider instances with configuration.
    """

    _providers: dict[str, type[LLMProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_class: type[LLMProvider]) -> None:
        """
        Register a provider class.

        Args:
            name: Provider identifier (e.g., "openai", "anthropic")
            provider_class: Provider class that implements LLMProvider

        Raises:
            TypeError: If provider_class doesn't implement LLMProvider
        """
        if not issubclass(provider_class, LLMProvider):
            raise TypeError(
                f"Provider class must inherit from LLMProvider, got {provider_class}"
            )

        cls._providers[name] = provider_class

    @classmethod
    def get_provider_class(cls, name: str) -> type[LLMProvider]:
        """
        Get a provider class by name.

        Args:
            name: Provider identifier

        Returns:
            Provider class

        Raises:
            ProviderNotFoundError: If provider is not registered
        """
        provider_class = cls._providers.get(name)
        if provider_class is None:
            raise ProviderNotFoundError(name)
        return provider_class

    @classmethod
    def create_provider(cls, name: str, **kwargs: Any) -> LLMProvider:
        """
        Create a provider instance.

        Args:
            name: Provider identifier
            **kwargs: Provider-specific configuration

        Returns:
            Instantiated provider

        Raises:
            ProviderNotFoundError: If provider is not registered

        Example:
            >>> registry = ProviderRegistry()
            >>> provider = registry.create_provider("openai", api_key="sk-...")
        """
        provider_class = cls.get_provider_class(name)
        return provider_class(**kwargs)

    @classmethod
    def list_providers(cls) -> list[str]:
        """
        List all registered provider names.

        Returns:
            List of provider identifiers
        """
        return list(cls._providers.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        Check if a provider is registered.

        Args:
            name: Provider identifier

        Returns:
            True if provider is registered, False otherwise
        """
        return name in cls._providers

    @classmethod
    def unregister(cls, name: str) -> None:
        """
        Unregister a provider.

        Args:
            name: Provider identifier

        Raises:
            ProviderNotFoundError: If provider is not registered
        """
        if name not in cls._providers:
            raise ProviderNotFoundError(name)
        del cls._providers[name]

    @classmethod
    def clear(cls) -> None:
        """Clear all registered providers (mainly for testing)."""
        cls._providers.clear()
