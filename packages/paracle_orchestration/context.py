"""Execution context for workflow orchestration."""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

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

    def add_step_result(self, step_id: str, result: Any) -> None:
        """Add result for a completed step."""
        self.step_results[step_id] = result

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
