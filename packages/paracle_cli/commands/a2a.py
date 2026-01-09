"""A2A Protocol CLI Commands.

Commands for managing A2A server and client operations.
"""

import asyncio
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group(name="a2a")
def a2a() -> None:
    """A2A (Agent-to-Agent) protocol commands.

    Manage A2A server and interact with external A2A agents.
    """
    pass


# =============================================================================
# SERVER COMMANDS
# =============================================================================


@a2a.command("serve")
@click.option(
    "--host",
    default="0.0.0.0",
    help="Server host address",
)
@click.option(
    "--port",
    "-p",
    default=8080,
    type=int,
    help="Server port",
)
@click.option(
    "--agents",
    "-a",
    multiple=True,
    help="Agent IDs to expose (default: all)",
)
@click.option(
    "--parac-root",
    type=click.Path(exists=True, file_okay=False),
    default=".parac",
    help="Path to .parac directory",
)
@click.option(
    "--no-streaming",
    is_flag=True,
    help="Disable SSE streaming",
)
@click.option(
    "--auth",
    type=click.Choice(["none", "apikey", "bearer"]),
    default="none",
    help="Authentication mode",
)
@click.option(
    "--api-key",
    envvar="PARACLE_A2A_API_KEY",
    help="API key for authentication",
)
def serve(
    host: str,
    port: int,
    agents: tuple[str, ...],
    parac_root: str,
    no_streaming: bool,
    auth: str,
    api_key: str | None,
) -> None:
    """Start A2A server exposing Paracle agents.

    Example:
        paracle a2a serve --port 8080
        paracle a2a serve --agents coder,reviewer --auth apikey
    """
    try:
        from paracle_a2a.config import A2AServerConfig, SecuritySchemeConfig
        from paracle_a2a.server.app import run_a2a_server
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("Install with: pip install paracle[api]")
        raise SystemExit(1)

    # Build config
    security_schemes = []
    require_auth = False

    if auth == "apikey" and api_key:
        require_auth = True
        security_schemes.append(
            SecuritySchemeConfig(
                scheme="apiKey",
                type="apiKey",
                api_key_name="X-API-Key",
                api_key_location="header",
            )
        )
    elif auth == "bearer":
        require_auth = True
        security_schemes.append(
            SecuritySchemeConfig(
                scheme="bearer",
                type="http",
                bearer_format="JWT",
            )
        )

    config = A2AServerConfig(
        host=host,
        port=port,
        agent_ids=list(agents),
        expose_all_agents=len(agents) == 0,
        enable_streaming=not no_streaming,
        require_authentication=require_auth,
        security_schemes=security_schemes,
        api_keys=[api_key] if api_key else [],
        parac_root=parac_root,
    )

    console.print(f"[green]Starting A2A server on {host}:{port}[/green]")
    console.print(f"  Base path: {config.base_path}")
    console.print(
        f"  Agents: {'all' if config.expose_all_agents else ', '.join(agents)}"
    )
    console.print(f"  Streaming: {not no_streaming}")
    console.print(f"  Auth: {auth}")
    console.print()
    console.print(f"Agent Card: http://{host}:{port}/.well-known/agent.json")
    console.print()

    run_a2a_server(Path(parac_root), config)


# =============================================================================
# AGENT COMMANDS
# =============================================================================


@a2a.group("agents")
def agents_group() -> None:
    """Discover and list A2A agents."""
    pass


@agents_group.command("list")
@click.option(
    "--url",
    "-u",
    help="Remote A2A server URL",
)
@click.option(
    "--local",
    is_flag=True,
    help="List local Paracle agents",
)
@click.option(
    "--parac-root",
    type=click.Path(exists=True, file_okay=False),
    default=".parac",
    help="Path to .parac directory",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def list_agents(
    url: str | None,
    local: bool,
    parac_root: str,
    output_format: str,
) -> None:
    """List available A2A agents.

    Example:
        paracle a2a agents list --local
        paracle a2a agents list --url http://example.com/a2a
    """
    if local or not url:
        _list_local_agents(Path(parac_root), output_format)
    else:
        asyncio.run(_list_remote_agents(url, output_format))


def _list_local_agents(parac_root: Path, output_format: str) -> None:
    """List local agents."""
    from paracle_a2a.config import A2AServerConfig
    from paracle_a2a.server.agent_card_generator import AgentCardGenerator

    config = A2AServerConfig(parac_root=str(parac_root))
    generator = AgentCardGenerator(parac_root, config)

    agents = generator.get_available_agents()

    if output_format == "json":
        import json

        console.print(json.dumps({"agents": agents}))
    else:
        table = Table(title="Local Paracle Agents")
        table.add_column("Agent ID", style="cyan")
        table.add_column("Status", style="green")

        for agent_id in agents:
            table.add_row(agent_id, "available")

        console.print(table)


async def _list_remote_agents(url: str, output_format: str) -> None:
    """List agents from remote server."""
    from paracle_a2a.client import AgentDiscovery

    discovery = AgentDiscovery()

    try:
        cards = await discovery.discover_agents(url)

        if output_format == "json":
            import json

            agents = [
                {
                    "id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "url": c.url,
                }
                for c in cards
            ]
            console.print(json.dumps({"agents": agents}))
        else:
            table = Table(title=f"A2A Agents at {url}")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Description")

            for card in cards:
                table.add_row(
                    card.id or "N/A",
                    card.name,
                    (
                        (card.description[:50] + "...")
                        if len(card.description) > 50
                        else card.description
                    ),
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error discovering agents:[/red] {e}")
        raise SystemExit(1)


@agents_group.command("discover")
@click.argument("url")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
def discover_agent(url: str, output_format: str) -> None:
    """Discover an A2A agent and display its capabilities.

    Example:
        paracle a2a agents discover http://example.com/a2a/agents/helper
    """
    asyncio.run(_discover_agent(url, output_format))


async def _discover_agent(url: str, output_format: str) -> None:
    """Discover agent and display info."""
    from paracle_a2a.client import AgentDiscovery

    discovery = AgentDiscovery()

    try:
        card = await discovery.discover(url)

        if output_format == "json":
            import json

            console.print(json.dumps(card.to_well_known(), indent=2))
        elif output_format == "yaml":
            import yaml

            console.print(yaml.dump(card.to_well_known(), default_flow_style=False))
        else:
            console.print(f"[bold cyan]Agent: {card.name}[/bold cyan]")
            console.print(f"ID: {card.id or 'N/A'}")
            console.print(f"URL: {card.url}")
            console.print(f"Version: {card.version or 'N/A'}")
            console.print(f"Description: {card.description}")
            console.print()

            if card.capabilities:
                console.print("[bold]Capabilities:[/bold]")
                console.print(f"  Streaming: {card.capabilities.streaming}")
                console.print(
                    f"  Push notifications: {card.capabilities.push_notifications}"
                )
                console.print()

            if card.skills:
                console.print("[bold]Skills:[/bold]")
                for skill in card.skills:
                    console.print(
                        f"  - {skill.name}: {skill.description or 'No description'}"
                    )

    except Exception as e:
        console.print(f"[red]Error discovering agent:[/red] {e}")
        raise SystemExit(1)


# =============================================================================
# INVOKE COMMAND
# =============================================================================


@a2a.command("invoke")
@click.argument("url")
@click.argument("message")
@click.option(
    "--context",
    "-c",
    "context_id",
    help="Context ID for conversation continuity",
)
@click.option(
    "--stream",
    is_flag=True,
    help="Stream responses (SSE)",
)
@click.option(
    "--timeout",
    "-t",
    default=60,
    type=int,
    help="Timeout in seconds",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def invoke(
    url: str,
    message: str,
    context_id: str | None,
    stream: bool,
    timeout: int,
    output_format: str,
) -> None:
    """Invoke an A2A agent with a message.

    Example:
        paracle a2a invoke http://example.com/a2a/agents/coder "Write a hello world"
        paracle a2a invoke http://example.com/a2a/agents/coder "Continue" --context ctx123
    """
    asyncio.run(_invoke_agent(url, message, context_id, stream, timeout, output_format))


async def _invoke_agent(
    url: str,
    message: str,
    context_id: str | None,
    stream: bool,
    timeout: int,
    output_format: str,
) -> None:
    """Invoke agent."""
    from paracle_a2a.client import ParacleA2AClient
    from paracle_a2a.config import A2AClientConfig

    config = A2AClientConfig(timeout_seconds=float(timeout))
    client = ParacleA2AClient(url, config)

    try:
        if stream:
            console.print(f"[dim]Invoking {url} with streaming...[/dim]")
            console.print()

            async for event in client.invoke_streaming(
                message=message,
                context_id=context_id,
            ):
                if output_format == "json":
                    import json

                    console.print(json.dumps(event.model_dump(by_alias=True)))
                else:
                    from paracle_a2a.models import (
                        TaskArtifactUpdateEvent,
                        TaskStatusUpdateEvent,
                    )

                    if isinstance(event, TaskStatusUpdateEvent):
                        console.print(
                            f"[cyan]Status:[/cyan] {event.status.state.value}"
                        )
                        if event.status.message:
                            console.print(f"  {event.status.message}")
                    elif isinstance(event, TaskArtifactUpdateEvent):
                        for part in event.artifact.parts:
                            if hasattr(part, "text"):
                                console.print(part.text, end="")

            console.print()
        else:
            console.print(f"[dim]Invoking {url}...[/dim]")

            task = await client.invoke(
                message=message,
                context_id=context_id,
                wait=True,
            )

            if output_format == "json":
                import json

                console.print(json.dumps(task.model_dump(by_alias=True), indent=2))
            else:
                console.print()
                console.print(f"[bold]Task ID:[/bold] {task.id}")
                console.print(f"[bold]Status:[/bold] {task.status.state.value}")
                if task.context_id:
                    console.print(f"[bold]Context ID:[/bold] {task.context_id}")
                if task.status.message:
                    console.print()
                    console.print(task.status.message)

    except Exception as e:
        console.print(f"[red]Error invoking agent:[/red] {e}")
        raise SystemExit(1)


# =============================================================================
# STATUS COMMAND
# =============================================================================


@a2a.command("status")
@click.argument("task_id")
@click.option(
    "--url",
    "-u",
    required=True,
    help="A2A server URL",
)
@click.option(
    "--watch",
    "-w",
    is_flag=True,
    help="Watch for updates",
)
@click.option(
    "--interval",
    default=2,
    type=int,
    help="Watch interval in seconds",
)
def status(
    task_id: str,
    url: str,
    watch: bool,
    interval: int,
) -> None:
    """Check status of an A2A task.

    Example:
        paracle a2a status 01HXYZ... --url http://example.com/a2a/agents/coder
        paracle a2a status 01HXYZ... --url http://example.com/a2a/agents/coder --watch
    """
    asyncio.run(_check_status(task_id, url, watch, interval))


async def _check_status(
    task_id: str,
    url: str,
    watch: bool,
    interval: int,
) -> None:
    """Check task status."""
    from paracle_a2a.client import ParacleA2AClient

    client = ParacleA2AClient(url)

    try:

        while True:
            task = await client.get_task(task_id)

            # Clear and redraw if watching
            if watch:
                console.clear()

            console.print(f"[bold]Task:[/bold] {task.id}")
            console.print(f"[bold]Status:[/bold] {task.status.state.value}")
            if task.status.message:
                console.print(f"[bold]Message:[/bold] {task.status.message}")
            if task.status.progress is not None:
                console.print(
                    f"[bold]Progress:[/bold] {task.status.progress * 100:.1f}%"
                )
            if task.context_id:
                console.print(f"[bold]Context:[/bold] {task.context_id}")

            if not watch or task.is_terminal():
                break

            console.print(f"\n[dim]Refreshing in {interval}s... (Ctrl+C to stop)[/dim]")
            await asyncio.sleep(interval)

    except KeyboardInterrupt:
        console.print("\n[dim]Stopped watching[/dim]")
    except Exception as e:
        console.print(f"[red]Error checking status:[/red] {e}")
        raise SystemExit(1)
