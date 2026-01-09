"""Data models for run storage."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_serializer


class RunStatus(str, Enum):
    """Run execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class AgentRunMetadata(BaseModel):
    """Metadata for an agent execution run."""

    run_id: str
    agent_id: str
    agent_name: str
    started_at: datetime
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    status: RunStatus = RunStatus.PENDING
    exit_code: int | None = None

    # Execution context
    provider: str | None = None
    model: str | None = None
    temperature: float | None = None

    # Resource usage
    tokens_used: int | None = None
    cost_usd: float | None = None
    memory_mb: int | None = None
    cpu_seconds: float | None = None

    # Result summary
    artifacts_count: int = 0
    files_modified: int = 0
    error_count: int = 0
    error_message: str | None = None

    # Additional metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_serializer("started_at", "completed_at", when_used="json")
    def serialize_datetime(self, dt: datetime | None) -> str | None:
        return dt.isoformat() if dt else None


class WorkflowRunMetadata(BaseModel):
    """Metadata for a workflow execution run."""

    run_id: str
    workflow_id: str
    workflow_name: str
    started_at: datetime
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    status: RunStatus = RunStatus.PENDING

    # Steps
    steps_total: int = 0
    steps_completed: int = 0
    steps_failed: int = 0
    steps_skipped: int = 0

    # Agents involved
    agents_used: list[str] = Field(default_factory=list)

    # Resource usage (aggregated)
    tokens_total: int | None = None
    cost_total_usd: float | None = None
    artifacts_count: int = 0
    error_message: str | None = None

    # Additional metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_serializer("started_at", "completed_at", when_used="json")
    def serialize_datetime(self, dt: datetime | None) -> str | None:
        return dt.isoformat() if dt else None


class RunQuery(BaseModel):
    """Query parameters for searching runs."""

    agent_id: str | None = None
    workflow_id: str | None = None
    status: RunStatus | None = None
    since: datetime | None = None
    until: datetime | None = None
    limit: int = 20
    offset: int = 0
