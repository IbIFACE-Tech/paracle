"""Workflow orchestration engine.

This module provides the WorkflowOrchestrator for executing DAG-based workflows
with support for:
- Parallel step execution
- Human-in-the-Loop approval gates (ISO 42001 compliance)
- Event-driven observability
- Timeout handling
"""

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from paracle_domain.models import (
    ApprovalConfig,
    ApprovalPriority,
    Workflow,
    WorkflowStep,
    generate_id,
)
from paracle_events import EventBus
from paracle_events.events import (
    Event,
    workflow_completed,
    workflow_failed,
    workflow_started,
)

from paracle_orchestration.approval import ApprovalManager
from paracle_orchestration.approval import ApprovalTimeoutError as ApprovalTimeout
from paracle_orchestration.context import ExecutionContext
from paracle_orchestration.dag import DAG
from paracle_orchestration.exceptions import (
    ExecutionTimeoutError,
    InvalidWorkflowError,
    StepExecutionError,
)

# TYPE_CHECKING block intentionally empty - reserved for future type imports
if TYPE_CHECKING:
    ...  # noqa: PIE790


class WorkflowOrchestrator:
    """Orchestrates workflow execution with DAG-based parallelization.

    The orchestrator:
    - Validates workflow structure (DAG, dependencies)
    - Executes steps in topological order
    - Parallelizes independent steps
    - Supports Human-in-the-Loop approval gates (ISO 42001)
    - Emits events for observability
    - Manages execution context and error handling

    Human-in-the-Loop Approval:
        Steps can be configured to require human approval before execution.
        When a step has `requires_approval=True`, the workflow will:
        1. Execute the step to generate output
        2. Create an approval request with the output as context
        3. Pause execution and wait for human decision
        4. Continue if approved, fail if rejected

    Example:
        >>> orchestrator = WorkflowOrchestrator(
        ...     event_bus=event_bus,
        ...     step_executor=execute_step_fn,
        ...     approval_manager=ApprovalManager(event_bus),
        ... )
        >>> workflow = Workflow(spec=workflow_spec)
        >>> context = await orchestrator.execute(workflow, {"input": "data"})
        >>> print(context.status)  # ExecutionStatus.COMPLETED
    """

    def __init__(
        self,
        event_bus: EventBus,
        step_executor: Callable[[WorkflowStep, dict[str, Any]], Any],
        approval_manager: ApprovalManager | None = None,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            event_bus: Event bus for publishing workflow events
            step_executor: Async function to execute a single step
                          Signature: async def (step, inputs) -> result
            approval_manager: Optional approval manager for Human-in-the-Loop.
                            If None, steps with requires_approval are skipped.
        """
        self.event_bus = event_bus
        self.step_executor = step_executor
        self.approval_manager = approval_manager or ApprovalManager(event_bus)
        self.active_executions: dict[str, ExecutionContext] = {}

    async def execute(
        self,
        workflow: Workflow,
        inputs: dict[str, Any],
        timeout_seconds: float | None = None,
        execution_id: str | None = None,
        auto_approve: bool = False,
    ) -> ExecutionContext:
        """Execute a workflow with given inputs.

        Args:
            workflow: Workflow to execute
            inputs: Input data for the workflow
            timeout_seconds: Optional execution timeout
            execution_id: Optional pre-generated execution ID (for async tracking)
            auto_approve: If True, automatically approve all approval gates (YOLO mode)

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

        # Use provided execution_id or generate new one
        if execution_id is None:
            execution_id = generate_id("execution")

        # Create approval manager with YOLO setting if requested
        if auto_approve:
            self.approval_manager = ApprovalManager(
                self.event_bus,
                auto_approve=True,
                auto_approver="system:orchestrator",
            )

        # Check if context already exists (from async execution)
        context = self.active_executions.get(execution_id)

        if context is None:
            # Create new execution context
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
        else:
            # Update existing context (from async init)
            context.workflow_id = workflow.id
            context.inputs = inputs
            context.metadata.update(
                {
                    "workflow_name": workflow.spec.name,
                    "total_steps": len(workflow.spec.steps),
                }
            )

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

            # Collect final outputs from workflow specification
            self._collect_outputs(workflow, context)

            # Mark as completed
            context.complete()
            await self._emit_event("workflow.completed", context)

        except asyncio.TimeoutError as timeout_err:
            context.timeout_exceeded()
            await self._emit_event("workflow.timeout", context)
            raise ExecutionTimeoutError(
                context.execution_id, timeout_seconds
            ) from timeout_err

        except (StepExecutionError, InvalidWorkflowError) as exec_err:
            # Known workflow/step execution errors
            context.fail(str(exec_err))
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
                task = self._execute_step(workflow, step, context)
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
    ) -> Any:
        """Execute a single workflow step with optional approval gate.

        If the step requires approval (`requires_approval=True`), the workflow
        will pause after execution and wait for human decision.

        Args:
            workflow: Parent workflow
            step: Step to execute
            context: Execution context

        Returns:
            Step execution result

        Raises:
            StepExecutionError: If step execution or approval fails.
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

            # Check if step requires approval (Human-in-the-Loop)
            if step.requires_approval:
                result = await self._handle_approval_gate(
                    workflow, step, context, result, step_inputs
                )

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

    async def _handle_approval_gate(
        self,
        workflow: Workflow,
        step: WorkflowStep,
        context: ExecutionContext,
        result: Any,
        step_inputs: dict[str, Any],
    ) -> Any:
        """Handle Human-in-the-Loop approval gate for a step.

        Creates an approval request and waits for human decision.

        Args:
            workflow: Parent workflow
            step: Step requiring approval
            context: Execution context
            result: Step execution result to be approved
            step_inputs: Inputs that were provided to the step

        Returns:
            Original result if approved.

        Raises:
            StepExecutionError: If rejected or approval timeout.
        """
        # Build approval config from step's approval_config dict
        approval_config = ApprovalConfig(**step.approval_config)

        # Determine priority from config or default to MEDIUM
        priority = approval_config.priority or ApprovalPriority.MEDIUM

        # Create approval request with execution context
        approval_context = {
            "step_output": result,
            "step_inputs": step_inputs,
            "workflow_name": workflow.spec.name,
            "previous_steps": list(context.step_results.keys()),
        }

        request = await self.approval_manager.create_request(
            workflow_id=workflow.id,
            execution_id=context.execution_id,
            step_id=step.name,
            step_name=step.name,
            agent_name=step.agent,
            context=approval_context,
            config=approval_config,
            priority=priority,
            metadata={
                "workflow_inputs": context.inputs,
                "total_steps": context.metadata.get("total_steps", 0),
            },
        )

        # Mark context as awaiting approval
        context.await_approval(step.name, request.id)

        await self._emit_event(
            "workflow.step.awaiting_approval",
            context,
            {
                "step": step.name,
                "agent": step.agent,
                "approval_id": request.id,
                "priority": priority.value,
            },
        )

        try:
            # Wait for human decision
            is_approved = await self.approval_manager.wait_for_decision(
                request.id,
                timeout_seconds=approval_config.timeout_seconds,
            )

            # Resume from approval state
            context.resume_from_approval()

            if not is_approved:
                # Get the decided request to include rejection reason
                decided = self.approval_manager.get_request(request.id)
                reason = decided.decision_reason if decided else "Rejected by approver"

                await self._emit_event(
                    "workflow.step.approval_rejected",
                    context,
                    {
                        "step": step.name,
                        "approval_id": request.id,
                        "reason": reason,
                    },
                )

                raise StepExecutionError(
                    step.name,
                    Exception(f"Approval rejected: {reason}"),
                )

            # Approval granted
            await self._emit_event(
                "workflow.step.approval_granted",
                context,
                {"step": step.name, "approval_id": request.id},
            )

            return result

        except ApprovalTimeout as e:
            # Handle timeout
            context.resume_from_approval()

            await self._emit_event(
                "workflow.step.approval_timeout",
                context,
                {
                    "step": step.name,
                    "approval_id": request.id,
                    "timeout_seconds": e.timeout_seconds,
                },
            )

            if approval_config.auto_reject_on_timeout:
                raise StepExecutionError(
                    step.name,
                    Exception(f"Approval timed out after {e.timeout_seconds}s"),
                )

            # Re-raise the timeout error
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
                # Extract step name (may have suffix, ignore it)
                step_name = ref.split(".")[0] if "." in ref else ref

                if step_name in step_results:
                    resolved[key] = step_results[step_name]
                else:
                    # Step not executed yet, keep original
                    resolved[key] = value
            else:
                resolved[key] = value

        return resolved

    def _collect_outputs(
        self,
        workflow: Workflow,
        context: ExecutionContext,
    ) -> None:
        """Collect final outputs from workflow specification.

        Maps workflow outputs from step results according to the
        workflow spec's outputs definition.

        Args:
            workflow: Workflow specification
            context: Execution context with step_results
        """
        if not workflow.spec.outputs:
            # No outputs defined, use all step results
            context.outputs = context.step_results.copy()
            return

        # Collect specified outputs
        for output_name, output_spec in workflow.spec.outputs.items():
            output_value = self._resolve_output_spec(output_spec, context.step_results)
            if output_value is not None:
                context.outputs[output_name] = output_value
            else:
                # Direct reference or simple mapping
                context.outputs[output_name] = output_spec

    def _resolve_output_spec(
        self, output_spec: Any, step_results: dict[str, Any]
    ) -> Any | None:
        """Resolve an output specification to its value.

        Args:
            output_spec: Output specification (dict or value)
            step_results: Step execution results

        Returns:
            Resolved output value or None if not found
        """
        if not isinstance(output_spec, dict) or "source" not in output_spec:
            return None

        source = output_spec["source"]
        if not source.startswith("steps."):
            return None

        return self._extract_from_step_results(source, step_results)

    def _extract_from_step_results(
        self, source: str, step_results: dict[str, Any]
    ) -> Any | None:
        """Extract value from step results using source path.

        Args:
            source: Source path (e.g., "steps.step_id.outputs.key")
            step_results: Step execution results

        Returns:
            Extracted value or None if not found
        """
        parts = source.split(".")
        if len(parts) < 4:
            return None

        step_id = parts[1]
        output_key = parts[3]

        step_result = step_results.get(step_id)
        if not step_result or not isinstance(step_result, dict):
            return None

        return self._get_output_from_result(step_result, output_key)

    def _get_output_from_result(
        self, step_result: dict[str, Any], output_key: str
    ) -> Any | None:
        """Get output value from step result dict.

        Args:
            step_result: Step execution result
            output_key: Output key to extract

        Returns:
            Output value or None if not found
        """
        # Check in nested outputs dict first
        if "outputs" in step_result:
            outputs_dict = step_result["outputs"]
            if output_key in outputs_dict:
                return outputs_dict[output_key]

        # Check in top-level result dict
        if output_key in step_result:
            return step_result[output_key]

        return None

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
