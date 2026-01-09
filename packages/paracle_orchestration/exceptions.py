"""Orchestration exceptions.

Exception hierarchy for workflow orchestration with proper chaining.
All exceptions include error codes for documentation and support.
"""


class OrchestrationError(Exception):
    """Base exception for orchestration errors.

    Attributes:
        error_code: Unique error code (PARACLE-ORCH-XXX)
        message: Human-readable error message
    """

    error_code: str = "PARACLE-ORCH-000"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class CircularDependencyError(OrchestrationError):
    """Raised when circular dependency detected in workflow steps."""

    error_code = "PARACLE-ORCH-001"

    def __init__(self, cycle: list[str]) -> None:
        self.cycle = cycle
        cycle_str = " -> ".join(cycle)
        super().__init__(f"Circular dependency detected: {cycle_str}")


class StepExecutionError(OrchestrationError):
    """Raised when a workflow step fails to execute.

    Uses proper exception chaining with __cause__.
    """

    error_code = "PARACLE-ORCH-002"

    def __init__(self, step_id: str, error: Exception) -> None:
        self.step_id = step_id
        self.original_error = error
        super().__init__(f"Step '{step_id}' failed: {error}")
        self.__cause__ = error  # Proper exception chaining


class WorkflowNotFoundError(OrchestrationError):
    """Raised when a workflow is not found."""

    error_code = "PARACLE-ORCH-003"

    def __init__(self, workflow_id: str) -> None:
        self.workflow_id = workflow_id
        super().__init__(f"Workflow '{workflow_id}' not found")


class InvalidWorkflowError(OrchestrationError):
    """Raised when a workflow specification is invalid."""

    error_code = "PARACLE-ORCH-004"

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Invalid workflow: {reason}")


class ExecutionTimeoutError(OrchestrationError):
    """Raised when workflow execution exceeds timeout."""

    error_code = "PARACLE-ORCH-005"

    def __init__(self, execution_id: str, timeout_seconds: float) -> None:
        self.execution_id = execution_id
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"Execution '{execution_id}' exceeded timeout of {timeout_seconds}s"
        )
