"""Microsoft Agent Framework (MSAF) adapter."""

from typing import Any

try:
    from azure.ai.projects import AIProjectClient
except ImportError:
    raise ImportError(
        "azure-ai-projects package is required for MSAF adapter. "
        "Install with: pip install azure-ai-projects"
    )

from paracle_domain.models import AgentSpec, WorkflowSpec

from paracle_adapters.base import FrameworkAdapter
from paracle_adapters.exceptions import AdapterExecutionError


class MSAFAdapter(FrameworkAdapter):
    """
    Microsoft Agent Framework (MSAF) adapter.

    Integrates Paracle agents with Azure AI Agent Service,
    enabling deployment and execution on Azure infrastructure.

    Requires Azure AI Project Client with proper authentication.
    """

    def __init__(self, project_client: AIProjectClient, **config: Any):
        """
        Initialize MSAF adapter.

        Args:
            project_client: Azure AI Project Client instance
            **config: Additional configuration
        """
        super().__init__(**config)
        self.client = project_client

    async def create_agent(self, agent_spec: AgentSpec) -> Any:
        """
        Create an Azure AI Agent from Paracle AgentSpec.

        Args:
            agent_spec: Paracle agent specification

        Returns:
            Azure AI Agent instance

        Raises:
            AdapterExecutionError: If agent creation fails
        """
        try:
            # Convert tools
            tools = self._convert_tools(agent_spec)

            # Create agent via Azure AI
            agent = self.client.agents.create_agent(
                model=agent_spec.model,
                name=agent_spec.name,
                description=agent_spec.description or "",
                instructions=agent_spec.system_prompt or "You are a helpful assistant.",
                tools=tools,
                headers={"x-ms-enable-preview": "true"},
            )

            return agent

        except Exception as e:
            raise AdapterExecutionError(
                f"Failed to create MSAF agent: {e}",
                framework="msaf",
                original_error=e,
            ) from e

    async def execute_agent(
        self,
        agent_instance: Any,
        input_data: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute an Azure AI Agent.

        Args:
            agent_instance: Azure AI Agent instance
            input_data: Input data (must contain "prompt" or "message")
            **kwargs: Additional execution parameters

        Returns:
            Result dictionary with "response" and "metadata"

        Raises:
            AdapterExecutionError: If execution fails
        """
        try:
            # Create thread for conversation
            thread = self.client.agents.create_thread()

            # Get message content
            message_content = input_data.get("prompt") or input_data.get("message", "")

            # Create message in thread
            self.client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=message_content,
            )

            # Run agent
            run = self.client.agents.create_and_process_run(
                thread_id=thread.id,
                assistant_id=agent_instance.id,
            )

            # Get response from last message
            messages = self.client.agents.list_messages(thread_id=thread.id)
            last_message = messages.data[0] if messages.data else None

            response_content = ""
            if last_message and last_message.role == "assistant":
                # Extract text from content blocks
                for content_block in last_message.content:
                    if hasattr(content_block, "text"):
                        response_content += content_block.text.value

            return {
                "response": response_content,
                "metadata": {
                    "thread_id": thread.id,
                    "run_id": run.id,
                    "agent_id": agent_instance.id,
                    "framework": "msaf",
                },
            }

        except Exception as e:
            raise AdapterExecutionError(
                f"Failed to execute MSAF agent: {e}",
                framework="msaf",
                original_error=e,
            ) from e

    async def create_workflow(self, workflow_spec: WorkflowSpec) -> Any:
        """
        Create an Azure AI workflow.

        Args:
            workflow_spec: Paracle workflow specification

        Returns:
            Azure AI workflow/orchestration instance

        Note:
            MSAF workflow support depends on Azure AI capabilities.
            Complex workflows may require custom orchestration.
        """
        # MSAF doesn't have native workflow concept
        # Would need to orchestrate multiple agents
        raise NotImplementedError(
            "MSAF adapter does not yet support workflows. "
            "Use Paracle's native orchestration or orchestrate agents manually."
        )

    async def execute_workflow(
        self,
        workflow_instance: Any,
        inputs: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute an Azure AI workflow."""
        raise NotImplementedError("MSAF workflows not yet implemented")

    def _convert_tools(self, agent_spec: AgentSpec) -> list[dict[str, Any]]:
        """
        Convert Paracle tools to Azure AI tools format.

        Args:
            agent_spec: Agent specification

        Returns:
            List of Azure AI tool definitions
        """
        tools = []

        # Get tool specs from agent config
        tool_specs = agent_spec.config.get("tools", [])

        for tool_spec in tool_specs:
            if isinstance(tool_spec, str):
                # Check for built-in tools
                if tool_spec.lower() == "code_interpreter":
                    tools.append({"type": "code_interpreter"})
                elif tool_spec.lower() == "file_search":
                    tools.append({"type": "file_search"})
                else:
                    # Custom function tool (simplified)
                    tools.append({
                        "type": "function",
                        "function": {
                            "name": tool_spec,
                            "description": f"Tool: {tool_spec}",
                            "parameters": {
                                "type": "object",
                                "properties": {},
                            },
                        },
                    })
            elif isinstance(tool_spec, dict):
                # Detailed tool spec
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool_spec.get("name", "unknown"),
                        "description": tool_spec.get("description", ""),
                        "parameters": tool_spec.get("parameters", {
                            "type": "object",
                            "properties": {},
                        }),
                    },
                })

        return tools

    @property
    def framework_name(self) -> str:
        """Return framework identifier."""
        return "msaf"

    @property
    def supported_features(self) -> list[str]:
        """Return list of supported features."""
        return [
            "agents",
            "tools",
            "threads",
            "file_search",
            "code_interpreter",
            "async",
        ]

    def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate MSAF adapter configuration.

        Args:
            config: Configuration dictionary

        Returns:
            True if valid

        Raises:
            ValueError: If configuration is invalid
        """
        if "project_client" in config:
            if not isinstance(config["project_client"], AIProjectClient):
                raise ValueError(
                    "project_client must be an instance of AIProjectClient"
                )

        return True
