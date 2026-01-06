"""Base classes for built-in tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class ToolError(Exception):
    """Base exception for tool errors."""

    def __init__(
        self, tool_name: str, message: str, details: dict[str, Any] | None = None
    ):
        self.tool_name = tool_name
        self.message = message
        self.details = details or {}
        super().__init__(f"Tool '{tool_name}' failed: {message}")


class PermissionError(ToolError):
    """Raised when a tool operation is not permitted."""

    pass


class ValidationError(ToolError):
    """Raised when tool input validation fails."""

    pass


class ToolResult(BaseModel):
    """Result of a tool execution.

    Attributes:
        success: Whether the tool executed successfully
        output: The tool's output (can be any JSON-serializable type)
        error: Error message if success is False
        metadata: Additional metadata about the execution
    """

    success: bool = Field(..., description="Whether the tool executed successfully")
    output: Any = Field(default=None, description="The tool's output")
    error: str | None = Field(default=None, description="Error message if failed")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional execution metadata"
    )

    @classmethod
    def success_result(cls, output: Any, **metadata) -> ToolResult:
        """Create a successful result.

        Args:
            output: The tool's output
            **metadata: Additional metadata

        Returns:
            ToolResult with success=True
        """
        return cls(success=True, output=output, metadata=metadata)

    @classmethod
    def error_result(cls, error: str, **metadata) -> ToolResult:
        """Create an error result.

        Args:
            error: Error message
            **metadata: Additional metadata

        Returns:
            ToolResult with success=False
        """
        return cls(success=False, error=error, metadata=metadata)


@runtime_checkable
class Tool(Protocol):
    """Protocol for built-in tools.

    All built-in tools should implement this protocol.
    """

    name: str
    description: str
    parameters: dict[str, Any]

    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult with execution outcome

        Raises:
            ToolError: If tool execution fails
        """
        ...


class BaseTool(ABC):
    """Abstract base class for built-in tools.

    Provides common functionality for all tools including:
    - Parameter validation
    - Permission checking
    - Error handling
    - Metadata tracking
    """

    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        permissions: list[str] | None = None,
    ):
        """Initialize the tool.

        Args:
            name: Tool name (e.g., "read_file")
            description: Human-readable description
            parameters: JSON schema for parameters
            permissions: List of required permissions
        """
        self.name = name
        self.description = description
        self.parameters = parameters
        self.permissions = permissions or []

    @abstractmethod
    async def _execute(self, **kwargs) -> Any:
        """Internal execution logic to be implemented by subclasses.

        Args:
            **kwargs: Validated parameters

        Returns:
            Tool output (any JSON-serializable type)

        Raises:
            ToolError: If execution fails
        """
        pass

    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with error handling.

        Args:
            **kwargs: Tool parameters

        Returns:
            ToolResult with execution outcome
        """
        try:
            # Validate parameters (basic check - can be enhanced)
            self._validate_parameters(kwargs)

            # Execute the tool
            output = await self._execute(**kwargs)

            # Return success result
            return ToolResult.success_result(
                output=output,
                tool_name=self.name,
            )

        except ToolError as e:
            # Re-raise tool errors as-is
            return ToolResult.error_result(
                error=str(e),
                tool_name=self.name,
                error_type=type(e).__name__,
            )

        except Exception as e:
            # Wrap unexpected errors
            return ToolResult.error_result(
                error=f"Unexpected error: {str(e)}",
                tool_name=self.name,
                error_type=type(e).__name__,
            )

    def _validate_parameters(self, params: dict[str, Any]) -> None:
        """Validate parameters against the tool's schema.

        Args:
            params: Parameters to validate

        Raises:
            ValidationError: If validation fails
        """
        # Basic validation - check required parameters
        required = self.parameters.get("required", [])
        missing = set(required) - set(params.keys())

        if missing:
            raise ValidationError(
                self.name,
                f"Missing required parameters: {', '.join(missing)}",
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert tool to dictionary representation.

        Returns:
            Dictionary with tool metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "permissions": self.permissions,
        }
