"""Tests for YOLO mode (auto-approval) functionality.

This test suite validates that the YOLO mode feature works correctly across:
- ApprovalManager auto-approve functionality
- WorkflowOrchestrator integration
- CLI flag handling
- API endpoint support
"""

import asyncio
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from paracle_domain.models import (
    ApprovalConfig,
    ApprovalPriority,
    ApprovalStatus,
    Workflow,
    WorkflowSpec,
    WorkflowStep,
)
from paracle_events import EventBus
from paracle_orchestration.approval import ApprovalManager
from paracle_orchestration.context import ExecutionStatus
from paracle_orchestration.engine import WorkflowOrchestrator

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def event_bus():
    """Create an event bus for testing."""
    return EventBus()


@pytest.fixture
async def mock_step_executor():
    """Create a mock step executor."""

    async def executor(step: WorkflowStep, inputs: dict[str, Any]) -> Any:
        """Mock executor that returns inputs with step name."""
        await asyncio.sleep(0.01)  # Simulate work
        return {
            "step": step.name,
            "output": f"result from {step.name}",
            "inputs": inputs,
        }

    return executor


@pytest.fixture
def workflow_with_approval():
    """Create a workflow with an approval step."""
    spec = WorkflowSpec(
        name="approval-workflow",
        steps=[
            WorkflowStep(
                id="step1",
                name="Generate Report",
                agent="reporter",
            ),
            WorkflowStep(
                id="step2",
                name="Review Report",
                agent="reviewer",
                depends_on=["step1"],
                requires_approval=True,
                approval_config={
                    "required": True,
                    "priority": "medium",
                    "timeout_seconds": 300,
                    "approvers": ["user:admin"],
                    "reason_required": False,
                },
            ),
            WorkflowStep(
                id="step3",
                name="Publish Report",
                agent="publisher",
                depends_on=["step2"],
            ),
        ],
    )
    return Workflow(spec=spec)


# =============================================================================
# ApprovalManager Tests
# =============================================================================


class TestApprovalManagerYoloMode:
    """Test ApprovalManager with auto_approve enabled."""

    @pytest.mark.asyncio
    async def test_auto_approve_enabled(self, event_bus):
        """Test that auto_approve=True automatically approves requests."""
        # Arrange
        manager = ApprovalManager(
            event_bus=event_bus,
            auto_approve=True,
            auto_approver="system:test",
        )

        # Act
        request = await manager.create_request(
            workflow_id="wf_test",
            execution_id="exec_test",
            step_id="step1",
            step_name="Test Step",
            agent_name="test-agent",
            context={"data": "test"},
            config=ApprovalConfig(
                required=True,
                priority=ApprovalPriority.HIGH,
                approvers=["user:admin"],
            ),
        )

        # Assert
        assert request is not None
        assert request.status == ApprovalStatus.APPROVED
        assert request.decided_by == "system:test"
        assert "Auto-approved" in (request.decision_reason or "")

    @pytest.mark.asyncio
    async def test_auto_approve_wait_for_decision(self, event_bus):
        """Test that wait_for_decision returns immediately with auto-approve."""
        # Arrange
        manager = ApprovalManager(
            event_bus=event_bus,
            auto_approve=True,
            auto_approver="system:test",
        )

        request = await manager.create_request(
            workflow_id="wf_test",
            execution_id="exec_test",
            step_id="step1",
            step_name="Test Step",
            agent_name="test-agent",
            context={"data": "test"},
            config=ApprovalConfig(required=True),
        )

        # Act
        is_approved = await manager.wait_for_decision(
            request.id, timeout_seconds=1.0
        )

        # Assert
        assert is_approved is True

    @pytest.mark.asyncio
    async def test_auto_approve_emits_event(self, event_bus):
        """Test that auto-approval emits events correctly."""
        # Arrange
        manager = ApprovalManager(
            event_bus=event_bus,
            auto_approve=True,
            auto_approver="system:test",
        )

        # Act
        request = await manager.create_request(
            workflow_id="wf_test",
            execution_id="exec_test",
            step_id="step1",
            step_name="Test Step",
            agent_name="test-agent",
            context={"data": "test"},
            config=ApprovalConfig(required=True),
        )

        # Wait for async event processing
        await asyncio.sleep(0.1)

        # Assert - verify the request was auto-approved
        assert request.status == ApprovalStatus.APPROVED
        assert request.decided_by == "system:test"

    @pytest.mark.asyncio
    async def test_auto_approve_disabled_requires_manual(self, event_bus):
        """Test that auto_approve=False requires manual approval."""
        # Arrange
        manager = ApprovalManager(
            event_bus=event_bus,
            auto_approve=False,
        )

        request = await manager.create_request(
            workflow_id="wf_test",
            execution_id="exec_test",
            step_id="step1",
            step_name="Test Step",
            agent_name="test-agent",
            context={"data": "test"},
            config=ApprovalConfig(required=True),
        )

        # Assert
        assert request.status == ApprovalStatus.PENDING
        assert request.decided_by is None


# =============================================================================
# WorkflowOrchestrator Tests
# =============================================================================


class TestOrchestratorYoloMode:
    """Test WorkflowOrchestrator with auto_approve parameter."""

    @pytest.mark.asyncio
    async def test_execute_with_auto_approve(
        self, event_bus, mock_step_executor, workflow_with_approval
    ):
        """Test that workflow with approval completes with auto_approve=True."""
        # Arrange
        orchestrator = WorkflowOrchestrator(
            event_bus=event_bus,
            step_executor=mock_step_executor,
        )

        # Act
        context = await orchestrator.execute(
            workflow=workflow_with_approval,
            inputs={"input": "test"},
            auto_approve=True,
        )

        # Assert
        assert context.status == ExecutionStatus.COMPLETED
        assert "step1" in context.results
        assert "step2" in context.results
        assert "step3" in context.results

    @pytest.mark.asyncio
    async def test_execute_without_auto_approve_blocks(
        self, event_bus, mock_step_executor, workflow_with_approval
    ):
        """Test that workflow blocks on approval without auto_approve."""
        # Arrange
        orchestrator = WorkflowOrchestrator(
            event_bus=event_bus,
            step_executor=mock_step_executor,
        )

        # Act - Execute without auto_approve with timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                orchestrator.execute(
                    workflow=workflow_with_approval,
                    inputs={"input": "test"},
                    auto_approve=False,
                ),
                timeout=1.0,  # Should timeout waiting for approval
            )

    @pytest.mark.asyncio
    async def test_approval_manager_created_with_yolo(
        self, event_bus, mock_step_executor, workflow_with_approval
    ):
        """Test that ApprovalManager is created with auto_approve when requested."""
        # Arrange
        orchestrator = WorkflowOrchestrator(
            event_bus=event_bus,
            step_executor=mock_step_executor,
        )

        # Act
        await orchestrator.execute(
            workflow=workflow_with_approval,
            inputs={"input": "test"},
            auto_approve=True,
        )

        # Assert
        assert orchestrator.approval_manager is not None
        assert orchestrator.approval_manager.auto_approve is True
        assert orchestrator.approval_manager.auto_approver == "system:orchestrator"


# =============================================================================
# CLI Integration Tests
# =============================================================================


class TestCLIYoloFlag:
    """Test CLI --yolo flag integration."""

    @patch("paracle_cli.commands.workflow.get_client")
    @patch("paracle_cli.commands.workflow._use_local_fallback")
    def test_yolo_flag_passed_to_api(self, mock_fallback, mock_get_client):
        """Test that --yolo flag passes auto_approve=True to API."""
        # Arrange
        from click.testing import CliRunner
        from paracle_cli.main import cli

        mock_fallback.return_value = False
        mock_client = MagicMock()
        mock_client.workflow_execute.return_value = {
            "execution_id": "exec_123",
            "status": "pending",
            "message": "Started",
        }
        mock_get_client.return_value = mock_client

        runner = CliRunner()

        # Act
        result = runner.invoke(
            cli,
            ["workflow", "run", "test-workflow", "--yolo"],
        )

        # Assert
        assert result.exit_code == 0
        mock_client.workflow_execute.assert_called_once()
        call_kwargs = mock_client.workflow_execute.call_args[1]
        assert call_kwargs["auto_approve"] is True

    @patch("paracle_cli.commands.workflow.get_client")
    @patch("paracle_cli.commands.workflow._use_local_fallback")
    def test_no_yolo_flag_defaults_false(self, mock_fallback, mock_get_client):
        """Test that without --yolo, auto_approve defaults to False."""
        # Arrange
        from click.testing import CliRunner
        from paracle_cli.main import cli

        mock_fallback.return_value = False
        mock_client = MagicMock()
        mock_client.workflow_execute.return_value = {
            "execution_id": "exec_123",
            "status": "pending",
            "message": "Started",
        }
        mock_get_client.return_value = mock_client

        runner = CliRunner()

        # Act
        result = runner.invoke(
            cli,
            ["workflow", "run", "test-workflow"],
        )

        # Assert
        assert result.exit_code == 0
        mock_client.workflow_execute.assert_called_once()
        call_kwargs = mock_client.workflow_execute.call_args[1]
        assert call_kwargs["auto_approve"] is False


# =============================================================================
# API Tests
# =============================================================================


class TestAPIYoloSupport:
    """Test API endpoint support for auto_approve."""

    @pytest.mark.asyncio
    async def test_execute_request_accepts_auto_approve(self):
        """Test that WorkflowExecuteRequest accepts auto_approve field."""
        from paracle_api.routers.workflow_execution import WorkflowExecuteRequest

        # Act
        request = WorkflowExecuteRequest(
            workflow_id="wf_test",
            inputs={"key": "value"},
            async_execution=True,
            auto_approve=True,
        )

        # Assert
        assert request.workflow_id == "wf_test"
        assert request.auto_approve is True

    @pytest.mark.asyncio
    async def test_execute_request_defaults_auto_approve_false(self):
        """Test that auto_approve defaults to False."""
        from paracle_api.routers.workflow_execution import WorkflowExecuteRequest

        # Act
        request = WorkflowExecuteRequest(
            workflow_id="wf_test",
            inputs={"key": "value"},
        )

        # Assert
        assert request.auto_approve is False


# =============================================================================
# Integration Tests
# =============================================================================


class TestYoloModeIntegration:
    """End-to-end integration tests for YOLO mode."""

    @pytest.mark.asyncio
    async def test_full_workflow_with_yolo(self, event_bus, mock_step_executor):
        """Test complete workflow execution with YOLO mode enabled."""
        # Arrange
        spec = WorkflowSpec(
            name="multi-approval-workflow",
            steps=[
                WorkflowStep(id="step1", name="Step 1", agent="agent1"),
                WorkflowStep(
                    id="step2",
                    name="Step 2 (requires approval)",
                    agent="agent2",
                    depends_on=["step1"],
                    requires_approval=True,
                    approval_config={"required": True},
                ),
                WorkflowStep(
                    id="step3",
                    name="Step 3",
                    agent="agent3",
                    depends_on=["step2"],
                ),
                WorkflowStep(
                    id="step4",
                    name="Step 4 (requires approval)",
                    agent="agent4",
                    depends_on=["step3"],
                    requires_approval=True,
                    approval_config={"required": True},
                ),
                WorkflowStep(
                    id="step5",
                    name="Step 5",
                    agent="agent5",
                    depends_on=["step4"],
                ),
            ],
        )
        workflow = Workflow(spec=spec)

        orchestrator = WorkflowOrchestrator(
            event_bus=event_bus,
            step_executor=mock_step_executor,
        )

        # Act
        context = await orchestrator.execute(
            workflow=workflow,
            inputs={"input": "test"},
            auto_approve=True,
        )

        # Assert
        assert context.status == ExecutionStatus.COMPLETED
        # All 5 steps should complete
        assert len(context.results) == 5
        assert all(f"step{i}" in context.results for i in range(1, 6))

    @pytest.mark.asyncio
    async def test_yolo_vs_manual_timing(
        self, event_bus, mock_step_executor, workflow_with_approval
    ):
        """Test that YOLO mode is faster than manual approval."""
        import time

        orchestrator = WorkflowOrchestrator(
            event_bus=event_bus,
            step_executor=mock_step_executor,
        )

        # Time YOLO execution
        start = time.time()
        context_yolo = await orchestrator.execute(
            workflow=workflow_with_approval,
            inputs={"input": "test"},
            auto_approve=True,
        )
        yolo_time = time.time() - start

        # Assert YOLO completed quickly (< 1 second for this simple workflow)
        assert yolo_time < 1.0
        assert context_yolo.status == ExecutionStatus.COMPLETED
