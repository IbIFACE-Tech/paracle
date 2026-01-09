"""CLI commands for task management.

Follows API-first pattern: CLI -> API -> Core
Falls back to direct core access when API unavailable.
"""

import json

import click
from paracle_kanban import Task, TaskPriority, TaskStatus, TaskType
from paracle_kanban.board import BoardRepository
from rich.console import Console
from rich.table import Table

from paracle_cli.api_client import APIClient, use_api_or_fallback

console = Console()


# =============================================================================
# API Functions
# =============================================================================


def _api_create_task(
    client: APIClient,
    board_id: str,
    title: str,
    description: str,
    priority: str,
    task_type: str,
    assignee: str | None,
    tags: list[str],
) -> dict:
    """Create task via API."""
    return client.tasks_create(
        board_id=board_id,
        title=title,
        description=description,
        priority=priority,
        task_type=task_type,
        assigned_to=assignee,
        tags=tags,
    )


def _api_list_tasks(
    client: APIClient,
    board_id: str | None,
    status: str | None,
    assignee: str | None,
    priority: str | None,
) -> dict:
    """List tasks via API."""
    return client.tasks_list(
        board_id=board_id,
        status=status,
        assigned_to=assignee,
        priority=priority,
    )


def _api_get_task(client: APIClient, task_id: str) -> dict:
    """Get task via API."""
    return client.tasks_get(task_id)


def _api_move_task(
    client: APIClient, task_id: str, status: str, reason: str | None
) -> dict:
    """Move task via API."""
    return client.tasks_move(task_id, status, reason)


def _api_assign_task(client: APIClient, task_id: str, agent_id: str) -> dict:
    """Assign task via API."""
    return client.tasks_assign(task_id, agent_id)


def _api_unassign_task(client: APIClient, task_id: str) -> dict:
    """Unassign task via API."""
    return client.tasks_unassign(task_id)


def _api_delete_task(client: APIClient, task_id: str) -> dict:
    """Delete task via API."""
    return client.tasks_delete(task_id)


# =============================================================================
# Fallback Functions (direct core access)
# =============================================================================


def _fallback_create_task(
    board_id: str,
    title: str,
    description: str,
    priority: str,
    task_type: str,
    assignee: str | None,
    tags: list[str],
) -> dict:
    """Create task directly from core."""
    repo = BoardRepository()

    # Verify board exists
    board = repo.get_board(board_id)
    if not board:
        raise ValueError(f"Board '{board_id}' not found")

    # Create task
    task = Task(
        board_id=board_id,
        title=title,
        description=description,
        priority=TaskPriority[priority.upper()],
        task_type=TaskType[task_type.upper()],
        assigned_to=assignee,
        tags=tags,
    )

    task = repo.create_task(task)

    return {
        "id": task.id,
        "board_id": task.board_id,
        "title": task.title,
        "description": task.description,
        "status": task.status.value if hasattr(task.status, "value") else task.status,
        "priority": task.priority.value if hasattr(task.priority, "value") else task.priority,
        "task_type": task.task_type.value if hasattr(task.task_type, "value") else task.task_type,
        "assigned_to": task.assigned_to,
        "tags": task.tags,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }


def _fallback_list_tasks(
    board_id: str | None,
    status: str | None,
    assignee: str | None,
    priority: str | None,
) -> dict:
    """List tasks directly from core."""
    repo = BoardRepository()

    # Convert string filters to enums
    status_filter = TaskStatus[status.upper()] if status else None
    priority_filter = TaskPriority[priority.upper()] if priority else None

    tasks = repo.list_tasks(
        board_id=board_id,
        status=status_filter,
        assigned_to=assignee,
        priority=priority_filter,
    )

    return {
        "tasks": [
            {
                "id": t.id,
                "board_id": t.board_id,
                "title": t.title,
                "description": t.description,
                "status": t.status.value if hasattr(t.status, "value") else t.status,
                "priority": t.priority.value if hasattr(t.priority, "value") else t.priority,
                "task_type": t.task_type.value if hasattr(t.task_type, "value") else t.task_type,
                "assigned_to": t.assigned_to,
                "tags": t.tags,
                "created_at": t.created_at.isoformat(),
                "updated_at": t.updated_at.isoformat(),
            }
            for t in tasks
        ],
        "total": len(tasks),
    }


def _fallback_get_task(task_id: str) -> dict:
    """Get task directly from core."""
    repo = BoardRepository()
    task = repo.get_task(task_id)

    if not task:
        raise ValueError(f"Task '{task_id}' not found")

    return {
        "id": task.id,
        "board_id": task.board_id,
        "title": task.title,
        "description": task.description,
        "status": task.status.value if hasattr(task.status, "value") else task.status,
        "priority": task.priority.value if hasattr(task.priority, "value") else task.priority,
        "task_type": task.task_type.value if hasattr(task.task_type, "value") else task.task_type,
        "assigned_to": task.assigned_to,
        "tags": task.tags,
        "depends_on": task.depends_on,
        "blocked_by": task.blocked_by,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "cycle_time_hours": task.cycle_time() if task.completed_at else None,
        "lead_time_hours": task.lead_time() if task.completed_at else None,
    }


def _fallback_move_task(task_id: str, status: str, reason: str | None) -> dict:
    """Move task directly via core."""
    repo = BoardRepository()
    task = repo.get_task(task_id)

    if not task:
        raise ValueError(f"Task '{task_id}' not found")

    new_status = TaskStatus[status.upper()]

    # Validate transition
    if not task.can_transition_to(new_status):
        raise ValueError(
            f"Cannot move from {task.status.value} to {new_status.value}")

    # Check blocked reason
    if new_status == TaskStatus.BLOCKED and not reason:
        raise ValueError("Reason required when moving to BLOCKED status")

    # Move task
    old_status = task.status
    task.move_to(new_status, reason=reason)
    task = repo.update_task(task)

    return {
        "id": task.id,
        "title": task.title,
        "old_status": old_status.value if hasattr(old_status, "value") else old_status,
        "status": task.status.value if hasattr(task.status, "value") else task.status,
    }


def _fallback_assign_task(task_id: str, agent_id: str) -> dict:
    """Assign task directly via core."""
    repo = BoardRepository()
    task = repo.get_task(task_id)

    if not task:
        raise ValueError(f"Task '{task_id}' not found")

    task.assign(agent_id)
    task = repo.update_task(task)

    return {
        "id": task.id,
        "title": task.title,
        "assigned_to": task.assigned_to,
    }


def _fallback_unassign_task(task_id: str) -> dict:
    """Unassign task directly via core."""
    repo = BoardRepository()
    task = repo.get_task(task_id)

    if not task:
        raise ValueError(f"Task '{task_id}' not found")

    task.unassign()
    task = repo.update_task(task)

    return {
        "id": task.id,
        "title": task.title,
        "assigned_to": task.assigned_to,
    }


def _fallback_delete_task(task_id: str) -> dict:
    """Delete task directly via core."""
    repo = BoardRepository()
    task = repo.get_task(task_id)

    if not task:
        raise ValueError(f"Task '{task_id}' not found")

    title = task.title
    repo.delete_task(task_id)

    return {
        "success": True,
        "task_id": task_id,
        "message": f"Task '{title}' deleted successfully",
    }


# =============================================================================
# CLI Commands
# =============================================================================


@click.group()
def task() -> None:
    """Manage Kanban tasks."""
    pass


@task.command("create")
@click.argument("board_id")
@click.argument("title")
@click.option("--description", "-d", default="", help="Task description")
@click.option(
    "--priority",
    "-p",
    type=click.Choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                      case_sensitive=False),
    default="MEDIUM",
    help="Task priority",
)
@click.option(
    "--type",
    "-t",
    "task_type",
    type=click.Choice(
        ["FEATURE", "BUG", "REFACTOR", "DOCS", "TEST", "CHORE"], case_sensitive=False
    ),
    default="FEATURE",
    help="Task type",
)
@click.option("--assignee", "-a", help="Assign to agent ID")
@click.option("--tags", "-g", multiple=True, help="Task tags (can use multiple times)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def create_task(
    board_id: str,
    title: str,
    description: str,
    priority: str,
    task_type: str,
    assignee: str | None,
    tags: tuple[str, ...],
    as_json: bool,
) -> None:
    """Create a new task."""
    try:
        result = use_api_or_fallback(
            _api_create_task,
            _fallback_create_task,
            board_id,
            title,
            description,
            priority,
            task_type,
            assignee,
            list(tags),
        )

        if as_json:
            click.echo(json.dumps(result, indent=2, default=str))
        else:
            console.print(f"[green]✓[/green] Created task: {result['id']}")
            console.print(f"  Title: {result['title']}")
            console.print(f"  Status: {result['status']}")
            console.print(f"  Priority: {result['priority']}")
            if result.get("assigned_to"):
                console.print(f"  Assigned to: {result['assigned_to']}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@task.command("list")
@click.option("--board", "-b", help="Filter by board ID")
@click.option(
    "--status",
    "-s",
    type=click.Choice(
        ["BACKLOG", "TODO", "IN_PROGRESS", "REVIEW", "BLOCKED", "DONE", "ARCHIVED"],
        case_sensitive=False,
    ),
    help="Filter by status",
)
@click.option("--assignee", "-a", help="Filter by assignee")
@click.option(
    "--priority",
    "-p",
    type=click.Choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                      case_sensitive=False),
    help="Filter by priority",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_tasks(
    board: str | None,
    status: str | None,
    assignee: str | None,
    priority: str | None,
    as_json: bool,
) -> None:
    """List tasks with optional filters."""
    try:
        result = use_api_or_fallback(
            _api_list_tasks,
            _fallback_list_tasks,
            board,
            status,
            assignee,
            priority,
        )

        if as_json:
            click.echo(json.dumps(result, indent=2, default=str))
        else:
            tasks = result.get("tasks", [])
            if not tasks:
                console.print("[yellow]No tasks found[/yellow]")
                return

            table = Table(title=f"Tasks ({len(tasks)} total)")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Title", style="white")
            table.add_column("Status", style="blue")
            table.add_column("Priority", style="yellow")
            table.add_column("Type", style="magenta")
            table.add_column("Assignee", style="green")

            for t in tasks:
                # Color status based on value
                status_color = {
                    "BACKLOG": "dim",
                    "TODO": "cyan",
                    "IN_PROGRESS": "yellow",
                    "REVIEW": "blue",
                    "BLOCKED": "red",
                    "DONE": "green",
                    "ARCHIVED": "dim",
                }.get(t["status"], "white")

                # Color priority
                priority_color = {
                    "LOW": "dim",
                    "MEDIUM": "white",
                    "HIGH": "yellow",
                    "CRITICAL": "red bold",
                }.get(t["priority"], "white")

                table.add_row(
                    t["id"][:8] + "...",
                    t["title"][:40],
                    f"[{status_color}]{t['status']}[/{status_color}]",
                    f"[{priority_color}]{t['priority']}[/{priority_color}]",
                    t["task_type"],
                    t.get("assigned_to") or "-",
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@task.command("get")
@click.argument("task_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def get_task(task_id: str, as_json: bool) -> None:
    """Get task details."""
    try:
        result = use_api_or_fallback(
            _api_get_task,
            _fallback_get_task,
            task_id,
        )

        if as_json:
            click.echo(json.dumps(result, indent=2, default=str))
        else:
            console.print(f"\n[bold cyan]Task: {result['title']}[/bold cyan]")
            console.print(f"  ID: {result['id']}")
            console.print(f"  Board: {result['board_id']}")
            console.print(
                f"  Description: {result.get('description') or '(none)'}")
            console.print(f"  Status: [{result['status']}]")
            console.print(f"  Priority: [{result['priority']}]")
            console.print(f"  Type: {result['task_type']}")
            console.print(
                f"  Assigned to: {result.get('assigned_to') or '(unassigned)'}"
            )
            console.print(f"  Created: {result['created_at']}")
            console.print(f"  Updated: {result['updated_at']}")

            if result.get("started_at"):
                console.print(f"  Started: {result['started_at']}")
            if result.get("completed_at"):
                console.print(f"  Completed: {result['completed_at']}")

            if result.get("tags"):
                console.print(f"  Tags: {', '.join(result['tags'])}")
            if result.get("depends_on"):
                console.print(
                    f"  Depends on: {', '.join(result['depends_on'])}")
            if result.get("blocked_by"):
                console.print(f"  Blocked by: {result['blocked_by']}")

            # Show metrics if available
            if result.get("cycle_time_hours"):
                console.print(
                    f"  Cycle time: {result['cycle_time_hours']:.1f} hours")
            if result.get("lead_time_hours"):
                console.print(
                    f"  Lead time: {result['lead_time_hours']:.1f} hours")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@task.command("move")
@click.argument("task_id")
@click.argument(
    "status",
    type=click.Choice(
        ["BACKLOG", "TODO", "IN_PROGRESS", "REVIEW", "BLOCKED", "DONE", "ARCHIVED"],
        case_sensitive=False,
    ),
)
@click.option("--reason", "-r", help="Reason for move (required for BLOCKED)")
def move_task(task_id: str, status: str, reason: str | None) -> None:
    """Move task to a different status."""
    try:
        result = use_api_or_fallback(
            _api_move_task,
            _fallback_move_task,
            task_id,
            status,
            reason,
        )

        old_status = result.get("old_status", "unknown")
        new_status = result.get("status", status)
        console.print(
            f"[green]✓[/green] Moved task from {old_status} to {new_status}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@task.command("assign")
@click.argument("task_id")
@click.argument("agent_id")
def assign_task(task_id: str, agent_id: str) -> None:
    """Assign task to an agent."""
    try:
        use_api_or_fallback(
            _api_assign_task,
            _fallback_assign_task,
            task_id,
            agent_id,
        )

        console.print(f"[green]✓[/green] Assigned task to {agent_id}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@task.command("unassign")
@click.argument("task_id")
def unassign_task(task_id: str) -> None:
    """Unassign task."""
    try:
        use_api_or_fallback(
            _api_unassign_task,
            _fallback_unassign_task,
            task_id,
        )

        console.print("[green]✓[/green] Unassigned task")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@task.command("delete")
@click.argument("task_id")
@click.confirmation_option(prompt="Are you sure you want to delete this task?")
def delete_task(task_id: str) -> None:
    """Delete a task."""
    try:
        result = use_api_or_fallback(
            _api_delete_task,
            _fallback_delete_task,
            task_id,
        )

        console.print(
            f"[green]✓[/green] {result.get('message', 'Task deleted')}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)
