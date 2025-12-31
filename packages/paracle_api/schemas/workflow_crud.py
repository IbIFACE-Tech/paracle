"""Schemas for Workflow CRUD operations.

Request and response models for creating, updating, and deleting workflows.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from paracle_domain.models import EntityStatus, WorkflowSpec, WorkflowStep


# =============================================================================
# Workflow Creation
# =============================================================================


class WorkflowCreateRequest(BaseModel):
    """Request to create a new workflow."""

    spec: WorkflowSpec = Field(..., description="Workflow specification")


class WorkflowResponse(BaseModel):
    """Response containing workflow details."""

    id: str = Field(..., description="Workflow ID")
    name: str = Field(..., description="Workflow name")
    description: str | None = Field(None, description="Workflow description")
    status: EntityStatus = Field(..., description="Current status")
    steps_count: int = Field(..., description="Number of steps")
    progress: float = Field(..., description="Completion progress (0-100)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# =============================================================================
# Workflow Update
# =============================================================================


class WorkflowUpdateRequest(BaseModel):
    """Request to update a workflow."""

    description: str | None = Field(None, description="New description")
    steps: list[WorkflowStep] | None = Field(None, description="Updated steps")
    inputs: dict | None = Field(None, description="Updated inputs")
    outputs: dict | None = Field(None, description="Updated outputs")
    config: dict | None = Field(None, description="Updated configuration")


# =============================================================================
# Workflow Deletion
# =============================================================================


class WorkflowDeleteResponse(BaseModel):
    """Response for workflow deletion."""

    success: bool = Field(..., description="Whether deletion succeeded")
    workflow_id: str = Field(..., description="ID of deleted workflow")
    message: str = Field(..., description="Deletion message")


# =============================================================================
# Workflow Listing
# =============================================================================


class WorkflowListRequest(BaseModel):
    """Request to list workflows with filters."""

    status: EntityStatus | None = Field(None, description="Filter by status")
    limit: int = Field(default=100, ge=1, le=1000, description="Max results")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


class WorkflowListResponse(BaseModel):
    """Response containing list of workflows."""

    workflows: list[WorkflowResponse] = Field(
        ..., description="List of workflows"
    )
    total: int = Field(..., description="Total count (before pagination)")
    limit: int = Field(..., description="Limit used")
    offset: int = Field(..., description="Offset used")


# =============================================================================
# Workflow Execution
# =============================================================================


class WorkflowExecuteRequest(BaseModel):
    """Request to execute a workflow."""

    inputs: dict = Field(
        default_factory=dict, description="Input values for workflow"
    )
    config: dict = Field(
        default_factory=dict, description="Execution configuration"
    )


class WorkflowExecuteResponse(BaseModel):
    """Response for workflow execution."""

    workflow_id: str = Field(..., description="Workflow ID")
    status: EntityStatus = Field(..., description="Execution status")
    message: str = Field(..., description="Execution message")
    current_step: str | None = Field(None, description="Current step")
