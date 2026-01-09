"""Tests for run replay functionality."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from paracle_core.ids import generate_ulid
from paracle_runs import (
    AgentRunMetadata,
    RunStatus,
    WorkflowRunMetadata,
    replay_agent_run,
    replay_workflow_run,
    set_run_storage,
)
from paracle_runs.storage import RunStorage


@pytest.fixture
def temp_runs_dir():
    """Create temporary runs directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage(temp_runs_dir):
    """Create RunStorage instance with temp directory."""
    storage = RunStorage(temp_runs_dir)
    # Set as global storage for replay functions
    set_run_storage(storage)
    yield storage
    # Reset to None after test
    set_run_storage(None)


def test_replay_agent_run_basic(storage):
    """Test basic agent run replay."""
    run_id = generate_ulid()
    metadata = AgentRunMetadata(
        run_id=run_id,
        agent_id="coder",
        agent_name="Coder Agent",
        started_at=datetime.now(),
        completed_at=datetime.now(),
        status=RunStatus.COMPLETED,
        tokens_used=500,
        cost_usd=0.01,
    )

    input_data = {"prompt": "Fix bug in test.py"}
    output_data = {"result": "Fixed", "changes": ["line 10"]}

    storage.save_agent_run(
        metadata=metadata,
        input_data=input_data,
        output_data=output_data,
    )

    # Replay the run
    replay_metadata, replay_data = replay_agent_run(run_id)

    assert replay_metadata.run_id == run_id
    assert replay_metadata.agent_id == "coder"
    assert replay_data["input"]["prompt"] == "Fix bug in test.py"
    assert replay_data["output"]["result"] == "Fixed"


def test_replay_agent_run_with_artifacts(storage):
    """Test replaying agent run with artifacts."""
    run_id = generate_ulid()
    metadata = AgentRunMetadata(
        run_id=run_id,
        agent_id="coder",
        agent_name="Coder Agent",
        started_at=datetime.now(),
        status=RunStatus.COMPLETED,
        artifacts_count=2,
    )

    artifacts = {
        "test.py": "def test(): pass",
        "README.md": "# Test",
    }

    storage.save_agent_run(
        metadata=metadata,
        input_data={"prompt": "Test"},
        artifacts=artifacts,
    )

    # Replay the run
    replay_metadata, replay_data = replay_agent_run(run_id)

    assert replay_metadata.artifacts_count == 2
    assert "artifacts" in replay_data
    assert "test.py" in str(replay_data.get("artifacts", {}))


def test_replay_agent_run_with_logs(storage):
    """Test replaying agent run with execution logs."""
    run_id = generate_ulid()
    metadata = AgentRunMetadata(
        run_id=run_id,
        agent_id="coder",
        agent_name="Coder Agent",
        started_at=datetime.now(),
        status=RunStatus.COMPLETED,
    )

    logs = """
    [2026-01-08 10:00:00] Starting agent execution
    [2026-01-08 10:00:05] Processing input
    [2026-01-08 10:00:10] Execution completed
    """

    storage.save_agent_run(
        metadata=metadata,
        input_data={"prompt": "Test"},
        logs=logs,
    )

    # Replay the run
    replay_metadata, replay_data = replay_agent_run(run_id)

    assert "logs" in replay_data
    assert "Starting agent execution" in replay_data["logs"]


def test_replay_workflow_run_basic(storage):
    """Test basic workflow run replay."""
    run_id = generate_ulid()
    metadata = WorkflowRunMetadata(
        run_id=run_id,
        workflow_id="wf_123",
        workflow_name="Test Workflow",
        started_at=datetime.now(),
        completed_at=datetime.now(),
        status=RunStatus.COMPLETED,
        steps_total=2,
        steps_completed=2,
        agents_used=["coder", "tester"],
    )

    inputs = {"data": "test input"}
    outputs = {"result": "success"}
    steps = {
        "step1": {"agent": "coder", "input": "x", "output": "y"},
        "step2": {"agent": "tester", "input": "a", "output": "b"},
    }

    storage.save_workflow_run(
        metadata=metadata,
        inputs=inputs,
        outputs=outputs,
        steps=steps,
    )

    # Replay the run
    replay_metadata, replay_data = replay_workflow_run(run_id)

    assert replay_metadata.run_id == run_id
    assert replay_metadata.workflow_id == "wf_123"
    assert replay_metadata.steps_total == 2
    assert replay_data["inputs"]["data"] == "test input"
    assert replay_data["outputs"]["result"] == "success"


def test_replay_workflow_run_with_steps(storage):
    """Test replaying workflow run with step details."""
    run_id = generate_ulid()
    metadata = WorkflowRunMetadata(
        run_id=run_id,
        workflow_id="wf_123",
        workflow_name="Test Workflow",
        started_at=datetime.now(),
        status=RunStatus.COMPLETED,
        steps_total=3,
    )

    steps = {
        "step1": {
            "agent": "coder",
            "input": {"task": "write code"},
            "output": {"code": "def hello(): pass"},
        },
        "step2": {
            "agent": "tester",
            "input": {"code": "def hello(): pass"},
            "output": {"tests": "def test_hello(): pass"},
        },
        "step3": {
            "agent": "reviewer",
            "input": {"code": "def hello(): pass"},
            "output": {"approved": True},
        },
    }

    storage.save_workflow_run(
        metadata=metadata,
        inputs={},
        outputs={},
        steps=steps,
    )

    # Replay the run
    replay_metadata, replay_data = replay_workflow_run(run_id)

    assert len(replay_data["steps"]) == 3
    assert replay_data["steps"]["step1"]["agent"] == "coder"
    assert replay_data["steps"]["step2"]["agent"] == "tester"
    assert replay_data["steps"]["step3"]["agent"] == "reviewer"


def test_replay_workflow_run_with_logs(storage):
    """Test replaying workflow run with execution logs."""
    run_id = generate_ulid()
    metadata = WorkflowRunMetadata(
        run_id=run_id,
        workflow_id="wf_123",
        workflow_name="Test Workflow",
        started_at=datetime.now(),
        status=RunStatus.COMPLETED,
    )

    logs = """
    [2026-01-08 10:00:00] Workflow started
    [2026-01-08 10:00:05] Step 1 completed
    [2026-01-08 10:00:10] Step 2 completed
    [2026-01-08 10:00:15] Workflow completed
    """

    storage.save_workflow_run(
        metadata=metadata,
        inputs={},
        outputs={},
        logs=logs,
    )

    # Replay the run
    replay_metadata, replay_data = replay_workflow_run(run_id)

    assert "logs" in replay_data
    assert "Workflow started" in replay_data["logs"]


def test_replay_nonexistent_agent_run():
    """Test replaying agent run that doesn't exist."""
    with pytest.raises(FileNotFoundError):
        replay_agent_run("nonexistent_run_id")


def test_replay_nonexistent_workflow_run():
    """Test replaying workflow run that doesn't exist."""
    with pytest.raises(FileNotFoundError):
        replay_workflow_run("nonexistent_run_id")


def test_replay_failed_agent_run(storage):
    """Test replaying failed agent run."""
    run_id = generate_ulid()
    metadata = AgentRunMetadata(
        run_id=run_id,
        agent_id="coder",
        agent_name="Coder Agent",
        started_at=datetime.now(),
        completed_at=datetime.now(),
        status=RunStatus.FAILED,
        error_count=1,
        error_message="Execution failed: Invalid input",
    )

    input_data = {"prompt": "Invalid"}
    output_data = None

    storage.save_agent_run(
        metadata=metadata,
        input_data=input_data,
        output_data=output_data,
    )

    # Replay should still work for failed runs
    replay_metadata, replay_data = replay_agent_run(run_id)

    assert replay_metadata.status == RunStatus.FAILED
    assert replay_metadata.error_message == "Execution failed: Invalid input"
    assert replay_data["input"]["prompt"] == "Invalid"


def test_replay_failed_workflow_run(storage):
    """Test replaying failed workflow run."""
    run_id = generate_ulid()
    metadata = WorkflowRunMetadata(
        run_id=run_id,
        workflow_id="wf_123",
        workflow_name="Test Workflow",
        started_at=datetime.now(),
        completed_at=datetime.now(),
        status=RunStatus.FAILED,
        steps_total=3,
        steps_completed=1,
        steps_failed=2,
        error_message="Steps 2 and 3 failed",
    )

    storage.save_workflow_run(
        metadata=metadata,
        inputs={"data": "test"},
        outputs=None,
    )

    # Replay should work for failed workflows
    replay_metadata, replay_data = replay_workflow_run(run_id)

    assert replay_metadata.status == RunStatus.FAILED
    assert replay_metadata.steps_failed == 2
    assert "Steps 2 and 3 failed" in replay_metadata.error_message


def test_replay_with_trace_data(storage):
    """Test replaying run with OpenTelemetry trace data."""
    run_id = generate_ulid()
    metadata = AgentRunMetadata(
        run_id=run_id,
        agent_id="coder",
        agent_name="Coder Agent",
        started_at=datetime.now(),
        status=RunStatus.COMPLETED,
    )

    trace_data = {
        "trace_id": "abc123",
        "spans": [
            {"name": "agent_execution", "duration_ms": 100},
            {"name": "llm_call", "duration_ms": 50},
        ],
    }

    storage.save_agent_run(
        metadata=metadata,
        input_data={"prompt": "Test"},
        trace=trace_data,
    )

    # Replay the run
    replay_metadata, replay_data = replay_agent_run(run_id)

    assert "trace" in replay_data
    assert replay_data["trace"]["trace_id"] == "abc123"
    assert len(replay_data["trace"]["spans"]) == 2


def test_replay_preserves_metadata(storage):
    """Test that replay preserves all metadata fields."""
    run_id = generate_ulid()
    started_at = datetime.now()
    completed_at = datetime.now()

    metadata = AgentRunMetadata(
        run_id=run_id,
        agent_id="coder",
        agent_name="Coder Agent",
        started_at=started_at,
        completed_at=completed_at,
        duration_seconds=120.5,
        status=RunStatus.COMPLETED,
        tokens_used=5000,
        cost_usd=0.15,
        artifacts_count=3,
        error_count=0,
    )

    storage.save_agent_run(metadata=metadata, input_data={})

    # Replay and verify all metadata preserved
    replay_metadata, _ = replay_agent_run(run_id)

    assert replay_metadata.run_id == run_id
    assert replay_metadata.agent_id == "coder"
    assert replay_metadata.duration_seconds == 120.5
    assert replay_metadata.tokens_used == 5000
    assert replay_metadata.cost_usd == 0.15
    assert replay_metadata.artifacts_count == 3
