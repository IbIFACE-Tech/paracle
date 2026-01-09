"""Kanban API router.

Provides REST endpoints for board and task management:
- POST /api/boards - Create new board
- GET /api/boards - List boards
- GET /api/boards/{board_id} - Get board details
- GET /api/boards/{board_id}/show - Get board with tasks
- GET /api/boards/{board_id}/stats - Get board statistics
- PUT /api/boards/{board_id} - Update board
- DELETE /api/boards/{board_id} - Delete board
- POST /api/tasks - Create new task
- GET /api/tasks - List tasks with filters
- GET /api/tasks/{task_id} - Get task details
- PUT /api/tasks/{task_id} - Update task
- PUT /api/tasks/{task_id}/move - Move task to status
- PUT /api/tasks/{task_id}/assign - Assign task
- PUT /api/tasks/{task_id}/unassign - Unassign task
- DELETE /api/tasks/{task_id} - Delete task
"""

from pathlib import Path
from tempfile import gettempdir

from fastapi import APIRouter, HTTPException, Query
from paracle_kanban import Board, Task, TaskPriority, TaskStatus, TaskType
from paracle_kanban.board import BoardRepository

from paracle_api.schemas.kanban import (
    BoardCreateRequest,
    BoardDeleteResponse,
    BoardListResponse,
    BoardResponse,
    BoardStatsResponse,
    BoardUpdateRequest,
    TaskAssignRequest,
    TaskCreateRequest,
    TaskDeleteResponse,
    TaskListResponse,
    TaskMoveRequest,
    TaskResponse,
    TaskUpdateRequest,
)

router = APIRouter(prefix="/api", tags=["kanban"])


# =============================================================================
# Repository Instance
# =============================================================================


def _get_repository() -> BoardRepository:
    """Get or create repository instance.

    Uses a fallback path if .parac/ not found.
    """
    try:
        return BoardRepository()
    except RuntimeError:
        # Fallback for when .parac/ is not found
        fallback_path = Path(gettempdir()) / "paracle" / "kanban.db"
        fallback_path.parent.mkdir(parents=True, exist_ok=True)
        return BoardRepository(db_path=fallback_path)


# =============================================================================
# Conversion Helpers
# =============================================================================


def _board_to_response(board: Board) -> BoardResponse:
    """Convert Board to BoardResponse."""
    return BoardResponse(
        id=board.id,
        name=board.name,
        description=board.description,
        columns=[c.value if hasattr(c, "value") else str(c) for c in board.columns],
        archived=board.archived,
        created_at=board.created_at,
        updated_at=board.updated_at,
    )


def _task_to_response(task: Task) -> TaskResponse:
    """Convert Task to TaskResponse."""
    return TaskResponse(
        id=task.id,
        board_id=task.board_id,
        title=task.title,
        description=task.description,
        status=task.status.value if hasattr(task.status, "value") else str(task.status),
        priority=(
            task.priority.value
            if hasattr(task.priority, "value")
            else str(task.priority)
        ),
        task_type=(
            task.task_type.value
            if hasattr(task.task_type, "value")
            else str(task.task_type)
        ),
        assigned_to=task.assigned_to,
        created_at=task.created_at,
        updated_at=task.updated_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        tags=task.tags,
        depends_on=task.depends_on,
        blocked_by=task.blocked_by,
        cycle_time_hours=task.cycle_time() if task.completed_at else None,
        lead_time_hours=task.lead_time() if task.completed_at else None,
    )


# =============================================================================
# Board Endpoints
# =============================================================================


@router.post(
    "/boards",
    response_model=BoardResponse,
    status_code=201,
    operation_id="createBoard",
    summary="Create a new board",
)
async def create_board(request: BoardCreateRequest) -> BoardResponse:
    """Create a new Kanban board.

    Args:
        request: Board creation request

    Returns:
        Created board details
    """
    repo = _get_repository()

    # Create board with optional custom columns
    if request.columns:
        columns = [TaskStatus(c) for c in request.columns]
        board = Board(
            name=request.name, description=request.description, columns=columns
        )
    else:
        board = Board(name=request.name, description=request.description)

    board = repo.create_board(board)
    return _board_to_response(board)


@router.get(
    "/boards",
    response_model=BoardListResponse,
    operation_id="listBoards",
    summary="List all boards",
)
async def list_boards(
    include_archived: bool = Query(False, description="Include archived boards"),
) -> BoardListResponse:
    """List all Kanban boards.

    Args:
        include_archived: Whether to include archived boards

    Returns:
        List of boards
    """
    repo = _get_repository()
    boards = repo.list_boards(include_archived=include_archived)

    return BoardListResponse(
        boards=[_board_to_response(b) for b in boards],
        total=len(boards),
    )


@router.get(
    "/boards/{board_id}",
    response_model=BoardResponse,
    operation_id="getBoard",
    summary="Get board details",
)
async def get_board(board_id: str) -> BoardResponse:
    """Get board details by ID.

    Args:
        board_id: Board identifier

    Returns:
        Board details

    Raises:
        HTTPException: 404 if board not found
    """
    repo = _get_repository()
    board = repo.get_board(board_id)

    if not board:
        raise HTTPException(status_code=404, detail=f"Board '{board_id}' not found")

    return _board_to_response(board)


@router.get(
    "/boards/{board_id}/stats",
    response_model=BoardStatsResponse,
    operation_id="getBoardStats",
    summary="Get board statistics",
)
async def get_board_stats(board_id: str) -> BoardStatsResponse:
    """Get statistics for a board.

    Args:
        board_id: Board identifier

    Returns:
        Board statistics

    Raises:
        HTTPException: 404 if board not found
    """
    repo = _get_repository()
    board = repo.get_board(board_id)

    if not board:
        raise HTTPException(status_code=404, detail=f"Board '{board_id}' not found")

    stats = repo.get_board_stats(board_id)

    return BoardStatsResponse(
        total_tasks=stats["total_tasks"],
        status_counts=stats["status_counts"],
        avg_cycle_time_hours=stats["avg_cycle_time_hours"],
        avg_lead_time_hours=stats["avg_lead_time_hours"],
    )


@router.put(
    "/boards/{board_id}",
    response_model=BoardResponse,
    operation_id="updateBoard",
    summary="Update a board",
)
async def update_board(board_id: str, request: BoardUpdateRequest) -> BoardResponse:
    """Update a board.

    Args:
        board_id: Board identifier
        request: Update request

    Returns:
        Updated board details

    Raises:
        HTTPException: 404 if board not found
    """
    repo = _get_repository()
    board = repo.get_board(board_id)

    if not board:
        raise HTTPException(status_code=404, detail=f"Board '{board_id}' not found")

    # Apply updates
    if request.name is not None:
        board.name = request.name
    if request.description is not None:
        board.description = request.description
    if request.columns is not None:
        board.columns = [TaskStatus(c) for c in request.columns]
    if request.archived is not None:
        board.archived = request.archived

    board = repo.update_board(board)
    return _board_to_response(board)


@router.delete(
    "/boards/{board_id}",
    response_model=BoardDeleteResponse,
    operation_id="deleteBoard",
    summary="Delete a board",
)
async def delete_board(board_id: str) -> BoardDeleteResponse:
    """Delete a board and all its tasks.

    Args:
        board_id: Board identifier

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: 404 if board not found
    """
    repo = _get_repository()
    board = repo.get_board(board_id)

    if not board:
        raise HTTPException(status_code=404, detail=f"Board '{board_id}' not found")

    repo.delete_board(board_id)

    return BoardDeleteResponse(
        success=True,
        board_id=board_id,
        message=f"Board '{board.name}' deleted successfully",
    )


# =============================================================================
# Task Endpoints
# =============================================================================


@router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=201,
    operation_id="createTask",
    summary="Create a new task",
)
async def create_task(request: TaskCreateRequest) -> TaskResponse:
    """Create a new task.

    Args:
        request: Task creation request

    Returns:
        Created task details

    Raises:
        HTTPException: 404 if board not found
    """
    repo = _get_repository()

    # Verify board exists
    board = repo.get_board(request.board_id)
    if not board:
        raise HTTPException(
            status_code=404, detail=f"Board '{request.board_id}' not found"
        )

    # Create task
    task = Task(
        board_id=request.board_id,
        title=request.title,
        description=request.description,
        priority=TaskPriority[request.priority.upper()],
        task_type=TaskType[request.task_type.upper()],
        assigned_to=request.assigned_to,
        tags=request.tags,
        depends_on=request.depends_on,
    )

    task = repo.create_task(task)
    return _task_to_response(task)


@router.get(
    "/tasks",
    response_model=TaskListResponse,
    operation_id="listTasks",
    summary="List tasks with filters",
)
async def list_tasks(
    board_id: str | None = Query(None, description="Filter by board ID"),
    status: str | None = Query(None, description="Filter by status"),
    assigned_to: str | None = Query(None, description="Filter by assignee"),
    priority: str | None = Query(None, description="Filter by priority"),
) -> TaskListResponse:
    """List tasks with optional filters.

    Args:
        board_id: Filter by board
        status: Filter by status
        assigned_to: Filter by assignee
        priority: Filter by priority

    Returns:
        List of tasks
    """
    repo = _get_repository()

    # Convert string filters to enums
    status_filter = TaskStatus[status.upper()] if status else None
    priority_filter = TaskPriority[priority.upper()] if priority else None

    tasks = repo.list_tasks(
        board_id=board_id,
        status=status_filter,
        assigned_to=assigned_to,
        priority=priority_filter,
    )

    return TaskListResponse(
        tasks=[_task_to_response(t) for t in tasks],
        total=len(tasks),
    )


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    operation_id="getTask",
    summary="Get task details",
)
async def get_task(task_id: str) -> TaskResponse:
    """Get task details by ID.

    Args:
        task_id: Task identifier

    Returns:
        Task details

    Raises:
        HTTPException: 404 if task not found
    """
    repo = _get_repository()
    task = repo.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    return _task_to_response(task)


@router.put(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    operation_id="updateTask",
    summary="Update a task",
)
async def update_task(task_id: str, request: TaskUpdateRequest) -> TaskResponse:
    """Update a task.

    Args:
        task_id: Task identifier
        request: Update request

    Returns:
        Updated task details

    Raises:
        HTTPException: 404 if task not found
    """
    repo = _get_repository()
    task = repo.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    # Apply updates
    if request.title is not None:
        task.title = request.title
    if request.description is not None:
        task.description = request.description
    if request.priority is not None:
        task.priority = TaskPriority[request.priority.upper()]
    if request.task_type is not None:
        task.task_type = TaskType[request.task_type.upper()]
    if request.tags is not None:
        task.tags = request.tags
    if request.depends_on is not None:
        task.depends_on = request.depends_on

    task = repo.update_task(task)
    return _task_to_response(task)


@router.put(
    "/tasks/{task_id}/move",
    response_model=TaskResponse,
    operation_id="moveTask",
    summary="Move task to a different status",
)
async def move_task(task_id: str, request: TaskMoveRequest) -> TaskResponse:
    """Move task to a different status.

    Args:
        task_id: Task identifier
        request: Move request

    Returns:
        Updated task details

    Raises:
        HTTPException: 404 if task not found, 400 if transition invalid
    """
    repo = _get_repository()
    task = repo.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    new_status = TaskStatus[request.status.upper()]

    # Validate transition
    if not task.can_transition_to(new_status):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot move from {task.status.value} to {new_status.value}",
        )

    # Check blocked reason
    if new_status == TaskStatus.BLOCKED and not request.reason:
        raise HTTPException(
            status_code=400,
            detail="Reason required when moving to BLOCKED status",
        )

    # Move task
    task.move_to(new_status, reason=request.reason)
    task = repo.update_task(task)

    return _task_to_response(task)


@router.put(
    "/tasks/{task_id}/assign",
    response_model=TaskResponse,
    operation_id="assignTask",
    summary="Assign task to an agent",
)
async def assign_task(task_id: str, request: TaskAssignRequest) -> TaskResponse:
    """Assign task to an agent.

    Args:
        task_id: Task identifier
        request: Assignment request

    Returns:
        Updated task details

    Raises:
        HTTPException: 404 if task not found
    """
    repo = _get_repository()
    task = repo.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    task.assign(request.agent_id)
    task = repo.update_task(task)

    return _task_to_response(task)


@router.put(
    "/tasks/{task_id}/unassign",
    response_model=TaskResponse,
    operation_id="unassignTask",
    summary="Unassign task",
)
async def unassign_task(task_id: str) -> TaskResponse:
    """Unassign task.

    Args:
        task_id: Task identifier

    Returns:
        Updated task details

    Raises:
        HTTPException: 404 if task not found
    """
    repo = _get_repository()
    task = repo.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    task.unassign()
    task = repo.update_task(task)

    return _task_to_response(task)


@router.delete(
    "/tasks/{task_id}",
    response_model=TaskDeleteResponse,
    operation_id="deleteTask",
    summary="Delete a task",
)
async def delete_task(task_id: str) -> TaskDeleteResponse:
    """Delete a task.

    Args:
        task_id: Task identifier

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: 404 if task not found
    """
    repo = _get_repository()
    task = repo.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    repo.delete_task(task_id)

    return TaskDeleteResponse(
        success=True,
        task_id=task_id,
        message=f"Task '{task.title}' deleted successfully",
    )
