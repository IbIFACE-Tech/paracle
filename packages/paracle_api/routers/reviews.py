"""REST API router for artifact review workflow."""

import logging

from fastapi import APIRouter, HTTPException, status
from paracle_review import ReviewManager
from paracle_review.exceptions import (
    ReviewAlreadyDecidedError,
    ReviewNotFoundError,
    ReviewTimeoutError,
)
from paracle_review.models import ReviewStatus

from paracle_api.schemas.reviews import (
    ApprovalRequest,
    ReviewCreateRequest,
    ReviewListResponse,
    ReviewResponse,
    ReviewStatsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reviews", tags=["reviews"])

# Global review manager
_review_manager: ReviewManager | None = None


def get_review_manager() -> ReviewManager:
    """Get or create review manager singleton.

    Returns:
        ReviewManager instance
    """
    global _review_manager
    if _review_manager is None:
        _review_manager = ReviewManager()
    return _review_manager


@router.post(
    "/",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create artifact review",
    description="Create a new review request for an artifact",
    operation_id="createReview",
)
async def create_review(request: ReviewCreateRequest) -> ReviewResponse:
    """Create artifact review request."""
    manager = get_review_manager()

    try:
        review_id = await manager.create_review(
            artifact_id=request.artifact_id,
            artifact_type=request.artifact_type,
            sandbox_id=request.sandbox_id,
            artifact_content=request.artifact_content,
            risk_level=request.risk_level,
        )

        review = await manager.get_review(review_id)

        return ReviewResponse(
            review_id=review.review_id,
            artifact_id=review.artifact_id,
            artifact_type=review.artifact_type,
            sandbox_id=review.sandbox_id,
            status=review.status.value,
            risk_level=review.risk_level,
            created_at=review.created_at.isoformat(),
            updated_at=review.updated_at.isoformat(),
            expires_at=review.expires_at.isoformat() if review.expires_at else None,
            artifact_content=review.artifact_content,
            decisions=[
                {
                    "reviewer": d.reviewer,
                    "decision": d.decision,
                    "timestamp": d.timestamp.isoformat(),
                    "comment": d.comment,
                }
                for d in review.decisions
            ],
            required_approvals=review.required_approvals,
            approval_count=review.approval_count(),
        )

    except Exception as e:
        logger.error(f"Failed to create review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create review: {str(e)}",
        )


@router.get(
    "/{review_id}",
    response_model=ReviewResponse,
    summary="Get review",
    description="Get review details by ID",
    operation_id="getReview",
)
async def get_review(review_id: str) -> ReviewResponse:
    """Get review by ID."""
    manager = get_review_manager()

    try:
        review = await manager.get_review(review_id)

        return ReviewResponse(
            review_id=review.review_id,
            artifact_id=review.artifact_id,
            artifact_type=review.artifact_type,
            sandbox_id=review.sandbox_id,
            status=review.status.value,
            risk_level=review.risk_level,
            created_at=review.created_at.isoformat(),
            updated_at=review.updated_at.isoformat(),
            expires_at=review.expires_at.isoformat() if review.expires_at else None,
            artifact_content=review.artifact_content,
            decisions=[
                {
                    "reviewer": d.reviewer,
                    "decision": d.decision,
                    "timestamp": d.timestamp.isoformat(),
                    "comment": d.comment,
                }
                for d in review.decisions
            ],
            required_approvals=review.required_approvals,
            approval_count=review.approval_count(),
        )

    except ReviewNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review not found: {review_id}",
        )
    except Exception as e:
        logger.error(f"Failed to get review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/",
    response_model=ReviewListResponse,
    summary="List reviews",
    description="List reviews with optional filters",
    operation_id="listReviews",
)
async def list_reviews(
    status_filter: str | None = None,
    sandbox_id: str | None = None,
) -> ReviewListResponse:
    """List reviews with filters."""
    manager = get_review_manager()

    try:
        # Parse status filter
        status_enum = None
        if status_filter:
            try:
                status_enum = ReviewStatus(status_filter)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}",
                )

        reviews = manager.list_reviews(
            status=status_enum,
            sandbox_id=sandbox_id,
        )

        return ReviewListResponse(
            reviews=[
                {
                    "review_id": r.review_id,
                    "artifact_id": r.artifact_id,
                    "artifact_type": r.artifact_type,
                    "sandbox_id": r.sandbox_id,
                    "status": r.status.value,
                    "risk_level": r.risk_level,
                    "created_at": r.created_at.isoformat(),
                    "updated_at": r.updated_at.isoformat(),
                    "expires_at": r.expires_at.isoformat() if r.expires_at else None,
                    "approval_count": r.approval_count(),
                    "required_approvals": r.required_approvals,
                }
                for r in reviews
            ],
            total=len(reviews),
        )

    except Exception as e:
        logger.error(f"Failed to list reviews: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/{review_id}/approve",
    response_model=ReviewResponse,
    summary="Approve review",
    description="Approve an artifact review",
    operation_id="approveReview",
)
async def approve_review(
    review_id: str,
    request: ApprovalRequest,
) -> ReviewResponse:
    """Approve review."""
    manager = get_review_manager()

    try:
        await manager.approve(
            review_id=review_id,
            reviewer=request.reviewer,
            comment=request.comment,
        )

        review = await manager.get_review(review_id)

        return ReviewResponse(
            review_id=review.review_id,
            artifact_id=review.artifact_id,
            artifact_type=review.artifact_type,
            sandbox_id=review.sandbox_id,
            status=review.status.value,
            risk_level=review.risk_level,
            created_at=review.created_at.isoformat(),
            updated_at=review.updated_at.isoformat(),
            expires_at=review.expires_at.isoformat() if review.expires_at else None,
            artifact_content=review.artifact_content,
            decisions=[
                {
                    "reviewer": d.reviewer,
                    "decision": d.decision,
                    "timestamp": d.timestamp.isoformat(),
                    "comment": d.comment,
                }
                for d in review.decisions
            ],
            required_approvals=review.required_approvals,
            approval_count=review.approval_count(),
        )

    except ReviewNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review not found: {review_id}",
        )
    except ReviewAlreadyDecidedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ReviewTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to approve review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/{review_id}/reject",
    response_model=ReviewResponse,
    summary="Reject review",
    description="Reject an artifact review",
    operation_id="rejectReview",
)
async def reject_review(
    review_id: str,
    request: ApprovalRequest,
) -> ReviewResponse:
    """Reject review."""
    manager = get_review_manager()

    try:
        await manager.reject(
            review_id=review_id,
            reviewer=request.reviewer,
            comment=request.comment,
        )

        review = await manager.get_review(review_id)

        return ReviewResponse(
            review_id=review.review_id,
            artifact_id=review.artifact_id,
            artifact_type=review.artifact_type,
            sandbox_id=review.sandbox_id,
            status=review.status.value,
            risk_level=review.risk_level,
            created_at=review.created_at.isoformat(),
            updated_at=review.updated_at.isoformat(),
            expires_at=review.expires_at.isoformat() if review.expires_at else None,
            artifact_content=review.artifact_content,
            decisions=[
                {
                    "reviewer": d.reviewer,
                    "decision": d.decision,
                    "timestamp": d.timestamp.isoformat(),
                    "comment": d.comment,
                }
                for d in review.decisions
            ],
            required_approvals=review.required_approvals,
            approval_count=review.approval_count(),
        )

    except ReviewNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review not found: {review_id}",
        )
    except ReviewAlreadyDecidedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to reject review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel review",
    description="Cancel a pending review",
    operation_id="cancelReview",
)
async def cancel_review(review_id: str) -> None:
    """Cancel review."""
    manager = get_review_manager()

    try:
        await manager.cancel(review_id)

    except ReviewNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review not found: {review_id}",
        )
    except Exception as e:
        logger.error(f"Failed to cancel review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/stats/summary",
    response_model=ReviewStatsResponse,
    summary="Get review statistics",
    description="Get aggregate review statistics",
    operation_id="getReviewStats",
)
async def get_review_stats() -> ReviewStatsResponse:
    """Get review statistics."""
    manager = get_review_manager()

    try:
        all_reviews = manager.list_reviews()

        stats = {
            "total": len(all_reviews),
            "pending": len(
                [r for r in all_reviews if r.status == ReviewStatus.PENDING]
            ),
            "approved": len(
                [r for r in all_reviews if r.status == ReviewStatus.APPROVED]
            ),
            "rejected": len(
                [r for r in all_reviews if r.status == ReviewStatus.REJECTED]
            ),
            "timeout": len(
                [r for r in all_reviews if r.status == ReviewStatus.TIMEOUT]
            ),
            "by_risk_level": {
                "low": len([r for r in all_reviews if r.risk_level == "low"]),
                "medium": len([r for r in all_reviews if r.risk_level == "medium"]),
                "high": len([r for r in all_reviews if r.risk_level == "high"]),
            },
        }

        return ReviewStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
