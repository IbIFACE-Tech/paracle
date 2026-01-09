"""CLI commands for plugin management."""

import asyncio
import sys

import click
from rich.console import Console
from rich.table import Table

console = Console()
stderr_console = Console(file=sys.stderr)


@click.group(name="plugin")
def plugin_group():
    """Manage Paracle plugins."""
    pass


@plugin_group.command(name="list")
@click.option("--type", "-t", help="Filter by plugin type")
def list_plugins(type: str):
    """List all registered plugins."""
    from paracle_plugins.registry import get_plugin_registry

    try:
        registry = get_plugin_registry()
        plugins = registry.list_plugins()

        # Filter by type if specified
        if type:
            plugins = [p for p in plugins if p["type"] == type]

        if not plugins:
            console.print("[yellow]No plugins registered[/yellow]")
            return

        # Create table
        table = Table(title="Registered Plugins")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Type", style="magenta")
        table.add_column("Author", style="blue")
        table.add_column("Capabilities", style="yellow")

        for plugin in plugins:
            table.add_row(
                plugin["name"],
                plugin["version"],
                plugin["type"],
                plugin["author"],
                ", ".join(plugin["capabilities"][:3]),  # First 3
            )

        console.print(table)
        console.print(f"\nTotal: {len(plugins)} plugins")
    except Exception as e:
        stderr_console.print(f"[red]Error listing plugins: {e}[/red]")
        sys.exit(1)


@plugin_group.command(name="show")
@click.argument("plugin_name")
def show_plugin(plugin_name: str):
    """Show detailed plugin information."""
    from paracle_plugins.registry import get_plugin_registry

    try:
        registry = get_plugin_registry()
        plugin = registry.get_plugin(plugin_name)

        if not plugin:
            stderr_console.print(f"[red]Plugin '{plugin_name}' not found[/red]")
            sys.exit(1)

        metadata = plugin.metadata

        console.print(f"\n[bold cyan]Plugin: {metadata.name}[/bold cyan]")
        console.print(f"Version: {metadata.version}")
        console.print(f"Type: {metadata.plugin_type.value}")
        console.print(f"Description: {metadata.description}")
        console.print(f"Author: {metadata.author}")

        if metadata.homepage:
            console.print(f"Homepage: {metadata.homepage}")

        console.print(f"License: {metadata.license}")
        console.print(f"Paracle Version: {metadata.paracle_version}")

        if metadata.capabilities:
            console.print("\nCapabilities:")
            for cap in metadata.capabilities:
                console.print(f"  • {cap.value}")

        if metadata.dependencies:
            console.print("\nDependencies:")
            for dep in metadata.dependencies:
                console.print(f"  • {dep}")

        if metadata.tags:
            console.print(f"\nTags: {', '.join(metadata.tags)}")

        console.print()
    except Exception as e:
        stderr_console.print(f"[red]Error showing plugin: {e}[/red]")
        sys.exit(1)


@plugin_group.command(name="health")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def health_check(output_json: bool):
    """Check health of all registered plugins."""
    import json

    from paracle_plugins.registry import get_plugin_registry

    try:
        registry = get_plugin_registry()
        results = asyncio.run(registry.health_check_all())

        if output_json:
            console.print(json.dumps(results, indent=2))
        else:
            table = Table(title="Plugin Health Check")
            table.add_column("Plugin", style="cyan")
            table.add_column("Version", style="green")
            table.add_column("Status", style="magenta")
            table.add_column("Details")

            for plugin_name, result in results.items():
                status = result.get("status", "unknown")
                status_style = "green" if status == "healthy" else "red"

                details = result.get("error", "")
                if not details and "capabilities" in result:
                    details = f"{len(result['capabilities'])} capabilities"

                table.add_row(
                    plugin_name,
                    result.get("version", "?"),
                    f"[{status_style}]{status}[/{status_style}]",
                    details,
                )

            console.print(table)
    except Exception as e:
        stderr_console.print(f"[red]Error checking plugin health: {e}[/red]")
        sys.exit(1)


@plugin_group.command(name="load")
@click.option(
    "--source",
    type=click.Choice(["all", "directory", "config", "entry_points"]),
    default="all",
    help="Plugin source to load from",
)
def load_plugins(source: str):
    """Load plugins from configured sources."""
    from paracle_plugins.loader import PluginLoader

    try:
        loader = PluginLoader()

        if source == "all":
            count = asyncio.run(loader.load_all())
        elif source == "directory":
            count = asyncio.run(loader.load_from_directory())
        elif source == "config":
            count = asyncio.run(loader.load_from_config())
        elif source == "entry_points":
            count = asyncio.run(loader.load_from_entry_points())
        else:
            stderr_console.print(f"[red]Unknown source: {source}[/red]")
            sys.exit(1)

        console.print(f"[green]✓[/green] Loaded {count} plugins from {source}")
    except Exception as e:
        stderr_console.print(f"[red]Error loading plugins: {e}[/red]")
        sys.exit(1)


@plugin_group.command(name="reload")
@click.argument("plugin_name")
def reload_plugin(plugin_name: str):
    """Reload a specific plugin."""
    from paracle_plugins.loader import PluginLoader

    try:
        loader = PluginLoader()
        success = asyncio.run(loader.reload_plugin(plugin_name))

        if success:
            console.print(f"[green]✓[/green] Reloaded plugin '{plugin_name}'")
        else:
            stderr_console.print(f"[red]Failed to reload plugin '{plugin_name}'[/red]")
            sys.exit(1)
    except Exception as e:
        stderr_console.print(f"[red]Error reloading plugin: {e}[/red]")
        sys.exit(1)


@plugin_group.command(name="stats")
def plugin_stats():
    """Show plugin statistics."""
    from paracle_plugins.registry import get_plugin_registry

    try:
        registry = get_plugin_registry()

        table = Table(title="Plugin Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Plugins", str(registry.count))

        for plugin_type, count in registry.count_by_type.items():
            table.add_row(f"  {plugin_type.capitalize()}", str(count))

        console.print(table)
    except Exception as e:
        stderr_console.print(f"[red]Error getting plugin stats: {e}[/red]")
        sys.exit(1)


def register_commands(cli_group):
    """Register plugin commands with CLI."""
    cli_group.add_command(plugin_group)
