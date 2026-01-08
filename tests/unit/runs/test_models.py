"""Tests for run models."""

from datetime import datetime

from paracle_core.ids import generate_ulid
from paracle_runs.models import (
    AgentRunMetadata,
    RunQuery,
    RunStatus,
    WorkflowRunMetadata,
)


def test_run_status_enum():
    """Test RunStatus enum values."""
    assert RunStatus.PENDING.value == "pending"
    assert RunStatus.RUNNING.value == "running"
    assert RunStatus.COMPLETED.value == "completed"
    assert RunStatus.FAILED.value == "failed"
    assert RunStatus.TIMEOUT.value == "timeout"


def test_run_status_from_string():
    """Test creating RunStatus from string."""
    assert RunStatus("pending") == RunStatus.PENDING
    assert RunStatus("completed") == RunStatus.COMPLETED
    assert RunStatus("failed") == RunStatus.FAILED


def test_agent_run_metadata_minimal():
    """Test creating agent run metadata with minimal fields."""
    metadata = AgentRunMetadata(
        run_id=generate_ulid(),
        agent_id="coder",
        agent_name="Coder Agent",
        started_at=datetime.now(),
        status=RunStatus.PENDING,
    )

    assert metadata.run_id
    assert metadata.agent_id == "coder"
    assert metadata.agent_name == "Coder Agent"
    assert metadata.status == RunStatus.PENDING
    assert metadata.completed_at is None
    assert metadata.duration_seconds is None
    assert metadata.tokens_used is None
    assert metadata.cost_usd is None


def test_agent_run_metadata_full():
    """Test creating agent run metadata with all fields."""
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
        error_message=None,
    )

    assert metadata.run_id == run_id
    assert metadata.agent_id == "coder"
    assert metadata.completed_at == completed_at
    assert metadata.duration_seconds == 120.5
    assert metadata.status == RunStatus.COMPLETED
    assert metadata.tokens_used == 5000
    assert metadata.cost_usd == 0.15
    assert metadata.artifacts_count == 3
    assert metadata.error_count == 0


def test_agent_run_metadata_with_error():
    """Test agent run metadata with error information."""
    metadata = AgentRunMetadata(
        run_id=generate_ulid(),
        agent_id="coder",
        agent_name="Coder Agent",
        started_at=datetime.now(),
        completed_at=datetime.now(),
        status=RunStatus.FAILED,
        error_count=1,
        error_message="Execution failed: Invalid input",
    )

    assert metadata.status == RunStatus.FAILED
    assert metadata.error_count == 1
    assert metadata.error_message == "Execution failed: Invalid input"


def test_workflow_run_metadata_minimal():
    """Test creating workflow run metadata with minimal fields."""
    metadata = WorkflowRunMetadata(
        run_id=generate_ulid(),
        workflow_id="wf_123",
        workflow_name="Test Workflow",
        started_at=datetime.now(),
        status=RunStatus.RUNNING,
    )

    assert metadata.run_id
    assert metadata.workflow_id == "wf_123"
    assert metadata.workflow_name == "Test Workflow"
    assert metadata.status == RunStatus.RUNNING
    assert metadata.steps_total == 0
    assert metadata.steps_completed == 0
    assert metadata.agents_used == []


def test_workflow_run_metadata_full():
    """Test creating workflow run metadata with all fields."""
    run_id = generate_ulid()
    started_at = datetime.now()
    completed_at = datetime.now()

    metadata = WorkflowRunMetadata(
        run_id=run_id,
        workflow_id="wf_123",
        workflow_name="Test Workflow",
        started_at=started_at,
        completed_at=completed_at,
        duration_seconds=300.0,
        status=RunStatus.COMPLETED,
        steps_total=5,
        steps_completed=5,
        steps_failed=0,
        agents_used=["coder", "tester", "reviewer"],
        tokens_total=10000,
        cost_total_usd=0.50,
        error_message=None,
    )

    assert metadata.run_id == run_id
    assert metadata.workflow_id == "wf_123"
    assert metadata.duration_seconds == 300.0
    assert metadata.steps_total == 5
    assert metadata.steps_completed == 5
    assert metadata.steps_failed == 0
    assert len(metadata.agents_used) == 3
    assert "coder" in metadata.agents_used
    assert metadata.tokens_total == 10000
    assert metadata.cost_total_usd == 0.50


def test_workflow_run_metadata_with_failures():
    """Test workflow run metadata with failed steps."""
    metadata = WorkflowRunMetadata(
        run_id=generate_ulid(),
        workflow_id="wf_123",
        workflow_name="Test Workflow",
        started_at=datetime.now(),
        completed_at=datetime.now(),
        status=RunStatus.COMPLETED,
        steps_total=5,
        steps_completed=3,
        steps_failed=2,
        agents_used=["coder", "tester"],
        error_message="2 steps failed",
    )

    assert metadata.steps_total == 5
    assert metadata.steps_completed == 3
    assert metadata.steps_failed == 2
    assert metadata.error_message == "2 steps failed"


def test_run_query_defaults():
    """Test RunQuery with default values."""
    query = RunQuery()

    assert query.agent_id is None
    assert query.workflow_id is None
    assert query.status is None
    assert query.since is None
    assert query.until is None
    assert query.limit == 20
    assert query.offset == 0


def test_run_query_with_filters():
    """Test RunQuery with filter values."""
    since = datetime.now()
    until = datetime.now()

    query = RunQuery(
        agent_id="coder",
        workflow_id="wf_123",
        status=RunStatus.COMPLETED,
        since=since,
        until=until,
        limit=50,
        offset=10,
    )

    assert query.agent_id == "coder"
    assert query.workflow_id == "wf_123"
    assert query.status == RunStatus.COMPLETED
    assert query.since == since
    assert query.until == until
    assert query.limit == 50
    assert query.offset == 10


def test_run_query_agent_only():
    """Test RunQuery for specific agent."""
    query = RunQuery(agent_id="coder", limit=20)

    assert query.agent_id == "coder"
    assert query.workflow_id is None
    assert query.limit == 20


def test_run_query_workflow_only():
    """Test RunQuery for specific workflow."""
    query = RunQuery(workflow_id="wf_123", limit=30)

    assert query.workflow_id == "wf_123"
    assert query.agent_id is None
    assert query.limit == 30


def test_run_query_status_filter():
    """Test RunQuery with status filter."""
    query = RunQuery(status=RunStatus.FAILED)

    assert query.status == RunStatus.FAILED


def test_run_query_date_range():
    """Test RunQuery with date range."""
    since = datetime(2026, 1, 1)
    until = datetime(2026, 1, 31)

    query = RunQuery(since=since, until=until)

    assert query.since == since
    assert query.until == until


def test_run_query_pagination():
    """Test RunQuery pagination."""
    # First page
    query1 = RunQuery(limit=10, offset=0)
    assert query1.limit == 10
    assert query1.offset == 0

    # Second page
    query2 = RunQuery(limit=10, offset=10)
    assert query2.limit == 10
    assert query2.offset == 10


def test_agent_run_metadata_dict_conversion():
    """Test converting agent run metadata to dict."""
    metadata = AgentRunMetadata(
        run_id=generate_ulid(),
        agent_id="coder",
        agent_name="Coder Agent",
        started_at=datetime.now(),
        status=RunStatus.COMPLETED,
        tokens_used=1000,
        cost_usd=0.05,
    )

    data = metadata.model_dump()

    assert data["agent_id"] == "coder"
    assert data["status"] == RunStatus.COMPLETED
    assert data["tokens_used"] == 1000
    assert data["cost_usd"] == 0.05


def test_workflow_run_metadata_dict_conversion():
    """Test converting workflow run metadata to dict."""
    metadata = WorkflowRunMetadata(
        run_id=generate_ulid(),
        workflow_id="wf_123",
        workflow_name="Test Workflow",
        started_at=datetime.now(),
        status=RunStatus.COMPLETED,
        steps_total=3,
        agents_used=["coder", "tester"],
    )

    data = metadata.model_dump()

    assert data["workflow_id"] == "wf_123"
    assert data["steps_total"] == 3
    assert "coder" in data["agents_used"]


def test_agent_run_metadata_json_serialization():
    """Test JSON serialization of agent run metadata."""
    metadata = AgentRunMetadata(
        run_id=generate_ulid(),
        agent_id="coder",
        agent_name="Coder Agent",
        started_at=datetime.now(),
        status=RunStatus.COMPLETED,
    )

    json_str = metadata.model_dump_json()
    assert isinstance(json_str, str)
    assert "coder" in json_str
    assert "completed" in json_str


def test_workflow_run_metadata_json_serialization():
    """Test JSON serialization of workflow run metadata."""
    metadata = WorkflowRunMetadata(
        run_id=generate_ulid(),
        workflow_id="wf_123",
        workflow_name="Test Workflow",
        started_at=datetime.now(),
        status=RunStatus.COMPLETED,
    )

    json_str = metadata.model_dump_json()
    assert isinstance(json_str, str)
    assert "wf_123" in json_str
    assert "completed" in json_str
