"""CLI commands for sandbox management."""

import asyncio
import json
from pathlib import Path

import click
from paracle_sandbox import SandboxConfig, SandboxExecutor, SandboxManager
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.group("sandbox")
def sandbox_group():
    """Sandbox management commands for isolated execution."""
    pass


@sandbox_group.command("execute")
@click.argument("code_file", type=click.Path(exists=True))
@click.option("--cpu", type=float, default=1.0, help="CPU cores limit (0.5-16.0)")
@click.option("--memory", type=int, default=512, help="Memory limit in MB (128-16384)")
@click.option("--timeout", type=int, default=300, help="Timeout in seconds (10-3600)")
@click.option(
    "--network",
    type=click.Choice(["none", "bridge", "host"]),
    default="none",
    help="Network mode",
)
@click.option("--inputs", type=click.Path(exists=True), help="JSON file with inputs")
@click.option("--monitor/--no-monitor", default=True, help="Enable resource monitoring")
@click.option("--output", type=click.Path(), help="Save results to JSON file")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def execute(
    code_file: str,
    cpu: float,
    memory: int,
    timeout: int,
    network: str,
    inputs: str | None,
    monitor: bool,
    output: str | None,
    verbose: bool,
):
    """Execute code in isolated sandbox.

    Example:
        paracle sandbox execute agent.py --cpu 1.0 --memory 512 --timeout 300
    """
    console.print(Panel.fit("🔒 Sandbox Execution", style="bold blue"))

    # Load code
    code_path = Path(code_file)
    agent_code = code_path.read_text()

    # Load inputs if provided
    inputs_data = {}
    if inputs:
        inputs_path = Path(inputs)
        inputs_data = json.loads(inputs_path.read_text())

    # Create configuration
    config = SandboxConfig(
        cpu_cores=cpu,
        memory_mb=memory,
        timeout_seconds=timeout,
        network_mode=network,
    )

    # Display configuration
    if verbose:
        config_table = Table(title="Sandbox Configuration")
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="green")
        config_table.add_row("CPU Cores", f"{config.cpu_cores}")
        config_table.add_row("Memory", f"{config.memory_mb} MB")
        config_table.add_row("Timeout", f"{config.timeout_seconds}s")
        config_table.add_row("Network", config.network_mode)
        config_table.add_row(
            "Monitoring", "Enabled" if monitor else "Disabled")
        console.print(config_table)

    # Execute
    async def run():
        executor = SandboxExecutor()
        console.print(f"\n[cyan]Executing {code_path.name}...[/cyan]")

        result = await executor.execute_agent(
            agent_code=agent_code,
            config=config,
            inputs=inputs_data,
            monitor=monitor,
        )

        # Display results
        if result["success"]:
            console.print("\n[bold green]✅ Execution Successful[/bold green]")
            console.print(
                f"\n[bold]Output:[/bold]\n{result['result']['stdout']}")

            if result["result"]["stderr"]:
                console.print(
                    f"\n[yellow]Warnings:[/yellow]\n{result['result']['stderr']}"
                )
        else:
            console.print("\n[bold red]❌ Execution Failed[/bold red]")
            console.print(
                f"\n[red]Error:[/red] {result.get('error', 'Unknown error')}")

        # Display stats
        if "stats" in result and verbose:
            stats = result["stats"]
            stats_table = Table(title="Resource Usage")
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="yellow")
            stats_table.add_row("CPU", f"{stats.get('cpu_percent', 0):.1f}%")
            stats_table.add_row(
                "Memory", f"{stats.get('memory_mb', 0):.1f} MB")
            stats_table.add_row(
                "Memory %", f"{stats.get('memory_percent', 0):.1f}%"
            )
            console.print(stats_table)

        # Save output
        if output:
            output_path = Path(output)
            output_path.write_text(json.dumps(result, indent=2))
            console.print(f"\n[green]Results saved to {output}[/green]")

        return result

    result = asyncio.run(run())
    raise SystemExit(0 if result["success"] else 1)


@sandbox_group.command("health")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def health(verbose: bool):
    """Check sandbox availability.

    Example:
        paracle sandbox health
    """
    console.print(Panel.fit("🔍 Sandbox Health Check", style="bold blue"))

    async def check():
        executor = SandboxExecutor()
        result = await executor.health_check()

        if result["available"]:
            console.print("\n[bold green]✅ Sandbox Available[/bold green]")
            console.print("  Docker: ✓ Connected")
            console.print("  Test: ✓ Passed")
        else:
            console.print("\n[bold red]❌ Sandbox Not Available[/bold red]")
            console.print(f"  Error: {result.get('error', 'Unknown error')}")

            if not result.get("docker_available"):
                console.print(
                    "\n[yellow]💡 Docker is not available. Install Docker to use sandbox mode.[/yellow]"
                )
                console.print(
                    "   Visit: https://docs.docker.com/get-docker/"
                )

        if verbose:
            console.print(
                f"\n[dim]Full result:[/dim]\n{json.dumps(result, indent=2)}")

        return result["available"]

    available = asyncio.run(check())
    raise SystemExit(0 if available else 1)


@sandbox_group.command("test")
@click.option("--cpu", type=float, default=0.5, help="CPU cores limit")
@click.option("--memory", type=int, default=256, help="Memory limit in MB")
def test(cpu: float, memory: int):
    """Test sandbox with simple execution.

    Example:
        paracle sandbox test --cpu 0.5 --memory 256
    """
    console.print(Panel.fit("🧪 Sandbox Test", style="bold blue"))

    test_code = """
import sys
import os

print("Sandbox Test OK")
print(f"Python: {sys.version}")
print(f"Working dir: {os.getcwd()}")
print(f"Available memory: {os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024**2):.0f} MB")
"""

    async def run_test():
        executor = SandboxExecutor()

        config = SandboxConfig(
            cpu_cores=cpu,
            memory_mb=memory,
            timeout_seconds=30,
        )

        console.print(
            f"\n[cyan]Running test with {cpu} CPU cores and {memory} MB memory...[/cyan]"
        )

        result = await executor.execute_agent(
            agent_code=test_code,
            config=config,
            monitor=False,
        )

        if result["success"]:
            console.print("\n[bold green]✅ Test Passed[/bold green]")
            console.print(f"\n{result['result']['stdout']}")
        else:
            console.print("\n[bold red]❌ Test Failed[/bold red]")
            console.print(f"\n{result.get('error', 'Unknown error')}")

        return result["success"]

    success = asyncio.run(run_test())
    raise SystemExit(0 if success else 1)


@sandbox_group.command("list")
def list_sandboxes():
    """List active sandboxes.

    Example:
        paracle sandbox list
    """
    console.print(Panel.fit("📦 Active Sandboxes", style="bold blue"))

    async def list_active():
        manager = SandboxManager()
        stats = await manager.get_stats()

        if stats["total_sandboxes"] == 0:
            console.print("\n[yellow]No active sandboxes[/yellow]")
            return

        console.print(
            f"\n[cyan]Total: {stats['total_sandboxes']}/{stats['max_concurrent']}[/cyan]"
        )
        console.print(
            f"[cyan]Utilization: {stats['utilization']*100:.1f}%[/cyan]\n"
        )

        table = Table(title="Active Sandboxes")
        table.add_column("Sandbox ID", style="cyan")
        table.add_column("CPU %", style="yellow")
        table.add_column("Memory MB", style="green")
        table.add_column("Memory %", style="magenta")

        for sandbox_id, sandbox_stats in stats["sandboxes"].items():
            if "error" in sandbox_stats:
                table.add_row(
                    sandbox_id[:8],
                    "-",
                    "-",
                    f"[red]{sandbox_stats['error']}[/red]",
                )
            else:
                table.add_row(
                    sandbox_id[:8],
                    f"{sandbox_stats.get('cpu_percent', 0):.1f}",
                    f"{sandbox_stats.get('memory_mb', 0):.1f}",
                    f"{sandbox_stats.get('memory_percent', 0):.1f}",
                )

        console.print(table)

    asyncio.run(list_active())


@sandbox_group.command("cleanup")
@click.option("--all", "cleanup_all", is_flag=True, help="Destroy all sandboxes")
@click.option("--force", is_flag=True, help="Force cleanup without confirmation")
def cleanup(cleanup_all: bool, force: bool):
    """Cleanup sandboxes.

    Example:
        paracle sandbox cleanup --all
    """
    console.print(Panel.fit("🧹 Sandbox Cleanup", style="bold blue"))

    if not cleanup_all:
        console.print("[yellow]Use --all to cleanup all sandboxes[/yellow]")
        return

    if not force:
        confirm = click.confirm(
            "Are you sure you want to destroy all sandboxes?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    async def cleanup_all_sandboxes():
        manager = SandboxManager()
        stats = await manager.get_stats()
        count = stats["total_sandboxes"]

        if count == 0:
            console.print("\n[yellow]No active sandboxes to cleanup[/yellow]")
            return

        console.print(f"\n[cyan]Destroying {count} sandbox(es)...[/cyan]")

        await manager.destroy_all()

        console.print(f"\n[green]✅ Cleaned up {count} sandbox(es)[/green]")

    asyncio.run(cleanup_all_sandboxes())
