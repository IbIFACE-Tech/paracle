"""
Workflow orchestration and execution engine.

This package provides:
- DAG-based workflow execution
- Parallel step execution
- Agent coordination and caching
- Event-driven orchestration
- Human-in-the-Loop approval gates (ISO 42001)
- Workflow loading from YAML definitions
"""

__version__ = "0.0.1"

from paracle_orchestration.agent_executor import AgentExecutor
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
from paracle_orchestration.engine_wrapper import WorkflowEngine
from paracle_orchestration.exceptions import (
    CircularDependencyError,
    OrchestrationError,
    StepExecutionError,
)
from paracle_orchestration.workflow_loader import (
    WorkflowLoader,
    WorkflowLoadError,
    list_available_workflows,
    load_workflow,
)

__all__ = [
    # Orchestration
    "AgentCoordinator",
    "AgentExecutor",
    "ExecutionContext",
    "ExecutionStatus",
    "WorkflowOrchestrator",
    "WorkflowEngine",
    # Approval (Human-in-the-Loop)
    "ApprovalManager",
    "ApprovalError",
    "ApprovalNotFoundError",
    "ApprovalAlreadyDecidedError",
    "ApprovalTimeoutError",
    "UnauthorizedApproverError",
    # Workflow Loading
    "WorkflowLoader",
    "WorkflowLoadError",
    "load_workflow",
    "list_available_workflows",
    # Exceptions
    "OrchestrationError",
    "CircularDependencyError",
    "StepExecutionError",
]
