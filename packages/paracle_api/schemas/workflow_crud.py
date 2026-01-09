"""Schemas for Workflow CRUD operations.

Request and response models for creating, updating, and deleting workflows.
"""

from datetime import datetime

from paracle_domain.models import EntityStatus, WorkflowSpec, WorkflowStep
from pydantic import BaseModel, Field

# =============================================================================
# Workflow Creation
# =============================================================================


class WorkflowCreateRequest(BaseModel):
    """Request to create a new workflow."""

    spec: WorkflowSpec = Field(..., description="Workflow specification")


class WorkflowResponse(BaseModel):
    """Response containing workflow details."""

    id: str = Field(
        ..., description="Workflow ID", examples=["wf_01HQKZJ8XYQF2VWRGS7DTKHM3"]
    )
    name: str = Field(
        ...,
        description="Workflow name",
        examples=["data-processing", "agent-orchestration"],
    )
    description: str | None = Field(
        None,
        description="Workflow description",
        examples=["Process CSV data and generate reports"],
    )
    status: EntityStatus = Field(..., description="Current status", examples=["active"])
    steps_count: int = Field(..., description="Number of steps", examples=[5])
    progress: float = Field(
        ..., description="Completion progress (0-100)", examples=[75.5]
    )
    created_at: datetime = Field(
        ..., description="Creation timestamp", examples=["2026-01-07T14:30:00Z"]
    )
    updated_at: datetime = Field(
        ..., description="Last update timestamp", examples=["2026-01-07T15:45:00Z"]
    )


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

    workflows: list[WorkflowResponse] = Field(..., description="List of workflows")
    total: int = Field(..., description="Total count (before pagination)")
    limit: int = Field(..., description="Limit used")
    offset: int = Field(..., description="Offset used")


# =============================================================================
# Workflow Execution
# =============================================================================


class WorkflowExecuteRequest(BaseModel):
    """Request to execute a workflow."""

    inputs: dict = Field(
        default_factory=dict,
        description="Input values for workflow",
        examples=[{"source": "data.csv", "target": "output.json"}],
    )
    config: dict = Field(
        default_factory=dict,
        description="Execution configuration",
        examples=[{"timeout": 300, "retry_count": 3}],
    )


class WorkflowExecuteResponse(BaseModel):
    """Response for workflow execution."""

    workflow_id: str = Field(..., description="Workflow ID")
    status: EntityStatus = Field(..., description="Execution status")
    message: str = Field(..., description="Execution message")
    current_step: str | None = Field(None, description="Current step")
