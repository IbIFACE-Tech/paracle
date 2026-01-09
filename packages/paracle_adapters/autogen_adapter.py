"""AutoGen framework adapter.

Provides integration with Microsoft AutoGen for conversational multi-agent systems.
Supports AssistantAgent, UserProxyAgent, GroupChat, and tool registration.
"""

from typing import Any

# Try AutoGen imports (supports both autogen and pyautogen packages)
try:
    # Try newer autogen-agentchat package first
    from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
    from autogen_agentchat.teams import RoundRobinGroupChat
    from autogen_core.models import ChatCompletionClient

    AUTOGEN_AVAILABLE = True
    AUTOGEN_VERSION = "0.4+"
except ImportError:
    try:
        # Fallback to legacy autogen/pyautogen
        from autogen import (  # noqa: F401
            AssistantAgent,
            GroupChat,
            GroupChatManager,
            UserProxyAgent,
        )

        AUTOGEN_AVAILABLE = True
        AUTOGEN_VERSION = "0.2.x"
        RoundRobinGroupChat = None
        ChatCompletionClient = None
    except ImportError:
        AUTOGEN_AVAILABLE = False
        AUTOGEN_VERSION = None
        AssistantAgent = None
        UserProxyAgent = None

if not AUTOGEN_AVAILABLE:
    raise ImportError(
        "autogen package is required for AutoGen adapter. "
        "Install with: pip install autogen-agentchat autogen-ext"
    )

from paracle_domain.models import AgentSpec, WorkflowSpec

from paracle_adapters.base import FrameworkAdapter
from paracle_adapters.exceptions import AdapterConfigurationError, AdapterExecutionError


class AutoGenAdapter(FrameworkAdapter):
    """
    AutoGen framework adapter.

    Integrates Paracle with Microsoft AutoGen for conversational
    multi-agent systems with automatic message routing.

    Features:
    - AssistantAgent and UserProxyAgent creation
    - GroupChat orchestration
    - Function/tool registration
    - Code execution support
    - Human-in-the-loop workflows

    Example:
        >>> config = {"model": "gpt-4", "api_key": "..."}
        >>> adapter = AutoGenAdapter(llm_config=config)
        >>> agent = await adapter.create_agent(agent_spec)
        >>> result = await adapter.execute_agent(agent, {"input": "Hello"})
    """

    def __init__(self, llm_config: dict[str, Any] | None = None, **config: Any):
        """
        Initialize AutoGen adapter.

        Args:
            llm_config: LLM configuration dict with model and API settings
            **config: Additional configuration
                - human_input_mode: "NEVER", "ALWAYS", or "TERMINATE"
                - code_execution_config: Config for code execution
                - max_consecutive_auto_reply: Max auto replies
                - tools: Pre-configured functions/tools
        """
        super().__init__(**config)
        self.llm_config = llm_config or self._get_default_llm_config()
        self._agents: dict[str, Any] = {}
        self._functions: dict[str, callable] = {}

        # Register pre-configured functions
        if "tools" in config:
            for name, func in config["tools"].items():
                if callable(func):
                    self._functions[name] = func

    def _get_default_llm_config(self) -> dict[str, Any]:
        """Get default LLM configuration."""
        import os

        return {
            "model": os.getenv("OPENAI_MODEL", "gpt-4"),
            "api_key": os.getenv("OPENAI_API_KEY"),
            "temperature": 0.7,
        }

    async def create_agent(self, agent_spec: AgentSpec) -> Any:
        """
        Create an AutoGen agent from Paracle AgentSpec.

        Creates either an AssistantAgent or UserProxyAgent based on
        the agent configuration.

        Args:
            agent_spec: Paracle agent specification

        Returns:
            Dictionary containing AutoGen agent and metadata
        """
        try:
            agent_type = agent_spec.config.get("agent_type", "assistant")
            # AutoGen requires valid Python identifiers for names
            name = agent_spec.name.replace("-", "_").replace(" ", "_")

            # Build system message
            system_message = (
                agent_spec.system_prompt or f"You are {name}, a helpful AI assistant."
            )

            # Get functions for this agent
            functions = self._get_agent_functions(agent_spec)

            if AUTOGEN_VERSION == "0.4+":
                # Modern AutoGen 0.4+ API
                agent = await self._create_agent_v04(
                    name=name,
                    agent_type=agent_type,
                    system_message=system_message,
                    functions=functions,
                    agent_spec=agent_spec,
                )
            else:
                # Legacy AutoGen 0.2.x API
                agent = self._create_agent_legacy(
                    name=name,
                    agent_type=agent_type,
                    system_message=system_message,
                    functions=functions,
                    agent_spec=agent_spec,
                )

            # Cache agent
            self._agents[name] = agent

            return {
                "type": f"autogen_{agent_type}",
                "agent": agent,
                "name": name,
                "system_message": system_message,
                "functions": list(functions.keys()),
                "spec": agent_spec,
            }

        except Exception as e:
            if isinstance(e, AdapterConfigurationError | AdapterExecutionError):
                raise
            raise AdapterExecutionError(
                f"Failed to create AutoGen agent: {e}",
                framework="autogen",
                original_error=e,
            ) from e

    async def _create_agent_v04(
        self,
        name: str,
        agent_type: str,
        system_message: str,
        functions: dict,
        agent_spec: AgentSpec,
    ) -> Any:
        """Create agent using AutoGen 0.4+ API."""
        from autogen_agentchat.agents import AssistantAgent

        # Create model client
        model_client = self._create_model_client()

        if agent_type == "user_proxy":
            # UserProxyAgent in 0.4+ is different
            agent = AssistantAgent(
                name=name,
                model_client=model_client,
                system_message=system_message,
            )
        else:
            agent = AssistantAgent(
                name=name,
                model_client=model_client,
                system_message=system_message,
                tools=list(functions.values()) if functions else None,
            )

        return agent

    def _create_agent_legacy(
        self,
        name: str,
        agent_type: str,
        system_message: str,
        functions: dict,
        agent_spec: AgentSpec,
    ) -> Any:
        """Create agent using legacy AutoGen 0.2.x API."""
        if agent_type == "user_proxy":
            agent = UserProxyAgent(
                name=name,
                system_message=system_message,
                human_input_mode=self.config.get("human_input_mode", "NEVER"),
                max_consecutive_auto_reply=self.config.get(
                    "max_consecutive_auto_reply", 10
                ),
                code_execution_config=self.config.get(
                    "code_execution_config",
                    {"work_dir": "workspace", "use_docker": False},
                ),
            )
        else:
            agent = AssistantAgent(
                name=name,
                system_message=system_message,
                llm_config=self.llm_config,
                function_map=functions if functions else None,
            )

        return agent

    def _create_model_client(self) -> Any:
        """Create model client for AutoGen 0.4+."""
        try:
            from autogen_ext.models.openai import OpenAIChatCompletionClient

            return OpenAIChatCompletionClient(
                model=self.llm_config.get("model", "gpt-4"),
                api_key=self.llm_config.get("api_key"),
            )
        except ImportError:
            raise AdapterConfigurationError(
                "autogen-ext package required for model client. "
                "Install with: pip install autogen-ext[openai]",
                framework="autogen",
            )

    async def execute_agent(
        self,
        agent_instance: Any,
        input_data: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute an AutoGen agent.

        For single agent execution, creates a temporary conversation
        with a user proxy.

        Args:
            agent_instance: Agent dict from create_agent()
            input_data: Input data with message
            **kwargs: Additional execution parameters

        Returns:
            Result dictionary with "response" and "metadata"
        """
        try:
            agent = agent_instance["agent"]
            user_input = input_data.get("input") or input_data.get("prompt", "")

            if AUTOGEN_VERSION == "0.4+":
                result = await self._execute_agent_v04(agent, user_input, kwargs)
            else:
                result = await self._execute_agent_legacy(agent, user_input, kwargs)

            return result

        except Exception as e:
            raise AdapterExecutionError(
                f"Failed to execute AutoGen agent: {e}",
                framework="autogen",
                original_error=e,
            ) from e

    async def _execute_agent_v04(
        self, agent: Any, message: str, kwargs: dict
    ) -> dict[str, Any]:
        """Execute using AutoGen 0.4+ API."""
        from autogen_agentchat.base import Response
        from autogen_core import CancellationToken

        # Run agent with message
        response = await agent.run(
            task=message,
            cancellation_token=CancellationToken(),
        )

        # Extract response
        if isinstance(response, Response):
            response_text = response.chat_message.content
        else:
            response_text = str(response)

        return {
            "response": response_text,
            "metadata": {
                "framework": "autogen",
                "agent_type": "assistant",
                "version": "0.4+",
            },
        }

    async def _execute_agent_legacy(
        self, agent: Any, message: str, kwargs: dict
    ) -> dict[str, Any]:
        """Execute using legacy AutoGen 0.2.x API."""
        # Create temporary user proxy for conversation
        user_proxy = UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
            code_execution_config=False,
        )

        # Initiate chat
        await user_proxy.a_initiate_chat(
            agent,
            message=message,
            max_turns=kwargs.get("max_turns", 2),
        )

        # Get last message from agent
        last_message = agent.last_message(user_proxy)
        response_text = last_message.get("content", "") if last_message else ""

        return {
            "response": response_text,
            "metadata": {
                "framework": "autogen",
                "agent_type": "assistant",
                "version": "0.2.x",
            },
        }

    async def create_workflow(self, workflow_spec: WorkflowSpec) -> Any:
        """
        Create an AutoGen GroupChat workflow from Paracle WorkflowSpec.

        Maps workflow steps to agents in a group chat configuration.

        Args:
            workflow_spec: Paracle workflow specification

        Returns:
            Dictionary containing GroupChat and agents
        """
        try:
            agents = []

            # Create agents for each step
            for step in workflow_spec.steps:
                agent_name = step.agent
                if agent_name in self._agents:
                    agents.append(self._agents[agent_name])
                else:
                    # Create default agent for step
                    agent_spec = AgentSpec(
                        name=agent_name,
                        model=self.llm_config.get("model", "gpt-4"),
                        provider="openai",
                        system_prompt=step.inputs.get(
                            "system_prompt",
                            f"You are {agent_name}, responsible for {step.name}",
                        ),
                    )
                    agent_result = await self.create_agent(agent_spec)
                    agents.append(agent_result["agent"])

            if AUTOGEN_VERSION == "0.4+":
                workflow = await self._create_workflow_v04(agents, workflow_spec)
            else:
                workflow = self._create_workflow_legacy(agents, workflow_spec)

            return workflow

        except Exception as e:
            raise AdapterExecutionError(
                f"Failed to create AutoGen workflow: {e}",
                framework="autogen",
                original_error=e,
            ) from e

    async def _create_workflow_v04(
        self, agents: list, workflow_spec: WorkflowSpec
    ) -> dict[str, Any]:
        """Create workflow using AutoGen 0.4+ API."""
        from autogen_agentchat.teams import RoundRobinGroupChat

        team = RoundRobinGroupChat(
            participants=agents,
            max_turns=self.config.get("max_turns", 10),
        )

        return {
            "type": "autogen_team",
            "team": team,
            "agents": agents,
            "spec": workflow_spec,
        }

    def _create_workflow_legacy(
        self, agents: list, workflow_spec: WorkflowSpec
    ) -> dict[str, Any]:
        """Create workflow using legacy AutoGen 0.2.x API."""
        from autogen import GroupChat, GroupChatManager

        groupchat = GroupChat(
            agents=agents,
            messages=[],
            max_round=self.config.get("max_rounds", 10),
        )

        manager = GroupChatManager(
            groupchat=groupchat,
            llm_config=self.llm_config,
        )

        return {
            "type": "autogen_groupchat",
            "groupchat": groupchat,
            "manager": manager,
            "agents": agents,
            "spec": workflow_spec,
        }

    async def execute_workflow(
        self,
        workflow_instance: Any,
        inputs: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute an AutoGen workflow (GroupChat).

        Args:
            workflow_instance: Workflow dict from create_workflow()
            inputs: Input data with initial message
            **kwargs: Additional execution parameters

        Returns:
            Execution result dictionary
        """
        try:
            initial_message = inputs.get("message") or inputs.get("input", "")

            if workflow_instance["type"] == "autogen_team":
                result = await self._execute_workflow_v04(
                    workflow_instance, initial_message, kwargs
                )
            else:
                result = await self._execute_workflow_legacy(
                    workflow_instance, initial_message, kwargs
                )

            return result

        except Exception as e:
            raise AdapterExecutionError(
                f"Failed to execute AutoGen workflow: {e}",
                framework="autogen",
                original_error=e,
            ) from e

    async def _execute_workflow_v04(
        self, workflow: dict, message: str, kwargs: dict
    ) -> dict[str, Any]:
        """Execute workflow using AutoGen 0.4+ API."""
        from autogen_core import CancellationToken

        team = workflow["team"]

        result = await team.run(
            task=message,
            cancellation_token=CancellationToken(),
        )

        return {
            "response": str(result),
            "metadata": {
                "framework": "autogen",
                "workflow_type": "team",
                "version": "0.4+",
                "agents_count": len(workflow.get("agents", [])),
            },
        }

    async def _execute_workflow_legacy(
        self, workflow: dict, message: str, kwargs: dict
    ) -> dict[str, Any]:
        """Execute workflow using legacy AutoGen 0.2.x API."""
        manager = workflow["manager"]
        agents = workflow["agents"]

        # Use first agent as initiator
        if agents:
            initiator = agents[0]
            await initiator.a_initiate_chat(
                manager,
                message=message,
            )

        # Get conversation history
        messages = workflow["groupchat"].messages
        response = messages[-1]["content"] if messages else ""

        return {
            "response": response,
            "metadata": {
                "framework": "autogen",
                "workflow_type": "groupchat",
                "version": "0.2.x",
                "agents_count": len(agents),
                "messages_count": len(messages),
            },
        }

    def _get_agent_functions(self, agent_spec: AgentSpec) -> dict[str, callable]:
        """Get functions for agent from spec and registry."""
        functions = {}

        tool_names = agent_spec.config.get("tools", [])

        for tool_name in tool_names:
            if isinstance(tool_name, str) and tool_name in self._functions:
                functions[tool_name] = self._functions[tool_name]

        return functions

    def register_function(self, name: str, func: callable) -> None:
        """Register a function for use in agents."""
        self._functions[name] = func

    @property
    def framework_name(self) -> str:
        """Return framework identifier."""
        return "autogen"

    @property
    def supported_features(self) -> list[str]:
        """Return list of supported features."""
        return [
            "agents",
            "tools",
            "workflows",
            "group_chat",
            "code_execution",
            "human_in_loop",
            "async",
        ]

    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate AutoGen adapter configuration."""
        if "human_input_mode" in config:
            valid_modes = ["NEVER", "ALWAYS", "TERMINATE"]
            if config["human_input_mode"] not in valid_modes:
                raise ValueError(f"human_input_mode must be one of: {valid_modes}")

        return True

    @staticmethod
    def get_version_info() -> dict[str, Any]:
        """Get AutoGen version information."""
        info = {
            "autogen_available": AUTOGEN_AVAILABLE,
            "autogen_version": AUTOGEN_VERSION,
        }

        if AUTOGEN_AVAILABLE:
            try:
                if AUTOGEN_VERSION == "0.4+":
                    import autogen_agentchat

                    info["package_version"] = autogen_agentchat.__version__
                else:
                    import autogen

                    info["package_version"] = autogen.__version__
            except (ImportError, AttributeError):
                pass

        return info
