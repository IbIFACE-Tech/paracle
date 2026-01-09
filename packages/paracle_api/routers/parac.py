"""Parac governance API router.

Provides REST endpoints for .parac/ workspace governance:
- GET /parac/status - Get current project status
- POST /parac/sync - Synchronize state with project
- GET /parac/validate - Validate workspace consistency
- POST /parac/session/start - Start a work session
- POST /parac/session/end - End session with updates
"""

from fastapi import APIRouter, HTTPException
from paracle_core.parac.state import find_parac_root, load_state, save_state
from paracle_core.parac.sync import ParacSynchronizer
from paracle_core.parac.validator import ParacValidator

from paracle_api.schemas.parac import (
    GitInfo,
    PhaseInfo,
    SessionEndRequest,
    SessionEndResponse,
    SessionStartResponse,
    StateChange,
    StatusResponse,
    SyncChange,
    SyncRequest,
    SyncResponse,
    ValidationIssue,
    ValidationResponse,
)

router = APIRouter(prefix="/parac", tags=["parac"])


def get_parac_root_or_raise() -> tuple:
    """Get .parac/ root or raise HTTP 404.

    Returns:
        Tuple of (parac_root, project_root).

    Raises:
        HTTPException: If .parac/ not found.
    """
    parac_root = find_parac_root()
    if parac_root is None:
        raise HTTPException(
            status_code=404,
            detail="No .parac/ directory found. Initialize with 'paracle init'.",
        )
    return parac_root, parac_root.parent


@router.get("/status", response_model=StatusResponse, operation_id="getParacStatus")
async def get_status() -> StatusResponse:
    """Get current project status from .parac/.

    Returns the current phase, git info, and project state.
    """
    parac_root, project_root = get_parac_root_or_raise()

    synchronizer = ParacSynchronizer(parac_root, project_root)
    summary = synchronizer.get_summary()

    state = load_state(parac_root)
    if state is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to load project state.",
        )

    phase_data = summary.get("phase", {})
    git_data = summary.get("git", {})

    return StatusResponse(
        parac_root=str(parac_root),
        project_root=str(project_root),
        snapshot_date=summary.get("snapshot_date", "unknown"),
        phase=PhaseInfo(
            id=phase_data.get("id", "unknown"),
            name=phase_data.get("name", "unknown"),
            status=phase_data.get("status", "unknown"),
            progress=phase_data.get("progress", "0%"),
        ),
        git=GitInfo(
            branch=git_data.get("branch", "unknown"),
            last_commit=git_data.get("last_commit", "unknown"),
            has_changes=git_data.get("has_changes", False),
        ),
        blockers=summary.get("blockers", 0),
        next_actions=summary.get("next_actions", 0),
    )


@router.post("/sync", response_model=SyncResponse, operation_id="syncParacState")
async def sync_state(request: SyncRequest | None = None) -> SyncResponse:
    """Synchronize .parac/ state with project reality.

    Updates git info, file metrics, and other project state.
    """
    parac_root, project_root = get_parac_root_or_raise()

    if request is None:
        request = SyncRequest()

    synchronizer = ParacSynchronizer(parac_root, project_root)
    result = synchronizer.sync(
        update_git=request.update_git,
        update_metrics=request.update_metrics,
    )

    return SyncResponse(
        success=result.success,
        changes=[SyncChange(description=c) for c in result.changes],
        errors=result.errors,
    )


@router.get(
    "/validate",
    response_model=ValidationResponse,
    operation_id="validateParacWorkspace",
)
async def validate_workspace() -> ValidationResponse:
    """Validate .parac/ workspace consistency.

    Checks YAML syntax, required files, and cross-file consistency.
    """
    parac_root, _ = get_parac_root_or_raise()

    validator = ParacValidator(parac_root)
    result = validator.validate()

    return ValidationResponse(
        valid=result.valid,
        files_checked=result.files_checked,
        errors=len(result.errors),
        warnings=len(result.warnings),
        issues=[
            ValidationIssue(
                level=issue.level.value,
                file=issue.file,
                message=issue.message,
                line=issue.line,
            )
            for issue in result.issues
        ],
    )


@router.post(
    "/session/start",
    response_model=SessionStartResponse,
    operation_id="startParacSession",
)
async def start_session() -> SessionStartResponse:
    """Start a new work session.

    Reads .parac/ context and returns current state for session start.
    """
    parac_root, _ = get_parac_root_or_raise()

    state = load_state(parac_root)
    if state is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to load project state.",
        )

    phase = state.current_phase

    return SessionStartResponse(
        phase=PhaseInfo(
            id=phase.id,
            name=phase.name,
            status=phase.status,
            progress=phase.progress,
        ),
        focus_areas=phase.focus_areas,
        blockers=len(state.blockers),
        message="Source of truth verified. Proceeding.",
    )


@router.post(
    "/session/end",
    response_model=SessionEndResponse,
    operation_id="endParacSession",
)
async def end_session(request: SessionEndRequest) -> SessionEndResponse:
    """End work session with .parac/ updates.

    Applies progress updates, marks items completed/in-progress.
    """
    parac_root, _ = get_parac_root_or_raise()

    state = load_state(parac_root)
    if state is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to load project state.",
        )

    changes: list[StateChange] = []

    # Apply progress update
    if request.progress is not None:
        old_progress = state.current_phase.progress
        state.update_progress(request.progress)
        changes.append(
            StateChange(
                field="progress",
                change=f"{old_progress} → {state.current_phase.progress}",
            )
        )

    # Mark items completed
    for item in request.completed:
        state.add_completed(item)
        changes.append(StateChange(field="completed", change=f"+ {item}"))

    # Mark items in-progress
    for item in request.in_progress:
        state.add_in_progress(item)
        changes.append(StateChange(field="in_progress", change=f"+ {item}"))

    # Apply or dry-run
    if request.dry_run:
        return SessionEndResponse(
            applied=False,
            changes=changes,
            message="Dry run - no changes applied.",
        )

    if changes:
        if save_state(state, parac_root):
            return SessionEndResponse(
                applied=True,
                changes=changes,
                message="Changes applied successfully.",
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to save state changes.",
            )

    return SessionEndResponse(
        applied=False,
        changes=[],
        message="No changes specified.",
    )
