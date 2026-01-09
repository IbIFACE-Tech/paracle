"""Kanban board model and repository.

This module provides the Board model for organizing tasks
and a repository for persistence.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from paracle_domain.models import generate_id
from pydantic import BaseModel, Field

from paracle_kanban.task import Task, TaskPriority, TaskStatus


def _find_parac_root(start_path: Path | None = None) -> Path:
    """Find the .parac/ directory starting from a path and going up.

    Args:
        start_path: Starting directory. Defaults to current working directory.

    Returns:
        Path to .parac/ directory.

    Raises:
        RuntimeError: If .parac/ directory not found.
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()
    while current != current.parent:
        parac_dir = current / ".parac"
        if parac_dir.is_dir():
            return parac_dir
        current = current.parent

    # Check root
    parac_dir = current / ".parac"
    if parac_dir.is_dir():
        return parac_dir

    raise RuntimeError(
        ".parac/ directory not found. " "Run 'paracle init' to initialize a workspace."
    )


class Board(BaseModel):
    """Kanban board model.

    Represents a Kanban board with multiple columns (statuses)
    containing tasks at various stages.

    Attributes:
        id: Unique board identifier
        name: Board name
        description: Board description
        created_at: When board was created
        updated_at: When board was last updated
        columns: Ordered list of columns (statuses) to display
        archived: Whether board is archived
    """

    id: str = Field(default_factory=lambda: generate_id("board"))
    name: str
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    columns: list[TaskStatus] = Field(
        default_factory=lambda: [
            TaskStatus.TODO,
            TaskStatus.IN_PROGRESS,
            TaskStatus.REVIEW,
            TaskStatus.DONE,
        ]
    )
    archived: bool = False

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class BoardRepository:
    """Repository for persisting boards and tasks.

    Uses SQLite for storage in .parac/memory/data/kanban.db
    """

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize the board repository.

        Args:
            db_path: Optional custom database path
        """
        if db_path is None:
            parac_root = _find_parac_root()
            data_dir = parac_root / "memory" / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "kanban.db"

        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS boards (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    columns TEXT NOT NULL,
                    archived INTEGER DEFAULT 0
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    board_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    assigned_to TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    tags TEXT,
                    metadata TEXT,
                    depends_on TEXT,
                    blocked_by TEXT,
                    FOREIGN KEY (board_id) REFERENCES boards (id)
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_tasks_board_id
                ON tasks (board_id)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_tasks_status
                ON tasks (status)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to
                ON tasks (assigned_to)
            """
            )

            conn.commit()

    # Board Operations

    def create_board(self, board: Board) -> Board:
        """Create a new board.

        Args:
            board: Board to create

        Returns:
            Created board
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO boards (id, name, description, created_at, updated_at, columns, archived)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    board.id,
                    board.name,
                    board.description,
                    board.created_at.isoformat(),
                    board.updated_at.isoformat(),
                    json.dumps([c.value for c in board.columns]),
                    1 if board.archived else 0,
                ),
            )
            conn.commit()

        return board

    def get_board(self, board_id: str) -> Board | None:
        """Get board by ID.

        Args:
            board_id: Board ID

        Returns:
            Board if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM boards WHERE id = ?",
                (board_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return Board(
            id=row["id"],
            name=row["name"],
            description=row["description"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            columns=[TaskStatus(c) for c in json.loads(row["columns"])],
            archived=bool(row["archived"]),
        )

    def list_boards(self, include_archived: bool = False) -> list[Board]:
        """List all boards.

        Args:
            include_archived: Whether to include archived boards

        Returns:
            List of boards
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if include_archived:
                cursor = conn.execute("SELECT * FROM boards ORDER BY created_at DESC")
            else:
                cursor = conn.execute(
                    "SELECT * FROM boards WHERE archived = 0 ORDER BY created_at DESC"
                )
            rows = cursor.fetchall()

        return [
            Board(
                id=row["id"],
                name=row["name"],
                description=row["description"] or "",
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                columns=[TaskStatus(c) for c in json.loads(row["columns"])],
                archived=bool(row["archived"]),
            )
            for row in rows
        ]

    def update_board(self, board: Board) -> Board:
        """Update a board.

        Args:
            board: Board to update

        Returns:
            Updated board
        """
        board.updated_at = datetime.utcnow()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE boards
                SET name = ?, description = ?, updated_at = ?, columns = ?, archived = ?
                WHERE id = ?
                """,
                (
                    board.name,
                    board.description,
                    board.updated_at.isoformat(),
                    json.dumps([c.value for c in board.columns]),
                    1 if board.archived else 0,
                    board.id,
                ),
            )
            conn.commit()

        return board

    def delete_board(self, board_id: str) -> None:
        """Delete a board and all its tasks.

        Args:
            board_id: Board ID
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM tasks WHERE board_id = ?", (board_id,))
            conn.execute("DELETE FROM boards WHERE id = ?", (board_id,))
            conn.commit()

    # Task Operations

    def create_task(self, task: Task) -> Task:
        """Create a new task.

        Args:
            task: Task to create

        Returns:
            Created task
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO tasks (
                    id, board_id, title, description, status, priority, task_type,
                    assigned_to, created_at, updated_at, started_at, completed_at,
                    tags, metadata, depends_on, blocked_by
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.id,
                    task.board_id,
                    task.title,
                    task.description,
                    task.status if isinstance(task.status, str) else task.status.value,
                    (
                        task.priority
                        if isinstance(task.priority, str)
                        else task.priority.value
                    ),
                    (
                        task.task_type
                        if isinstance(task.task_type, str)
                        else task.task_type.value
                    ),
                    task.assigned_to,
                    task.created_at.isoformat(),
                    task.updated_at.isoformat(),
                    task.started_at.isoformat() if task.started_at else None,
                    task.completed_at.isoformat() if task.completed_at else None,
                    json.dumps(task.tags),
                    json.dumps(task.metadata),
                    json.dumps(task.depends_on),
                    task.blocked_by,
                ),
            )
            conn.commit()

        return task

    def get_task(self, task_id: str) -> Task | None:
        """Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM tasks WHERE id = ?",
                (task_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_task(row)

    def list_tasks(
        self,
        board_id: str | None = None,
        status: TaskStatus | None = None,
        assigned_to: str | None = None,
        priority: TaskPriority | None = None,
    ) -> list[Task]:
        """List tasks with optional filters.

        Args:
            board_id: Filter by board ID
            status: Filter by status
            assigned_to: Filter by assignee
            priority: Filter by priority

        Returns:
            List of tasks
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            query = "SELECT * FROM tasks WHERE 1=1"
            params: list[Any] = []

            if board_id:
                query += " AND board_id = ?"
                params.append(board_id)

            if status:
                query += " AND status = ?"
                params.append(status.value)

            if assigned_to:
                query += " AND assigned_to = ?"
                params.append(assigned_to)

            if priority:
                query += " AND priority = ?"
                params.append(priority.value)

            query += " ORDER BY created_at DESC"

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        return [self._row_to_task(row) for row in rows]

    def update_task(self, task: Task) -> Task:
        """Update a task.

        Args:
            task: Task to update

        Returns:
            Updated task
        """
        task.updated_at = datetime.utcnow()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE tasks
                SET title = ?, description = ?, status = ?, priority = ?, task_type = ?,
                    assigned_to = ?, updated_at = ?, started_at = ?, completed_at = ?,
                    tags = ?, metadata = ?, depends_on = ?, blocked_by = ?
                WHERE id = ?
                """,
                (
                    task.title,
                    task.description,
                    task.status if isinstance(task.status, str) else task.status.value,
                    (
                        task.priority
                        if isinstance(task.priority, str)
                        else task.priority.value
                    ),
                    (
                        task.task_type
                        if isinstance(task.task_type, str)
                        else task.task_type.value
                    ),
                    task.assigned_to,
                    task.updated_at.isoformat(),
                    task.started_at.isoformat() if task.started_at else None,
                    task.completed_at.isoformat() if task.completed_at else None,
                    json.dumps(task.tags),
                    json.dumps(task.metadata),
                    json.dumps(task.depends_on),
                    task.blocked_by,
                    task.id,
                ),
            )
            conn.commit()

        return task

    def delete_task(self, task_id: str) -> None:
        """Delete a task.

        Args:
            task_id: Task ID
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()

    def get_board_stats(self, board_id: str) -> dict[str, Any]:
        """Get statistics for a board.

        Args:
            board_id: Board ID

        Returns:
            Statistics dictionary
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT
                    status,
                    COUNT(*) as count
                FROM tasks
                WHERE board_id = ?
                GROUP BY status
                """,
                (board_id,),
            )
            status_counts = {row[0]: row[1] for row in cursor.fetchall()}

            cursor = conn.execute(
                """
                SELECT AVG(JULIANDAY(completed_at) - JULIANDAY(started_at)) * 24
                FROM tasks
                WHERE board_id = ? AND started_at IS NOT NULL AND completed_at IS NOT NULL
                """,
                (board_id,),
            )
            avg_cycle_time = cursor.fetchone()[0]

            cursor = conn.execute(
                """
                SELECT AVG(JULIANDAY(completed_at) - JULIANDAY(created_at)) * 24
                FROM tasks
                WHERE board_id = ? AND completed_at IS NOT NULL
                """,
                (board_id,),
            )
            avg_lead_time = cursor.fetchone()[0]

            cursor = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE board_id = ?",
                (board_id,),
            )
            total_tasks = cursor.fetchone()[0]

        return {
            "total_tasks": total_tasks,
            "status_counts": status_counts,
            "avg_cycle_time_hours": avg_cycle_time,
            "avg_lead_time_hours": avg_lead_time,
        }

    def _row_to_task(self, row: sqlite3.Row) -> Task:
        """Convert database row to Task model.

        Args:
            row: Database row

        Returns:
            Task model
        """
        return Task(
            id=row["id"],
            board_id=row["board_id"],
            title=row["title"],
            description=row["description"] or "",
            status=TaskStatus(row["status"]),
            priority=TaskPriority(row["priority"]),
            task_type=row["task_type"],
            assigned_to=row["assigned_to"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            started_at=(
                datetime.fromisoformat(row["started_at"]) if row["started_at"] else None
            ),
            completed_at=(
                datetime.fromisoformat(row["completed_at"])
                if row["completed_at"]
                else None
            ),
            tags=json.loads(row["tags"]) if row["tags"] else [],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            depends_on=json.loads(row["depends_on"]) if row["depends_on"] else [],
            blocked_by=row["blocked_by"],
        )
