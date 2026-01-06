"""Workflow Engine wrapper for API layer.

Wraps WorkflowOrchestrator to provide API-friendly methods:
- Background execution (execute_async)
- Status polling (get_execution_status)
- Execution listing (list_executions)

Phase 4 - API Server Enhancement.
"""

import asyncio
import logging
from typing import Any

from paracle_domain.models import Workflow
from paracle_events import EventBus

from paracle_orchestration.context import ExecutionContext, ExecutionStatus
from paracle_orchestration.engine import WorkflowOrchestrator
from paracle_orchestration.exceptions import OrchestrationError, WorkflowNotFoundError

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """API-friendly workflow execution engine.

    Wraps WorkflowOrchestrator to provide:
    - Background (fire-and-forget) execution
    - Execution status tracking across requests
    - Execution history per workflow

    Example:
        >>> engine = WorkflowEngine()
        >>> execution_id = await engine.execute_async(workflow, {"input": "data"})
        >>> status = await engine.get_execution_status(execution_id)
        >>> print(status.progress)  # 0.5
    """

    def __init__(self, event_bus: EventBus | None = None, step_executor: Any = None):
        """Initialize WorkflowEngine.

        Args:
            event_bus: Event bus for publishing events (optional)
            step_executor: Step executor (optional, uses AgentExecutor)
        """
        # Create default event bus if not provided
        if event_bus is None:
            event_bus = EventBus()

        # Create default step executor if not provided
        if step_executor is None:
            # Use AgentExecutor for real LLM execution
            from paracle_orchestration.agent_executor import AgentExecutor

            agent_executor = AgentExecutor()
            step_executor = agent_executor.execute_step

        self.orchestrator = WorkflowOrchestrator(
            event_bus=event_bus, step_executor=step_executor
        )

        # Store completed executions for history
        # Protected by _history_lock for thread-safe access
        self.execution_history: dict[str, ExecutionContext] = {}
        self._history_lock = asyncio.Lock()

    async def execute(
        self, workflow: Workflow, inputs: dict[str, Any]
    ) -> ExecutionContext:
        """Execute workflow synchronously (blocking).

        Args:
            workflow: Workflow to execute
            inputs: Workflow inputs

        Returns:
            Completed ExecutionContext

        Raises:
            OrchestrationError: If execution fails
        """
        try:
            context = await self.orchestrator.execute(workflow, inputs)

            # Store in history with thread-safe access
            async with self._history_lock:
                self.execution_history[context.execution_id] = context

            return context

        except Exception as e:
            raise OrchestrationError(f"Workflow execution failed: {e}") from e

    async def execute_async(
        self, workflow: Workflow, inputs: dict[str, Any]
    ) -> str:
        """Execute workflow asynchronously in background.

        Returns immediately with execution_id for tracking.

        Args:
            workflow: Workflow to execute
            inputs: Workflow inputs

        Returns:
            execution_id for status polling
        """
        # Generate execution ID upfront so we can return it immediately
        from paracle_domain.models import generate_id

        execution_id = generate_id("execution")

        # Create initial context with pending status
        from datetime import datetime
        initial_context = ExecutionContext(
            execution_id=execution_id,
            workflow_id=workflow.id,
            workflow_name=workflow.spec.name,  # Fixed: access via spec
            inputs=inputs,
            status=ExecutionStatus.PENDING,
            started_at=datetime.now(),
        )

        # Store initial context immediately (so status can be queried)
        self.orchestrator.active_executions[execution_id] = initial_context

        # Start execution as background task
        task = asyncio.create_task(
            self._background_execute(execution_id, workflow, inputs)
        )

        # Store task for potential cancellation
        self._pending_tasks = getattr(self, "_pending_tasks", {})
        self._pending_tasks[execution_id] = task

        return execution_id

    async def _background_execute(
        self, execution_id: str, workflow: Workflow, inputs: dict[str, Any]
    ) -> None:
        """Background task for async execution.

        Args:
            execution_id: Pre-generated execution ID
            workflow: Workflow to execute
            inputs: Workflow inputs
        """
        try:
            # Execute workflow with pre-generated execution_id
            # Pass execution_id to orchestrator so it uses this one
            context = await self.orchestrator.execute(
                workflow, inputs, execution_id=execution_id
            )

            # Move to history after completion with thread-safe access
            async with self._history_lock:
                self.execution_history[execution_id] = context

            # Clean up task tracking
            if hasattr(self, "_pending_tasks") and execution_id in self._pending_tasks:
                del self._pending_tasks[execution_id]

        except Exception as e:
            # Log error and update context with failure status
            logger.error(
                f"Background execution failed for {execution_id}: {e}",
                exc_info=True
            )
            try:
                context = self.orchestrator.get_execution(execution_id)
                if context:
                    context.status = ExecutionStatus.FAILED
                    context.error = str(e)
                    async with self._history_lock:
                        self.execution_history[execution_id] = context
            except Exception as inner_e:
                logger.error(
                    f"Failed to update execution status for {execution_id}: {inner_e}",
                    exc_info=True
                )

    async def get_execution_status(self, execution_id: str) -> ExecutionStatus:
        """Get execution status (for polling).

        Args:
            execution_id: Execution identifier

        Returns:
            ExecutionStatus with current state

        Raises:
            WorkflowNotFoundError: If execution not found
        """
        # Check active executions first
        context = self.orchestrator.get_execution(execution_id)

        if context is None:
            # Check completed history with thread-safe access
            async with self._history_lock:
                context = self.execution_history.get(execution_id)

        if context is None:
            raise WorkflowNotFoundError(
                f"Execution '{execution_id}' not found (may have been purged)"
            )

        # Convert ExecutionContext to ExecutionStatus
        # (ExecutionContext has a .status property that is ExecutionStatus enum)
        return self._context_to_status(context)

    def _context_to_status(self, context: ExecutionContext) -> ExecutionStatus:
        """Convert ExecutionContext to API-friendly status object.

        Args:
            context: Execution context

        Returns:
            Status object with execution details
        """
        # Create a status object that mimics ExecutionStatus
        # but with additional API-friendly fields
        class Status:
            def __init__(self, ctx: ExecutionContext):
                self.execution_id = ctx.execution_id
                self.workflow_id = ctx.workflow_id
                self.status = ctx.status.value  # Convert enum to string
                self.progress = ctx.progress
                self.current_step = ctx.current_step
                self.completed_steps = list(ctx.step_results.keys())
                self.failed_steps = []  # TODO: Track failed steps
                self.started_at = ctx.started_at
                self.completed_at = ctx.completed_at
                self.error = ctx.errors[0] if ctx.errors else None
                self.result = ctx.outputs

        return Status(context)

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution.

        Args:
            execution_id: Execution identifier

        Returns:
            True if cancelled, False if already completed

        Raises:
            WorkflowNotFoundError: If execution not found
        """
        # Try to cancel in orchestrator
        cancelled = await self.orchestrator.cancel_execution(execution_id)

        if not cancelled:
            # Check if it exists at all with thread-safe access
            async with self._history_lock:
                context = self.execution_history.get(execution_id)
            if context is None:
                raise WorkflowNotFoundError(
                    f"Execution '{execution_id}' not found")

        return cancelled

    async def list_executions(
        self, workflow_id: str, status_filter: str | None = None
    ) -> list[ExecutionStatus]:
        """List all executions for a workflow.

        Args:
            workflow_id: Workflow identifier
            status_filter: Optional status filter (completed, running, failed)

        Returns:
            List of execution statuses

        Note:
            Returns both active and completed executions.
        """
        executions = []

        # Collect from active executions
        for context in self.orchestrator.get_active_executions():
            if context.workflow_id == workflow_id:
                if status_filter is None or context.status.value == status_filter:
                    executions.append(self._context_to_status(context))

        # Collect from history with thread-safe access
        async with self._history_lock:
            for context in self.execution_history.values():
                if context.workflow_id == workflow_id:
                    if status_filter is None or context.status.value == status_filter:
                        executions.append(self._context_to_status(context))

        # Sort by started_at (most recent first)
        executions.sort(
            key=lambda x: x.started_at if x.started_at else "", reverse=True
        )

        return executions
