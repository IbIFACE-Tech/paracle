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
from paracle_domain.models import (
    Agent,
    AgentSpec,
    AgentStatus,
    EntityStatus,
    Tool,
    ToolSpec,
    Workflow,
    WorkflowSpec,
    WorkflowStatus,
    WorkflowStep,
)

__version__ = "0.0.1"

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
