"""Plugin loader for discovering and loading plugins."""

import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Any

import yaml

from paracle_plugins.base import BasePlugin
from paracle_plugins.registry import get_plugin_registry

logger = logging.getLogger(__name__)


class PluginLoader:
    """
    Plugin loader for discovering and loading Paracle plugins.

    Supports loading plugins from:
    - .parac/plugins/ directory (Python files)
    - plugins.yaml configuration
    - Installed Python packages (entry points)

    Example:
        >>> loader = PluginLoader(parac_root=Path(".parac"))
        >>> await loader.load_all()
        >>> # All plugins are now registered in the global registry
    """

    def __init__(self, parac_root: Path | None = None):
        """
        Initialize plugin loader.

        Args:
            parac_root: Path to .parac directory
        """
        self.parac_root = parac_root or self._find_parac_root()
        self.registry = get_plugin_registry()

    def _find_parac_root(self) -> Path | None:
        """Find .parac directory by walking up from cwd."""
        current = Path.cwd()
        while current != current.parent:
            parac = current / ".parac"
            if parac.is_dir():
                return parac
            current = current.parent
        return None

    async def load_all(self) -> int:
        """
        Load all plugins from all sources.

        Returns:
            Number of plugins loaded

        Raises:
            Exception: If critical plugin fails to load
        """
        count = 0

        # Load from .parac/plugins/ directory
        count += await self.load_from_directory()

        # Load from plugins.yaml
        count += await self.load_from_config()

        # Load from entry points
        count += await self.load_from_entry_points()

        logger.info(f"Loaded {count} plugins")
        return count

    async def load_from_directory(self) -> int:
        """
        Load plugins from .parac/plugins/ directory.

        Looks for Python files with Plugin classes.

        Returns:
            Number of plugins loaded
        """
        if not self.parac_root:
            return 0

        plugins_dir = self.parac_root / "plugins"
        if not plugins_dir.exists():
            return 0

        count = 0
        for plugin_file in plugins_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue

            try:
                plugin = await self._load_plugin_from_file(plugin_file)
                if plugin:
                    config = await self._load_plugin_config(plugin.metadata.name)
                    await self.registry.register(plugin, config)
                    count += 1
            except Exception as e:
                logger.error(f"Failed to load plugin from {plugin_file}: {e}")

        return count

    async def load_from_config(self) -> int:
        """
        Load plugins from plugins.yaml configuration.

        Returns:
            Number of plugins loaded
        """
        if not self.parac_root:
            return 0

        config_path = self.parac_root / "config" / "plugins.yaml"
        if not config_path.exists():
            return 0

        try:
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            count = 0
            for plugin_config in config.get("plugins", []):
                if not plugin_config.get("enabled", True):
                    continue

                try:
                    plugin = await self._load_plugin_by_name(plugin_config["name"])
                    if plugin:
                        await self.registry.register(
                            plugin, plugin_config.get("config", {})
                        )
                        count += 1
                except Exception as e:
                    logger.error(
                        f"Failed to load plugin " f"'{plugin_config['name']}': {e}"
                    )

            return count
        except Exception as e:
            logger.error(f"Failed to read plugins.yaml: {e}")
            return 0

    async def load_from_entry_points(self) -> int:
        """
        Load plugins from Python package entry points.

        Looks for entry points in group 'paracle.plugins'.

        Returns:
            Number of plugins loaded
        """
        try:
            import importlib.metadata

            count = 0
            for entry_point in importlib.metadata.entry_points(group="paracle.plugins"):
                try:
                    plugin_class = entry_point.load()
                    plugin = plugin_class()

                    config = await self._load_plugin_config(plugin.metadata.name)
                    await self.registry.register(plugin, config)
                    count += 1
                except Exception as e:
                    logger.error(
                        f"Failed to load plugin entry point "
                        f"'{entry_point.name}': {e}"
                    )

            return count
        except ImportError:
            # importlib.metadata not available (Python < 3.8)
            return 0

    async def _load_plugin_from_file(self, plugin_file: Path) -> BasePlugin | None:
        """
        Load plugin from Python file.

        Args:
            plugin_file: Path to plugin Python file

        Returns:
            Plugin instance or None
        """
        spec = importlib.util.spec_from_file_location(plugin_file.stem, plugin_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Look for Plugin class
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BasePlugin)
                    and attr is not BasePlugin
                ):
                    return attr()

        return None

    async def _load_plugin_by_name(self, plugin_name: str) -> BasePlugin | None:
        """
        Load plugin by name (from installed package).

        Args:
            plugin_name: Plugin name

        Returns:
            Plugin instance or None
        """
        try:
            # Try to import as package
            module = importlib.import_module(plugin_name)
            if hasattr(module, "Plugin"):
                return module.Plugin()

            # Try common naming patterns
            for class_name in ["Plugin", f"{plugin_name}Plugin"]:
                if hasattr(module, class_name):
                    plugin_class = getattr(module, class_name)
                    return plugin_class()

            return None
        except ImportError:
            return None

    async def _load_plugin_config(self, plugin_name: str) -> dict[str, Any]:
        """
        Load configuration for a plugin.

        Args:
            plugin_name: Plugin name

        Returns:
            Plugin configuration dictionary
        """
        if not self.parac_root:
            return {}

        config_path = self.parac_root / "config" / "plugins.yaml"
        if not config_path.exists():
            return {}

        try:
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            for plugin_config in config.get("plugins", []):
                if plugin_config.get("name") == plugin_name:
                    return plugin_config.get("config", {})

            return {}
        except Exception:
            return {}

    async def reload_plugin(self, plugin_name: str) -> bool:
        """
        Reload a plugin (unregister and load again).

        Args:
            plugin_name: Plugin name to reload

        Returns:
            True if reloaded successfully
        """
        try:
            await self.registry.unregister(plugin_name)
            plugin = await self._load_plugin_by_name(plugin_name)
            if plugin:
                config = await self._load_plugin_config(plugin_name)
                await self.registry.register(plugin, config)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to reload plugin '{plugin_name}': {e}")
            return False
