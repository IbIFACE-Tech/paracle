"""Base classes for MetaAgent capabilities.

Provides the foundation for all integrated capabilities that
extend the MetaAgent's functionality beyond artifact generation.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CapabilityConfig(BaseModel):
    """Base configuration for capabilities."""

    enabled: bool = Field(default=True, description="Whether capability is enabled")
    timeout: float = Field(
        default=30.0, ge=1.0, le=300.0, description="Timeout in seconds"
    )
    max_retries: int = Field(default=3, ge=0, le=10, description="Max retry attempts")


class CapabilityResult(BaseModel):
    """Result of a capability execution."""

    capability: str = Field(..., description="Capability name")
    success: bool = Field(..., description="Whether execution succeeded")
    output: Any = Field(default=None, description="Execution output")
    error: str | None = Field(default=None, description="Error message if failed")
    duration_ms: float = Field(default=0.0, description="Execution duration in ms")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    def success_result(
        cls,
        capability: str,
        output: Any,
        duration_ms: float = 0.0,
        **metadata,
    ) -> "CapabilityResult":
        """Create a successful result."""
        return cls(
            capability=capability,
            success=True,
            output=output,
            duration_ms=duration_ms,
            metadata=metadata,
        )

    @classmethod
    def error_result(
        cls,
        capability: str,
        error: str,
        duration_ms: float = 0.0,
        **metadata,
    ) -> "CapabilityResult":
        """Create an error result."""
        return cls(
            capability=capability,
            success=False,
            error=error,
            duration_ms=duration_ms,
            metadata=metadata,
        )


class BaseCapability(ABC):
    """Abstract base class for all MetaAgent capabilities.

    Capabilities extend the MetaAgent with powerful integrations
    like web search, code execution, MCP tools, etc.

    Example:
        >>> class MyCapability(BaseCapability):
        ...     name = "my_capability"
        ...
        ...     async def execute(self, **kwargs) -> CapabilityResult:
        ...         result = await self._do_work(**kwargs)
        ...         return CapabilityResult.success_result(
        ...             capability=self.name,
        ...             output=result
        ...         )
    """

    name: str = "base"
    description: str = "Base capability"

    def __init__(self, config: CapabilityConfig | None = None):
        """Initialize capability with configuration.

        Args:
            config: Capability configuration
        """
        self.config = config or CapabilityConfig()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize capability resources.

        Override to perform async initialization.
        """
        self._initialized = True

    async def shutdown(self) -> None:
        """Cleanup capability resources.

        Override to perform async cleanup.
        """
        self._initialized = False

    @abstractmethod
    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute the capability.

        Args:
            **kwargs: Capability-specific parameters

        Returns:
            CapabilityResult with execution outcome
        """
        pass

    @property
    def is_initialized(self) -> bool:
        """Check if capability is initialized."""
        return self._initialized

    @property
    def is_enabled(self) -> bool:
        """Check if capability is enabled."""
        return self.config.enabled

    def __repr__(self) -> str:
        status = "enabled" if self.is_enabled else "disabled"
        return f"{self.__class__.__name__}(name={self.name}, status={status})"
