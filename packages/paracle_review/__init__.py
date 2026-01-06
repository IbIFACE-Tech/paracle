"""Paracle Review - Artifact review and approval workflow.

This package provides review workflows for artifacts generated during
sandbox execution, allowing human oversight and approval before
applying changes.

Components:
- ReviewManager: Manages review requests and approvals
- ArtifactReview: Review state and metadata
- ReviewPolicy: Review trigger policies

Example:
    ```python
    from paracle_review import ReviewManager, ReviewPolicy

    # Create review manager
    manager = ReviewManager()

    # Create review request for artifact
    review_id = await manager.create_review(
        artifact_id="file-123",
        artifact_type="file_change",
        content={"path": "/app/config.py", "changes": diff}
    )

    # Approve review
    await manager.approve(review_id, reviewer="user@example.com")
    ```
"""

from paracle_review.config import ReviewConfig, ReviewPolicy
from paracle_review.exceptions import ReviewError, ReviewNotFoundError
from paracle_review.manager import ReviewManager
from paracle_review.models import ArtifactReview, ReviewDecision, ReviewStatus

__all__ = [
    "ReviewManager",
    "ReviewConfig",
    "ReviewPolicy",
    "ArtifactReview",
    "ReviewStatus",
    "ReviewDecision",
    "ReviewError",
    "ReviewNotFoundError",
]
