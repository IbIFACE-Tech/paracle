"""CLI commands for task management."""

import json

import click
from paracle_kanban import Task, TaskPriority, TaskStatus, TaskType
from paracle_kanban.board import BoardRepository
from rich.console import Console
from rich.table import Table

console = Console()


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
        repo = BoardRepository()

        # Verify board exists
        board = repo.get_board(board_id)
        if not board:
            console.print(f"[red]Error: Board '{board_id}' not found[/red]")
            raise SystemExit(1)

        # Create task
        task = Task(
            board_id=board_id,
            title=title,
            description=description,
            priority=TaskPriority[priority.upper()],
            task_type=TaskType[task_type.upper()],
            assigned_to=assignee,
            tags=list(tags),
        )

        task = repo.create_task(task)

        if as_json:
            click.echo(task.model_dump_json(indent=2))
        else:
            console.print(f"[green]✓[/green] Created task: {task.id}")
            console.print(f"  Title: {task.title}")
            console.print(f"  Status: {task.status.value}")
            console.print(f"  Priority: {task.priority.value}")
            if task.assigned_to:
                console.print(f"  Assigned to: {task.assigned_to}")

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
        repo = BoardRepository()

        # Convert string filters to enums
        status_filter = TaskStatus[status.upper()] if status else None
        priority_filter = TaskPriority[priority.upper()] if priority else None

        tasks = repo.list_tasks(
            board_id=board,
            status=status_filter,
            assigned_to=assignee,
            priority=priority_filter,
        )

        if as_json:
            click.echo(json.dumps([t.model_dump()
                       for t in tasks], indent=2, default=str))
        else:
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
                    TaskStatus.BACKLOG: "dim",
                    TaskStatus.TODO: "cyan",
                    TaskStatus.IN_PROGRESS: "yellow",
                    TaskStatus.REVIEW: "blue",
                    TaskStatus.BLOCKED: "red",
                    TaskStatus.DONE: "green",
                    TaskStatus.ARCHIVED: "dim",
                }.get(t.status, "white")

                # Color priority
                priority_color = {
                    TaskPriority.LOW: "dim",
                    TaskPriority.MEDIUM: "white",
                    TaskPriority.HIGH: "yellow",
                    TaskPriority.CRITICAL: "red bold",
                }.get(t.priority, "white")

                table.add_row(
                    t.id[:8] + "...",
                    t.title[:40],
                    f"[{status_color}]{t.status.value}[/{status_color}]",
                    f"[{priority_color}]{t.priority.value}[/{priority_color}]",
                    t.task_type.value,
                    t.assigned_to or "-",
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
        repo = BoardRepository()
        task = repo.get_task(task_id)

        if not task:
            console.print(f"[red]Error: Task '{task_id}' not found[/red]")
            raise SystemExit(1)

        if as_json:
            click.echo(task.model_dump_json(indent=2))
        else:
            console.print(f"\n[bold cyan]Task: {task.title}[/bold cyan]")
            console.print(f"  ID: {task.id}")
            console.print(f"  Board: {task.board_id}")
            console.print(f"  Description: {task.description or '(none)'}")
            console.print(f"  Status: [{task.status.value}]")
            console.print(f"  Priority: [{task.priority.value}]")
            console.print(f"  Type: {task.task_type.value}")
            console.print(
                f"  Assigned to: {task.assigned_to or '(unassigned)'}")
            console.print(f"  Created: {task.created_at.isoformat()}")
            console.print(f"  Updated: {task.updated_at.isoformat()}")

            if task.started_at:
                console.print(f"  Started: {task.started_at.isoformat()}")
            if task.completed_at:
                console.print(f"  Completed: {task.completed_at.isoformat()}")

            if task.tags:
                console.print(f"  Tags: {', '.join(task.tags)}")
            if task.depends_on:
                console.print(f"  Depends on: {', '.join(task.depends_on)}")
            if task.blocked_by:
                console.print(f"  Blocked by: {task.blocked_by}")

            # Show metrics if available
            if task.completed_at:
                if task.started_at:
                    cycle_time = task.cycle_time()
                    if cycle_time:
                        console.print(f"  Cycle time: {cycle_time:.1f} hours")
                lead_time = task.lead_time()
                if lead_time:
                    console.print(f"  Lead time: {lead_time:.1f} hours")

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
        repo = BoardRepository()
        task = repo.get_task(task_id)

        if not task:
            console.print(f"[red]Error: Task '{task_id}' not found[/red]")
            raise SystemExit(1)

        new_status = TaskStatus[status.upper()]

        # Validate transition
        if not task.can_transition_to(new_status):
            console.print(
                f"[red]Error: Cannot move from {task.status.value} to {new_status.value}[/red]"
            )
            raise SystemExit(1)

        # Check blocked reason
        if new_status == TaskStatus.BLOCKED and not reason:
            console.print(
                "[red]Error: --reason required when moving to BLOCKED[/red]")
            raise SystemExit(1)

        # Move task
        old_status = task.status
        task.move_to(new_status, reason=reason)
        repo.update_task(task)

        console.print(
            f"[green]✓[/green] Moved task from {old_status.value} to {new_status.value}"
        )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@task.command("assign")
@click.argument("task_id")
@click.argument("agent_id")
def assign_task(task_id: str, agent_id: str) -> None:
    """Assign task to an agent."""
    try:
        repo = BoardRepository()
        task = repo.get_task(task_id)

        if not task:
            console.print(f"[red]Error: Task '{task_id}' not found[/red]")
            raise SystemExit(1)

        task.assign(agent_id)
        repo.update_task(task)

        console.print(f"[green]✓[/green] Assigned task to {agent_id}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@task.command("unassign")
@click.argument("task_id")
def unassign_task(task_id: str) -> None:
    """Unassign task."""
    try:
        repo = BoardRepository()
        task = repo.get_task(task_id)

        if not task:
            console.print(f"[red]Error: Task '{task_id}' not found[/red]")
            raise SystemExit(1)

        task.unassign()
        repo.update_task(task)

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
        repo = BoardRepository()
        task = repo.get_task(task_id)

        if not task:
            console.print(f"[red]Error: Task '{task_id}' not found[/red]")
            raise SystemExit(1)

        repo.delete_task(task_id)
        console.print(f"[green]✓[/green] Deleted task: {task.title}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)
