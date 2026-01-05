"""Workflow orchestration engine."""

import asyncio
from collections.abc import Callable
from typing import Any

from paracle_domain.models import Workflow, WorkflowStep, generate_id
from paracle_events import EventBus
from paracle_events.events import (
    Event,
    workflow_completed,
    workflow_failed,
    workflow_started,
)

from paracle_orchestration.context import ExecutionContext
from paracle_orchestration.dag import DAG
from paracle_orchestration.exceptions import (
    ExecutionTimeoutError,
    InvalidWorkflowError,
    StepExecutionError,
)


class WorkflowOrchestrator:
    """Orchestrates workflow execution with DAG-based parallelization.

    The orchestrator:
    - Validates workflow structure (DAG, dependencies)
    - Executes steps in topological order
    - Parallelizes independent steps
    - Emits events for observability
    - Manages execution context and error handling

    Example:
        >>> orchestrator = WorkflowOrchestrator(
        ...     event_bus=event_bus,
        ...     step_executor=execute_step_fn
        ... )
        >>> workflow = Workflow(spec=workflow_spec)
        >>> context = await orchestrator.execute(workflow, {"input": "data"})
        >>> print(context.status)  # ExecutionStatus.COMPLETED
    """

    def __init__(
        self,
        event_bus: EventBus,
        step_executor: Callable[[WorkflowStep, dict[str, Any]], Any],
    ) -> None:
        """Initialize the orchestrator.

        Args:
            event_bus: Event bus for publishing workflow events
            step_executor: Async function to execute a single step
                          Signature: async def (step, inputs) -> result
        """
        self.event_bus = event_bus
        self.step_executor = step_executor
        self.active_executions: dict[str, ExecutionContext] = {}

    async def execute(
        self,
        workflow: Workflow,
        inputs: dict[str, Any],
        timeout_seconds: float | None = None,
    ) -> ExecutionContext:
        """Execute a workflow with given inputs.

        Args:
            workflow: Workflow to execute
            inputs: Input data for the workflow
            timeout_seconds: Optional execution timeout

        Returns:
            ExecutionContext with results and status

        Raises:
            InvalidWorkflowError: If workflow structure is invalid
            StepExecutionError: If a step fails to execute
        """
        # Validate workflow structure
        if not workflow.spec.steps:
            raise InvalidWorkflowError("Workflow has no steps")

        dag = DAG(workflow.spec.steps)
        dag.validate()

        # Create execution context
        execution_id = generate_id("execution")
        context = ExecutionContext(
            workflow_id=workflow.id,
            execution_id=execution_id,
            inputs=inputs,
            metadata={
                "workflow_name": workflow.spec.name,
                "total_steps": len(workflow.spec.steps),
            },
        )

        # Store in active executions
        self.active_executions[execution_id] = context

        try:
            # Start execution
            context.start()
            await self._emit_event("workflow.started", context)

            # Execute with optional timeout
            if timeout_seconds:
                await asyncio.wait_for(
                    self._execute_workflow(workflow, context, dag),
                    timeout=timeout_seconds,
                )
            else:
                await self._execute_workflow(workflow, context, dag)

            # Mark as completed
            context.complete()
            await self._emit_event("workflow.completed", context)

        except asyncio.TimeoutError:
            context.timeout_exceeded()
            await self._emit_event("workflow.timeout", context)
            raise ExecutionTimeoutError(context.execution_id, timeout_seconds)

        except Exception as e:
            context.fail(str(e))
            await self._emit_event("workflow.failed", context)
            # Return context with failed status instead of raising
            # This allows callers to inspect the failure

        finally:
            # Remove from active executions
            self.active_executions.pop(execution_id, None)

        return context

    async def _execute_workflow(
        self,
        workflow: Workflow,
        context: ExecutionContext,
        dag: DAG,
    ) -> None:
        """Execute workflow steps in DAG order.

        Args:
            workflow: Workflow being executed
            context: Execution context
            dag: Validated DAG of workflow steps
        """
        # Get execution levels for parallel execution
        levels = dag.get_execution_levels()

        # Execute each level sequentially, steps within level in parallel
        for step_names in levels:
            # Execute all steps in this level in parallel
            tasks = []
            for step_name in step_names:
                step = dag.steps[step_name]
                task = self._execute_step(workflow, step, context, dag)
                tasks.append(task)

            # Wait for all steps in this level to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check for errors
            for step_name, result in zip(step_names, results, strict=True):
                if isinstance(result, Exception):
                    raise StepExecutionError(step_name, result)

                # Store step result
                context.add_step_result(step_name, result)

    async def _execute_step(
        self,
        workflow: Workflow,
        step: WorkflowStep,
        context: ExecutionContext,
        dag: DAG,
    ) -> Any:
        """Execute a single workflow step.

        Args:
            workflow: Parent workflow
            step: Step to execute
            context: Execution context
            dag: DAG for dependency resolution

        Returns:
            Step execution result
        """
        context.current_step = step.name

        await self._emit_event(
            "workflow.step.started",
            context,
            {"step": step.name, "agent": step.agent},
        )

        try:
            # Resolve step inputs from workflow inputs and previous results
            step_inputs = self._resolve_step_inputs(
                step, context.inputs, context.step_results
            )

            # Execute the step
            result = await self.step_executor(step, step_inputs)

            await self._emit_event(
                "workflow.step.completed",
                context,
                {"step": step.name, "agent": step.agent},
            )

            return result

        except Exception as e:
            await self._emit_event(
                "workflow.step.failed",
                context,
                {"step": step.name, "agent": step.agent, "error": str(e)},
            )
            raise

    def _resolve_step_inputs(
        self,
        step: WorkflowStep,
        workflow_inputs: dict[str, Any],
        step_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Resolve inputs for a step.

        Combines:
        - Step's static inputs
        - Workflow inputs
        - Results from previous steps (referenced via $step.output)

        Args:
            step: Workflow step
            workflow_inputs: Top-level workflow inputs
            step_results: Results from completed steps

        Returns:
            Resolved input dictionary for the step
        """
        inputs = {}

        # Start with step's static inputs
        if step.inputs:
            inputs.update(step.inputs)

        # Add workflow inputs (can override step inputs)
        inputs.update(workflow_inputs)

        # Resolve references to previous step outputs
        # Format: $step_name returns the entire result from that step
        resolved = {}
        for key, value in inputs.items():
            if isinstance(value, str) and value.startswith("$"):
                # Reference to a previous step
                ref = value[1:]  # Remove $
                # Extract step name (may have .output or other suffix, ignore it)
                step_name = ref.split(".")[0] if "." in ref else ref

                if step_name in step_results:
                    resolved[key] = step_results[step_name]
                else:
                    resolved[key] = value  # Step not executed yet, keep original
            else:
                resolved[key] = value

        return resolved

    async def _emit_event(
        self,
        event_type: str,
        context: ExecutionContext,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Emit a workflow event.

        Args:
            event_type: Type of event (e.g., "workflow.started")
            context: Execution context
            data: Additional event data
        """
        # Map event type strings to factory functions
        if event_type == "workflow.started":
            event = workflow_started(context.workflow_id)
        elif event_type == "workflow.completed":
            event = workflow_completed(context.workflow_id, results=context.outputs)
        elif event_type == "workflow.failed":
            error = context.errors[0] if context.errors else "Unknown error"
            event = workflow_failed(context.workflow_id, error=error)
        else:
            # For other event types, create a basic event with source
            from paracle_events.events import EventType
            try:
                event_type_enum = EventType(event_type)
            except ValueError:
                # Custom event type - just use WORKFLOW_STARTED as fallback
                event_type_enum = EventType.WORKFLOW_STARTED

            payload = {
                "workflow_id": context.workflow_id,
                "execution_id": context.execution_id,
                "status": context.status.value,
            }
            if data:
                payload.update(data)

            event = Event(
                type=event_type_enum,
                source=context.workflow_id,
                payload=payload,
            )

        await self.event_bus.publish_async(event)

    def get_active_executions(self) -> list[ExecutionContext]:
        """Get all currently active executions.

        Returns:
            List of execution contexts for running workflows
        """
        return list(self.active_executions.values())

    def get_execution(self, execution_id: str) -> ExecutionContext | None:
        """Get execution context by ID.

        Args:
            execution_id: Execution identifier

        Returns:
            ExecutionContext if found, None otherwise
        """
        return self.active_executions.get(execution_id)

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution.

        Args:
            execution_id: Execution identifier

        Returns:
            True if cancelled, False if not found or already terminal
        """
        context = self.active_executions.get(execution_id)
        if context and not context.is_terminal:
            context.cancel()
            await self._emit_event("workflow.cancelled", context)
            return True
        return False
