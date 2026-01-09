"""CLI commands for run management."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import click
from paracle_runs import RunStatus, get_run_storage
from paracle_runs.models import RunQuery
from rich import print as rprint
from rich.console import Console
from rich.table import Table

console = Console()


@click.group(name="runs")
def runs_group():
    """Manage execution runs (agents and workflows)."""
    pass


@runs_group.command(name="list")
@click.option(
    "--type",
    "run_type",
    type=click.Choice(["agent", "workflow", "all"]),
    default="all",
    help="Type of runs to list",
)
@click.option("--agent-id", help="Filter by agent ID")
@click.option("--workflow-id", help="Filter by workflow ID")
@click.option(
    "--status",
    type=click.Choice([s.value for s in RunStatus]),
    help="Filter by status",
)
@click.option("--since", help="Filter runs since date (YYYY-MM-DD)")
@click.option("--limit", default=20, help="Maximum number of runs to list")
def list_runs(run_type, agent_id, workflow_id, status, since, limit):
    """List execution runs."""
    storage = get_run_storage()

    # Parse since date
    since_dt = None
    if since:
        try:
            since_dt = datetime.strptime(since, "%Y-%m-%d")
        except ValueError:
            rprint("[red]Invalid date format. Use YYYY-MM-DD[/red]")
            return

    # Create query
    query = RunQuery(
        agent_id=agent_id,
        workflow_id=workflow_id,
        status=RunStatus(status) if status else None,
        since=since_dt,
        limit=limit,
    )

    # List runs
    agent_runs = []
    workflow_runs = []

    if run_type in ["agent", "all"]:
        agent_runs = storage.list_agent_runs(query)

    if run_type in ["workflow", "all"]:
        workflow_runs = storage.list_workflow_runs(query)

    # Display agent runs
    if agent_runs:
        rprint("\n[bold cyan]Agent Runs[/bold cyan]")
        table = Table(show_header=True)
        table.add_column("Run ID", style="cyan")
        table.add_column("Agent", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Started", style="blue")
        table.add_column("Duration", style="magenta")

        for run in agent_runs:
            duration = f"{run.duration_seconds:.1f}s" if run.duration_seconds else "N/A"
            table.add_row(
                run.run_id[:16] + "...",
                run.agent_name,
                run.status.value,
                run.started_at.strftime("%Y-%m-%d %H:%M"),
                duration,
            )

        console.print(table)

    # Display workflow runs
    if workflow_runs:
        rprint("\n[bold cyan]Workflow Runs[/bold cyan]")
        table = Table(show_header=True)
        table.add_column("Run ID", style="cyan")
        table.add_column("Workflow", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Started", style="blue")
        table.add_column("Steps", style="white")
        table.add_column("Duration", style="magenta")

        for run in workflow_runs:
            duration = f"{run.duration_seconds:.1f}s" if run.duration_seconds else "N/A"
            steps_str = f"{run.steps_completed}/{run.steps_total}"
            if run.steps_failed > 0:
                steps_str += f" ({run.steps_failed} failed)"

            table.add_row(
                run.run_id[:16] + "...",
                run.workflow_name,
                run.status.value,
                run.started_at.strftime("%Y-%m-%d %H:%M"),
                steps_str,
                duration,
            )

        console.print(table)

    if not agent_runs and not workflow_runs:
        rprint("[yellow]No runs found[/yellow]")


@runs_group.command(name="get")
@click.argument("run_id")
@click.option(
    "--type",
    "run_type",
    type=click.Choice(["agent", "workflow"]),
    required=True,
    help="Type of run",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def get_run(run_id, run_type, as_json):
    """Get details of a specific run."""
    storage = get_run_storage()

    try:
        if run_type == "agent":
            metadata, run_data = storage.load_agent_run(run_id)
        else:
            metadata, run_data = storage.load_workflow_run(run_id)

        if as_json:
            output = {
                "metadata": metadata.model_dump(mode="json"),
                "data": run_data,
            }
            click.echo(json.dumps(output, indent=2, default=str))
        else:
            rprint(f"\n[bold cyan]Run: {run_id}[/bold cyan]")
            rprint(f"Status: [{metadata.status.value}]{metadata.status.value}[/]")
            rprint(f"Started: {metadata.started_at}")
            if metadata.completed_at:
                rprint(f"Completed: {metadata.completed_at}")
            if metadata.duration_seconds:
                rprint(f"Duration: {metadata.duration_seconds:.2f}s")

            if run_type == "agent":
                rprint(f"\nAgent: {metadata.agent_name}")
                if metadata.tokens_used:
                    rprint(f"Tokens: {metadata.tokens_used}")
                if metadata.cost_usd:
                    rprint(f"Cost: ${metadata.cost_usd:.4f}")
            else:
                rprint(f"\nWorkflow: {metadata.workflow_name}")
                rprint(f"Steps: {metadata.steps_completed}/{metadata.steps_total}")
                if metadata.steps_failed > 0:
                    rprint(
                        f"Failed steps: {metadata.steps_failed}",
                        style="red",
                    )
                if metadata.agents_used:
                    rprint(f"Agents: {', '.join(metadata.agents_used)}")

            if run_data.get("artifacts"):
                rprint(f"\nArtifacts: {len(run_data['artifacts'])} files")

    except FileNotFoundError:
        rprint(f"[red]Run not found: {run_id}[/red]")
    except Exception as e:
        rprint(f"[red]Error loading run: {e}[/red]")


@runs_group.command(name="artifacts")
@click.argument("run_id")
@click.option(
    "--type",
    "run_type",
    type=click.Choice(["agent", "workflow"]),
    required=True,
    help="Type of run",
)
@click.option("--output", type=click.Path(), help="Extract artifacts to directory")
def get_artifacts(run_id, run_type, output):
    """Get artifacts from a run."""
    storage = get_run_storage()

    try:
        if run_type == "agent":
            _, run_data = storage.load_agent_run(run_id)
        else:
            _, run_data = storage.load_workflow_run(run_id)

        artifacts = run_data.get("artifacts", {})

        if not artifacts:
            rprint("[yellow]No artifacts found[/yellow]")
            return

        if output:
            output_path = Path(output)
            output_path.mkdir(parents=True, exist_ok=True)

            for name, content in artifacts.items():
                file_path = output_path / name
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(str(content))

            rprint(f"[green]Artifacts extracted to {output_path}[/green]")
        else:
            rprint(f"\n[bold cyan]Artifacts ({len(artifacts)} files)[/bold cyan]")
            for name in artifacts:
                rprint(f"  • {name}")

    except FileNotFoundError:
        rprint(f"[red]Run not found: {run_id}[/red]")
    except Exception as e:
        rprint(f"[red]Error loading artifacts: {e}[/red]")


@runs_group.command(name="replay")
@click.argument("run_id")
@click.option(
    "--type",
    "run_type",
    type=click.Choice(["agent", "workflow"]),
    required=True,
    help="Type of run",
)
def replay_run(run_id, run_type):
    """Replay a run with the same inputs."""
    from paracle_runs import replay_agent_run, replay_workflow_run

    try:
        if run_type == "agent":
            result = replay_agent_run(run_id)
        else:
            result = replay_workflow_run(run_id)

        rprint(f"\n[bold green]Replay started for run: {run_id}[/bold green]")
        rprint(json.dumps(result, indent=2, default=str))

    except FileNotFoundError:
        rprint(f"[red]Run not found: {run_id}[/red]")
    except Exception as e:
        rprint(f"[red]Error replaying run: {e}[/red]")


@runs_group.command(name="cleanup")
@click.option(
    "--older-than",
    default=30,
    help="Delete runs older than N days",
)
@click.option(
    "--max-runs",
    type=int,
    help="Keep only N most recent runs per type",
)
@click.option("--dry-run", is_flag=True, help="Show what would be deleted")
def cleanup_runs(older_than, max_runs, dry_run):
    """Clean up old runs."""
    storage = get_run_storage()

    if dry_run:
        rprint("[yellow]DRY RUN - No files will be deleted[/yellow]")

        # Count runs that would be deleted
        cutoff_date = datetime.now() - timedelta(days=older_than)

        agent_query = RunQuery(until=cutoff_date, limit=10000)
        agent_runs = storage.list_agent_runs(agent_query)

        workflow_query = RunQuery(until=cutoff_date, limit=10000)
        workflow_runs = storage.list_workflow_runs(workflow_query)

        total = len(agent_runs) + len(workflow_runs)
        rprint(f"\nWould delete {total} runs:")
        rprint(f"  • Agent runs: {len(agent_runs)}")
        rprint(f"  • Workflow runs: {len(workflow_runs)}")

    else:
        deleted_count = storage.cleanup_old_runs(
            max_age_days=older_than, max_runs=max_runs
        )
        rprint(f"[green]Deleted {deleted_count} old runs[/green]")


@runs_group.command(name="search")
@click.option("--agent-id", help="Filter by agent ID")
@click.option("--workflow-id", help="Filter by workflow ID")
@click.option(
    "--status",
    type=click.Choice([s.value for s in RunStatus]),
    help="Filter by status",
)
@click.option("--since", help="Since date (YYYY-MM-DD)")
@click.option("--until", help="Until date (YYYY-MM-DD)")
@click.option("--limit", default=50, help="Maximum number of results")
def search_runs(agent_id, workflow_id, status, since, until, limit):
    """Search runs with advanced filtering."""
    # Parse dates
    since_dt = None
    until_dt = None

    if since:
        try:
            since_dt = datetime.strptime(since, "%Y-%m-%d")
        except ValueError:
            rprint("[red]Invalid since date format. Use YYYY-MM-DD[/red]")
            return

    if until:
        try:
            until_dt = datetime.strptime(until, "%Y-%m-%d")
        except ValueError:
            rprint("[red]Invalid until date format. Use YYYY-MM-DD[/red]")
            return

    # Create query
    query = RunQuery(
        agent_id=agent_id,
        workflow_id=workflow_id,
        status=RunStatus(status) if status else None,
        since=since_dt,
        until=until_dt,
        limit=limit,
    )

    # Search
    storage = get_run_storage()
    agent_runs = storage.list_agent_runs(query)
    workflow_runs = storage.list_workflow_runs(query)

    total = len(agent_runs) + len(workflow_runs)
    rprint(f"\n[bold cyan]Found {total} runs[/bold cyan]")

    if agent_runs:
        rprint(f"\nAgent runs: {len(agent_runs)}")
        for run in agent_runs[:10]:  # Show first 10
            rprint(f"  • {run.run_id} - {run.agent_name} - {run.status.value}")

    if workflow_runs:
        rprint(f"\nWorkflow runs: {len(workflow_runs)}")
        for run in workflow_runs[:10]:  # Show first 10
            rprint(f"  • {run.run_id} - {run.workflow_name} - {run.status.value}")
