"""Paracle CLI - Tools Commands.

Commands for managing and testing tools (built-in and MCP).
Phase 4 - Priority 1 CLI Commands.
"""

import json

import click
from paracle_tools import BuiltinToolRegistry
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
def tools() -> None:
    """Manage tools (built-in and MCP).

    Examples:
        # List all available tools
        $ paracle tools list

        # Show tool details
        $ paracle tools info read_file

        # Test a tool
        $ paracle tools test read_file --param path=README.md
    """
    pass


@tools.command("list")
@click.option(
    "--category",
    type=click.Choice(["filesystem", "http", "shell", "mcp"]),
    help="Filter by tool category",
)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def list_tools(category: str | None, output_json: bool) -> None:
    """List all available tools.

    Shows built-in tools and registered MCP tools.

    Examples:
        $ paracle tools list
        $ paracle tools list --category filesystem
        $ paracle tools list --json
    """
    try:
        # Get builtin tools with safe defaults
        import os
        current_dir = os.getcwd()
        registry = BuiltinToolRegistry(
            filesystem_paths=[current_dir],
            allowed_commands=["echo", "cat", "ls"],
        )
        builtin_tools = registry.list_tools()

        # Filter by category if specified
        if category and category != "mcp":
            builtin_tools = [
                t for t in builtin_tools if t.get("category") == category
            ]

        # TODO: Get MCP tools when MCP integration is ready
        mcp_tools = []

        all_tools = builtin_tools + mcp_tools

        if output_json:
            console.print_json(json.dumps(
                {"tools": all_tools, "total": len(all_tools)}))
            return

        if not all_tools:
            console.print("[dim]No tools found.[/dim]")
            return

        # Create table
        table = Table(
            title="Available Tools", show_header=True, header_style="bold cyan"
        )
        table.add_column("Name", style="cyan", width=20)
        table.add_column("Category", width=12)
        table.add_column("Description")
        table.add_column("Source", justify="center", width=8)

        for tool in all_tools:
            source = "builtin" if tool in builtin_tools else "MCP"
            source_style = "[green]builtin[/green]" if source == "builtin" else "[blue]MCP[/blue]"

            desc = tool.get("description", "")
            desc_short = desc[:60] + "..." if len(desc) > 60 else desc

            table.add_row(
                tool.get("name", "unknown"),
                tool.get("category", ""),
                desc_short,
                source_style,
            )

        console.print(table)
        console.print(f"\n[dim]Total: {len(all_tools)} tools[/dim]")
        console.print(
            f"[dim]Built-in: {len(builtin_tools)} | MCP: {len(mcp_tools)}[/dim]"
        )

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise click.Abort()


@tools.command("info")
@click.argument("tool_name")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def info_tool(tool_name: str, output_json: bool) -> None:
    """Show detailed information about a tool.

    Args:
        tool_name: Name of the tool to inspect

    Examples:
        $ paracle tools info read_file
        $ paracle tools info http_get --json
    """
    try:
        # Get builtin tools with safe defaults
        import os
        current_dir = os.getcwd()
        registry = BuiltinToolRegistry(
            filesystem_paths=[current_dir],
            allowed_commands=["echo", "cat", "ls"],
        )

        if not registry.has_tool(tool_name):
            console.print(f"[red]✗ Tool not found:[/red] {tool_name}")
            console.print(
                "\n[dim]Use 'paracle tools list' to see available tools[/dim]")
            raise click.Abort()

        tool = registry.get_tool(tool_name)

        if output_json:
            tool_data = {
                "name": tool.name,
                "category": tool.category,
                "description": tool.description,
                "parameters": tool.parameters,
                "source": "builtin",
            }
            console.print_json(json.dumps(tool_data))
            return

        # Display tool info
        console.print(f"\n[bold cyan]{tool.name}[/bold cyan]")
        console.print(f"[dim]Category:[/dim] {tool.category}")
        console.print("[dim]Source:[/dim] [green]Built-in[/green]\n")

        console.print("[bold]Description:[/bold]")
        console.print(f"  {tool.description}\n")

        console.print("[bold]Parameters:[/bold]")
        if tool.parameters:
            for param_name, param_info in tool.parameters.items():
                required = param_info.get("required", False)
                param_type = param_info.get("type", "any")
                param_desc = param_info.get("description", "")

                req_badge = "[red]*[/red]" if required else " "
                console.print(
                    f"  {req_badge} [cyan]{param_name}[/cyan] ({param_type})")
                if param_desc:
                    console.print(f"      {param_desc}")
        else:
            console.print("  [dim]No parameters[/dim]")

        # Show permissions if applicable
        permissions = registry.get_tool_permissions(tool_name)
        if permissions:
            console.print("\n[bold]Permissions Required:[/bold]")
            for perm in permissions:
                console.print(f"  • {perm}")

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise click.Abort()


@tools.command("test")
@click.argument("tool_name")
@click.option(
    "--param",
    "-p",
    multiple=True,
    help="Parameter key=value pairs (can be repeated)",
)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def test_tool(tool_name: str, param: tuple[str, ...], output_json: bool) -> None:
    """Test a tool with sample parameters.

    Args:
        tool_name: Name of the tool to test

    Examples:
        # Test read_file tool
        $ paracle tools test read_file -p path=README.md

        # Test http_get tool
        $ paracle tools test http_get -p url=https://api.example.com/data
    """
    try:
        # Get builtin tools with safe defaults
        import os
        current_dir = os.getcwd()
        registry = BuiltinToolRegistry(
            filesystem_paths=[current_dir],
            allowed_commands=["echo", "cat", "ls", "pwd"],
        )

        if not registry.has_tool(tool_name):
            console.print(f"[red]✗ Tool not found:[/red] {tool_name}")
            raise click.Abort()

        # Parse parameters
        params = {}
        for param_pair in param:
            if "=" not in param_pair:
                console.print(
                    f"[red]✗ Invalid parameter format:[/red] {param_pair}")
                console.print(
                    "[dim]Use key=value format, e.g., -p path=README.md[/dim]")
                raise click.Abort()
            key, value = param_pair.split("=", 1)
            params[key.strip()] = value.strip()

        # Execute tool
        console.print(f"[dim]Testing tool:[/dim] {tool_name}")
        console.print(f"[dim]Parameters:[/dim] {params}\n")

        result = registry.execute_tool(tool_name, params)

        if output_json:
            result_data = {
                "success": result.success,
                "output": result.output,
                "error": result.error,
                "metadata": result.metadata,
            }
            console.print_json(json.dumps(result_data))
            return

        # Display result
        if result.success:
            console.print("[green]✓ Tool executed successfully[/green]\n")
            console.print("[bold]Output:[/bold]")
            console.print(result.output)
        else:
            console.print("[red]✗ Tool execution failed[/red]\n")
            console.print("[bold]Error:[/bold]")
            console.print(result.error)

        if result.metadata:
            console.print("\n[bold]Metadata:[/bold]")
            for key, value in result.metadata.items():
                console.print(f"  {key}: {value}")

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise click.Abort()


@tools.command("register")
@click.argument("tool_spec_path")
@click.option("--name", help="Tool name (defaults to filename)")
@click.option("--category", help="Tool category")
def register_tool(tool_spec_path: str, name: str | None, category: str | None) -> None:
    """Register a custom tool from spec file.

    Args:
        tool_spec_path: Path to tool specification (JSON or YAML)

    Examples:
        $ paracle tools register ./my_tool.json
        $ paracle tools register ./my_tool.yaml --name custom_tool --category custom

    Note:
        Custom tool registration is planned for Phase 5.
    """
    console.print(
        "[yellow]⚠️  Custom tool registration coming in Phase 5[/yellow]")
    console.print(f"[dim]Spec file:[/dim] {tool_spec_path}")
    if name:
        console.print(f"[dim]Name:[/dim] {name}")
    if category:
        console.print(f"[dim]Category:[/dim] {category}")
    console.print(
        "\n[dim]Use built-in tools for now with 'paracle tools list'[/dim]")
