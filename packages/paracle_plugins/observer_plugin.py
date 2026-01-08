"""Observer plugin interface for execution monitoring."""

from abc import abstractmethod
from typing import Any

from pydantic import BaseModel

from paracle_plugins.base import BasePlugin


class ExecutionEvent(BaseModel):
    """Event during agent/workflow execution."""

    event_type: str  # started, completed, failed, step_completed
    timestamp: str
    agent_id: str | None = None
    workflow_id: str | None = None
    execution_id: str
    step_name: str | None = None
    data: dict[str, Any] = {}


class ObserverPlugin(BasePlugin):
    """
    Base class for execution observer plugins.

    Implement this to monitor agent and workflow executions.

    Use cases:
    - Metrics collection (Prometheus, DataDog)
    - Error reporting (Sentry, Rollbar)
    - Cost tracking
    - Audit logging
    - Performance profiling

    Example:
        >>> class MetricsObserverPlugin(ObserverPlugin):
        ...     @property
        ...     def metadata(self) -> PluginMetadata:
        ...         return PluginMetadata(
        ...             name="prometheus-observer",
        ...             version="1.0.0",
        ...             description="Send metrics to Prometheus",
        ...             author="Me",
        ...             plugin_type=PluginType.OBSERVER,
        ...             capabilities=[
        ...                 PluginCapability.METRICS_COLLECTION
        ...             ],
        ...             dependencies=["prometheus-client"]
        ...         )
        ...
        ...     async def on_execution_started(
        ...         self, event: ExecutionEvent
        ...     ) -> None:
        ...         self.execution_counter.inc()
        ...
        ...     async def on_execution_completed(
        ...         self, event: ExecutionEvent
        ...     ) -> None:
        ...         duration = event.data.get("duration", 0)
        ...         self.execution_duration.observe(duration)
    """

    @abstractmethod
    async def on_execution_started(self, event: ExecutionEvent) -> None:
        """
        Called when execution starts.

        Args:
            event: Execution start event
        """
        pass

    @abstractmethod
    async def on_execution_completed(self, event: ExecutionEvent) -> None:
        """
        Called when execution completes successfully.

        Args:
            event: Execution completion event with results
        """
        pass

    @abstractmethod
    async def on_execution_failed(self, event: ExecutionEvent) -> None:
        """
        Called when execution fails.

        Args:
            event: Execution failure event with error details
        """
        pass

    async def on_step_started(self, event: ExecutionEvent) -> None:
        """
        Called when a workflow step starts.

        Args:
            event: Step start event
        """
        pass

    async def on_step_completed(self, event: ExecutionEvent) -> None:
        """
        Called when a workflow step completes.

        Args:
            event: Step completion event
        """
        pass

    async def on_step_failed(self, event: ExecutionEvent) -> None:
        """
        Called when a workflow step fails.

        Args:
            event: Step failure event
        """
        pass

    async def on_llm_call(self, event: ExecutionEvent) -> None:
        """
        Called when LLM API is called.

        Useful for cost tracking and performance monitoring.

        Args:
            event: LLM call event with model, tokens, cost
        """
        pass
