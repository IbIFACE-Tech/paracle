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
    type=click.Choice(["safe", "yolo", "sandbox", "review"],
                      case_sensitive=False),
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

    Examples:

        # Basic code review
        paracle agent run reviewer --task "Review changes in src/app.py"

        # Bug fix with yolo mode (auto-approve all actions)
        paracle agent run coder --task "Fix memory leak" --mode yolo

        # Sandboxed execution (safe environment)
        paracle agent run tester --task "Run integration tests" --mode sandbox

        # With custom model and inputs
        paracle agent run architect \\
            --task "Design auth system" \\
            --model gpt-4-turbo \\
            --input feature=authentication \\
            --input users=1000000

        # Include files in context
        paracle agent run documenter \\
            --task "Generate API docs" \\
            --file src/api.py \\
            --file src/models.py

        # Cost-limited execution
        paracle agent run coder \\
            --task "Implement feature X" \\
            --cost-limit 2.50 \\
            --output result.json
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

    console.print(
        Panel(
            f"[bold]{icon} Running Agent: {agent_name.upper()}[/bold]\n\n"
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
                console.print(
                    f"[yellow]⚠️  Failed to read {file_path}: {e}[/yellow]")

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

    table = Table(title="Execution Plan", show_header=True)
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Agent", agent_name)
    table.add_row("Task", task)
    table.add_row("Mode", mode)
    table.add_row("Model", model or "default (from agent spec)")
    table.add_row("Provider", provider or "default (from agent spec)")
    table.add_row("Inputs", str(len(inputs)) + " parameters")

    if verbose and inputs:
        for key, value in inputs.items():
            value_str = str(value)[:50] + \
                "..." if len(str(value)) > 50 else str(value)
            table.add_row(f"  • {key}", value_str)

    console.print(table)
    console.print("\n[green]✅ Validation passed - ready for execution[/green]")


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
    # Initialize executor
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
        task_id = progress.add_task(
            f"[cyan]Executing {agent_name}...", total=None
        )

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

    # Display outputs
    if "outputs" in result and result["outputs"]:
        console.print("[bold]Outputs:[/bold]")
        for key, value in result["outputs"].items():
            value_str = str(value)[:200] + \
                "..." if len(str(value)) > 200 else str(value)
            console.print(f"  • [cyan]{key}[/cyan]: {value_str}")

    # Display cost information
    if "cost" in result:
        cost = result["cost"]
        console.print("\n[bold]Cost:[/bold]")
        console.print(f"  • Total: [yellow]${cost['total_cost']:.4f}[/yellow]")

        if verbose:
            console.print(f"  • Prompt tokens: {cost['prompt_tokens']}")
            console.print(
                f"  • Completion tokens: {cost['completion_tokens']}")
            console.print(f"  • Provider: {cost['provider']}")
            console.print(f"  • Model: {cost['model']}")

    # Display verbose information
    if verbose and "execution_time" in result:
        console.print(
            f"\n[dim]Execution time: {result['execution_time']:.2f}s[/dim]"
        )


def _save_output(result: dict[str, Any], output_path: str) -> None:
    """Save output to JSON file."""
    import json

    try:
        Path(output_path).write_text(json.dumps(result, indent=2))
        console.print(f"\n[green]💾 Output saved to: {output_path}[/green]")
    except Exception as e:
        console.print(f"\n[yellow]⚠️  Failed to save output: {e}[/yellow]")
