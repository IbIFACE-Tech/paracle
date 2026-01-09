"""Tests for ExecutionContext and ExecutionStatus."""

from datetime import UTC, datetime

import pytest

from paracle_orchestration.context import ExecutionContext, ExecutionStatus


class TestExecutionStatus:
    """Test ExecutionStatus enum."""

    def test_execution_status_values(self):
        # Assert all expected statuses exist
        assert ExecutionStatus.PENDING == "pending"
        assert ExecutionStatus.RUNNING == "running"
        assert ExecutionStatus.COMPLETED == "completed"
        assert ExecutionStatus.FAILED == "failed"
        assert ExecutionStatus.CANCELLED == "cancelled"
        assert ExecutionStatus.TIMEOUT == "timeout"


class TestExecutionContextCreation:
    """Test ExecutionContext creation and defaults."""

    def test_create_minimal_context(self):
        # Arrange & Act
        context = ExecutionContext(
            workflow_id="wf_123", execution_id="exec_456", inputs={"query": "hello"}
        )

        # Assert
        assert context.workflow_id == "wf_123"
        assert context.execution_id == "exec_456"
        assert context.inputs == {"query": "hello"}
        assert context.status == ExecutionStatus.PENDING
        assert context.outputs == {}
        assert context.step_results == {}
        assert context.errors == []
        assert context.start_time is None
        assert context.end_time is None
        assert context.metadata == {}

    def test_create_context_with_metadata(self):
        # Arrange & Act
        context = ExecutionContext(
            workflow_id="wf_123",
            execution_id="exec_456",
            inputs={"query": "hello"},
            metadata={"user": "alice", "env": "prod"},
        )

        # Assert
        assert context.metadata == {"user": "alice", "env": "prod"}


class TestExecutionLifecycle:
    """Test execution lifecycle methods."""

    def test_start_sets_running_status_and_timestamp(self):
        # Arrange
        context = ExecutionContext(
            workflow_id="wf_123", execution_id="exec_456", inputs={}
        )
        before = datetime.now(UTC)

        # Act
        context.start()

        # Assert
        after = datetime.now(UTC)
        assert context.status == ExecutionStatus.RUNNING
        assert context.start_time is not None
        assert before <= context.start_time <= after

    def test_complete_sets_completed_status_and_timestamp(self):
        # Arrange
        context = ExecutionContext(
            workflow_id="wf_123", execution_id="exec_456", inputs={}
        )
        context.start()
        before = datetime.now(UTC)

        # Act
        context.complete()

        # Assert
        after = datetime.now(UTC)
        assert context.status == ExecutionStatus.COMPLETED
        assert context.end_time is not None
        assert before <= context.end_time <= after

    def test_complete_with_outputs(self):
        # Arrange
        context = ExecutionContext(
            workflow_id="wf_123", execution_id="exec_456", inputs={}
        )
        outputs = {"result": "success", "data": [1, 2, 3]}

        # Act
        context.complete(outputs)

        # Assert
        assert context.status == ExecutionStatus.COMPLETED
        assert context.outputs == outputs

    def test_fail_sets_failed_status_and_adds_error(self):
        # Arrange
        context = ExecutionContext(
            workflow_id="wf_123", execution_id="exec_456", inputs={}
        )
        context.start()
        error_msg = "Step 'analyze' failed: Connection timeout"

        # Act
        context.fail(error_msg)

        # Assert
        assert context.status == ExecutionStatus.FAILED
        assert context.end_time is not None
        assert error_msg in context.errors

    def test_cancel_sets_cancelled_status(self):
        # Arrange
        context = ExecutionContext(
            workflow_id="wf_123", execution_id="exec_456", inputs={}
        )
        context.start()

        # Act
        context.cancel()

        # Assert
        assert context.status == ExecutionStatus.CANCELLED
        assert context.end_time is not None

    def test_timeout_exceeded_sets_timeout_status(self):
        # Arrange
        context = ExecutionContext(
            workflow_id="wf_123", execution_id="exec_456", inputs={}
        )
        context.start()

        # Act
        context.timeout_exceeded()

        # Assert
        assert context.status == ExecutionStatus.TIMEOUT
        assert context.end_time is not None


class TestExecutionDuration:
    """Test duration calculation."""

    def test_duration_none_before_start(self):
        # Arrange
        context = ExecutionContext(
            workflow_id="wf_123", execution_id="exec_456", inputs={}
        )

        # Act & Assert
        assert context.duration_seconds is None

    def test_duration_calculated_while_running(self):
        # Arrange
        context = ExecutionContext(
            workflow_id="wf_123", execution_id="exec_456", inputs={}
        )
        context.start()

        # Act
        import time

        time.sleep(0.1)
        duration = context.duration_seconds

        # Assert
        assert duration is not None
        assert duration >= 0.1

    def test_duration_calculated_after_completion(self):
        # Arrange
        context = ExecutionContext(
            workflow_id="wf_123", execution_id="exec_456", inputs={}
        )
        context.start()

        import time

        time.sleep(0.1)

        # Act
        context.complete()
        duration = context.duration_seconds

        # Assert
        assert duration is not None
        assert duration >= 0.1


class TestTerminalStates:
    """Test terminal state checking."""

    def test_is_terminal_for_completed(self):
        # Arrange
        context = ExecutionContext(
            workflow_id="wf_123", execution_id="exec_456", inputs={}
        )
        context.complete()

        # Act & Assert
        assert context.is_terminal is True
        assert context.is_running is False

    def test_is_terminal_for_failed(self):
        # Arrange
        context = ExecutionContext(
            workflow_id="wf_123", execution_id="exec_456", inputs={}
        )
        context.fail("error")

        # Act & Assert
        assert context.is_terminal is True
        assert context.is_running is False

    def test_is_terminal_for_cancelled(self):
        # Arrange
        context = ExecutionContext(
            workflow_id="wf_123", execution_id="exec_456", inputs={}
        )
        context.cancel()

        # Act & Assert
        assert context.is_terminal is True
        assert context.is_running is False

    def test_is_terminal_for_timeout(self):
        # Arrange
        context = ExecutionContext(
            workflow_id="wf_123", execution_id="exec_456", inputs={}
        )
        context.timeout_exceeded()

        # Act & Assert
        assert context.is_terminal is True
        assert context.is_running is False

    def test_not_terminal_for_pending(self):
        # Arrange
        context = ExecutionContext(
            workflow_id="wf_123", execution_id="exec_456", inputs={}
        )

        # Act & Assert
        assert context.is_terminal is False
        assert context.is_running is False

    def test_not_terminal_for_running(self):
        # Arrange
        context = ExecutionContext(
            workflow_id="wf_123", execution_id="exec_456", inputs={}
        )
        context.start()

        # Act & Assert
        assert context.is_terminal is False
        assert context.is_running is True


class TestStepResults:
    """Test step result management."""

    def test_add_step_result(self):
        # Arrange
        context = ExecutionContext(
            workflow_id="wf_123", execution_id="exec_456", inputs={}
        )
        result = {"output": "analyzed", "confidence": 0.95}

        # Act
        context.add_step_result("analyze", result)

        # Assert
        assert context.step_results["analyze"] == result

    def test_add_multiple_step_results(self):
        # Arrange
        context = ExecutionContext(
            workflow_id="wf_123", execution_id="exec_456", inputs={}
        )

        # Act
        context.add_step_result("step1", {"data": "a"})
        context.add_step_result("step2", {"data": "b"})
        context.add_step_result("step3", {"data": "c"})

        # Assert
        assert len(context.step_results) == 3
        assert context.step_results["step1"] == {"data": "a"}
        assert context.step_results["step2"] == {"data": "b"}
        assert context.step_results["step3"] == {"data": "c"}


class TestErrorManagement:
    """Test error collection."""

    def test_add_error(self):
        # Arrange
        context = ExecutionContext(
            workflow_id="wf_123", execution_id="exec_456", inputs={}
        )
        error_msg = "Connection failed"

        # Act
        context.add_error(error_msg)

        # Assert
        assert error_msg in context.errors

    def test_add_multiple_errors(self):
        # Arrange
        context = ExecutionContext(
            workflow_id="wf_123", execution_id="exec_456", inputs={}
        )

        # Act
        context.add_error("Error 1")
        context.add_error("Error 2")
        context.add_error("Error 3")

        # Assert
        assert len(context.errors) == 3
        assert "Error 1" in context.errors
        assert "Error 2" in context.errors
        assert "Error 3" in context.errors
