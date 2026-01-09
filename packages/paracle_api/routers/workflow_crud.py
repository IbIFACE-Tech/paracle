"""Workflow CRUD API router.

Provides REST endpoints for workflow lifecycle management:
- POST /api/workflows - Create new workflow
- GET /api/workflows - List workflows with filters
- GET /api/workflows/{workflow_id} - Get workflow details
- PUT /api/workflows/{workflow_id} - Update workflow
- DELETE /api/workflows/{workflow_id} - Delete workflow
- POST /api/workflows/{workflow_id}/execute - Execute workflow

Note: GET /api/workflows now loads from .parac/workflows/ YAML files
"""

from fastapi import APIRouter, HTTPException, Query
from paracle_domain.models import EntityStatus, Workflow
from paracle_orchestration.workflow_loader import WorkflowLoader, WorkflowLoadError
from paracle_store.workflow_repository import WorkflowRepository

from paracle_api.schemas.workflow_crud import (
    WorkflowCreateRequest,
    WorkflowDeleteResponse,
    WorkflowExecuteRequest,
    WorkflowExecuteResponse,
    WorkflowListResponse,
    WorkflowResponse,
    WorkflowUpdateRequest,
)

# Global repository instance (in-memory for now)
# TODO: Replace with dependency injection in Phase 2
_repository = WorkflowRepository()

# Workflow loader for YAML definitions
_loader = None


def _get_loader() -> WorkflowLoader:
    """Get or initialize workflow loader."""
    global _loader
    if _loader is None:
        try:
            _loader = WorkflowLoader()
        except WorkflowLoadError:
            # If .parac/ not found, loader unavailable
            pass
    return _loader


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


@router.get(
    "",
    response_model=WorkflowListResponse,
    operation_id="listWorkflows",
    summary="List all workflows",
)
async def list_workflows(
    status: str | None = Query(None, description="Filter by status"),
    category: str | None = Query(None, description="Filter by category"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> WorkflowListResponse:
    """List workflows with optional filters.

    Loads workflows from .parac/workflows/ YAML files if available,
    otherwise falls back to in-memory repository.

    Args:
        status: Filter by status (active/inactive) (optional)
        category: Filter by category (optional)
        limit: Maximum results to return
        offset: Offset for pagination

    Returns:
        List of workflows matching filters
    """
    loader = _get_loader()

    # Try loading from YAML files first
    if loader is not None:
        try:
            # List from catalog
            workflows_meta = loader.list_workflows(status=status, category=category)

            # Load specs and convert to response format
            workflow_responses = []
            for meta in workflows_meta:
                try:
                    spec = loader.load_workflow_spec(meta["name"])
                    workflow_responses.append(
                        WorkflowResponse(
                            id=meta["name"],
                            name=meta["name"],
                            description=meta.get("description", ""),
                            status=meta.get("status", "active"),
                            steps_count=len(spec.steps),
                            progress=0,  # Static definitions have no progress
                            created_at=None,
                            updated_at=None,
                        )
                    )
                except Exception:
                    # Skip workflows that fail to load
                    continue

            total = len(workflow_responses)

            # Apply pagination
            workflow_responses = workflow_responses[offset : offset + limit]

            return WorkflowListResponse(
                workflows=workflow_responses,
                total=total,
                limit=limit,
                offset=offset,
            )

        except Exception:
            # Fall through to repository-based listing
            pass

    # Fallback: Use in-memory repository
    workflows = _repository.list()

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
    """Get workflow details by ID or name.

    Tries to load from .parac/workflows/ YAML files first,
    then falls back to in-memory repository.

    Args:
        workflow_id: Workflow identifier or name

    Returns:
        Workflow details

    Raises:
        HTTPException: 404 if workflow not found
    """
    loader = _get_loader()

    # Try loading from YAML files first
    if loader is not None:
        try:
            spec = loader.load_workflow_spec(workflow_id)
            # Get metadata from catalog
            catalog = loader.load_catalog()
            meta = next(
                (
                    w
                    for w in catalog.get("workflows", [])
                    if w.get("name") == workflow_id
                ),
                {},
            )

            return WorkflowResponse(
                id=workflow_id,
                name=spec.name,
                description=spec.description or "",
                status=meta.get("status", "active"),
                steps_count=len(spec.steps),
                progress=0,
                created_at=None,
                updated_at=None,
            )
        except WorkflowLoadError:
            # Fall through to repository
            pass

    # Fallback: Use in-memory repository
    workflow = _repository.get(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow '{workflow_id}' not found",
        )

    return _workflow_to_response(workflow)


@router.put(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    operation_id="updateWorkflow",
    summary="Update workflow",
)
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


@router.delete(
    "/{workflow_id}",
    response_model=WorkflowDeleteResponse,
    operation_id="deleteWorkflow",
    summary="Delete workflow",
)
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

    success = _repository.delete(workflow_id)

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
