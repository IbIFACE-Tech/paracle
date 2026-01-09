"""Integration tests for Workflow Execution API endpoints.

Tests the workflow execution system with real WorkflowEngine integration.
Phase 4 - Deferred from Phase 3.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from paracle_api.main import app
from paracle_api.routers import workflow_crud, workflow_execution
from paracle_domain.models import Workflow, WorkflowSpec, WorkflowStep
from paracle_orchestration.context import ExecutionStatus


class TestWorkflowExecution:
    """Tests for /api/workflows execution endpoints."""

    @pytest.fixture(autouse=True)
    def reset_repositories(self) -> None:
        """Reset repositories before each test."""
        from paracle_api.routers import workflow_crud, workflow_execution

        workflow_crud._repository.clear()
        workflow_execution._repository.clear()
        # Make sure they share the same repository instance
        workflow_execution._repository = workflow_crud._repository
        # Reset engine state if needed
        workflow_execution._engine = MagicMock()

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_workflow(self) -> Workflow:
        """Create a sample workflow for testing."""
        spec = WorkflowSpec(
            name=f"test-workflow-{uuid.uuid4().hex[:8]}",
            description="Test workflow for execution",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="First step",
                    agent="test-agent",
                    prompt="Execute first step",
                    depends_on=[],
                ),
                WorkflowStep(
                    id="step2",
                    name="Second step",
                    agent="test-agent",
                    prompt="Execute second step",
                    depends_on=["step1"],
                ),
            ],
        )
        workflow = Workflow(spec=spec)
        return workflow_crud._repository.add(workflow)

    # =========================================================================
    # POST /api/workflows/execute - Execute Workflow
    # =========================================================================

    def test_execute_workflow_async(
        self, client: TestClient, sample_workflow: Workflow
    ) -> None:
        """Test executing a workflow asynchronously."""
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"

        # Mock engine execute_async
        async def mock_execute_async(workflow, inputs):
            return execution_id

        workflow_execution._engine.execute_async = AsyncMock(
            side_effect=mock_execute_async
        )

        response = client.post(
            "/api/workflows/execute",
            json={
                "workflow_id": sample_workflow.id,
                "inputs": {"param1": "value1"},
                "async_execution": True,
            },
        )

        assert response.status_code == 202
        data = response.json()
        assert data["execution_id"] == execution_id
        assert data["workflow_id"] == sample_workflow.id
        assert data["status"] == "pending"
        assert data["async_execution"] is True
        assert "started in background" in data["message"].lower()

    def test_execute_workflow_sync(
        self, client: TestClient, sample_workflow: Workflow
    ) -> None:
        """Test executing a workflow synchronously."""
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"

        # Mock engine execute (synchronous)
        mock_result = MagicMock()
        mock_result.execution_id = execution_id
        mock_result.success = True

        async def mock_execute(workflow, inputs):
            return mock_result

        workflow_execution._engine.execute = AsyncMock(side_effect=mock_execute)

        response = client.post(
            "/api/workflows/execute",
            json={
                "workflow_id": sample_workflow.id,
                "inputs": {},
                "async_execution": False,
            },
        )

        assert response.status_code == 202
        data = response.json()
        assert data["execution_id"] == execution_id
        assert data["status"] == "completed"
        assert data["async_execution"] is False

    def test_execute_workflow_not_found(self, client: TestClient) -> None:
        """Test executing a non-existent workflow."""
        response = client.post(
            "/api/workflows/execute",
            json={
                "workflow_id": "non-existent-workflow",
                "inputs": {},
            },
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_execute_workflow_with_inputs(
        self, client: TestClient, sample_workflow: Workflow
    ) -> None:
        """Test executing workflow with custom inputs."""
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"

        # Capture the inputs passed to engine
        captured_inputs = None

        async def mock_execute_async(workflow, inputs):
            nonlocal captured_inputs
            captured_inputs = inputs
            return execution_id

        workflow_execution._engine.execute_async = AsyncMock(
            side_effect=mock_execute_async
        )

        custom_inputs = {
            "source_file": "data.csv",
            "target_format": "json",
            "validate": True,
        }

        response = client.post(
            "/api/workflows/execute",
            json={
                "workflow_id": sample_workflow.id,
                "inputs": custom_inputs,
            },
        )

        assert response.status_code == 202
        assert captured_inputs == custom_inputs

    # =========================================================================
    # GET /api/workflows/executions/{execution_id} - Get Status
    # =========================================================================

    def test_get_execution_status_running(
        self, client: TestClient, sample_workflow: Workflow
    ) -> None:
        """Test getting status of a running execution."""
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"

        # Mock execution status
        mock_status = MagicMock(spec=ExecutionStatus)
        mock_status.execution_id = execution_id
        mock_status.workflow_id = sample_workflow.id
        mock_status.status = "running"
        mock_status.progress = 0.5
        mock_status.current_step = "step1"
        mock_status.completed_steps = []
        mock_status.failed_steps = []
        mock_status.started_at = None
        mock_status.completed_at = None
        mock_status.error = None
        mock_status.result = None

        async def mock_get_status(exec_id):
            return mock_status

        workflow_execution._engine.get_execution_status = AsyncMock(
            side_effect=mock_get_status
        )

        response = client.get(f"/api/workflows/executions/{execution_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["execution_id"] == execution_id
        assert data["workflow_id"] == sample_workflow.id
        assert data["status"] == "running"
        assert data["progress"] == 0.5
        assert data["current_step"] == "step1"

    def test_get_execution_status_completed(
        self, client: TestClient, sample_workflow: Workflow
    ) -> None:
        """Test getting status of a completed execution."""
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"

        # Mock completed execution
        from datetime import datetime, timezone

        mock_status = MagicMock(spec=ExecutionStatus)
        mock_status.execution_id = execution_id
        mock_status.workflow_id = sample_workflow.id
        mock_status.status = "completed"
        mock_status.progress = 1.0
        mock_status.current_step = None
        mock_status.completed_steps = ["step1", "step2"]
        mock_status.failed_steps = []
        mock_status.started_at = datetime.now(timezone.utc)
        mock_status.completed_at = datetime.now(timezone.utc)
        mock_status.error = None
        mock_status.result = {"output": "success"}

        async def mock_get_status(exec_id):
            return mock_status

        workflow_execution._engine.get_execution_status = AsyncMock(
            side_effect=mock_get_status
        )

        response = client.get(f"/api/workflows/executions/{execution_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress"] == 1.0
        assert data["completed_steps"] == ["step1", "step2"]
        assert data["result"] == {"output": "success"}

    def test_get_execution_status_failed(
        self, client: TestClient, sample_workflow: Workflow
    ) -> None:
        """Test getting status of a failed execution."""
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"

        mock_status = MagicMock(spec=ExecutionStatus)
        mock_status.execution_id = execution_id
        mock_status.workflow_id = sample_workflow.id
        mock_status.status = "failed"
        mock_status.progress = 0.5
        mock_status.current_step = "step2"
        mock_status.completed_steps = ["step1"]
        mock_status.failed_steps = ["step2"]
        mock_status.started_at = None
        mock_status.completed_at = None
        mock_status.error = "Step2 execution failed: timeout"
        mock_status.result = None

        async def mock_get_status(exec_id):
            return mock_status

        workflow_execution._engine.get_execution_status = AsyncMock(
            side_effect=mock_get_status
        )

        response = client.get(f"/api/workflows/executions/{execution_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["failed_steps"] == ["step2"]
        assert "timeout" in data["error"]

    def test_get_execution_status_not_found(self, client: TestClient) -> None:
        """Test getting status of non-existent execution."""
        from paracle_orchestration.exceptions import WorkflowNotFoundError

        async def mock_get_status(exec_id):
            raise WorkflowNotFoundError(f"Execution {exec_id} not found")

        workflow_execution._engine.get_execution_status = AsyncMock(
            side_effect=mock_get_status
        )

        response = client.get("/api/workflows/executions/non-existent-exec")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    # =========================================================================
    # POST /api/workflows/executions/{execution_id}/cancel - Cancel Execution
    # =========================================================================

    def test_cancel_execution_success(
        self, client: TestClient, sample_workflow: Workflow
    ) -> None:
        """Test successfully cancelling a running execution."""
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"

        # Mock cancel and status
        async def mock_cancel(exec_id):
            return True

        mock_status = MagicMock(spec=ExecutionStatus)
        mock_status.execution_id = execution_id
        mock_status.workflow_id = sample_workflow.id

        async def mock_get_status(exec_id):
            return mock_status

        workflow_execution._engine.cancel_execution = AsyncMock(side_effect=mock_cancel)
        workflow_execution._engine.get_execution_status = AsyncMock(
            side_effect=mock_get_status
        )

        response = client.post(f"/api/workflows/executions/{execution_id}/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["execution_id"] == execution_id
        assert data["success"] is True
        assert "cancelled successfully" in data["message"].lower()

    def test_cancel_execution_already_completed(
        self, client: TestClient, sample_workflow: Workflow
    ) -> None:
        """Test cancelling an already completed execution."""
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"

        # Mock cancel returning False (already completed)
        async def mock_cancel(exec_id):
            return False

        mock_status = MagicMock(spec=ExecutionStatus)
        mock_status.execution_id = execution_id
        mock_status.workflow_id = sample_workflow.id

        async def mock_get_status(exec_id):
            return mock_status

        workflow_execution._engine.cancel_execution = AsyncMock(side_effect=mock_cancel)
        workflow_execution._engine.get_execution_status = AsyncMock(
            side_effect=mock_get_status
        )

        response = client.post(f"/api/workflows/executions/{execution_id}/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "already completed" in data["message"].lower()

    def test_cancel_execution_not_found(self, client: TestClient) -> None:
        """Test cancelling a non-existent execution."""
        from paracle_orchestration.exceptions import WorkflowNotFoundError

        async def mock_cancel(exec_id):
            raise WorkflowNotFoundError(f"Execution {exec_id} not found")

        workflow_execution._engine.cancel_execution = AsyncMock(side_effect=mock_cancel)

        response = client.post("/api/workflows/executions/non-existent-exec/cancel")

        assert response.status_code == 404

    # =========================================================================
    # GET /api/workflows/{workflow_id}/executions - List Executions
    # =========================================================================

    def test_list_workflow_executions(
        self, client: TestClient, sample_workflow: Workflow
    ) -> None:
        """Test listing all executions for a workflow."""
        # Mock list of executions
        mock_executions = []
        for i in range(3):
            mock_exec = MagicMock(spec=ExecutionStatus)
            mock_exec.execution_id = f"exec_{i}"
            mock_exec.workflow_id = sample_workflow.id
            mock_exec.status = ["completed", "running", "failed"][i]
            mock_exec.progress = [1.0, 0.5, 0.3][i]
            mock_exec.current_step = [None, "step2", "step1"][i]
            mock_exec.completed_steps = [["step1", "step2"], ["step1"], []][i]
            mock_exec.failed_steps = [[], [], ["step1"]][i]
            mock_exec.started_at = None
            mock_exec.completed_at = None
            mock_exec.error = None
            mock_exec.result = None
            mock_executions.append(mock_exec)

        async def mock_list_executions(workflow_id, status_filter):
            return mock_executions

        workflow_execution._engine.list_executions = AsyncMock(
            side_effect=mock_list_executions
        )

        response = client.get(f"/api/workflows/{sample_workflow.id}/executions")

        assert response.status_code == 200
        data = response.json()
        assert "executions" in data
        assert data["total"] == 3
        assert len(data["executions"]) == 3

    def test_list_workflow_executions_with_filter(
        self, client: TestClient, sample_workflow: Workflow
    ) -> None:
        """Test listing executions with status filter."""
        # Mock only running executions
        mock_exec = MagicMock(spec=ExecutionStatus)
        mock_exec.execution_id = "exec_running"
        mock_exec.workflow_id = sample_workflow.id
        mock_exec.status = "running"
        mock_exec.progress = 0.5
        mock_exec.current_step = "step2"
        mock_exec.completed_steps = ["step1"]
        mock_exec.failed_steps = []
        mock_exec.started_at = None
        mock_exec.completed_at = None
        mock_exec.error = None
        mock_exec.result = None

        async def mock_list_executions(workflow_id, status_filter):
            if status_filter == "running":
                return [mock_exec]
            return []

        workflow_execution._engine.list_executions = AsyncMock(
            side_effect=mock_list_executions
        )

        response = client.get(
            f"/api/workflows/{sample_workflow.id}/executions?status=running"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["executions"][0]["status"] == "running"

    def test_list_workflow_executions_pagination(
        self, client: TestClient, sample_workflow: Workflow
    ) -> None:
        """Test pagination of execution list."""
        # Create 10 mock executions
        mock_executions = []
        for i in range(10):
            mock_exec = MagicMock(spec=ExecutionStatus)
            mock_exec.execution_id = f"exec_{i}"
            mock_exec.workflow_id = sample_workflow.id
            mock_exec.status = "completed"
            mock_exec.progress = 1.0
            mock_exec.current_step = None
            mock_exec.completed_steps = ["step1", "step2"]
            mock_exec.failed_steps = []
            mock_exec.started_at = None
            mock_exec.completed_at = None
            mock_exec.error = None
            mock_exec.result = None
            mock_executions.append(mock_exec)

        async def mock_list_executions(workflow_id, status_filter):
            return mock_executions

        workflow_execution._engine.list_executions = AsyncMock(
            side_effect=mock_list_executions
        )

        response = client.get(
            f"/api/workflows/{sample_workflow.id}/executions?limit=5&offset=0"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert data["limit"] == 5
        assert data["offset"] == 0
        assert len(data["executions"]) == 5

    def test_list_executions_workflow_not_found(self, client: TestClient) -> None:
        """Test listing executions for non-existent workflow."""
        response = client.get("/api/workflows/non-existent-workflow/executions")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
