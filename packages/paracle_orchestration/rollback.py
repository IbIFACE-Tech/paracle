"""Workflow Rollback and Compensation System.

Provides rollback capabilities for workflow executions:
- Checkpoints at each step for recovery
- Compensating actions for failed steps
- Transaction-like semantics for workflows
- State recovery after failures

This enables robust error recovery in multi-step workflows.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from paracle_core.logging import get_logger
from pydantic import BaseModel, ConfigDict, Field

from paracle_orchestration.context import ExecutionContext

logger = get_logger(__name__)


def _utcnow() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


def _generate_id(prefix: str = "chk") -> str:
    """Generate unique ID."""
    return f"{prefix}_{uuid4().hex[:12]}"


class CheckpointStatus(str, Enum):
    """Status of a checkpoint."""

    CREATED = "created"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    EXPIRED = "expired"


class StepCheckpoint(BaseModel):
    """Checkpoint capturing state after a workflow step.

    Contains all information needed to:
    - Resume execution from this point
    - Rollback to this point
    - Execute compensating actions
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: _generate_id("chk"))
    execution_id: str = Field(..., description="Workflow execution ID")
    step_name: str = Field(..., description="Name of the completed step")
    step_index: int = Field(..., description="Index of the step in workflow")
    status: CheckpointStatus = Field(default=CheckpointStatus.CREATED)

    # State capture
    step_result: Any = Field(None, description="Result from the step")
    step_inputs: dict[str, Any] = Field(default_factory=dict)
    context_snapshot: dict[str, Any] = Field(
        default_factory=dict,
        description="Snapshot of execution context at checkpoint",
    )

    # Timing
    created_at: datetime = Field(default_factory=_utcnow)
    duration_ms: float | None = Field(None, description="Step execution time in ms")

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump(mode="json")


class CompensatingAction(BaseModel):
    """Definition of a compensating action for rollback.

    Compensating actions undo the effects of a completed step
    when rollback is required.
    """

    step_name: str = Field(..., description="Step this action compensates")
    action_type: str = Field(..., description="Type of compensation")
    parameters: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=0, description="Execution priority (higher = first)")
    required: bool = Field(
        default=True,
        description="If True, rollback fails if compensation fails",
    )
    timeout_seconds: float = Field(default=30.0)


class RollbackResult(BaseModel):
    """Result of a rollback operation."""

    success: bool = Field(..., description="Whether rollback succeeded")
    execution_id: str = Field(..., description="Execution that was rolled back")
    rolled_back_to: str | None = Field(None, description="Checkpoint ID rolled back to")
    steps_compensated: list[str] = Field(
        default_factory=list,
        description="Steps that were compensated",
    )
    errors: list[str] = Field(
        default_factory=list, description="Errors during rollback"
    )
    duration_ms: float | None = Field(None)


class CompensationHandler(ABC):
    """Abstract handler for executing compensating actions.

    Implementations provide actual compensation logic for specific step types.
    """

    @abstractmethod
    async def compensate(
        self,
        action: CompensatingAction,
        checkpoint: StepCheckpoint,
    ) -> bool:
        """Execute a compensating action.

        Args:
            action: Compensation action definition
            checkpoint: Checkpoint of the step being compensated

        Returns:
            True if compensation succeeded
        """
        pass

    @abstractmethod
    def can_handle(self, action: CompensatingAction) -> bool:
        """Check if this handler can process the action type."""
        pass


class DefaultCompensationHandler(CompensationHandler):
    """Default compensation handler with no-op behavior.

    Logs compensation attempts but doesn't perform actual rollback.
    Useful as a fallback or for steps that don't need compensation.
    """

    async def compensate(
        self,
        action: CompensatingAction,
        checkpoint: StepCheckpoint,
    ) -> bool:
        """Log and return success (no-op compensation)."""
        logger.info(
            f"No-op compensation for step '{action.step_name}' "
            f"(type: {action.action_type})"
        )
        return True

    def can_handle(self, action: CompensatingAction) -> bool:
        """Handle all action types as fallback."""
        return True


class CheckpointManager:
    """Manages checkpoints for workflow executions.

    Provides:
    - Checkpoint creation and storage
    - Checkpoint retrieval and querying
    - Checkpoint pruning
    """

    def __init__(self, max_checkpoints_per_execution: int = 100) -> None:
        """Initialize checkpoint manager.

        Args:
            max_checkpoints_per_execution: Max checkpoints to keep per execution
        """
        self._checkpoints: dict[str, list[StepCheckpoint]] = {}
        self._max_per_execution = max_checkpoints_per_execution

    def create_checkpoint(
        self,
        execution_id: str,
        step_name: str,
        step_index: int,
        step_result: Any,
        step_inputs: dict[str, Any],
        context: ExecutionContext,
        duration_ms: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StepCheckpoint:
        """Create a checkpoint for a completed step.

        Args:
            execution_id: Workflow execution ID
            step_name: Name of the completed step
            step_index: Index of the step
            step_result: Result from the step
            step_inputs: Inputs that were provided to the step
            context: Current execution context
            duration_ms: Step execution duration
            metadata: Optional additional metadata

        Returns:
            Created checkpoint
        """
        # Capture context snapshot
        context_snapshot = {
            "workflow_id": context.workflow_id,
            "status": context.status.value,
            "step_results": dict(context.step_results),
            "errors": list(context.errors),
            "start_time": (
                context.start_time.isoformat() if context.start_time else None
            ),
        }

        checkpoint = StepCheckpoint(
            execution_id=execution_id,
            step_name=step_name,
            step_index=step_index,
            step_result=step_result,
            step_inputs=step_inputs,
            context_snapshot=context_snapshot,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )

        # Store checkpoint
        if execution_id not in self._checkpoints:
            self._checkpoints[execution_id] = []

        self._checkpoints[execution_id].append(checkpoint)

        # Prune if needed
        if len(self._checkpoints[execution_id]) > self._max_per_execution:
            self._checkpoints[execution_id] = self._checkpoints[execution_id][
                -self._max_per_execution :
            ]

        return checkpoint

    def get_checkpoints(
        self,
        execution_id: str,
        from_index: int | None = None,
        to_index: int | None = None,
    ) -> list[StepCheckpoint]:
        """Get checkpoints for an execution.

        Args:
            execution_id: Execution ID
            from_index: Start step index (inclusive)
            to_index: End step index (inclusive)

        Returns:
            List of checkpoints
        """
        checkpoints = self._checkpoints.get(execution_id, [])

        if from_index is not None:
            checkpoints = [c for c in checkpoints if c.step_index >= from_index]

        if to_index is not None:
            checkpoints = [c for c in checkpoints if c.step_index <= to_index]

        return sorted(checkpoints, key=lambda c: c.step_index)

    def get_latest_checkpoint(self, execution_id: str) -> StepCheckpoint | None:
        """Get the latest checkpoint for an execution."""
        checkpoints = self._checkpoints.get(execution_id, [])
        if not checkpoints:
            return None
        return max(checkpoints, key=lambda c: c.step_index)

    def get_checkpoint_by_step(
        self,
        execution_id: str,
        step_name: str,
    ) -> StepCheckpoint | None:
        """Get checkpoint for a specific step."""
        checkpoints = self._checkpoints.get(execution_id, [])
        for checkpoint in checkpoints:
            if checkpoint.step_name == step_name:
                return checkpoint
        return None

    def clear_checkpoints(self, execution_id: str) -> int:
        """Clear all checkpoints for an execution.

        Returns number of checkpoints cleared.
        """
        if execution_id not in self._checkpoints:
            return 0
        count = len(self._checkpoints[execution_id])
        del self._checkpoints[execution_id]
        return count

    def count(self, execution_id: str | None = None) -> int:
        """Count checkpoints.

        Args:
            execution_id: If provided, count for this execution only

        Returns:
            Checkpoint count
        """
        if execution_id:
            return len(self._checkpoints.get(execution_id, []))
        return sum(len(v) for v in self._checkpoints.values())


class WorkflowRollbackManager:
    """Manages rollback operations for workflow executions.

    Coordinates:
    - Checkpoint management
    - Compensation handler execution
    - Rollback orchestration
    """

    def __init__(
        self,
        checkpoint_manager: CheckpointManager | None = None,
        compensation_handlers: list[CompensationHandler] | None = None,
    ) -> None:
        """Initialize rollback manager.

        Args:
            checkpoint_manager: Manager for checkpoints
            compensation_handlers: Handlers for compensation actions
        """
        self.checkpoint_manager = checkpoint_manager or CheckpointManager()
        self._compensation_handlers: list[CompensationHandler] = (
            compensation_handlers or []
        )
        self._compensation_handlers.append(DefaultCompensationHandler())

        # Store compensation definitions per step
        self._compensation_registry: dict[str, CompensatingAction] = {}

    def register_compensation(
        self,
        step_name: str,
        action: CompensatingAction,
    ) -> None:
        """Register a compensating action for a step.

        Args:
            step_name: Step name
            action: Compensation action definition
        """
        self._compensation_registry[step_name] = action

    def add_handler(self, handler: CompensationHandler) -> None:
        """Add a compensation handler.

        Args:
            handler: Handler to add
        """
        # Insert before default handler
        self._compensation_handlers.insert(-1, handler)

    def create_checkpoint(
        self,
        execution_id: str,
        step_name: str,
        step_index: int,
        step_result: Any,
        step_inputs: dict[str, Any],
        context: ExecutionContext,
        duration_ms: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StepCheckpoint:
        """Create a checkpoint after step completion.

        Convenience method that delegates to checkpoint manager.
        """
        return self.checkpoint_manager.create_checkpoint(
            execution_id=execution_id,
            step_name=step_name,
            step_index=step_index,
            step_result=step_result,
            step_inputs=step_inputs,
            context=context,
            duration_ms=duration_ms,
            metadata=metadata,
        )

    async def rollback(
        self,
        execution_id: str,
        to_checkpoint_id: str | None = None,
        to_step_index: int | None = None,
    ) -> RollbackResult:
        """Rollback an execution to a previous state.

        Args:
            execution_id: Execution to rollback
            to_checkpoint_id: Specific checkpoint to rollback to
            to_step_index: Step index to rollback to

        Returns:
            RollbackResult with details of the operation
        """
        start_time = _utcnow()
        errors: list[str] = []
        compensated_steps: list[str] = []

        # Determine target checkpoint
        target_checkpoint = None
        if to_checkpoint_id:
            checkpoints = self.checkpoint_manager.get_checkpoints(execution_id)
            for cp in checkpoints:
                if cp.id == to_checkpoint_id:
                    target_checkpoint = cp
                    break
        elif to_step_index is not None:
            checkpoints = self.checkpoint_manager.get_checkpoints(
                execution_id, to_index=to_step_index
            )
            if checkpoints:
                target_checkpoint = checkpoints[-1]

        target_index = target_checkpoint.step_index if target_checkpoint else -1

        # Get checkpoints to rollback (in reverse order)
        all_checkpoints = self.checkpoint_manager.get_checkpoints(execution_id)
        checkpoints_to_rollback = [
            cp for cp in reversed(all_checkpoints) if cp.step_index > target_index
        ]

        # Execute compensating actions
        for checkpoint in checkpoints_to_rollback:
            action = self._compensation_registry.get(checkpoint.step_name)
            if not action:
                # No compensation defined - skip or use default
                action = CompensatingAction(
                    step_name=checkpoint.step_name,
                    action_type="no-op",
                    required=False,
                )

            try:
                # Find handler
                handler = self._find_handler(action)
                success = await asyncio.wait_for(
                    handler.compensate(action, checkpoint),
                    timeout=action.timeout_seconds,
                )

                if success:
                    compensated_steps.append(checkpoint.step_name)
                    logger.info(f"Compensated step: {checkpoint.step_name}")
                elif action.required:
                    errors.append(
                        f"Required compensation failed for step: {checkpoint.step_name}"
                    )
                    break

            except asyncio.TimeoutError:
                error_msg = f"Compensation timeout for step: {checkpoint.step_name}"
                errors.append(error_msg)
                logger.error(error_msg)
                if action.required:
                    break

            except Exception as e:
                error_msg = f"Compensation error for step {checkpoint.step_name}: {e}"
                errors.append(error_msg)
                logger.exception(error_msg)
                if action.required:
                    break

        # Calculate duration
        end_time = _utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000

        return RollbackResult(
            success=len(errors) == 0,
            execution_id=execution_id,
            rolled_back_to=target_checkpoint.id if target_checkpoint else None,
            steps_compensated=compensated_steps,
            errors=errors,
            duration_ms=duration_ms,
        )

    def _find_handler(self, action: CompensatingAction) -> CompensationHandler:
        """Find handler for compensation action."""
        for handler in self._compensation_handlers:
            if handler.can_handle(action):
                return handler
        # Default handler should always be last and handle everything
        return self._compensation_handlers[-1]

    async def rollback_to_step(
        self,
        execution_id: str,
        step_name: str,
    ) -> RollbackResult:
        """Rollback to a specific step by name.

        Args:
            execution_id: Execution to rollback
            step_name: Step name to rollback to

        Returns:
            RollbackResult
        """
        checkpoint = self.checkpoint_manager.get_checkpoint_by_step(
            execution_id, step_name
        )
        if not checkpoint:
            return RollbackResult(
                success=False,
                execution_id=execution_id,
                errors=[f"Checkpoint not found for step: {step_name}"],
            )

        return await self.rollback(
            execution_id,
            to_checkpoint_id=checkpoint.id,
        )

    def get_rollback_plan(
        self,
        execution_id: str,
        to_step_index: int | None = None,
    ) -> list[tuple[StepCheckpoint, CompensatingAction | None]]:
        """Get the rollback plan without executing it.

        Useful for preview/confirmation before rollback.

        Args:
            execution_id: Execution ID
            to_step_index: Target step index

        Returns:
            List of (checkpoint, compensation_action) tuples
        """
        all_checkpoints = self.checkpoint_manager.get_checkpoints(execution_id)
        target_index = to_step_index if to_step_index is not None else -1

        checkpoints_to_rollback = [
            cp for cp in reversed(all_checkpoints) if cp.step_index > target_index
        ]

        plan = []
        for checkpoint in checkpoints_to_rollback:
            action = self._compensation_registry.get(checkpoint.step_name)
            plan.append((checkpoint, action))

        return plan


# =============================================================================
# Transaction-like wrapper
# =============================================================================


class WorkflowTransaction:
    """Transaction-like wrapper for workflow execution.

    Provides transaction semantics:
    - Begin: Start transaction
    - Commit: Finalize successful execution
    - Rollback: Revert on failure

    Example:
        >>> async with WorkflowTransaction(rollback_manager, execution_id) as tx:
        ...     await execute_step_1()
        ...     tx.checkpoint("step_1", result_1, context)
        ...     await execute_step_2()
        ...     tx.checkpoint("step_2", result_2, context)
        >>> # Auto-commit on success, auto-rollback on exception
    """

    def __init__(
        self,
        rollback_manager: WorkflowRollbackManager,
        execution_id: str,
        auto_rollback: bool = True,
    ) -> None:
        """Initialize transaction.

        Args:
            rollback_manager: Rollback manager instance
            execution_id: Workflow execution ID
            auto_rollback: Automatically rollback on exception
        """
        self._rollback_manager = rollback_manager
        self._execution_id = execution_id
        self._auto_rollback = auto_rollback
        self._step_index = 0
        self._committed = False
        self._rolled_back = False

    async def __aenter__(self) -> WorkflowTransaction:
        """Enter transaction context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit transaction context.

        Commits on success, rolls back on exception if auto_rollback is True.
        """
        if exc_type is not None and self._auto_rollback and not self._rolled_back:
            logger.warning(
                f"Auto-rolling back execution {self._execution_id} due to: {exc_val}"
            )
            await self.rollback()
            # Don't suppress the exception
            return False

        if not self._rolled_back and not self._committed:
            self.commit()

        return False

    def checkpoint(
        self,
        step_name: str,
        step_result: Any,
        context: ExecutionContext,
        step_inputs: dict[str, Any] | None = None,
        duration_ms: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StepCheckpoint:
        """Create a checkpoint within the transaction.

        Args:
            step_name: Name of the completed step
            step_result: Result from the step
            context: Execution context
            step_inputs: Inputs provided to the step
            duration_ms: Step duration
            metadata: Additional metadata

        Returns:
            Created checkpoint
        """
        checkpoint = self._rollback_manager.create_checkpoint(
            execution_id=self._execution_id,
            step_name=step_name,
            step_index=self._step_index,
            step_result=step_result,
            step_inputs=step_inputs or {},
            context=context,
            duration_ms=duration_ms,
            metadata=metadata,
        )
        self._step_index += 1
        return checkpoint

    def commit(self) -> None:
        """Commit the transaction (mark as successful)."""
        self._committed = True
        logger.info(f"Transaction committed for execution: {self._execution_id}")

    async def rollback(
        self,
        to_step_index: int | None = None,
    ) -> RollbackResult:
        """Rollback the transaction.

        Args:
            to_step_index: Step index to rollback to (None = rollback all)

        Returns:
            RollbackResult
        """
        result = await self._rollback_manager.rollback(
            execution_id=self._execution_id,
            to_step_index=to_step_index,
        )
        self._rolled_back = True
        return result

    @property
    def is_committed(self) -> bool:
        """Check if transaction is committed."""
        return self._committed

    @property
    def is_rolled_back(self) -> bool:
        """Check if transaction is rolled back."""
        return self._rolled_back
