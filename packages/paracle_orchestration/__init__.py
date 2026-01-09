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

__version__ = "1.0.1"

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
from paracle_orchestration.dry_run import (
    DryRunConfig,
    DryRunExecutor,
    MockResponse,
    MockStrategy,
    create_response_template,
)
from paracle_orchestration.engine import WorkflowOrchestrator
from paracle_orchestration.engine_wrapper import WorkflowEngine
from paracle_orchestration.exceptions import (
    CircularDependencyError,
    OrchestrationError,
    StepExecutionError,
)
from paracle_orchestration.planner import ExecutionGroup, ExecutionPlan, WorkflowPlanner
from paracle_orchestration.retry import (
    AGGRESSIVE_RETRY_POLICY,
    CONSERVATIVE_RETRY_POLICY,
    DEFAULT_RETRY_POLICY,
    TRANSIENT_ONLY_POLICY,
    MaxRetriesExceededError,
    RetryError,
    RetryManager,
    classify_error,
)
from paracle_orchestration.skill_injector import SkillInjector
from paracle_orchestration.skill_loader import Skill, SkillLoader
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
    # Skills
    "Skill",
    "SkillInjector",
    "SkillLoader",
    # Planning
    "WorkflowPlanner",
    "ExecutionPlan",
    "ExecutionGroup",
    # Dry-Run Mode
    "DryRunExecutor",
    "DryRunConfig",
    "MockStrategy",
    "MockResponse",
    "create_response_template",
    # Approval (Human-in-the-Loop)
    "ApprovalManager",
    "ApprovalError",
    "ApprovalNotFoundError",
    "ApprovalAlreadyDecidedError",
    "ApprovalTimeoutError",
    "UnauthorizedApproverError",
    # Retry
    "RetryManager",
    "RetryError",
    "MaxRetriesExceededError",
    "classify_error",
    "DEFAULT_RETRY_POLICY",
    "AGGRESSIVE_RETRY_POLICY",
    "CONSERVATIVE_RETRY_POLICY",
    "TRANSIENT_ONLY_POLICY",
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
