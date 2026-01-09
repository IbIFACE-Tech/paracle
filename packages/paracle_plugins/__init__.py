"""
Paracle Plugin System

Extensibility framework for community contributions.
Enables developers to extend Paracle with custom:
- LLM Providers
- Tools
- Framework Adapters
- Execution Observers
- Memory Backends
"""

from paracle_plugins.base import (
    BasePlugin,
    PluginCapability,
    PluginMetadata,
    PluginType,
)
from paracle_plugins.loader import PluginLoader
from paracle_plugins.registry import PluginRegistry, get_plugin_registry

__version__ = "1.0.1"

__all__ = [
    "BasePlugin",
    "PluginCapability",
    "PluginMetadata",
    "PluginType",
    "PluginLoader",
    "PluginRegistry",
    "get_plugin_registry",
]
