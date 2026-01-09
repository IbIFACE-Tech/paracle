"""CrewAI framework adapter.

Provides integration with CrewAI for role-based multi-agent teams.
Supports agents, tasks, crews, and hierarchical workflows.
"""

from typing import Any

# Try CrewAI imports
try:
    from crewai import Agent, Crew, Process, Task
    from crewai.tools import BaseTool as CrewAIBaseTool

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = None
    Task = None
    Crew = None

if not CREWAI_AVAILABLE:
    raise ImportError(
        "crewai package is required for CrewAI adapter. "
        "Install with: pip install crewai crewai-tools"
    )

from paracle_domain.models import AgentSpec, WorkflowSpec

from paracle_adapters.base import FrameworkAdapter
from paracle_adapters.exceptions import AdapterConfigurationError, AdapterExecutionError


class CrewAIAdapter(FrameworkAdapter):
    """
    CrewAI framework adapter.

    Integrates Paracle with CrewAI for role-based multi-agent teams.
    CrewAI excels at collaborative agent workflows where each agent
    has a specific role and goal.

    Features:
    - Agent creation with roles, goals, and backstories
    - Task creation and assignment
    - Crew orchestration (sequential or hierarchical)
    - Tool integration
    - Memory support

    Example:
        >>> adapter = CrewAIAdapter(model="gpt-4")
        >>> agent = await adapter.create_agent(agent_spec)
        >>> workflow = await adapter.create_workflow(workflow_spec)
        >>> result = await adapter.execute_workflow(workflow, {"topic": "AI"})
    """

    def __init__(self, model: str = "gpt-4", **config: Any):
        """
        Initialize CrewAI adapter.

        Args:
            model: LLM model name (default: gpt-4)
            **config: Additional configuration
                - verbose: Enable verbose output (default: False)
                - memory: Enable crew memory (default: True)
                - process: Process type - "sequential" or "hierarchical"
                - tools: Pre-configured CrewAI tools
        """
        super().__init__(**config)
        self.model = model
        self._tools_registry: dict[str, CrewAIBaseTool] = {}
        self._agents: dict[str, Agent] = {}

        # Register pre-configured tools
        if "tools" in config:
            for t in config["tools"]:
                if isinstance(t, CrewAIBaseTool):
                    self._tools_registry[t.name] = t

    async def create_agent(self, agent_spec: AgentSpec) -> Any:
        """
        Create a CrewAI Agent from Paracle AgentSpec.

        CrewAI agents have roles, goals, and backstories that define
        their behavior and expertise.

        Args:
            agent_spec: Paracle agent specification

        Returns:
            Dictionary containing CrewAI Agent and metadata

        Raises:
            AdapterExecutionError: If agent creation fails
        """
        try:
            # Extract CrewAI-specific config
            role = agent_spec.config.get(
                "role", agent_spec.name.replace("_", " ").title()
            )
            goal = agent_spec.config.get(
                "goal", agent_spec.system_prompt or f"Act as a {role}"
            )
            backstory = agent_spec.config.get(
                "backstory", f"You are an expert {role} with years of experience."
            )

            # Get tools for this agent
            tools = self._create_tools(agent_spec)

            # Create CrewAI agent
            agent = Agent(
                role=role,
                goal=goal,
                backstory=backstory,
                verbose=self.config.get("verbose", False),
                allow_delegation=agent_spec.config.get("allow_delegation", False),
                tools=tools,
                llm=self.model,
                memory=self.config.get("memory", True),
            )

            # Cache agent for crew assembly
            self._agents[agent_spec.name] = agent

            return {
                "type": "crewai_agent",
                "agent": agent,
                "role": role,
                "goal": goal,
                "tools": tools,
                "spec": agent_spec,
            }

        except Exception as e:
            if isinstance(e, AdapterConfigurationError | AdapterExecutionError):
                raise
            raise AdapterExecutionError(
                f"Failed to create CrewAI agent: {e}",
                framework="crewai",
                original_error=e,
            ) from e

    async def execute_agent(
        self,
        agent_instance: Any,
        input_data: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute a single CrewAI agent with a task.

        Note: CrewAI agents work best in crews. For single-agent execution,
        we create a minimal crew with one task.

        Args:
            agent_instance: Agent dict from create_agent()
            input_data: Input data with task description
            **kwargs: Additional execution parameters

        Returns:
            Result dictionary with "response" and "metadata"
        """
        try:
            agent = agent_instance["agent"]
            user_input = input_data.get("input") or input_data.get("prompt", "")

            # Create a single task for the agent
            task = Task(
                description=user_input,
                expected_output=input_data.get(
                    "expected_output", "A comprehensive response to the task."
                ),
                agent=agent,
            )

            # Create minimal crew
            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=self.config.get("verbose", False),
                process=Process.sequential,
            )

            # Execute crew
            result = crew.kickoff()

            return {
                "response": str(result),
                "metadata": {
                    "framework": "crewai",
                    "agent_type": "crewai_agent",
                    "role": agent_instance.get("role", "unknown"),
                    "execution_type": "single_agent",
                },
            }

        except Exception as e:
            raise AdapterExecutionError(
                f"Failed to execute CrewAI agent: {e}",
                framework="crewai",
                original_error=e,
            ) from e

    async def create_workflow(self, workflow_spec: WorkflowSpec) -> Any:
        """
        Create a CrewAI Crew from Paracle WorkflowSpec.

        Maps Paracle workflow steps to CrewAI tasks and assembles
        them into a crew.

        Args:
            workflow_spec: Paracle workflow specification

        Returns:
            Dictionary containing Crew and task configurations
        """
        try:
            agents = []
            tasks = []
            task_map = {}

            # Create tasks from workflow steps
            for step in workflow_spec.steps:
                # Get or create agent for this step
                agent_name = step.agent
                if agent_name in self._agents:
                    agent = self._agents[agent_name]
                else:
                    # Create a default agent
                    agent = Agent(
                        role=agent_name.replace("_", " ").title(),
                        goal=f"Complete the {step.name} task",
                        backstory=f"Expert in {step.name}",
                        verbose=self.config.get("verbose", False),
                        llm=self.model,
                    )
                    self._agents[agent_name] = agent

                if agent not in agents:
                    agents.append(agent)

                # Create task
                description = step.inputs.get(
                    "description", step.inputs.get("task", f"Execute: {step.name}")
                )
                expected_output = step.inputs.get(
                    "expected_output", f"Completed output for {step.name}"
                )

                # Handle dependencies - CrewAI uses context from previous tasks
                context_tasks = []
                for dep in step.depends_on or []:
                    if dep in task_map:
                        context_tasks.append(task_map[dep])

                task = Task(
                    description=description,
                    expected_output=expected_output,
                    agent=agent,
                    context=context_tasks if context_tasks else None,
                )

                tasks.append(task)
                task_map[step.id] = task

            # Determine process type
            process_type = self.config.get("process", "sequential")
            if process_type == "hierarchical":
                process = Process.hierarchical
            else:
                process = Process.sequential

            # Create crew
            crew = Crew(
                agents=agents,
                tasks=tasks,
                verbose=self.config.get("verbose", False),
                memory=self.config.get("memory", True),
                process=process,
            )

            return {
                "type": "crewai_crew",
                "crew": crew,
                "agents": agents,
                "tasks": tasks,
                "process": process_type,
                "spec": workflow_spec,
            }

        except Exception as e:
            raise AdapterExecutionError(
                f"Failed to create CrewAI workflow: {e}",
                framework="crewai",
                original_error=e,
            ) from e

    async def execute_workflow(
        self,
        workflow_instance: Any,
        inputs: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute a CrewAI Crew workflow.

        Args:
            workflow_instance: Workflow dict from create_workflow()
            inputs: Input data for the workflow
            **kwargs: Additional execution parameters

        Returns:
            Execution result dictionary
        """
        try:
            crew = workflow_instance["crew"]

            # Execute crew with inputs
            result = crew.kickoff(inputs=inputs)

            # Extract task results if available
            task_results = {}
            if hasattr(result, "tasks_output"):
                for i, task_output in enumerate(result.tasks_output):
                    task_results[f"task_{i}"] = str(task_output)

            return {
                "response": str(result),
                "metadata": {
                    "framework": "crewai",
                    "workflow_type": "crew",
                    "process": workflow_instance.get("process", "sequential"),
                    "agents_count": len(workflow_instance.get("agents", [])),
                    "tasks_count": len(workflow_instance.get("tasks", [])),
                    "task_results": task_results,
                },
            }

        except Exception as e:
            raise AdapterExecutionError(
                f"Failed to execute CrewAI workflow: {e}",
                framework="crewai",
                original_error=e,
            ) from e

    def _create_tools(self, agent_spec: AgentSpec) -> list:
        """Create CrewAI tools from agent spec."""
        tools = []

        tool_names = agent_spec.config.get("tools", [])

        for tool_item in tool_names:
            if isinstance(tool_item, str):
                # Check registry first
                if tool_item in self._tools_registry:
                    tools.append(self._tools_registry[tool_item])
                # Note: CrewAI doesn't support dynamic tool creation
                # like LangChain, so we skip unknown tools

            elif isinstance(tool_item, CrewAIBaseTool):
                tools.append(tool_item)

        return tools

    def register_tool(self, tool: CrewAIBaseTool) -> None:
        """Register a CrewAI tool for use in agents."""
        self._tools_registry[tool.name] = tool

    def get_cached_agent(self, name: str) -> Agent | None:
        """Get a cached agent by name."""
        return self._agents.get(name)

    def clear_agent_cache(self) -> None:
        """Clear the agent cache."""
        self._agents.clear()

    @property
    def framework_name(self) -> str:
        """Return framework identifier."""
        return "crewai"

    @property
    def supported_features(self) -> list[str]:
        """Return list of supported features."""
        return [
            "agents",
            "tools",
            "workflows",
            "crews",
            "memory",
            "delegation",
            "hierarchical_process",
            "sequential_process",
        ]

    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate CrewAI adapter configuration."""
        if "process" in config:
            valid_processes = ["sequential", "hierarchical"]
            if config["process"] not in valid_processes:
                raise ValueError(f"process must be one of: {valid_processes}")

        if "tools" in config:
            for t in config["tools"]:
                if not isinstance(t, CrewAIBaseTool):
                    raise ValueError("All tools must be CrewAI BaseTool instances")

        return True

    @staticmethod
    def get_version_info() -> dict[str, Any]:
        """Get CrewAI version information."""
        info = {
            "crewai_available": CREWAI_AVAILABLE,
        }

        if CREWAI_AVAILABLE:
            try:
                import crewai

                info["crewai_version"] = crewai.__version__
            except (ImportError, AttributeError):
                pass

        return info
