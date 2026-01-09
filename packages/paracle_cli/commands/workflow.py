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
    from paracle_orchestration.workflow_loader import WorkflowLoader

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
        # Quick health check using typed method
        return client.is_available()
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


@click.group(invoke_without_command=True)
@click.option(
    "--list",
    "-l",
    "list_flag",
    is_flag=True,
    help="List all workflows (shortcut for 'list')",
)
@click.pass_context
def workflow(ctx: click.Context, list_flag: bool) -> None:
    """Manage workflows and workflow executions.

    Examples:
        # List all workflows (shortcut)
        $ paracle workflow -l

        # List all workflows
        $ paracle workflow list

        # Execute a workflow
        $ paracle workflow run my-workflow --input key=value

        # Check execution status
        $ paracle workflow status exec_abc123

        # Cancel running execution
        $ paracle workflow cancel exec_abc123
    """
    if list_flag:
        ctx.invoke(list_workflows, status=None, limit=100, offset=0, output_json=False)
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


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
        result = client.workflow_list(limit=limit, offset=offset, status=status)

        if output_json:
            console.print_json(json.dumps(result))
            return

        workflows = result.get("workflows", [])
        total = result.get("total", 0)

        if not workflows:
            console.print("[dim]No workflows found.[/dim]")
            return

        # Create table
        table = Table(title="Workflows", show_header=True, header_style="bold cyan")
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
        console.print(f"\n[dim]Showing {len(workflows)} of {total} workflows[/dim]")

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
@click.option(
    "--yolo",
    "--auto-approve",
    is_flag=True,
    help="Auto-approve all approval gates (YOLO mode)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Dry-run mode: mock LLM responses for cost-free testing",
)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def run_workflow(
    workflow_id: str,
    input: tuple[str, ...],
    sync: bool,
    watch: bool,
    yolo: bool,
    dry_run: bool,
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

        # Auto-approve all approval gates (YOLO mode)
        $ paracle workflow run my-workflow --yolo
    """
    # Parse inputs
    inputs = {}
    for input_pair in input:
        if "=" not in input_pair:
            console.print(f"[red]✗ Invalid input format:[/red] {input_pair}")
            console.print("[dim]Use key=value format, e.g., -i source=data.csv[/dim]")
            raise click.Abort()
        key, value = input_pair.split("=", 1)
        inputs[key.strip()] = value.strip()

    # YOLO mode warning
    if yolo:
        console.print(
            "[yellow]⚠️  YOLO MODE - " "Auto-approving all approval gates[/yellow]"
        )

    # Dry-run mode warning
    if dry_run:
        console.print(
            "[blue]🔵 DRY-RUN MODE - " "Using mocked LLM responses (no cost)[/blue]"
        )

    # API-first: Try API, fallback to local if unavailable
    use_local = _use_local_fallback()

    if use_local:
        # Local execution fallback
        _run_workflow_local(
            workflow_id, inputs, sync or watch, output_json, yolo, dry_run
        )
        return

    # API execution (preferred)
    client = get_client()

    try:
        # Execute workflow
        async_execution = not sync and not watch

        # Build execution parameters
        execution_params = {
            "workflow_id": workflow_id,
            "inputs": inputs,
            "async_execution": async_execution,
            "auto_approve": yolo,
            "dry_run": dry_run,  # Pass dry-run flag to API
        }

        result = client.workflow_execute(**execution_params)

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


@workflow.command("plan")
@click.argument("workflow_id")
@click.option(
    "--input",
    "-i",
    multiple=True,
    help="Input key=value pairs (can be repeated)",
)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def plan_workflow(
    workflow_id: str,
    input: tuple[str, ...],
    output_json: bool,
) -> None:
    """Generate an execution plan for a workflow without running it.

    This command analyzes the workflow DAG and provides:
    - Execution order (topologically sorted)
    - Parallel execution opportunities
    - Estimated cost (tokens and USD)
    - Estimated time
    - Approval gates
    - Optimization suggestions

    Args:
        workflow_id: Workflow ID or name to plan

    Examples:
        # Generate execution plan
        $ paracle workflow plan my-workflow

        # With inputs for better estimation
        $ paracle workflow plan my-workflow -i source=data.csv

        # JSON output for automation
        $ paracle workflow plan my-workflow --json
    """
    # Parse inputs
    inputs = {}
    for input_pair in input:
        if "=" not in input_pair:
            console.print(f"[red]✗ Invalid input format:[/red] {input_pair}")
            console.print("[dim]Use key=value format, e.g., -i source=data.csv[/dim]")
            raise click.Abort()
        key, value = input_pair.split("=", 1)
        inputs[key.strip()] = value.strip()

    # API-first: Try API, fallback to local if unavailable
    use_local = _use_local_fallback()

    if use_local:
        # Local planning fallback
        _plan_workflow_local(workflow_id, inputs, output_json)
        return

    # API execution (preferred)
    client = get_client()

    try:
        # Generate execution plan via API using typed method
        plan_data = client.workflow_plan(workflow_id, inputs)

        if output_json:
            console.print_json(json.dumps(plan_data))
            return

        # Display plan in rich format
        _display_execution_plan(plan_data)

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
def status_execution(execution_id: str, output_json: bool, watch: bool) -> None:
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
            console.print(f"[green]Completed Steps:[/green] {', '.join(completed)}")

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


@workflow.command("create")
@click.argument("workflow_id")
@click.option(
    "--description",
    "-d",
    help="Description of what the workflow does",
)
@click.option(
    "--template",
    "-t",
    type=click.Choice(["sequential", "parallel", "conditional"]),
    default="sequential",
    help="Workflow template type",
)
@click.option(
    "--ai-enhance",
    is_flag=True,
    help="Use AI to enhance the workflow specification",
)
@click.option(
    "--ai-provider",
    type=click.Choice(["auto", "meta", "openai", "anthropic", "azure"]),
    default="auto",
    help="AI provider to use (requires --ai-enhance)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Overwrite existing workflow",
)
def create_workflow(
    workflow_id: str,
    description: str | None,
    template: str,
    ai_enhance: bool,
    ai_provider: str,
    force: bool,
) -> None:
    """Create a new workflow from template, optionally AI-enhanced.

    Creates a new workflow specification in .parac/workflows/ with all
    required sections pre-filled.

    With --ai-enhance, uses AI to generate detailed steps, conditions,
    and error handling based on the description.

    Template Types:
        sequential: Steps run one after another (default)
        parallel: Steps run concurrently where possible
        conditional: Steps with conditions and branches

    Examples:
        # Basic template
        paracle workflow create code-review -t sequential

        # AI-enhanced (requires AI provider)
        paracle workflow create test-pipeline \\
            --description "Run unit tests, then integration tests" \\
            --ai-enhance

        # With specific AI provider
        paracle workflow create deploy \\
            --description "Build, test, and deploy to production" \\
            --ai-enhance --ai-provider anthropic

    After creating, you should:
        1. Edit .parac/workflows/<workflow_id>.yaml
        2. Add agent references and step details
        3. Run 'paracle workflow plan <workflow_id>' to validate
    """
    import asyncio
    import re

    # Check workflow_id format
    if not re.match(r"^[a-z][a-z0-9-]*$", workflow_id):
        console.print(
            "[red]Error:[/red] Workflow ID must be lowercase, "
            "start with a letter, and contain only letters, numbers, hyphens"
        )
        raise SystemExit(1)

    # Find .parac root
    from paracle_cli.utils import get_parac_root_or_exit

    parac_root = get_parac_root_or_exit()
    workflows_dir = parac_root / "workflows"
    workflow_file = workflows_dir / f"{workflow_id}.yaml"

    # Check if exists
    if workflow_file.exists() and not force:
        console.print(f"[red]Error:[/red] Workflow already exists: {workflow_file}")
        console.print("Use --force to overwrite")
        raise SystemExit(1)

    # AI enhancement if requested
    ai_generated_content = None
    if ai_enhance:
        if not description:
            console.print("[red]Error:[/red] --description required with --ai-enhance")
            raise SystemExit(1)

        from paracle_cli.ai_helper import get_ai_provider

        # Get AI provider
        if ai_provider == "auto":
            ai = get_ai_provider()
        else:
            ai = get_ai_provider(ai_provider)

        if ai is None:
            console.print("[yellow]⚠ AI not available[/yellow]")
            if not click.confirm("Create basic template instead?", default=True):
                console.print("\\n[cyan]To enable AI enhancement:[/cyan]")
                console.print("  pip install paracle[meta]  # Recommended")
                console.print("  pip install paracle[openai]  # Or external")
                raise SystemExit(1)
            ai_enhance = False  # Fall back to basic template
        else:
            console.print(f"[dim]Using AI provider: {ai.name}[/dim]")
            console.print(f"[dim]Generating enhanced workflow: {description}[/dim]\\n")

            with console.status("[bold cyan]Generating workflow spec..."):
                result = asyncio.run(
                    ai.generate_workflow(
                        f"Workflow ID: {workflow_id}\\n"
                        f"Template: {template}\\n"
                        f"Description: {description}"
                    )
                )

            ai_generated_content = result.get("yaml", "")
            console.print("[green]✓[/green] AI-enhanced workflow spec generated")

    # Create from template (if not AI-enhanced)
    if ai_generated_content:
        workflow_content = ai_generated_content
    else:
        # Generate template based on type
        display_name = workflow_id.replace("-", " ").title()
        desc = description or f"{display_name} workflow"

        if template == "sequential":
            workflow_content = f"""---
id: {workflow_id}
name: "{display_name}"
description: "{desc}"
version: "1.0.0"

steps:
  - id: step_1
    name: "First Step"
    agent: coder  # Replace with appropriate agent
    task: "TODO: Describe what this step does"
    mode: safe

  - id: step_2
    name: "Second Step"
    agent: reviewer  # Replace with appropriate agent
    task: "TODO: Describe what this step does"
    mode: safe
    depends_on:
      - step_1

error_handling:
  on_failure: rollback
  notify: []
"""
        elif template == "parallel":
            workflow_content = f"""---
id: {workflow_id}
name: "{display_name}"
description: "{desc}"
version: "1.0.0"

steps:
  - id: step_1a
    name: "Parallel Step A"
    agent: coder
    task: "TODO: Describe parallel task A"
    mode: safe

  - id: step_1b
    name: "Parallel Step B"
    agent: tester
    task: "TODO: Describe parallel task B"
    mode: safe

  - id: step_2
    name: "Final Step"
    agent: reviewer
    task: "TODO: Describe final step"
    mode: safe
    depends_on:
      - step_1a
      - step_1b

error_handling:
  on_failure: rollback
  notify: []
"""
        else:  # conditional
            workflow_content = f"""---
id: {workflow_id}
name: "{display_name}"
description: "{desc}"
version: "1.0.0"

steps:
  - id: step_1
    name: "Check Condition"
    agent: coder
    task: "TODO: Describe check"
    mode: safe

  - id: step_2a
    name: "If True"
    agent: coder
    task: "TODO: Execute if condition met"
    mode: safe
    depends_on:
      - step_1
    condition: "{{{{ step_1.success }}}}"

  - id: step_2b
    name: "If False"
    agent: coder
    task: "TODO: Execute if condition not met"
    mode: safe
    depends_on:
      - step_1
    condition: "{{{{ not step_1.success }}}}"

error_handling:
  on_failure: rollback
  notify: []
"""

    # Ensure directory exists
    workflows_dir.mkdir(parents=True, exist_ok=True)

    # Write file
    workflow_file.write_text(workflow_content, encoding="utf-8")

    console.print(f"[green]OK[/green] Created workflow: {workflow_file}")
    console.print()
    console.print("Next steps:")
    console.print(f"  1. Edit {workflow_file.relative_to(parac_root.parent)}")
    console.print("  2. Update agent references and tasks")
    console.print(f"  3. Run: paracle workflow plan {workflow_id}")
    console.print(f"  4. Run: paracle workflow run {workflow_id}")
    console.print()
    console.print("[dim]See .parac/workflows/README.md for workflow syntax[/dim]")


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
                    console.print("\n[green]✓ Workflow completed successfully[/green]")
                elif status == "failed":
                    error = result.get("error", "Unknown error")
                    console.print(f"\n[red]✗ Workflow failed:[/red] {error}")
                else:
                    console.print("\n[yellow]! Workflow cancelled[/yellow]")
                break

            time.sleep(2)  # Poll every 2 seconds

        except KeyboardInterrupt:
            console.print("\n[yellow]Stopped watching (execution continues)[/yellow]")
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
    yolo: bool = False,
    dry_run: bool = False,
) -> None:
    """Execute workflow locally (fallback when API unavailable).

    Args:
        workflow_id: Workflow ID to execute
        inputs: Workflow inputs
        sync: Whether to run synchronously
        output_json: Whether to output JSON
        yolo: YOLO mode - auto-approve all approval gates
        dry_run: Dry-run mode - mock LLM responses
    """
    import asyncio

    from paracle_domain.models import Workflow, generate_id
    from paracle_events import EventBus
    from paracle_orchestration.engine import WorkflowOrchestrator
    from paracle_orchestration.workflow_loader import WorkflowLoader, WorkflowLoadError

    try:
        # Load workflow spec from YAML
        loader = WorkflowLoader()

        try:
            spec = loader.load_workflow_spec(workflow_id)
        except WorkflowLoadError as e:
            console.print(f"[red]✗ Workflow not found:[/red] {workflow_id}")
            console.print(f"[dim]Error: {e}[/dim]")
            console.print("[dim]Available workflows: paracle workflow list[/dim]")
            raise click.Abort()

        # Create workflow instance
        workflow = Workflow(id=generate_id("workflow"), spec=spec)

        # Generate execution ID
        execution_id = f"local_{workflow_id}_{int(time.time())}"

        if output_json:
            # Simple JSON output for local execution
            result = {
                "execution_id": execution_id,
                "status": "running" if not sync else "pending",
                "message": "Executing locally (API unavailable)",
                "mode": "sync" if sync else "async",
                "workflow": workflow_id,
            }
            console.print_json(json.dumps(result))

        if sync:
            console.print(f"[cyan]Executing workflow:[/cyan] {spec.name}")
            console.print(f"[dim]Execution ID:[/dim] {execution_id}")
            console.print(f"[dim]Steps:[/dim] {len(spec.steps)}")
            console.print()

            # Initialize orchestration components
            event_bus = EventBus()

            # Create real agent executor
            from paracle_orchestration.agent_executor import AgentExecutor

            agent_executor = AgentExecutor()

            # Create orchestrator and execute
            orchestrator = WorkflowOrchestrator(
                event_bus=event_bus,
                step_executor=agent_executor.execute_step,
            )

            context = asyncio.run(
                orchestrator.execute(workflow, inputs, auto_approve=yolo)
            )

            console.print()
            if context.status.value == "completed":
                console.print("[green]✓ Workflow completed successfully[/green]")

                from rich.table import Table

                # Display outputs in a rich table format
                if context.outputs:
                    console.print("\n[bold]📦 Workflow Outputs:[/bold]")
                    table = Table(show_header=True, header_style="bold cyan")
                    table.add_column("Output", style="cyan")
                    table.add_column("Value", style="white")

                    for key, value in context.outputs.items():
                        if isinstance(value, dict | list):
                            value_str = json.dumps(value, indent=2)
                        else:
                            value_str = str(value)

                        # Truncate long values
                        if len(value_str) > 200:
                            value_str = value_str[:197] + "..."

                        table.add_row(key, value_str)

                    console.print(table)

                # Display execution metadata
                if hasattr(context, "metadata") and context.metadata:
                    console.print("\n[bold]ℹ️  Execution Details:[/bold]")
                    meta_table = Table(show_header=False)
                    meta_table.add_column("Property", style="dim")
                    meta_table.add_column("Value", style="white")

                    for key, value in context.metadata.items():
                        meta_table.add_row(key, str(value))

                    console.print(meta_table)
            else:
                console.print(f"[red]✗ Workflow {context.status.value}[/red]")
                if context.error:
                    console.print(f"[dim]Error:[/dim] {context.error}")
        else:
            console.print(
                "[yellow]⚠️  Async local execution " "not fully supported[/yellow]"
            )
            console.print("[dim]Use --sync for complete local execution[/dim]")

    except Exception as e:
        console.print(f"[red]✗ Local execution error:[/red] {e}")
        if not output_json:
            import traceback

            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise click.Abort()


def _list_workflows_local(
    status_filter: str | None,
    limit: int,
    offset: int,
    output_json: bool,
) -> None:
    """List workflows locally (fallback when API unavailable).

    Loads workflows from .parac/workflows/ directory using WorkflowLoader.

    Args:
        status_filter: Optional status filter (active/inactive/all)
        limit: Max workflows to return
        offset: Pagination offset
        output_json: Whether to output JSON
    """
    try:
        # Use WorkflowLoader to read workflows from YAML files
        loader = WorkflowLoader()

        # List workflows from catalog
        workflows_metadata = loader.list_workflows(status=status_filter)

        # Load full specs for display
        workflows = []
        for meta in workflows_metadata:
            try:
                spec = loader.load_workflow_spec(meta["name"])
                workflows.append(
                    {
                        "id": meta["name"],  # Use name as ID for YAML workflows
                        "name": meta["name"],
                        "description": meta.get("description", ""),
                        "category": meta.get("category", "general"),
                        "status": meta.get("status", "active"),
                        "spec": {
                            "name": spec.name,
                            "description": spec.description,
                            "steps": [{"name": s.name} for s in spec.steps],
                        },
                    }
                )
            except Exception as e:
                console.print(
                    f"[yellow]⚠️  Warning: Could not load workflow "
                    f"{meta['name']}: {e}[/yellow]"
                )
                continue

        # Pagination
        total = len(workflows)
        workflows = workflows[offset : offset + limit]

        if output_json:
            console.print_json(json.dumps({"workflows": workflows, "total": total}))
            return

        if not workflows:
            console.print("[dim]No workflows found in .parac/workflows/[/dim]")
            console.print(
                "[dim]Create workflows with YAML files in "
                ".parac/workflows/definitions/[/dim]"
            )
            return

        # Create table
        table = Table(
            title="Workflows (Local - from .parac/)",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Name", style="cyan", width=25)
        table.add_column("Description")
        table.add_column("Steps", justify="right")
        table.add_column("Category", justify="center")
        table.add_column("Status", justify="center")

        for wf in workflows:
            name = wf.get("name", "Unnamed")
            desc = wf.get("description", "")
            steps = len(wf.get("spec", {}).get("steps", []))
            category = wf.get("category", "general")
            wf_status = wf.get("status", "active")

            # Color status
            status_display = wf_status
            if wf_status == "active":
                status_display = f"[green]{wf_status}[/green]"
            elif wf_status == "inactive":
                status_display = f"[dim]{wf_status}[/dim]"

            table.add_row(
                name,
                desc[:40] + "..." if len(desc) > 40 else desc,
                str(steps),
                category,
                status_display,
            )

        console.print(table)
        console.print(f"\n[dim]Showing {len(workflows)} of {total} workflows[/dim]")
        console.print(
            "[dim]Source: .parac/workflows/catalog.yaml "
            "and .parac/workflows/definitions/[/dim]"
        )

    except Exception as e:
        console.print(f"[red]✗ Local listing error:[/red] {e}")
        console.print(
            "[dim]Ensure .parac/workflows/ directory exists with " "catalog.yaml[/dim]"
        )
        raise click.Abort()


def _display_execution_plan(plan: dict[str, Any]) -> None:
    """Display execution plan in rich format.

    Args:
        plan: ExecutionPlan dict from API or planner
    """
    from rich.panel import Panel
    from rich.tree import Tree

    console.print("\n[bold cyan]Workflow Execution Plan[/bold cyan]\n")

    # Overview
    overview_table = Table(show_header=False, box=None)
    overview_table.add_column("Property", style="cyan")
    overview_table.add_column("Value")

    overview_table.add_row("Workflow", plan.get("workflow_name", "Unknown"))
    overview_table.add_row("Total Steps", str(plan.get("total_steps", 0)))
    overview_table.add_row("Estimated Tokens", f"{plan.get('estimated_tokens', 0):,}")
    overview_table.add_row(
        "Estimated Cost", f"${plan.get('estimated_cost_usd', 0):.4f}"
    )
    overview_table.add_row(
        "Estimated Time", f"{plan.get('estimated_time_seconds', 0):.1f}s"
    )

    console.print(Panel(overview_table, title="Overview"))

    # Execution order
    console.print("\n[bold]Execution Order:[/bold]")
    order_tree = Tree("Execution Flow")

    for step_id in plan.get("execution_order", []):
        order_tree.add(f"[cyan]{step_id}[/cyan]")

    console.print(order_tree)

    # Parallel groups
    parallel_groups = plan.get("parallel_groups", [])
    if parallel_groups:
        console.print("\n[bold]Parallel Execution Opportunities:[/bold]")
        for group in parallel_groups:
            if group.get("can_parallelize"):
                steps = group.get("steps", [])
                console.print(
                    f"  [green]✓[/green] Group {group.get('group_number')}: "
                    f"{len(steps)} steps can run in parallel"
                )
                for step in steps:
                    console.print(f"    - {step}")

    # Approval gates
    approval_gates = plan.get("approval_gates", [])
    if approval_gates:
        console.print("\n[bold]Approval Gates:[/bold]")
        for gate in approval_gates:
            console.print(f"  [yellow]⚠[/yellow]  {gate}")

    # Optimization suggestions
    suggestions = plan.get("optimization_suggestions", [])
    if suggestions:
        console.print("\n[bold]Optimization Suggestions:[/bold]")
        for suggestion in suggestions:
            console.print(f"  [blue]💡[/blue] {suggestion}")


def _plan_workflow_local(
    workflow_id: str, inputs: dict[str, Any], output_json: bool
) -> None:
    """Plan workflow execution using local WorkflowPlanner.

    Args:
        workflow_id: Workflow identifier
        inputs: Input parameters
        output_json: Output as JSON
    """
    try:
        from paracle_orchestration import WorkflowPlanner
        from paracle_orchestration.workflow_loader import WorkflowLoader

        # Load workflow spec
        loader = WorkflowLoader()
        workflow_spec = loader.load_workflow_spec(workflow_id)

        # Create planner
        planner = WorkflowPlanner()

        # Generate plan
        execution_plan = planner.plan(workflow_spec)

        # Convert to dict for display
        plan_dict = execution_plan.model_dump()

        if output_json:
            console.print_json(json.dumps(plan_dict))
        else:
            _display_execution_plan(plan_dict)

    except Exception as e:
        console.print(f"[red]✗ Local planning error:[/red] {e}")
        raise click.Abort()
