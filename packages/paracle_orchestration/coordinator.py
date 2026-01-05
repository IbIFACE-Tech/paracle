"""Agent coordinator for caching and execution management."""

import asyncio
from datetime import UTC, datetime
from typing import Any

from paracle_domain.factory import AgentFactory
from paracle_domain.models import Agent


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
    ) -> None:
        """Initialize the agent coordinator.

        Args:
            agent_factory: Factory for creating agent instances
            cache_enabled: Whether to cache agent instances
            max_cache_size: Maximum number of cached agents
        """
        self.agent_factory = agent_factory
        self.cache_enabled = cache_enabled
        self.max_cache_size = max_cache_size
        self.agent_cache: dict[str, Any] = {}
        self.execution_metrics: dict[str, dict[str, Any]] = {}

    async def execute_agent(
        self,
        agent: Agent,
        inputs: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute an agent with given inputs.

        Args:
            agent: Agent to execute
            inputs: Input data for the agent
            context: Optional execution context

        Returns:
            Dictionary with execution results:
            - result: Agent output
            - execution_time: Duration in seconds
            - metadata: Additional execution metadata
        """
        start_time = _utcnow()

        # Get or create agent instance
        agent_instance = await self._get_agent_instance(agent)

        # Prepare inputs with context
        full_inputs = dict(inputs)
        if context:
            full_inputs["_context"] = context

        # Execute agent (this would call the actual LLM provider)
        # For now, we return a placeholder - actual execution would be implemented
        # by the framework adapter layer
        try:
            result = await self._execute_agent_instance(agent_instance, full_inputs)

            execution_time = (_utcnow() - start_time).total_seconds()

            # Track metrics
            self._track_execution(agent.id, execution_time, success=True)

            return {
                "agent_id": agent.id,
                "result": result,
                "execution_time": execution_time,
                "metadata": {
                    "agent_name": agent.spec.name,
                    "model": agent.spec.model,
                    "provider": agent.spec.provider,
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
                processed_results.append({
                    "agent_id": agents[i].id,
                    "error": str(result),
                    "success": False,
                })
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
