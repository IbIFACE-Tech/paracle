"""Tool plugin interface for custom tools."""

from abc import abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from paracle_plugins.base import BasePlugin


class ToolParameter(BaseModel):
    """Tool parameter definition."""

    name: str
    type: str  # string, number, boolean, object, array
    description: str
    required: bool = False
    default: Any = None


class ToolSchema(BaseModel):
    """Tool schema definition."""

    name: str = Field(..., description="Tool name (unique)")
    description: str = Field(..., description="Tool description")
    parameters: dict[str, ToolParameter] = Field(
        default_factory=dict, description="Tool parameters"
    )
    returns: str = Field(..., description="Return value description")


class ToolExecutionContext(BaseModel):
    """Context for tool execution."""

    agent_id: str
    execution_id: str
    workspace: str  # Path to workspace directory
    config: dict[str, Any]  # Plugin configuration


class ToolPlugin(BasePlugin):
    """
    Base class for custom tool plugins.

    Implement this to add custom tools to Paracle agents.

    Example:
        >>> class WeatherToolPlugin(ToolPlugin):
        ...     @property
        ...     def metadata(self) -> PluginMetadata:
        ...         return PluginMetadata(
        ...             name="weather-tool",
        ...             version="1.0.0",
        ...             description="Get weather information",
        ...             author="Me",
        ...             plugin_type=PluginType.TOOL,
        ...             capabilities=[PluginCapability.NETWORK_ACCESS],
        ...             dependencies=["requests"]
        ...         )
        ...
        ...     def get_tool_schema(self) -> ToolSchema:
        ...         return ToolSchema(
        ...             name="get_weather",
        ...             description="Get current weather for a location",
        ...             parameters={
        ...                 "location": ToolParameter(
        ...                     name="location",
        ...                     type="string",
        ...                     description="City name",
        ...                     required=True
        ...                 ),
        ...                 "units": ToolParameter(
        ...                     name="units",
        ...                     type="string",
        ...                     description="Temperature units",
        ...                     default="metric"
        ...                 )
        ...             },
        ...             returns="Weather information as JSON"
        ...         )
        ...
        ...     async def execute(
        ...         self,
        ...         context: ToolExecutionContext,
        ...         **kwargs: Any
        ...     ) -> Dict[str, Any]:
        ...         location = kwargs["location"]
        ...         units = kwargs.get("units", "metric")
        ...         # Call weather API
        ...         weather = await self._fetch_weather(location, units)
        ...         return {
        ...             "location": location,
        ...             "temperature": weather["temp"],
        ...             "conditions": weather["conditions"]
        ...         }
    """

    @abstractmethod
    def get_tool_schema(self) -> ToolSchema:
        """
        Get tool schema definition.

        Returns:
            Tool schema with name, description, parameters
        """
        pass

    @abstractmethod
    async def execute(
        self, context: ToolExecutionContext, **kwargs: Any
    ) -> dict[str, Any]:
        """
        Execute the tool with given parameters.

        Args:
            context: Execution context (agent, workspace, config)
            **kwargs: Tool parameters from schema

        Returns:
            Tool execution result

        Raises:
            ValueError: If parameters are invalid
            PermissionError: If tool lacks required permissions
            RuntimeError: If execution fails
        """
        pass

    async def validate_parameters(self, **kwargs: Any) -> bool:
        """
        Validate tool parameters before execution.

        Args:
            **kwargs: Parameters to validate

        Returns:
            True if valid, False otherwise
        """
        schema = self.get_tool_schema()

        # Check required parameters
        for param_name, param in schema.parameters.items():
            if param.required and param_name not in kwargs:
                return False

        return True
