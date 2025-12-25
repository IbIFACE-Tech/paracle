"""Domain models for Paracle.

Core domain entities following DDD principles.
All models are pure Python with Pydantic validation.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def generate_id(prefix: str) -> str:
    """Generate a unique ID with prefix."""
    return f"{prefix}_{uuid4().hex[:12]}"


class EntityStatus(str, Enum):
    """Common status for entities."""

    PENDING = "pending"
    ACTIVE = "active"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ARCHIVED = "archived"


# =============================================================================
# Agent Models
# =============================================================================


class AgentSpec(BaseModel):
    """Specification of an agent.

    AgentSpec defines the configuration for an agent, including:
    - LLM provider and model settings
    - System prompt and behavior
    - Inheritance from parent agents
    - Tool configuration
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "code-reviewer",
                "description": "Reviews code for best practices",
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.3,
                "parent": "base-agent",
            }
        }
    )

    name: str = Field(..., description="Unique name of the agent")
    description: str | None = Field(None, description="Agent description")
    provider: str = Field(
        ..., description="LLM provider (openai, anthropic, google, ollama)"
    )
    model: str = Field(..., description="Model name (e.g., gpt-4, claude-3)")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)
    system_prompt: str | None = Field(None, description="System prompt")
    parent: str | None = Field(
        None, description="Parent agent name for inheritance"
    )
    tools: list[str] = Field(
        default_factory=list, description="List of tool names"
    )
    config: dict[str, Any] = Field(
        default_factory=dict, description="Additional configuration"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata (tags, labels, etc.)"
    )

    def has_parent(self) -> bool:
        """Check if agent has a parent."""
        return self.parent is not None


class AgentStatus(BaseModel):
    """Runtime status of an agent."""

    phase: EntityStatus = Field(default=EntityStatus.PENDING)
    message: str | None = None
    error: str | None = None
    last_run: datetime | None = None
    run_count: int = Field(default=0, ge=0)
    last_updated: datetime = Field(default_factory=utc_now)


class Agent(BaseModel):
    """Agent instance.

    An Agent is a runtime instance created from an AgentSpec.
    It tracks execution status and maintains state.
    """

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    id: str = Field(default_factory=lambda: generate_id("agent"))
    spec: AgentSpec
    resolved_spec: AgentSpec | None = Field(
        None, description="Spec after inheritance resolution"
    )
    status: AgentStatus = Field(default_factory=AgentStatus)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def get_effective_spec(self) -> AgentSpec:
        """Get the effective spec (resolved or original)."""
        return self.resolved_spec if self.resolved_spec else self.spec

    def update_status(
        self,
        phase: EntityStatus | None = None,
        message: str | None = None,
        error: str | None = None,
    ) -> None:
        """Update agent status."""
        if phase:
            self.status.phase = phase
        if message:
            self.status.message = message
        if error:
            self.status.error = error
        self.status.last_updated = utc_now()
        self.updated_at = utc_now()


# =============================================================================
# Workflow Models
# =============================================================================


class WorkflowStep(BaseModel):
    """A step in a workflow."""

    id: str = Field(..., description="Step identifier")
    name: str = Field(..., description="Step name")
    agent: str = Field(..., description="Agent name to execute")
    prompt: str | None = Field(None, description="Prompt template")
    inputs: dict[str, Any] = Field(
        default_factory=dict, description="Input mappings"
    )
    outputs: dict[str, Any] = Field(
        default_factory=dict, description="Output mappings"
    )
    depends_on: list[str] = Field(
        default_factory=list, description="Step dependencies"
    )
    config: dict[str, Any] = Field(
        default_factory=dict, description="Step configuration"
    )


class WorkflowSpec(BaseModel):
    """Specification of a workflow."""

    name: str = Field(..., description="Workflow name")
    description: str | None = Field(None, description="Workflow description")
    steps: list[WorkflowStep] = Field(..., description="Workflow steps")
    inputs: dict[str, Any] = Field(
        default_factory=dict, description="Workflow inputs"
    )
    outputs: dict[str, Any] = Field(
        default_factory=dict, description="Workflow outputs"
    )
    config: dict[str, Any] = Field(
        default_factory=dict, description="Workflow configuration"
    )


class WorkflowStatus(BaseModel):
    """Status of workflow execution."""

    phase: EntityStatus = Field(default=EntityStatus.PENDING)
    current_step: str | None = None
    completed_steps: list[str] = Field(default_factory=list)
    failed_steps: list[str] = Field(default_factory=list)
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    results: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class Workflow(BaseModel):
    """Workflow instance."""

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    id: str = Field(default_factory=lambda: generate_id("workflow"))
    spec: WorkflowSpec
    status: WorkflowStatus = Field(default_factory=WorkflowStatus)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def start(self) -> None:
        """Mark workflow as started."""
        self.status.phase = EntityStatus.RUNNING
        self.status.started_at = utc_now()
        self.updated_at = utc_now()

    def complete(self, results: dict[str, Any] | None = None) -> None:
        """Mark workflow as completed."""
        self.status.phase = EntityStatus.SUCCEEDED
        self.status.progress = 100.0
        self.status.completed_at = utc_now()
        if results:
            self.status.results = results
        self.updated_at = utc_now()

    def fail(self, error: str) -> None:
        """Mark workflow as failed."""
        self.status.phase = EntityStatus.FAILED
        self.status.error = error
        self.status.completed_at = utc_now()
        self.updated_at = utc_now()


# =============================================================================
# Tool Models
# =============================================================================


class ToolSpec(BaseModel):
    """Specification of a tool."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema for parameters"
    )
    returns: dict[str, Any] = Field(
        default_factory=dict, description="Return type schema"
    )
    is_mcp: bool = Field(default=False, description="Is MCP tool")
    mcp_server: str | None = Field(None, description="MCP server URI")


class Tool(BaseModel):
    """Tool instance."""

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    id: str = Field(default_factory=lambda: generate_id("tool"))
    spec: ToolSpec
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now)
