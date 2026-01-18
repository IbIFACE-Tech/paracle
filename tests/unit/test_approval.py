"""Tests for Human-in-the-Loop approval system."""

import asyncio
from datetime import datetime

import pytest

from paracle_core.compat import UTC
from paracle_domain.models import (
    ApprovalConfig,
    ApprovalPriority,
    ApprovalRequest,
    ApprovalStatus,
    WorkflowStep,
)
from paracle_orchestration import ExecutionContext, ExecutionStatus
from paracle_orchestration.approval import (
    ApprovalAlreadyDecidedError,
    ApprovalManager,
    ApprovalNotFoundError,
    ApprovalTimeoutError,
    UnauthorizedApproverError,
)


class TestApprovalModels:
    """Tests for approval domain models."""

    def test_approval_config_defaults(self) -> None:
        """Test ApprovalConfig default values."""
        config = ApprovalConfig()
        assert config.required is False
        assert config.approvers == []
        assert config.timeout_seconds == 3600
        assert config.priority == ApprovalPriority.MEDIUM
        assert config.auto_reject_on_timeout is False
        assert config.reason_required is False

    def test_approval_config_custom(self) -> None:
        """Test ApprovalConfig with custom values."""
        config = ApprovalConfig(
            required=True,
            approvers=["admin@example.com", "manager@example.com"],
            timeout_seconds=1800,
            priority=ApprovalPriority.HIGH,
            auto_reject_on_timeout=True,
            reason_required=True,
        )
        assert config.required is True
        assert len(config.approvers) == 2
        assert config.timeout_seconds == 1800
        assert config.priority == ApprovalPriority.HIGH

    def test_approval_request_creation(self) -> None:
        """Test ApprovalRequest creation."""
        request = ApprovalRequest(
            workflow_id="wf_123",
            execution_id="exec_456",
            step_id="review",
            step_name="Code Review",
            agent_name="code-reviewer",
            context={"code": "print('hello')"},
        )
        assert request.id.startswith("approval_")
        assert request.workflow_id == "wf_123"
        assert request.status == ApprovalStatus.PENDING
        assert request.is_pending is True
        assert request.is_decided is False
        assert request.is_approved is False

    def test_approval_request_approve(self) -> None:
        """Test approving a request."""
        request = ApprovalRequest(
            workflow_id="wf_123",
            execution_id="exec_456",
            step_id="review",
            step_name="Code Review",
            agent_name="code-reviewer",
        )

        request.approve("admin@example.com", "LGTM")

        assert request.status == ApprovalStatus.APPROVED
        assert request.is_approved is True
        assert request.is_decided is True
        assert request.decided_by == "admin@example.com"
        assert request.decision_reason == "LGTM"
        assert request.decided_at is not None

    def test_approval_request_reject(self) -> None:
        """Test rejecting a request."""
        request = ApprovalRequest(
            workflow_id="wf_123",
            execution_id="exec_456",
            step_id="review",
            step_name="Code Review",
            agent_name="code-reviewer",
        )

        request.reject("admin@example.com", "Needs more tests")

        assert request.status == ApprovalStatus.REJECTED
        assert request.is_approved is False
        assert request.is_decided is True
        assert request.decision_reason == "Needs more tests"

    def test_approval_request_expire(self) -> None:
        """Test expiring a request."""
        request = ApprovalRequest(
            workflow_id="wf_123",
            execution_id="exec_456",
            step_id="review",
            step_name="Code Review",
            agent_name="code-reviewer",
        )

        request.expire()

        assert request.status == ApprovalStatus.EXPIRED
        assert request.is_decided is True
        assert request.is_approved is False

    def test_approval_request_cancel(self) -> None:
        """Test cancelling a request."""
        request = ApprovalRequest(
            workflow_id="wf_123",
            execution_id="exec_456",
            step_id="review",
            step_name="Code Review",
            agent_name="code-reviewer",
        )

        request.cancel()

        assert request.status == ApprovalStatus.CANCELLED
        assert request.is_decided is True

    def test_workflow_step_approval_fields(self) -> None:
        """Test WorkflowStep has approval fields."""
        step = WorkflowStep(
            id="step1",
            name="Deployment",
            agent="deployer",
            requires_approval=True,
            approval_config={
                "approvers": ["admin@example.com"],
                "timeout_seconds": 1800,
            },
        )
        assert step.requires_approval is True
        assert step.approval_config["approvers"] == ["admin@example.com"]

    def test_workflow_step_default_no_approval(self) -> None:
        """Test WorkflowStep defaults to no approval."""
        step = WorkflowStep(
            id="step1",
            name="Analysis",
            agent="analyzer",
        )
        assert step.requires_approval is False
        assert step.approval_config == {}


class TestApprovalManager:
    """Tests for ApprovalManager."""

    @pytest.fixture
    def manager(self) -> ApprovalManager:
        """Create a fresh ApprovalManager."""
        return ApprovalManager()

    @pytest.mark.asyncio
    async def test_create_request(self, manager: ApprovalManager) -> None:
        """Test creating an approval request."""
        request = await manager.create_request(
            workflow_id="wf_123",
            execution_id="exec_456",
            step_id="review",
            step_name="Code Review",
            agent_name="code-reviewer",
            context={"output": "Analysis complete"},
        )

        assert request.id.startswith("approval_")
        assert request.status == ApprovalStatus.PENDING
        assert request.expires_at is not None
        assert request.expires_at > datetime.now(UTC)

    @pytest.mark.asyncio
    async def test_approve_request(self, manager: ApprovalManager) -> None:
        """Test approving a request through manager."""
        request = await manager.create_request(
            workflow_id="wf_123",
            execution_id="exec_456",
            step_id="review",
            step_name="Code Review",
            agent_name="code-reviewer",
        )

        approved = await manager.approve(request.id, "admin@example.com", "LGTM")

        assert approved.status == ApprovalStatus.APPROVED
        assert approved.decided_by == "admin@example.com"

    @pytest.mark.asyncio
    async def test_reject_request(self, manager: ApprovalManager) -> None:
        """Test rejecting a request through manager."""
        request = await manager.create_request(
            workflow_id="wf_123",
            execution_id="exec_456",
            step_id="review",
            step_name="Code Review",
            agent_name="code-reviewer",
        )

        rejected = await manager.reject(
            request.id, "admin@example.com", "Missing tests"
        )

        assert rejected.status == ApprovalStatus.REJECTED
        assert rejected.decision_reason == "Missing tests"

    @pytest.mark.asyncio
    async def test_cancel_request(self, manager: ApprovalManager) -> None:
        """Test cancelling a request."""
        request = await manager.create_request(
            workflow_id="wf_123",
            execution_id="exec_456",
            step_id="review",
            step_name="Code Review",
            agent_name="code-reviewer",
        )

        cancelled = await manager.cancel(request.id)

        assert cancelled.status == ApprovalStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_approve_not_found(self, manager: ApprovalManager) -> None:
        """Test approving non-existent request."""
        with pytest.raises(ApprovalNotFoundError) as exc_info:
            await manager.approve("approval_nonexistent", "admin@example.com")

        assert exc_info.value.approval_id == "approval_nonexistent"

    @pytest.mark.asyncio
    async def test_approve_already_decided(self, manager: ApprovalManager) -> None:
        """Test approving already-approved request."""
        request = await manager.create_request(
            workflow_id="wf_123",
            execution_id="exec_456",
            step_id="review",
            step_name="Code Review",
            agent_name="code-reviewer",
        )

        await manager.approve(request.id, "admin@example.com")

        with pytest.raises(ApprovalAlreadyDecidedError) as exc_info:
            await manager.approve(request.id, "other@example.com")

        assert exc_info.value.status == ApprovalStatus.APPROVED

    @pytest.mark.asyncio
    async def test_unauthorized_approver(self, manager: ApprovalManager) -> None:
        """Test unauthorized approver."""
        config = ApprovalConfig(
            required=True,
            approvers=["admin@example.com"],
        )
        request = await manager.create_request(
            workflow_id="wf_123",
            execution_id="exec_456",
            step_id="review",
            step_name="Code Review",
            agent_name="code-reviewer",
            config=config,
        )

        with pytest.raises(UnauthorizedApproverError) as exc_info:
            await manager.approve(request.id, "other@example.com")

        assert exc_info.value.approver == "other@example.com"

    @pytest.mark.asyncio
    async def test_authorized_approver(self, manager: ApprovalManager) -> None:
        """Test authorized approver can approve."""
        config = ApprovalConfig(
            required=True,
            approvers=["admin@example.com", "manager@example.com"],
        )
        request = await manager.create_request(
            workflow_id="wf_123",
            execution_id="exec_456",
            step_id="review",
            step_name="Code Review",
            agent_name="code-reviewer",
            config=config,
        )

        # Authorized approver can approve
        approved = await manager.approve(request.id, "admin@example.com")
        assert approved.is_approved

    @pytest.mark.asyncio
    async def test_any_approver_when_empty_list(self, manager: ApprovalManager) -> None:
        """Test anyone can approve when approvers list is empty."""
        config = ApprovalConfig(required=True, approvers=[])
        request = await manager.create_request(
            workflow_id="wf_123",
            execution_id="exec_456",
            step_id="review",
            step_name="Code Review",
            agent_name="code-reviewer",
            config=config,
        )

        # Anyone can approve
        approved = await manager.approve(request.id, "random@example.com")
        assert approved.is_approved

    @pytest.mark.asyncio
    async def test_list_pending(self, manager: ApprovalManager) -> None:
        """Test listing pending requests."""
        await manager.create_request(
            workflow_id="wf_1",
            execution_id="exec_1",
            step_id="s1",
            step_name="Step 1",
            agent_name="agent1",
            priority=ApprovalPriority.LOW,
        )
        await manager.create_request(
            workflow_id="wf_1",
            execution_id="exec_2",
            step_id="s2",
            step_name="Step 2",
            agent_name="agent2",
            priority=ApprovalPriority.CRITICAL,
        )
        await manager.create_request(
            workflow_id="wf_2",
            execution_id="exec_3",
            step_id="s3",
            step_name="Step 3",
            agent_name="agent3",
            priority=ApprovalPriority.MEDIUM,
        )

        # All pending
        all_pending = manager.list_pending()
        assert len(all_pending) == 3
        # Should be sorted by priority (CRITICAL first)
        assert all_pending[0].priority == ApprovalPriority.CRITICAL

        # Filter by workflow
        wf1_pending = manager.list_pending(workflow_id="wf_1")
        assert len(wf1_pending) == 2

        # Filter by priority
        critical = manager.list_pending(priority=ApprovalPriority.CRITICAL)
        assert len(critical) == 1

    @pytest.mark.asyncio
    async def test_list_decided(self, manager: ApprovalManager) -> None:
        """Test listing decided requests."""
        r1 = await manager.create_request(
            workflow_id="wf_1",
            execution_id="exec_1",
            step_id="s1",
            step_name="Step 1",
            agent_name="agent1",
        )
        r2 = await manager.create_request(
            workflow_id="wf_1",
            execution_id="exec_2",
            step_id="s2",
            step_name="Step 2",
            agent_name="agent2",
        )

        await manager.approve(r1.id, "admin@example.com")
        await manager.reject(r2.id, "admin@example.com")

        decided = manager.list_decided()
        assert len(decided) == 2

        approved = manager.list_decided(status=ApprovalStatus.APPROVED)
        assert len(approved) == 1

    @pytest.mark.asyncio
    async def test_get_stats(self, manager: ApprovalManager) -> None:
        """Test getting approval statistics."""
        r1 = await manager.create_request(
            workflow_id="wf_1",
            execution_id="exec_1",
            step_id="s1",
            step_name="Step 1",
            agent_name="agent1",
        )
        r2 = await manager.create_request(
            workflow_id="wf_1",
            execution_id="exec_2",
            step_id="s2",
            step_name="Step 2",
            agent_name="agent2",
        )
        r3 = await manager.create_request(
            workflow_id="wf_1",
            execution_id="exec_3",
            step_id="s3",
            step_name="Step 3",
            agent_name="agent3",
        )

        await manager.approve(r1.id, "admin@example.com")
        await manager.reject(r2.id, "admin@example.com")

        stats = manager.get_stats()
        assert stats["pending_count"] == 1
        assert stats["decided_count"] == 2
        assert stats["approved_count"] == 1
        assert stats["rejected_count"] == 1

    @pytest.mark.asyncio
    async def test_wait_for_decision_approved(self, manager: ApprovalManager) -> None:
        """Test waiting for approval decision."""
        request = await manager.create_request(
            workflow_id="wf_123",
            execution_id="exec_456",
            step_id="review",
            step_name="Code Review",
            agent_name="code-reviewer",
        )

        # Approve in background after short delay
        async def approve_later() -> None:
            await asyncio.sleep(0.1)
            await manager.approve(request.id, "admin@example.com")

        asyncio.create_task(approve_later())

        # Wait for decision
        is_approved = await manager.wait_for_decision(request.id, timeout_seconds=5)

        assert is_approved is True

    @pytest.mark.asyncio
    async def test_wait_for_decision_rejected(self, manager: ApprovalManager) -> None:
        """Test waiting for rejection decision."""
        request = await manager.create_request(
            workflow_id="wf_123",
            execution_id="exec_456",
            step_id="review",
            step_name="Code Review",
            agent_name="code-reviewer",
        )

        # Reject in background after short delay
        async def reject_later() -> None:
            await asyncio.sleep(0.1)
            await manager.reject(request.id, "admin@example.com")

        asyncio.create_task(reject_later())

        # Wait for decision
        is_approved = await manager.wait_for_decision(request.id, timeout_seconds=5)

        assert is_approved is False

    @pytest.mark.asyncio
    async def test_wait_for_decision_timeout(self, manager: ApprovalManager) -> None:
        """Test timeout while waiting for decision."""
        request = await manager.create_request(
            workflow_id="wf_123",
            execution_id="exec_456",
            step_id="review",
            step_name="Code Review",
            agent_name="code-reviewer",
        )

        # Wait with very short timeout
        with pytest.raises(ApprovalTimeoutError) as exc_info:
            await manager.wait_for_decision(request.id, timeout_seconds=0.1)

        assert exc_info.value.approval_id == request.id

    @pytest.mark.asyncio
    async def test_get_request(self, manager: ApprovalManager) -> None:
        """Test getting request by ID."""
        request = await manager.create_request(
            workflow_id="wf_123",
            execution_id="exec_456",
            step_id="review",
            step_name="Code Review",
            agent_name="code-reviewer",
        )

        # Get pending
        found = manager.get_request(request.id)
        assert found is not None
        assert found.id == request.id

        # Approve and get decided
        await manager.approve(request.id, "admin@example.com")
        found = manager.get_request(request.id)
        assert found is not None
        assert found.is_approved

        # Non-existent
        not_found = manager.get_request("approval_nonexistent")
        assert not_found is None


class TestExecutionContextApproval:
    """Tests for ExecutionContext approval integration."""

    def test_await_approval(self) -> None:
        """Test marking context as awaiting approval."""
        context = ExecutionContext(
            workflow_id="wf_123",
            execution_id="exec_456",
            inputs={"query": "test"},
        )
        context.start()

        context.await_approval("step1", "approval_789")

        assert context.status == ExecutionStatus.AWAITING_APPROVAL
        assert context.is_awaiting_approval is True
        assert context.current_step == "step1"
        assert context.pending_approval_id == "approval_789"

    def test_resume_from_approval(self) -> None:
        """Test resuming from approval."""
        context = ExecutionContext(
            workflow_id="wf_123",
            execution_id="exec_456",
            inputs={"query": "test"},
        )
        context.start()
        context.await_approval("step1", "approval_789")

        context.resume_from_approval()

        assert context.status == ExecutionStatus.RUNNING
        assert context.is_awaiting_approval is False
        assert context.pending_approval_id is None

    def test_awaiting_approval_status(self) -> None:
        """Test ExecutionStatus includes AWAITING_APPROVAL."""
        assert ExecutionStatus.AWAITING_APPROVAL.value == "awaiting_approval"
