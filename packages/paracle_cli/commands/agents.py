"""CLI commands for agent management.

Commands:
- list: List all agents
- get: Get specific agent details
- export: Export agents to various formats

Note: These commands consume the Paracle REST API.
Ensure the API is running (uvicorn paracle_api.main:app).
"""

from pathlib import Path

import click
import httpx
from rich.console import Console
from rich.table import Table

console = Console()

# API configuration
API_BASE_URL = "http://localhost:8000"

# Error messages
ERR_API_CONNECT = "[red]Error:[/red] Cannot connect to Paracle API."
ERR_API_INSTRUCTION = "Ensure API is running: uvicorn paracle_api.main:app"


def get_api_client() -> httpx.Client:
    """Get HTTP client for API calls.

    Returns:
        Configured httpx.Client instance.
    """
    return httpx.Client(base_url=API_BASE_URL, timeout=10.0)


def handle_api_error(response: httpx.Response, default_message: str) -> None:
    """Handle API error responses.

    Args:
        response: HTTP response object.
        default_message: Default error message if detail not available.
    """
    if response.status_code == 404:
        detail = response.json().get("detail", default_message)
        console.print(f"[red]Error:[/red] {detail}")
    elif response.status_code == 500:
        detail = response.json().get("detail", "Internal server error")
        console.print(f"[red]Error:[/red] {detail}")
    else:
        console.print(
            f"[red]Error:[/red] API returned status {response.status_code}"
        )
        console.print(response.text)
    raise SystemExit(1)


def get_parac_root_or_exit() -> Path:
    """Get .parac/ root or exit with error.

    This function is deprecated - API handles .parac/ discovery.
    Kept for backward compatibility.
    """
    from paracle_core.parac.state import find_parac_root

    parac_root = find_parac_root()
    if parac_root is None:
        console.print("[red]Error:[/red] No .parac/ directory found.")
        console.print(
            "Run 'paracle init' to create one, or navigate to a project."
        )
        raise SystemExit(1)
    return parac_root


@click.group()
def agents() -> None:
    """Manage and discover agents in .parac/ workspace."""
    pass


@agents.command("list")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
)
def list_agents(output_format: str) -> None:
    """List all agents defined in .parac/agents/specs/.

    Examples:
        paracle agents list
        paracle agents list --format=json
        paracle agents list --format=yaml
    """
    try:
        with get_api_client() as client:
            response = client.get("/agents")

        if response.status_code != 200:
            handle_api_error(response, "Failed to list agents")

        data = response.json()
        agents = data["agents"]

        if not agents:
            console.print(
                "[yellow]No agents found in .parac/agents/specs/[/yellow]"
            )
            return

        if output_format == "json":
            import json

            console.print(json.dumps(agents, indent=2))

        elif output_format == "yaml":
            import yaml

            console.print(
                yaml.dump(
                    agents, default_flow_style=False, sort_keys=False
                )
            )

        else:  # table
            table = Table(title=f"🤖 Agents ({len(agents)} found)")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="bold")
            table.add_column("Role", style="green")
            table.add_column("Capabilities", style="yellow")

            for agent in agents:
                capabilities = ", ".join(agent["capabilities"][:3])
                if len(agent["capabilities"]) > 3:
                    capabilities += f" +{len(agent['capabilities']) - 3} more"

                table.add_row(
                    agent["id"],
                    agent["name"],
                    agent["role"],
                    capabilities,
                )

            console.print(table)

    except httpx.ConnectError:
        console.print(ERR_API_CONNECT)
        console.print(ERR_API_INSTRUCTION)
        raise SystemExit(1)


@agents.command("get")
@click.argument("agent_id")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["markdown", "json", "yaml"]),
    default="markdown",
)
@click.option("--spec", is_flag=True, help="Show full specification markdown")
def get_agent(agent_id: str, output_format: str, spec: bool) -> None:
    """Get details for a specific agent.

    Examples:
        paracle agents get pm
        paracle agents get coder --spec
        paracle agents get architect --format=json
    """
    try:
        with get_api_client() as client:
            if spec:
                # Get full specification
                response = client.get(f"/agents/{agent_id}/spec")
                if response.status_code != 200:
                    handle_api_error(
                        response, f"Agent '{agent_id}' not found"
                    )

                data = response.json()
                console.print(data["content"])
                return

            # Get metadata
            response = client.get(f"/agents/{agent_id}")
            if response.status_code != 200:
                handle_api_error(response, f"Agent '{agent_id}' not found")

            agent = response.json()

            if output_format == "json":
                import json

                console.print(json.dumps(agent, indent=2))

            elif output_format == "yaml":
                import yaml

                console.print(
                    yaml.dump(
                        agent, default_flow_style=False, sort_keys=False
                    )
                )

            else:  # markdown
                console.print(f"# {agent['name']}\n")
                console.print(f"**ID**: {agent['id']}")
                console.print(f"**Role**: {agent['role']}")
                console.print(f"**Spec File**: {agent['spec_file']}")
                console.print(f"\n**Description**: {agent['description']}\n")

                if agent["capabilities"]:
                    console.print("**Capabilities**:")
                    for cap in agent["capabilities"]:
                        console.print(f"  • {cap}")

    except httpx.ConnectError:
        console.print(ERR_API_CONNECT)
        console.print(ERR_API_INSTRUCTION)
        raise SystemExit(1)


@agents.command("export")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "yaml"]),
    default="json",
)
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def export_agents(output_format: str, output: str | None) -> None:
    """Export all agents to JSON or YAML.

    Examples:
        paracle agents export > agents.json
        paracle agents export --format=yaml --output=agents.yaml
    """
    try:
        with get_api_client() as client:
            response = client.get("/agents")

        if response.status_code != 200:
            handle_api_error(response, "Failed to export agents")

        data = response.json()
        agents = data["agents"]

        if output_format == "json":
            import json

            content = json.dumps(agents, indent=2)
        else:  # yaml
            import yaml

            content = yaml.dump(
                agents, default_flow_style=False, sort_keys=False
            )

        if output:
            Path(output).write_text(content, encoding="utf-8")
            console.print(
                f"[green]Exported {len(agents)} agents to {output}[/green]"
            )
        else:
            console.print(content)

    except httpx.ConnectError:
        console.print(ERR_API_CONNECT)
        console.print(ERR_API_INSTRUCTION)
        raise SystemExit(1)
