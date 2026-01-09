"""Review data models."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ReviewStatus(str, Enum):
    """Review status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ReviewDecision(BaseModel):
    """Individual review decision.

    Attributes:
        reviewer: Who made the decision
        decision: Approve or reject
        timestamp: When decision was made
        comment: Optional comment
    """

    reviewer: str = Field(..., description="Reviewer identifier")
    decision: str = Field(..., description="approve or reject")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    comment: str | None = Field(None, description="Optional comment")


class ArtifactReview(BaseModel):
    """Artifact review request.

    Tracks review state, decisions, and metadata for artifacts
    requiring approval.

    Attributes:
        review_id: Unique review identifier
        artifact_id: Artifact being reviewed
        artifact_type: Type of artifact
        sandbox_id: Source sandbox
        status: Current review status
        risk_level: Risk classification (low, medium, high)
        created_at: When review was created
        updated_at: When review was last updated
        expires_at: Review expiration time
        artifact_content: Artifact content/metadata
        decisions: Review decisions made
        required_approvals: Number of approvals needed
    """

    review_id: str = Field(..., description="Review identifier")
    artifact_id: str = Field(..., description="Artifact identifier")
    artifact_type: str = Field(..., description="Artifact type")
    sandbox_id: str = Field(..., description="Source sandbox")

    status: ReviewStatus = Field(
        default=ReviewStatus.PENDING, description="Review status"
    )

    risk_level: str = Field(
        default="medium", description="Risk level (low, medium, high)"
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    expires_at: datetime | None = Field(None, description="Expiration timestamp")

    artifact_content: dict[str, Any] = Field(
        default_factory=dict, description="Artifact content"
    )

    decisions: list[ReviewDecision] = Field(
        default_factory=list, description="Review decisions"
    )

    required_approvals: int = Field(default=1, ge=1, description="Required approvals")

    def approval_count(self) -> int:
        """Count approvals.

        Returns:
            Number of approve decisions
        """
        return sum(1 for d in self.decisions if d.decision == "approve")

    def rejection_count(self) -> int:
        """Count rejections.

        Returns:
            Number of reject decisions
        """
        return sum(1 for d in self.decisions if d.decision == "reject")

    def is_approved(self) -> bool:
        """Check if review is approved.

        Returns:
            True if sufficient approvals, False otherwise
        """
        return self.approval_count() >= self.required_approvals

    def is_rejected(self) -> bool:
        """Check if review is rejected.

        Returns:
            True if any rejection, False otherwise
        """
        return self.rejection_count() > 0

    def is_expired(self) -> bool:
        """Check if review is expired.

        Returns:
            True if past expiration time, False otherwise
        """
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "review_id": "01HWXYZ123",
                    "artifact_id": "file-456",
                    "artifact_type": "file_change",
                    "sandbox_id": "sandbox-789",
                    "status": "pending",
                    "risk_level": "high",
                    "artifact_content": {
                        "path": "/etc/passwd",
                        "operation": "write",
                    },
                }
            ]
        }
    }
