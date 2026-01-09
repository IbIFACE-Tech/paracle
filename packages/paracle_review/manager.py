"""Review manager for artifact approval workflow."""

import fnmatch
import logging
from datetime import datetime, timedelta

from paracle_domain.models import generate_id

from paracle_review.config import ReviewConfig
from paracle_review.exceptions import (
    ReviewAlreadyDecidedError,
    ReviewError,
    ReviewNotFoundError,
    ReviewTimeoutError,
)
from paracle_review.models import ArtifactReview, ReviewDecision, ReviewStatus

logger = logging.getLogger(__name__)


class ReviewManager:
    """Manages artifact review workflow.

    Handles review creation, approval/rejection, and policy enforcement.

    Attributes:
        config: Review configuration
        reviews: Active reviews by ID
    """

    def __init__(self, config: ReviewConfig | None = None):
        """Initialize review manager.

        Args:
            config: Review configuration
        """
        self.config = config or ReviewConfig()
        self.reviews: dict[str, ArtifactReview] = {}

    async def create_review(
        self,
        artifact_id: str,
        artifact_type: str,
        sandbox_id: str,
        artifact_content: dict | None = None,
        risk_level: str | None = None,
    ) -> str:
        """Create artifact review request.

        Args:
            artifact_id: Artifact identifier
            artifact_type: Type of artifact
            sandbox_id: Source sandbox
            artifact_content: Artifact content/metadata
            risk_level: Override risk level (auto-detected if None)

        Returns:
            Review ID

        Raises:
            ReviewError: If review creation fails
        """
        if not self.config.policy.enabled:
            raise ReviewError("Review system is disabled")

        # Check if review is needed
        if not await self._should_review(artifact_type, artifact_content or {}):
            raise ReviewError("Review not required for this artifact")

        # Generate review ID
        review_id = generate_id("review")

        # Detect risk level if not provided
        if not risk_level:
            risk_level = self._assess_risk(artifact_type, artifact_content or {})

        # Calculate expiration
        expires_at = None
        if self.config.policy.review_timeout_hours:
            expires_at = datetime.utcnow() + timedelta(
                hours=self.config.policy.review_timeout_hours
            )

        # Create review
        review = ArtifactReview(
            review_id=review_id,
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            sandbox_id=sandbox_id,
            risk_level=risk_level,
            artifact_content=artifact_content or {},
            required_approvals=self.config.policy.min_approvals,
            expires_at=expires_at,
        )

        # Store review
        self.reviews[review_id] = review

        logger.info(
            f"Created review {review_id} for {artifact_type} "
            f"(risk: {risk_level}, approvals: {self.config.policy.min_approvals})"
        )

        # Send notification
        if self.config.notify_on_review:
            await self._notify_review_created(review)

        # Auto-approve if policy allows
        if self.config.policy.auto_approve_low_risk and risk_level == "low":
            await self.approve(review_id, reviewer="system")
            logger.info(f"Auto-approved low-risk review {review_id}")

        return review_id

    async def approve(
        self,
        review_id: str,
        reviewer: str,
        comment: str | None = None,
    ) -> None:
        """Approve artifact review.

        Args:
            review_id: Review to approve
            reviewer: Who is approving
            comment: Optional approval comment

        Raises:
            ReviewNotFoundError: If review not found
            ReviewAlreadyDecidedError: If already decided
        """
        review = self.reviews.get(review_id)
        if not review:
            raise ReviewNotFoundError(f"Review not found: {review_id}", review_id)

        # Check if already decided
        if review.status != ReviewStatus.PENDING:
            raise ReviewAlreadyDecidedError(
                f"Review already {review.status.value}",
                review_id,
            )

        # Check if expired
        if review.is_expired():
            review.status = ReviewStatus.TIMEOUT
            raise ReviewTimeoutError(
                "Review has expired",
                review_id,
            )

        # Add approval decision
        decision = ReviewDecision(
            reviewer=reviewer,
            decision="approve",
            comment=comment,
        )
        review.decisions.append(decision)
        review.updated_at = datetime.utcnow()

        # Check if enough approvals
        if review.is_approved():
            review.status = ReviewStatus.APPROVED
            logger.info(
                f"Review {review_id} approved by {reviewer} "
                f"({review.approval_count()}/{review.required_approvals})"
            )
        else:
            logger.info(
                f"Review {review_id} partially approved by {reviewer} "
                f"({review.approval_count()}/{review.required_approvals})"
            )

    async def reject(
        self,
        review_id: str,
        reviewer: str,
        comment: str | None = None,
    ) -> None:
        """Reject artifact review.

        Args:
            review_id: Review to reject
            reviewer: Who is rejecting
            comment: Optional rejection comment

        Raises:
            ReviewNotFoundError: If review not found
            ReviewAlreadyDecidedError: If already decided
        """
        review = self.reviews.get(review_id)
        if not review:
            raise ReviewNotFoundError(f"Review not found: {review_id}", review_id)

        if review.status != ReviewStatus.PENDING:
            raise ReviewAlreadyDecidedError(
                f"Review already {review.status.value}",
                review_id,
            )

        # Add rejection decision
        decision = ReviewDecision(
            reviewer=reviewer,
            decision="reject",
            comment=comment,
        )
        review.decisions.append(decision)
        review.status = ReviewStatus.REJECTED
        review.updated_at = datetime.utcnow()

        logger.info(f"Review {review_id} rejected by {reviewer}")

    async def cancel(self, review_id: str) -> None:
        """Cancel review.

        Args:
            review_id: Review to cancel

        Raises:
            ReviewNotFoundError: If review not found
        """
        review = self.reviews.get(review_id)
        if not review:
            raise ReviewNotFoundError(f"Review not found: {review_id}", review_id)

        review.status = ReviewStatus.CANCELLED
        review.updated_at = datetime.utcnow()

        logger.info(f"Review {review_id} cancelled")

    async def get_review(self, review_id: str) -> ArtifactReview:
        """Get review by ID.

        Args:
            review_id: Review identifier

        Returns:
            ArtifactReview instance

        Raises:
            ReviewNotFoundError: If review not found
        """
        review = self.reviews.get(review_id)
        if not review:
            raise ReviewNotFoundError(f"Review not found: {review_id}", review_id)

        # Check and update if expired
        if review.status == ReviewStatus.PENDING and review.is_expired():
            review.status = ReviewStatus.TIMEOUT
            review.updated_at = datetime.utcnow()

        return review

    def list_reviews(
        self,
        status: ReviewStatus | None = None,
        sandbox_id: str | None = None,
    ) -> list[ArtifactReview]:
        """List reviews.

        Args:
            status: Filter by status
            sandbox_id: Filter by sandbox

        Returns:
            List of reviews
        """
        reviews = list(self.reviews.values())

        if status:
            reviews = [r for r in reviews if r.status == status]

        if sandbox_id:
            reviews = [r for r in reviews if r.sandbox_id == sandbox_id]

        return reviews

    def get_pending_count(self, sandbox_id: str | None = None) -> int:
        """Get count of pending reviews.

        Args:
            sandbox_id: Filter by sandbox

        Returns:
            Number of pending reviews
        """
        reviews = self.list_reviews(status=ReviewStatus.PENDING, sandbox_id=sandbox_id)
        return len(reviews)

    async def _should_review(
        self,
        artifact_type: str,
        artifact_content: dict,
    ) -> bool:
        """Check if artifact should be reviewed.

        Args:
            artifact_type: Artifact type
            artifact_content: Artifact content

        Returns:
            True if review is needed, False otherwise
        """
        trigger_mode = self.config.policy.trigger_mode

        if trigger_mode == "all_artifacts":
            return True

        if trigger_mode == "manual":
            return False

        # High-risk only mode - check patterns
        risk_level = self._assess_risk(artifact_type, artifact_content)
        return risk_level in ["medium", "high"]

    def _assess_risk(
        self,
        artifact_type: str,
        artifact_content: dict,
    ) -> str:
        """Assess artifact risk level.

        Args:
            artifact_type: Artifact type
            artifact_content: Artifact content

        Returns:
            Risk level: low, medium, high
        """
        # Check against high-risk patterns
        for pattern in self.config.policy.high_risk_patterns:
            # Check artifact content for pattern matches
            for value in artifact_content.values():
                if isinstance(value, str):
                    if fnmatch.fnmatch(value, pattern) or pattern in value:
                        return "high"

        # Medium risk for write operations
        if artifact_type in ["file_change", "command_execution"]:
            operation = artifact_content.get("operation", "")
            if operation in ["write", "delete", "execute"]:
                return "medium"

        return "low"

    async def _notify_review_created(self, review: ArtifactReview) -> None:
        """Send notification for new review.

        Args:
            review: Review that was created
        """
        message = (
            f"Review requested: {review.artifact_type} "
            f"(ID: {review.review_id}, Risk: {review.risk_level})"
        )

        for channel in self.config.notification_channels:
            if channel == "log":
                logger.info(f"[REVIEW] {message}")
            # Future: Add email, Slack, etc.

    async def cleanup_old_reviews(self, days: int = 7) -> int:
        """Clean up old completed reviews.

        Args:
            days: Delete reviews older than this many days

        Returns:
            Number of reviews deleted
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        deleted = 0

        for review_id, review in list(self.reviews.items()):
            if (
                review.status
                in [ReviewStatus.APPROVED, ReviewStatus.REJECTED, ReviewStatus.TIMEOUT]
                and review.updated_at < cutoff
            ):
                self.reviews.pop(review_id)
                deleted += 1

        logger.info(f"Cleaned up {deleted} old reviews")
        return deleted
