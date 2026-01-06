"""Paracle CLI - IDE integration commands.

Commands for managing IDE/AI assistant integration:
- init: Initialize IDE configuration files
- sync: Synchronize configs with .parac/ state
- status: Show IDE integration status
- list: List supported IDEs

Architecture: CLI -> API -> Core (API-first design)
Falls back to direct core access if API is unavailable.
"""

from pathlib import Path

import click
from paracle_core.parac.state import find_parac_root
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from paracle_cli.api_client import APIClient, APIError, get_client

console = Console()


def get_parac_root_or_exit() -> Path:
    """Get .parac/ root or exit with error."""
    parac_root = find_parac_root()
    if parac_root is None:
        console.print("[red]Error:[/red] No .parac/ directory found.")
        console.print(
            "Run 'paracle init' to create one, or navigate to a project.")
        raise SystemExit(1)
    return parac_root


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


@click.group()
def ide() -> None:
    """IDE and AI assistant integration commands.

    Generate and manage IDE configuration files from .parac/ context.
    """
    pass


# =============================================================================
# LIST Command
# =============================================================================


def _list_via_api(client: APIClient) -> None:
    """List IDEs via API."""
    result = client.ide_list()

    console.print("\n[bold]Supported IDEs:[/bold]\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("IDE", style="cyan")
    table.add_column("File")
    table.add_column("Destination")

    for ide_info in result["ides"]:
        table.add_row(
            ide_info["display_name"],
            ide_info["file_name"],
            ide_info["destination"],
        )

    console.print(table)


def _list_direct() -> None:
    """List IDEs via direct core access."""
    try:
        from paracle_core.parac.ide_generator import IDEConfigGenerator
    except ImportError:
        # Fallback list if jinja2 not installed
        ides = ["cursor", "claude", "cline", "copilot", "windsurf"]
        console.print("\n[bold]Supported IDEs:[/bold]\n")
        for ide_name in ides:
            console.print(f"  - {ide_name}")
        return

    # Use generator for accurate list
    generator = IDEConfigGenerator(Path(".parac"))

    console.print("\n[bold]Supported IDEs:[/bold]\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("IDE", style="cyan")
    table.add_column("File")
    table.add_column("Destination")

    for _ide_name, config in generator.SUPPORTED_IDES.items():
        dest = f"{config.destination_dir}/{config.file_name}"
        table.add_row(config.display_name, config.file_name, dest)

    console.print(table)


@ide.command("list")
def ide_list() -> None:
    """List supported IDEs."""
    use_api_or_fallback(_list_via_api, _list_direct)


# =============================================================================
# STATUS Command
# =============================================================================


def _status_via_api(client: APIClient, as_json: bool) -> None:
    """Get status via API."""
    result = client.ide_status()

    if as_json:
        import json
        console.print(json.dumps(result, indent=2))
        return

    # Rich formatted output
    console.print()
    console.print(
        Panel(
            "[bold]IDE Integration Status[/bold]",
            subtitle=".parac/integrations/ide/",
        )
    )

    # Create table
    table = Table(show_header=True, header_style="bold")
    table.add_column("IDE", style="cyan")
    table.add_column("Generated", justify="center")
    table.add_column("Copied", justify="center")
    table.add_column("Project Path")

    for ide_item in result["ides"]:
        generated = "[green]Yes[/green]" if ide_item["generated"] else "[dim]-[/dim]"
        copied = "[green]Yes[/green]" if ide_item["copied"] else "[dim]-[/dim]"
        project_path = ide_item.get("project_path") or "-"

        # Shorten path for display
        if project_path != "-":
            project_path = Path(project_path).name

        table.add_row(ide_item["name"].title(), generated, copied, project_path)

    console.print(table)

    # Summary
    console.print()
    console.print(
        f"Generated: {result['generated_count']}/{len(result['ides'])}"
    )
    console.print(f"Copied: {result['copied_count']}/{len(result['ides'])}")

    if result["generated_count"] == 0:
        console.print("\n[dim]Run 'paracle ide init' to generate configs[/dim]")


def _status_direct(as_json: bool) -> None:
    """Get status via direct core access."""
    parac_root = get_parac_root_or_exit()

    try:
        from paracle_core.parac.ide_generator import IDEConfigGenerator
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    generator = IDEConfigGenerator(parac_root)
    status = generator.get_status()

    if as_json:
        import json
        console.print(json.dumps(status, indent=2))
        return

    # Rich formatted output
    console.print()
    console.print(
        Panel(
            "[bold]IDE Integration Status[/bold]",
            subtitle=".parac/integrations/ide/",
        )
    )

    # Create table
    table = Table(show_header=True, header_style="bold")
    table.add_column("IDE", style="cyan")
    table.add_column("Generated", justify="center")
    table.add_column("Copied", justify="center")
    table.add_column("Project Path")

    for ide_name, ide_status in status["ides"].items():
        generated = "[green]Yes[/green]" if ide_status["generated"] else "[dim]-[/dim]"
        copied = "[green]Yes[/green]" if ide_status["copied"] else "[dim]-[/dim]"
        project_path = ide_status["project_path"] or "-"

        # Shorten path for display
        if project_path != "-":
            project_path = Path(project_path).name

        table.add_row(ide_name.title(), generated, copied, project_path)

    console.print(table)

    # Summary
    generated_count = sum(
        1 for s in status["ides"].values() if s["generated"]
    )
    copied_count = sum(
        1 for s in status["ides"].values() if s["copied"]
    )

    console.print()
    console.print(f"Generated: {generated_count}/{len(status['ides'])}")
    console.print(f"Copied: {copied_count}/{len(status['ides'])}")

    if generated_count == 0:
        console.print("\n[dim]Run 'paracle ide init' to generate configs[/dim]")


@ide.command("status")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def ide_status(as_json: bool) -> None:
    """Show IDE integration status.

    Displays which IDE configurations are generated and copied.
    """
    use_api_or_fallback(_status_via_api, _status_direct, as_json)


# =============================================================================
# INIT Command
# =============================================================================


def _init_via_api(
    client: APIClient,
    ide_names: tuple[str, ...],
    force: bool,
    copy: bool,
) -> None:
    """Initialize IDEs via API."""
    ides = list(ide_names) if ide_names else []

    try:
        result = client.ide_init(ides=ides, force=force, copy=copy)
    except APIError as e:
        if e.status_code == 409:
            console.print(f"[yellow]Warning:[/yellow] {e.detail}")
            if not click.confirm("Overwrite?"):
                raise SystemExit(0)
            # Retry with force
            result = client.ide_init(ides=ides, force=True, copy=copy)
        else:
            raise

    console.print("\n[bold]Generating IDE configurations...[/bold]\n")

    for item in result["results"]:
        if item["generated"]:
            console.print(f"  [green]OK[/green] Generated: {item['ide']}")
            if item["copied"]:
                console.print(f"    [blue]->[/blue] Copied to: {item['project_path']}")
        elif item.get("error"):
            console.print(f"  [red]FAIL[/red] {item['ide']}: {item['error']}")

    if result.get("manifest_path"):
        console.print(f"\n  [dim]Manifest: {result['manifest_path']}[/dim]")

    # Summary
    console.print()
    if result["generated_count"] > 0:
        console.print(
            f"[green]OK[/green] Generated {result['generated_count']} config(s) "
            f"in .parac/integrations/ide/"
        )
    if result["copied_count"] > 0:
        console.print(
            f"[blue]->[/blue] Copied {result['copied_count']} config(s) "
            f"to project root"
        )
    if result["failed_count"] > 0:
        console.print(
            f"[red]FAIL[/red] {result['failed_count']} config(s) failed"
        )


def _init_direct(
    ide_names: tuple[str, ...],
    force: bool,
    copy: bool,
) -> None:
    """Initialize IDEs via direct core access."""
    parac_root = get_parac_root_or_exit()

    try:
        from paracle_core.parac.ide_generator import IDEConfigGenerator
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("Install jinja2: pip install jinja2")
        raise SystemExit(1)

    generator = IDEConfigGenerator(parac_root)
    supported = generator.get_supported_ides()

    # Determine which IDEs to initialize
    if not ide_names or "all" in ide_names:
        ides_to_init = supported
    else:
        ides_to_init = []
        for name in ide_names:
            if name.lower() in supported:
                ides_to_init.append(name.lower())
            else:
                console.print(
                    f"[yellow]Warning:[/yellow] Unknown IDE '{name}'. "
                    f"Supported: {', '.join(supported)}"
                )

    if not ides_to_init:
        console.print("[red]Error:[/red] No valid IDEs specified.")
        raise SystemExit(1)

    # Check for existing files if not forcing
    if not force:
        existing = []
        for ide_name in ides_to_init:
            config = generator.get_ide_config(ide_name)
            if config:
                generated_file = generator.ide_output_dir / config.file_name
                if generated_file.exists():
                    existing.append(ide_name)

        if existing:
            console.print(
                f"[yellow]Warning:[/yellow] Files exist for: {', '.join(existing)}"
            )
            if not click.confirm("Overwrite?"):
                raise SystemExit(0)

    # Generate configs
    console.print("\n[bold]Generating IDE configurations...[/bold]\n")

    results = {"generated": [], "copied": [], "failed": []}

    for ide_name in ides_to_init:
        try:
            # Generate to .parac/integrations/ide/
            path = generator.generate_to_file(ide_name)
            results["generated"].append((ide_name, path))
            console.print(f"  [green]OK[/green] Generated: {path.name}")

            # Copy to project root if requested
            if copy:
                dest = generator.copy_to_project(ide_name)
                results["copied"].append((ide_name, dest))
                console.print(f"    [blue]->[/blue] Copied to: {dest}")

        except Exception as e:
            results["failed"].append((ide_name, str(e)))
            console.print(f"  [red]FAIL[/red] {ide_name}: {e}")

    # Generate manifest
    try:
        manifest_path = generator.generate_manifest()
        console.print(f"\n  [dim]Manifest: {manifest_path}[/dim]")
    except Exception as e:
        console.print(
            f"\n  [yellow]Warning:[/yellow] Could not generate manifest: {e}"
        )

    # Summary
    console.print()
    if results["generated"]:
        console.print(
            f"[green]OK[/green] Generated {len(results['generated'])} config(s) "
            f"in .parac/integrations/ide/"
        )
    if results["copied"]:
        console.print(
            f"[blue]->[/blue] Copied {len(results['copied'])} config(s) "
            f"to project root"
        )
    if results["failed"]:
        console.print(
            f"[red]FAIL[/red] {len(results['failed'])} config(s) failed"
        )


@ide.command("init")
@click.option(
    "--ide",
    "ide_names",
    multiple=True,
    help="IDE(s) to initialize (cursor, claude, cline, copilot, windsurf, all)",
)
@click.option("--force", is_flag=True, help="Overwrite existing files")
@click.option("--copy/--no-copy", default=True, help="Copy to project root")
def ide_init(ide_names: tuple[str, ...], force: bool, copy: bool) -> None:
    """Initialize IDE configuration files.

    Generates IDE-specific configuration files from .parac/ context
    and optionally copies them to the project root.

    Examples:
        paracle ide init --ide=cursor
        paracle ide init --ide=all
        paracle ide init --ide=cursor --ide=claude
    """
    use_api_or_fallback(_init_via_api, _init_direct, ide_names, force, copy)


# =============================================================================
# SYNC Command
# =============================================================================


def _sync_via_api(client: APIClient, copy: bool, watch: bool) -> None:
    """Sync IDEs via API."""
    if watch:
        console.print(
            "[yellow]Warning:[/yellow] Watch mode not yet implemented. "
            "Will run single sync."
        )

    result = client.ide_sync(copy=copy)

    console.print("\n[bold]Syncing IDE configurations...[/bold]\n")

    for ide_name in result["synced"]:
        console.print(f"  [green]OK[/green] Synced: {ide_name}")

    if copy and result["copied"]:
        console.print()
        for ide_name in result["copied"]:
            console.print(f"  [blue]->[/blue] Copied: {ide_name}")

    for error in result.get("errors", []):
        console.print(f"  [red]Error:[/red] {error}")

    console.print(
        f"\n[green]OK[/green] Synced {len(result['synced'])} IDE configuration(s)"
    )


def _sync_direct(copy: bool, watch: bool) -> None:
    """Sync IDEs via direct core access."""
    if watch:
        console.print(
            "[yellow]Warning:[/yellow] Watch mode not yet implemented. "
            "Will run single sync."
        )

    parac_root = get_parac_root_or_exit()

    try:
        from paracle_core.parac.ide_generator import IDEConfigGenerator
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    generator = IDEConfigGenerator(parac_root)

    console.print("\n[bold]Syncing IDE configurations...[/bold]\n")

    # Generate all configs
    generated = generator.generate_all()

    for _ide_name, path in generated.items():
        console.print(f"  [green]OK[/green] Synced: {path.name}")

    # Copy to project root if requested
    if copy:
        copied = generator.copy_all_to_project()
        console.print()
        for _ide_name, path in copied.items():
            console.print(f"  [blue]->[/blue] Copied: {path}")

    # Update manifest
    try:
        generator.generate_manifest()
    except Exception:
        pass

    console.print(
        f"\n[green]OK[/green] Synced {len(generated)} IDE configuration(s)"
    )


@ide.command("sync")
@click.option("--copy/--no-copy", default=True, help="Copy to project root")
@click.option(
    "--watch", is_flag=True, help="Watch for changes (not yet implemented)"
)
def ide_sync(copy: bool, watch: bool) -> None:
    """Synchronize IDE configs with .parac/ state.

    Regenerates all IDE configuration files from current .parac/ context.

    Examples:
        paracle ide sync
        paracle ide sync --no-copy
    """
    use_api_or_fallback(_sync_via_api, _sync_direct, copy, watch)


# =============================================================================
# BUILD Command - Native Agent Compilation
# =============================================================================


@ide.command("build")
@click.option(
    "--target",
    required=True,
    type=click.Choice(["vscode", "claude", "cursor", "windsurf", "codex", "all"]),
    help="Target IDE for agent compilation",
)
@click.option(
    "--copy/--no-copy",
    default=True,
    help="Copy to expected IDE locations (e.g., .github/agents/)",
)
@click.option(
    "--output",
    type=click.Path(),
    help="Custom output directory",
)
def ide_build(target: str, copy: bool, output: str | None) -> None:
    """Build native agent files for IDEs.

    Compiles .parac/agents/ to IDE-native formats:

    \b
    - vscode: .github/agents/*.agent.md (Copilot custom agents)
    - claude: .claude/agents/*.md (Claude Code subagents)
    - cursor: .cursorrules with agent router (@architect, @coder, etc.)
    - windsurf: .windsurfrules + mcp_config.json
    - codex: AGENTS.md at project root

    Generated files reference Paracle MCP tools via:
        paracle mcp serve --stdio

    Examples:
        paracle ide build --target vscode
        paracle ide build --target all --copy
        paracle ide build --target claude --no-copy --output ./custom/
    """
    parac_root = get_parac_root_or_exit()

    try:
        from paracle_core.parac.agent_compiler import AgentCompiler
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("Ensure paracle_core is properly installed.")
        raise SystemExit(1)

    compiler = AgentCompiler(parac_root)

    # Determine output directory
    output_dir = Path(output) if output else None

    console.print(f"\n[bold]Building agents for {target}...[/bold]\n")

    try:
        result = compiler.build(target, output_dir=output_dir)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    # Display generated files
    for file_path in result["files"]:
        console.print(f"  [green]OK[/green] Generated: {Path(file_path).name}")

    # Copy to destinations if requested
    if copy:
        console.print()
        try:
            copied = compiler.copy_to_destinations(target)
            for dest in copied:
                console.print(f"  [blue]->[/blue] Copied to: {dest}")
        except Exception as e:
            console.print(f"  [yellow]Warning:[/yellow] Copy failed: {e}")

    # Summary
    console.print(
        f"\n[green]OK[/green] Built {len(result['files'])} file(s) for {target}"
    )

    # Hint about MCP
    console.print(
        "\n[dim]Tip: Start MCP server for tool access: paracle mcp serve --stdio[/dim]"
    )
