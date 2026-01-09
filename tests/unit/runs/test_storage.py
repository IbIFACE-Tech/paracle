"""Tests for run storage functionality."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import yaml
from paracle_core.ids import generate_ulid
from paracle_runs import (
    AgentRunMetadata,
    RunStatus,
    WorkflowRunMetadata,
    get_run_storage,
)
from paracle_runs.models import RunQuery
from paracle_runs.storage import RunStorage


@pytest.fixture
def temp_runs_dir():
    """Create temporary runs directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage(temp_runs_dir):
    """Create RunStorage instance with temp directory."""
    return RunStorage(temp_runs_dir)


def test_agent_run_metadata_creation():
    """Test creating agent run metadata."""
    metadata = AgentRunMetadata(
        run_id=generate_ulid(),
        agent_id="coder",
        agent_name="Coder Agent",
        started_at=datetime.now(),
        status=RunStatus.COMPLETED,
        tokens_used=1000,
        cost_usd=0.01,
    )

    assert metadata.run_id
    assert metadata.agent_id == "coder"
    assert metadata.status == RunStatus.COMPLETED
    assert metadata.tokens_used == 1000
    assert metadata.cost_usd == 0.01


def test_workflow_run_metadata_creation():
    """Test creating workflow run metadata."""
    metadata = WorkflowRunMetadata(
        run_id=generate_ulid(),
        workflow_id="wf_123",
        workflow_name="Test Workflow",
        started_at=datetime.now(),
        status=RunStatus.COMPLETED,
        steps_total=5,
        steps_completed=5,
        agents_used=["coder", "tester"],
    )

    assert metadata.run_id
    assert metadata.workflow_id == "wf_123"
    assert metadata.steps_total == 5
    assert metadata.steps_completed == 5
    assert len(metadata.agents_used) == 2


def test_save_agent_run(storage):
    """Test saving agent run data."""
    metadata = AgentRunMetadata(
        run_id=generate_ulid(),
        agent_id="coder",
        agent_name="Coder Agent",
        started_at=datetime.now(),
        completed_at=datetime.now(),
        duration_seconds=10.5,
        status=RunStatus.COMPLETED,
        tokens_used=500,
        cost_usd=0.005,
    )

    input_data = {"prompt": "Fix bug", "context": {"file": "test.py"}}
    output_data = {"result": "Fixed", "changes": ["line 10"]}
    artifacts = {"test.py": "def test(): pass"}

    run_dir = storage.save_agent_run(
        metadata=metadata,
        input_data=input_data,
        output_data=output_data,
        artifacts=artifacts,
        logs="Execution log",
    )

    assert run_dir.exists()
    assert (run_dir / "metadata.yaml").exists()
    assert (run_dir / "input.json").exists()
    assert (run_dir / "output.json").exists()
    assert (run_dir / "artifacts" / "artifacts.json").exists()
    assert (run_dir / "logs.txt").exists()


def test_save_workflow_run(storage):
    """Test saving workflow run data."""
    metadata = WorkflowRunMetadata(
        run_id=generate_ulid(),
        workflow_id="wf_123",
        workflow_name="Test Workflow",
        started_at=datetime.now(),
        completed_at=datetime.now(),
        duration_seconds=30.0,
        status=RunStatus.COMPLETED,
        steps_total=3,
        steps_completed=3,
        agents_used=["coder", "tester"],
    )

    inputs = {"data": "test"}
    outputs = {"result": "success"}
    steps = {
        "step1": {"input": "x", "output": "y"},
        "step2": {"input": "a", "output": "b"},
    }

    run_dir = storage.save_workflow_run(
        metadata=metadata,
        inputs=inputs,
        outputs=outputs,
        steps=steps,
        logs="Workflow log",
    )

    assert run_dir.exists()
    assert (run_dir / "metadata.yaml").exists()
    assert (run_dir / "inputs.json").exists()
    assert (run_dir / "outputs.json").exists()
    assert (run_dir / "steps").exists()
    assert (run_dir / "steps" / "step1.json").exists()
    assert (run_dir / "logs.txt").exists()


def test_load_agent_run(storage):
    """Test loading agent run data."""
    run_id = generate_ulid()
    metadata = AgentRunMetadata(
        run_id=run_id,
        agent_id="coder",
        agent_name="Coder Agent",
        started_at=datetime.now(),
        status=RunStatus.COMPLETED,
    )

    input_data = {"prompt": "Test"}
    output_data = {"result": "Done"}

    storage.save_agent_run(
        metadata=metadata, input_data=input_data, output_data=output_data
    )

    loaded_metadata, run_data = storage.load_agent_run(run_id)

    assert loaded_metadata.run_id == run_id
    assert loaded_metadata.agent_id == "coder"
    assert run_data["input"]["prompt"] == "Test"
    assert run_data["output"]["result"] == "Done"


def test_load_workflow_run(storage):
    """Test loading workflow run data."""
    run_id = generate_ulid()
    metadata = WorkflowRunMetadata(
        run_id=run_id,
        workflow_id="wf_123",
        workflow_name="Test Workflow",
        started_at=datetime.now(),
        status=RunStatus.COMPLETED,
    )

    inputs = {"data": "test"}
    outputs = {"result": "success"}

    storage.save_workflow_run(metadata=metadata, inputs=inputs, outputs=outputs)

    loaded_metadata, run_data = storage.load_workflow_run(run_id)

    assert loaded_metadata.run_id == run_id
    assert loaded_metadata.workflow_id == "wf_123"
    assert run_data["inputs"]["data"] == "test"
    assert run_data["outputs"]["result"] == "success"


def test_load_nonexistent_run(storage):
    """Test loading run that doesn't exist."""
    with pytest.raises(FileNotFoundError):
        storage.load_agent_run("nonexistent_run_id")

    with pytest.raises(FileNotFoundError):
        storage.load_workflow_run("nonexistent_run_id")


def test_list_agent_runs(storage):
    """Test listing agent runs."""
    # Create multiple runs
    for i in range(5):
        metadata = AgentRunMetadata(
            run_id=generate_ulid(),
            agent_id=f"agent_{i}",
            agent_name=f"Agent {i}",
            started_at=datetime.now(),
            status=RunStatus.COMPLETED,
        )
        storage.save_agent_run(metadata=metadata, input_data={})

    runs = storage.list_agent_runs()
    assert len(runs) == 5


def test_list_workflow_runs(storage):
    """Test listing workflow runs."""
    # Create multiple runs
    for i in range(3):
        metadata = WorkflowRunMetadata(
            run_id=generate_ulid(),
            workflow_id=f"wf_{i}",
            workflow_name=f"Workflow {i}",
            started_at=datetime.now(),
            status=RunStatus.COMPLETED,
        )
        storage.save_workflow_run(metadata=metadata, inputs={})

    runs = storage.list_workflow_runs()
    assert len(runs) == 3


def test_list_runs_with_query(storage):
    """Test listing runs with query filters."""
    # Create runs with different statuses
    for status in [RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.PENDING]:
        metadata = AgentRunMetadata(
            run_id=generate_ulid(),
            agent_id="coder",
            agent_name="Coder Agent",
            started_at=datetime.now(),
            status=status,
        )
        storage.save_agent_run(metadata=metadata, input_data={})

    # Query for completed runs only
    query = RunQuery(status=RunStatus.COMPLETED, limit=10)
    completed_runs = storage.list_agent_runs(query)
    assert all(r.status == RunStatus.COMPLETED for r in completed_runs)

    # Query for specific agent
    query = RunQuery(agent_id="coder", limit=10)
    agent_runs = storage.list_agent_runs(query)
    assert all(r.agent_id == "coder" for r in agent_runs)


def test_list_runs_with_date_filter(storage):
    """Test listing runs with date filters."""
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    tomorrow = now + timedelta(days=1)

    # Create run from yesterday
    old_metadata = AgentRunMetadata(
        run_id=generate_ulid(),
        agent_id="coder",
        agent_name="Coder Agent",
        started_at=yesterday,
        status=RunStatus.COMPLETED,
    )
    storage.save_agent_run(metadata=old_metadata, input_data={})

    # Create run from today
    new_metadata = AgentRunMetadata(
        run_id=generate_ulid(),
        agent_id="coder",
        agent_name="Coder Agent",
        started_at=now,
        status=RunStatus.COMPLETED,
    )
    storage.save_agent_run(metadata=new_metadata, input_data={})

    # Query for runs since today
    query = RunQuery(since=now - timedelta(hours=1), limit=10)
    recent_runs = storage.list_agent_runs(query)
    assert len(recent_runs) == 1
    assert recent_runs[0].started_at >= now - timedelta(hours=1)


def test_delete_agent_run(storage):
    """Test deleting agent run."""
    run_id = generate_ulid()
    metadata = AgentRunMetadata(
        run_id=run_id,
        agent_id="coder",
        agent_name="Coder Agent",
        started_at=datetime.now(),
        status=RunStatus.COMPLETED,
    )
    storage.save_agent_run(metadata=metadata, input_data={})

    # Verify run exists
    runs = storage.list_agent_runs()
    assert len(runs) == 1

    # Delete run
    deleted = storage.delete_run(run_id, "agent")
    assert deleted

    # Verify run is deleted
    runs = storage.list_agent_runs()
    assert len(runs) == 0


def test_delete_workflow_run(storage):
    """Test deleting workflow run."""
    run_id = generate_ulid()
    metadata = WorkflowRunMetadata(
        run_id=run_id,
        workflow_id="wf_123",
        workflow_name="Test Workflow",
        started_at=datetime.now(),
        status=RunStatus.COMPLETED,
    )
    storage.save_workflow_run(metadata=metadata, inputs={})

    # Delete run
    deleted = storage.delete_run(run_id, "workflow")
    assert deleted

    # Verify run is deleted
    runs = storage.list_workflow_runs()
    assert len(runs) == 0


def test_delete_nonexistent_run(storage):
    """Test deleting run that doesn't exist."""
    deleted = storage.delete_run("nonexistent_run_id", "agent")
    assert not deleted


def test_cleanup_old_runs(storage):
    """Test cleaning up old runs."""
    now = datetime.now()
    old_date = now - timedelta(days=40)

    # Create old run
    old_metadata = AgentRunMetadata(
        run_id=generate_ulid(),
        agent_id="coder",
        agent_name="Coder Agent",
        started_at=old_date,
        status=RunStatus.COMPLETED,
    )
    storage.save_agent_run(metadata=old_metadata, input_data={})

    # Create recent run
    new_metadata = AgentRunMetadata(
        run_id=generate_ulid(),
        agent_id="coder",
        agent_name="Coder Agent",
        started_at=now,
        status=RunStatus.COMPLETED,
    )
    storage.save_agent_run(metadata=new_metadata, input_data={})

    # Cleanup runs older than 30 days
    deleted_count = storage.cleanup_old_runs(max_age_days=30)
    assert deleted_count == 1

    # Verify only recent run remains
    runs = storage.list_agent_runs()
    assert len(runs) == 1
    assert runs[0].started_at >= now - timedelta(hours=1)


def test_cleanup_with_max_runs(storage):
    """Test cleanup with max runs limit."""
    # Create 10 runs
    for i in range(10):
        metadata = AgentRunMetadata(
            run_id=generate_ulid(),
            agent_id="coder",
            agent_name="Coder Agent",
            started_at=datetime.now(),
            status=RunStatus.COMPLETED,
        )
        storage.save_agent_run(metadata=metadata, input_data={})

    # Cleanup keeping only 5 most recent
    deleted_count = storage.cleanup_old_runs(max_age_days=365, max_runs=5)
    assert deleted_count == 5

    # Verify only 5 runs remain
    runs = storage.list_agent_runs()
    assert len(runs) == 5


def test_global_run_storage():
    """Test global run storage instance."""
    storage1 = get_run_storage()
    storage2 = get_run_storage()

    assert storage1 is storage2  # Same instance


def test_metadata_yaml_format(storage):
    """Test metadata is saved in YAML format."""
    run_id = generate_ulid()
    metadata = AgentRunMetadata(
        run_id=run_id,
        agent_id="coder",
        agent_name="Coder Agent",
        started_at=datetime.now(),
        status=RunStatus.COMPLETED,
    )
    storage.save_agent_run(metadata=metadata, input_data={})

    # Read metadata file directly
    metadata_file = storage.agents_dir / run_id / "metadata.yaml"
    with open(metadata_file) as f:
        data = yaml.safe_load(f)

    assert data["run_id"] == run_id
    assert data["agent_id"] == "coder"
    assert data["status"] == "completed"


def test_json_data_format(storage):
    """Test data is saved in JSON format."""
    run_id = generate_ulid()
    metadata = AgentRunMetadata(
        run_id=run_id,
        agent_id="coder",
        agent_name="Coder Agent",
        started_at=datetime.now(),
        status=RunStatus.COMPLETED,
    )
    input_data = {"prompt": "Test", "context": {"key": "value"}}
    storage.save_agent_run(metadata=metadata, input_data=input_data)

    # Read input file directly
    input_file = storage.agents_dir / run_id / "input.json"
    with open(input_file) as f:
        data = json.load(f)

    assert data["prompt"] == "Test"
    assert data["context"]["key"] == "value"
