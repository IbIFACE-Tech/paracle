"""Execution context for workflow orchestration."""

from enum import Enum
from typing import Any

from paracle_core.compat import UTC, datetime
from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(UTC)


class ExecutionStatus(str, Enum):
    """Status of workflow execution."""

    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"  # Human-in-the-Loop pause
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ExecutionCost(BaseModel):
    """Cost tracking for workflow execution.

    Tracks token usage and costs for all LLM calls within an execution.
    """

    # Token counts
    prompt_tokens: int = Field(default=0, ge=0, description="Total prompt tokens")
    completion_tokens: int = Field(
        default=0, ge=0, description="Total completion tokens"
    )
    total_tokens: int = Field(default=0, ge=0, description="Total tokens")

    # Costs in USD
    prompt_cost: float = Field(default=0.0, ge=0.0, description="Total prompt cost")
    completion_cost: float = Field(
        default=0.0, ge=0.0, description="Total completion cost"
    )
    total_cost: float = Field(default=0.0, ge=0.0, description="Total cost")

    # Request count
    request_count: int = Field(default=0, ge=0, description="Number of LLM requests")

    # Per-step breakdown
    step_costs: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Cost breakdown by step"
    )

    def add_step_cost(
        self,
        step_id: str,
        prompt_tokens: int,
        completion_tokens: int,
        prompt_cost: float,
        completion_cost: float,
        provider: str | None = None,
        model: str | None = None,
    ) -> None:
        """Add cost for a step.

        Args:
            step_id: Step identifier
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            prompt_cost: Cost of prompt tokens
            completion_cost: Cost of completion tokens
            provider: LLM provider name
            model: Model name
        """
        # Update totals
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_tokens += prompt_tokens + completion_tokens
        self.prompt_cost += prompt_cost
        self.completion_cost += completion_cost
        self.total_cost += prompt_cost + completion_cost
        self.request_count += 1

        # Store step breakdown
        self.step_costs[step_id] = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "prompt_cost": prompt_cost,
            "completion_cost": completion_cost,
            "total_cost": prompt_cost + completion_cost,
            "provider": provider,
            "model": model,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "prompt_cost": self.prompt_cost,
            "completion_cost": self.completion_cost,
            "total_cost": self.total_cost,
            "request_count": self.request_count,
            "step_costs": self.step_costs,
        }


class ExecutionContext(BaseModel):
    """Context for tracking workflow execution state.

    Contains all information about a running or completed workflow execution,
    including inputs, outputs, step results, errors, and timing information.

    Example:
        >>> context = ExecutionContext(
        ...     workflow_id="workflow_123",
        ...     execution_id="exec_456",
        ...     inputs={"query": "hello"}
        ... )
        >>> context.status = ExecutionStatus.RUNNING
        >>> context.step_results["step1"] = {"result": "processed"}
    """

    workflow_id: str = Field(..., description="ID of the workflow being executed")
    execution_id: str = Field(..., description="Unique ID for this execution")
    inputs: dict[str, Any] = Field(..., description="Workflow input data")
    outputs: dict[str, Any] = Field(
        default_factory=dict, description="Final workflow outputs"
    )
    status: ExecutionStatus = Field(
        default=ExecutionStatus.PENDING, description="Current execution status"
    )
    current_step: str | None = Field(None, description="Currently executing step ID")
    step_results: dict[str, Any] = Field(
        default_factory=dict, description="Results from completed steps"
    )
    errors: list[str] = Field(default_factory=list, description="Execution errors")
    start_time: datetime | None = Field(None, description="Execution start timestamp")
    end_time: datetime | None = Field(None, description="Execution end timestamp")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional execution metadata"
    )
    cost: ExecutionCost = Field(
        default_factory=ExecutionCost, description="Cost tracking for this execution"
    )

    def start(self) -> None:
        """Mark execution as started."""
        self.status = ExecutionStatus.RUNNING
        self.start_time = _utcnow()

    def complete(self, outputs: dict[str, Any] | None = None) -> None:
        """Mark execution as completed successfully."""
        self.status = ExecutionStatus.COMPLETED
        self.end_time = _utcnow()
        if outputs is not None:
            self.outputs = outputs

    def fail(self, error: str) -> None:
        """Mark execution as failed."""
        self.status = ExecutionStatus.FAILED
        self.end_time = _utcnow()
        self.errors.append(error)

    def cancel(self) -> None:
        """Mark execution as cancelled."""
        self.status = ExecutionStatus.CANCELLED
        self.end_time = _utcnow()

    def timeout_exceeded(self) -> None:
        """Mark execution as timed out."""
        self.status = ExecutionStatus.TIMEOUT
        self.end_time = _utcnow()

    def await_approval(self, step_id: str, approval_id: str) -> None:
        """Mark execution as awaiting human approval.

        Args:
            step_id: The step requiring approval.
            approval_id: ID of the approval request.
        """
        self.status = ExecutionStatus.AWAITING_APPROVAL
        self.current_step = step_id
        self.metadata["pending_approval_id"] = approval_id

    def resume_from_approval(self) -> None:
        """Resume execution after approval granted."""
        self.status = ExecutionStatus.RUNNING
        self.metadata.pop("pending_approval_id", None)

    @property
    def is_awaiting_approval(self) -> bool:
        """Check if execution is waiting for human approval."""
        return self.status == ExecutionStatus.AWAITING_APPROVAL

    @property
    def pending_approval_id(self) -> str | None:
        """Get the pending approval ID if awaiting approval."""
        return self.metadata.get("pending_approval_id")

    @property
    def duration_seconds(self) -> float | None:
        """Calculate execution duration in seconds."""
        if self.start_time is None:
            return None
        end = self.end_time or _utcnow()
        return (end - self.start_time).total_seconds()

    @property
    def is_terminal(self) -> bool:
        """Check if execution is in a terminal state."""
        return self.status in {
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
            ExecutionStatus.TIMEOUT,
        }

    @property
    def is_running(self) -> bool:
        """Check if execution is currently running."""
        return self.status == ExecutionStatus.RUNNING

    @property
    def progress(self) -> float:
        """Calculate execution progress as a ratio (0.0 to 1.0).

        Returns:
            Progress ratio based on completed steps vs total steps
        """
        # Get total steps from metadata if available
        total_steps = self.metadata.get("total_steps", 0)

        if total_steps == 0:
            # No steps known, use status-based progress
            if self.status == ExecutionStatus.COMPLETED:
                return 1.0
            elif self.status in {
                ExecutionStatus.FAILED,
                ExecutionStatus.CANCELLED,
                ExecutionStatus.TIMEOUT,
            }:
                return 0.0
            elif self.status == ExecutionStatus.RUNNING:
                return 0.5  # Assume halfway if no step info
            else:
                return 0.0  # PENDING or AWAITING_APPROVAL

        # Calculate from completed steps
        completed = len(self.step_results)
        return min(1.0, completed / total_steps)

    @property
    def started_at(self) -> datetime | None:
        """Get start time (alias for start_time)."""
        return self.start_time

    @property
    def completed_at(self) -> datetime | None:
        """Get completion time (alias for end_time)."""
        return self.end_time

    def add_step_result(self, step_id: str, result: Any) -> None:
        """Add result for a completed step."""
        self.step_results[step_id] = result

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)

    @property
    def results(self) -> dict[str, Any]:
        """Get step results (alias for step_results)."""
        return self.step_results
