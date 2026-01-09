"""Schemas for Agent CRUD operations.

Request and response models for creating, updating, and deleting agents.
"""

from datetime import datetime

from paracle_domain.models import AgentSpec, EntityStatus
from pydantic import BaseModel, Field

# =============================================================================
# Agent Creation
# =============================================================================


class AgentCreateRequest(BaseModel):
    """Request to create a new agent from a spec.

    Can either reference an existing spec by name, or provide a full spec inline.
    """

    spec_name: str | None = Field(None, description="Name of existing spec to use")
    spec: AgentSpec | None = Field(
        None, description="Inline agent spec (if not using spec_name)"
    )
    resolve_inheritance: bool = Field(
        default=True, description="Whether to resolve inheritance"
    )

    def model_post_init(self, __context) -> None:
        """Validate that exactly one of spec_name or spec is provided."""
        if self.spec_name is None and self.spec is None:
            raise ValueError("Either spec_name or spec must be provided")
        if self.spec_name is not None and self.spec is not None:
            raise ValueError("Cannot provide both spec_name and spec")


class AgentResponse(BaseModel):
    """Response containing agent details."""

    id: str = Field(..., description="Agent ID")
    spec_name: str = Field(..., description="Spec name")
    description: str | None = Field(None, description="Agent description")
    provider: str = Field(..., description="LLM provider")
    model: str = Field(..., description="Model name")
    status: EntityStatus = Field(..., description="Current status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# =============================================================================
# Agent Update
# =============================================================================


class AgentUpdateRequest(BaseModel):
    """Request to update an agent."""

    description: str | None = Field(None, description="New description")
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, gt=0)
    system_prompt: str | None = Field(None)
    tools: list[str] | None = Field(None)
    config: dict | None = Field(None)
    metadata: dict | None = Field(None)


# =============================================================================
# Agent Deletion
# =============================================================================


class AgentDeleteResponse(BaseModel):
    """Response for agent deletion."""

    success: bool = Field(..., description="Whether deletion succeeded")
    agent_id: str = Field(..., description="ID of deleted agent")
    message: str = Field(..., description="Deletion message")


# =============================================================================
# Agent Listing
# =============================================================================


class AgentListRequest(BaseModel):
    """Request to list agents with filters."""

    status: EntityStatus | None = Field(None, description="Filter by status")
    provider: str | None = Field(None, description="Filter by provider")
    spec_name: str | None = Field(None, description="Filter by spec name")
    limit: int = Field(default=100, ge=1, le=1000, description="Max results")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


class AgentListResponse(BaseModel):
    """Response containing list of agents."""

    agents: list[AgentResponse] = Field(..., description="List of agents")
    total: int = Field(..., description="Total count (before pagination)")
    limit: int = Field(..., description="Limit used")
    offset: int = Field(..., description="Offset used")


# =============================================================================
# Agent Status Update
# =============================================================================


class AgentStatusUpdateRequest(BaseModel):
    """Request to update agent status."""

    phase: EntityStatus | None = Field(None, description="New phase")
    message: str | None = Field(None, description="Status message")
    error: str | None = Field(None, description="Error message if failed")


# =============================================================================
# Spec Management
# =============================================================================


class SpecRegisterRequest(BaseModel):
    """Request to register a new agent spec."""

    spec: AgentSpec = Field(..., description="Agent specification to register")
    overwrite: bool = Field(
        default=False, description="Overwrite if spec already exists"
    )


class SpecResponse(BaseModel):
    """Response containing spec details."""

    name: str = Field(..., description="Spec name")
    description: str | None = Field(None, description="Spec description")
    provider: str = Field(..., description="LLM provider")
    model: str = Field(..., description="Model name")
    parent: str | None = Field(None, description="Parent spec name")
    tools_count: int = Field(..., description="Number of tools")


class SpecListResponse(BaseModel):
    """Response containing list of specs."""

    specs: list[SpecResponse] = Field(..., description="List of specs")
    total: int = Field(..., description="Total count")
