"""Approval API endpoints for Human-in-the-Loop workflows.

This module provides REST API endpoints for managing approval requests,
enabling human oversight of AI agent decisions (ISO 42001 compliance).

Endpoints:
    GET  /approvals/pending     - List pending approval requests
    GET  /approvals/decided     - List decided approval requests
    GET  /approvals/{id}        - Get approval request by ID
    POST /approvals/{id}/approve - Approve a request
    POST /approvals/{id}/reject  - Reject a request
    POST /approvals/{id}/cancel  - Cancel a request
    GET  /approvals/stats       - Get approval statistics
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from paracle_domain.models import ApprovalPriority, ApprovalStatus
from paracle_orchestration.approval import (
    ApprovalAlreadyDecidedError,
    ApprovalError,
    ApprovalManager,
    ApprovalNotFoundError,
    UnauthorizedApproverError,
)
from pydantic import BaseModel, Field

router = APIRouter(prefix="/approvals", tags=["approvals"])

# Global approval manager (in production, use dependency injection)
_approval_manager: ApprovalManager | None = None


def get_approval_manager() -> ApprovalManager:
    """Get the global approval manager."""
    global _approval_manager
    if _approval_manager is None:
        _approval_manager = ApprovalManager()
    return _approval_manager


def set_approval_manager(manager: ApprovalManager) -> None:
    """Set the global approval manager (for testing)."""
    global _approval_manager
    _approval_manager = manager


# =============================================================================
# Request/Response Models
# =============================================================================


class ApprovalRequestResponse(BaseModel):
    """Response model for approval request."""

    id: str
    workflow_id: str
    execution_id: str
    step_id: str
    step_name: str
    agent_name: str
    context: dict[str, Any]
    status: str
    priority: str
    created_at: str
    expires_at: str | None
    decided_at: str | None
    decided_by: str | None
    decision_reason: str | None


class ApproveRequest(BaseModel):
    """Request body for approving a request."""

    approver: str = Field(..., description="ID/email of the approver")
    reason: str | None = Field(None, description="Optional reason for approval")


class RejectRequest(BaseModel):
    """Request body for rejecting a request."""

    approver: str = Field(..., description="ID/email of the approver")
    reason: str | None = Field(None, description="Optional reason for rejection")


class ApprovalStatsResponse(BaseModel):
    """Response model for approval statistics."""

    pending_count: int
    decided_count: int
    approved_count: int
    rejected_count: int
    expired_count: int
    cancelled_count: int


class ApprovalListResponse(BaseModel):
    """Response model for approval list."""

    approvals: list[ApprovalRequestResponse]
    total: int


# =============================================================================
# Helper Functions
# =============================================================================


def _to_response(request: Any) -> ApprovalRequestResponse:
    """Convert domain ApprovalRequest to response model."""
    return ApprovalRequestResponse(
        id=request.id,
        workflow_id=request.workflow_id,
        execution_id=request.execution_id,
        step_id=request.step_id,
        step_name=request.step_name,
        agent_name=request.agent_name,
        context=request.context,
        status=request.status.value,
        priority=request.priority.value,
        created_at=request.created_at.isoformat(),
        expires_at=request.expires_at.isoformat() if request.expires_at else None,
        decided_at=request.decided_at.isoformat() if request.decided_at else None,
        decided_by=request.decided_by,
        decision_reason=request.decision_reason,
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.get(
    "/pending", response_model=ApprovalListResponse, operation_id="listPendingApprovals"
)
async def list_pending_approvals(
    workflow_id: str | None = None,
    priority: str | None = None,
    manager: ApprovalManager = Depends(get_approval_manager),
) -> ApprovalListResponse:
    """List pending approval requests.

    Args:
        workflow_id: Filter by workflow ID.
        priority: Filter by priority (low, medium, high, critical).

    Returns:
        List of pending approval requests, sorted by priority.
    """
    # Convert priority string to enum
    priority_enum = None
    if priority:
        try:
            priority_enum = ApprovalPriority(priority.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority: {priority}. Must be one of: low, medium, high, critical",
            )

    approvals = manager.list_pending(workflow_id=workflow_id, priority=priority_enum)
    return ApprovalListResponse(
        approvals=[_to_response(a) for a in approvals],
        total=len(approvals),
    )


@router.get(
    "/decided", response_model=ApprovalListResponse, operation_id="listDecidedApprovals"
)
async def list_decided_approvals(
    workflow_id: str | None = None,
    approval_status: str | None = None,
    limit: int = 100,
    manager: ApprovalManager = Depends(get_approval_manager),
) -> ApprovalListResponse:
    """List decided approval requests.

    Args:
        workflow_id: Filter by workflow ID.
        approval_status: Filter by status (approved, rejected, expired, cancelled).
        limit: Maximum number of results.

    Returns:
        List of decided approval requests, most recent first.
    """
    # Convert status string to enum
    status_enum = None
    if approval_status:
        try:
            status_enum = ApprovalStatus(approval_status.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {approval_status}",
            )

    approvals = manager.list_decided(
        workflow_id=workflow_id, status=status_enum, limit=limit
    )
    return ApprovalListResponse(
        approvals=[_to_response(a) for a in approvals],
        total=len(approvals),
    )


@router.get(
    "/stats", response_model=ApprovalStatsResponse, operation_id="getApprovalStats"
)
async def get_approval_stats(
    manager: ApprovalManager = Depends(get_approval_manager),
) -> ApprovalStatsResponse:
    """Get approval statistics.

    Returns:
        Statistics about pending and decided approvals.
    """
    stats = manager.get_stats()
    return ApprovalStatsResponse(**stats)


@router.get(
    "/{approval_id}", response_model=ApprovalRequestResponse, operation_id="getApproval"
)
async def get_approval(
    approval_id: str,
    manager: ApprovalManager = Depends(get_approval_manager),
) -> ApprovalRequestResponse:
    """Get approval request by ID.

    Args:
        approval_id: ID of the approval request.

    Returns:
        The approval request.

    Raises:
        404: If approval not found.
    """
    request = manager.get_request(approval_id)
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval not found: {approval_id}",
        )
    return _to_response(request)


@router.post(
    "/{approval_id}/approve",
    response_model=ApprovalRequestResponse,
    operation_id="approveRequest",
)
async def approve_request(
    approval_id: str,
    body: ApproveRequest,
    manager: ApprovalManager = Depends(get_approval_manager),
) -> ApprovalRequestResponse:
    """Approve a pending request.

    Args:
        approval_id: ID of the approval request.
        body: Approval details (approver, reason).

    Returns:
        The updated approval request.

    Raises:
        404: If approval not found.
        409: If already decided.
        403: If approver not authorized.
    """
    try:
        request = await manager.approve(approval_id, body.approver, body.reason)
        return _to_response(request)

    except ApprovalNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval not found: {approval_id}",
        )

    except ApprovalAlreadyDecidedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Approval already decided: {e.status.value}",
        )

    except UnauthorizedApproverError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User {body.approver} not authorized to approve this request",
        )

    except ApprovalError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{approval_id}/reject",
    response_model=ApprovalRequestResponse,
    operation_id="rejectRequest",
)
async def reject_request(
    approval_id: str,
    body: RejectRequest,
    manager: ApprovalManager = Depends(get_approval_manager),
) -> ApprovalRequestResponse:
    """Reject a pending request.

    Args:
        approval_id: ID of the approval request.
        body: Rejection details (approver, reason).

    Returns:
        The updated approval request.

    Raises:
        404: If approval not found.
        409: If already decided.
        403: If approver not authorized.
    """
    try:
        request = await manager.reject(approval_id, body.approver, body.reason)
        return _to_response(request)

    except ApprovalNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval not found: {approval_id}",
        )

    except ApprovalAlreadyDecidedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Approval already decided: {e.status.value}",
        )

    except UnauthorizedApproverError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User {body.approver} not authorized to reject this request",
        )

    except ApprovalError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{approval_id}/cancel",
    response_model=ApprovalRequestResponse,
    operation_id="cancelApproval",
)
async def cancel_request(
    approval_id: str,
    manager: ApprovalManager = Depends(get_approval_manager),
) -> ApprovalRequestResponse:
    """Cancel a pending request.

    Typically used when the parent workflow is cancelled.

    Args:
        approval_id: ID of the approval request.

    Returns:
        The updated approval request.

    Raises:
        404: If approval not found.
        409: If already decided.
    """
    try:
        request = await manager.cancel(approval_id)
        return _to_response(request)

    except ApprovalNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval not found: {approval_id}",
        )

    except ApprovalAlreadyDecidedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Approval already decided: {e.status.value}",
        )
