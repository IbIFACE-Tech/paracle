"""Plugin registry for managing loaded plugins."""

import logging
from typing import Any

from paracle_plugins.base import BasePlugin, PluginType

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Registry for managing Paracle plugins.

    Provides:
    - Plugin registration and discovery
    - Plugin lifecycle management
    - Plugin lookup by name or type
    - Plugin health monitoring

    Example:
        >>> registry = get_plugin_registry()
        >>> await registry.register(my_plugin)
        >>> plugin = registry.get_plugin("my-plugin")
        >>> providers = registry.get_plugins_by_type(PluginType.PROVIDER)
    """

    def __init__(self):
        self._plugins: dict[str, BasePlugin] = {}
        self._plugins_by_type: dict[PluginType, list[BasePlugin]] = {
            plugin_type: [] for plugin_type in PluginType
        }

    async def register(
        self, plugin: BasePlugin, config: dict[str, Any] | None = None
    ) -> None:
        """
        Register and initialize a plugin.

        Args:
            plugin: Plugin instance to register
            config: Plugin configuration

        Raises:
            ValueError: If plugin with same name already registered
            Exception: If plugin initialization fails
        """
        plugin_name = plugin.metadata.name

        if plugin_name in self._plugins:
            raise ValueError(f"Plugin '{plugin_name}' is already registered")

        # Initialize plugin
        try:
            await plugin.initialize(config or {})
        except Exception as e:
            logger.error(f"Failed to initialize plugin '{plugin_name}': {e}")
            raise

        # Register plugin
        self._plugins[plugin_name] = plugin
        self._plugins_by_type[plugin.metadata.plugin_type].append(plugin)

        logger.info(
            f"Registered plugin '{plugin_name}' "
            f"(type={plugin.metadata.plugin_type}, "
            f"version={plugin.metadata.version})"
        )

    async def unregister(self, plugin_name: str) -> None:
        """
        Unregister and cleanup a plugin.

        Args:
            plugin_name: Name of plugin to unregister

        Raises:
            KeyError: If plugin not found
        """
        if plugin_name not in self._plugins:
            raise KeyError(f"Plugin '{plugin_name}' not found")

        plugin = self._plugins[plugin_name]

        # Cleanup plugin
        try:
            await plugin.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up plugin '{plugin_name}': {e}")

        # Unregister plugin
        del self._plugins[plugin_name]
        self._plugins_by_type[plugin.metadata.plugin_type].remove(plugin)

        logger.info(f"Unregistered plugin '{plugin_name}'")

    def get_plugin(self, plugin_name: str) -> BasePlugin | None:
        """
        Get plugin by name.

        Args:
            plugin_name: Plugin name

        Returns:
            Plugin instance or None if not found
        """
        return self._plugins.get(plugin_name)

    def get_plugins_by_type(self, plugin_type: PluginType) -> list[BasePlugin]:
        """
        Get all plugins of a specific type.

        Args:
            plugin_type: Type of plugins to get

        Returns:
            List of plugins of the specified type
        """
        return self._plugins_by_type.get(plugin_type, [])

    def list_plugins(self) -> list[dict[str, Any]]:
        """
        List all registered plugins with metadata.

        Returns:
            List of plugin metadata dictionaries
        """
        return [
            {
                "name": plugin.metadata.name,
                "version": plugin.metadata.version,
                "type": plugin.metadata.plugin_type.value,
                "description": plugin.metadata.description,
                "author": plugin.metadata.author,
                "capabilities": [c.value for c in plugin.metadata.capabilities],
            }
            for plugin in self._plugins.values()
        ]

    async def health_check_all(self) -> dict[str, dict[str, Any]]:
        """
        Run health check on all registered plugins.

        Returns:
            Dictionary mapping plugin names to health check results
        """
        results = {}
        for name, plugin in self._plugins.items():
            try:
                results[name] = await plugin.health_check()
            except Exception as e:
                results[name] = {
                    "plugin": name,
                    "status": "unhealthy",
                    "error": str(e),
                }
        return results

    async def cleanup_all(self) -> None:
        """Cleanup all registered plugins."""
        for plugin_name in list(self._plugins.keys()):
            try:
                await self.unregister(plugin_name)
            except Exception as e:
                logger.error(f"Error cleaning up plugin '{plugin_name}': {e}")

    @property
    def count(self) -> int:
        """Get number of registered plugins."""
        return len(self._plugins)

    @property
    def count_by_type(self) -> dict[str, int]:
        """Get plugin count by type."""
        return {
            plugin_type.value: len(plugins)
            for plugin_type, plugins in self._plugins_by_type.items()
        }


# Singleton instance
_registry: PluginRegistry | None = None


def get_plugin_registry() -> PluginRegistry:
    """
    Get the global plugin registry instance.

    Returns:
        Plugin registry singleton
    """
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry
