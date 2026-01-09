"""Base protocol for framework adapters."""

from abc import ABC, abstractmethod
from typing import Any

from paracle_domain.models import AgentSpec, WorkflowSpec


class FrameworkAdapter(ABC):
    """
    Abstract base class for framework adapters.

    Framework adapters enable Paracle agents to run on different
    multi-agent frameworks (MSAF, LangChain, LlamaIndex, etc.).

    This follows the Adapter pattern from hexagonal architecture,
    allowing Paracle to integrate with external frameworks without
    coupling the domain logic to any specific implementation.
    """

    def __init__(self, **config: Any):
        """
        Initialize the adapter with configuration.

        Args:
            **config: Framework-specific configuration
        """
        self.config = config

    @abstractmethod
    async def create_agent(self, agent_spec: AgentSpec) -> Any:
        """
        Create a framework-specific agent instance from Paracle AgentSpec.

        Args:
            agent_spec: Paracle agent specification

        Returns:
            Framework-native agent instance

        Example:
            >>> adapter = MSAFAdapter(...)
            >>> spec = AgentSpec(name="helper", model="gpt-4")
            >>> azure_agent = await adapter.create_agent(spec)
        """
        pass

    @abstractmethod
    async def execute_agent(
        self,
        agent_instance: Any,
        input_data: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute a framework-specific agent.

        Args:
            agent_instance: Framework-native agent instance
            input_data: Input data for the agent
            **kwargs: Framework-specific execution parameters

        Returns:
            Execution result as dictionary with standardized keys:
            - "response": The agent's response (str)
            - "metadata": Additional execution metadata (dict)

        Example:
            >>> result = await adapter.execute_agent(
            ...     agent_instance,
            ...     {"prompt": "Hello, how are you?"}
            ... )
            >>> print(result["response"])
        """
        pass

    @abstractmethod
    async def create_workflow(self, workflow_spec: WorkflowSpec) -> Any:
        """
        Create a framework-specific workflow from Paracle WorkflowSpec.

        Args:
            workflow_spec: Paracle workflow specification

        Returns:
            Framework-native workflow instance

        Example:
            >>> spec = WorkflowSpec(name="pipeline", steps=[...])
            >>> workflow = await adapter.create_workflow(spec)
        """
        pass

    @abstractmethod
    async def execute_workflow(
        self,
        workflow_instance: Any,
        inputs: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute a framework-specific workflow.

        Args:
            workflow_instance: Framework-native workflow instance
            inputs: Input data for the workflow
            **kwargs: Framework-specific execution parameters

        Returns:
            Execution result as dictionary

        Example:
            >>> result = await adapter.execute_workflow(
            ...     workflow,
            ...     {"input": "data"}
            ... )
        """
        pass

    @property
    @abstractmethod
    def framework_name(self) -> str:
        """Return the framework identifier (e.g., 'msaf', 'langchain')."""
        pass

    @property
    @abstractmethod
    def supported_features(self) -> list[str]:
        """
        Return list of supported features.

        Common features:
        - "agents": Agent execution
        - "workflows": Workflow orchestration
        - "tools": Tool calling
        - "memory": Conversation memory
        - "streaming": Response streaming
        - "async": Async execution
        """
        pass

    @abstractmethod
    def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate framework-specific configuration.

        Args:
            config: Configuration dictionary

        Returns:
            True if valid

        Raises:
            ValueError: If configuration is invalid
        """
        pass

    def supports_feature(self, feature: str) -> bool:
        """
        Check if adapter supports a specific feature.

        Args:
            feature: Feature name to check

        Returns:
            True if feature is supported
        """
        return feature in self.supported_features

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(framework={self.framework_name})"
