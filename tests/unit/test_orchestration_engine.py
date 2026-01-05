"""Tests for WorkflowOrchestrator."""

import asyncio
from typing import Any
from unittest.mock import AsyncMock

import pytest

from paracle_domain.models import (
    ApprovalConfig,
    ApprovalPriority,
    Workflow,
    WorkflowSpec,
    WorkflowStep,
    generate_id,
)
from paracle_events import EventBus
from paracle_orchestration.approval import ApprovalManager
from paracle_orchestration.context import ExecutionContext, ExecutionStatus
from paracle_orchestration.engine import WorkflowOrchestrator
from paracle_orchestration.exceptions import (
    CircularDependencyError,
    ExecutionTimeoutError,
    InvalidWorkflowError,
    StepExecutionError,
)


def make_step(name: str, agent: str | None = None, **kwargs) -> WorkflowStep:
    """Helper to create WorkflowStep with id defaulting to name."""
    return WorkflowStep(id=name, name=name, agent=agent or name, **kwargs)


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
        return {"step": step.name, "output": f"result from {step.name}", "inputs": inputs}

    return executor


@pytest.fixture
def orchestrator(event_bus, mock_step_executor):
    """Create a workflow orchestrator."""
    return WorkflowOrchestrator(event_bus, mock_step_executor)


@pytest.fixture
def simple_workflow():
    """Create a simple linear workflow."""
    spec = WorkflowSpec(
        name="simple-workflow",
        steps=[
            make_step("step1"),
            make_step("step2", depends_on=["step1"]),
            make_step("step3", depends_on=["step2"]),
        ],
    )
    return Workflow(spec=spec)


@pytest.fixture
def parallel_workflow():
    """Create a workflow with parallel steps."""
    spec = WorkflowSpec(
        name="parallel-workflow",
        steps=[
            make_step("step1"),
            make_step("step2", depends_on=["step1"]),
            make_step("step3", depends_on=["step1"]),
            make_step("step4", depends_on=["step2", "step3"]),
        ],
    )
    return Workflow(spec=spec)


class TestWorkflowValidation:
    """Test workflow validation."""

    @pytest.mark.asyncio
    async def test_validate_raises_for_circular_dependency(
        self, orchestrator, event_bus
    ):
        # Arrange
        spec = WorkflowSpec(
            name="circular",
            steps=[
                make_step("step1", depends_on=["step2"]),
                make_step("step2", depends_on=["step1"]),
            ],
        )
        workflow = Workflow(spec=spec)

        # Act & Assert
        with pytest.raises(CircularDependencyError):
            await orchestrator.execute(workflow, {})

    @pytest.mark.asyncio
    async def test_validate_raises_for_missing_dependency(
        self, orchestrator, event_bus
    ):
        # Arrange
        spec = WorkflowSpec(
            name="missing-dep",
            steps=[
                make_step("step1"),
                make_step("step2", depends_on=["nonexistent"]),
            ],
        )
        workflow = Workflow(spec=spec)

        # Act & Assert
        with pytest.raises(InvalidWorkflowError):
            await orchestrator.execute(workflow, {})


class TestSimpleWorkflowExecution:
    """Test simple workflow execution."""

    @pytest.mark.asyncio
    async def test_execute_simple_workflow(self, orchestrator, simple_workflow):
        # Arrange
        inputs = {"query": "test"}

        # Act
        context = await orchestrator.execute(simple_workflow, inputs)

        # Assert
        assert context.status == ExecutionStatus.COMPLETED
        assert "step1" in context.step_results
        assert "step2" in context.step_results
        assert "step3" in context.step_results
        assert context.errors == []

    @pytest.mark.asyncio
    async def test_execute_records_execution_time(self, orchestrator, simple_workflow):
        # Arrange
        inputs = {"query": "test"}

        # Act
        context = await orchestrator.execute(simple_workflow, inputs)

        # Assert
        assert context.start_time is not None
        assert context.end_time is not None
        assert context.duration_seconds is not None
        assert context.duration_seconds > 0

    @pytest.mark.asyncio
    async def test_execute_stores_workflow_metadata(self, orchestrator, simple_workflow):
        # Arrange
        inputs = {"query": "test"}

        # Act
        context = await orchestrator.execute(simple_workflow, inputs)

        # Assert
        assert context.workflow_id == simple_workflow.id
        assert context.metadata["workflow_name"] == "simple-workflow"
        assert context.metadata["total_steps"] == 3

    @pytest.mark.asyncio
    async def test_execute_tracks_active_execution(self, orchestrator, simple_workflow):
        # Arrange
        inputs = {"query": "test"}

        # Create a flag to track if execution was active
        was_active = False

        async def checking_executor(step, inputs):
            nonlocal was_active
            if orchestrator.active_executions:
                was_active = True
            await asyncio.sleep(0.01)
            return {"output": "result"}

        orchestrator.step_executor = checking_executor

        # Act
        await orchestrator.execute(simple_workflow, inputs)

        # Assert
        assert was_active is True
        assert len(orchestrator.active_executions) == 0  # Cleaned up after


class TestParallelWorkflowExecution:
    """Test parallel workflow execution."""

    @pytest.mark.asyncio
    async def test_execute_parallel_workflow(self, orchestrator, parallel_workflow):
        # Arrange
        inputs = {"query": "test"}

        # Act
        context = await orchestrator.execute(parallel_workflow, inputs)

        # Assert
        assert context.status == ExecutionStatus.COMPLETED
        assert len(context.step_results) == 4
        assert "step1" in context.step_results
        assert "step2" in context.step_results
        assert "step3" in context.step_results
        assert "step4" in context.step_results

    @pytest.mark.asyncio
    async def test_parallel_steps_execute_concurrently(
        self, event_bus, parallel_workflow
    ):
        # Arrange
        execution_times = {}

        async def timing_executor(step, inputs):
            import time

            start = time.time()
            await asyncio.sleep(0.1)
            end = time.time()
            execution_times[step.name] = (start, end)
            return {"output": f"result from {step.name}"}

        orchestrator = WorkflowOrchestrator(event_bus, timing_executor)
        inputs = {"query": "test"}

        # Act
        await orchestrator.execute(parallel_workflow, inputs)

        # Assert - step2 and step3 should overlap in time
        step2_start, step2_end = execution_times["step2"]
        step3_start, step3_end = execution_times["step3"]

        # Check that they started roughly at the same time (within 50ms)
        assert abs(step2_start - step3_start) < 0.05


class TestStepInputResolution:
    """Test step input resolution."""

    @pytest.mark.asyncio
    async def test_resolve_static_inputs(self, event_bus):
        # Arrange
        captured_inputs = {}

        async def capturing_executor(step, inputs):
            captured_inputs[step.name] = inputs
            return {"output": f"result from {step.name}"}

        orchestrator = WorkflowOrchestrator(event_bus, capturing_executor)

        spec = WorkflowSpec(
            name="static-inputs",
            steps=[
                make_step("step1", inputs={"static_param": "value"}),
            ],
        )
        workflow = Workflow(spec=spec)

        # Act
        await orchestrator.execute(workflow, {})

        # Assert
        assert captured_inputs["step1"]["static_param"] == "value"

    @pytest.mark.asyncio
    async def test_resolve_workflow_inputs(self, event_bus):
        # Arrange
        captured_inputs = {}

        async def capturing_executor(step, inputs):
            captured_inputs[step.name] = inputs
            return {"output": f"result from {step.name}"}

        orchestrator = WorkflowOrchestrator(event_bus, capturing_executor)

        spec = WorkflowSpec(
            name="workflow-inputs", steps=[make_step("step1")]
        )
        workflow = Workflow(spec=spec)
        workflow_inputs = {"workflow_param": "workflow_value"}

        # Act
        await orchestrator.execute(workflow, workflow_inputs)

        # Assert
        assert captured_inputs["step1"]["workflow_param"] == "workflow_value"

    @pytest.mark.asyncio
    async def test_resolve_previous_step_outputs(self, event_bus):
        # Arrange
        captured_inputs = {}

        async def capturing_executor(step, inputs):
            captured_inputs[step.name] = inputs
            return {"output": f"result from {step.name}", "data": [1, 2, 3]}

        orchestrator = WorkflowOrchestrator(event_bus, capturing_executor)

        spec = WorkflowSpec(
            name="step-outputs",
            steps=[
                make_step("step1"),
                make_step(
                    "step2",
                    agent="agent2",
                    depends_on=["step1"],
                    inputs={"from_step1": "$step1.output"},
                ),
            ],
        )
        workflow = Workflow(spec=spec)

        # Act
        await orchestrator.execute(workflow, {})

        # Assert
        assert "from_step1" in captured_inputs["step2"]
        assert captured_inputs["step2"]["from_step1"]["output"] == "result from step1"


class TestErrorHandling:
    """Test error handling during execution."""

    @pytest.mark.asyncio
    async def test_execute_handles_step_failure(self, event_bus, simple_workflow):
        # Arrange
        async def failing_executor(step, inputs):
            if step.name == "step2":
                raise ValueError("Step 2 failed")
            return {"output": "success"}

        orchestrator = WorkflowOrchestrator(event_bus, failing_executor)

        # Act
        context = await orchestrator.execute(simple_workflow, {})

        # Assert
        assert context.status == ExecutionStatus.FAILED
        assert len(context.errors) > 0
        assert "step2" in context.errors[0]

    @pytest.mark.asyncio
    async def test_step_failure_stops_dependent_steps(self, event_bus):
        # Arrange
        executed_steps = []

        async def tracking_executor(step, inputs):
            executed_steps.append(step.name)
            if step.name == "step1":
                raise ValueError("Step 1 failed")
            return {"output": "success"}

        orchestrator = WorkflowOrchestrator(event_bus, tracking_executor)

        spec = WorkflowSpec(
            name="test",
            steps=[
                make_step("step1"),
                make_step("step2", depends_on=["step1"]),
            ],
        )
        workflow = Workflow(spec=spec)

        # Act
        context = await orchestrator.execute(workflow, {})

        # Assert
        assert context.status == ExecutionStatus.FAILED
        assert executed_steps == ["step1"]  # step2 should not execute


class TestTimeoutHandling:
    """Test timeout handling."""

    @pytest.mark.asyncio
    async def test_execute_with_timeout(self, event_bus):
        # Arrange
        async def slow_executor(step, inputs):
            await asyncio.sleep(1)  # Longer than timeout
            return {"output": "success"}

        orchestrator = WorkflowOrchestrator(event_bus, slow_executor)

        spec = WorkflowSpec(
            name="slow-workflow", steps=[make_step("step1")]
        )
        workflow = Workflow(spec=spec)

        # Act & Assert
        with pytest.raises(ExecutionTimeoutError):
            await orchestrator.execute(workflow, {}, timeout_seconds=0.1)

    @pytest.mark.asyncio
    async def test_timeout_cleans_up_active_execution(self, event_bus):
        # Arrange
        async def slow_executor(step, inputs):
            await asyncio.sleep(1)
            return {"output": "success"}

        orchestrator = WorkflowOrchestrator(event_bus, slow_executor)

        spec = WorkflowSpec(
            name="slow-workflow", steps=[make_step("step1")]
        )
        workflow = Workflow(spec=spec)

        # Act
        try:
            await orchestrator.execute(workflow, {}, timeout_seconds=0.1)
        except ExecutionTimeoutError:
            pass

        # Assert
        assert len(orchestrator.active_executions) == 0


class TestEventEmission:
    """Test event emission during workflow execution."""

    @pytest.mark.asyncio
    async def test_emits_workflow_started_event(self, simple_workflow):
        # Arrange
        event_bus = EventBus()
        emitted_events = []

        def capture_event(event):
            emitted_events.append(event)

        event_bus.subscribe("workflow.started", capture_event)

        async def mock_executor(step, inputs):
            return {"output": "success"}

        orchestrator = WorkflowOrchestrator(event_bus, mock_executor)

        # Act
        await orchestrator.execute(simple_workflow, {})

        # Assert
        await asyncio.sleep(0.1)  # Allow events to propagate
        started_events = [e for e in emitted_events if e.event_type == "workflow.started"]
        assert len(started_events) == 1

    @pytest.mark.asyncio
    async def test_emits_workflow_completed_event(self, simple_workflow):
        # Arrange
        event_bus = EventBus()
        emitted_events = []

        def capture_event(event):
            emitted_events.append(event)

        event_bus.subscribe("workflow.completed", capture_event)

        async def mock_executor(step, inputs):
            return {"output": "success"}

        orchestrator = WorkflowOrchestrator(event_bus, mock_executor)

        # Act
        await orchestrator.execute(simple_workflow, {})

        # Assert
        await asyncio.sleep(0.1)  # Allow events to propagate
        completed_events = [e for e in emitted_events if e.event_type == "workflow.completed"]
        assert len(completed_events) == 1


class TestActiveExecutionManagement:
    """Test active execution tracking."""

    @pytest.mark.asyncio
    async def test_get_active_executions_empty_initially(self, orchestrator):
        # Act
        active = orchestrator.get_active_executions()

        # Assert
        assert active == []

    @pytest.mark.asyncio
    async def test_get_active_execution_by_id(self, orchestrator, simple_workflow):
        # Arrange
        execution_id = None

        async def tracking_executor(step, inputs):
            nonlocal execution_id
            if execution_id is None and orchestrator.active_executions:
                execution_id = list(orchestrator.active_executions.keys())[0]
            await asyncio.sleep(0.01)
            return {"output": "success"}

        orchestrator.step_executor = tracking_executor

        # Act
        await orchestrator.execute(simple_workflow, {})

        # Assert
        assert execution_id is not None

    @pytest.mark.asyncio
    async def test_cancel_execution(self, event_bus):
        # Arrange
        async def long_executor(step, inputs):
            await asyncio.sleep(10)
            return {"output": "success"}

        orchestrator = WorkflowOrchestrator(event_bus, long_executor)

        spec = WorkflowSpec(
            name="long-workflow", steps=[make_step("step1")]
        )
        workflow = Workflow(spec=spec)

        # Act
        async def execute_and_cancel():
            # Start execution in background
            task = asyncio.create_task(orchestrator.execute(workflow, {}))
            await asyncio.sleep(0.1)  # Let it start

            # Get execution ID
            executions = orchestrator.get_active_executions()
            if executions:
                execution_id = executions[0].execution_id
                await orchestrator.cancel_execution(execution_id)

            try:
                await task
            except asyncio.CancelledError:
                pass

        await execute_and_cancel()

        # Assert
        assert len(orchestrator.active_executions) == 0


class TestApprovalIntegration:
    """Test Human-in-the-Loop approval integration."""

    @pytest.fixture
    def approval_manager(self, event_bus):
        """Create an approval manager for testing."""
        return ApprovalManager(event_bus)

    @pytest.fixture
    def orchestrator_with_approvals(self, event_bus, approval_manager):
        """Create an orchestrator with approval manager."""
        async def mock_executor(step, inputs):
            return {"output": f"result from {step.name}", "inputs": inputs}

        return WorkflowOrchestrator(
            event_bus,
            mock_executor,
            approval_manager=approval_manager,
        )

    @pytest.fixture
    def approval_workflow(self):
        """Create a workflow with an approval-required step."""
        spec = WorkflowSpec(
            name="approval-workflow",
            steps=[
                make_step("analyze"),
                make_step(
                    "deploy",
                    depends_on=["analyze"],
                    requires_approval=True,
                    approval_config={
                        "required": True,
                        "timeout_seconds": 300,
                        "priority": "high",
                    },
                ),
            ],
        )
        return Workflow(spec=spec)

    @pytest.mark.asyncio
    async def test_step_with_approval_creates_request(
        self, orchestrator_with_approvals, approval_manager, approval_workflow
    ):
        """Test that a step with requires_approval creates an approval request."""
        # Arrange
        created_requests = []

        def capture_created(request):
            created_requests.append(request)

        approval_manager._on_approval_created = capture_created

        # Act - Start execution in background
        async def execute_and_approve():
            task = asyncio.create_task(
                orchestrator_with_approvals.execute(approval_workflow, {"env": "prod"})
            )

            # Wait for approval request to be created
            await asyncio.sleep(0.1)

            # Approve the request
            if created_requests:
                await approval_manager.approve(
                    created_requests[0].id,
                    approver="admin@example.com",
                    reason="Looks good",
                )

            return await task

        context = await execute_and_approve()

        # Assert
        assert len(created_requests) == 1
        assert created_requests[0].step_name == "deploy"
        assert created_requests[0].agent_name == "deploy"
        assert context.status == ExecutionStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_approved_step_continues_execution(
        self, orchestrator_with_approvals, approval_manager, approval_workflow
    ):
        """Test that approved step allows workflow to complete."""
        # Arrange & Act
        async def execute_and_approve():
            task = asyncio.create_task(
                orchestrator_with_approvals.execute(approval_workflow, {"env": "prod"})
            )

            # Wait for approval request
            await asyncio.sleep(0.1)

            # Get pending requests and approve
            pending = approval_manager.list_pending()
            if pending:
                await approval_manager.approve(
                    pending[0].id,
                    approver="admin@example.com",
                )

            return await task

        context = await execute_and_approve()

        # Assert
        assert context.status == ExecutionStatus.COMPLETED
        assert "analyze" in context.step_results
        assert "deploy" in context.step_results

    @pytest.mark.asyncio
    async def test_rejected_step_fails_workflow(
        self, orchestrator_with_approvals, approval_manager, approval_workflow
    ):
        """Test that rejected approval fails the workflow."""
        # Arrange & Act
        async def execute_and_reject():
            task = asyncio.create_task(
                orchestrator_with_approvals.execute(approval_workflow, {"env": "prod"})
            )

            # Wait for approval request
            await asyncio.sleep(0.1)

            # Get pending requests and reject
            pending = approval_manager.list_pending()
            if pending:
                await approval_manager.reject(
                    pending[0].id,
                    approver="security@example.com",
                    reason="Security review required",
                )

            return await task

        context = await execute_and_reject()

        # Assert
        assert context.status == ExecutionStatus.FAILED
        assert len(context.errors) > 0
        assert "rejected" in context.errors[0].lower()

    @pytest.mark.asyncio
    async def test_approval_context_includes_step_output(
        self, orchestrator_with_approvals, approval_manager, approval_workflow
    ):
        """Test that approval request includes step output as context."""
        # Arrange
        created_request = None

        def capture_request(request):
            nonlocal created_request
            created_request = request

        approval_manager._on_approval_created = capture_request

        # Act
        async def execute_and_approve():
            task = asyncio.create_task(
                orchestrator_with_approvals.execute(approval_workflow, {"env": "prod"})
            )

            await asyncio.sleep(0.1)

            # Approve to complete
            pending = approval_manager.list_pending()
            if pending:
                await approval_manager.approve(pending[0].id, approver="admin")

            return await task

        await execute_and_approve()

        # Assert
        assert created_request is not None
        assert "step_output" in created_request.context
        assert "step_inputs" in created_request.context
        assert "workflow_name" in created_request.context

    @pytest.mark.asyncio
    async def test_workflow_without_approval_steps_completes_normally(
        self, orchestrator_with_approvals
    ):
        """Test that workflow without approval steps completes without waiting."""
        # Arrange
        spec = WorkflowSpec(
            name="no-approval-workflow",
            steps=[
                make_step("step1"),
                make_step("step2", depends_on=["step1"]),
            ],
        )
        workflow = Workflow(spec=spec)

        # Act
        context = await orchestrator_with_approvals.execute(workflow, {"data": "test"})

        # Assert
        assert context.status == ExecutionStatus.COMPLETED
        assert "step1" in context.step_results
        assert "step2" in context.step_results

    @pytest.mark.asyncio
    async def test_execution_context_shows_awaiting_approval_status(
        self, orchestrator_with_approvals, approval_manager, approval_workflow
    ):
        """Test that execution context reflects awaiting approval status."""
        # Arrange
        observed_status = None

        # Act
        async def observe_and_approve():
            nonlocal observed_status

            task = asyncio.create_task(
                orchestrator_with_approvals.execute(approval_workflow, {"env": "prod"})
            )

            # Wait for approval to be requested
            await asyncio.sleep(0.1)

            # Check active execution status
            active = orchestrator_with_approvals.get_active_executions()
            if active:
                observed_status = active[0].status

            # Approve to complete
            pending = approval_manager.list_pending()
            if pending:
                await approval_manager.approve(pending[0].id, approver="admin")

            return await task

        await observe_and_approve()

        # Assert
        assert observed_status == ExecutionStatus.AWAITING_APPROVAL
