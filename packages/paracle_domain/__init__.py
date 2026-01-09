"""Paracle Domain - Core Domain Models."""

from paracle_domain.factory import (
    AgentFactory,
    AgentFactoryError,
    ProviderNotAvailableError,
)
from paracle_domain.inheritance import (
    CircularInheritanceError,
    InheritanceError,
    InheritanceResult,
    MaxDepthExceededError,
    ParentNotFoundError,
    resolve_inheritance,
    validate_inheritance_chain,
)
from paracle_domain.models import (  # Retry models
    Agent,
    AgentSpec,
    AgentStatus,
    ApprovalConfig,
    ApprovalPriority,
    ApprovalRequest,
    ApprovalStatus,
    BackoffStrategy,
    EntityStatus,
    ErrorCategory,
    RetryAttempt,
    RetryCondition,
    RetryContext,
    RetryPolicy,
    Tool,
    ToolSpec,
    Workflow,
    WorkflowSpec,
    WorkflowStatus,
    WorkflowStep,
)

__version__ = "1.0.1"

__all__ = [
    # Models
    "Agent",
    "AgentSpec",
    "AgentStatus",
    "EntityStatus",
    "Tool",
    "ToolSpec",
    "Workflow",
    "WorkflowSpec",
    "WorkflowStatus",
    "WorkflowStep",
    # Approval (Human-in-the-Loop)
    "ApprovalConfig",
    "ApprovalPriority",
    "ApprovalRequest",
    "ApprovalStatus",
    # Retry
    "BackoffStrategy",
    "ErrorCategory",
    "RetryAttempt",
    "RetryCondition",
    "RetryContext",
    "RetryPolicy",
    "ApprovalRequest",
    "ApprovalStatus",
    # Factory
    "AgentFactory",
    "AgentFactoryError",
    "ProviderNotAvailableError",
    # Inheritance
    "CircularInheritanceError",
    "InheritanceError",
    "InheritanceResult",
    "MaxDepthExceededError",
    "ParentNotFoundError",
    "resolve_inheritance",
    "validate_inheritance_chain",
]
