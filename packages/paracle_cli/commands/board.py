"""CLI commands for board management."""

import json

import click
from paracle_kanban import Board
from paracle_kanban.board import BoardRepository
from rich.console import Console
from rich.table import Table
from rich.text import Text

console = Console()


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
        repo = BoardRepository()

        board = Board(name=name, description=description)
        board = repo.create_board(board)

        if as_json:
            click.echo(board.model_dump_json(indent=2))
        else:
            console.print(f"[green]✓[/green] Created board: {board.id}")
            console.print(f"  Name: {board.name}")
            console.print(
                f"  Columns: {', '.join(c.value for c in board.columns)}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@board.command("list")
@click.option("--archived", is_flag=True, help="Include archived boards")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_boards(archived: bool, as_json: bool) -> None:
    """List all boards."""
    try:
        repo = BoardRepository()
        boards = repo.list_boards(include_archived=archived)

        if as_json:
            click.echo(json.dumps([b.model_dump()
                       for b in boards], indent=2, default=str))
        else:
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
                status = "[red]Archived[/red]" if b.archived else "[green]Active[/green]"
                table.add_row(
                    b.id[:8] + "...",
                    b.name,
                    b.description[:30] if b.description else "-",
                    str(len(b.columns)),
                    b.created_at.strftime("%Y-%m-%d"),
                    status,
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@board.command("get")
@click.argument("board_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def get_board(board_id: str, as_json: bool) -> None:
    """Get board details."""
    try:
        repo = BoardRepository()
        board = repo.get_board(board_id)

        if not board:
            console.print(f"[red]Error: Board '{board_id}' not found[/red]")
            raise SystemExit(1)

        if as_json:
            click.echo(board.model_dump_json(indent=2))
        else:
            console.print(f"\n[bold cyan]Board: {board.name}[/bold cyan]")
            console.print(f"  ID: {board.id}")
            console.print(f"  Description: {board.description or '(none)'}")
            console.print(
                f"  Columns: {', '.join(c.value for c in board.columns)}")
            console.print(f"  Created: {board.created_at.isoformat()}")
            console.print(f"  Updated: {board.updated_at.isoformat()}")
            console.print(
                f"  Status: {'Archived' if board.archived else 'Active'}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@board.command("show")
@click.argument("board_id")
def show_board(board_id: str) -> None:
    """Show board with tasks in columns."""
    try:
        repo = BoardRepository()
        board_obj = repo.get_board(board_id)

        if not board_obj:
            console.print(f"[red]Error: Board '{board_id}' not found[/red]")
            raise SystemExit(1)

        # Get all tasks for this board
        tasks = repo.list_tasks(board_id=board_id)

        # Group tasks by status
        tasks_by_status = {status: [] for status in board_obj.columns}
        for task in tasks:
            if task.status in tasks_by_status:
                tasks_by_status[task.status].append(task)

        # Create table with columns
        table = Table(
            title=f"[bold cyan]{board_obj.name}[/bold cyan]",
            show_header=True,
            header_style="bold magenta",
        )

        # Add column headers
        for status in board_obj.columns:
            count = len(tasks_by_status[status])
            table.add_column(f"{status.value} ({count})",
                             style="white", vertical="top")

        # Find max rows needed
        max_rows = max(len(tasks_by_status[status])
                       for status in board_obj.columns)

        # Add rows
        for row_idx in range(max_rows):
            row_data = []
            for status in board_obj.columns:
                column_tasks = tasks_by_status[status]
                if row_idx < len(column_tasks):
                    task = column_tasks[row_idx]

                    # Color by priority
                    priority_color = {
                        "LOW": "dim",
                        "MEDIUM": "white",
                        "HIGH": "yellow",
                        "CRITICAL": "red bold",
                    }.get(task.priority.value, "white")

                    # Build task card
                    task_text = Text()
                    task_text.append(f"#{task.id[:8]}", style="dim")
                    task_text.append("\n")
                    task_text.append(task.title[:30], style=priority_color)
                    if task.assigned_to:
                        task_text.append(
                            f"\n👤 {task.assigned_to[:10]}", style="green")
                    if task.blocked_by:
                        task_text.append("\n🚫 BLOCKED", style="red bold")

                    row_data.append(task_text)
                else:
                    row_data.append("")

            table.add_row(*row_data)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@board.command("stats")
@click.argument("board_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def board_stats(board_id: str, as_json: bool) -> None:
    """Show board statistics."""
    try:
        repo = BoardRepository()
        board = repo.get_board(board_id)

        if not board:
            console.print(f"[red]Error: Board '{board_id}' not found[/red]")
            raise SystemExit(1)

        stats = repo.get_board_stats(board_id)

        if as_json:
            click.echo(json.dumps(stats, indent=2))
        else:
            console.print(
                f"\n[bold cyan]Statistics: {board.name}[/bold cyan]\n")

            # Total tasks
            console.print(f"  Total tasks: {stats['total_tasks']}")

            # Status counts
            if stats["status_counts"]:
                console.print("\n  Status breakdown:")
                for status, count in stats["status_counts"].items():
                    console.print(f"    {status}: {count}")

            # Metrics
            if stats["avg_cycle_time_hours"]:
                console.print(
                    f"\n  Average cycle time: {stats['avg_cycle_time_hours']:.1f} hours"
                )
            if stats["avg_lead_time_hours"]:
                console.print(
                    f"  Average lead time: {stats['avg_lead_time_hours']:.1f} hours"
                )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@board.command("archive")
@click.argument("board_id")
def archive_board(board_id: str) -> None:
    """Archive a board."""
    try:
        repo = BoardRepository()
        board = repo.get_board(board_id)

        if not board:
            console.print(f"[red]Error: Board '{board_id}' not found[/red]")
            raise SystemExit(1)

        board.archived = True
        repo.update_board(board)

        console.print(f"[green]✓[/green] Archived board: {board.name}")

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
        repo = BoardRepository()
        board = repo.get_board(board_id)

        if not board:
            console.print(f"[red]Error: Board '{board_id}' not found[/red]")
            raise SystemExit(1)

        repo.delete_board(board_id)
        console.print(f"[green]✓[/green] Deleted board: {board.name}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)
