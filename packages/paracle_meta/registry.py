"""Capability registry for lazy loading and management.

This module provides a registry for managing capabilities with lazy initialization.
Capabilities are only created and initialized when first accessed, reducing startup
time and resource usage.

Example:
    >>> from paracle_meta.registry import CapabilityRegistry
    >>> from paracle_meta.capabilities import FileSystemConfig
    >>>
    >>> registry = CapabilityRegistry()
    >>> await registry.initialize()
    >>>
    >>> # Capabilities are created lazily on first access
    >>> fs = await registry.get("filesystem")
    >>> await fs.read_file("path/to/file.txt")
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from paracle_meta.capabilities.base import BaseCapability, CapabilityConfig
    from paracle_meta.capabilities.provider_protocol import CapabilityProvider


T = TypeVar("T")


class CapabilityStatus(Enum):
    """Capability status."""

    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class CapabilityInfo:
    """Information about a registered capability.

    Attributes:
        name: Capability name.
        factory: Factory function to create the capability.
        config: Configuration for the capability.
        instance: The capability instance (if loaded).
        status: Current status.
        error: Error message if status is ERROR.
        requires_provider: Whether capability requires an LLM provider.
    """

    name: str
    factory: Callable[..., BaseCapability]
    config: CapabilityConfig | None = None
    instance: BaseCapability | None = None
    status: CapabilityStatus = CapabilityStatus.NOT_LOADED
    error: str | None = None
    requires_provider: bool = False


@dataclass
class RegistryConfig:
    """Configuration for the capability registry.

    Attributes:
        auto_initialize: Whether to initialize capabilities on first access.
        parallel_init: Whether to initialize multiple capabilities in parallel.
        max_parallel: Maximum capabilities to initialize in parallel.
        provider: Default LLM provider for capabilities that need one.
    """

    auto_initialize: bool = True
    parallel_init: bool = True
    max_parallel: int = 5
    provider: CapabilityProvider | None = None


class CapabilityRegistry:
    """Registry for lazy-loading capabilities.

    Manages capability lifecycle with lazy initialization.
    Capabilities are only created when first accessed.

    Attributes:
        config: Registry configuration.
    """

    # Built-in capability factories
    _BUILTIN_FACTORIES: dict[str, tuple[str, str, bool]] = {
        # name: (module, class_name, requires_provider)
        "filesystem": (
            "paracle_meta.capabilities.filesystem",
            "FileSystemCapability",
            False,
        ),
        "memory": (
            "paracle_meta.capabilities.memory",
            "MemoryCapability",
            False,
        ),
        "shell": (
            "paracle_meta.capabilities.shell",
            "ShellCapability",
            False,
        ),
        "anthropic": (
            "paracle_meta.capabilities.anthropic_integration",
            "AnthropicCapability",
            False,  # Has its own client
        ),
        "code_creation": (
            "paracle_meta.capabilities.code_creation",
            "CodeCreationCapability",
            True,
        ),
        "web": (
            "paracle_meta.capabilities.web",
            "WebCapability",
            False,
        ),
        "code_execution": (
            "paracle_meta.capabilities.code_execution",
            "CodeExecutionCapability",
            False,
        ),
        "mcp": (
            "paracle_meta.capabilities.mcp",
            "MCPCapability",
            False,
        ),
        "task_management": (
            "paracle_meta.capabilities.task_management",
            "TaskManagementCapability",
            False,
        ),
        "agent_spawner": (
            "paracle_meta.capabilities.agent_spawner",
            "AgentSpawner",
            False,
        ),
    }

    def __init__(
        self,
        config: RegistryConfig | None = None,
        capabilities_config: dict[str, CapabilityConfig] | None = None,
    ):
        """Initialize the registry.

        Args:
            config: Registry configuration.
            capabilities_config: Configuration for individual capabilities.
        """
        self._config = config or RegistryConfig()
        self._capabilities_config = capabilities_config or {}
        self._capabilities: dict[str, CapabilityInfo] = {}
        self._lock = asyncio.Lock()
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Whether the registry is initialized."""
        return self._initialized

    @property
    def provider(self) -> CapabilityProvider | None:
        """Default LLM provider."""
        return self._config.provider

    @provider.setter
    def provider(self, value: CapabilityProvider | None) -> None:
        """Set the default LLM provider."""
        self._config.provider = value

    async def initialize(self) -> None:
        """Initialize the registry (but not capabilities)."""
        self._register_builtins()
        self._initialized = True

    def _register_builtins(self) -> None:
        """Register built-in capabilities."""
        for name, (
            module,
            class_name,
            requires_provider,
        ) in self._BUILTIN_FACTORIES.items():
            if name not in self._capabilities:
                self._capabilities[name] = CapabilityInfo(
                    name=name,
                    factory=lambda m=module, c=class_name: self._import_capability(
                        m, c
                    ),
                    config=self._capabilities_config.get(name),
                    requires_provider=requires_provider,
                )

    def _import_capability(self, module_path: str, class_name: str) -> BaseCapability:
        """Import and instantiate a capability class."""
        import importlib

        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        return cls

    def register(
        self,
        name: str,
        factory: Callable[..., BaseCapability],
        config: CapabilityConfig | None = None,
        requires_provider: bool = False,
    ) -> None:
        """Register a capability.

        Args:
            name: Capability name.
            factory: Factory function that returns a capability class or instance.
            config: Configuration for the capability.
            requires_provider: Whether capability requires an LLM provider.
        """
        self._capabilities[name] = CapabilityInfo(
            name=name,
            factory=factory,
            config=config,
            requires_provider=requires_provider,
        )

    def unregister(self, name: str) -> None:
        """Unregister a capability.

        Args:
            name: Capability name.
        """
        if name in self._capabilities:
            del self._capabilities[name]

    async def get(self, name: str) -> BaseCapability:
        """Get a capability, initializing if needed.

        Args:
            name: Capability name.

        Returns:
            The capability instance.

        Raises:
            KeyError: If capability not registered.
            RuntimeError: If capability fails to initialize.
        """
        if name not in self._capabilities:
            raise KeyError(f"Capability '{name}' not registered")

        info = self._capabilities[name]

        if info.status == CapabilityStatus.READY and info.instance:
            return info.instance

        if info.status == CapabilityStatus.ERROR:
            raise RuntimeError(f"Capability '{name}' failed: {info.error}")

        async with self._lock:
            # Double-check after acquiring lock
            if info.status == CapabilityStatus.READY and info.instance:
                return info.instance

            info.status = CapabilityStatus.LOADING

            try:
                # Create instance
                factory_result = info.factory()

                # Handle class vs instance
                if isinstance(factory_result, type):
                    # Factory returned a class, instantiate it
                    if info.config:
                        instance = factory_result(config=info.config)
                    elif info.requires_provider and self._config.provider:
                        instance = factory_result(provider=self._config.provider)
                    else:
                        instance = factory_result()
                else:
                    instance = factory_result

                # Initialize
                if self._config.auto_initialize:
                    await instance.initialize()

                info.instance = instance
                info.status = CapabilityStatus.READY
                return instance

            except Exception as e:
                info.status = CapabilityStatus.ERROR
                info.error = str(e)
                raise RuntimeError(f"Failed to initialize '{name}': {e}") from e

    async def get_optional(self, name: str) -> BaseCapability | None:
        """Get a capability if available, return None if not.

        Args:
            name: Capability name.

        Returns:
            The capability instance or None.
        """
        try:
            return await self.get(name)
        except (KeyError, RuntimeError):
            return None

    def is_registered(self, name: str) -> bool:
        """Check if capability is registered.

        Args:
            name: Capability name.

        Returns:
            True if registered.
        """
        return name in self._capabilities

    def is_loaded(self, name: str) -> bool:
        """Check if capability is loaded.

        Args:
            name: Capability name.

        Returns:
            True if loaded and ready.
        """
        if name not in self._capabilities:
            return False
        return self._capabilities[name].status == CapabilityStatus.READY

    def get_status(self, name: str) -> CapabilityStatus:
        """Get capability status.

        Args:
            name: Capability name.

        Returns:
            Capability status.
        """
        if name not in self._capabilities:
            return CapabilityStatus.NOT_LOADED
        return self._capabilities[name].status

    def list_capabilities(self) -> list[str]:
        """List all registered capabilities.

        Returns:
            List of capability names.
        """
        return list(self._capabilities.keys())

    def list_loaded(self) -> list[str]:
        """List loaded capabilities.

        Returns:
            List of loaded capability names.
        """
        return [
            name
            for name, info in self._capabilities.items()
            if info.status == CapabilityStatus.READY
        ]

    async def preload(self, names: list[str] | None = None) -> dict[str, bool]:
        """Preload capabilities.

        Args:
            names: Capabilities to preload (None for all).

        Returns:
            Dict of name -> success.
        """
        names = names or list(self._capabilities.keys())
        results: dict[str, bool] = {}

        if self._config.parallel_init:
            # Load in parallel
            async def load_one(name: str) -> tuple[str, bool]:
                try:
                    await self.get(name)
                    return (name, True)
                except Exception:
                    return (name, False)

            tasks = [load_one(name) for name in names]
            for batch_start in range(0, len(tasks), self._config.max_parallel):
                batch = tasks[batch_start : batch_start + self._config.max_parallel]
                batch_results = await asyncio.gather(*batch, return_exceptions=True)
                for result in batch_results:
                    if isinstance(result, tuple):
                        results[result[0]] = result[1]
        else:
            # Load sequentially
            for name in names:
                try:
                    await self.get(name)
                    results[name] = True
                except Exception:
                    results[name] = False

        return results

    async def shutdown(self) -> None:
        """Shutdown all loaded capabilities."""
        for info in self._capabilities.values():
            if info.instance and info.status == CapabilityStatus.READY:
                try:
                    await info.instance.shutdown()
                except Exception:
                    pass  # Best effort
                info.status = CapabilityStatus.SHUTDOWN
                info.instance = None

        self._initialized = False

    def __contains__(self, name: str) -> bool:
        """Check if capability is registered."""
        return name in self._capabilities

    def __iter__(self):
        """Iterate over registered capability names."""
        return iter(self._capabilities)


class CapabilityFacade:
    """Facade for accessing capabilities through the registry.

    Provides a convenient interface for capability access with
    attribute-style access.

    Example:
        >>> facade = CapabilityFacade(registry)
        >>> await facade.filesystem.read_file("path.txt")
        >>> await facade.memory.store("key", "value")
    """

    def __init__(self, registry: CapabilityRegistry):
        """Initialize facade.

        Args:
            registry: The capability registry.
        """
        self._registry = registry

    def __getattr__(self, name: str) -> AsyncCapabilityProxy:
        """Get capability by attribute access."""
        return AsyncCapabilityProxy(self._registry, name)


class AsyncCapabilityProxy:
    """Proxy for async capability access.

    Allows calling capability methods without explicit await for get().

    Example:
        >>> proxy = AsyncCapabilityProxy(registry, "filesystem")
        >>> result = await proxy.read_file("path.txt")  # Automatically gets capability
    """

    def __init__(self, registry: CapabilityRegistry, name: str):
        """Initialize proxy.

        Args:
            registry: The capability registry.
            name: Capability name.
        """
        self._registry = registry
        self._name = name

    def __getattr__(self, method: str) -> Callable[..., Any]:
        """Get capability method."""

        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            capability = await self._registry.get(self._name)
            attr = getattr(capability, method)
            if asyncio.iscoroutinefunction(attr):
                return await attr(*args, **kwargs)
            return attr(*args, **kwargs)

        return wrapper

    async def __aenter__(self) -> BaseCapability:
        """Enter async context."""
        return await self._registry.get(self._name)

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context."""
        pass  # Capability stays loaded
