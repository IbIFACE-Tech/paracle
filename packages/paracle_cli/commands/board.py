"""CLI commands for board management.

Uses API-first pattern: CLI -> API -> Core
Falls back to direct core access if API is unavailable.
"""

import json

import click
from paracle_kanban import Board
from paracle_kanban.board import BoardRepository
from paracle_kanban.task import TaskStatus
from rich.console import Console
from rich.table import Table
from rich.text import Text

from paracle_cli.api_client import APIError, use_api_or_fallback

console = Console()


# =============================================================================
# API Functions
# =============================================================================


def _api_list_boards(client, archived: bool) -> dict:
    """List boards via API."""
    return client.boards_list(include_archived=archived)


def _api_create_board(client, name: str, description: str) -> dict:
    """Create board via API."""
    return client.boards_create(name=name, description=description)


def _api_get_board(client, board_id: str) -> dict:
    """Get board via API."""
    return client.boards_get(board_id)


def _api_get_board_stats(client, board_id: str) -> dict:
    """Get board stats via API."""
    return client.boards_stats(board_id)


def _api_update_board(client, board_id: str, archived: bool) -> dict:
    """Update board via API."""
    return client.boards_update(board_id, archived=archived)


def _api_delete_board(client, board_id: str) -> dict:
    """Delete board via API."""
    return client.boards_delete(board_id)


def _api_list_tasks(client, board_id: str) -> dict:
    """List tasks for board via API."""
    return client.tasks_list(board_id=board_id)


# =============================================================================
# Fallback Functions (Direct Core Access)
# =============================================================================


def _fallback_list_boards(archived: bool) -> dict:
    """List boards directly from core."""
    repo = BoardRepository()
    boards = repo.list_boards(include_archived=archived)
    return {
        "boards": [
            {
                "id": b.id,
                "name": b.name,
                "description": b.description,
                "columns": [c.value if hasattr(c, 'value') else c for c in b.columns],
                "archived": b.archived,
                "created_at": b.created_at.isoformat(),
                "updated_at": b.updated_at.isoformat(),
            }
            for b in boards
        ],
        "total": len(boards),
    }


def _fallback_create_board(name: str, description: str) -> dict:
    """Create board directly in core."""
    repo = BoardRepository()
    board = Board(name=name, description=description)
    board = repo.create_board(board)
    return {
        "id": board.id,
        "name": board.name,
        "description": board.description,
        "columns": [
            c.value if hasattr(c, "value") else c for c in board.columns
        ],
        "archived": board.archived,
        "created_at": board.created_at.isoformat(),
        "updated_at": board.updated_at.isoformat(),
    }


def _fallback_get_board(board_id: str) -> dict:
    """Get board directly from core."""
    repo = BoardRepository()
    board = repo.get_board(board_id)
    if not board:
        raise ValueError(f"Board '{board_id}' not found")
    return {
        "id": board.id,
        "name": board.name,
        "description": board.description,
        "columns": [
            c.value if hasattr(c, "value") else c for c in board.columns
        ],
        "archived": board.archived,
        "created_at": board.created_at.isoformat(),
        "updated_at": board.updated_at.isoformat(),
    }


def _fallback_get_board_stats(board_id: str) -> dict:
    """Get board stats directly from core."""
    repo = BoardRepository()
    board = repo.get_board(board_id)
    if not board:
        raise ValueError(f"Board '{board_id}' not found")
    return repo.get_board_stats(board_id)


def _fallback_update_board(board_id: str, archived: bool) -> dict:
    """Update board directly in core."""
    repo = BoardRepository()
    board = repo.get_board(board_id)
    if not board:
        raise ValueError(f"Board '{board_id}' not found")
    board.archived = archived
    repo.update_board(board)
    return {"id": board.id, "name": board.name, "archived": board.archived}


def _fallback_delete_board(board_id: str) -> dict:
    """Delete board directly from core."""
    repo = BoardRepository()
    board = repo.get_board(board_id)
    if not board:
        raise ValueError(f"Board '{board_id}' not found")
    repo.delete_board(board_id)
    return {"success": True, "board_id": board_id, "message": f"Deleted {board.name}"}


def _fallback_list_tasks(board_id: str) -> dict:
    """List tasks for board directly from core."""
    repo = BoardRepository()
    board = repo.get_board(board_id)
    if not board:
        raise ValueError(f"Board '{board_id}' not found")
    tasks = repo.list_tasks(board_id=board_id)
    return {
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status.value if hasattr(t.status, "value") else t.status,
                "priority": t.priority.value if hasattr(t.priority, "value") else t.priority,
                "assigned_to": t.assigned_to,
                "blocked_by": t.blocked_by,
            }
            for t in tasks
        ],
        "total": len(tasks),
        "board": {
            "id": board.id,
            "name": board.name,
            "columns": [
                c.value if hasattr(c, "value") else c for c in board.columns
            ],
        },
    }


# =============================================================================
# CLI Commands
# =============================================================================


@click.group()
def board() -> None:
    """Manage Kanban boards."""
    pass


@board.command("create")
@click.argument("name")
@click.option("--description", "-d", default="", help="Board description")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def create_board(name: str, description: str, as_json: bool) -> None:
    """Create a new board."""
    try:
        result = use_api_or_fallback(
            _api_create_board, _fallback_create_board, name, description
        )

        if as_json:
            click.echo(json.dumps(result, indent=2, default=str))
        else:
            console.print(f"[green]OK[/green] Created board: {result['id']}")
            console.print(f"  Name: {result['name']}")
            console.print(f"  Columns: {', '.join(result['columns'])}")

    except (APIError, ValueError) as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@board.command("list")
@click.option("--archived", is_flag=True, help="Include archived boards")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_boards(archived: bool, as_json: bool) -> None:
    """List all boards."""
    try:
        result = use_api_or_fallback(
            _api_list_boards, _fallback_list_boards, archived)

        if as_json:
            click.echo(json.dumps(result, indent=2, default=str))
        else:
            boards = result.get("boards", [])
            if not boards:
                console.print("[yellow]No boards found[/yellow]")
                return

            table = Table(title=f"Boards ({len(boards)} total)")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="white")
            table.add_column("Description", style="dim")
            table.add_column("Columns", style="blue")
            table.add_column("Created", style="green")
            table.add_column("Status", style="yellow")

            for b in boards:
                status = (
                    "[red]Archived[/red]" if b["archived"] else "[green]Active[/green]"
                )
                created = (
                    b["created_at"][:10]
                    if isinstance(b["created_at"], str)
                    else str(b["created_at"])[:10]
                )
                table.add_row(
                    b["id"][:8] + "...",
                    b["name"],
                    (b["description"] or "-")[:30],
                    str(len(b["columns"])),
                    created,
                    status,
                )

            console.print(table)

    except (APIError, ValueError) as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@board.command("get")
@click.argument("board_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def get_board(board_id: str, as_json: bool) -> None:
    """Get board details."""
    try:
        result = use_api_or_fallback(
            _api_get_board, _fallback_get_board, board_id)

        if as_json:
            click.echo(json.dumps(result, indent=2, default=str))
        else:
            console.print(f"\n[bold cyan]Board: {result['name']}[/bold cyan]")
            console.print(f"  ID: {result['id']}")
            console.print(
                f"  Description: {result['description'] or '(none)'}")
            console.print(f"  Columns: {', '.join(result['columns'])}")
            console.print(f"  Created: {result['created_at']}")
            console.print(f"  Updated: {result['updated_at']}")
            console.print(
                f"  Status: {'Archived' if result['archived'] else 'Active'}")

    except (APIError, ValueError) as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@board.command("show")
@click.argument("board_id")
def show_board(board_id: str) -> None:
    """Show board with tasks in columns."""
    try:
        result = use_api_or_fallback(
            _api_list_tasks, _fallback_list_tasks, board_id)

        board_info = result.get("board", {})
        tasks = result.get("tasks", [])
        columns = [
            TaskStatus(c)
            for c in board_info.get(
                "columns", ["TODO", "IN_PROGRESS", "REVIEW", "DONE"]
            )
        ]

        # Group tasks by status
        tasks_by_status = {status: [] for status in columns}
        for task in tasks:
            task_status = TaskStatus(task["status"])
            if task_status in tasks_by_status:
                tasks_by_status[task_status].append(task)

        # Create table with columns
        table = Table(
            title=f"[bold cyan]{board_info.get('name', 'Board')}[/bold cyan]",
            show_header=True,
            header_style="bold magenta",
        )

        # Add column headers
        for status in columns:
            count = len(tasks_by_status[status])
            table.add_column(f"{status.value} ({count})",
                             style="white", vertical="top")

        # Find max rows needed
        max_rows = max((len(tasks_by_status[status])
                       for status in columns), default=0)

        # Add rows
        for row_idx in range(max_rows):
            row_data = []
            for status in columns:
                column_tasks = tasks_by_status[status]
                if row_idx < len(column_tasks):
                    task = column_tasks[row_idx]

                    # Color by priority
                    priority_color = {
                        "LOW": "dim",
                        "MEDIUM": "white",
                        "HIGH": "yellow",
                        "CRITICAL": "red bold",
                    }.get(task["priority"], "white")

                    # Build task card
                    task_text = Text()
                    task_text.append(f"#{task['id'][:8]}", style="dim")
                    task_text.append("\n")
                    task_text.append(task["title"][:30], style=priority_color)
                    if task.get("assigned_to"):
                        task_text.append(
                            f"\n-> {task['assigned_to'][:10]}", style="green"
                        )
                    if task.get("blocked_by"):
                        task_text.append("\n! BLOCKED", style="red bold")

                    row_data.append(task_text)
                else:
                    row_data.append("")

            table.add_row(*row_data)

        console.print(table)

    except (APIError, ValueError) as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@board.command("stats")
@click.argument("board_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def board_stats(board_id: str, as_json: bool) -> None:
    """Show board statistics."""
    try:
        # Get board info first
        board_result = use_api_or_fallback(
            _api_get_board, _fallback_get_board, board_id
        )

        # Then get stats
        stats = use_api_or_fallback(
            _api_get_board_stats, _fallback_get_board_stats, board_id
        )

        if as_json:
            click.echo(json.dumps(stats, indent=2))
        else:
            console.print(
                f"\n[bold cyan]Statistics: {board_result['name']}[/bold cyan]\n"
            )

            # Total tasks
            console.print(f"  Total tasks: {stats['total_tasks']}")

            # Status counts
            status_counts = stats.get("status_counts", {})
            if status_counts:
                console.print("\n  Status breakdown:")
                for status, count in status_counts.items():
                    console.print(f"    {status}: {count}")

            # Metrics
            if stats.get("avg_cycle_time_hours"):
                console.print(
                    f"\n  Average cycle time: {stats['avg_cycle_time_hours']:.1f} hours"
                )
            if stats.get("avg_lead_time_hours"):
                console.print(
                    f"  Average lead time: {stats['avg_lead_time_hours']:.1f} hours"
                )

    except (APIError, ValueError) as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@board.command("archive")
@click.argument("board_id")
def archive_board(board_id: str) -> None:
    """Archive a board."""
    try:
        result = use_api_or_fallback(
            _api_update_board, _fallback_update_board, board_id, True
        )

        console.print(
            f"[green]OK[/green] Archived board: {result.get('name', board_id)}"
        )

    except (APIError, ValueError) as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@board.command("delete")
@click.argument("board_id")
@click.confirmation_option(
    prompt="Are you sure? This will delete the board and all its tasks!"
)
def delete_board(board_id: str) -> None:
    """Delete a board and all its tasks."""
    try:
        result = use_api_or_fallback(
            _api_delete_board, _fallback_delete_board, board_id
        )

        console.print(
            f"[green]OK[/green] {result.get('message', 'Board deleted')}")

    except (APIError, ValueError) as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)
