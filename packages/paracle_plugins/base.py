"""Base plugin interface and types for Paracle plugin system."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PluginType(str, Enum):
    """Types of plugins supported by Paracle."""

    PROVIDER = "provider"  # LLM provider plugins
    TOOL = "tool"  # Custom tool plugins
    ADAPTER = "adapter"  # Framework adapter plugins
    OBSERVER = "observer"  # Execution observer plugins
    MEMORY = "memory"  # Memory backend plugins


class PluginCapability(str, Enum):
    """Capabilities that plugins can declare."""

    # Provider capabilities
    TEXT_GENERATION = "text_generation"
    CHAT_COMPLETION = "chat_completion"
    STREAMING = "streaming"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"

    # Tool capabilities
    FILE_ACCESS = "file_access"
    NETWORK_ACCESS = "network_access"
    SHELL_ACCESS = "shell_access"
    DATABASE_ACCESS = "database_access"

    # Observer capabilities
    EXECUTION_TRACKING = "execution_tracking"
    METRICS_COLLECTION = "metrics_collection"
    ERROR_REPORTING = "error_reporting"
    COST_TRACKING = "cost_tracking"

    # Memory capabilities
    PERSISTENT_STORAGE = "persistent_storage"
    VECTOR_SEARCH = "vector_search"
    SEMANTIC_CACHE = "semantic_cache"


class PluginMetadata(BaseModel):
    """Metadata for a Paracle plugin."""

    name: str = Field(..., description="Plugin name (unique identifier)")
    version: str = Field(..., description="Plugin version (semver)")
    description: str = Field(..., description="Plugin description")
    author: str = Field(..., description="Plugin author")
    homepage: str | None = Field(None, description="Plugin homepage URL")
    license: str = Field(default="MIT", description="Plugin license")

    plugin_type: PluginType = Field(..., description="Type of plugin")
    capabilities: list[PluginCapability] = Field(
        default_factory=list, description="Capabilities provided by this plugin"
    )

    dependencies: list[str] = Field(
        default_factory=list, description="Python package dependencies (pip install)"
    )

    paracle_version: str = Field(
        default=">=1.0.0", description="Compatible Paracle version"
    )

    config_schema: dict[str, Any] = Field(
        default_factory=dict, description="JSON schema for plugin configuration"
    )

    tags: list[str] = Field(
        default_factory=list, description="Tags for plugin discovery"
    )


class BasePlugin(ABC):
    """
    Base class for all Paracle plugins.

    All plugins must inherit from this class and implement:
    - metadata property: Plugin metadata
    - initialize() method: Plugin initialization
    - cleanup() method: Cleanup resources

    Example:
        >>> class MyProviderPlugin(BasePlugin):
        ...     @property
        ...     def metadata(self) -> PluginMetadata:
        ...         return PluginMetadata(
        ...             name="my-provider",
        ...             version="1.0.0",
        ...             description="Custom LLM provider",
        ...             author="Me",
        ...             plugin_type=PluginType.PROVIDER,
        ...             capabilities=[PluginCapability.CHAT_COMPLETION]
        ...         )
        ...
        ...     async def initialize(self, config: Dict[str, Any]) -> None:
        ...         self.api_key = config["api_key"]
        ...
        ...     async def cleanup(self) -> None:
        ...         pass
    """

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata.

        Returns:
            Plugin metadata including name, version, capabilities, etc.
        """
        pass

    @abstractmethod
    async def initialize(self, config: dict[str, Any]) -> None:
        """Initialize the plugin with configuration.

        Called once when the plugin is loaded. Use this to:
        - Validate configuration
        - Initialize connections
        - Allocate resources

        Args:
            config: Plugin configuration from .parac/config/plugins.yaml

        Raises:
            ValueError: If configuration is invalid
            ConnectionError: If unable to connect to external services
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup plugin resources.

        Called when the plugin is unloaded. Use this to:
        - Close connections
        - Release resources
        - Flush buffers
        """
        pass

    async def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate plugin configuration against schema.

        Args:
            config: Configuration to validate

        Returns:
            True if valid, False otherwise
        """
        # Basic validation - plugins can override for custom validation
        if not self.metadata.config_schema:
            return True

        # TODO: Implement JSON schema validation
        return True

    async def health_check(self) -> dict[str, Any]:
        """Check plugin health and status.

        Returns:
            Health check result with status and details
        """
        return {
            "plugin": self.metadata.name,
            "version": self.metadata.version,
            "status": "healthy",
            "capabilities": [c.value for c in self.metadata.capabilities],
        }
