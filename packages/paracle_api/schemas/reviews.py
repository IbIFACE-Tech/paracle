"""API schemas for artifact review workflow."""

from typing import Any

from pydantic import BaseModel, Field


class ReviewCreateRequest(BaseModel):
    """Request to create artifact review."""

    artifact_id: str = Field(..., description="Artifact identifier")
    artifact_type: str = Field(..., description="Artifact type")
    sandbox_id: str = Field(..., description="Source sandbox")
    artifact_content: dict[str, Any] = Field(
        default_factory=dict, description="Artifact content/metadata"
    )
    risk_level: str | None = Field(
        None, description="Override risk level (auto-detected if None)"
    )


class ApprovalRequest(BaseModel):
    """Request to approve or reject review."""

    reviewer: str = Field(..., description="Reviewer identifier")
    comment: str | None = Field(None, description="Optional comment")


class ReviewDecisionResponse(BaseModel):
    """Review decision details."""

    reviewer: str
    decision: str
    timestamp: str
    comment: str | None


class ReviewResponse(BaseModel):
    """Review details response."""

    review_id: str
    artifact_id: str
    artifact_type: str
    sandbox_id: str
    status: str
    risk_level: str
    created_at: str
    updated_at: str
    expires_at: str | None
    artifact_content: dict[str, Any]
    decisions: list[dict[str, Any]]
    required_approvals: int
    approval_count: int


class ReviewListItem(BaseModel):
    """Review list item."""

    review_id: str
    artifact_id: str
    artifact_type: str
    sandbox_id: str
    status: str
    risk_level: str
    created_at: str
    updated_at: str
    expires_at: str | None
    approval_count: int
    required_approvals: int


class ReviewListResponse(BaseModel):
    """List of reviews response."""

    reviews: list[dict[str, Any]]
    total: int


class ReviewStatsResponse(BaseModel):
    """Review statistics response."""

    total: int
    pending: int
    approved: int
    rejected: int
    timeout: int
    by_risk_level: dict[str, int]
