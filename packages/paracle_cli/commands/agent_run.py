"""CLI command for running individual agents for tasks."""

import asyncio
from pathlib import Path
from typing import Any

import click
from paracle_domain.models import WorkflowStep
from paracle_orchestration.agent_executor import AgentExecutor
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()


def _is_remote_agent(agent_name: str) -> bool:
    """Check if agent name refers to a remote A2A agent.

    Remote agents can be specified as:
    - "remote:agent_id" - explicit remote prefix
    - "agent_id" - if registered in remote agent registry

    Args:
        agent_name: Agent identifier

    Returns:
        True if agent is a remote A2A agent
    """
    if agent_name.startswith("remote:"):
        return True
    try:
        from paracle_a2a.registry import get_remote_registry

        registry = get_remote_registry()
        return registry.is_remote(agent_name)
    except ImportError:
        return False


def _get_remote_agent(agent_name: str) -> Any:
    """Get remote agent configuration.

    Args:
        agent_name: Agent identifier (with or without 'remote:' prefix)

    Returns:
        RemoteAgentConfig or None if not found
    """
    try:
        from paracle_a2a.registry import get_remote_registry

        registry = get_remote_registry()
        return registry.resolve(agent_name)
    except ImportError:
        return None


@click.command("run")
@click.argument("agent_name")
@click.option(
    "--task",
    "-t",
    required=True,
    help="Task description or instruction for the agent",
)
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["safe", "yolo", "sandbox", "review"], case_sensitive=False),
    default="safe",
    help="Execution mode: safe (default), yolo (auto-approve), sandbox (isolated), review (human-in-loop)",
)
@click.option(
    "--model",
    default=None,
    help="LLM model to use (e.g., gpt-4, gpt-4-turbo, claude-3-opus)",
)
@click.option(
    "--provider",
    type=click.Choice(
        ["openai", "anthropic", "google", "mistral", "groq", "ollama"],
        case_sensitive=False,
    ),
    default=None,
    help="LLM provider (defaults to agent spec or openai)",
)
@click.option(
    "--temperature",
    type=float,
    default=None,
    help="Temperature for generation (0.0-2.0)",
)
@click.option(
    "--max-tokens",
    type=int,
    default=None,
    help="Maximum tokens to generate",
)
@click.option(
    "--input",
    "-i",
    multiple=True,
    help="Input key-value pairs (format: key=value)",
)
@click.option(
    "--file",
    "-f",
    multiple=True,
    type=click.Path(exists=True),
    help="Input files to include in context",
)
@click.option(
    "--timeout",
    type=int,
    default=300,
    help="Execution timeout in seconds (default: 300)",
)
@click.option(
    "--cost-limit",
    type=float,
    default=None,
    help="Maximum cost in USD (execution aborts if exceeded)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Save output to file (JSON format)",
)
@click.option(
    "--stream/--no-stream",
    default=True,
    help="Stream output in real-time",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed execution information",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Validate without executing",
)
def run(
    agent_name: str,
    task: str,
    mode: str,
    model: str | None,
    provider: str | None,
    temperature: float | None,
    max_tokens: int | None,
    input: tuple[str],
    file: tuple[str],
    timeout: int,
    cost_limit: float | None,
    output: str | None,
    stream: bool,
    verbose: bool,
    dry_run: bool,
) -> None:
    """Run a single agent for a specific task.

    Supports both local Paracle agents and remote A2A agents.

    Examples:

        # Basic code review
        paracle agents run reviewer --task "Review changes in src/app.py"

        # Bug fix with yolo mode (auto-approve all actions)
        paracle agents run coder --task "Fix memory leak" --mode yolo

        # Sandboxed execution (safe environment)
        paracle agents run tester --task "Run integration tests" --mode sandbox

        # With custom model and inputs
        paracle agents run architect \\
            --task "Design auth system" \\
            --model gpt-4-turbo \\
            --input feature=authentication \\
            --input users=1000000

        # Include files in context
        paracle agents run documenter \\
            --task "Generate API docs" \\
            --file src/api.py \\
            --file src/models.py

        # Cost-limited execution
        paracle agents run coder \\
            --task "Implement feature X" \\
            --cost-limit 2.50 \\
            --output result.json

        # Run a remote A2A agent (defined in manifest)
        paracle agents run remote:external-coder --task "Write unit tests"

        # Run remote agent by ID (if in registry)
        paracle agents run partner-analyst --task "Analyze sales data"
    """
    # Display header
    _display_header(agent_name, task, mode)

    # Parse inputs
    inputs = _parse_inputs(input, file)

    # Validate mode
    if mode == "sandbox" and not _check_sandbox_available():
        console.print(
            "[yellow]⚠️  Sandbox mode not available, falling back to safe mode[/yellow]"
        )
        mode = "safe"

    if dry_run:
        _dry_run(agent_name, task, mode, model, provider, inputs, verbose)
        return

    # Execute agent task
    try:
        result = asyncio.run(
            _execute_agent_task(
                agent_name=agent_name,
                task=task,
                mode=mode,
                model=model,
                provider=provider,
                temperature=temperature,
                max_tokens=max_tokens,
                inputs=inputs,
                timeout=timeout,
                cost_limit=cost_limit,
                stream=stream,
                verbose=verbose,
            )
        )

        # Display results
        _display_results(result, verbose)

        # Save output if requested
        if output:
            _save_output(result, output)

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Execution cancelled by user[/yellow]")
        raise click.Abort()
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        if verbose:
            console.print_exception()
        raise click.Abort()


def _display_header(agent_name: str, task: str, mode: str) -> None:
    """Display execution header."""
    mode_colors = {
        "safe": "green",
        "yolo": "yellow",
        "sandbox": "cyan",
        "review": "blue",
    }
    mode_icons = {
        "safe": "🛡️",
        "yolo": "🚀",
        "sandbox": "📦",
        "review": "👀",
    }

    color = mode_colors.get(mode, "white")
    icon = mode_icons.get(mode, "⚙️")

    # Check if remote agent
    is_remote = _is_remote_agent(agent_name)
    agent_type = "[magenta]REMOTE A2A[/magenta]" if is_remote else "LOCAL"

    # Get remote agent info if applicable
    remote_info = ""
    if is_remote:
        remote_agent = _get_remote_agent(agent_name)
        if remote_agent:
            remote_info = f"\nEndpoint: [dim]{remote_agent.url}[/dim]"
            icon = "🌐"

    console.print(
        Panel(
            f"[bold]{icon} Running Agent: {agent_name.upper()}[/bold]\n"
            f"Type: {agent_type}{remote_info}\n\n"
            f"Task: {task}\n"
            f"Mode: [{color}]{mode.upper()}[/{color}]",
            title="[bold cyan]Paracle Agent Execution[/bold cyan]",
            border_style="cyan",
        )
    )


def _parse_inputs(input_args: tuple[str], files: tuple[str]) -> dict[str, Any]:
    """Parse input arguments and files."""
    inputs: dict[str, Any] = {}

    # Parse key=value pairs
    for arg in input_args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            inputs[key] = value
        else:
            console.print(f"[yellow]⚠️  Invalid input format: {arg}[/yellow]")

    # Load file contents
    if files:
        inputs["files"] = []
        for file_path in files:
            try:
                content = Path(file_path).read_text()
                inputs["files"].append({"path": file_path, "content": content})
            except Exception as e:
                console.print(f"[yellow]⚠️  Failed to read {file_path}: {e}[/yellow]")

    return inputs


def _check_sandbox_available() -> bool:
    """Check if sandbox execution is available."""
    try:
        from paracle_sandbox import SandboxExecutor  # noqa: F401

        return True
    except ImportError:
        return False


def _dry_run(
    agent_name: str,
    task: str,
    mode: str,
    model: str | None,
    provider: str | None,
    inputs: dict[str, Any],
    verbose: bool,
) -> None:
    """Perform dry run validation."""
    console.print("\n[bold cyan]🔍 DRY RUN - Validation Only[/bold cyan]\n")

    is_remote = _is_remote_agent(agent_name)

    table = Table(title="Execution Plan", show_header=True)
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Agent", agent_name)
    table.add_row("Type", "[magenta]Remote A2A[/magenta]" if is_remote else "Local")
    table.add_row("Task", task)
    table.add_row("Mode", mode)

    if is_remote:
        remote_agent = _get_remote_agent(agent_name)
        if remote_agent:
            table.add_row("Endpoint", remote_agent.url)
            table.add_row("Auth", remote_agent.auth_type or "none")
        else:
            table.add_row("Endpoint", "[red]NOT FOUND[/red]")
    else:
        table.add_row("Model", model or "default (from agent spec)")
        table.add_row("Provider", provider or "default (from agent spec)")

    table.add_row("Inputs", str(len(inputs)) + " parameters")

    if verbose and inputs:
        for key, value in inputs.items():
            value_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
            table.add_row(f"  • {key}", value_str)

    console.print(table)

    # Validate remote agent exists
    if is_remote:
        remote_agent = _get_remote_agent(agent_name)
        if not remote_agent:
            console.print(f"\n[red]❌ Remote agent not found: {agent_name}[/red]")
            console.print(
                "[dim]Define remote agents in .parac/agents/manifest.yaml under remote_agents:[/dim]"
            )
            return

    console.print("\n[green]✅ Validation passed - ready for execution[/green]")


async def _execute_remote_agent_task(
    agent_name: str,
    task: str,
    inputs: dict[str, Any],
    timeout: int,
    stream: bool,
    verbose: bool,
) -> dict[str, Any]:
    """Execute task on a remote A2A agent.

    Args:
        agent_name: Remote agent identifier
        task: Task description
        inputs: Input parameters
        timeout: Timeout in seconds
        stream: Whether to stream responses
        verbose: Show verbose output

    Returns:
        Execution result dict
    """
    from paracle_a2a.client import ParacleA2AClient
    from paracle_a2a.models import TaskState

    remote_agent = _get_remote_agent(agent_name)
    if not remote_agent:
        raise RuntimeError(f"Remote agent not found: {agent_name}")

    # Build message with task and inputs
    message = task
    if inputs:
        import json

        message += f"\n\nInputs:\n```json\n{json.dumps(inputs, indent=2)}\n```"

    # Create client
    config = remote_agent.get_client_config()
    config.timeout_seconds = float(timeout)
    client = ParacleA2AClient(remote_agent.url, config)

    import time

    start_time = time.time()

    if stream:
        # Streaming execution
        result_text = ""
        status = "unknown"

        async for event in client.invoke_streaming(message=message):
            from paracle_a2a.models import (
                TaskArtifactUpdateEvent,
                TaskStatusUpdateEvent,
            )

            if isinstance(event, TaskStatusUpdateEvent):
                status = event.status.state.value
                if verbose and event.status.message:
                    console.print(f"[dim]Status: {event.status.message}[/dim]")
            elif isinstance(event, TaskArtifactUpdateEvent):
                for part in event.artifact.parts:
                    if hasattr(part, "text"):
                        result_text += part.text
                        if verbose:
                            console.print(part.text, end="")

        execution_time = time.time() - start_time
        return {
            "outputs": {"result": result_text},
            "status": status,
            "execution_time": execution_time,
            "remote_agent": {
                "id": remote_agent.id,
                "name": remote_agent.name,
                "url": remote_agent.url,
            },
        }
    else:
        # Non-streaming execution
        a2a_task = await client.invoke(message=message, wait=True)

        execution_time = time.time() - start_time

        result_text = ""
        if a2a_task.status.state == TaskState.COMPLETED:
            result_text = a2a_task.status.message or "Task completed"

        return {
            "outputs": {"result": result_text},
            "status": a2a_task.status.state.value,
            "task_id": a2a_task.id,
            "context_id": a2a_task.context_id,
            "execution_time": execution_time,
            "remote_agent": {
                "id": remote_agent.id,
                "name": remote_agent.name,
                "url": remote_agent.url,
            },
        }


async def _execute_agent_task(
    agent_name: str,
    task: str,
    mode: str,
    model: str | None,
    provider: str | None,
    temperature: float | None,
    max_tokens: int | None,
    inputs: dict[str, Any],
    timeout: int,
    cost_limit: float | None,
    stream: bool,
    verbose: bool,
) -> dict[str, Any]:
    """Execute agent task."""
    # Check for remote agent
    if _is_remote_agent(agent_name):
        return await _execute_remote_agent_task(
            agent_name=agent_name,
            task=task,
            inputs=inputs,
            timeout=timeout,
            stream=stream,
            verbose=verbose,
        )

    # Initialize executor for local agent
    executor = AgentExecutor()

    # Build step configuration
    config: dict[str, Any] = {
        "system_prompt": task,
    }

    if model:
        config["model"] = model
    if provider:
        config["provider"] = provider
    if temperature is not None:
        config["temperature"] = temperature
    if max_tokens:
        config["max_tokens"] = max_tokens

    # Add mode-specific config
    if mode == "yolo":
        config["auto_approve"] = True
    elif mode == "sandbox":
        config["sandbox"] = True
    elif mode == "review":
        config["requires_approval"] = True

    # Create workflow step
    step = WorkflowStep(
        id=f"{agent_name}_task",
        name=task[:50],  # Truncate for display
        agent=agent_name,
        config=config,
        inputs=inputs,
    )

    # Execute with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task_id = progress.add_task(f"[cyan]Executing {agent_name}...", total=None)

        try:
            result = await asyncio.wait_for(
                executor.execute_step(step, inputs), timeout=timeout
            )

            progress.update(task_id, completed=True)

            # Check cost limit
            if cost_limit and result.get("cost", {}).get("total_cost", 0) > cost_limit:
                raise RuntimeError(
                    f"Cost limit exceeded: ${result['cost']['total_cost']:.4f} > ${cost_limit:.2f}"
                )

            return result

        except asyncio.TimeoutError:
            progress.stop()
            raise RuntimeError(f"Execution timed out after {timeout} seconds")


def _display_results(result: dict[str, Any], verbose: bool) -> None:
    """Display execution results."""
    console.print("\n[bold green]✅ Execution Complete[/bold green]\n")

    # Display remote agent info if applicable
    if "remote_agent" in result:
        remote = result["remote_agent"]
        console.print("[bold]Remote Agent:[/bold]")
        console.print(f"  • ID: [magenta]{remote['id']}[/magenta]")
        console.print(f"  • Name: {remote['name']}")
        if verbose:
            console.print(f"  • URL: [dim]{remote['url']}[/dim]")
        if "task_id" in result:
            console.print(f"  • Task ID: [dim]{result['task_id']}[/dim]")
        if "context_id" in result and result["context_id"]:
            console.print(f"  • Context ID: [dim]{result['context_id']}[/dim]")
        console.print()

    # Display status for remote agents
    if "status" in result:
        status = result["status"]
        status_color = "green" if status == "completed" else "yellow"
        console.print(f"[bold]Status:[/bold] [{status_color}]{status}[/{status_color}]")

    # Display outputs
    if "outputs" in result and result["outputs"]:
        console.print("[bold]Outputs:[/bold]")
        for key, value in result["outputs"].items():
            value_str = (
                str(value)[:200] + "..." if len(str(value)) > 200 else str(value)
            )
            console.print(f"  • [cyan]{key}[/cyan]: {value_str}")

    # Display cost information
    if "cost" in result:
        cost = result["cost"]
        console.print("\n[bold]Cost:[/bold]")
        console.print(f"  • Total: [yellow]${cost['total_cost']:.4f}[/yellow]")

        if verbose:
            console.print(f"  • Prompt tokens: {cost['prompt_tokens']}")
            console.print(f"  • Completion tokens: {cost['completion_tokens']}")
            console.print(f"  • Provider: {cost['provider']}")
            console.print(f"  • Model: {cost['model']}")

    # Display verbose information
    if verbose and "execution_time" in result:
        console.print(f"\n[dim]Execution time: {result['execution_time']:.2f}s[/dim]")


def _save_output(result: dict[str, Any], output_path: str) -> None:
    """Save output to JSON file."""
    import json

    try:
        Path(output_path).write_text(json.dumps(result, indent=2))
        console.print(f"\n[green]💾 Output saved to: {output_path}[/green]")
    except Exception as e:
        console.print(f"\n[yellow]⚠️  Failed to save output: {e}[/yellow]")
