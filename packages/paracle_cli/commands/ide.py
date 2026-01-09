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
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from paracle_cli.api_client import APIClient, APIError, get_client
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
    help="List supported IDEs (shortcut for 'list')",
)
@click.pass_context
def ide(ctx: click.Context, list_flag: bool) -> None:
    """IDE and AI assistant integration commands.

    Generate and manage IDE configuration files from .parac/ context.

    Examples:
        paracle ide -l      - List supported IDEs (shortcut)
        paracle ide list    - List supported IDEs
        paracle ide sync    - Sync IDE configs
    """
    if list_flag:
        ctx.invoke(ide_list)
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


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
    console.print(f"Generated: {result['generated_count']}/{len(result['ides'])}")
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
    generated_count = sum(1 for s in status["ides"].values() if s["generated"])
    copied_count = sum(1 for s in status["ides"].values() if s["copied"])

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
            f"[blue]->[/blue] Copied {result['copied_count']} config(s) to project root"
        )
    if result["failed_count"] > 0:
        console.print(f"[red]FAIL[/red] {result['failed_count']} config(s) failed")


def _init_direct(
    ide_names: tuple[str, ...],
    force: bool,
    copy: bool,
    no_format: bool = False,
    strict: bool = False,
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
            path = generator.generate_to_file(
                ide_name, skip_format=no_format, strict=strict
            )
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
        console.print(f"\n  [yellow]Warning:[/yellow] Could not generate manifest: {e}")

    # Summary
    console.print()
    if results["generated"]:
        console.print(
            f"[green]OK[/green] Generated {len(results['generated'])} config(s) "
            f"in .parac/integrations/ide/"
        )
    if results["copied"]:
        console.print(
            f"[blue]->[/blue] Copied {len(results['copied'])} config(s) to project root"
        )
    if results["failed"]:
        console.print(f"[red]FAIL[/red] {len(results['failed'])} config(s) failed")


@ide.command("init")
@click.option(
    "--ide",
    "ide_names",
    multiple=True,
    help="IDE(s) to initialize. Use 'paracle ide list' to see all options.",
)
@click.option("--force", is_flag=True, help="Overwrite existing files")
@click.option("--copy/--no-copy", default=True, help="Copy to project root")
@click.option(
    "--no-format",
    is_flag=True,
    help="Skip agent spec formatting (only validate)",
)
@click.option(
    "--strict",
    is_flag=True,
    help="Treat validation warnings as errors",
)
def ide_init(
    ide_names: tuple[str, ...],
    force: bool,
    copy: bool,
    no_format: bool,
    strict: bool,
) -> None:
    """Initialize IDE configuration files.

    Generates IDE-specific configuration files from .parac/ context
    and optionally copies them to the project root.

    Validation:
    - Validates .parac/ workspace structure before generation
    - Auto-formats agent specs (use --no-format to skip)
    - Use --strict to treat warnings as errors

    Supported IDEs (13 total):
    - MCP Native: cursor, claude, windsurf, zed
    - Rules-based: cline, copilot, warp, gemini, opencode
    - Web-based: claude_desktop, chatgpt, raycast
    - CI/CD: claude_action, copilot_agent

    Examples:
        paracle ide init --ide=cursor
        paracle ide init --ide=all
        paracle ide init --ide=cursor --ide=claude --ide=zed
    """
    use_api_or_fallback(
        _init_via_api,
        _init_direct,
        ide_names,
        force,
        copy,
        no_format,
        strict,
    )


# =============================================================================
# SYNC Command
# =============================================================================


def _sync_via_api(
    client: APIClient, copy: bool, watch: bool, with_skills: bool
) -> None:
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

    # Export skills if requested (API doesn't support this yet, fall back)
    if with_skills:
        _export_skills_to_platforms()


def _sync_direct(
    copy: bool,
    watch: bool,
    with_skills: bool,
    no_format: bool = False,
    strict: bool = False,
) -> None:
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
    generated = generator.generate_all(skip_format=no_format, strict=strict)

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

    console.print(f"\n[green]OK[/green] Synced {len(generated)} IDE configuration(s)")

    # Export skills to IDE platforms if requested
    if with_skills:
        _export_skills_to_platforms()


def _export_skills_to_platforms() -> None:
    """Export skills to IDE platform directories."""
    parac_root = get_parac_root_or_exit()
    skills_dir = parac_root / "agents" / "skills"

    if not skills_dir.exists():
        console.print("\n[dim]No skills directory found, skipping.[/dim]")
        return

    try:
        from paracle_skills import SkillExporter, SkillLoader
        from paracle_skills.exporter import AGENT_SKILLS_PLATFORMS
    except ImportError:
        console.print(
            "\n[yellow]Warning:[/yellow] paracle_skills not available. "
            "Skills export skipped."
        )
        return

    # Load skills
    loader = SkillLoader(skills_dir)
    try:
        skills = loader.load_all()
    except Exception as e:
        console.print(f"\n[yellow]Warning:[/yellow] Failed to load skills: {e}")
        return

    if not skills:
        console.print("\n[dim]No skills found to export.[/dim]")
        return

    console.print(f"\n[bold]Exporting {len(skills)} skill(s) to platforms...[/bold]\n")

    # Export to Agent Skills platforms (copilot, cursor, claude, codex)
    exporter = SkillExporter(skills)
    project_root = parac_root.parent

    try:
        results = exporter.export_all(project_root, AGENT_SKILLS_PLATFORMS, True)

        # Count successes per platform
        platform_counts: dict[str, int] = {}
        for result in results:
            for platform, export_result in result.results.items():
                if export_result.success:
                    platform_counts[platform] = platform_counts.get(platform, 0) + 1

        for platform, count in platform_counts.items():
            platform_dirs = {
                "copilot": ".github/skills/",
                "cursor": ".cursor/skills/",
                "claude": ".claude/skills/",
                "codex": ".codex/skills/",
            }
            dest = platform_dirs.get(platform, f".{platform}/skills/")
            console.print(f"  [green]OK[/green] {platform}: {count} skill(s) -> {dest}")

    except Exception as e:
        console.print(f"  [red]Error:[/red] Skills export failed: {e}")


@ide.command("sync")
@click.option("--copy/--no-copy", default=True, help="Copy to project root")
@click.option("--watch", is_flag=True, help="Watch for changes (not implemented)")
@click.option(
    "--with-skills/--no-skills",
    default=True,
    help="Export skills to IDE platforms (default: yes)",
)
@click.option(
    "--no-format",
    is_flag=True,
    help="Skip agent spec formatting (only validate)",
)
@click.option(
    "--strict",
    is_flag=True,
    help="Treat validation warnings as errors",
)
def ide_sync(
    copy: bool, watch: bool, with_skills: bool, no_format: bool, strict: bool
) -> None:
    """Synchronize IDE configs with .parac/ state.

    Regenerates all IDE configuration files from current .parac/ context.
    Also exports skills to platform-specific directories when available.

    Validation:
    - Validates .parac/ workspace structure before generation
    - Auto-formats agent specs (use --no-format to skip)
    - Use --strict to treat warnings as errors

    Examples:
        paracle ide sync
        paracle ide sync --no-copy
        paracle ide sync --no-skills
        paracle ide sync --strict
    """
    use_api_or_fallback(
        _sync_via_api,
        _sync_direct,
        copy,
        watch,
        with_skills,
        no_format,
        strict,
    )


# =============================================================================
# BUILD Command - Native Agent Compilation
# =============================================================================


@ide.command("build")
@click.option(
    "--target",
    required=True,
    type=click.Choice(
        [
            "vscode",
            "claude",
            "cursor",
            "windsurf",
            "codex",
            "zed",
            "warp",
            "gemini",
            "all",
        ]
    ),
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
    MCP Native:
    - vscode: .github/agents/*.agent.md (Copilot custom agents)
    - claude: .claude/agents/*.md (Claude Code subagents)
    - cursor: .cursorrules with agent router (@architect, @coder, etc.)
    - windsurf: .windsurfrules + mcp_config.json
    - zed: .zed/ai_rules.json + mcp settings

    Rules-based:
    - codex: AGENTS.md at project root
    - warp: .warp/ai-rules.yaml
    - gemini: .gemini/instructions.md

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


# =============================================================================
# SETUP Command - Automatic IDE Detection & Configuration
# =============================================================================


def _detect_installed_ides() -> list[str]:
    """Detect IDEs installed on the system.

    Returns:
        List of detected IDE names
    """
    import shutil

    detected = []

    # Check for IDE-specific directories and executables
    ide_checks = {
        "cursor": [".cursor", "cursor"],
        "vscode": [".vscode", "code"],
        "zed": [".zed", "zed"],
        "windsurf": [".windsurf", "windsurf"],
        "warp": [".warp", "warp"],
    }

    project_root = Path.cwd()

    for ide_name, checks in ide_checks.items():
        for check in checks:
            # Check for directory
            if (project_root / check).exists():
                detected.append(ide_name)
                break
            # Check for executable
            if shutil.which(check):
                detected.append(ide_name)
                break

    # Always include claude (Claude Code CLI) if paracle is available
    if shutil.which("claude") or shutil.which("paracle"):
        if "claude" not in detected:
            detected.append("claude")

    return detected


@ide.command("setup")
@click.option(
    "--ide",
    "ide_name",
    type=str,
    help="Specific IDE to set up (auto-detects if not specified)",
)
@click.option("--all", "setup_all", is_flag=True, help="Set up all detected IDEs")
@click.option("--force", is_flag=True, help="Overwrite existing configurations")
def ide_setup(ide_name: str | None, setup_all: bool, force: bool) -> None:
    """Automatically detect and configure IDEs.

    Detects installed IDEs and configures them for Paracle integration,
    including MCP server setup where supported.

    Examples:
        paracle ide setup              # Auto-detect and configure
        paracle ide setup --ide cursor # Configure specific IDE
        paracle ide setup --all        # Configure all detected IDEs
    """
    parac_root = get_parac_root_or_exit()

    console.print("\n[bold]IDE Setup[/bold]\n")

    # Detect installed IDEs
    detected = _detect_installed_ides()

    if not detected:
        console.print("[yellow]No IDEs detected.[/yellow]")
        console.print("\nSupported IDEs:")
        console.print("  cursor, claude, windsurf, zed, vscode, warp")
        console.print("\nRun with --ide <name> to configure manually.")
        return

    console.print(f"[green]Detected IDEs:[/green] {', '.join(detected)}\n")

    # Determine which IDEs to configure
    if ide_name:
        ides_to_setup = [ide_name.lower()]
    elif setup_all:
        ides_to_setup = detected
    else:
        # Interactive: ask user
        console.print("Which IDE(s) would you like to configure?")
        for i, ide in enumerate(detected, 1):
            console.print(f"  {i}. {ide}")
        console.print(f"  {len(detected) + 1}. All")
        console.print(f"  {len(detected) + 2}. Cancel")

        choice = click.prompt("Enter choice", type=int, default=len(detected) + 1)
        if choice == len(detected) + 2:
            console.print("[dim]Cancelled.[/dim]")
            return
        elif choice == len(detected) + 1:
            ides_to_setup = detected
        elif 1 <= choice <= len(detected):
            ides_to_setup = [detected[choice - 1]]
        else:
            console.print("[red]Invalid choice.[/red]")
            return

    # Configure each IDE
    try:
        from paracle_core.parac.ide_generator import IDEConfigGenerator
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    generator = IDEConfigGenerator(parac_root)

    for ide in ides_to_setup:
        console.print(f"\n[bold]Configuring {ide}...[/bold]")

        try:
            # Generate config
            path = generator.generate_to_file(ide)
            console.print(f"  [green]OK[/green] Generated: {path.name}")

            # Copy to project
            dest = generator.copy_to_project(ide)
            console.print(f"  [blue]->[/blue] Copied to: {dest}")

            # IDE-specific MCP setup hints
            mcp_ides = ["cursor", "claude", "windsurf", "zed", "vscode"]
            if ide in mcp_ides:
                console.print(f"  [dim]MCP: Add paracle server to {ide} settings[/dim]")

        except Exception as e:
            console.print(f"  [red]FAIL[/red] {ide}: {e}")

    console.print("\n[green]OK[/green] IDE setup complete!")
    console.print("\n[dim]Start MCP server: paracle mcp serve --stdio[/dim]")


# =============================================================================
# INSTRUCTIONS Command - Show copy-paste instructions for web-based IDEs
# =============================================================================


@ide.command("instructions")
@click.argument("ide_name", type=str)
def ide_instructions(ide_name: str) -> None:
    """Show setup instructions for an IDE.

    Displays copy-paste instructions for web-based IDEs like ChatGPT,
    Claude.ai, and Raycast that don't support file-based configuration.

    Examples:
        paracle ide instructions chatgpt
        paracle ide instructions claude_desktop
        paracle ide instructions raycast
    """
    parac_root = get_parac_root_or_exit()

    try:
        from paracle_core.parac.ide_generator import IDEConfigGenerator
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    generator = IDEConfigGenerator(parac_root)
    config = generator.get_ide_config(ide_name.lower())

    if not config:
        console.print(f"[red]Unknown IDE:[/red] {ide_name}")
        console.print("\nSupported IDEs:")
        for name in generator.get_supported_ides():
            console.print(f"  - {name}")
        return

    # Web-based IDEs that need copy-paste
    web_ides = ["chatgpt", "claude_desktop", "raycast"]

    console.print(f"\n[bold]Instructions for {config.display_name}[/bold]\n")

    if ide_name.lower() in web_ides:
        console.print("This IDE uses copy-paste configuration.\n")
        console.print("[bold]Steps:[/bold]")
        console.print("1. Run: paracle ide init --ide=" + ide_name.lower())
        console.print(f"2. Open: {config.destination_dir}/{config.file_name}")
        console.print("3. Copy the entire file content")
        console.print(f"4. Paste into {config.display_name}\n")

        if ide_name.lower() == "chatgpt":
            console.print("[dim]Options:[/dim]")
            console.print("  - Paste at conversation start")
            console.print("  - Add to Custom Instructions")
            console.print("  - Create a GPT with these instructions")
        elif ide_name.lower() == "claude_desktop":
            console.print("[dim]Options:[/dim]")
            console.print("  - Paste at conversation start")
            console.print("  - Add to Claude.ai Project Knowledge")
            console.print("  - Set as Claude Desktop system prompt")
        elif ide_name.lower() == "raycast":
            console.print("[dim]Options:[/dim]")
            console.print("  - Create AI Command with instructions")
            console.print("  - Paste in Raycast AI chat")
    else:
        console.print("This IDE uses file-based configuration.\n")
        console.print("[bold]Steps:[/bold]")
        console.print(f"1. Run: paracle ide init --ide={ide_name.lower()} --copy")
        console.print(f"2. Config copied to: {config.destination_dir}/")

        # MCP setup hint
        mcp_ides = ["cursor", "claude", "windsurf", "zed", "vscode"]
        if ide_name.lower() in mcp_ides:
            console.print("\n[bold]MCP Setup:[/bold]")
            console.print("Add Paracle MCP server to your IDE settings:")
            console.print("  Command: paracle mcp serve --stdio")


# =============================================================================
# MCP Command - Generate MCP configurations for all IDEs
# =============================================================================


def _mcp_list_direct() -> None:
    """List MCP-supported IDEs via direct core access."""
    try:
        from paracle_core.parac.ide_generator import IDEConfigGenerator
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    generator = IDEConfigGenerator(Path(".parac"))

    console.print("\n[bold]IDEs with MCP Support:[/bold]\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("IDE", style="cyan")
    table.add_column("Config File")
    table.add_column("Location")
    table.add_column("Scope")

    for _ide_name, config in generator.SUPPORTED_MCP.items():
        scope = "Home (~)" if config.uses_home_dir else "Project"
        dest = f"{config.destination_dir}/{config.file_name}"
        table.add_row(config.display_name, config.file_name, dest, scope)

    console.print(table)


def _mcp_status_direct(as_json: bool) -> None:
    """Get MCP status via direct core access."""
    parac_root = get_parac_root_or_exit()

    try:
        from paracle_core.parac.ide_generator import IDEConfigGenerator
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    generator = IDEConfigGenerator(parac_root)
    status = generator.get_mcp_status()

    if as_json:
        import json

        console.print(json.dumps(status, indent=2))
        return

    # Rich formatted output
    console.print()
    console.print(
        Panel(
            "[bold]MCP Configuration Status[/bold]",
            subtitle=".parac/integrations/mcp/",
        )
    )

    table = Table(show_header=True, header_style="bold")
    table.add_column("IDE", style="cyan")
    table.add_column("Generated", justify="center")
    table.add_column("Installed", justify="center")
    table.add_column("Location")

    for ide_name, info in status["configs"].items():
        generated = "[green]Yes[/green]" if info["generated"] else "[dim]-[/dim]"
        installed = "[green]Yes[/green]" if info["installed"] else "[dim]-[/dim]"
        scope = "(home)" if info["uses_home_dir"] else ""
        location = f"{info['display_name']} {scope}"

        table.add_row(ide_name, generated, installed, location)

    console.print(table)

    # Summary
    gen_count = sum(1 for s in status["configs"].values() if s["generated"])
    inst_count = sum(1 for s in status["configs"].values() if s["installed"])

    console.print()
    console.print(f"Generated: {gen_count}/{len(status['configs'])}")
    console.print(f"Installed: {inst_count}/{len(status['configs'])}")

    if gen_count == 0:
        console.print("\n[dim]Run 'paracle ide mcp --generate' to create configs[/dim]")


def _mcp_generate_direct(
    ide_names: tuple[str, ...],
    copy: bool,
    force: bool,
    include_home: bool,
) -> None:
    """Generate MCP configs via direct core access."""
    parac_root = get_parac_root_or_exit()

    try:
        from paracle_core.parac.ide_generator import IDEConfigGenerator
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    generator = IDEConfigGenerator(parac_root)
    supported = generator.get_supported_mcp_ides()

    # Determine which IDEs to generate for
    if not ide_names or "all" in ide_names:
        ides_to_generate = supported
    else:
        ides_to_generate = []
        for name in ide_names:
            if name.lower() in supported:
                ides_to_generate.append(name.lower())
            else:
                console.print(
                    f"[yellow]Warning:[/yellow] Unknown MCP IDE '{name}'. "
                    f"Supported: {', '.join(supported)}"
                )

    if not ides_to_generate:
        console.print("[red]Error:[/red] No valid MCP IDEs specified.")
        raise SystemExit(1)

    # Generate configs
    console.print("\n[bold]Generating MCP configurations...[/bold]\n")

    results = {"generated": [], "copied": [], "skipped": [], "failed": []}

    for ide_name in ides_to_generate:
        config = generator.get_mcp_config(ide_name)
        if not config:
            continue

        # Skip home directory configs unless requested
        if config.uses_home_dir and not include_home:
            results["skipped"].append(ide_name)
            console.print(
                f"  [dim]SKIP[/dim] {config.display_name} (use --include-home)"
            )
            continue

        try:
            # Generate to .parac/integrations/mcp/
            path = generator.generate_mcp_to_file(ide_name)
            results["generated"].append((ide_name, path))
            console.print(f"  [green]OK[/green] Generated: {path.name}")

            # Copy to destination if requested
            if copy:
                dest = generator.copy_mcp_to_project(ide_name)
                results["copied"].append((ide_name, dest))
                console.print(f"    [blue]->[/blue] Copied to: {dest}")

        except Exception as e:
            results["failed"].append((ide_name, str(e)))
            console.print(f"  [red]FAIL[/red] {ide_name}: {e}")

    # Summary
    console.print()
    if results["generated"]:
        console.print(
            f"[green]OK[/green] Generated {len(results['generated'])} MCP config(s) "
            f"in .parac/integrations/mcp/"
        )
    if results["copied"]:
        console.print(
            f"[blue]->[/blue] Copied {len(results['copied'])} config(s) to IDE directories"
        )
    if results["skipped"]:
        console.print(
            f"[dim]Skipped {len(results['skipped'])} home-directory config(s)[/dim]"
        )
    if results["failed"]:
        console.print(f"[red]FAIL[/red] {len(results['failed'])} config(s) failed")

    # MCP server hint
    console.print("\n[dim]Start MCP server: paracle mcp serve --stdio[/dim]")


@ide.command("mcp")
@click.option(
    "--ide",
    "ide_names",
    multiple=True,
    help="IDE(s) to generate MCP config for. Use 'paracle ide mcp --list' to see all.",
)
@click.option("--list", "-l", "list_flag", is_flag=True, help="List MCP-supported IDEs")
@click.option(
    "--status", "-s", "status_flag", is_flag=True, help="Show MCP config status"
)
@click.option(
    "--generate", "-g", "generate_flag", is_flag=True, help="Generate MCP configs"
)
@click.option("--copy/--no-copy", default=True, help="Copy to IDE directories")
@click.option("--force", is_flag=True, help="Overwrite existing files")
@click.option(
    "--include-home/--no-include-home",
    default=False,
    help="Include configs for home directory (Windsurf, Claude Desktop)",
)
@click.option("--json", "as_json", is_flag=True, help="Output status as JSON")
def ide_mcp(
    ide_names: tuple[str, ...],
    list_flag: bool,
    status_flag: bool,
    generate_flag: bool,
    copy: bool,
    force: bool,
    include_home: bool,
    as_json: bool,
) -> None:
    """Generate MCP (Model Context Protocol) configurations for IDEs.

    Creates mcp.json/mcp_config.json files that connect your IDE to the
    Paracle MCP server, enabling access to Paracle tools from your IDE.

    \b
    Supported IDEs:
    - Project-level: vscode, cursor, cline, zed, rovodev
    - Home directory: windsurf (~/.codeium/windsurf/), claude_desktop

    \b
    Generated config enables these MCP tools:
    - Agent execution and workflow management
    - .parac/ governance tools
    - Memory and context tools
    - Skill invocation

    Examples:
        paracle ide mcp --list              # List MCP-supported IDEs
        paracle ide mcp --status            # Show current status
        paracle ide mcp --generate          # Generate all project-level configs
        paracle ide mcp --generate --copy   # Generate and install
        paracle ide mcp --ide cursor        # Generate for specific IDE
        paracle ide mcp --generate --include-home  # Include Windsurf/Claude Desktop
    """
    if list_flag:
        _mcp_list_direct()
    elif status_flag:
        _mcp_status_direct(as_json)
    elif generate_flag or ide_names:
        _mcp_generate_direct(ide_names, copy, force, include_home)
    else:
        # Default: show status
        _mcp_status_direct(as_json)


# =============================================================================
# Skills Command - Export skills for IDE/AI platforms
# =============================================================================

# Supported platforms for skill export
SKILL_PLATFORMS = ["copilot", "cursor", "claude", "codex", "rovodev"]


def _skills_list_direct(output_format: str, verbose: bool) -> None:
    """List skills via direct core access."""
    parac_root = get_parac_root_or_exit()

    try:
        from paracle_skills import SkillLoader
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    skills_dir = parac_root / "agents" / "skills"
    loader = SkillLoader(skills_dir)

    try:
        skill_list = loader.load_all()
    except Exception as e:
        console.print(f"[red]Error loading skills:[/red] {e}")
        raise SystemExit(1)

    if not skill_list:
        console.print("[yellow]No skills found in .parac/agents/skills/[/yellow]")
        console.print("\nCreate a skill with: paracle ide skills create my-skill")
        return

    if output_format == "json":
        import json

        data = [
            {
                "name": s.name,
                "description": s.description,
                "category": s.metadata.category.value,
                "level": s.metadata.level.value,
                "tools": len(s.tools),
            }
            for s in skill_list
        ]
        console.print(json.dumps(data, indent=2))

    elif output_format == "yaml":
        import yaml

        data = [
            {
                "name": s.name,
                "description": s.description,
                "category": s.metadata.category.value,
                "level": s.metadata.level.value,
            }
            for s in skill_list
        ]
        console.print(yaml.dump(data, default_flow_style=False))

    else:  # table
        table = Table(title=f"Skills ({len(skill_list)} found)")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Category", style="green")
        table.add_column("Level", style="yellow")
        if verbose:
            table.add_column("Tools", justify="right")
            table.add_column("Description")

        for skill in sorted(skill_list, key=lambda s: s.name):
            if verbose:
                desc = (
                    skill.description[:50] + "..."
                    if len(skill.description) > 50
                    else skill.description
                )
                table.add_row(
                    skill.name,
                    skill.metadata.category.value,
                    skill.metadata.level.value,
                    str(len(skill.tools)),
                    desc,
                )
            else:
                table.add_row(
                    skill.name,
                    skill.metadata.category.value,
                    skill.metadata.level.value,
                )

        console.print(table)


def _skills_status_direct() -> None:
    """Show skill export status for each platform."""
    parac_root = get_parac_root_or_exit()
    project_root = parac_root.parent

    try:
        from paracle_skills import SkillLoader
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    skills_dir = parac_root / "agents" / "skills"
    loader = SkillLoader(skills_dir)

    try:
        skill_list = loader.load_all()
    except Exception:
        skill_list = []

    skill_count = len(skill_list)

    # Platform directories
    platform_dirs = {
        "copilot": ".github/skills",
        "cursor": ".cursor/skills",
        "claude": ".claude/skills",
        "codex": ".codex/skills",
        "rovodev": ".rovodev/subagents",
    }

    console.print()
    console.print(
        Panel(
            f"[bold]Skill Export Status[/bold]\n{skill_count} skills in .parac/agents/skills/",
            subtitle="paracle ide skills",
        )
    )

    table = Table(show_header=True, header_style="bold")
    table.add_column("Platform", style="cyan")
    table.add_column("Directory")
    table.add_column("Exported", justify="center")

    for platform, directory in platform_dirs.items():
        platform_path = project_root / directory
        if platform_path.exists():
            # Count exported skills
            if platform == "rovodev":
                exported = len(list(platform_path.glob("*.md")))
            else:
                exported = len(list(platform_path.glob("*/SKILL.md")))
            status = f"[green]{exported}[/green]" if exported > 0 else "[dim]0[/dim]"
        else:
            status = "[dim]-[/dim]"

        table.add_row(platform, directory, status)

    console.print(table)

    if skill_count == 0:
        console.print(
            "\n[dim]No skills found. Create with: paracle ide skills create my-skill[/dim]"
        )
    else:
        console.print(
            "\n[dim]Export with: paracle ide skills export --platform copilot[/dim]"
        )


def _skills_export_direct(
    platforms: tuple[str, ...],
    skill_names: tuple[str, ...],
    overwrite: bool,
    dry_run: bool,
) -> None:
    """Export skills to IDE platforms."""
    parac_root = get_parac_root_or_exit()
    project_root = parac_root.parent

    try:
        from paracle_skills import SkillExporter, SkillLoader
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    # Determine platforms
    platform_list = list(platforms)
    if not platform_list or "all" in platform_list:
        platform_list = SKILL_PLATFORMS

    # Remove 'all' if present
    platform_list = [p for p in platform_list if p != "all"]

    # Validate platforms
    invalid = [p for p in platform_list if p not in SKILL_PLATFORMS]
    if invalid:
        console.print(
            f"[yellow]Warning:[/yellow] Unknown platform(s): {', '.join(invalid)}"
        )
        platform_list = [p for p in platform_list if p in SKILL_PLATFORMS]

    if not platform_list:
        console.print("[red]Error:[/red] No valid platforms specified.")
        console.print(f"Available: {', '.join(SKILL_PLATFORMS)}")
        raise SystemExit(1)

    # Load skills
    skills_dir = parac_root / "agents" / "skills"
    loader = SkillLoader(skills_dir)

    try:
        all_skills = loader.load_all()
    except Exception as e:
        console.print(f"[red]Error loading skills:[/red] {e}")
        raise SystemExit(1)

    # Filter skills if specified
    if skill_names:
        skill_name_set = set(skill_names)
        all_skills = [s for s in all_skills if s.name in skill_name_set]
        not_found = skill_name_set - {s.name for s in all_skills}
        if not_found:
            console.print(f"[yellow]Skills not found:[/yellow] {', '.join(not_found)}")

    if not all_skills:
        console.print("[yellow]No skills to export.[/yellow]")
        return

    # Show export plan
    console.print(
        Panel(
            f"[bold]Exporting {len(all_skills)} skill(s) to {len(platform_list)} platform(s)[/bold]",
            title="Skill Export",
        )
    )

    console.print(f"\n[bold]Skills:[/bold] {', '.join(s.name for s in all_skills)}")
    console.print(f"[bold]Platforms:[/bold] {', '.join(platform_list)}")
    console.print(f"[bold]Output:[/bold] {project_root}")

    if dry_run:
        console.print("\n[yellow]Dry run - no files will be created.[/yellow]")
        console.print("\n[bold]Would create:[/bold]")
        platform_dirs = {
            "copilot": ".github/skills",
            "cursor": ".cursor/skills",
            "claude": ".claude/skills",
            "codex": ".codex/skills",
            "rovodev": ".rovodev/subagents",
        }
        for skill in all_skills:
            for p in platform_list:
                if p == "rovodev":
                    console.print(
                        f"  {project_root}/{platform_dirs[p]}/{skill.name}.md"
                    )
                else:
                    console.print(
                        f"  {project_root}/{platform_dirs[p]}/{skill.name}/SKILL.md"
                    )
        return

    # Export skills
    exporter = SkillExporter(all_skills)
    results = exporter.export_all(project_root, platform_list, overwrite)

    # Show results
    console.print("\n[bold]Export Results:[/bold]\n")

    success_count = 0
    error_count = 0

    for result in results:
        if result.all_success:
            console.print(f"[green]OK[/green] {result.skill_name}")
            success_count += 1
        else:
            for platform_name, export_result in result.results.items():
                if export_result.success:
                    console.print(
                        f"  [green]OK[/green] {platform_name}: {export_result.output_path}"
                    )
                else:
                    console.print(
                        f"  [red]FAIL[/red] {platform_name}: {', '.join(export_result.errors)}"
                    )
                    error_count += 1

    console.print(
        f"\n[bold]Summary:[/bold] {success_count} succeeded, {error_count} failed"
    )


@ide.command("skills")
@click.option("--list", "-l", "list_flag", is_flag=True, help="List available skills")
@click.option(
    "--status",
    "-s",
    "status_flag",
    is_flag=True,
    help="Show export status per platform",
)
@click.option(
    "--export", "-e", "export_flag", is_flag=True, help="Export skills to platforms"
)
@click.option(
    "--platform",
    "-p",
    "platforms",
    multiple=True,
    type=click.Choice(SKILL_PLATFORMS + ["all"]),
    help="Target platform(s) for export",
)
@click.option(
    "--skill", "skill_names", multiple=True, help="Specific skill(s) to export"
)
@click.option("--all", "export_all", is_flag=True, help="Export to all platforms")
@click.option("--overwrite", is_flag=True, help="Overwrite existing files")
@click.option("--dry-run", is_flag=True, help="Show what would be exported")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format for list",
)
def ide_skills(
    list_flag: bool,
    status_flag: bool,
    export_flag: bool,
    platforms: tuple[str, ...],
    skill_names: tuple[str, ...],
    export_all: bool,
    overwrite: bool,
    dry_run: bool,
    verbose: bool,
    output_format: str,
) -> None:
    """Export skills to IDE/AI platforms.

    Skills are reusable capabilities that can be assigned to agents
    and exported to multiple IDE/AI platforms.

    \b
    Supported platforms:
    - copilot: GitHub Copilot (.github/skills/)
    - cursor: Cursor (.cursor/skills/)
    - claude: Claude Code (.claude/skills/)
    - codex: OpenAI Codex (.codex/skills/)
    - rovodev: Atlassian Rovo Dev (.rovodev/subagents/)

    \b
    Examples:
        paracle ide skills --list              # List all skills
        paracle ide skills --status            # Show export status
        paracle ide skills --export --all      # Export to all platforms
        paracle ide skills -e -p copilot       # Export to Copilot
        paracle ide skills -e -p cursor -p claude  # Export to multiple
        paracle ide skills -e --skill my-skill # Export specific skill
    """
    if list_flag:
        _skills_list_direct(output_format, verbose)
    elif status_flag:
        _skills_status_direct()
    elif export_flag or export_all or platforms:
        if export_all:
            platforms = tuple(SKILL_PLATFORMS)
        _skills_export_direct(platforms, skill_names, overwrite, dry_run)
    else:
        # Default: show status
        _skills_status_direct()
