"""Paracle CLI - MCP server commands.

Commands for managing the Model Context Protocol (MCP) server:
- serve: Start MCP server (stdio or HTTP)
- list: List available MCP tools

The MCP server exposes all Paracle tools to IDEs and AI assistants,
enabling tool execution via the Model Context Protocol.

MCP Specification: https://modelcontextprotocol.io/
"""

import sys

import click
from rich.console import Console
from rich.table import Table

console = Console()
stderr_console = Console(file=sys.stderr)

# Tool category prefixes
PREFIX_CONTEXT = "context."
PREFIX_WORKFLOW = "workflow."
PREFIX_MEMORY = "memory."


def _categorize_tool(name: str) -> str:
    """Categorize a tool by its name prefix.

    Args:
        name: Tool name

    Returns:
        Category string: "context", "workflow", "memory", "router", or "agent"
    """
    if name.startswith(PREFIX_CONTEXT):
        return "context"
    if name.startswith(PREFIX_WORKFLOW):
        return "workflow"
    if name.startswith(PREFIX_MEMORY):
        return "memory"
    if name == "set_active_agent":
        return "router"
    return "agent"


def _filter_tools_by_category(schemas: list, category: str) -> list:
    """Filter tool schemas by category.

    Args:
        schemas: List of tool schemas
        category: Category to filter by

    Returns:
        Filtered list of tool schemas
    """
    if category == "all":
        return schemas

    return [tool for tool in schemas if _categorize_tool(tool["name"]) == category]


def _group_tools_by_category(schemas: list) -> dict[str, list]:
    """Group tools by their category.

    Args:
        schemas: List of tool schemas

    Returns:
        Dict mapping category to list of tools
    """
    groups: dict[str, list] = {
        "agent": [],
        "context": [],
        "workflow": [],
        "memory": [],
        "router": [],
    }

    for tool in schemas:
        cat = _categorize_tool(tool["name"])
        groups[cat].append(tool)

    return groups


def _print_tools_table(title: str, tools: list, style: str = "cyan") -> None:
    """Print a formatted table of tools.

    Args:
        title: Table title
        tools: List of tool schemas
        style: Rich style for tool names
    """
    if not tools:
        return

    console.print(f"[bold]{title}[/bold]")
    table = Table(show_header=True, header_style="bold", box=None)
    table.add_column("Tool", style=style)
    table.add_column("Description")

    for tool in sorted(tools, key=lambda t: t["name"]):
        desc = tool.get("description", "-")
        # Truncate long descriptions
        if len(desc) > 60:
            desc = desc[:57] + "..."
        table.add_row(tool["name"], desc)

    console.print(table)
    console.print()


@click.group(invoke_without_command=True)
@click.option(
    "--list",
    "-l",
    "list_flag",
    is_flag=True,
    help="List MCP tools (shortcut for 'list')",
)
@click.pass_context
def mcp(ctx: click.Context, list_flag: bool) -> None:
    """MCP server commands.

    Start and manage the Paracle MCP server for IDE tool integration.

    The MCP server exposes all Paracle tools (25+) to IDEs via the
    Model Context Protocol, enabling:

    \b
    - Agent-specific tools (code_generation, git_commit, test_execution...)
    - Context tools (current_state, roadmap, policies, decisions)
    - Workflow tools (run, list)
    - Memory tools (log_action)

    Examples:
        paracle mcp -l              - List MCP tools (shortcut)
        paracle mcp list            - List all MCP tools
        paracle mcp serve --stdio   - Start MCP server
    """
    if list_flag:
        ctx.invoke(mcp_list, category="all", as_json=False)
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@mcp.command("serve")
@click.option(
    "--stdio",
    is_flag=True,
    help="Use stdio transport (recommended for IDE integration)",
)
@click.option(
    "--websocket",
    is_flag=True,
    default=False,
    help="Use WebSocket transport (for remote connections)",
)
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to bind WebSocket server (default: 127.0.0.1)",
)
@click.option(
    "--port",
    default=3000,
    type=int,
    help="HTTP/WebSocket port (default: 3000)",
)
@click.option(
    "--auth",
    type=click.Choice(["none", "jwt"]),
    default="none",
    help="Authentication method for WebSocket (default: none)",
)
def mcp_serve(stdio: bool, websocket: bool, host: str, port: int, auth: str) -> None:
    """Start MCP server exposing Paracle tools.

    The MCP server exposes all Paracle tools to IDEs and AI assistants:

    \b
    Agent Tools (25+):
    - code_analysis, diagram_generation, pattern_matching (architect)
    - code_generation, refactoring, testing (coder)
    - git_add, git_commit, git_status, git_push, git_tag (releasemanager)
    - static_analysis, security_scan, code_review (reviewer)
    - test_generation, test_execution, coverage_analysis (tester)
    - task_tracking, milestone_management (pm)
    - markdown_generation, api_doc_generation (documenter)
    - version_management, changelog_generation (releasemanager)

    \b
    Context Tools:
    - context.current_state - Get current project state
    - context.roadmap - Get project roadmap
    - context.decisions - Get architectural decisions
    - context.policies - Get active policies

    \b
    Workflow Tools:
    - workflow.run - Execute a Paracle workflow
    - workflow.list - List available workflows

    \b
    Memory Tools:
    - memory.log_action - Log agent action

    \b
    Router Tool:
    - set_active_agent - Set active agent for context-aware operations

    Examples:
        paracle mcp serve --stdio    # For IDE integration (recommended)
        paracle mcp serve --websocket --auth jwt  # For remote connections
        paracle mcp serve --port 3000  # For debugging/testing (HTTP)
    """
    try:
        from paracle_mcp.server import ParacleMCPServer
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("Ensure paracle_mcp is properly installed.")
        raise SystemExit(1)

    server = ParacleMCPServer()

    # Validate flags
    if stdio and websocket:
        console.print("[red]Error:[/red] Cannot use both --stdio and --websocket")
        raise SystemExit(1)

    if stdio:
        _serve_stdio(server)
    elif websocket:
        _serve_websocket(server, host, port, auth)
    else:
        _serve_http(server, port)


def _serve_stdio(server) -> None:
    """Run MCP server in stdio mode."""
    stderr_console.print("[dim]Starting MCP server (stdio transport)...[/dim]")
    stderr_console.print("[dim]Press Ctrl+C to stop.[/dim]")
    try:
        server.serve_stdio()
    except KeyboardInterrupt:
        stderr_console.print("\n[dim]MCP server stopped.[/dim]")


def _serve_http(server, port: int) -> None:
    """Run MCP server in HTTP mode."""
    console.print(f"\n[bold]Starting MCP server on port {port}...[/bold]\n")
    console.print(f"  [green]Endpoint:[/green] http://localhost:{port}/mcp")
    console.print(f"  [green]Health:[/green]   http://localhost:{port}/health")
    console.print("\n[dim]Press Ctrl+C to stop.[/dim]\n")

    try:
        server.serve_http(port=port)
    except KeyboardInterrupt:
        console.print("\n[dim]MCP server stopped.[/dim]")
    except ImportError:
        console.print("[red]Error:[/red] HTTP transport requires aiohttp.")
        console.print("Install with: pip install aiohttp")
        raise SystemExit(1)


def _serve_websocket(server, host: str, port: int, auth: str) -> None:
    """Run MCP server in WebSocket mode."""
    console.print("\n[bold]Starting MCP WebSocket server...[/bold]\n")
    console.print(f"  [green]Endpoint:[/green] ws://{host}:{port}/mcp")
    console.print(f"  [green]Auth:[/green]     {auth}")
    console.print("\n[dim]Press Ctrl+C to stop.[/dim]\n")

    if auth == "jwt":
        console.print("[yellow]Note:[/yellow] JWT authentication requires valid token")
        console.print("[dim]Generate token with: paracle auth generate-token[/dim]\n")

    try:
        server.serve_websocket(host=host, port=port, auth=auth)
    except KeyboardInterrupt:
        console.print("\n[dim]MCP server stopped.[/dim]")
    except ImportError:
        console.print("[red]Error:[/red] WebSocket transport requires websockets.")
        console.print("Install with: pip install websockets")
        raise SystemExit(1)
    except AttributeError:
        console.print("[red]Error:[/red] WebSocket server not implemented yet.")
        console.print("This feature will be available in v1.3.0.")
        raise SystemExit(1)


@mcp.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option(
    "--category",
    type=click.Choice(["agent", "context", "workflow", "memory", "all"]),
    default="all",
    help="Filter by tool category",
)
def mcp_list(as_json: bool, category: str) -> None:
    """List available MCP tools.

    Shows all tools that will be exposed by the MCP server.

    Examples:
        paracle mcp list
        paracle mcp list --json
        paracle mcp list --category context
    """
    try:
        from paracle_mcp.server import ParacleMCPServer
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("Ensure paracle_mcp is properly installed.")
        raise SystemExit(1)

    server = ParacleMCPServer()
    schemas = server.get_tool_schemas()

    # Filter by category if specified
    schemas = _filter_tools_by_category(schemas, category)

    if as_json:
        import json

        console.print(json.dumps(schemas, indent=2))
        return

    _display_tools_list(schemas, category)


def _display_tools_list(schemas: list, category: str) -> None:
    """Display formatted tools list.

    Args:
        schemas: List of tool schemas
        category: Current filter category
    """
    console.print("\n[bold]Available MCP Tools:[/bold]\n")

    groups = _group_tools_by_category(schemas)

    # Display categories with their styles
    category_config = [
        ("agent", "Agent Tools", "cyan"),
        ("context", "Context Tools", "green"),
        ("workflow", "Workflow Tools", "yellow"),
        ("memory", "Memory Tools", "magenta"),
        ("router", "Router Tools", "blue"),
    ]

    for cat_key, title, style in category_config:
        if category in ("all", cat_key) and groups[cat_key]:
            _print_tools_table(title, groups[cat_key], style)

    console.print(f"[dim]Total: {len(schemas)} tools[/dim]")


@mcp.command("config")
@click.option(
    "--ide",
    type=click.Choice(["vscode", "cursor", "windsurf", "claude"]),
    help="Show config for specific IDE",
)
def mcp_config(ide: str | None) -> None:
    """Show MCP configuration for IDEs.

    Displays the configuration snippet needed to integrate Paracle MCP
    with various IDEs.

    Examples:
        paracle mcp config
        paracle mcp config --ide vscode
    """
    configs = _get_ide_configs()

    if ide:
        _show_single_ide_config(configs, ide)
    else:
        _show_all_ide_configs(configs)


def _get_ide_configs() -> dict:
    """Get MCP configuration snippets for all IDEs."""
    return {
        "vscode": {
            "title": "VS Code (settings.json or .vscode/mcp.json)",
            "config": """{
  "mcp": {
    "servers": {
      "paracle": {
        "command": "paracle",
        "args": ["mcp", "serve", "--stdio"]
      }
    }
  }
}""",
        },
        "cursor": {
            "title": "Cursor (Settings > MCP)",
            "config": """Command: paracle
Args: mcp serve --stdio

Or in mcp_config.json:
{
  "mcpServers": {
    "paracle": {
      "command": "paracle",
      "args": ["mcp", "serve", "--stdio"]
    }
  }
}""",
        },
        "windsurf": {
            "title": "Windsurf (~/.codeium/windsurf/mcp_config.json)",
            "config": """{
  "mcpServers": {
    "paracle": {
      "command": "paracle",
      "args": ["mcp", "serve", "--stdio"],
      "env": {}
    }
  }
}""",
        },
        "claude": {
            "title": "Claude Code (~/.claude/mcp_servers.json)",
            "config": """{
  "mcpServers": {
    "paracle": {
      "command": "paracle",
      "args": ["mcp", "serve", "--stdio"]
    }
  }
}""",
        },
    }


def _show_single_ide_config(configs: dict, ide: str) -> None:
    """Show configuration for a single IDE."""
    if ide in configs:
        cfg = configs[ide]
        console.print(f"\n[bold]{cfg['title']}[/bold]\n")
        console.print(cfg["config"])
        console.print()


def _show_all_ide_configs(configs: dict) -> None:
    """Show configuration for all IDEs."""
    console.print("\n[bold]MCP Configuration for IDEs[/bold]\n")

    for cfg in configs.values():
        console.print(f"[cyan]## {cfg['title']}[/cyan]\n")
        console.print(cfg["config"])
        console.print()

    console.print("[dim]After configuring, restart your IDE to enable MCP tools.[/dim]")
