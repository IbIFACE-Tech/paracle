"""A2A Call Tool.

BaseTool implementation for calling external A2A agents.
"""

from typing import Any

from pydantic import BaseModel, Field

from paracle_a2a.client import ParacleA2AClient
from paracle_a2a.config import A2AClientConfig
from paracle_a2a.models import TaskState, get_message_text


class A2ACallToolInput(BaseModel):
    """Input schema for A2A call tool."""

    url: str = Field(
        ...,
        description="A2A agent endpoint URL",
    )
    message: str = Field(
        ...,
        description="Message to send to the agent",
    )
    context_id: str | None = Field(
        default=None,
        description="Context ID for conversation continuity",
    )
    wait: bool = Field(
        default=True,
        description="Wait for task completion",
    )
    timeout_seconds: float = Field(
        default=60.0,
        description="Timeout in seconds",
    )


class A2ACallToolOutput(BaseModel):
    """Output schema for A2A call tool."""

    task_id: str = Field(
        ...,
        description="A2A task ID",
    )
    status: str = Field(
        ...,
        description="Task status",
    )
    result: str | None = Field(
        default=None,
        description="Task result (if completed)",
    )
    error: str | None = Field(
        default=None,
        description="Error message (if failed)",
    )


class A2ACallTool:
    """Tool for calling external A2A agents.

    This tool can be registered in the agent tool registry
    to allow Paracle agents to invoke external A2A-compatible
    agents as part of their workflows.

    Example:
        ```python
        from paracle_a2a.integration import A2ACallTool

        tool = A2ACallTool()

        # Register with tool registry
        from paracle_orchestration import agent_tool_registry
        agent_tool_registry.register_tool("a2a_call", tool)

        # Or use directly
        result = await tool.execute({
            "url": "http://example.com/a2a/agents/helper",
            "message": "Help me analyze this code",
        })
        ```
    """

    name: str = "a2a_call"
    description: str = (
        "Call an external A2A-compatible AI agent. "
        "Use this to delegate tasks to specialized agents available via A2A protocol."
    )

    def __init__(
        self,
        config: A2AClientConfig | None = None,
        default_timeout: float = 60.0,
    ):
        """Initialize A2A call tool.

        Args:
            config: Client configuration
            default_timeout: Default timeout in seconds
        """
        self.config = config or A2AClientConfig()
        self.default_timeout = default_timeout

    def get_input_schema(self) -> dict[str, Any]:
        """Get JSON schema for tool input.

        Returns:
            JSON Schema for input
        """
        return A2ACallToolInput.model_json_schema()

    def get_output_schema(self) -> dict[str, Any]:
        """Get JSON schema for tool output.

        Returns:
            JSON Schema for output
        """
        return A2ACallToolOutput.model_json_schema()

    async def execute(
        self,
        input_data: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> A2ACallToolOutput:
        """Execute A2A call.

        Args:
            input_data: Tool input parameters
            context: Optional execution context

        Returns:
            Tool output with task result
        """
        # Parse input
        tool_input = A2ACallToolInput(**input_data)

        # Create client with timeout
        config = A2AClientConfig(
            timeout_seconds=tool_input.timeout_seconds,
            **{
                k: v
                for k, v in self.config.model_dump().items()
                if k != "timeout_seconds"
            },
        )
        client = ParacleA2AClient(tool_input.url, config)

        try:
            # Invoke agent
            task = await client.invoke(
                message=tool_input.message,
                context_id=tool_input.context_id,
                wait=tool_input.wait,
            )

            # Extract result
            result = None
            error = None

            # SDK uses lowercase enum values
            if task.status.state == TaskState.completed:
                # Get message text from status if present
                if task.status.message:
                    result = get_message_text(task.status.message)
                else:
                    result = "Task completed"
            elif task.status.state == TaskState.failed:
                if task.status.message:
                    error = get_message_text(task.status.message)
                else:
                    error = "Task failed"

            return A2ACallToolOutput(
                task_id=task.id,
                status=task.status.state.value,
                result=result,
                error=error,
            )

        except Exception as e:
            return A2ACallToolOutput(
                task_id="",
                status="failed",
                result=None,
                error=str(e),
            )

    async def __call__(
        self,
        input_data: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> A2ACallToolOutput:
        """Make tool callable.

        Args:
            input_data: Tool input
            context: Optional context

        Returns:
            Tool output
        """
        return await self.execute(input_data, context)


def create_a2a_tool(
    config: A2AClientConfig | None = None,
) -> A2ACallTool:
    """Create A2A call tool for registration.

    Args:
        config: Optional client config

    Returns:
        A2ACallTool instance
    """
    return A2ACallTool(config)
