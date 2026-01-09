"""Microsoft Agent Framework (MSAF) adapter.

Provides integration with Microsoft's Agent Framework for building
AI agents with graph-based workflows and multi-agent orchestration.

Supports both:
- New agent-framework SDK (preferred)
- Legacy azure-ai-projects SDK (Azure AI Agent Service)
"""

from typing import Any

# Try new agent-framework SDK first
try:
    from agent_framework import Agent as MSAFAgent
    from agent_framework.azure import AzureOpenAIResponsesClient
    from agent_framework.openai import OpenAIResponsesClient

    MSAF_AVAILABLE = True
    MSAF_VERSION = "agent-framework"
except ImportError:
    MSAF_AVAILABLE = False
    MSAF_VERSION = None
    MSAFAgent = None
    AzureOpenAIResponsesClient = None
    OpenAIResponsesClient = None

# Fallback to azure-ai-projects (Azure AI Agent Service)
if not MSAF_AVAILABLE:
    try:
        from azure.ai.projects import AIProjectClient

        MSAF_AVAILABLE = True
        MSAF_VERSION = "azure-ai-projects"
    except ImportError:
        AIProjectClient = None

if not MSAF_AVAILABLE:
    raise ImportError(
        "Microsoft Agent Framework packages not found. "
        "Install with: pip install agent-framework --pre "
        "OR pip install azure-ai-projects"
    )

from paracle_domain.models import AgentSpec, WorkflowSpec

from paracle_adapters.base import FrameworkAdapter
from paracle_adapters.exceptions import (
    AdapterConfigurationError,
    AdapterExecutionError,
    FeatureNotSupportedError,
)


class MSAFAdapter(FrameworkAdapter):
    """
    Microsoft Agent Framework (MSAF) adapter.

    Integrates Paracle agents with Microsoft's Agent Framework,
    supporting both the new agent-framework SDK and Azure AI Agent Service.

    Features:
    - Agent creation with instructions and tools
    - Graph-based workflow orchestration (agent-framework)
    - Azure AI integration (azure-ai-projects)
    - OpenTelemetry observability

    Example (agent-framework):
        >>> from agent_framework.openai import OpenAIResponsesClient
        >>> client = OpenAIResponsesClient(api_key="...")
        >>> adapter = MSAFAdapter(client=client)
        >>> agent = await adapter.create_agent(agent_spec)

    Example (azure-ai-projects):
        >>> from azure.ai.projects import AIProjectClient
        >>> client = AIProjectClient(conn_str="...")
        >>> adapter = MSAFAdapter(project_client=client)
        >>> agent = await adapter.create_agent(agent_spec)
    """

    def __init__(self, client: Any = None, project_client: Any = None, **config: Any):
        """
        Initialize MSAF adapter.

        Args:
            client: agent-framework client (OpenAIResponsesClient or
                AzureOpenAIResponsesClient)
            project_client: Azure AI Project Client (legacy)
            **config: Additional configuration
                - api_key: OpenAI API key (for agent-framework)
                - azure_credential: Azure credential (for Azure OpenAI)
        """
        super().__init__(**config)

        # Determine which SDK to use based on provided client
        # If client is provided, use new agent-framework SDK
        # If project_client is provided, use legacy azure-ai-projects SDK
        if client is not None:
            self.client = client
            self.project_client = None
            self._use_new_sdk = True
        elif project_client is not None:
            self.client = None
            self.project_client = project_client
            self._use_new_sdk = False
        else:
            # No client provided - use default based on available SDK
            if MSAF_VERSION == "agent-framework":
                self.client = None
                self.project_client = None
                self._use_new_sdk = True
            else:
                self.client = None
                self.project_client = None
                self._use_new_sdk = False

        self._agents: dict[str, Any] = {}

    async def create_agent(self, agent_spec: AgentSpec) -> Any:
        """
        Create a Microsoft Agent Framework agent.

        Args:
            agent_spec: Paracle agent specification

        Returns:
            Dictionary containing agent instance and metadata

        Raises:
            AdapterExecutionError: If agent creation fails
        """
        try:
            if self._use_new_sdk:
                return await self._create_agent_new_sdk(agent_spec)
            else:
                return await self._create_agent_azure(agent_spec)

        except Exception as e:
            if isinstance(e, AdapterConfigurationError | AdapterExecutionError):
                raise
            raise AdapterExecutionError(
                f"Failed to create MSAF agent: {e}",
                framework="msaf",
                original_error=e,
            ) from e

    async def _create_agent_new_sdk(self, agent_spec: AgentSpec) -> dict[str, Any]:
        """Create agent using new agent-framework SDK."""
        if self.client is None:
            raise AdapterConfigurationError(
                "Client must be provided for agent-framework. "
                "Pass client parameter when initializing adapter.",
                framework="msaf",
            )

        # Create agent
        agent = self.client.create_agent(
            name=agent_spec.name,
            instructions=agent_spec.system_prompt or "You are a helpful assistant.",
        )

        # Cache agent
        self._agents[agent_spec.name] = agent

        return {
            "type": "msaf_agent",
            "agent": agent,
            "name": agent_spec.name,
            "instructions": agent_spec.system_prompt,
            "spec": agent_spec,
            "sdk_version": "agent-framework",
        }

    async def _create_agent_azure(self, agent_spec: AgentSpec) -> dict[str, Any]:
        """Create agent using azure-ai-projects SDK."""
        if self.project_client is None:
            raise AdapterConfigurationError(
                "Project client must be provided for Azure AI. "
                "Pass project_client parameter when initializing adapter.",
                framework="msaf",
            )

        # Convert tools
        tools = self._convert_tools(agent_spec)

        # Create agent via Azure AI
        agent = self.project_client.agents.create_agent(
            model=agent_spec.model,
            name=agent_spec.name,
            description=agent_spec.description or "",
            instructions=agent_spec.system_prompt or "You are a helpful assistant.",
            tools=tools,
            headers={"x-ms-enable-preview": "true"},
        )

        # Cache agent
        self._agents[agent_spec.name] = agent

        return {
            "type": "msaf_azure_agent",
            "agent": agent,
            "name": agent_spec.name,
            "agent_id": agent.id,
            "spec": agent_spec,
            "sdk_version": "azure-ai-projects",
        }

    async def execute_agent(
        self,
        agent_instance: Any,
        input_data: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute a Microsoft Agent Framework agent.

        Args:
            agent_instance: Agent dict from create_agent()
            input_data: Input data with "input", "prompt", or "message" key
            **kwargs: Additional execution parameters

        Returns:
            Result dictionary with "response" and "metadata"

        Raises:
            AdapterExecutionError: If execution fails
        """
        try:
            sdk_version = agent_instance.get("sdk_version", "agent-framework")

            if sdk_version == "agent-framework":
                return await self._execute_agent_new_sdk(agent_instance, input_data)
            else:
                return await self._execute_agent_azure(agent_instance, input_data)

        except Exception as e:
            raise AdapterExecutionError(
                f"Failed to execute MSAF agent: {e}",
                framework="msaf",
                original_error=e,
            ) from e

    async def _execute_agent_new_sdk(
        self, agent_instance: dict, input_data: dict
    ) -> dict[str, Any]:
        """Execute using new agent-framework SDK."""
        agent = agent_instance["agent"]

        # Get input message
        user_input = (
            input_data.get("input")
            or input_data.get("prompt")
            or input_data.get("message", "")
        )

        # Run agent
        response = await agent.run(user_input)

        return {
            "response": str(response),
            "metadata": {
                "framework": "msaf",
                "agent_type": "msaf_agent",
                "sdk_version": "agent-framework",
            },
        }

    async def _execute_agent_azure(
        self, agent_instance: dict, input_data: dict
    ) -> dict[str, Any]:
        """Execute using azure-ai-projects SDK."""
        agent = agent_instance["agent"]

        # Create thread for conversation
        thread = self.project_client.agents.create_thread()

        # Get message content
        message_content = (
            input_data.get("input")
            or input_data.get("prompt")
            or input_data.get("message", "")
        )

        # Create message in thread
        self.project_client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=message_content,
        )

        # Run agent
        run = self.project_client.agents.create_and_process_run(
            thread_id=thread.id,
            assistant_id=agent.id,
        )

        # Get response from last message
        messages = self.project_client.agents.list_messages(thread_id=thread.id)
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
                "framework": "msaf",
                "agent_type": "msaf_azure_agent",
                "thread_id": thread.id,
                "run_id": run.id,
                "agent_id": agent.id,
                "sdk_version": "azure-ai-projects",
            },
        }

    async def create_workflow(self, workflow_spec: WorkflowSpec) -> Any:
        """
        Create a Microsoft Agent Framework workflow.

        The new agent-framework SDK supports graph-based workflows.
        Azure AI Agent Service requires manual orchestration.

        Args:
            workflow_spec: Paracle workflow specification

        Returns:
            Workflow instance

        Raises:
            FeatureNotSupportedError: If workflow not supported
        """
        if self._use_new_sdk:
            # agent-framework supports graph-based workflows
            # TODO: Implement when workflow API is stable
            raise FeatureNotSupportedError(
                "msaf",
                "workflows",
                "Graph-based workflows coming soon. "
                "Use Paracle's native orchestration for now.",
            )
        else:
            raise FeatureNotSupportedError(
                "msaf",
                "workflows",
                "Azure AI Agent Service does not support native workflows. "
                "Use Paracle's native orchestration instead.",
            )

    async def execute_workflow(
        self,
        workflow_instance: Any,
        inputs: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute a Microsoft Agent Framework workflow."""
        raise FeatureNotSupportedError(
            "msaf",
            "workflow_execution",
            "Workflow execution not yet implemented.",
        )

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
                    tools.append(
                        {
                            "type": "function",
                            "function": {
                                "name": tool_spec,
                                "description": f"Tool: {tool_spec}",
                                "parameters": {
                                    "type": "object",
                                    "properties": {},
                                },
                            },
                        }
                    )
            elif isinstance(tool_spec, dict):
                # Detailed tool spec
                tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool_spec.get("name", "unknown"),
                            "description": tool_spec.get("description", ""),
                            "parameters": tool_spec.get(
                                "parameters",
                                {
                                    "type": "object",
                                    "properties": {},
                                },
                            ),
                        },
                    }
                )

        return tools

    @property
    def framework_name(self) -> str:
        """Return framework identifier."""
        return "msaf"

    @property
    def supported_features(self) -> list[str]:
        """Return list of supported features."""
        features = ["agents", "tools", "async"]

        if self._use_new_sdk:
            features.extend(
                [
                    "graph_workflows",
                    "opentelemetry",
                    "middleware",
                ]
            )
        else:
            features.extend(
                [
                    "threads",
                    "file_search",
                    "code_interpreter",
                ]
            )

        return features

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
        # Check for at least one client
        has_client = "client" in config and config["client"] is not None
        has_project = (
            "project_client" in config and config["project_client"] is not None
        )

        if not has_client and not has_project:
            raise ValueError(
                "Either 'client' (agent-framework) or "
                "'project_client' (azure-ai-projects) must be provided"
            )

        return True

    @staticmethod
    def get_version_info() -> dict[str, Any]:
        """Get MSAF version information."""
        info = {
            "msaf_available": MSAF_AVAILABLE,
            "msaf_version": MSAF_VERSION,
        }

        if MSAF_VERSION == "agent-framework":
            try:
                import agent_framework

                info["package_version"] = getattr(
                    agent_framework, "__version__", "unknown"
                )
            except (ImportError, AttributeError):
                pass
        elif MSAF_VERSION == "azure-ai-projects":
            try:
                import azure.ai.projects

                info["package_version"] = getattr(
                    azure.ai.projects, "__version__", "unknown"
                )
            except (ImportError, AttributeError):
                pass

        return info
