"""Autonomous agent spawner capability for MetaAgent.

Enables the MetaAgent to dynamically spawn specialized agents
for specific tasks or when under high load.
"""

import asyncio
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)


class AgentStatus(str, Enum):
    """Spawned agent status."""

    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    IDLE = "idle"
    TERMINATED = "terminated"
    ERROR = "error"


class AgentType(str, Enum):
    """Types of agents that can be spawned."""

    RESEARCHER = "researcher"
    CODER = "coder"
    REVIEWER = "reviewer"
    TESTER = "tester"
    DOCUMENTER = "documenter"
    ANALYST = "analyst"
    GENERAL = "general"


class SpawnConfig(CapabilityConfig):
    """Configuration for agent spawner capability."""

    max_spawned_agents: int = Field(
        default=10, ge=1, le=50, description="Max number of spawned agents"
    )
    agent_idle_timeout: float = Field(
        default=300.0, ge=60.0, le=3600.0, description="Idle timeout before termination"
    )
    auto_scale: bool = Field(
        default=True, description="Enable auto-scaling based on load"
    )
    scale_up_threshold: float = Field(
        default=0.8, ge=0.5, le=1.0, description="Load threshold to spawn new agents"
    )
    scale_down_threshold: float = Field(
        default=0.2, ge=0.0, le=0.5, description="Load threshold to terminate agents"
    )
    min_agents: int = Field(
        default=0, ge=0, le=10, description="Minimum number of spawned agents"
    )
    default_model: str = Field(
        default="anthropic/claude-sonnet-4-20250514",
        description="Default LLM model for spawned agents",
    )


class SpawnedAgent(BaseModel):
    """A dynamically spawned agent."""

    id: str = Field(default_factory=lambda: f"agent_{uuid.uuid4().hex[:8]}")
    name: str
    agent_type: AgentType
    status: AgentStatus = AgentStatus.INITIALIZING
    model: str = "anthropic/claude-sonnet-4-20250514"
    system_prompt: str = ""
    capabilities: list[str] = Field(default_factory=list)
    current_task: str | None = None
    tasks_completed: int = 0
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_available(self) -> bool:
        """Check if agent is available for tasks."""
        return self.status in (AgentStatus.READY, AgentStatus.IDLE)

    @property
    def idle_seconds(self) -> float:
        """Get seconds since last activity."""
        return (datetime.utcnow() - self.last_active_at).total_seconds()


class AgentPool:
    """Pool of spawned agents with auto-scaling."""

    def __init__(self, config: SpawnConfig):
        self.config = config
        self.agents: dict[str, SpawnedAgent] = {}
        self._lock = asyncio.Lock()

    @property
    def total_agents(self) -> int:
        """Total number of agents."""
        return len(self.agents)

    @property
    def available_agents(self) -> int:
        """Number of available agents."""
        return sum(1 for a in self.agents.values() if a.is_available)

    @property
    def busy_agents(self) -> int:
        """Number of busy agents."""
        return sum(1 for a in self.agents.values() if a.status == AgentStatus.BUSY)

    @property
    def load(self) -> float:
        """Current load ratio (0-1)."""
        if self.total_agents == 0:
            return 1.0  # No agents = full load
        return self.busy_agents / self.total_agents

    async def add_agent(self, agent: SpawnedAgent) -> None:
        """Add an agent to the pool."""
        async with self._lock:
            self.agents[agent.id] = agent

    async def remove_agent(self, agent_id: str) -> SpawnedAgent | None:
        """Remove an agent from the pool."""
        async with self._lock:
            return self.agents.pop(agent_id, None)

    async def get_available_agent(
        self,
        agent_type: AgentType | None = None,
    ) -> SpawnedAgent | None:
        """Get an available agent, optionally of a specific type."""
        async with self._lock:
            for agent in self.agents.values():
                if not agent.is_available:
                    continue
                if agent_type and agent.agent_type != agent_type:
                    continue
                return agent
        return None

    def get_idle_agents(self, idle_threshold: float) -> list[SpawnedAgent]:
        """Get agents that have been idle too long."""
        return [
            a
            for a in self.agents.values()
            if a.status == AgentStatus.IDLE and a.idle_seconds > idle_threshold
        ]


class AgentSpawner(BaseCapability):
    """Autonomous agent spawner capability for MetaAgent.

    Enables dynamic spawning of specialized agents based on:
    - Task requirements (spawn specialist for specific work)
    - Load balancing (spawn when overloaded)
    - Auto-scaling (maintain optimal agent pool)

    Example:
        >>> spawner = AgentSpawner()
        >>> await spawner.initialize()
        >>>
        >>> # Spawn a specialized agent
        >>> result = await spawner.execute(
        ...     action="spawn",
        ...     name="CodeReviewer",
        ...     agent_type="reviewer",
        ...     capabilities=["code_review", "security_audit"]
        ... )
        >>> agent_id = result.output["id"]
        >>>
        >>> # Assign a task to the agent
        >>> result = await spawner.execute(
        ...     action="assign_task",
        ...     agent_id=agent_id,
        ...     task="Review PR #123 for security issues"
        ... )
        >>>
        >>> # Check pool status
        >>> result = await spawner.execute(action="pool_status")
        >>> print(f"Load: {result.output['load']:.1%}")
    """

    name = "agent_spawner"
    description = "Dynamically spawn specialized agents for tasks or high load"

    # Default system prompts for agent types
    DEFAULT_PROMPTS: dict[AgentType, str] = {
        AgentType.RESEARCHER: (
            "You are a research specialist. Your role is to gather, analyze, "
            "and synthesize information from various sources. Provide thorough, "
            "well-sourced research with clear citations."
        ),
        AgentType.CODER: (
            "You are an expert software developer. Write clean, efficient, "
            "well-documented code following best practices. Consider edge cases "
            "and maintain high code quality standards."
        ),
        AgentType.REVIEWER: (
            "You are a code reviewer. Analyze code for quality, security, "
            "performance, and adherence to best practices. Provide constructive, "
            "actionable feedback."
        ),
        AgentType.TESTER: (
            "You are a testing specialist. Design comprehensive test cases, "
            "identify edge cases, and ensure thorough coverage. Focus on both "
            "functionality and reliability."
        ),
        AgentType.DOCUMENTER: (
            "You are a documentation specialist. Write clear, comprehensive "
            "documentation including tutorials, API references, and guides. "
            "Make complex topics accessible."
        ),
        AgentType.ANALYST: (
            "You are an analyst. Examine data, identify patterns, and provide "
            "insights. Present findings clearly with supporting evidence."
        ),
        AgentType.GENERAL: (
            "You are a helpful assistant capable of handling various tasks. "
            "Adapt your approach based on the specific requirements of each task."
        ),
    }

    def __init__(self, config: SpawnConfig | None = None):
        """Initialize agent spawner capability.

        Args:
            config: Spawner configuration
        """
        super().__init__(config or SpawnConfig())
        self.config: SpawnConfig = self.config
        self._pool: AgentPool | None = None
        self._auto_scale_task: asyncio.Task | None = None

    async def initialize(self) -> None:
        """Initialize agent spawner."""
        self._pool = AgentPool(self.config)

        # Start auto-scaling if enabled
        if self.config.auto_scale:
            self._auto_scale_task = asyncio.create_task(self._auto_scale_loop())

        await super().initialize()

    async def shutdown(self) -> None:
        """Shutdown agent spawner and terminate all agents."""
        # Stop auto-scaling
        if self._auto_scale_task:
            self._auto_scale_task.cancel()
            try:
                await self._auto_scale_task
            except asyncio.CancelledError:
                pass

        # Terminate all agents
        if self._pool:
            for agent_id in list(self._pool.agents.keys()):
                await self._terminate_agent(agent_id)

        await super().shutdown()

    async def _auto_scale_loop(self) -> None:
        """Background loop for auto-scaling."""
        while True:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds

                if not self._pool:
                    continue

                # Scale up if load is high
                if (
                    self._pool.load > self.config.scale_up_threshold
                    and self._pool.total_agents < self.config.max_spawned_agents
                ):
                    await self._spawn_agent(
                        name=f"AutoScaled_{self._pool.total_agents + 1}",
                        agent_type=AgentType.GENERAL,
                    )

                # Scale down if load is low
                elif (
                    self._pool.load < self.config.scale_down_threshold
                    and self._pool.total_agents > self.config.min_agents
                ):
                    idle_agents = self._pool.get_idle_agents(
                        self.config.agent_idle_timeout
                    )
                    if idle_agents:
                        await self._terminate_agent(idle_agents[0].id)

            except asyncio.CancelledError:
                break
            except Exception:
                # Log error but continue loop
                pass

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute agent spawner capability.

        Args:
            action: Action to perform
            **kwargs: Action-specific parameters

        Returns:
            CapabilityResult with spawner operation outcome
        """
        if not self._initialized:
            await self.initialize()

        action = kwargs.pop("action", "pool_status")
        start_time = time.time()

        try:
            if action == "spawn":
                result = await self._spawn_agent(**kwargs)
            elif action == "terminate":
                result = await self._terminate_agent(**kwargs)
            elif action == "assign_task":
                result = await self._assign_task(**kwargs)
            elif action == "complete_task":
                result = await self._complete_task(**kwargs)
            elif action == "get_agent":
                result = await self._get_agent(**kwargs)
            elif action == "list_agents":
                result = await self._list_agents(**kwargs)
            elif action == "pool_status":
                result = await self._pool_status(**kwargs)
            elif action == "get_available":
                result = await self._get_available_agent(**kwargs)
            else:
                return CapabilityResult.error_result(
                    capability=self.name,
                    error=f"Unknown action: {action}",
                )

            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.success_result(
                capability=self.name,
                output=result,
                duration_ms=duration_ms,
                action=action,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.error_result(
                capability=self.name,
                error=str(e),
                duration_ms=duration_ms,
                action=action,
            )

    async def _spawn_agent(
        self,
        name: str,
        agent_type: str | AgentType = AgentType.GENERAL,
        model: str | None = None,
        system_prompt: str | None = None,
        capabilities: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Spawn a new agent.

        Args:
            name: Agent name
            agent_type: Type of agent
            model: LLM model to use
            system_prompt: Custom system prompt
            capabilities: Agent capabilities
            metadata: Additional metadata

        Returns:
            Spawned agent data
        """
        if not self._pool:
            raise RuntimeError("Agent pool not initialized")

        if self._pool.total_agents >= self.config.max_spawned_agents:
            raise RuntimeError(
                f"Maximum agents reached ({self.config.max_spawned_agents})"
            )

        # Convert string to enum
        if isinstance(agent_type, str):
            agent_type = AgentType(agent_type)

        # Get default prompt if not provided
        if not system_prompt:
            system_prompt = self.DEFAULT_PROMPTS.get(
                agent_type, self.DEFAULT_PROMPTS[AgentType.GENERAL]
            )

        agent = SpawnedAgent(
            name=name,
            agent_type=agent_type,
            model=model or self.config.default_model,
            system_prompt=system_prompt,
            capabilities=capabilities or [],
            metadata=metadata or {},
        )

        # Simulate initialization
        await asyncio.sleep(0.1)
        agent.status = AgentStatus.READY

        await self._pool.add_agent(agent)
        return agent.model_dump()

    async def _terminate_agent(
        self,
        agent_id: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Terminate a spawned agent.

        Args:
            agent_id: ID of agent to terminate

        Returns:
            Termination result
        """
        if not self._pool:
            raise RuntimeError("Agent pool not initialized")

        agent = await self._pool.remove_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        agent.status = AgentStatus.TERMINATED

        return {
            "agent_id": agent_id,
            "terminated": True,
            "tasks_completed": agent.tasks_completed,
            "total_cost": agent.total_cost_usd,
        }

    async def _assign_task(
        self,
        agent_id: str,
        task: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Assign a task to an agent.

        Args:
            agent_id: Agent ID
            task: Task description

        Returns:
            Assignment result
        """
        if not self._pool:
            raise RuntimeError("Agent pool not initialized")

        agent = self._pool.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        if not agent.is_available:
            raise RuntimeError(f"Agent not available: {agent.status}")

        agent.status = AgentStatus.BUSY
        agent.current_task = task
        agent.last_active_at = datetime.utcnow()

        return {
            "agent_id": agent_id,
            "task": task,
            "assigned": True,
        }

    async def _complete_task(
        self,
        agent_id: str,
        result: Any = None,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        **kwargs,
    ) -> dict[str, Any]:
        """Mark an agent's task as complete.

        Args:
            agent_id: Agent ID
            result: Task result
            tokens_used: Tokens used
            cost_usd: Cost in USD

        Returns:
            Completion result
        """
        if not self._pool:
            raise RuntimeError("Agent pool not initialized")

        agent = self._pool.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        task = agent.current_task
        agent.current_task = None
        agent.status = AgentStatus.IDLE
        agent.tasks_completed += 1
        agent.total_tokens_used += tokens_used
        agent.total_cost_usd += cost_usd
        agent.last_active_at = datetime.utcnow()

        return {
            "agent_id": agent_id,
            "task": task,
            "result": result,
            "completed": True,
        }

    async def _get_agent(self, agent_id: str, **kwargs) -> dict[str, Any]:
        """Get agent by ID."""
        if not self._pool:
            raise RuntimeError("Agent pool not initialized")

        agent = self._pool.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        return agent.model_dump()

    async def _list_agents(
        self,
        status: str | None = None,
        agent_type: str | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """List spawned agents.

        Args:
            status: Filter by status
            agent_type: Filter by agent type

        Returns:
            List of agent data
        """
        if not self._pool:
            return []

        agents = list(self._pool.agents.values())

        if status:
            agents = [a for a in agents if a.status == AgentStatus(status)]

        if agent_type:
            agents = [a for a in agents if a.agent_type == AgentType(agent_type)]

        return [a.model_dump() for a in agents]

    async def _pool_status(self, **kwargs) -> dict[str, Any]:
        """Get agent pool status."""
        if not self._pool:
            return {"error": "Pool not initialized"}

        return {
            "total_agents": self._pool.total_agents,
            "available_agents": self._pool.available_agents,
            "busy_agents": self._pool.busy_agents,
            "load": self._pool.load,
            "max_agents": self.config.max_spawned_agents,
            "auto_scale": self.config.auto_scale,
            "scale_up_threshold": self.config.scale_up_threshold,
            "scale_down_threshold": self.config.scale_down_threshold,
        }

    async def _get_available_agent(
        self,
        agent_type: str | None = None,
        **kwargs,
    ) -> dict[str, Any] | None:
        """Get an available agent.

        Args:
            agent_type: Preferred agent type

        Returns:
            Available agent data or None
        """
        if not self._pool:
            return None

        type_enum = AgentType(agent_type) if agent_type else None
        agent = await self._pool.get_available_agent(type_enum)

        if agent:
            return agent.model_dump()
        return None

    # Convenience methods
    async def spawn(
        self,
        name: str,
        agent_type: str = "general",
        **kwargs,
    ) -> CapabilityResult:
        """Spawn a new agent."""
        return await self.execute(
            action="spawn", name=name, agent_type=agent_type, **kwargs
        )

    async def terminate(self, agent_id: str) -> CapabilityResult:
        """Terminate an agent."""
        return await self.execute(action="terminate", agent_id=agent_id)

    async def assign(self, agent_id: str, task: str) -> CapabilityResult:
        """Assign a task to an agent."""
        return await self.execute(action="assign_task", agent_id=agent_id, task=task)

    async def get_pool_status(self) -> CapabilityResult:
        """Get pool status."""
        return await self.execute(action="pool_status")

    @property
    def pool_load(self) -> float:
        """Current pool load."""
        return self._pool.load if self._pool else 1.0

    @property
    def available_agents(self) -> int:
        """Number of available agents."""
        return self._pool.available_agents if self._pool else 0
