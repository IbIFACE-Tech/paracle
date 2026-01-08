"""Kanban API schemas.

Provides request/response models for board and task management endpoints.
"""

from datetime import datetime

from pydantic import BaseModel, Field

# =============================================================================
# Board Schemas
# =============================================================================


class BoardCreateRequest(BaseModel):
    """Request to create a new board."""

    name: str = Field(..., description="Board name")
    description: str = Field(default="", description="Board description")
    columns: list[str] | None = Field(
        default=None,
        description="Custom column names (default: TODO, IN_PROGRESS, REVIEW, DONE)",
    )


class BoardResponse(BaseModel):
    """Board details response."""

    id: str = Field(..., description="Board ID")
    name: str = Field(..., description="Board name")
    description: str = Field(..., description="Board description")
    columns: list[str] = Field(..., description="Board columns")
    archived: bool = Field(..., description="Whether board is archived")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class BoardListResponse(BaseModel):
    """List of boards response."""

    boards: list[BoardResponse] = Field(..., description="List of boards")
    total: int = Field(..., description="Total count")


class BoardUpdateRequest(BaseModel):
    """Request to update a board."""

    name: str | None = Field(default=None, description="New board name")
    description: str | None = Field(default=None, description="New description")
    columns: list[str] | None = Field(default=None, description="New columns")
    archived: bool | None = Field(default=None, description="Archive status")


class BoardDeleteResponse(BaseModel):
    """Board deletion response."""

    success: bool = Field(..., description="Whether deletion succeeded")
    board_id: str = Field(..., description="Deleted board ID")
    message: str = Field(..., description="Status message")


class BoardStatsResponse(BaseModel):
    """Board statistics response."""

    total_tasks: int = Field(..., description="Total task count")
    status_counts: dict[str, int] = Field(..., description="Tasks per status")
    avg_cycle_time_hours: float | None = Field(
        None, description="Average cycle time in hours"
    )
    avg_lead_time_hours: float | None = Field(
        None, description="Average lead time in hours"
    )


# =============================================================================
# Task Schemas
# =============================================================================


class TaskCreateRequest(BaseModel):
    """Request to create a new task."""

    board_id: str = Field(..., description="Board ID")
    title: str = Field(..., description="Task title")
    description: str = Field(default="", description="Task description")
    priority: str = Field(default="MEDIUM", description="Task priority")
    task_type: str = Field(default="FEATURE", description="Task type")
    assigned_to: str | None = Field(default=None, description="Assignee agent ID")
    tags: list[str] = Field(default_factory=list, description="Task tags")
    depends_on: list[str] = Field(
        default_factory=list, description="Dependency task IDs"
    )


class TaskResponse(BaseModel):
    """Task details response."""

    id: str = Field(..., description="Task ID")
    board_id: str = Field(..., description="Board ID")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    status: str = Field(..., description="Task status")
    priority: str = Field(..., description="Task priority")
    task_type: str = Field(..., description="Task type")
    assigned_to: str | None = Field(None, description="Assignee")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    started_at: datetime | None = Field(None, description="Start timestamp")
    completed_at: datetime | None = Field(None, description="Completion timestamp")
    tags: list[str] = Field(..., description="Task tags")
    depends_on: list[str] = Field(..., description="Dependencies")
    blocked_by: str | None = Field(None, description="Blocker reason")
    cycle_time_hours: float | None = Field(None, description="Cycle time")
    lead_time_hours: float | None = Field(None, description="Lead time")


class TaskListResponse(BaseModel):
    """List of tasks response."""

    tasks: list[TaskResponse] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total count")


class TaskUpdateRequest(BaseModel):
    """Request to update a task."""

    title: str | None = Field(default=None, description="New title")
    description: str | None = Field(default=None, description="New description")
    priority: str | None = Field(default=None, description="New priority")
    task_type: str | None = Field(default=None, description="New type")
    tags: list[str] | None = Field(default=None, description="New tags")
    depends_on: list[str] | None = Field(default=None, description="New dependencies")


class TaskMoveRequest(BaseModel):
    """Request to move a task to a different status."""

    status: str = Field(..., description="Target status")
    reason: str | None = Field(
        default=None, description="Reason (required for BLOCKED)"
    )


class TaskAssignRequest(BaseModel):
    """Request to assign a task."""

    agent_id: str = Field(..., description="Agent ID to assign to")


class TaskDeleteResponse(BaseModel):
    """Task deletion response."""

    success: bool = Field(..., description="Whether deletion succeeded")
    task_id: str = Field(..., description="Deleted task ID")
    message: str = Field(..., description="Status message")
