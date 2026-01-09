"""Parac governance API schemas."""

from pydantic import BaseModel, Field


class PhaseInfo(BaseModel):
    """Phase information."""

    id: str = Field(description="Phase identifier")
    name: str = Field(description="Phase name")
    status: str = Field(description="Phase status")
    progress: str = Field(description="Phase progress percentage")


class GitInfo(BaseModel):
    """Git repository information."""

    branch: str = Field(description="Current branch")
    last_commit: str = Field(description="Last commit hash and message")
    has_changes: bool = Field(description="Has uncommitted changes")


class StatusResponse(BaseModel):
    """Project status response."""

    parac_root: str = Field(description="Path to .parac/ directory")
    project_root: str = Field(description="Path to project root")
    snapshot_date: str = Field(description="Last state snapshot date")
    phase: PhaseInfo = Field(description="Current phase information")
    git: GitInfo = Field(description="Git repository information")
    blockers: int = Field(description="Number of active blockers")
    next_actions: int = Field(description="Number of pending actions")


class SyncRequest(BaseModel):
    """Sync request options."""

    update_git: bool = Field(default=True, description="Sync git information")
    update_metrics: bool = Field(default=True, description="Sync file metrics")


class SyncChange(BaseModel):
    """A single sync change."""

    description: str = Field(description="Change description")


class SyncResponse(BaseModel):
    """Sync operation response."""

    success: bool = Field(description="Whether sync succeeded")
    changes: list[SyncChange] = Field(default_factory=list, description="Changes made")
    errors: list[str] = Field(default_factory=list, description="Errors encountered")


class ValidationIssue(BaseModel):
    """A single validation issue."""

    level: str = Field(description="Issue level: error, warning, info")
    file: str = Field(description="File with issue")
    message: str = Field(description="Issue description")
    line: int | None = Field(default=None, description="Line number if applicable")


class ValidationResponse(BaseModel):
    """Validation result response."""

    valid: bool = Field(description="Whether validation passed")
    files_checked: int = Field(description="Number of files checked")
    errors: int = Field(description="Number of errors")
    warnings: int = Field(description="Number of warnings")
    issues: list[ValidationIssue] = Field(
        default_factory=list, description="All validation issues"
    )


class SessionStartResponse(BaseModel):
    """Session start response."""

    phase: PhaseInfo = Field(description="Current phase information")
    focus_areas: list[str] = Field(
        default_factory=list, description="Current focus areas"
    )
    blockers: int = Field(description="Number of active blockers")
    message: str = Field(
        default="Source of truth verified. Proceeding.",
        description="Session start message",
    )


class SessionEndRequest(BaseModel):
    """Session end request with updates."""

    progress: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="New progress percentage (0-100)",
    )
    completed: list[str] = Field(
        default_factory=list, description="Items to mark as completed"
    )
    in_progress: list[str] = Field(
        default_factory=list, description="Items to mark as in-progress"
    )
    dry_run: bool = Field(
        default=False, description="If true, show changes without applying"
    )


class StateChange(BaseModel):
    """A state change made during session end."""

    field: str = Field(description="Field that changed")
    change: str = Field(description="Description of change")


class SessionEndResponse(BaseModel):
    """Session end response."""

    applied: bool = Field(description="Whether changes were applied")
    changes: list[StateChange] = Field(
        default_factory=list, description="Changes made or proposed"
    )
    message: str = Field(description="Result message")
