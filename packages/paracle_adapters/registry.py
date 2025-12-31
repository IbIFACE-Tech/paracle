"""Adapter registry for managing framework adapters."""

from typing import Any

from paracle_adapters.base import FrameworkAdapter
from paracle_adapters.exceptions import AdapterNotFoundError


class AdapterRegistry:
    """
    Registry for framework adapters.

    Allows registration and retrieval of adapter classes,
    and instantiation of adapter instances with configuration.
    """

    _adapters: dict[str, type[FrameworkAdapter]] = {}

    @classmethod
    def register(cls, name: str, adapter_class: type[FrameworkAdapter]) -> None:
        """
        Register an adapter class.

        Args:
            name: Adapter identifier (e.g., "msaf", "langchain")
            adapter_class: Adapter class that implements FrameworkAdapter

        Raises:
            TypeError: If adapter_class doesn't implement FrameworkAdapter
        """
        if not issubclass(adapter_class, FrameworkAdapter):
            raise TypeError(
                f"Adapter class must inherit from FrameworkAdapter, got {adapter_class}"
            )

        cls._adapters[name] = adapter_class

    @classmethod
    def get_adapter_class(cls, name: str) -> type[FrameworkAdapter]:
        """
        Get an adapter class by name.

        Args:
            name: Adapter identifier

        Returns:
            Adapter class

        Raises:
            AdapterNotFoundError: If adapter is not registered
        """
        adapter_class = cls._adapters.get(name)
        if adapter_class is None:
            raise AdapterNotFoundError(name)
        return adapter_class

    @classmethod
    def create_adapter(cls, name: str, **kwargs: Any) -> FrameworkAdapter:
        """
        Create an adapter instance.

        Args:
            name: Adapter identifier
            **kwargs: Adapter-specific configuration

        Returns:
            Instantiated adapter

        Raises:
            AdapterNotFoundError: If adapter is not registered

        Example:
            >>> registry = AdapterRegistry()
            >>> adapter = registry.create_adapter("langchain", api_key="...")
        """
        adapter_class = cls.get_adapter_class(name)
        return adapter_class(**kwargs)

    @classmethod
    def list_adapters(cls) -> list[str]:
        """
        List all registered adapter names.

        Returns:
            List of adapter identifiers
        """
        return list(cls._adapters.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        Check if an adapter is registered.

        Args:
            name: Adapter identifier

        Returns:
            True if adapter is registered, False otherwise
        """
        return name in cls._adapters

    @classmethod
    def unregister(cls, name: str) -> None:
        """
        Unregister an adapter.

        Args:
            name: Adapter identifier

        Raises:
            AdapterNotFoundError: If adapter is not registered
        """
        if name not in cls._adapters:
            raise AdapterNotFoundError(name)
        del cls._adapters[name]

    @classmethod
    def clear(cls) -> None:
        """Clear all registered adapters (mainly for testing)."""
        cls._adapters.clear()
