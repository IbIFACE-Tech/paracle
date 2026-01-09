"""Human-in-the-Loop approval management for workflow orchestration.

This module provides the ApprovalManager for managing approval requests
when workflows require human oversight (ISO 42001 compliance).

Usage:
    >>> manager = ApprovalManager(event_bus)
    >>> request = await manager.create_request(
    ...     workflow_id="wf_123",
    ...     execution_id="exec_456",
    ...     step_id="review",
    ...     step_name="Code Review",
    ...     agent_name="code-reviewer",
    ...     context={"output": "Analysis complete"},
    ... )
    >>> # Later, human approves
    >>> await manager.approve(request.id, approver="user@example.com")
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from paracle_core.compat import UTC, datetime, timedelta
from paracle_domain.models import (
    ApprovalConfig,
    ApprovalPriority,
    ApprovalRequest,
    ApprovalStatus,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from paracle_events import EventBus


class ApprovalError(Exception):
    """Base exception for approval errors."""

    def __init__(self, message: str, *, code: str = "APPROVAL_ERROR") -> None:
        super().__init__(message)
        self.code = code


class ApprovalNotFoundError(ApprovalError):
    """Raised when approval request is not found."""

    def __init__(self, approval_id: str) -> None:
        super().__init__(
            f"Approval request not found: {approval_id}",
            code="APPROVAL_NOT_FOUND",
        )
        self.approval_id = approval_id


class ApprovalAlreadyDecidedError(ApprovalError):
    """Raised when trying to decide on already-decided approval."""

    def __init__(self, approval_id: str, status: ApprovalStatus) -> None:
        super().__init__(
            f"Approval {approval_id} already decided: {status.value}",
            code="APPROVAL_ALREADY_DECIDED",
        )
        self.approval_id = approval_id
        self.status = status


class ApprovalTimeoutError(ApprovalError):
    """Raised when approval times out."""

    def __init__(self, approval_id: str, timeout_seconds: int) -> None:
        super().__init__(
            f"Approval {approval_id} timed out after {timeout_seconds}s",
            code="APPROVAL_TIMEOUT",
        )
        self.approval_id = approval_id
        self.timeout_seconds = timeout_seconds


class UnauthorizedApproverError(ApprovalError):
    """Raised when approver is not authorized."""

    def __init__(self, approver: str, approval_id: str) -> None:
        super().__init__(
            f"User {approver} not authorized to approve {approval_id}",
            code="UNAUTHORIZED_APPROVER",
        )
        self.approver = approver
        self.approval_id = approval_id


class ApprovalManager:
    """Manages approval requests for human-in-the-loop workflows.

    The ApprovalManager:
    - Creates and tracks approval requests
    - Manages approval lifecycle (pending → approved/rejected/expired)
    - Handles approval timeouts
    - Emits events for observability
    - Supports webhook notifications (future)

    Approval requests are stored in-memory by default.
    For persistence, inject a repository.

    Example:
        >>> manager = ApprovalManager(event_bus)
        >>>
        >>> # Create approval request
        >>> request = await manager.create_request(
        ...     workflow_id="wf_123",
        ...     execution_id="exec_456",
        ...     step_id="deploy",
        ...     step_name="Production Deployment",
        ...     agent_name="deployer",
        ...     context={"changes": ["file1.py", "file2.py"]},
        ...     config=ApprovalConfig(
        ...         approvers=["admin@example.com"],
        ...         timeout_seconds=1800,  # 30 minutes
        ...         priority=ApprovalPriority.HIGH,
        ...     ),
        ... )
        >>>
        >>> # Wait for approval (blocks until decided or timeout)
        >>> is_approved = await manager.wait_for_decision(request.id)
    """

    def __init__(
        self,
        event_bus: EventBus | None = None,
        on_approval_created: Callable[[ApprovalRequest], None] | None = None,
        on_approval_decided: Callable[[ApprovalRequest], None] | None = None,
        auto_approve: bool = False,
        auto_approver: str = "system:auto",
    ) -> None:
        """Initialize the approval manager.

        Args:
            event_bus: Optional event bus for publishing approval events.
            on_approval_created: Callback when approval is created.
            on_approval_decided: Callback when approval is decided.
            auto_approve: If True, automatically approve all requests (YOLO mode).
            auto_approver: Approver name for auto-approvals.
        """
        self._event_bus = event_bus
        self._on_approval_created = on_approval_created
        self._on_approval_decided = on_approval_decided
        self.auto_approve = auto_approve
        self.auto_approver = auto_approver

        # In-memory storage (can be replaced with repository)
        self._pending_approvals: dict[str, ApprovalRequest] = {}
        self._decided_approvals: dict[str, ApprovalRequest] = {}

        # Condition variables for waiting on decisions
        self._decision_events: dict[str, asyncio.Event] = {}

    async def create_request(
        self,
        workflow_id: str,
        execution_id: str,
        step_id: str,
        step_name: str,
        agent_name: str,
        context: dict[str, Any] | None = None,
        config: ApprovalConfig | None = None,
        priority: ApprovalPriority = ApprovalPriority.MEDIUM,
        metadata: dict[str, Any] | None = None,
    ) -> ApprovalRequest:
        """Create a new approval request.

        Args:
            workflow_id: ID of the workflow requesting approval.
            execution_id: ID of the current execution.
            step_id: ID of the step requiring approval.
            step_name: Human-readable step name.
            agent_name: Name of the agent that produced output.
            context: Context for approval decision (step output, inputs).
            config: Approval configuration (approvers, timeout, etc.).
            priority: Priority level for the request.
            metadata: Additional metadata.

        Returns:
            Created ApprovalRequest in PENDING status.
        """
        config = config or ApprovalConfig(required=True)

        # Calculate expiration time
        timeout = config.timeout_seconds
        expires_at = datetime.now(UTC) + timedelta(seconds=timeout)

        request = ApprovalRequest(
            workflow_id=workflow_id,
            execution_id=execution_id,
            step_id=step_id,
            step_name=step_name,
            agent_name=agent_name,
            context=context or {},
            config=config,
            priority=priority,
            expires_at=expires_at,
            metadata=metadata or {},
        )

        # Store in pending
        self._pending_approvals[request.id] = request

        # Create decision event for waiting
        self._decision_events[request.id] = asyncio.Event()

        # Emit event
        await self._emit_event("approval.created", request)

        # Call callback
        if self._on_approval_created:
            self._on_approval_created(request)

        # Auto-approve if YOLO mode enabled
        if self.auto_approve:
            await self._auto_approve_request(request)

        return request

    async def approve(
        self,
        approval_id: str,
        approver: str,
        reason: str | None = None,
    ) -> ApprovalRequest:
        """Approve a pending request.

        Args:
            approval_id: ID of the approval request.
            approver: ID/email of the approver.
            reason: Optional reason for approval.

        Returns:
            Updated ApprovalRequest with APPROVED status.

        Raises:
            ApprovalNotFoundError: If request not found.
            ApprovalAlreadyDecidedError: If already decided.
            UnauthorizedApproverError: If approver not authorized.
        """
        request = self._get_pending_or_raise(approval_id)

        # Check authorization
        self._check_authorization(request, approver)

        # Check if reason required
        if request.config.reason_required and not reason:
            raise ApprovalError(
                "Reason required for this approval",
                code="REASON_REQUIRED",
            )

        # Approve
        request.approve(approver, reason)

        # Move to decided
        self._move_to_decided(request)

        # Emit event
        await self._emit_event("approval.approved", request)

        # Signal waiting coroutines
        self._signal_decision(request.id)

        # Call callback
        if self._on_approval_decided:
            self._on_approval_decided(request)

        return request

    async def _auto_approve_request(self, request: ApprovalRequest) -> None:
        """Automatically approve a request in YOLO mode.

        Args:
            request: Approval request to auto-approve.
        """
        # Approve the request
        request.approve(
            approver=self.auto_approver,
            reason="Auto-approved: YOLO mode enabled",
        )

        # Move to decided
        self._move_to_decided(request)

        # Emit special event for audit trail
        await self._emit_event("approval.auto_approved", request)

        # Signal waiting coroutines
        self._signal_decision(request.id)

        # Call callback
        if self._on_approval_decided:
            self._on_approval_decided(request)

    async def reject(
        self,
        approval_id: str,
        approver: str,
        reason: str | None = None,
    ) -> ApprovalRequest:
        """Reject a pending request.

        Args:
            approval_id: ID of the approval request.
            approver: ID/email of the approver.
            reason: Optional reason for rejection.

        Returns:
            Updated ApprovalRequest with REJECTED status.

        Raises:
            ApprovalNotFoundError: If request not found.
            ApprovalAlreadyDecidedError: If already decided.
            UnauthorizedApproverError: If approver not authorized.
        """
        request = self._get_pending_or_raise(approval_id)

        # Check authorization
        self._check_authorization(request, approver)

        # Check if reason required
        if request.config.reason_required and not reason:
            raise ApprovalError(
                "Reason required for this rejection",
                code="REASON_REQUIRED",
            )

        # Reject
        request.reject(approver, reason)

        # Move to decided
        self._move_to_decided(request)

        # Emit event
        await self._emit_event("approval.rejected", request)

        # Signal waiting coroutines
        self._signal_decision(request.id)

        # Call callback
        if self._on_approval_decided:
            self._on_approval_decided(request)

        return request

    async def cancel(self, approval_id: str) -> ApprovalRequest:
        """Cancel a pending request (e.g., workflow cancelled).

        Args:
            approval_id: ID of the approval request.

        Returns:
            Updated ApprovalRequest with CANCELLED status.
        """
        request = self._get_pending_or_raise(approval_id)

        request.cancel()
        self._move_to_decided(request)

        await self._emit_event("approval.cancelled", request)
        self._signal_decision(request.id)

        return request

    async def wait_for_decision(
        self,
        approval_id: str,
        timeout_seconds: float | None = None,
    ) -> bool:
        """Wait for approval decision.

        Blocks until the approval is decided or timeout.

        Args:
            approval_id: ID of the approval request.
            timeout_seconds: Override timeout (uses config timeout if None).

        Returns:
            True if approved, False otherwise.

        Raises:
            ApprovalTimeoutError: If timeout expires.
            ApprovalNotFoundError: If request not found.
        """
        # Check if already decided
        if approval_id in self._decided_approvals:
            return self._decided_approvals[approval_id].is_approved

        # Get pending request
        request = self._pending_approvals.get(approval_id)
        if request is None:
            raise ApprovalNotFoundError(approval_id)

        # Determine timeout
        if timeout_seconds is None:
            timeout_seconds = request.config.timeout_seconds

        # Get or create event
        event = self._decision_events.get(approval_id)
        if event is None:
            event = asyncio.Event()
            self._decision_events[approval_id] = event

        try:
            # Wait for decision with timeout
            await asyncio.wait_for(event.wait(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            # Handle timeout
            await self._handle_timeout(request)
            raise ApprovalTimeoutError(approval_id, int(timeout_seconds))

        # Get final status
        decided = self._decided_approvals.get(approval_id)
        if decided is None:
            # This shouldn't happen, but handle gracefully
            raise ApprovalError(
                f"Approval {approval_id} in unexpected state",
                code="UNEXPECTED_STATE",
            )

        return decided.is_approved

    async def _handle_timeout(self, request: ApprovalRequest) -> None:
        """Handle approval timeout.

        Args:
            request: The approval request that timed out.
        """
        if request.id not in self._pending_approvals:
            return  # Already decided

        request.expire()
        self._move_to_decided(request)

        await self._emit_event("approval.expired", request)
        self._signal_decision(request.id)

        if self._on_approval_decided:
            self._on_approval_decided(request)

    def get_request(self, approval_id: str) -> ApprovalRequest | None:
        """Get approval request by ID.

        Args:
            approval_id: ID of the approval request.

        Returns:
            ApprovalRequest or None if not found.
        """
        return self._pending_approvals.get(approval_id) or self._decided_approvals.get(
            approval_id
        )

    def list_pending(
        self,
        workflow_id: str | None = None,
        priority: ApprovalPriority | None = None,
    ) -> list[ApprovalRequest]:
        """List pending approval requests.

        Args:
            workflow_id: Filter by workflow ID.
            priority: Filter by priority.

        Returns:
            List of pending ApprovalRequests, sorted by priority and time.
        """
        requests = list(self._pending_approvals.values())

        if workflow_id:
            requests = [r for r in requests if r.workflow_id == workflow_id]

        if priority:
            requests = [r for r in requests if r.priority == priority]

        # Sort by priority (CRITICAL first) then by creation time
        priority_order = {
            ApprovalPriority.CRITICAL: 0,
            ApprovalPriority.HIGH: 1,
            ApprovalPriority.MEDIUM: 2,
            ApprovalPriority.LOW: 3,
        }
        return sorted(
            requests,
            key=lambda r: (priority_order.get(r.priority, 99), r.created_at),
        )

    def list_decided(
        self,
        workflow_id: str | None = None,
        status: ApprovalStatus | None = None,
        limit: int = 100,
    ) -> list[ApprovalRequest]:
        """List decided approval requests.

        Args:
            workflow_id: Filter by workflow ID.
            status: Filter by status.
            limit: Maximum number of results.

        Returns:
            List of decided ApprovalRequests, most recent first.
        """
        requests = list(self._decided_approvals.values())

        if workflow_id:
            requests = [r for r in requests if r.workflow_id == workflow_id]

        if status:
            requests = [r for r in requests if r.status == status]

        # Sort by decision time, most recent first
        requests = sorted(
            requests,
            key=lambda r: r.decided_at or r.created_at,
            reverse=True,
        )

        return requests[:limit]

    def get_stats(self) -> dict[str, Any]:
        """Get approval statistics.

        Returns:
            Dictionary with approval statistics.
        """
        decided = list(self._decided_approvals.values())
        return {
            "pending_count": len(self._pending_approvals),
            "decided_count": len(self._decided_approvals),
            "approved_count": sum(1 for r in decided if r.is_approved),
            "rejected_count": sum(
                1 for r in decided if r.status == ApprovalStatus.REJECTED
            ),
            "expired_count": sum(
                1 for r in decided if r.status == ApprovalStatus.EXPIRED
            ),
            "cancelled_count": sum(
                1 for r in decided if r.status == ApprovalStatus.CANCELLED
            ),
        }

    def _get_pending_or_raise(self, approval_id: str) -> ApprovalRequest:
        """Get pending request or raise appropriate error."""
        # Check if already decided
        if approval_id in self._decided_approvals:
            decided = self._decided_approvals[approval_id]
            raise ApprovalAlreadyDecidedError(approval_id, decided.status)

        # Get pending
        request = self._pending_approvals.get(approval_id)
        if request is None:
            raise ApprovalNotFoundError(approval_id)

        return request

    def _check_authorization(self, request: ApprovalRequest, approver: str) -> None:
        """Check if approver is authorized."""
        # If no approvers specified, anyone can approve
        if not request.config.approvers:
            return

        if approver not in request.config.approvers:
            raise UnauthorizedApproverError(approver, request.id)

    def _move_to_decided(self, request: ApprovalRequest) -> None:
        """Move request from pending to decided."""
        self._pending_approvals.pop(request.id, None)
        self._decided_approvals[request.id] = request

    def _signal_decision(self, approval_id: str) -> None:
        """Signal that a decision has been made and clean up event."""
        event = self._decision_events.pop(approval_id, None)
        if event:
            event.set()

    async def _emit_event(
        self,
        event_type: str,
        request: ApprovalRequest,
    ) -> None:
        """Emit an approval event."""
        if self._event_bus is None:
            return

        from paracle_events.events import Event, EventType

        # Map approval events to EventType enum
        # Use closest matching workflow event types since approval events
        # don't have dedicated enum values
        type_mapping = {
            "approval.created": EventType.WORKFLOW_STEP_STARTED,
            "approval.approved": EventType.WORKFLOW_STEP_COMPLETED,
            "approval.rejected": EventType.WORKFLOW_STEP_FAILED,
            "approval.cancelled": EventType.WORKFLOW_FAILED,
            "approval.expired": EventType.WORKFLOW_FAILED,
        }

        mapped_type = type_mapping.get(event_type, EventType.WORKFLOW_STEP_STARTED)

        event = Event(
            type=mapped_type,
            source="approval_manager",
            payload={
                "approval_event": event_type,  # Store original event type
                "approval_id": request.id,
                "workflow_id": request.workflow_id,
                "execution_id": request.execution_id,
                "step_id": request.step_id,
                "step_name": request.step_name,
                "status": request.status.value,
                "priority": request.priority.value,
                "approver": request.decided_by,
                "reason": request.decision_reason,
            },
        )
        await self._event_bus.publish_async(event)
