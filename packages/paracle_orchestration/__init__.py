"""
Workflow orchestration and execution engine.

This package provides:
- DAG-based workflow execution
- Parallel step execution
- Agent coordination and caching
- Event-driven orchestration
- Human-in-the-Loop approval gates (ISO 42001)
"""

__version__ = "0.0.1"

from paracle_orchestration.approval import (
    ApprovalAlreadyDecidedError,
    ApprovalError,
    ApprovalManager,
    ApprovalNotFoundError,
    ApprovalTimeoutError,
    UnauthorizedApproverError,
)
from paracle_orchestration.context import ExecutionContext, ExecutionStatus
from paracle_orchestration.coordinator import AgentCoordinator
from paracle_orchestration.engine import WorkflowOrchestrator
from paracle_orchestration.exceptions import (
    CircularDependencyError,
    OrchestrationError,
    StepExecutionError,
)

__all__ = [
    # Orchestration
    "AgentCoordinator",
    "ExecutionContext",
    "ExecutionStatus",
    "WorkflowOrchestrator",
    # Approval (Human-in-the-Loop)
    "ApprovalManager",
    "ApprovalError",
    "ApprovalNotFoundError",
    "ApprovalAlreadyDecidedError",
    "ApprovalTimeoutError",
    "UnauthorizedApproverError",
    # Exceptions
    "OrchestrationError",
    "CircularDependencyError",
    "StepExecutionError",
]
