"""Workflow execution API endpoints.

Phase 4: Real workflow execution with orchestration engine.
Deferred from Phase 3.

Endpoints:
- POST /api/workflows/execute - Execute workflow (create execution)
- GET /api/workflows/executions/{execution_id} - Get execution status
- POST /api/workflows/executions/{execution_id}/cancel - Cancel execution
- GET /api/workflows/{workflow_id}/executions - List workflow executions
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from paracle_domain.models import Workflow
from paracle_orchestration.dry_run import DryRunConfig, DryRunExecutor, MockStrategy
from paracle_orchestration.engine_wrapper import WorkflowEngine
from paracle_orchestration.exceptions import OrchestrationError, WorkflowNotFoundError
from paracle_orchestration.planner import WorkflowPlanner
from paracle_orchestration.workflow_loader import WorkflowLoader, WorkflowLoadError
from paracle_store.workflow_repository import WorkflowRepository
from pydantic import BaseModel, Field

# Global instances
_repository = WorkflowRepository()
_engine = WorkflowEngine()
_loader: WorkflowLoader | None = None


def _get_loader() -> WorkflowLoader | None:
    """Get or create workflow loader singleton."""
    global _loader
    if _loader is None:
        try:
            _loader = WorkflowLoader()
        except WorkflowLoadError:
            return None
    return _loader


router = APIRouter(prefix="/api/workflows", tags=["workflow_execution"])


# =============================================================================
# Request/Response Models
# =============================================================================


class WorkflowExecuteRequest(BaseModel):
    """Request to execute a workflow."""

    workflow_id: str = Field(..., description="Workflow ID to execute")
    inputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Input parameters for workflow",
    )
    async_execution: bool = Field(
        default=True, description="Run asynchronously (background)"
    )
    auto_approve: bool = Field(
        default=False, description="YOLO mode: auto-approve all approval gates"
    )
    dry_run: bool = Field(
        default=False, description="Dry-run mode: mock LLM calls for cost-free testing"
    )
    mock_strategy: str = Field(
        default="fixed",
        description="Mock strategy for dry-run (fixed/random/file/echo)",
    )


class ExecutionStatusResponse(BaseModel):
    """Response with execution status."""

    execution_id: str = Field(..., description="Unique execution ID")
    workflow_id: str = Field(..., description="Workflow being executed")
    status: str = Field(
        ..., description="Execution status (pending, running, completed, failed)"
    )
    progress: float = Field(
        ..., description="Execution progress (0.0 to 1.0)", ge=0.0, le=1.0
    )
    current_step: str | None = Field(None, description="Currently executing step")
    completed_steps: list[str] = Field(
        default_factory=list, description="Steps completed successfully"
    )
    failed_steps: list[str] = Field(
        default_factory=list, description="Steps that failed"
    )
    started_at: str | None = Field(None, description="Execution start time (ISO 8601)")
    completed_at: str | None = Field(
        None, description="Execution completion time (ISO 8601)"
    )
    error: str | None = Field(None, description="Error message if failed")
    result: dict[str, Any] | None = Field(
        None, description="Execution result if completed"
    )


class WorkflowExecuteResponse(BaseModel):
    """Response after initiating workflow execution."""

    execution_id: str = Field(..., description="Unique execution ID for tracking")
    workflow_id: str = Field(..., description="Workflow being executed")
    status: str = Field(..., description="Initial execution status")
    message: str = Field(..., description="Human-readable status message")
    async_execution: bool = Field(..., description="Whether execution is asynchronous")


class ExecutionCancelResponse(BaseModel):
    """Response after cancelling execution."""

    execution_id: str = Field(..., description="Execution ID that was cancelled")
    workflow_id: str = Field(..., description="Workflow that was cancelled")
    success: bool = Field(..., description="Whether cancellation succeeded")
    message: str = Field(..., description="Cancellation status message")


class ExecutionListResponse(BaseModel):
    """Response with list of executions."""

    executions: list[ExecutionStatusResponse] = Field(
        ..., description="List of executions"
    )
    total: int = Field(..., description="Total executions matching filters")
    limit: int = Field(..., description="Max results returned")
    offset: int = Field(..., description="Offset used for pagination")


# =============================================================================
# Workflow Execution Endpoints
# =============================================================================


@router.post(
    "/execute",
    response_model=WorkflowExecuteResponse,
    status_code=202,
    operation_id="executeWorkflow",
    summary="Execute a workflow",
    description="Create and execute a workflow (async by default)",
)
async def execute_workflow(request: WorkflowExecuteRequest) -> WorkflowExecuteResponse:
    """Execute a workflow using the orchestration engine.

    Creates a new execution and runs the workflow asynchronously by default.
    Returns immediately with execution ID for tracking.

    Args:
        request: Execution request with workflow ID and inputs

    Returns:
        Execution details with tracking ID

    Raises:
        HTTPException: 404 if workflow not found, 400 if workflow invalid

    Example:
        ```
        POST /api/workflows/execute
        {
            "workflow_id": "wf_01234567",
            "inputs": {"source": "data.csv", "target": "output.json"},
            "async_execution": true
        }
        ```
    """
    try:
        loader = _get_loader()
        workflow = None

        # Try loading from YAML files first
        if loader is not None:
            try:
                spec = loader.load_workflow_spec(request.workflow_id)
                workflow = Workflow(spec=spec)
            except WorkflowLoadError:
                pass

        # Fallback to repository
        if workflow is None:
            workflow = _repository.get(request.workflow_id)
            if workflow is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Workflow '{request.workflow_id}' not found",
                )

        # Handle dry-run mode
        if request.dry_run:
            config = DryRunConfig(
                strategy=MockStrategy(request.mock_strategy),
            )
            executor = DryRunExecutor(config)

            # Execute with mocked LLM calls
            result = await executor.execute_workflow(
                workflow=workflow,
                inputs=request.inputs,
            )

            return WorkflowExecuteResponse(
                execution_id=result["execution_id"],
                workflow_id=workflow.id,
                status="completed",
                message="Dry-run execution completed (no real LLM calls)",
                async_execution=False,
            )

        # Execute workflow
        if request.async_execution:
            # Asynchronous execution (background task)
            execution_id = await _engine.execute_async(
                workflow=workflow,
                inputs=request.inputs,
                auto_approve=request.auto_approve,
            )

            return WorkflowExecuteResponse(
                execution_id=execution_id,
                workflow_id=workflow.id,
                status="pending",
                message="Workflow execution started in background",
                async_execution=True,
            )
        else:
            # Synchronous execution (wait for completion)
            result = await _engine.execute(
                workflow=workflow,
                inputs=request.inputs,
                auto_approve=request.auto_approve,
            )

            return WorkflowExecuteResponse(
                execution_id=result.execution_id,
                workflow_id=workflow.id,
                status=result.status.value,
                message="Workflow execution completed",
                async_execution=False,
            )

    except WorkflowNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except OrchestrationError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{workflow_id}/plan",
    response_model=dict,
    operation_id="planWorkflow",
    summary="Plan workflow execution",
    description="Generate execution plan with cost/time estimates",
)
async def plan_workflow(workflow_id: str) -> dict:
    """Analyze workflow and generate execution plan.

    Returns execution plan with cost/time estimates, dependency analysis,
    and optimization suggestions without executing the workflow.

    Args:
        workflow_id: Workflow identifier

    Returns:
        Execution plan with analysis

    Raises:
        HTTPException: 404 if workflow not found

    Example:
        ```
        POST /api/workflows/wf_01234567/plan

        Returns:
        {
            "total_steps": 5,
            "execution_groups": [...],
            "estimated_cost_usd": 0.015,
            "estimated_time_seconds": 45,
            "approval_gates": [...],
            "optimization_suggestions": [...]
        }
        ```
    """
    try:
        loader = _get_loader()
        workflow = None

        # Try loading from YAML files first
        if loader is not None:
            try:
                spec = loader.load_workflow_spec(workflow_id)
                workflow = Workflow(spec=spec)
            except WorkflowLoadError:
                pass

        # Fallback to repository
        if workflow is None:
            workflow = _repository.get(workflow_id)
            if workflow is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Workflow '{workflow_id}' not found",
                )

        # Generate execution plan
        planner = WorkflowPlanner()
        plan = planner.plan(workflow)

        return {
            "workflow_id": workflow_id,
            "workflow_name": workflow.name or workflow_id,
            "total_steps": plan.total_steps,
            "execution_groups": [
                {
                    "group_number": g.group_number,
                    "steps": g.steps,
                    "can_parallelize": g.can_parallelize,
                }
                for g in plan.execution_groups
            ],
            "estimated_cost_usd": plan.estimated_cost_usd,
            "estimated_time_seconds": plan.estimated_time_seconds,
            "approval_gates": [
                {
                    "step_id": gate.step_id,
                    "approver": gate.approver,
                    "timeout_seconds": gate.timeout_seconds,
                }
                for gate in plan.approval_gates
            ],
            "optimization_suggestions": plan.optimization_suggestions,
        }

    except WorkflowNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(execution_id: str) -> ExecutionStatusResponse:
    """Get status of a workflow execution.

    Polls the orchestration engine for current execution state.

    Args:
        execution_id: Execution identifier

    Returns:
        Current execution status

    Raises:
        HTTPException: 404 if execution not found

    Example:
        ```
        GET /api/workflows/executions/exec_01234567
        ```
    """
    try:
        status = await _engine.get_execution_status(execution_id)

        return ExecutionStatusResponse(
            execution_id=status.execution_id,
            workflow_id=status.workflow_id,
            status=status.status,
            progress=status.progress,
            current_step=status.current_step,
            completed_steps=status.completed_steps,
            failed_steps=status.failed_steps,
            started_at=status.started_at.isoformat() if status.started_at else None,
            completed_at=(
                status.completed_at.isoformat() if status.completed_at else None
            ),
            error=status.error,
            result=status.result,
        )

    except WorkflowNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except OrchestrationError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/executions/{execution_id}/cancel", response_model=ExecutionCancelResponse
)
async def cancel_execution(execution_id: str) -> ExecutionCancelResponse:
    """Cancel a running workflow execution.

    Attempts graceful cancellation. Already completed steps are not rolled back.

    Args:
        execution_id: Execution identifier

    Returns:
        Cancellation confirmation

    Raises:
        HTTPException: 404 if execution not found, 400 if not cancellable

    Example:
        ```
        POST /api/workflows/executions/exec_01234567/cancel
        ```
    """
    try:
        success = await _engine.cancel_execution(execution_id)

        # Get status to include workflow_id
        status = await _engine.get_execution_status(execution_id)

        return ExecutionCancelResponse(
            execution_id=execution_id,
            workflow_id=status.workflow_id,
            success=success,
            message=(
                "Execution cancelled successfully"
                if success
                else "Execution already completed or failed"
            ),
        )

    except WorkflowNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except OrchestrationError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{workflow_id}/executions",
    response_model=ExecutionListResponse,
    operation_id="listWorkflowExecutions",
    summary="List workflow executions",
)
async def list_workflow_executions(
    workflow_id: str,
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> ExecutionListResponse:
    """List all executions for a workflow.

    Args:
        workflow_id: Workflow identifier
        status: Filter by status (optional)
        limit: Maximum results to return
        offset: Offset for pagination

    Returns:
        List of executions

    Raises:
        HTTPException: 404 if workflow not found

    Example:
        ```
        GET /api/workflows/wf_01234567/executions?status=running&limit=10
        ```
    """
    try:
        # Validate workflow exists
        workflow = _repository.get(workflow_id)
        if workflow is None:
            raise HTTPException(
                status_code=404, detail=f"Workflow '{workflow_id}' not found"
            )

        # Get executions from engine
        executions = await _engine.list_executions(
            workflow_id=workflow_id, status_filter=status
        )

        total = len(executions)

        # Apply pagination
        executions = executions[offset : offset + limit]

        return ExecutionListResponse(
            executions=[
                ExecutionStatusResponse(
                    execution_id=ex.execution_id,
                    workflow_id=ex.workflow_id,
                    status=ex.status,
                    progress=ex.progress,
                    current_step=ex.current_step,
                    completed_steps=ex.completed_steps,
                    failed_steps=ex.failed_steps,
                    started_at=(ex.started_at.isoformat() if ex.started_at else None),
                    completed_at=(
                        ex.completed_at.isoformat() if ex.completed_at else None
                    ),
                    error=ex.error,
                    result=ex.result,
                )
                for ex in executions
            ],
            total=total,
            limit=limit,
            offset=offset,
        )

    except WorkflowNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except OrchestrationError as e:
        raise HTTPException(status_code=500, detail=str(e))
