"""LlamaIndex framework adapter.

Provides integration with LlamaIndex for RAG-based agents and workflows.
Supports query engines, chat engines, and agent runners.
"""

from typing import Any

# Try LlamaIndex imports
try:
    from llama_index.core import (
        Settings,
        SimpleDirectoryReader,  # noqa: F401
        VectorStoreIndex,
    )
    from llama_index.core.agent import ReActAgent
    from llama_index.core.llms import LLM
    from llama_index.core.query_engine import BaseQueryEngine  # noqa: F401
    from llama_index.core.tools import FunctionTool, QueryEngineTool, ToolMetadata

    # BaseChatEngine may not be available in all versions
    try:
        from llama_index.core.chat_engine import BaseChatEngine
    except ImportError:
        BaseChatEngine = None

    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    LLM = None
    ReActAgent = None
    BaseChatEngine = None

if not LLAMAINDEX_AVAILABLE:
    raise ImportError(
        "llama-index packages are required for LlamaIndex adapter. "
        "Install with: pip install llama-index llama-index-llms-openai"
    )

from paracle_domain.models import AgentSpec, WorkflowSpec

from paracle_adapters.base import FrameworkAdapter
from paracle_adapters.exceptions import AdapterConfigurationError, AdapterExecutionError


class LlamaIndexAdapter(FrameworkAdapter):
    """
    LlamaIndex framework adapter.

    Integrates Paracle agents with LlamaIndex for RAG-based applications,
    query engines, and agentic workflows.

    Features:
    - ReAct agent creation from Paracle AgentSpec
    - Query engine integration
    - Tool creation and registration
    - Document indexing support
    - Chat engine support

    Example:
        >>> from llama_index.llms.openai import OpenAI
        >>> llm = OpenAI(model="gpt-4")
        >>> adapter = LlamaIndexAdapter(llm=llm)
        >>> agent = await adapter.create_agent(agent_spec)
        >>> result = await adapter.execute_agent(agent, {"input": "Hello"})
    """

    def __init__(self, llm: LLM | None = None, **config: Any):
        """
        Initialize LlamaIndex adapter.

        Args:
            llm: LlamaIndex LLM instance (e.g., OpenAI, Anthropic)
            **config: Additional configuration
                - embed_model: Embedding model for RAG
                - index: Pre-built VectorStoreIndex
                - verbose: Enable verbose output
                - tools: Pre-configured tools
        """
        super().__init__(**config)
        self.llm = llm
        self._tools_registry: dict[str, FunctionTool] = {}
        self._indexes: dict[str, VectorStoreIndex] = {}

        # Configure global settings if LLM provided
        if llm:
            Settings.llm = llm

        # Register pre-configured index
        if "index" in config:
            self._indexes["default"] = config["index"]

        # Register pre-configured tools
        if "tools" in config:
            for t in config["tools"]:
                if isinstance(t, FunctionTool | QueryEngineTool):
                    self._tools_registry[t.metadata.name] = t

    async def create_agent(self, agent_spec: AgentSpec) -> Any:
        """
        Create a LlamaIndex ReAct agent from Paracle AgentSpec.

        Args:
            agent_spec: Paracle agent specification

        Returns:
            Dictionary containing agent instance and metadata

        Raises:
            AdapterExecutionError: If agent creation fails
        """
        try:
            if self.llm is None:
                raise AdapterConfigurationError(
                    "LLM must be provided to create agents. "
                    "Pass llm parameter when initializing adapter.",
                    framework="llamaindex",
                )

            # Create tools from agent spec
            tools = self._create_tools(agent_spec)

            # Create system prompt
            system_prompt = (
                agent_spec.system_prompt or "You are a helpful AI assistant."
            )

            # Create ReAct agent (new API - direct constructor)
            agent = ReActAgent(
                name=agent_spec.name.replace("-", "_"),
                tools=tools,
                llm=self.llm,
                verbose=self.config.get("verbose", False),
                system_prompt=system_prompt,
            )

            return {
                "type": "react_agent",
                "agent": agent,
                "tools": tools,
                "system_prompt": system_prompt,
                "spec": agent_spec,
            }

        except Exception as e:
            if isinstance(e, AdapterConfigurationError | AdapterExecutionError):
                raise
            raise AdapterExecutionError(
                f"Failed to create LlamaIndex agent: {e}",
                framework="llamaindex",
                original_error=e,
            ) from e

    async def execute_agent(
        self,
        agent_instance: Any,
        input_data: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute a LlamaIndex agent.

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

            agent = agent_instance["agent"]

            # Execute agent (new API uses .run())
            if hasattr(agent, "run"):
                response = await agent.run(user_input)
            elif hasattr(agent, "achat"):
                response = await agent.achat(user_input)
            else:
                # Fallback to sync chat
                response = agent.chat(user_input)

            # Extract response text
            response_text = str(response)

            # Get sources if available
            sources = []
            if hasattr(response, "source_nodes"):
                for node in response.source_nodes:
                    sources.append(
                        {
                            "text": node.text[:200] if node.text else "",
                            "score": node.score if hasattr(node, "score") else None,
                        }
                    )

            return {
                "response": response_text,
                "metadata": {
                    "framework": "llamaindex",
                    "agent_type": agent_instance.get("type", "react_agent"),
                    "sources": sources,
                    "tools_used": self._get_tools_used(response),
                },
            }

        except Exception as e:
            raise AdapterExecutionError(
                f"Failed to execute LlamaIndex agent: {e}",
                framework="llamaindex",
                original_error=e,
            ) from e

    async def create_workflow(self, workflow_spec: WorkflowSpec) -> Any:
        """
        Create a LlamaIndex workflow from Paracle WorkflowSpec.

        LlamaIndex workflows are implemented as sequential agent pipelines
        where each step can be a query engine or agent.

        Args:
            workflow_spec: Paracle workflow specification

        Returns:
            Workflow dictionary with step configurations

        Raises:
            AdapterExecutionError: If workflow creation fails
        """
        try:
            workflow_steps = []

            for step in workflow_spec.steps:
                step_config = {
                    "id": step.id,
                    "name": step.name,
                    "agent_name": step.agent,
                    "inputs": step.inputs,
                    "depends_on": step.depends_on or [],
                }

                # Check if we have a query engine for this step
                index_name = step.inputs.get("index", "default")
                if index_name in self._indexes:
                    query_engine = self._indexes[index_name].as_query_engine()
                    step_config["query_engine"] = query_engine
                    step_config["type"] = "query"
                else:
                    step_config["type"] = "agent"

                workflow_steps.append(step_config)

            return {
                "type": "llamaindex_workflow",
                "steps": workflow_steps,
                "spec": workflow_spec,
            }

        except Exception as e:
            raise AdapterExecutionError(
                f"Failed to create LlamaIndex workflow: {e}",
                framework="llamaindex",
                original_error=e,
            ) from e

    async def execute_workflow(
        self,
        workflow_instance: Any,
        inputs: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute a LlamaIndex workflow.

        Args:
            workflow_instance: Workflow dict from create_workflow()
            inputs: Input data for the workflow
            **kwargs: Additional execution parameters

        Returns:
            Execution result dictionary
        """
        try:
            steps = workflow_instance["steps"]
            results = {}
            step_outputs = {}

            # Sort steps by dependencies (topological order)
            sorted_steps = self._topological_sort(steps)

            for step in sorted_steps:
                step_id = step["id"]

                # Gather inputs from dependencies
                step_input = dict(inputs)
                for dep in step.get("depends_on", []):
                    if dep in step_outputs:
                        step_input[f"result_{dep}"] = step_outputs[dep]

                # Execute step
                if step["type"] == "query" and "query_engine" in step:
                    query = step["inputs"].get("query", step_input.get("query", ""))
                    response = await step["query_engine"].aquery(query)
                    output = str(response)
                else:
                    # Use LLM directly for agent steps
                    prompt = step["inputs"].get("prompt", f"Execute: {step['name']}")
                    if self.llm:
                        response = await self.llm.acomplete(prompt)
                        output = str(response)
                    else:
                        output = f"Step {step_id} executed (no LLM)"

                step_outputs[step_id] = output
                results[step_id] = output

            return {
                "response": results,
                "metadata": {
                    "framework": "llamaindex",
                    "workflow_type": "pipeline",
                    "steps_executed": list(results.keys()),
                },
            }

        except Exception as e:
            raise AdapterExecutionError(
                f"Failed to execute LlamaIndex workflow: {e}",
                framework="llamaindex",
                original_error=e,
            ) from e

    def _create_tools(self, agent_spec: AgentSpec) -> list:
        """Create LlamaIndex tools from agent spec."""
        tools = []

        tool_names = agent_spec.config.get("tools", [])

        for tool_item in tool_names:
            if isinstance(tool_item, str):
                # Check registry first
                if tool_item in self._tools_registry:
                    tools.append(self._tools_registry[tool_item])
                else:
                    # Create placeholder tool
                    def placeholder_fn(query: str, name: str = tool_item) -> str:
                        return f"Tool '{name}' called with: {query}"

                    tool = FunctionTool.from_defaults(
                        fn=placeholder_fn,
                        name=tool_item,
                        description=f"Tool: {tool_item}",
                    )
                    tools.append(tool)

            elif isinstance(tool_item, dict):
                name = tool_item.get("name", "unknown")
                description = tool_item.get("description", f"Tool: {name}")
                func = tool_item.get("func")

                if func and callable(func):
                    tool = FunctionTool.from_defaults(
                        fn=func,
                        name=name,
                        description=description,
                    )
                    tools.append(tool)

            elif isinstance(tool_item, FunctionTool | QueryEngineTool):
                tools.append(tool_item)

        return tools

    def _get_tools_used(self, response: Any) -> list[str]:
        """Extract tool names used from response."""
        tools_used = []
        if hasattr(response, "sources"):
            for source in response.sources:
                if hasattr(source, "tool_name"):
                    tools_used.append(source.tool_name)
        return tools_used

    def _topological_sort(self, steps: list[dict]) -> list[dict]:
        """Sort steps in topological order based on dependencies."""
        from collections import deque

        # Build adjacency and in-degree
        in_degree = {s["id"]: 0 for s in steps}
        graph = {s["id"]: [] for s in steps}
        step_map = {s["id"]: s for s in steps}

        for step in steps:
            for dep in step.get("depends_on", []):
                if dep in graph:
                    graph[dep].append(step["id"])
                    in_degree[step["id"]] += 1

        # Kahn's algorithm
        queue = deque([sid for sid, deg in in_degree.items() if deg == 0])
        sorted_ids = []

        while queue:
            current = queue.popleft()
            sorted_ids.append(current)
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return [step_map[sid] for sid in sorted_ids]

    def register_index(self, name: str, index: VectorStoreIndex) -> None:
        """Register a vector store index for RAG operations."""
        self._indexes[name] = index

    def register_tool(self, tool: FunctionTool | QueryEngineTool) -> None:
        """Register a tool for use in agents."""
        self._tools_registry[tool.metadata.name] = tool

    def create_query_engine_tool(
        self,
        index: VectorStoreIndex,
        name: str,
        description: str,
    ) -> QueryEngineTool:
        """Create a query engine tool from an index."""
        query_engine = index.as_query_engine()
        tool = QueryEngineTool(
            query_engine=query_engine,
            metadata=ToolMetadata(
                name=name,
                description=description,
            ),
        )
        self._tools_registry[name] = tool
        return tool

    @property
    def framework_name(self) -> str:
        """Return framework identifier."""
        return "llamaindex"

    @property
    def supported_features(self) -> list[str]:
        """Return list of supported features."""
        return [
            "agents",
            "tools",
            "async",
            "rag",
            "query_engines",
            "chat_engines",
            "vector_stores",
            "workflows",
        ]

    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate LlamaIndex adapter configuration."""
        if "llm" in config and config["llm"] is not None:
            if not isinstance(config["llm"], LLM):
                raise ValueError("llm must be an instance of llama_index LLM")

        if "index" in config:
            if not isinstance(config["index"], VectorStoreIndex):
                raise ValueError("index must be a VectorStoreIndex instance")

        return True

    @staticmethod
    def get_version_info() -> dict[str, Any]:
        """Get LlamaIndex version information."""
        info = {
            "llamaindex_available": LLAMAINDEX_AVAILABLE,
        }

        if LLAMAINDEX_AVAILABLE:
            try:
                import llama_index.core

                info["llamaindex_version"] = llama_index.core.__version__
            except (ImportError, AttributeError):
                pass

        return info
