"""LangChain framework adapter."""

from typing import Any

try:
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain.prompts import PromptTemplate
    from langchain_core.language_models import BaseLanguageModel
    from langchain_core.tools import Tool
except ImportError:
    raise ImportError(
        "langchain packages are required for LangChain adapter. "
        "Install with: pip install langchain langchain-core"
    )

from paracle_adapters.base import FrameworkAdapter
from paracle_adapters.exceptions import (
    AdapterExecutionError,
    FeatureNotSupportedError,
)
from paracle_domain.models import AgentSpec, WorkflowSpec


class LangChainAdapter(FrameworkAdapter):
    """
    LangChain framework adapter.

    Integrates Paracle agents with the LangChain ecosystem,
    enabling use of LangChain tools, chains, and agents.
    """

    def __init__(self, llm: BaseLanguageModel | None = None, **config: Any):
        """
        Initialize LangChain adapter.

        Args:
            llm: LangChain language model instance (e.g., ChatOpenAI)
            **config: Additional configuration
        """
        super().__init__(**config)
        self.llm = llm

    async def create_agent(self, agent_spec: AgentSpec) -> AgentExecutor:
        """
        Create a LangChain agent from Paracle AgentSpec.

        Args:
            agent_spec: Paracle agent specification

        Returns:
            LangChain AgentExecutor

        Raises:
            AdapterExecutionError: If agent creation fails
        """
        try:
            if self.llm is None:
                raise ValueError(
                    "LLM must be provided to create agents. "
                    "Pass llm parameter when initializing adapter."
                )

            # Create tools from agent spec
            tools = self._create_tools(agent_spec)

            # Create prompt template
            prompt = self._create_prompt(agent_spec)

            # Create agent
            agent = create_react_agent(
                llm=self.llm,
                tools=tools,
                prompt=prompt,
            )

            # Return executor
            return AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=self.config.get("verbose", False),
                handle_parsing_errors=True,
                max_iterations=self.config.get("max_iterations", 15),
            )

        except Exception as e:
            raise AdapterExecutionError(
                f"Failed to create LangChain agent: {e}",
                framework="langchain",
                original_error=e,
            ) from e

    async def execute_agent(
        self,
        agent_instance: AgentExecutor,
        input_data: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute a LangChain agent.

        Args:
            agent_instance: LangChain AgentExecutor
            input_data: Input data (must contain "input" key)
            **kwargs: Additional execution parameters

        Returns:
            Result dictionary with "response" and "metadata"

        Raises:
            AdapterExecutionError: If execution fails
        """
        try:
            # LangChain expects "input" key
            if "input" not in input_data and "prompt" in input_data:
                input_data = {"input": input_data["prompt"]}

            # Execute
            result = await agent_instance.ainvoke(input_data, **kwargs)

            return {
                "response": result.get("output", ""),
                "metadata": {
                    "intermediate_steps": result.get("intermediate_steps", []),
                    "framework": "langchain",
                },
            }

        except Exception as e:
            raise AdapterExecutionError(
                f"Failed to execute LangChain agent: {e}",
                framework="langchain",
                original_error=e,
            ) from e

    async def create_workflow(self, workflow_spec: WorkflowSpec) -> Any:
        """
        Create a LangChain workflow (chain).

        Args:
            workflow_spec: Paracle workflow specification

        Returns:
            LangChain chain instance

        Note:
            Workflow support in LangChain adapter is limited.
            For complex workflows, use Paracle's native orchestration.
        """
        raise FeatureNotSupportedError("langchain", "workflows")

    async def execute_workflow(
        self,
        workflow_instance: Any,
        inputs: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute a LangChain workflow."""
        raise FeatureNotSupportedError("langchain", "workflows")

    def _create_tools(self, agent_spec: AgentSpec) -> list[Tool]:
        """
        Create LangChain tools from agent spec.

        Args:
            agent_spec: Agent specification

        Returns:
            List of LangChain Tool instances
        """
        tools = []

        # Get tool specs from agent config
        tool_specs = agent_spec.config.get("tools", [])

        for tool_spec in tool_specs:
            if isinstance(tool_spec, str):
                # Simple tool name - create placeholder
                tool = Tool(
                    name=tool_spec,
                    func=lambda x: f"Tool {tool_spec} called with: {x}",
                    description=f"Tool: {tool_spec}",
                )
                tools.append(tool)
            elif isinstance(tool_spec, dict):
                # Detailed tool spec
                tool = Tool(
                    name=tool_spec.get("name", "unknown"),
                    func=tool_spec.get("func", lambda x: "Not implemented"),
                    description=tool_spec.get("description", ""),
                )
                tools.append(tool)

        return tools

    def _create_prompt(self, agent_spec: AgentSpec) -> PromptTemplate:
        """
        Create LangChain prompt from agent spec.

        Args:
            agent_spec: Agent specification

        Returns:
            PromptTemplate instance
        """
        # Use system prompt if available, otherwise default
        system_prompt = agent_spec.system_prompt or "You are a helpful AI assistant."

        # LangChain ReAct agent template
        template = f"""{system_prompt}

TOOLS:
------

You have access to the following tools:

{{tools}}

To use a tool, please use the following format:

```
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{{tool_names}}]
Action Input: the input to the action
Observation: the result of the action
```

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

```
Thought: Do I need to use a tool? No
Final Answer: [your response here]
```

Begin!

Previous conversation history:
{{chat_history}}

New input: {{input}}
{{agent_scratchpad}}
"""

        return PromptTemplate(
            template=template,
            input_variables=["input", "chat_history", "agent_scratchpad"],
            partial_variables={"tools": "", "tool_names": ""},
        )

    @property
    def framework_name(self) -> str:
        """Return framework identifier."""
        return "langchain"

    @property
    def supported_features(self) -> list[str]:
        """Return list of supported features."""
        return [
            "agents",
            "tools",
            "memory",
            "async",
            "streaming",
        ]

    def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate LangChain adapter configuration.

        Args:
            config: Configuration dictionary

        Returns:
            True if valid

        Raises:
            ValueError: If configuration is invalid
        """
        if "llm" in config and not isinstance(config["llm"], BaseLanguageModel):
            raise ValueError(
                "llm must be an instance of langchain BaseLanguageModel"
            )

        if "max_iterations" in config:
            max_iter = config["max_iterations"]
            if not isinstance(max_iter, int) or max_iter < 1:
                raise ValueError("max_iterations must be a positive integer")

        return True
