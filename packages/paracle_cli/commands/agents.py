"""CLI commands for agent management.

Commands:
- list: List all agents
- get: Get specific agent details
- export: Export agents to various formats

Architecture: CLI -> API -> Core (API-first design)
Falls back to direct core access if API is unavailable.
"""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from paracle_cli.api_client import APIClient, APIError, get_client
from paracle_cli.commands.agent_run import run as _agent_run_cmd
from paracle_cli.commands.skills import skills as skills_group
from paracle_cli.utils import get_parac_root_or_exit

console = Console()


def get_api_client() -> APIClient | None:
    """Get API client if API is available.

    Returns:
        APIClient if API responds, None otherwise
    """
    client = get_client()
    if client.is_available():
        return client
    return None


def use_api_or_fallback(api_func, fallback_func, *args, **kwargs):
    """Try API first, fall back to direct core access.

    Args:
        api_func: Function to call via API
        fallback_func: Function to call directly if API unavailable
        *args, **kwargs: Arguments to pass

    Returns:
        Result from either function
    """
    client = get_api_client()
    if client:
        try:
            return api_func(client, *args, **kwargs)
        except APIError as e:
            if e.status_code == 404:
                # .parac/ not found - let fallback handle gracefully
                pass
            else:
                console.print(f"[yellow]API error:[/yellow] {e.detail}")
                console.print("[dim]Falling back to direct access...[/dim]")
        except Exception as e:
            console.print(f"[yellow]API unavailable:[/yellow] {e}")
            console.print("[dim]Falling back to direct access...[/dim]")

    return fallback_func(*args, **kwargs)


@click.group(invoke_without_command=True)
@click.option(
    "--list",
    "-l",
    "list_flag",
    is_flag=True,
    help="List all agents (shortcut for 'list')",
)
@click.pass_context
def agents(ctx: click.Context, list_flag: bool) -> None:
    """Manage, discover, and run agents.

    Agents are AI-powered specialists defined in .parac/agents/ that can
    execute tasks like code review, testing, documentation, and more.

    Common commands:
        paracle agents -l                - List all agents (shortcut)
        paracle agents list              - List all available agents
        paracle agents run coder -t "Fix bug"  - Run an agent with a task
        paracle agents skills -l         - List all available skills
    """
    if list_flag:
        ctx.invoke(list_agents, output_format="table",
                   remote=False, remote_only=False)
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# =============================================================================
# LIST Command
# =============================================================================


def _list_via_api(client: APIClient, output_format: str) -> None:
    """List agents via API."""
    result = client.agents_list()
    agents_list = result.get("agents", [])

    if not agents_list:
        console.print(
            "[yellow]No agents found in .parac/agents/specs/[/yellow]")
        return

    if output_format == "json":
        import json

        console.print(json.dumps(agents_list, indent=2))

    elif output_format == "yaml":
        import yaml

        console.print(
            yaml.dump(agents_list, default_flow_style=False, sort_keys=False))

    else:  # table
        table = Table(title=f"Agents ({len(agents_list)} found)")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="bold")
        table.add_column("Role", style="green")
        table.add_column("Capabilities", style="yellow")

        for agent in agents_list:
            capabilities = ", ".join(agent.get("capabilities", [])[:3])
            if len(agent.get("capabilities", [])) > 3:
                capabilities += f" +{len(agent['capabilities']) - 3} more"

            table.add_row(
                agent.get("id", ""),
                agent.get("name", ""),
                agent.get("role", ""),
                capabilities,
            )

        console.print(table)


def _list_direct(output_format: str) -> None:
    """List agents via direct core access."""
    parac_root = get_parac_root_or_exit()
    manifest_path = parac_root / "agents" / "manifest.yaml"

    if not manifest_path.exists():
        console.print("[yellow]No agents manifest found[/yellow]")
        console.print("Expected: .parac/agents/manifest.yaml")
        return

    # Load agents from manifest
    import yaml

    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        console.print(f"[red]Error loading manifest:[/red] {e}")
        return

    agents_data = manifest.get("agents", [])
    if not agents_data:
        console.print("[yellow]No agents defined in manifest[/yellow]")
        return

    agents_list = []
    for agent in agents_data:
        agents_list.append(
            {
                "id": agent.get("id", ""),
                "name": agent.get("name", ""),
                "role": agent.get("role", ""),
                "description": agent.get("description", ""),
                "capabilities": agent.get("responsibilities", [])[:5],
                "tools": agent.get("tools", []),
            }
        )

    if output_format == "json":
        import json

        console.print(json.dumps(agents_list, indent=2))

    elif output_format == "yaml":
        console.print(
            yaml.dump(agents_list, default_flow_style=False, sort_keys=False))

    else:  # table
        table = Table(title=f"Agents ({len(agents_list)} found)")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="bold")
        table.add_column("Role", style="green")
        table.add_column("Capabilities", style="yellow")

        for agent in agents_list:
            capabilities = ", ".join(agent.get("capabilities", [])[:3])
            if len(agent.get("capabilities", [])) > 3:
                capabilities += f" +{len(agent['capabilities']) - 3} more"

            table.add_row(
                agent.get("id", ""),
                agent.get("name", ""),
                agent.get("role", ""),
                capabilities,
            )

        console.print(table)


def _list_remote_agents(output_format: str) -> None:
    """List remote A2A agents from registry."""
    try:
        from paracle_a2a.registry import get_remote_registry
    except ImportError:
        console.print(
            "[dim]Remote A2A agents not available " "(install paracle[a2a])[/dim]"
        )
        return

    registry = get_remote_registry()
    remote_agents = registry.list_all()

    if not remote_agents:
        console.print("[dim]No remote A2A agents defined in manifest[/dim]")
        console.print(
            "[dim]Add remote_agents section to " ".parac/agents/manifest.yaml[/dim]"
        )
        return

    if output_format == "json":
        import json

        agents_data = [
            {
                "id": f"remote:{a.id}",
                "name": a.name,
                "url": a.url,
                "description": a.description,
                "auth_type": a.auth_type,
                "type": "remote_a2a",
            }
            for a in remote_agents
        ]
        console.print(json.dumps(agents_data, indent=2))

    elif output_format == "yaml":
        import yaml

        agents_data = [
            {
                "id": f"remote:{a.id}",
                "name": a.name,
                "url": a.url,
                "description": a.description,
                "auth_type": a.auth_type,
                "type": "remote_a2a",
            }
            for a in remote_agents
        ]
        console.print(
            yaml.dump(agents_data, default_flow_style=False, sort_keys=False))

    else:  # table
        table = Table(title=f"Remote A2A Agents ({len(remote_agents)} found)")
        table.add_column("ID", style="magenta", no_wrap=True)
        table.add_column("Name", style="bold")
        table.add_column("Endpoint", style="cyan")
        table.add_column("Auth", style="yellow")

        for agent in remote_agents:
            table.add_row(
                f"remote:{agent.id}",
                agent.name,
                agent.url[:40] + "..." if len(agent.url) > 40 else agent.url,
                agent.auth_type or "none",
            )

        console.print(table)


@agents.command("list")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
)
@click.option(
    "--remote",
    is_flag=True,
    help="Include remote A2A agents defined in manifest",
)
@click.option(
    "--remote-only",
    is_flag=True,
    help="Show only remote A2A agents",
)
def list_agents(output_format: str, remote: bool, remote_only: bool) -> None:
    """List all agents defined in .parac/agents/specs/.

    Examples:
        paracle agents list
        paracle agents list --format=json
        paracle agents list --remote          # Include remote A2A agents
        paracle agents list --remote-only     # Show only remote agents
        paracle agents list --format=yaml
    """
    if remote_only:
        _list_remote_agents(output_format)
    elif remote:
        use_api_or_fallback(_list_via_api, _list_direct, output_format)
        console.print()  # Separator
        _list_remote_agents(output_format)
    else:
        use_api_or_fallback(_list_via_api, _list_direct, output_format)


# =============================================================================
# GET Command
# =============================================================================


def _get_via_api(
    client: APIClient,
    agent_id: str,
    output_format: str,
    spec: bool,
) -> None:
    """Get agent via API."""
    if spec:
        # Get full specification
        result = client.agents_get_spec(agent_id)
        console.print(result.get("content", ""))
        return

    # Get metadata
    agent = client.agents_get(agent_id)

    if output_format == "json":
        import json

        console.print(json.dumps(agent, indent=2))

    elif output_format == "yaml":
        import yaml

        console.print(
            yaml.dump(agent, default_flow_style=False, sort_keys=False))

    else:  # markdown
        console.print(f"# {agent.get('name', agent_id)}\n")
        console.print(f"**ID**: {agent.get('id', '')}")
        console.print(f"**Role**: {agent.get('role', '')}")
        console.print(f"**Spec File**: {agent.get('spec_file', '')}")
        console.print(f"\n**Description**: {agent.get('description', '')}\n")

        if agent.get("capabilities"):
            console.print("**Capabilities**:")
            for cap in agent["capabilities"]:
                console.print(f"  - {cap}")


def _get_direct(agent_id: str, output_format: str, spec: bool) -> None:
    """Get agent via direct core access."""
    parac_root = get_parac_root_or_exit()
    specs_dir = parac_root / "agents" / "specs"

    # Find the agent spec file
    spec_file = specs_dir / f"{agent_id}.yaml"
    if not spec_file.exists():
        # Try to find by ID in files
        found = False
        for f in specs_dir.glob("*.yaml"):
            import yaml

            try:
                content = yaml.safe_load(f.read_text(encoding="utf-8"))
                if content and content.get("id") == agent_id:
                    spec_file = f
                    found = True
                    break
            except Exception:
                continue

        if not found:
            console.print(f"[red]Error:[/red] Agent '{agent_id}' not found")
            raise SystemExit(1)

    import yaml

    if spec:
        # Show raw file content
        console.print(spec_file.read_text(encoding="utf-8"))
        return

    # Parse and display
    try:
        content = yaml.safe_load(spec_file.read_text(encoding="utf-8"))
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to parse spec: {e}")
        raise SystemExit(1)

    agent = {
        "id": content.get("id", spec_file.stem),
        "name": content.get("name", spec_file.stem),
        "role": content.get("role", ""),
        "description": content.get("description", ""),
        "capabilities": content.get("capabilities", []),
        "spec_file": str(spec_file.relative_to(parac_root.parent)),
    }

    if output_format == "json":
        import json

        console.print(json.dumps(agent, indent=2))

    elif output_format == "yaml":
        console.print(
            yaml.dump(agent, default_flow_style=False, sort_keys=False))

    else:  # markdown
        console.print(f"# {agent['name']}\n")
        console.print(f"**ID**: {agent['id']}")
        console.print(f"**Role**: {agent['role']}")
        console.print(f"**Spec File**: {agent['spec_file']}")
        console.print(f"\n**Description**: {agent['description']}\n")

        if agent["capabilities"]:
            console.print("**Capabilities**:")
            for cap in agent["capabilities"]:
                console.print(f"  - {cap}")


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
    use_api_or_fallback(_get_via_api, _get_direct,
                        agent_id, output_format, spec)


# =============================================================================
# EXPORT Command
# =============================================================================


def _export_via_api(
    client: APIClient,
    output_format: str,
    output: str | None,
) -> None:
    """Export agents via API."""
    result = client.agents_list()
    agents_list = result.get("agents", [])

    if output_format == "json":
        import json

        content = json.dumps(agents_list, indent=2)
    else:  # yaml
        import yaml

        content = yaml.dump(
            agents_list, default_flow_style=False, sort_keys=False)

    if output:
        Path(output).write_text(content, encoding="utf-8")
        console.print(
            f"[green]OK[/green] Exported {len(agents_list)} agents to {output}"
        )
    else:
        console.print(content)


def _export_direct(output_format: str, output: str | None) -> None:
    """Export agents via direct core access."""
    parac_root = get_parac_root_or_exit()
    specs_dir = parac_root / "agents" / "specs"

    import yaml

    agents_list = []
    if specs_dir.exists():
        for spec_file in specs_dir.glob("*.yaml"):
            try:
                content = yaml.safe_load(spec_file.read_text(encoding="utf-8"))
                if content:
                    agents_list.append(
                        {
                            "id": content.get("id", spec_file.stem),
                            "name": content.get("name", spec_file.stem),
                            "role": content.get("role", ""),
                            "description": content.get("description", ""),
                            "capabilities": content.get("capabilities", []),
                            "spec_file": str(spec_file.relative_to(parac_root.parent)),
                        }
                    )
            except Exception:
                continue

    if output_format == "json":
        import json

        content = json.dumps(agents_list, indent=2)
    else:  # yaml
        content = yaml.dump(
            agents_list, default_flow_style=False, sort_keys=False)

    if output:
        Path(output).write_text(content, encoding="utf-8")
        console.print(
            f"[green]OK[/green] Exported {len(agents_list)} agents to {output}"
        )
    else:
        console.print(content)


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
    use_api_or_fallback(_export_via_api, _export_direct, output_format, output)


# =============================================================================
# VALIDATE Command - Validate agent specifications
# =============================================================================


@agents.command("validate")
@click.argument("agent_id", required=False)
@click.option(
    "--strict",
    is_flag=True,
    help="Treat warnings as errors",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
)
def validate_agents(
    agent_id: str | None,
    strict: bool,
    output_format: str,
) -> None:
    """Validate agent specifications against schema.

    Checks that agent specs have required sections and .parac/ references.

    Examples:
        paracle agents validate           # Validate all agents
        paracle agents validate coder     # Validate specific agent
        paracle agents validate --strict  # Treat warnings as errors
    """
    from paracle_core.agents.validator import AgentSpecValidator

    parac_root = get_parac_root_or_exit()
    specs_dir = parac_root / "agents" / "specs"

    if not specs_dir.exists():
        console.print(
            f"[red]Error:[/red] Specs directory not found: {specs_dir}")
        raise SystemExit(1)

    validator = AgentSpecValidator(strict=strict)

    if agent_id:
        # Validate single agent
        spec_file = specs_dir / f"{agent_id}.md"
        if not spec_file.exists():
            console.print(
                f"[red]Error:[/red] Agent spec not found: {spec_file}")
            raise SystemExit(1)

        result = validator.validate_file(spec_file)
        results = {agent_id: result}
    else:
        # Validate all agents
        results = validator.validate_directory(specs_dir)

    if output_format == "json":
        import json

        json_results = {
            agent_id: {
                "valid": r.valid,
                "errors": r.error_count,
                "warnings": r.warning_count,
                "messages": [str(e) for e in r.errors],
            }
            for agent_id, r in results.items()
        }
        console.print(json.dumps(json_results, indent=2))
    else:
        # Text output
        all_valid = True
        for agent_id, result in results.items():
            if result.valid:
                console.print(f"[green]OK[/green] {agent_id}")
            else:
                all_valid = False
                console.print(f"[red]INVALID[/red] {agent_id}")
                for error in result.errors:
                    severity_color = {
                        "error": "red",
                        "warning": "yellow",
                        "info": "blue",
                    }.get(error.severity.value, "white")
                    console.print(
                        f"  [{severity_color}]{error.severity.value.upper()}[/{severity_color}]: "
                        f"{error.message}"
                    )
                    if error.suggestion:
                        console.print(
                            f"    [dim]Suggestion: {error.suggestion}[/dim]")

        console.print()
        valid_count = sum(1 for r in results.values() if r.valid)
        console.print(
            f"Validated {len(results)} agent(s): "
            f"[green]{valid_count} valid[/green], "
            f"[red]{len(results) - valid_count} invalid[/red]"
        )

        if not all_valid:
            console.print(
                "\n[dim]Run 'paracle agents format' to auto-fix common issues[/dim]"
            )
            raise SystemExit(1)


# =============================================================================
# FORMAT Command - Auto-fix agent specifications
# =============================================================================


@agents.command("format")
@click.argument("agent_id", required=False)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be changed without modifying files",
)
@click.option(
    "--check",
    is_flag=True,
    help="Check if files need formatting (exit 1 if yes)",
)
def format_agents(
    agent_id: str | None,
    dry_run: bool,
    check: bool,
) -> None:
    """Auto-fix common issues in agent specifications.

    Adds missing sections, normalizes structure, and ensures .parac/
    governance references are present.

    Examples:
        paracle agents format           # Format all agents
        paracle agents format coder     # Format specific agent
        paracle agents format --dry-run # Show changes without applying
        paracle agents format --check   # Check if formatting needed
    """
    from paracle_core.agents.formatter import AgentSpecFormatter

    parac_root = get_parac_root_or_exit()
    specs_dir = parac_root / "agents" / "specs"

    if not specs_dir.exists():
        console.print(
            f"[red]Error:[/red] Specs directory not found: {specs_dir}")
        raise SystemExit(1)

    formatter = AgentSpecFormatter()

    if agent_id:
        # Format single agent
        spec_file = specs_dir / f"{agent_id}.md"
        if not spec_file.exists():
            console.print(
                f"[red]Error:[/red] Agent spec not found: {spec_file}")
            raise SystemExit(1)

        _, result, modified = formatter.format_file(
            spec_file, fix=not check, dry_run=dry_run or check
        )
        results = {agent_id: (result, modified)}
    else:
        # Format all agents
        results = formatter.format_directory(
            specs_dir, fix=not check, dry_run=dry_run or check
        )

    # Report results
    modified_count = sum(1 for _, (_, m) in results.items() if m)
    valid_count = sum(1 for _, (r, _) in results.items() if r.valid)

    for agent_id, (result, modified) in results.items():
        if modified:
            if dry_run or check:
                console.print(f"[yellow]WOULD MODIFY[/yellow] {agent_id}")
            else:
                console.print(f"[green]FORMATTED[/green] {agent_id}")
        elif result.valid:
            console.print(f"[dim]OK[/dim] {agent_id}")
        else:
            console.print(f"[red]NEEDS MANUAL FIX[/red] {agent_id}")
            for error in result.errors:
                if error.severity.value == "error":
                    console.print(f"  [red]ERROR[/red]: {error.message}")

    console.print()
    if dry_run or check:
        console.print(
            f"Would modify {modified_count} of {len(results)} agent(s)")
        if check and modified_count > 0:
            raise SystemExit(1)
    else:
        console.print(
            f"Formatted {modified_count} of {len(results)} agent(s), "
            f"{valid_count} now valid"
        )


# =============================================================================
# CREATE Command - Create new agent from template
# =============================================================================


@agents.command("create")
@click.argument("agent_id")
@click.option(
    "--role",
    "-r",
    required=True,
    help="Description of what the agent does",
)
@click.option(
    "--name",
    "-n",
    help="Human-readable name (defaults to title-cased ID)",
)
@click.option(
    "--ai-enhance",
    is_flag=True,
    help="Use AI to enhance the agent specification",
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
    help="Overwrite existing agent spec",
)
def create_agent(
    agent_id: str,
    role: str,
    name: str | None,
    ai_enhance: bool,
    ai_provider: str,
    force: bool,
) -> None:
    """Create a new agent from template, optionally AI-enhanced.

    Creates a new agent specification in .parac/agents/specs/ with all
    required sections pre-filled, including governance integration.

    With --ai-enhance, uses AI to generate detailed capabilities,
    responsibilities, and skill suggestions based on the role description.

    Examples:
        # Basic template
        paracle agents create my-agent --role "Handles API testing"

        # AI-enhanced (requires AI provider)
        paracle agents create reviewer --role "Code review" --ai-enhance

        # With specific AI provider
        paracle agents create tester --role "Test automation" \\
            --ai-enhance --ai-provider openai

    After creating, you should:
        1. Edit .parac/agents/specs/<agent_id>.md
        2. Fill in skills from .parac/agents/SKILL_ASSIGNMENTS.md
        3. Add responsibilities
        4. Run 'paracle agents validate <agent_id>'
    """
    import asyncio
    import re

    from paracle_core.agents.template import AgentTemplate

    parac_root = get_parac_root_or_exit()
    specs_dir = parac_root / "agents" / "specs"
    spec_file = specs_dir / f"{agent_id}.md"

    # Check agent_id format
    if not re.match(r"^[a-z][a-z0-9-]*$", agent_id):
        console.print(
            "[red]Error:[/red] Agent ID must be lowercase, "
            "start with a letter, and contain only letters, numbers, hyphens"
        )
        raise SystemExit(1)

    # Check if exists
    if spec_file.exists() and not force:
        console.print(
            f"[red]Error:[/red] Agent spec already exists: {spec_file}")
        console.print("Use --force to overwrite")
        raise SystemExit(1)

    # AI enhancement if requested
    if ai_enhance:
        from paracle_cli.ai_helper import get_ai_provider

        # Get AI provider
        if ai_provider == "auto":
            ai = get_ai_provider()
        else:
            ai = get_ai_provider(ai_provider)

        if ai is None:
            console.print("[yellow]⚠ AI not available[/yellow]")
            if not click.confirm("Create basic template instead?", default=True):
                console.print("\n[cyan]To enable AI enhancement:[/cyan]")
                console.print("  pip install paracle[meta]  # Recommended")
                console.print("  pip install paracle[openai]  # Or external")
                raise SystemExit(1)
            ai_enhance = False  # Fall back to basic template
        else:
            console.print(f"[dim]Using AI provider: {ai.name}[/dim]")
            console.print(f"[dim]Generating enhanced spec for: {role}[/dim]\n")

            with console.status("[bold cyan]Generating agent spec..."):
                result = asyncio.run(
                    ai.generate_agent(
                        f"Agent ID: {agent_id}\nRole: {role}\n"
                        f"Name: {name or agent_id.replace('-', ' ').title()}"
                    )
                )

            # Use AI-generated content
            content = result["yaml"]
            console.print("[green]✓[/green] AI-enhanced agent spec generated")

    # Create from template (if not AI-enhanced)
    if not ai_enhance:
        template = AgentTemplate.create_for_agent(
            agent_id=agent_id,
            agent_name=name,
            agent_role=role,
        )
        content = template.render()

    # Ensure directory exists
    specs_dir.mkdir(parents=True, exist_ok=True)

    # Write file
    spec_file.write_text(content, encoding="utf-8")

    console.print(f"[green]OK[/green] Created agent spec: {spec_file}")
    console.print()
    console.print("Next steps:")
    console.print(f"  1. Edit {spec_file.relative_to(parac_root.parent)}")
    console.print("  2. Review .parac/agents/SKILL_ASSIGNMENTS.md")
    console.print("  3. Add responsibilities")
    console.print(f"  4. Run: paracle agents validate {agent_id}")
    console.print()
    console.print(
        "[dim]See .parac/agents/specs/SCHEMA.md for required sections[/dim]")
    console.print(
        "[dim]See .parac/agents/specs/TEMPLATE.md for examples[/dim]")


# =============================================================================
# RUN Command - Execute an agent for a task
# =============================================================================

# Add the run command from agent_run module to agents group
agents.add_command(_agent_run_cmd, name="run")

# =============================================================================
# INSPECT Command - Detailed agent inspection
# =============================================================================


@agents.command("inspect")
@click.argument("agent_id")
@click.option("--format", type=click.Choice(["rich", "json", "yaml"]), default="rich")
@click.option("--show-system-prompt", is_flag=True, help="Include full system prompt")
@click.option("--show-tools", is_flag=True, help="Show available tools in detail")
@click.option("--show-skills", is_flag=True, help="Show assigned skills in detail")
def inspect_agent(
    agent_id: str,
    format: str,
    show_system_prompt: bool,
    show_tools: bool,
    show_skills: bool,
) -> None:
    """Inspect agent configuration in detail.

    Provides comprehensive view of agent spec including:
    - Basic information (name, role, description)
    - Model configuration (model, temperature, max_tokens)
    - Capabilities and tools
    - Assigned skills
    - Inheritance chain
    - System prompt (optional)

    Examples:
        paracle agents inspect coder
        paracle agents inspect coder --show-system-prompt
        paracle agents inspect architect --format=json
        paracle agents inspect tester --show-tools --show-skills
    """
    from paracle_core.registry import AgentRegistry

    parac_root = get_parac_root_or_exit()

    try:
        registry = AgentRegistry(parac_root)
        agent = registry.get_agent(agent_id)

        if not agent:
            console.print(f"[red]Error:[/red] Agent '{agent_id}' not found")
            console.print("[dim]Available agents:[/dim]")
            for avail in registry.list_agents():
                console.print(f"  • {avail}")
            raise click.exceptions.Exit(1)

        if format == "json":
            import json

            data = agent.model_dump(mode="json")
            if not show_system_prompt:
                data.pop("system_prompt", None)
            console.print(json.dumps(data, indent=2))

        elif format == "yaml":
            import yaml

            data = agent.model_dump(mode="json")
            if not show_system_prompt:
                data.pop("system_prompt", None)
            console.print(
                yaml.dump(data, default_flow_style=False, sort_keys=False))

        else:  # rich format
            from rich.panel import Panel
            from rich.syntax import Syntax
            from rich.tree import Tree

            # Main info panel
            info = f"""[bold cyan]Name:[/bold cyan] {agent.name}
[bold cyan]Role:[/bold cyan] {agent.role or 'Not specified'}
[bold cyan]Description:[/bold cyan] {agent.description or 'No description'}

[bold yellow]Model Configuration:[/bold yellow]
  • Model: {agent.model}
  • Temperature: {agent.temperature}
  • Max Tokens: {agent.max_tokens or 'default'}

[bold green]Capabilities:[/bold green]
  {', '.join(agent.capabilities) if agent.capabilities else 'None'}"""

            console.print(
                Panel(info, title=f"Agent: {agent_id}", border_style="cyan"))

            # Tools
            if agent.tools or show_tools:
                tools_tree = Tree("[bold magenta]Tools[/bold magenta]")
                if agent.tools:
                    for tool in agent.tools:
                        tools_tree.add(f"[cyan]{tool}[/cyan]")
                else:
                    tools_tree.add("[dim]No tools configured[/dim]")
                console.print(tools_tree)
                console.print()

            # Skills
            if agent.skills or show_skills:
                skills_tree = Tree("[bold blue]Skills[/bold blue]")
                if agent.skills:
                    for skill in agent.skills:
                        skills_tree.add(f"[blue]{skill}[/blue]")
                else:
                    skills_tree.add("[dim]No skills assigned[/dim]")
                console.print(skills_tree)
                console.print()

            # Inheritance
            if agent.parent:
                inheritance = f"[bold yellow]Inheritance:[/bold yellow]\n  Parent: {agent.parent}"
                console.print(Panel(inheritance, border_style="yellow"))
                console.print()

            # System prompt
            if show_system_prompt and agent.system_prompt:
                syntax = Syntax(
                    agent.system_prompt,
                    "markdown",
                    theme="monokai",
                    line_numbers=True,
                )
                console.print(
                    Panel(syntax, title="System Prompt", border_style="green"))

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.exceptions.Exit(1)


# =============================================================================
# VALIDATE Command - Validate agent spec
# =============================================================================


@agents.command("validate")
@click.argument("agent_id", required=False)
@click.option("--all", is_flag=True, help="Validate all agents")
@click.option("--strict", is_flag=True, help="Enable strict validation")
@click.option("--fix", is_flag=True, help="Attempt to fix common issues")
def validate_agent(agent_id: str | None, all: bool, strict: bool, fix: bool) -> None:
    """Validate agent spec against schema.

    Checks:
    - Required fields present
    - Valid model names
    - Tool references exist
    - Skill references exist
    - Parent agent exists (if specified)
    - No circular inheritance
    - System prompt quality (strict mode)

    Examples:
        paracle agents validate coder
        paracle agents validate --all
        paracle agents validate coder --strict
        paracle agents validate coder --fix
    """
    from paracle_core.registry import AgentRegistry

    parac_root = get_parac_root_or_exit()
    registry = AgentRegistry(parac_root)

    agents_to_validate = []
    if all:
        agents_to_validate = registry.list_agents()
    elif agent_id:
        agents_to_validate = [agent_id]
    else:
        console.print("[red]Error:[/red] Specify --agent-id or --all")
        raise click.exceptions.Exit(1)

    total_errors = 0
    total_warnings = 0
    total_fixed = 0

    for aid in agents_to_validate:
        console.print(f"\n[cyan]Validating:[/cyan] {aid}")

        try:
            agent = registry.get_agent(aid)
            if not agent:
                console.print("  [red]✗[/red] Agent not found")
                total_errors += 1
                continue

            errors = []
            warnings = []
            fixes = []

            # Required fields
            if not agent.name:
                errors.append("Missing 'name' field")
            if not agent.description:
                warnings.append("Missing 'description' field")
            if not agent.role:
                warnings.append("Missing 'role' field")

            # Model validation
            valid_models = [
                "claude-sonnet-4-20250514",
                "claude-opus-4-20250514",
                "claude-3-7-sonnet-20250219",
                "gpt-4o",
                "gpt-4-turbo",
            ]
            if agent.model not in valid_models:
                warnings.append(f"Model '{agent.model}' may not be supported")

            # Temperature validation
            if agent.temperature < 0 or agent.temperature > 1:
                errors.append(
                    f"Temperature {agent.temperature} out of range [0, 1]")

            # Parent validation
            if agent.parent:
                parent = registry.get_agent(agent.parent)
                if not parent:
                    errors.append(f"Parent agent '{agent.parent}' not found")

                # Check circular inheritance
                visited = {aid}
                current = agent.parent
                while current:
                    if current in visited:
                        errors.append(
                            f"Circular inheritance detected: {current}")
                        break
                    visited.add(current)
                    parent_agent = registry.get_agent(current)
                    current = parent_agent.parent if parent_agent else None

            # Tools validation
            if agent.tools:
                from paracle_tools.registry import ToolRegistry

                tool_registry = ToolRegistry()
                for tool in agent.tools:
                    if not tool_registry.has_tool(tool):
                        warnings.append(f"Tool '{tool}' not found in registry")

            # Skills validation
            if agent.skills:
                skills_dir = parac_root / "agents" / "skills"
                for skill in agent.skills:
                    skill_dir = skills_dir / skill
                    if not skill_dir.exists():
                        warnings.append(f"Skill '{skill}' directory not found")

            # Strict mode checks
            if strict:
                if agent.system_prompt and len(agent.system_prompt) < 50:
                    warnings.append("System prompt seems too short")
                if not agent.capabilities:
                    warnings.append("No capabilities defined")

            # Apply fixes
            if fix and warnings:
                spec_file = parac_root / "agents" / "specs" / f"{aid}.md"
                if spec_file.exists():
                    content = spec_file.read_text()

                    # Fix missing description
                    if "Missing 'description' field" in warnings:
                        if "description:" not in content:
                            content = content.replace(
                                f"name: {agent.name}",
                                f"name: {agent.name}\ndescription: TODO: Add description",
                            )
                            fixes.append("Added placeholder description")

                    if fixes:
                        spec_file.write_text(content)
                        total_fixed += len(fixes)

            # Report
            if errors:
                for err in errors:
                    console.print(f"  [red]✗[/red] {err}")
                total_errors += len(errors)
            if warnings:
                for warn in warnings:
                    console.print(f"  [yellow]⚠[/yellow] {warn}")
                total_warnings += len(warnings)
            if fixes:
                for f in fixes:
                    console.print(f"  [green]✓[/green] Fixed: {f}")

            if not errors and not warnings:
                console.print("  [green]✓[/green] Valid")

        except Exception as e:
            console.print(f"  [red]✗[/red] Validation failed: {e}")
            total_errors += 1

    # Summary
    console.print("\n" + "=" * 60)
    console.print("[bold]Validation Summary:[/bold]")
    console.print(f"  Agents validated: {len(agents_to_validate)}")
    console.print(f"  [red]Errors:[/red] {total_errors}")
    console.print(f"  [yellow]Warnings:[/yellow] {total_warnings}")
    if fix:
        console.print(f"  [green]Fixed:[/green] {total_fixed}")

    if total_errors > 0:
        raise click.exceptions.Exit(1)


# =============================================================================
# TEST Command - Test agent execution
# =============================================================================


@agents.command("test")
@click.argument("agent_id")
@click.option("--task", "-t", help="Test task to execute")
@click.option("--dry-run", is_flag=True, help="Validate without executing")
@click.option("--timeout", type=int, default=30, help="Execution timeout (seconds)")
def test_agent(agent_id: str, task: str | None, dry_run: bool, timeout: int) -> None:
    """Test agent execution with a sample task.

    Runs a quick test to verify:
    - Agent spec is valid
    - Model configuration works
    - Tools are accessible
    - Skills are loaded
    - Agent can execute tasks

    Examples:
        paracle agents test coder --task "Write hello world"
        paracle agents test coder --dry-run
        paracle agents test architect --timeout 60
    """
    import asyncio

    from paracle_core.registry import AgentRegistry
    from paracle_orchestration.executor import AgentExecutor

    parac_root = get_parac_root_or_exit()

    try:
        # Load agent
        console.print(f"[cyan]Testing agent:[/cyan] {agent_id}")
        registry = AgentRegistry(parac_root)
        agent = registry.get_agent(agent_id)

        if not agent:
            console.print(f"[red]✗[/red] Agent '{agent_id}' not found")
            raise click.exceptions.Exit(1)

        console.print("[green]✓[/green] Agent spec loaded")

        # Validate configuration
        console.print(f"[cyan]Model:[/cyan] {agent.model}")
        console.print(f"[cyan]Temperature:[/cyan] {agent.temperature}")
        console.print(
            f"[cyan]Tools:[/cyan] {len(agent.tools) if agent.tools else 0} configured"
        )
        console.print(
            f"[cyan]Skills:[/cyan] {len(agent.skills) if agent.skills else 0} assigned"
        )

        if dry_run:
            console.print(
                "\n[green]✓[/green] Dry run successful - agent is valid")
            return

        # Execute test task
        test_task = task or "Say hello and introduce yourself"

        console.print(f"\n[cyan]Executing test task:[/cyan] {test_task}")
        console.print(
            "[dim](This will consume a small amount of API credits)[/dim]\n")

        with console.status("[bold cyan]Running agent..."):
            executor = AgentExecutor(registry=registry)

            async def run_test():
                result = await executor.execute_agent(
                    agent_id=agent_id,
                    task=test_task,
                    timeout=timeout,
                )
                return result

            result = asyncio.run(run_test())

        # Display result
        if result.success:
            console.print("\n[green]✓[/green] Test successful")
            console.print("\n[bold]Agent Response:[/bold]")
            console.print(result.output)

            if result.tool_calls:
                console.print(
                    f"\n[cyan]Tool Calls:[/cyan] {len(result.tool_calls)}")
                for tc in result.tool_calls:
                    console.print(f"  • {tc.tool}: {tc.status}")

            console.print(
                f"\n[dim]Execution time: {result.duration:.2f}s[/dim]")
        else:
            console.print("\n[red]✗[/red] Test failed")
            console.print(f"[red]Error:[/red] {result.error}")
            raise click.exceptions.Exit(1)

    except Exception as e:
        console.print(f"\n[red]✗[/red] Test failed: {e}")
        raise click.exceptions.Exit(1)


# =============================================================================
# SKILLS Command - Unified skill management
# =============================================================================

# Add the skills subcommand group for skill management
# This provides: list, export, validate, create, show
# Also supports -l/--list shortcut via the modified skills group
agents.add_command(skills_group, name="skills")
