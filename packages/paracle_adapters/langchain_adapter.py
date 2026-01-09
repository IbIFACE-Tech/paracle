"""LangChain framework adapter.

Updated for LangChain 1.x / LangGraph compatibility.
Supports both legacy LangChain agents and modern LangGraph agents.
"""

from collections.abc import Callable
from typing import Any

# Try modern imports first (LangChain 1.x + LangGraph)
try:
    from langchain_core.language_models import BaseChatModel
    from langchain_core.messages import (  # noqa: F401
        AIMessage,
        HumanMessage,
        SystemMessage,
    )
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.tools import BaseTool, tool

    LANGCHAIN_AVAILABLE = True
    LANGCHAIN_VERSION = "1.x"
except ImportError:
    LANGCHAIN_AVAILABLE = False
    LANGCHAIN_VERSION = None
    BaseChatModel = None

# Try LangGraph for modern agent support
try:
    from langgraph.graph import StateGraph  # noqa: F401
    from langgraph.prebuilt import create_react_agent

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    create_react_agent = None

if not LANGCHAIN_AVAILABLE:
    raise ImportError(
        "langchain packages are required for LangChain adapter. "
        "Install with: pip install langchain-core langchain-openai langgraph"
    )

from paracle_domain.models import AgentSpec, WorkflowSpec

from paracle_adapters.base import FrameworkAdapter
from paracle_adapters.exceptions import (
    AdapterConfigurationError,
    AdapterExecutionError,
    FeatureNotSupportedError,
)


class LangChainAdapter(FrameworkAdapter):
    """
    LangChain framework adapter.

    Integrates Paracle agents with the LangChain ecosystem,
    supporting both LangChain 1.x and LangGraph for modern agent patterns.

    Features:
    - Agent creation from Paracle AgentSpec
    - Tool integration
    - Chat model support (OpenAI, Anthropic, etc.)
    - LangGraph ReAct agents (recommended)
    - Legacy chain support

    Example:
        >>> from langchain_openai import ChatOpenAI
        >>> llm = ChatOpenAI(model="gpt-4")
        >>> adapter = LangChainAdapter(llm=llm)
        >>> agent = await adapter.create_agent(agent_spec)
        >>> result = await adapter.execute_agent(agent, {"input": "Hello"})
    """

    def __init__(self, llm: BaseChatModel | None = None, **config: Any):
        """
        Initialize LangChain adapter.

        Args:
            llm: LangChain chat model instance (e.g., ChatOpenAI, ChatAnthropic)
            **config: Additional configuration
                - use_langgraph: bool - Use LangGraph agents (default: True if available)
                - verbose: bool - Enable verbose output
                - max_iterations: int - Max agent iterations (default: 15)
                - tools: list - Pre-configured LangChain tools
        """
        super().__init__(**config)
        self.llm = llm
        self.use_langgraph = config.get("use_langgraph", LANGGRAPH_AVAILABLE)
        self._tools_registry: dict[str, BaseTool] = {}

        # Register any pre-configured tools
        if "tools" in config:
            for t in config["tools"]:
                if isinstance(t, BaseTool):
                    self._tools_registry[t.name] = t

    async def create_agent(self, agent_spec: AgentSpec) -> Any:
        """
        Create a LangChain/LangGraph agent from Paracle AgentSpec.

        Args:
            agent_spec: Paracle agent specification

        Returns:
            LangGraph agent (if available) or LangChain runnable

        Raises:
            AdapterExecutionError: If agent creation fails
        """
        try:
            if self.llm is None:
                raise AdapterConfigurationError(
                    "LLM must be provided to create agents. "
                    "Pass llm parameter when initializing adapter.",
                    framework="langchain",
                )

            # Create tools from agent spec
            tools = self._create_tools(agent_spec)

            # Create system message from spec
            system_message = (
                agent_spec.system_prompt or "You are a helpful AI assistant."
            )

            if self.use_langgraph and LANGGRAPH_AVAILABLE:
                # Modern LangGraph ReAct agent
                agent = create_react_agent(
                    model=self.llm,
                    tools=tools,
                    prompt=system_message,
                )
                return {
                    "type": "langgraph",
                    "agent": agent,
                    "tools": tools,
                    "system_message": system_message,
                    "spec": agent_spec,
                }
            else:
                # Fallback: Simple LLM chain without ReAct
                prompt = ChatPromptTemplate.from_messages(
                    [
                        ("system", system_message),
                        MessagesPlaceholder(variable_name="messages"),
                    ]
                )
                chain = prompt | self.llm
                return {
                    "type": "chain",
                    "chain": chain,
                    "tools": tools,
                    "system_message": system_message,
                    "spec": agent_spec,
                }

        except Exception as e:
            if isinstance(e, AdapterConfigurationError | AdapterExecutionError):
                raise
            raise AdapterExecutionError(
                f"Failed to create LangChain agent: {e}",
                framework="langchain",
                original_error=e,
            ) from e

    async def execute_agent(
        self,
        agent_instance: Any,
        input_data: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute a LangChain/LangGraph agent.

        Args:
            agent_instance: Agent dict from create_agent()
            input_data: Input data with "input" or "prompt" key
            **kwargs: Additional execution parameters

        Returns:
            Result dictionary with "response" and "metadata"

        Raises:
            AdapterExecutionError: If execution fails
        """
        try:
            # Normalize input
            user_input = input_data.get("input") or input_data.get("prompt", "")

            agent_type = agent_instance.get("type", "chain")

            if agent_type == "langgraph":
                # Execute LangGraph agent
                agent = agent_instance["agent"]
                result = await agent.ainvoke(
                    {"messages": [HumanMessage(content=user_input)]},
                    **kwargs,
                )

                # Extract final response from messages
                messages = result.get("messages", [])
                response = ""
                tool_calls = []

                for msg in messages:
                    if isinstance(msg, AIMessage):
                        if msg.content:
                            response = msg.content
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            tool_calls.extend(msg.tool_calls)

                model_str = str(self.llm) if self.llm else "unknown"
                return {
                    "response": response,
                    "metadata": {
                        "framework": "langchain",
                        "agent_type": "langgraph_react",
                        "messages_count": len(messages),
                        "tool_calls": tool_calls,
                        "model": model_str,
                    },
                }
            else:
                # Execute simple chain
                chain = agent_instance["chain"]
                result = await chain.ainvoke(
                    {"messages": [HumanMessage(content=user_input)]},
                    **kwargs,
                )

                if hasattr(result, "content"):
                    response = result.content
                else:
                    response = str(result)

                model_str = str(self.llm) if self.llm else "unknown"
                return {
                    "response": response,
                    "metadata": {
                        "framework": "langchain",
                        "agent_type": "chain",
                        "model": model_str,
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
        Create a LangGraph workflow from Paracle WorkflowSpec.

        Args:
            workflow_spec: Paracle workflow specification

        Returns:
            LangGraph StateGraph workflow

        Raises:
            FeatureNotSupportedError: If LangGraph not available
        """
        if not LANGGRAPH_AVAILABLE:
            raise FeatureNotSupportedError(
                "langchain",
                "workflows",
                "LangGraph is required for workflow support. Install with: pip install langgraph",
            )

        try:
            from operator import add
            from typing import Annotated, TypedDict

            from langgraph.graph import END, StateGraph

            # Define state schema
            class WorkflowState(TypedDict):
                messages: Annotated[list, add]
                current_step: str
                results: dict

            # Create graph
            graph = StateGraph(WorkflowState)

            # Add nodes for each step
            for step in workflow_spec.steps:
                node_name = step.id

                async def step_node(
                    state: WorkflowState, step_id=step.id, step_spec=step
                ):
                    # Execute step using LLM
                    if self.llm:
                        default_prompt = f"Execute step: {step_spec.name}"
                        prompt = step_spec.inputs.get("prompt", default_prompt)
                        result = await self.llm.ainvoke([HumanMessage(content=prompt)])
                        return {
                            "results": {step_id: result.content},
                            "current_step": step_id,
                        }
                    return {"results": {step_id: "No LLM configured"}}

                graph.add_node(node_name, step_node)

            # Add edges based on dependencies
            entry_point = None
            for step in workflow_spec.steps:
                if not step.depends_on:
                    if entry_point is None:
                        entry_point = step.id
                        graph.set_entry_point(step.id)
                else:
                    for dep in step.depends_on:
                        graph.add_edge(dep, step.id)

            # Find terminal nodes and connect to END
            terminal_nodes = {s.id for s in workflow_spec.steps}
            for step in workflow_spec.steps:
                for dep in step.depends_on or []:
                    terminal_nodes.discard(dep)

            for terminal in terminal_nodes:
                graph.add_edge(terminal, END)

            # Compile graph
            compiled = graph.compile()

            return {
                "type": "langgraph_workflow",
                "graph": compiled,
                "spec": workflow_spec,
            }

        except Exception as e:
            raise AdapterExecutionError(
                f"Failed to create LangGraph workflow: {e}",
                framework="langchain",
                original_error=e,
            ) from e

    async def execute_workflow(
        self,
        workflow_instance: Any,
        inputs: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute a LangGraph workflow.

        Args:
            workflow_instance: Workflow dict from create_workflow()
            inputs: Input data for the workflow
            **kwargs: Additional execution parameters

        Returns:
            Execution result dictionary
        """
        if not LANGGRAPH_AVAILABLE:
            raise FeatureNotSupportedError(
                "langchain",
                "workflows",
                "LangGraph is required for workflow execution.",
            )

        try:
            graph = workflow_instance["graph"]

            # Initialize state
            initial_state = {
                "messages": [],
                "current_step": "",
                "results": {},
                **inputs,
            }

            # Execute workflow
            final_state = await graph.ainvoke(initial_state, **kwargs)

            return {
                "response": final_state.get("results", {}),
                "metadata": {
                    "framework": "langchain",
                    "workflow_type": "langgraph",
                    "steps_executed": list(final_state.get("results", {}).keys()),
                },
            }

        except Exception as e:
            raise AdapterExecutionError(
                f"Failed to execute LangGraph workflow: {e}",
                framework="langchain",
                original_error=e,
            ) from e

    def _create_tools(self, agent_spec: AgentSpec) -> list[BaseTool]:
        """
        Create LangChain tools from agent spec.

        Args:
            agent_spec: Agent specification

        Returns:
            List of LangChain BaseTool instances
        """
        tools = []

        # Get tool names from agent config
        tool_names = agent_spec.config.get("tools", [])

        for tool_item in tool_names:
            if isinstance(tool_item, str):
                # Check if tool is in registry
                if tool_item in self._tools_registry:
                    tools.append(self._tools_registry[tool_item])
                else:
                    # Create a placeholder tool
                    @tool
                    def placeholder_tool(query: str, tool_name: str = tool_item) -> str:
                        """Placeholder tool that echoes input."""
                        return f"Tool '{tool_name}' called with: {query}"

                    placeholder_tool.name = tool_item
                    placeholder_tool.description = f"Tool: {tool_item}"
                    tools.append(placeholder_tool)

            elif isinstance(tool_item, dict):
                # Create tool from dict spec
                name = tool_item.get("name", "unknown")
                description = tool_item.get("description", f"Tool: {name}")
                func = tool_item.get("func")

                if func and callable(func):

                    @tool
                    def custom_tool(query: str, fn: Callable = func) -> str:
                        """Custom tool wrapper."""
                        return fn(query)

                    custom_tool.name = name
                    custom_tool.description = description
                    tools.append(custom_tool)

            elif isinstance(tool_item, BaseTool):
                tools.append(tool_item)

        return tools

    def register_tool(self, tool_instance: BaseTool) -> None:
        """
        Register a LangChain tool for use in agents.

        Args:
            tool_instance: LangChain BaseTool instance
        """
        self._tools_registry[tool_instance.name] = tool_instance

    @property
    def framework_name(self) -> str:
        """Return framework identifier."""
        return "langchain"

    @property
    def supported_features(self) -> list[str]:
        """Return list of supported features."""
        features = [
            "agents",
            "tools",
            "async",
            "chat_models",
        ]

        if LANGGRAPH_AVAILABLE:
            features.extend(
                [
                    "workflows",
                    "react_agents",
                    "state_graphs",
                ]
            )

        return features

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
        if "llm" in config:
            if not isinstance(config["llm"], BaseChatModel):
                raise ValueError(
                    "llm must be an instance of langchain BaseChatModel "
                    "(e.g., ChatOpenAI, ChatAnthropic)"
                )

        if "max_iterations" in config:
            max_iter = config["max_iterations"]
            if not isinstance(max_iter, int) or max_iter < 1:
                raise ValueError("max_iterations must be a positive integer")

        if "tools" in config:
            for t in config["tools"]:
                if not isinstance(t, BaseTool):
                    raise ValueError("All tools must be BaseTool instances")

        return True

    @staticmethod
    def get_version_info() -> dict[str, Any]:
        """Get LangChain version information."""
        info = {
            "langchain_available": LANGCHAIN_AVAILABLE,
            "langchain_version": LANGCHAIN_VERSION,
            "langgraph_available": LANGGRAPH_AVAILABLE,
        }

        if LANGCHAIN_AVAILABLE:
            try:
                import langchain_core

                info["langchain_core_version"] = langchain_core.__version__
            except (ImportError, AttributeError):
                pass

        if LANGGRAPH_AVAILABLE:
            try:
                import langgraph

                info["langgraph_version"] = langgraph.__version__
            except (ImportError, AttributeError):
                pass

        return info
