"""Adapter plugin interface for framework integrations."""

from abc import abstractmethod
from typing import Any

from pydantic import BaseModel

from paracle_plugins.base import BasePlugin


class AgentConfig(BaseModel):
    """Agent configuration for framework."""

    name: str
    role: str
    model: str
    provider: str
    tools: list[str] = []
    config: dict[str, Any] = {}


class ExecutionResult(BaseModel):
    """Result from framework execution."""

    success: bool
    output: Any
    error: str | None = None
    metadata: dict[str, Any] = {}


class AdapterPlugin(BasePlugin):
    """
    Base class for framework adapter plugins.

    Implement this to integrate Paracle with external frameworks:
    - LangChain
    - LlamaIndex
    - AutoGPT
    - CrewAI
    - Semantic Kernel

    Example:
        >>> class LangChainAdapterPlugin(AdapterPlugin):
        ...     @property
        ...     def metadata(self) -> PluginMetadata:
        ...         return PluginMetadata(
        ...             name="langchain-adapter",
        ...             version="1.0.0",
        ...             description="LangChain integration adapter",
        ...             author="Me",
        ...             plugin_type=PluginType.ADAPTER,
        ...             dependencies=["langchain"]
        ...         )
        ...
        ...     async def create_agent(
        ...         self, config: AgentConfig
        ...     ) -> Any:
        ...         from langchain.agents import initialize_agent
        ...         # Create LangChain agent from Paracle config
        ...         return initialize_agent(
        ...             tools=self._load_tools(config.tools),
        ...             llm=self._create_llm(config),
        ...             agent="zero-shot-react-description"
        ...         )
        ...
        ...     async def execute_agent(
        ...         self,
        ...         agent: Any,
        ...         task: str,
        ...         context: Dict[str, Any]
        ...     ) -> ExecutionResult:
        ...         try:
        ...             result = agent.run(task)
        ...             return ExecutionResult(
        ...                 success=True,
        ...                 output=result
        ...             )
        ...         except Exception as e:
        ...             return ExecutionResult(
        ...                 success=False,
        ...                 output=None,
        ...                 error=str(e)
        ...             )
    """

    @abstractmethod
    async def create_agent(self, config: AgentConfig) -> Any:
        """
        Create framework-specific agent from Paracle config.

        Args:
            config: Paracle agent configuration

        Returns:
            Framework-specific agent object
        """
        pass

    @abstractmethod
    async def execute_agent(
        self, agent: Any, task: str, context: dict[str, Any]
    ) -> ExecutionResult:
        """
        Execute framework agent with task.

        Args:
            agent: Framework agent object
            task: Task description
            context: Execution context

        Returns:
            Execution result
        """
        pass

    async def get_supported_features(self) -> list[str]:
        """
        Get list of supported framework features.

        Returns:
            List of feature names
        """
        return []

    async def validate_agent_config(self, config: AgentConfig) -> bool:
        """
        Validate agent configuration for this framework.

        Args:
            config: Agent configuration

        Returns:
            True if valid, False otherwise
        """
        return True
