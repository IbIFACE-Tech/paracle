"""CLI commands for agent group management.

Commands:
- list: List all agent groups
- create: Create a new agent group
- get: Get details of a specific group
- delete: Delete a group
- sessions: List/manage group sessions
"""

import asyncio
import json

import click
from rich.console import Console
from rich.table import Table

console = Console()

# Default database path
DEFAULT_DB_PATH = ".parac/memory/data/agent_comm.db"


def get_store(db_path: str | None = None):
    """Get the session store.

    Args:
        db_path: Optional path to database. Uses default if not provided.
    """
    from paracle_agent_comm.persistence import SQLiteSessionStore

    path = db_path or DEFAULT_DB_PATH
    return SQLiteSessionStore(path)


def run_async(coro):
    """Run an async coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


@click.group(invoke_without_command=True)
@click.option(
    "--list", "-l", "list_flag", is_flag=True, help="List all groups (shortcut)"
)
@click.pass_context
def groups(ctx: click.Context, list_flag: bool) -> None:
    """Manage agent groups for multi-agent collaboration.

    Agent groups enable multiple agents to collaborate on tasks using
    different communication patterns: peer-to-peer, broadcast, or coordinator.

    Common commands:
        paracle groups -l              - List all groups (shortcut)
        paracle groups list            - List all groups
        paracle groups create "Team"   - Create a new group
        paracle groups sessions        - View collaboration sessions
    """
    if list_flag:
        ctx.invoke(list_groups)
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# =============================================================================
# LIST Command
# =============================================================================


@groups.command("list")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
@click.option(
    "--db",
    "db_path",
    type=click.Path(),
    help=f"Database path (default: {DEFAULT_DB_PATH})",
)
def list_groups(output_format: str = "table", db_path: str | None = None) -> None:
    """List all defined agent groups.

    Examples:
        paracle groups list
        paracle groups list --format=json
        paracle groups list --db=custom.db
    """
    try:
        store = get_store(db_path)
        groups_list = run_async(store.list_groups())
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    if not groups_list:
        console.print("[yellow]No agent groups found.[/yellow]")
        console.print(
            "Create one with: paracle groups create <name> --members=agent1,agent2"
        )
        return

    if output_format == "json":
        data = [
            {
                "id": g.id,
                "name": g.name,
                "members": g.members,
                "coordinator": g.coordinator,
                "pattern": g.communication_pattern.value,
                "status": g.status.value,
            }
            for g in groups_list
        ]
        console.print(json.dumps(data, indent=2))

    elif output_format == "yaml":
        import yaml

        data = [
            {
                "id": g.id,
                "name": g.name,
                "members": g.members,
                "coordinator": g.coordinator,
                "pattern": g.communication_pattern.value,
                "status": g.status.value,
            }
            for g in groups_list
        ]
        console.print(yaml.dump(data, default_flow_style=False))

    else:  # table
        table = Table(title=f"Agent Groups ({len(groups_list)})")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Members", style="bold")
        table.add_column("Pattern", style="green")
        table.add_column("Coordinator", style="yellow")
        table.add_column("Status", style="magenta")

        for g in groups_list:
            members = ", ".join(g.members[:3])
            if len(g.members) > 3:
                members += f" +{len(g.members) - 3}"

            table.add_row(
                g.name,
                members,
                g.communication_pattern.value,
                g.coordinator or "-",
                g.status.value,
            )

        console.print(table)


# =============================================================================
# CREATE Command
# =============================================================================


@groups.command("create")
@click.argument("name")
@click.option(
    "--members",
    "-m",
    required=True,
    help="Comma-separated list of agent IDs (e.g., coder,reviewer,tester)",
)
@click.option(
    "--coordinator",
    "-c",
    help="Coordinator agent ID (for coordinator pattern)",
)
@click.option(
    "--pattern",
    "-p",
    type=click.Choice(["peer-to-peer", "broadcast", "coordinator"]),
    default="peer-to-peer",
    help="Communication pattern",
)
@click.option(
    "--max-rounds",
    type=int,
    default=10,
    help="Maximum collaboration rounds (default: 10)",
)
@click.option(
    "--max-messages",
    type=int,
    default=100,
    help="Maximum messages per session (default: 100)",
)
@click.option(
    "--timeout",
    type=float,
    default=300.0,
    help="Session timeout in seconds (default: 300)",
)
@click.option(
    "--description",
    "-d",
    help="Group description",
)
@click.option(
    "--db",
    "db_path",
    type=click.Path(),
    help=f"Database path (default: {DEFAULT_DB_PATH})",
)
def create_group(
    name: str,
    members: str,
    coordinator: str | None,
    pattern: str,
    max_rounds: int,
    max_messages: int,
    timeout: float,
    description: str | None,
    db_path: str | None,
) -> None:
    """Create a new agent group.

    Examples:
        paracle groups create "Code Review Team" -m coder,reviewer
        paracle groups create "Dev Team" -m arch,coder,tester -p coordinator -c arch
        paracle groups create "Design Team" -m designer,reviewer --max-rounds=5
    """
    from paracle_agent_comm.models import AgentGroup, CommunicationPattern

    # Parse members
    member_list = [m.strip() for m in members.split(",") if m.strip()]
    if not member_list:
        console.print("[red]Error:[/red] At least one member is required")
        raise SystemExit(1)

    # Validate coordinator
    if pattern == "coordinator" and not coordinator:
        console.print("[red]Error:[/red] Coordinator pattern requires --coordinator")
        raise SystemExit(1)

    if coordinator and coordinator not in member_list:
        console.print(
            f"[red]Error:[/red] Coordinator '{coordinator}' must be in members list"
        )
        raise SystemExit(1)

    # Create group
    try:
        group = AgentGroup(
            name=name,
            description=description,
            members=member_list,
            coordinator=coordinator,
            communication_pattern=CommunicationPattern(pattern),
            max_rounds=max_rounds,
            max_messages=max_messages,
            timeout_seconds=timeout,
        )

        store = get_store(db_path)
        run_async(store.save_group(group))

        console.print(f"[green]Created group:[/green] {name}")
        console.print(f"  ID: {group.id}")
        console.print(f"  Members: {', '.join(member_list)}")
        console.print(f"  Pattern: {pattern}")
        if coordinator:
            console.print(f"  Coordinator: {coordinator}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


# =============================================================================
# GET Command
# =============================================================================


@groups.command("get")
@click.argument("group_name_or_id")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["markdown", "json", "yaml"]),
    default="markdown",
)
@click.option(
    "--db",
    "db_path",
    type=click.Path(),
    help=f"Database path (default: {DEFAULT_DB_PATH})",
)
def get_group(
    group_name_or_id: str,
    output_format: str,
    db_path: str | None,
) -> None:
    """Get details of a specific group.

    Examples:
        paracle groups get "Code Review Team"
        paracle groups get --format=json
    """
    from paracle_agent_comm.exceptions import GroupNotFoundError

    try:
        store = get_store(db_path)

        # Try by name first, then by ID
        group = run_async(store.get_group_by_name(group_name_or_id))
        if not group:
            try:
                group = run_async(store.get_group(group_name_or_id))
            except GroupNotFoundError:
                console.print(f"[red]Error:[/red] Group '{group_name_or_id}' not found")
                raise SystemExit(1)

    except GroupNotFoundError:
        console.print(f"[red]Error:[/red] Group '{group_name_or_id}' not found")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    data = {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "members": group.members,
        "coordinator": group.coordinator,
        "communication_pattern": group.communication_pattern.value,
        "max_rounds": group.max_rounds,
        "max_messages": group.max_messages,
        "timeout_seconds": group.timeout_seconds,
        "status": group.status.value,
        "current_session_id": group.current_session_id,
        "created_at": group.created_at.isoformat(),
        "updated_at": group.updated_at.isoformat(),
    }

    if output_format == "json":
        console.print(json.dumps(data, indent=2))

    elif output_format == "yaml":
        import yaml

        console.print(yaml.dump(data, default_flow_style=False))

    else:  # markdown
        console.print(f"# {group.name}\n")
        console.print(f"**ID**: {group.id}")
        console.print(f"**Pattern**: {group.communication_pattern.value}")
        console.print(f"**Status**: {group.status.value}")
        if group.description:
            console.print(f"\n**Description**: {group.description}")
        console.print(f"\n**Members** ({len(group.members)}):")
        for member in group.members:
            marker = " (coordinator)" if member == group.coordinator else ""
            console.print(f"  - {member}{marker}")
        console.print("\n**Limits**:")
        console.print(f"  - Max rounds: {group.max_rounds}")
        console.print(f"  - Max messages: {group.max_messages}")
        console.print(f"  - Timeout: {group.timeout_seconds}s")


# =============================================================================
# DELETE Command
# =============================================================================


@groups.command("delete")
@click.argument("group_name_or_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.option(
    "--db",
    "db_path",
    type=click.Path(),
    help=f"Database path (default: {DEFAULT_DB_PATH})",
)
def delete_group(
    group_name_or_id: str,
    force: bool,
    db_path: str | None,
) -> None:
    """Delete an agent group and all its sessions.

    Examples:
        paracle groups delete "Old Team"
        paracle groups delete "Test Team" --force
    """
    from paracle_agent_comm.exceptions import GroupNotFoundError

    try:
        store = get_store(db_path)

        # Find the group
        group = run_async(store.get_group_by_name(group_name_or_id))
        if not group:
            try:
                group = run_async(store.get_group(group_name_or_id))
            except GroupNotFoundError:
                console.print(f"[red]Error:[/red] Group '{group_name_or_id}' not found")
                raise SystemExit(1)

        # Count sessions
        session_count = run_async(store.get_session_count(group.id))

        if not force:
            console.print(f"About to delete group '[cyan]{group.name}[/cyan]'")
            if session_count > 0:
                console.print(
                    f"[yellow]Warning:[/yellow] This will also delete {session_count} session(s)"
                )
            if not click.confirm("Continue?"):
                console.print("Cancelled.")
                return

        run_async(store.delete_group(group.id))
        console.print(f"[green]Deleted:[/green] {group.name}")
        if session_count > 0:
            console.print(f"  Also deleted {session_count} session(s)")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


# =============================================================================
# SESSIONS Command
# =============================================================================


@groups.command("sessions")
@click.option(
    "--group",
    "-g",
    "group_name",
    help="Filter by group name",
)
@click.option(
    "--status",
    "-s",
    type=click.Choice(["active", "completed", "failed", "timeout"]),
    help="Filter by status",
)
@click.option(
    "--limit",
    "-n",
    type=int,
    default=20,
    help="Maximum number of sessions to show",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
)
@click.option(
    "--db",
    "db_path",
    type=click.Path(),
    help=f"Database path (default: {DEFAULT_DB_PATH})",
)
def list_sessions(
    group_name: str | None,
    status: str | None,
    limit: int,
    output_format: str,
    db_path: str | None,
) -> None:
    """List collaboration sessions.

    Examples:
        paracle groups sessions
        paracle groups sessions --group="Code Review Team"
        paracle groups sessions --status=completed
        paracle groups sessions --limit=50 --format=json
    """
    from paracle_agent_comm.models import GroupSessionStatus

    try:
        store = get_store(db_path)

        # Get group ID if name provided
        group_id = None
        if group_name:
            group = run_async(store.get_group_by_name(group_name))
            if not group:
                console.print(f"[red]Error:[/red] Group '{group_name}' not found")
                raise SystemExit(1)
            group_id = group.id

        # Parse status
        status_filter = None
        if status:
            status_filter = GroupSessionStatus(status)

        sessions = run_async(
            store.list_sessions(
                group_id=group_id,
                status=status_filter,
                limit=limit,
            )
        )

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    if not sessions:
        console.print("[yellow]No sessions found.[/yellow]")
        return

    if output_format == "json":
        data = [
            {
                "id": s.id,
                "group_id": s.group_id,
                "goal": s.goal,
                "status": s.status.value,
                "rounds": s.round_count,
                "messages": len(s.messages),
                "started_at": s.started_at.isoformat(),
                "ended_at": s.ended_at.isoformat() if s.ended_at else None,
                "outcome": s.outcome,
            }
            for s in sessions
        ]
        console.print(json.dumps(data, indent=2))

    else:  # table
        table = Table(title=f"Sessions ({len(sessions)})")
        table.add_column("ID", style="dim", no_wrap=True)
        table.add_column("Goal", style="cyan", max_width=30)
        table.add_column("Status", style="bold")
        table.add_column("Rounds", justify="right")
        table.add_column("Messages", justify="right")
        table.add_column("Started", style="dim")

        for s in sessions:
            status_style = {
                "active": "green",
                "completed": "blue",
                "failed": "red",
                "timeout": "yellow",
            }.get(s.status.value, "white")

            goal_short = s.goal[:27] + "..." if len(s.goal) > 30 else s.goal

            table.add_row(
                s.id[:8],
                goal_short,
                f"[{status_style}]{s.status.value}[/{status_style}]",
                str(s.round_count),
                str(len(s.messages)),
                s.started_at.strftime("%Y-%m-%d %H:%M"),
            )

        console.print(table)


# =============================================================================
# SESSION Command (single session details)
# =============================================================================


@groups.command("session")
@click.argument("session_id")
@click.option(
    "--messages",
    "-m",
    is_flag=True,
    help="Show message history",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["markdown", "json"]),
    default="markdown",
)
@click.option(
    "--db",
    "db_path",
    type=click.Path(),
    help=f"Database path (default: {DEFAULT_DB_PATH})",
)
def get_session(
    session_id: str,
    messages: bool,
    output_format: str,
    db_path: str | None,
) -> None:
    """Get details of a specific session.

    Examples:
        paracle groups session abc123
        paracle groups session abc123 --messages
        paracle groups session abc123 --format=json
    """
    from paracle_agent_comm.exceptions import SessionNotFoundError

    try:
        store = get_store(db_path)
        session = run_async(store.get_session(session_id))
    except SessionNotFoundError:
        console.print(f"[red]Error:[/red] Session '{session_id}' not found")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    if output_format == "json":
        data = {
            "id": session.id,
            "group_id": session.group_id,
            "goal": session.goal,
            "status": session.status.value,
            "round_count": session.round_count,
            "shared_context": session.shared_context,
            "outcome": session.outcome,
            "started_at": session.started_at.isoformat(),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "total_tokens": session.total_tokens,
            "estimated_cost": session.estimated_cost,
        }
        if messages:
            data["messages"] = [
                {
                    "id": m.id,
                    "sender": m.sender,
                    "type": m.message_type.value,
                    "content": m.get_text_content(),
                    "timestamp": m.timestamp.isoformat(),
                }
                for m in session.messages
            ]
        console.print(json.dumps(data, indent=2))

    else:  # markdown
        console.print(f"# Session: {session.id[:12]}...\n")
        console.print(f"**Goal**: {session.goal}")
        console.print(f"**Status**: {session.status.value}")
        console.print(f"**Rounds**: {session.round_count}")
        console.print(f"**Messages**: {len(session.messages)}")
        if session.outcome:
            console.print(f"**Outcome**: {session.outcome}")
        console.print(f"\n**Started**: {session.started_at}")
        if session.ended_at:
            console.print(f"**Ended**: {session.ended_at}")

        if messages and session.messages:
            console.print("\n## Message History\n")
            for i, msg in enumerate(session.messages):
                sender_style = "cyan" if msg.sender != "system" else "dim"
                console.print(
                    f"[{sender_style}]{msg.sender}[/{sender_style}] "
                    f"([dim]{msg.message_type.value}[/dim]):"
                )
                console.print(f"  {msg.get_text_content()}\n")
