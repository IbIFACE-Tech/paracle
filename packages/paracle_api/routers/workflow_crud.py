"""Workflow CRUD API router.

Provides REST endpoints for workflow lifecycle management:
- POST /api/workflows - Create new workflow
- GET /api/workflows - List workflows with filters
- GET /api/workflows/{workflow_id} - Get workflow details
- PUT /api/workflows/{workflow_id} - Update workflow
- DELETE /api/workflows/{workflow_id} - Delete workflow
- POST /api/workflows/{workflow_id}/execute - Execute workflow
"""

from fastapi import APIRouter, HTTPException, Query

from paracle_api.schemas.workflow_crud import (
    WorkflowCreateRequest,
    WorkflowDeleteResponse,
    WorkflowExecuteRequest,
    WorkflowExecuteResponse,
    WorkflowListResponse,
    WorkflowResponse,
    WorkflowUpdateRequest,
)
from paracle_domain.models import EntityStatus, Workflow
from paracle_store.workflow_repository import WorkflowRepository

# Global repository instance (in-memory for now)
# TODO: Replace with dependency injection in Phase 2
_repository = WorkflowRepository()

router = APIRouter(prefix="/api/workflows", tags=["workflow_crud"])


# =============================================================================
# Helper Functions
# =============================================================================


def _workflow_to_response(workflow: Workflow) -> WorkflowResponse:
    """Convert Workflow to WorkflowResponse."""
    return WorkflowResponse(
        id=workflow.id,
        name=workflow.spec.name,
        description=workflow.spec.description,
        status=workflow.status.phase,
        steps_count=len(workflow.spec.steps),
        progress=workflow.status.progress,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )


# =============================================================================
# Workflow CRUD Endpoints
# =============================================================================


@router.post("", response_model=WorkflowResponse, status_code=201)
async def create_workflow(
    request: WorkflowCreateRequest,
) -> WorkflowResponse:
    """Create a new workflow.

    Args:
        request: Workflow creation request

    Returns:
        Created workflow details

    Raises:
        HTTPException: 400 if spec invalid
    """
    try:
        workflow = Workflow(spec=request.spec)
        workflow = _repository.add(workflow)

        return _workflow_to_response(workflow)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=WorkflowListResponse)
async def list_workflows(
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> WorkflowListResponse:
    """List workflows with optional filters.

    Args:
        status: Filter by status (optional)
        limit: Maximum results to return
        offset: Offset for pagination

    Returns:
        List of workflows matching filters
    """
    # Start with all workflows
    workflows = _repository.list_all()

    # Apply filters
    if status:
        try:
            status_enum = EntityStatus(status)
            workflows = [w for w in workflows if w.status.phase == status_enum]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}",
            )

    total = len(workflows)

    # Apply pagination
    workflows = workflows[offset : offset + limit]

    return WorkflowListResponse(
        workflows=[_workflow_to_response(w) for w in workflows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str) -> WorkflowResponse:
    """Get workflow details by ID.

    Args:
        workflow_id: Workflow identifier

    Returns:
        Workflow details

    Raises:
        HTTPException: 404 if workflow not found
    """
    workflow = _repository.get(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow '{workflow_id}' not found",
        )

    return _workflow_to_response(workflow)


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str, request: WorkflowUpdateRequest
) -> WorkflowResponse:
    """Update a workflow's configuration.

    Only updates provided fields. Null values are ignored.

    Args:
        workflow_id: Workflow identifier
        request: Update request with new values

    Returns:
        Updated workflow details

    Raises:
        HTTPException: 404 if workflow not found, 400 if workflow is running
    """
    workflow = _repository.get(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow '{workflow_id}' not found",
        )

    # Don't allow updates to running workflows
    if workflow.status.phase == EntityStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="Cannot update a running workflow",
        )

    # Update spec fields
    spec = workflow.spec
    if request.description is not None:
        spec.description = request.description
    if request.steps is not None:
        spec.steps = request.steps
    if request.inputs is not None:
        spec.inputs = request.inputs
    if request.outputs is not None:
        spec.outputs = request.outputs
    if request.config is not None:
        spec.config = request.config

    # Update timestamp
    from paracle_domain.models import utc_now

    workflow.updated_at = utc_now()

    # Save changes
    workflow = _repository.update(workflow)

    return _workflow_to_response(workflow)


@router.delete("/{workflow_id}", response_model=WorkflowDeleteResponse)
async def delete_workflow(workflow_id: str) -> WorkflowDeleteResponse:
    """Delete a workflow.

    Args:
        workflow_id: Workflow identifier

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: 404 if workflow not found, 400 if workflow is running
    """
    workflow = _repository.get(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow '{workflow_id}' not found",
        )

    # Don't allow deletion of running workflows
    if workflow.status.phase == EntityStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a running workflow. Stop it first.",
        )

    success = _repository.remove(workflow_id)

    return WorkflowDeleteResponse(
        success=success,
        workflow_id=workflow_id,
        message=f"Workflow '{workflow_id}' deleted successfully",
    )


@router.post("/{workflow_id}/execute", response_model=WorkflowExecuteResponse)
async def execute_workflow(
    workflow_id: str, request: WorkflowExecuteRequest
) -> WorkflowExecuteResponse:
    """Execute a workflow.

    Note: This is a placeholder for Phase 3 (Orchestration).
    Currently just marks the workflow as RUNNING.

    Args:
        workflow_id: Workflow identifier
        request: Execution request with inputs

    Returns:
        Execution status

    Raises:
        HTTPException: 404 if workflow not found, 400 if already running
    """
    workflow = _repository.get(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow '{workflow_id}' not found",
        )

    # Don't allow execution if already running
    if workflow.status.phase == EntityStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="Workflow is already running",
        )

    # Update status to running
    from paracle_domain.models import utc_now

    workflow.status.phase = EntityStatus.RUNNING
    workflow.status.started_at = utc_now()
    workflow.updated_at = utc_now()

    # Save changes
    workflow = _repository.update(workflow)

    return WorkflowExecuteResponse(
        workflow_id=workflow.id,
        status=workflow.status.phase,
        message="Workflow execution started (orchestration in Phase 3)",
        current_step=workflow.status.current_step,
    )
