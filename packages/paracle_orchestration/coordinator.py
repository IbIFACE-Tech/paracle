"""Agent coordinator for caching and execution management."""

import asyncio
import logging
from typing import Any

from paracle_core.compat import UTC, datetime
from paracle_domain.factory import AgentFactory
from paracle_domain.models import Agent

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(UTC)


class AgentCoordinator:
    """Coordinates agent execution with caching and resource management.

    Features:
    - Agent instance caching (avoid recreating agents)
    - Parallel agent execution
    - Resource cleanup
    - Execution metrics tracking

    Example:
        >>> coordinator = AgentCoordinator(agent_factory)
        >>> agent = Agent(spec=agent_spec)
        >>> result = await coordinator.execute_agent(agent, {"input": "data"})
        >>> print(result["result"])
    """

    def __init__(
        self,
        agent_factory: AgentFactory,
        cache_enabled: bool = True,
        max_cache_size: int = 100,
        enable_skills: bool = True,
        skill_injection_mode: str = "full",
        parac_dir: str | None = None,
    ) -> None:
        """Initialize the agent coordinator.

        Args:
            agent_factory: Factory for creating agent instances
            cache_enabled: Whether to cache agent instances
            max_cache_size: Maximum number of cached agents
            enable_skills: Enable skill loading and injection
            skill_injection_mode: How to inject skills (modes below)
            parac_dir: Path to .parac directory (defaults to ./.parac)

        Skill Injection Modes:
            - full: Include full skill content
            - summary: Include only descriptions
            - references: Include references only
            - minimal: Just skill names
        """
        self.agent_factory = agent_factory
        self.cache_enabled = cache_enabled
        self.max_cache_size = max_cache_size
        self.agent_cache: dict[str, Any] = {}
        self.execution_metrics: dict[str, dict[str, Any]] = {}
        self.enable_skills = enable_skills

        # Initialize skill system (lazy import to avoid circular deps)
        if self.enable_skills:
            from pathlib import Path

            from paracle_orchestration.skill_injector import SkillInjector
            from paracle_orchestration.skill_loader import SkillLoader

            parac_path = Path(parac_dir) if parac_dir else None
            self.skill_loader = SkillLoader(parac_path)
            self.skill_injector = SkillInjector(injection_mode=skill_injection_mode)
            logger.info(
                f"Skill system enabled (mode: {skill_injection_mode}, "
                f"parac_dir: {self.skill_loader.parac_dir})"
            )
        else:
            self.skill_loader = None
            self.skill_injector = None
            logger.info("Skill system disabled")

    async def execute_agent(
        self,
        agent: Agent,
        inputs: dict[str, Any],
        context: dict[str, Any] | None = None,
        load_skills: bool = True,
    ) -> dict[str, Any]:
        """Execute an agent with given inputs.

        Args:
            agent: Agent to execute
            inputs: Input data for the agent
            context: Optional execution context
            load_skills: Whether to load and inject skills (default: True)

        Returns:
            Dictionary with execution results:
            - result: Agent output
            - execution_time: Duration in seconds
            - metadata: Additional execution metadata
            - skills: Loaded skills (if enabled)
        """
        start_time = _utcnow()

        # Load skills if enabled
        skills = []
        enhanced_prompt = agent.spec.system_prompt
        skill_context = {}

        if (
            self.enable_skills
            and load_skills
            and self.skill_loader
            and self.skill_injector
        ):
            try:
                # Load skills assigned to this agent
                skills = self.skill_loader.load_agent_skills(agent.spec.name)

                if skills:
                    # Enhance system prompt with skill knowledge
                    enhanced_prompt = self.skill_injector.inject_skills(
                        agent.spec.system_prompt, skills
                    )

                    # Create skill context for provider
                    skill_context = self.skill_injector.create_skill_context(skills)

                    skill_ids = [s.skill_id for s in skills]
                    logger.info(
                        f"Loaded {len(skills)} skills for "
                        f"agent {agent.spec.name}: {skill_ids}"
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to load skills for " f"agent {agent.spec.name}: {e}"
                )

        # Get or create agent instance
        agent_instance = await self._get_agent_instance(agent)

        # Prepare inputs with context and skills
        full_inputs = dict(inputs)
        if context:
            full_inputs["_context"] = context
        if skill_context:
            full_inputs["_skills"] = skill_context
        if enhanced_prompt:
            full_inputs["_enhanced_prompt"] = enhanced_prompt

        # Execute agent (actual provider call happens here)
        try:
            result = await self._execute_agent_instance(agent_instance, full_inputs)

            execution_time = (_utcnow() - start_time).total_seconds()

            # Track metrics
            self._track_execution(agent.id, execution_time, success=True)

            return {
                "agent_id": agent.id,
                "result": result,
                "execution_time": execution_time,
                "skills": [skill.to_dict() for skill in skills],
                "metadata": {
                    "agent_name": agent.spec.name,
                    "model": agent.spec.model,
                    "provider": agent.spec.provider,
                    "skills_loaded": len(skills),
                    "skill_ids": [s.skill_id for s in skills],
                },
            }

        except Exception:
            execution_time = (_utcnow() - start_time).total_seconds()
            self._track_execution(agent.id, execution_time, success=False)
            raise

    async def execute_parallel(
        self,
        agents: list[Agent],
        inputs_list: list[dict[str, Any]],
        shared_context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute multiple agents in parallel.

        Args:
            agents: List of agents to execute
            inputs_list: List of input dictionaries (one per agent)
            shared_context: Optional context shared across all agents

        Returns:
            List of execution results (one per agent)

        Raises:
            ValueError: If agents and inputs lists have different lengths
        """
        if len(agents) != len(inputs_list):
            raise ValueError(
                f"Number of agents ({len(agents)}) does not match "
                f"number of inputs ({len(inputs_list)})"
            )

        # Create tasks for parallel execution
        tasks = [
            self.execute_agent(agent, inputs, shared_context)
            for agent, inputs in zip(agents, inputs_list, strict=True)
        ]

        # Execute all in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error dicts
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    {
                        "agent_id": agents[i].id,
                        "error": str(result),
                        "success": False,
                    }
                )
            else:
                processed_results.append(result)

        return processed_results

    async def _get_agent_instance(self, agent: Agent) -> Any:
        """Get or create agent instance with caching.

        Args:
            agent: Agent to get instance for

        Returns:
            Agent instance (cached or newly created)
        """
        if not self.cache_enabled:
            return await self._create_agent_instance(agent)

        # Check cache
        if agent.id in self.agent_cache:
            return self.agent_cache[agent.id]

        # Create new instance
        instance = await self._create_agent_instance(agent)

        # Cache if under limit
        if len(self.agent_cache) < self.max_cache_size:
            self.agent_cache[agent.id] = instance
        else:
            # Simple eviction: remove oldest (first) entry
            oldest_key = next(iter(self.agent_cache))
            del self.agent_cache[oldest_key]
            self.agent_cache[agent.id] = instance

        return instance

    async def _create_agent_instance(self, agent: Agent) -> Any:
        """Create a new agent instance.

        Args:
            agent: Agent to create instance for

        Returns:
            Agent instance
        """
        # Use the agent factory to create the agent
        # This will resolve inheritance and create with provider
        created_agent = self.agent_factory.create(agent.spec)
        return created_agent

    async def _execute_agent_instance(
        self,
        agent_instance: Any,
        inputs: dict[str, Any],
    ) -> Any:
        """Execute an agent instance.

        This is a placeholder that would be implemented by framework adapters.
        In practice, this would call the LLM provider through the adapter.

        Args:
            agent_instance: Agent instance to execute
            inputs: Input data

        Returns:
            Agent execution result
        """
        # Placeholder - actual execution would go through framework adapters
        # For now, return the inputs as a simple echo
        return {"echo": inputs, "status": "placeholder"}

    def _track_execution(
        self,
        agent_id: str,
        execution_time: float,
        success: bool,
    ) -> None:
        """Track execution metrics for an agent.

        Args:
            agent_id: Agent identifier
            execution_time: Execution duration in seconds
            success: Whether execution succeeded
        """
        if agent_id not in self.execution_metrics:
            self.execution_metrics[agent_id] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_execution_time": 0.0,
                "avg_execution_time": 0.0,
            }

        metrics = self.execution_metrics[agent_id]
        metrics["total_executions"] += 1
        metrics["total_execution_time"] += execution_time

        if success:
            metrics["successful_executions"] += 1
        else:
            metrics["failed_executions"] += 1

        metrics["avg_execution_time"] = (
            metrics["total_execution_time"] / metrics["total_executions"]
        )

    def clear_cache(self, agent_id: str | None = None) -> None:
        """Clear the agent cache.

        Args:
            agent_id: Optional specific agent ID to clear.
                     If None, clears entire cache.
        """
        if agent_id:
            self.agent_cache.pop(agent_id, None)
        else:
            self.agent_cache.clear()

    def get_metrics(self, agent_id: str | None = None) -> dict[str, Any]:
        """Get execution metrics.

        Args:
            agent_id: Optional specific agent ID.
                     If None, returns metrics for all agents.

        Returns:
            Dictionary of metrics
        """
        if agent_id:
            return self.execution_metrics.get(agent_id, {})
        return dict(self.execution_metrics)

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats:
            - cached_agents: Number of cached agents
            - cache_size_limit: Maximum cache size
            - cache_enabled: Whether caching is enabled
        """
        return {
            "cached_agents": len(self.agent_cache),
            "cache_size_limit": self.max_cache_size,
            "cache_enabled": self.cache_enabled,
        }
