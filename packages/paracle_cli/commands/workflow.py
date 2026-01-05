"""Paracle CLI - Workflow Commands.

Commands for managing and executing workflows.
Phase 4 - Priority 1 CLI Commands.

Architecture: API-first with local fallback
- Try API endpoints first (via api_client)
- Fallback to local execution if API unavailable
"""

import json
import time
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from paracle_cli.api_client import APIError, get_client

# Local fallback imports
try:
    from paracle_orchestration.engine import WorkflowEngine
    from paracle_store.workflow_repository import WorkflowRepository

    LOCAL_EXECUTION_AVAILABLE = True
except ImportError:
    LOCAL_EXECUTION_AVAILABLE = False

console = Console()


def _is_api_available() -> bool:
    """Check if API server is available.

    Returns:
        True if API is reachable, False otherwise
    """
    try:
        client = get_client()
        # Quick health check
        response = client.get("/health", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


def _use_local_fallback() -> bool:
    """Determine if we should use local fallback.

    Returns:
        True if API unavailable and local execution possible
    """
    if not _is_api_available():
        if LOCAL_EXECUTION_AVAILABLE:
            console.print(
                "[yellow]⚠️  API server unavailable, using local execution[/yellow]"
            )
            return True
        else:
            console.print(
                "[red]✗ API server unavailable and local fallback not available[/red]"
            )
            console.print(
                "[dim]Start API: paracle serve or install full packages[/dim]"
            )
            raise click.Abort()
    return False


@click.group()
def workflow() -> None:
    """Manage workflows and workflow executions.

    Examples:
        # List all workflows
        $ paracle workflow list

        # Execute a workflow
        $ paracle workflow run my-workflow --input key=value

        # Check execution status
        $ paracle workflow status exec_abc123

        # Cancel running execution
        $ paracle workflow cancel exec_abc123
    """
    pass


@workflow.command("list")
@click.option(
    "--status",
    type=click.Choice(["active", "completed", "failed"]),
    help="Filter by workflow status",
)
@click.option(
    "--limit", default=100, type=int, help="Maximum number of workflows to show"
)
@click.option("--offset", default=0, type=int, help="Pagination offset")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def list_workflows(
    status: str | None, limit: int, offset: int, output_json: bool
) -> None:
    """List all workflows.

    Shows workflow ID, name, description, and status.

    Examples:
        $ paracle workflow list
        $ paracle workflow list --status active
        $ paracle workflow list --json
    """
    # API-first: Try API, fallback to local if unavailable
    use_local = _use_local_fallback()

    if use_local:
        _list_workflows_local(status, limit, offset, output_json)
        return

    # API execution (preferred)
    client = get_client()

    try:
        result = client.workflow_list(
            limit=limit, offset=offset, status=status)

        if output_json:
            console.print_json(json.dumps(result))
            return

        workflows = result.get("workflows", [])
        total = result.get("total", 0)

        if not workflows:
            console.print("[dim]No workflows found.[/dim]")
            return

        # Create table
        table = Table(title="Workflows", show_header=True,
                      header_style="bold cyan")
        table.add_column("ID", style="dim", width=20)
        table.add_column("Name", style="cyan")
        table.add_column("Description")
        table.add_column("Steps", justify="right")
        table.add_column("Status", justify="center")

        for wf in workflows:
            workflow_id = wf.get("id", "")
            name = wf.get("spec", {}).get("name", "Unnamed")
            desc = wf.get("spec", {}).get("description", "")
            steps = len(wf.get("spec", {}).get("steps", []))
            wf_status = wf.get("status", "unknown")

            # Color status
            status_display = wf_status
            if wf_status == "active":
                status_display = f"[green]{wf_status}[/green]"
            elif wf_status == "completed":
                status_display = f"[blue]{wf_status}[/blue]"
            elif wf_status == "failed":
                status_display = f"[red]{wf_status}[/red]"

            table.add_row(
                workflow_id,
                name,
                desc[:50] + "..." if len(desc) > 50 else desc,
                str(steps),
                status_display,
            )

        console.print(table)
        console.print(
            f"\n[dim]Showing {len(workflows)} of {total} workflows[/dim]"
        )

    except APIError as e:
        console.print(f"[red]✗ API Error:[/red] {e.detail}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise click.Abort()


@workflow.command("run")
@click.argument("workflow_id")
@click.option(
    "--input",
    "-i",
    multiple=True,
    help="Input key=value pairs (can be repeated)",
)
@click.option(
    "--sync",
    is_flag=True,
    help="Run synchronously (wait for completion)",
)
@click.option(
    "--watch",
    "-w",
    is_flag=True,
    help="Watch execution progress (implies --sync)",
)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def run_workflow(
    workflow_id: str,
    input: tuple[str, ...],
    sync: bool,
    watch: bool,
    output_json: bool,
) -> None:
    """Execute a workflow.

    Args:
        workflow_id: Workflow ID or name to execute

    Examples:
        # Simple execution
        $ paracle workflow run my-workflow

        # With inputs
        $ paracle workflow run my-workflow -i source=data.csv -i target=output.json

        # Synchronous execution
        $ paracle workflow run my-workflow --sync

        # Watch execution progress
        $ paracle workflow run my-workflow --watch
    """
    # Parse inputs
    inputs = {}
    for input_pair in input:
        if "=" not in input_pair:
            console.print(f"[red]✗ Invalid input format:[/red] {input_pair}")
            console.print(
                "[dim]Use key=value format, e.g., -i source=data.csv[/dim]"
            )
            raise click.Abort()
        key, value = input_pair.split("=", 1)
        inputs[key.strip()] = value.strip()

    # API-first: Try API, fallback to local if unavailable
    use_local = _use_local_fallback()

    if use_local:
        # Local execution fallback
        _run_workflow_local(workflow_id, inputs, sync or watch, output_json)
        return

    # API execution (preferred)
    client = get_client()

    try:
        # Execute workflow
        async_execution = not sync and not watch

        result = client.workflow_execute(
            workflow_id=workflow_id,
            inputs=inputs,
            async_execution=async_execution,
        )

        execution_id = result.get("execution_id")
        status = result.get("status")
        message = result.get("message", "")

        if output_json:
            console.print_json(json.dumps(result))
            return

        # Display execution info
        console.print("[green]✓ Workflow execution started[/green]")
        console.print(f"[cyan]Execution ID:[/cyan] {execution_id}")
        console.print(f"[dim]Status:[/dim] {status}")
        console.print(f"[dim]{message}[/dim]")

        # Watch execution if requested
        if watch:
            console.print("\n[dim]Watching execution...[/dim]\n")
            _watch_execution(client, execution_id)

    except APIError as e:
        console.print(f"[red]✗ API Error:[/red] {e.detail}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise click.Abort()


@workflow.command("status")
@click.argument("execution_id")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option(
    "--watch",
    "-w",
    is_flag=True,
    help="Watch execution until completion",
)
def status_execution(
    execution_id: str, output_json: bool, watch: bool
) -> None:
    """Check workflow execution status.

    Args:
        execution_id: Execution ID from 'workflow run'

    Examples:
        $ paracle workflow status exec_abc123
        $ paracle workflow status exec_abc123 --watch
        $ paracle workflow status exec_abc123 --json
    """
    client = get_client()

    if watch:
        _watch_execution(client, execution_id)
        return

    try:
        result = client.workflow_execution_status(execution_id)

        if output_json:
            console.print_json(json.dumps(result))
            return

        # Display status
        status = result.get("status")
        progress = result.get("progress", 0)
        current_step = result.get("current_step")
        completed = result.get("completed_steps", [])
        failed = result.get("failed_steps", [])
        error = result.get("error")

        # Color status
        status_display = status
        if status == "running":
            status_display = f"[yellow]{status}[/yellow]"
        elif status == "completed":
            status_display = f"[green]{status}[/green]"
        elif status == "failed":
            status_display = f"[red]{status}[/red]"

        console.print(f"[cyan]Execution:[/cyan] {execution_id}")
        console.print(f"[cyan]Status:[/cyan] {status_display}")
        console.print(f"[cyan]Progress:[/cyan] {progress * 100:.1f}%")

        if current_step:
            console.print(f"[cyan]Current Step:[/cyan] {current_step}")

        if completed:
            console.print(
                f"[green]Completed Steps:[/green] {', '.join(completed)}"
            )

        if failed:
            console.print(f"[red]Failed Steps:[/red] {', '.join(failed)}")

        if error:
            console.print(f"\n[red]Error:[/red] {error}")

    except APIError as e:
        console.print(f"[red]✗ API Error:[/red] {e.detail}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise click.Abort()


@workflow.command("cancel")
@click.argument("execution_id")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def cancel_execution(execution_id: str, output_json: bool) -> None:
    """Cancel a running workflow execution.

    Args:
        execution_id: Execution ID to cancel

    Examples:
        $ paracle workflow cancel exec_abc123
    """
    client = get_client()

    try:
        result = client.workflow_execution_cancel(execution_id)

        if output_json:
            console.print_json(json.dumps(result))
            return

        success = result.get("success")
        message = result.get("message", "")

        if success:
            console.print("[green]✓ Execution cancelled successfully[/green]")
        else:
            console.print("[yellow]! Execution already completed[/yellow]")

        console.print(f"[dim]{message}[/dim]")

    except APIError as e:
        console.print(f"[red]✗ API Error:[/red] {e.detail}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise click.Abort()


def _watch_execution(client: Any, execution_id: str) -> None:
    """Watch execution progress until completion.

    Args:
        client: API client
        execution_id: Execution ID to watch
    """
    last_status = None
    last_progress = None

    while True:
        try:
            result = client.workflow_execution_status(execution_id)
            status = result.get("status")
            progress = result.get("progress", 0)
            current_step = result.get("current_step")

            # Print updates only if changed
            if status != last_status or progress != last_progress:
                progress_bar = _create_progress_bar(progress)
                console.print(
                    f"[{_get_status_color(status)}]{status:12}[/{_get_status_color(status)}] "
                    f"{progress_bar} {progress * 100:5.1f}% "
                    f"[dim]({current_step or 'waiting'})[/dim]"
                )
                last_status = status
                last_progress = progress

            # Check if terminal
            if status in ("completed", "failed", "cancelled"):
                if status == "completed":
                    console.print(
                        "\n[green]✓ Workflow completed successfully[/green]")
                elif status == "failed":
                    error = result.get("error", "Unknown error")
                    console.print(f"\n[red]✗ Workflow failed:[/red] {error}")
                else:
                    console.print("\n[yellow]! Workflow cancelled[/yellow]")
                break

            time.sleep(2)  # Poll every 2 seconds

        except KeyboardInterrupt:
            console.print(
                "\n[yellow]Stopped watching (execution continues)[/yellow]")
            break
        except APIError as e:
            console.print(f"\n[red]✗ API Error:[/red] {e.detail}")
            raise click.Abort()
        except Exception as e:
            console.print(f"\n[red]✗ Error:[/red] {e}")
            raise click.Abort()


def _create_progress_bar(progress: float, width: int = 20) -> str:
    """Create a text progress bar.

    Args:
        progress: Progress from 0.0 to 1.0
        width: Width of progress bar

    Returns:
        Progress bar string
    """
    filled = int(progress * width)
    empty = width - filled
    return f"[{'█' * filled}{'░' * empty}]"


def _get_status_color(status: str) -> str:
    """Get Rich color for status.

    Args:
        status: Execution status

    Returns:
        Rich color name
    """
    colors = {
        "pending": "yellow",
        "running": "cyan",
        "completed": "green",
        "failed": "red",
        "cancelled": "yellow",
    }
    return colors.get(status, "white")


def _run_workflow_local(
    workflow_id: str,
    inputs: dict[str, Any],
    sync: bool,
    output_json: bool,
) -> None:
    """Execute workflow locally (fallback when API unavailable).

    Args:
        workflow_id: Workflow ID to execute
        inputs: Workflow inputs
        sync: Whether to run synchronously
        output_json: Whether to output JSON
    """
    import asyncio

    try:
        # Load workflow from repository
        repo = WorkflowRepository()
        workflow = repo.get(workflow_id)

        if not workflow:
            console.print(f"[red]✗ Workflow not found:[/red] {workflow_id}")
            console.print(
                "[dim]Available workflows: paracle workflow list[/dim]"
            )
            raise click.Abort()

        # Execute with local engine
        engine = WorkflowEngine()

        if output_json:
            # Simple JSON output for local execution
            result = {
                "execution_id": f"local_{workflow_id}_{int(time.time())}",
                "status": "running" if not sync else "pending",
                "message": "Executing locally (API unavailable)",
                "mode": "sync" if sync else "async",
            }
            console.print_json(json.dumps(result))

        if sync:
            console.print("[cyan]Executing workflow locally...[/cyan]")
            result = asyncio.run(engine.execute(workflow, inputs))

            if result.get("status") == "completed":
                console.print("[green]✓ Workflow completed[/green]")
                if result.get("outputs"):
                    console.print(
                        f"[dim]Outputs:[/dim] {json.dumps(result['outputs'], indent=2)}"
                    )
            else:
                console.print(
                    f"[red]✗ Workflow failed:[/red] {result.get('error')}"
                )
        else:
            console.print(
                "[yellow]⚠️  Async local execution not fully supported[/yellow]"
            )
            console.print(
                "[dim]Use --sync for complete local execution[/dim]"
            )

    except Exception as e:
        console.print(f"[red]✗ Local execution error:[/red] {e}")
        raise click.Abort()


def _list_workflows_local(
    status_filter: str | None,
    limit: int,
    offset: int,
    output_json: bool,
) -> None:
    """List workflows locally (fallback when API unavailable).

    Args:
        status_filter: Optional status filter
        limit: Max workflows to return
        offset: Pagination offset
        output_json: Whether to output JSON
    """
    try:
        repo = WorkflowRepository()
        workflows = repo.list_all()

        # Apply filters
        if status_filter:
            workflows = [
                wf for wf in workflows if wf.get("status") == status_filter
            ]

        # Pagination
        total = len(workflows)
        workflows = workflows[offset: offset + limit]

        if output_json:
            console.print_json(
                json.dumps({"workflows": workflows, "total": total})
            )
            return

        if not workflows:
            console.print("[dim]No workflows found.[/dim]")
            console.print(
                "[dim]Create workflows with workflow YAML files[/dim]"
            )
            return

        # Create table
        table = Table(
            title="Workflows (Local)",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("ID", style="dim", width=20)
        table.add_column("Name", style="cyan")
        table.add_column("Description")
        table.add_column("Steps", justify="right")

        for wf in workflows:
            workflow_id = wf.get("id", "")
            name = wf.get("spec", {}).get("name", "Unnamed")
            desc = wf.get("spec", {}).get("description", "")
            steps = len(wf.get("spec", {}).get("steps", []))

            table.add_row(
                workflow_id,
                name,
                desc[:50] + "..." if len(desc) > 50 else desc,
                str(steps),
            )

        console.print(table)
        console.print(
            f"\n[dim]Showing {len(workflows)} of {total} workflows[/dim]"
        )

    except Exception as e:
        console.print(f"[red]✗ Local listing error:[/red] {e}")
        raise click.Abort()
