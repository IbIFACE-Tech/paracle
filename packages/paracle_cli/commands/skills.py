"""CLI commands for project skill management.

Commands for managing project-level agent skills following the Agent Skills spec:
- list: List project skills
- export: Export skills to multiple platforms
- validate: Validate skill definitions
- create: Create a new skill from template
- show: Show skill details

Project skills are stored in .parac/agents/skills/.

For system-wide framework skills (paracle_meta), use 'paracle meta skills'.

Architecture: Uses paracle_skills package for skill operations.
"""

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from paracle_cli.utils import get_skills_dir

console = Console()


@click.group(invoke_without_command=True)
@click.option(
    "--list",
    "-l",
    "list_skills_flag",
    is_flag=True,
    help="List all available skills (shortcut for 'list')",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed information (with -l)"
)
@click.pass_context
def skills(ctx: click.Context, list_skills_flag: bool, verbose: bool) -> None:
    """Manage agent skills (write once, export anywhere).

    Skills are reusable capabilities that can be assigned to agents
    and exported to multiple AI platforms.

    Supported platforms:
        - GitHub Copilot (.github/skills/)
        - Cursor (.cursor/skills/)
        - Claude Code (.claude/skills/)
        - OpenAI Codex (.codex/skills/)
        - MCP (Model Context Protocol)

    Common commands:
        paracle agents skills -l                - List all skills (shortcut)
        paracle agents skills list              - List all skills
        paracle agents skills export --all      - Export to all platforms
        paracle agents skills create my-skill   - Create new skill

    Examples:
        paracle agents skills -l                - Quick list of all skills
        paracle agents skills -l -v             - Detailed list with descriptions
        paracle agents skills list --format=json
    """
    # Handle -l/--list shortcut
    if list_skills_flag:
        ctx.invoke(list_skills, output_format="table", verbose=verbose)
    elif ctx.invoked_subcommand is None:
        # No subcommand and no flags - show help
        click.echo(ctx.get_help())


@skills.command("list")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
def list_skills(output_format: str, verbose: bool) -> None:
    """List project skills.

    Shows skills from .parac/agents/skills/.

    For system-wide framework skills, use 'paracle meta skills list'.

    Examples:
        paracle agents skills list
        paracle agents skills list --format=json
        paracle agents skills list -v
    """
    from paracle_skills import SkillLoader

    skills_dir = get_skills_dir()
    loader = SkillLoader(skills_dir)

    try:
        skill_list = loader.load_all()
    except Exception as e:
        console.print(f"[red]Error loading skills:[/red] {e}")
        raise SystemExit(1)

    if not skill_list:
        console.print("[yellow]No project skills found.[/yellow]")
        console.print("\nCreate a skill: paracle agents skills create my-skill")
        console.print("System skills: paracle meta skills list")
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
        table = Table(title=f"Project Skills ({len(skill_list)} found)")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Category", style="green")
        table.add_column("Level", style="yellow")
        if verbose:
            table.add_column("Tools", justify="right")
            table.add_column("Description")

        for skill in sorted(skill_list, key=lambda s: s.name):
            row = [
                skill.name,
                skill.metadata.category.value,
                skill.metadata.level.value,
            ]
            if verbose:
                desc = (
                    skill.description[:50] + "..."
                    if len(skill.description) > 50
                    else skill.description
                )
                row.extend([str(len(skill.tools)), desc])
            table.add_row(*row)

        console.print(table)


@skills.command("export")
@click.option(
    "--platform",
    "-p",
    type=click.Choice(["copilot", "cursor", "claude", "codex", "mcp", "all"]),
    multiple=True,
    help="Target platform(s)",
)
@click.option("--all", "export_all", is_flag=True, help="Export to all platforms")
@click.option("--skill", "-s", multiple=True, help="Specific skill(s) to export")
@click.option("--overwrite", is_flag=True, help="Overwrite existing files")
@click.option(
    "--output", "-o", type=click.Path(), help="Output directory (default: project root)"
)
@click.option("--dry-run", is_flag=True, help="Show what would be exported")
@click.pass_context
def export_skills(
    ctx: click.Context,
    platform: tuple[str, ...],
    export_all: bool,
    skill: tuple[str, ...],
    overwrite: bool,
    output: str | None,
    dry_run: bool,
) -> None:
    """Export skills to one or more platforms.

    DEPRECATED: Use 'paracle ide skills --export' instead.

    Exports skill definitions from .parac/agents/skills/ to platform-specific
    formats for GitHub Copilot, Cursor, Claude Code, OpenAI Codex, or MCP.

    Examples:
        paracle ide skills --export --all        # NEW (recommended)
        paracle ide skills -e -p copilot         # NEW (recommended)
        paracle agents skills export --all       # DEPRECATED
    """
    # Show deprecation warning
    console.print(
        "[yellow]DEPRECATED:[/yellow] 'paracle skills export' is deprecated.\n"
        "Use 'paracle ide skills --export' instead.\n"
    )

    from paracle_core.parac.state import find_parac_root
    from paracle_skills import SkillExporter, SkillLoader
    from paracle_skills.exporter import ALL_PLATFORMS

    # Determine platforms
    platforms = list(platform)
    if export_all or "all" in platforms:
        platforms = ALL_PLATFORMS
    elif not platforms:
        console.print("[yellow]No platform specified.[/yellow]")
        console.print("Use --all or -p <platform>")
        console.print(f"\nAvailable platforms: {', '.join(ALL_PLATFORMS)}")
        return

    # Remove 'all' if present
    platforms = [p for p in platforms if p != "all"]

    # Determine output directory
    parac_root = find_parac_root()
    if parac_root is None:
        console.print("[red]Error:[/red] No .parac/ directory found.")
        raise SystemExit(1)

    output_dir = Path(output) if output else parac_root.parent

    # Load skills
    skills_dir = get_skills_dir()
    loader = SkillLoader(skills_dir)

    try:
        all_skills = loader.load_all()
    except Exception as e:
        console.print(f"[red]Error loading skills:[/red] {e}")
        raise SystemExit(1)

    # Filter skills if specified
    if skill:
        skill_names = set(skill)
        all_skills = [s for s in all_skills if s.name in skill_names]
        not_found = skill_names - {s.name for s in all_skills}
        if not_found:
            console.print(f"[yellow]Skills not found:[/yellow] {', '.join(not_found)}")

    if not all_skills:
        console.print("[yellow]No skills to export.[/yellow]")
        return

    # Show export plan
    console.print(
        Panel(
            f"[bold]Exporting {len(all_skills)} skill(s) to {len(platforms)} platform(s)[/bold]",
            title="Skill Export",
        )
    )

    console.print(f"\n[bold]Skills:[/bold] {', '.join(s.name for s in all_skills)}")
    console.print(f"[bold]Platforms:[/bold] {', '.join(platforms)}")
    console.print(f"[bold]Output:[/bold] {output_dir}")

    if dry_run:
        console.print("\n[yellow]Dry run - no files will be created.[/yellow]")
        console.print("\n[bold]Would create:[/bold]")
        for skill in all_skills:
            for p in platforms:
                if p == "mcp":
                    console.print(f"  {output_dir}/.parac/tools/mcp/{skill.name}.json")
                else:
                    platform_dirs = {
                        "copilot": ".github/skills",
                        "cursor": ".cursor/skills",
                        "claude": ".claude/skills",
                        "codex": ".codex/skills",
                    }
                    console.print(
                        f"  {output_dir}/{platform_dirs[p]}/{skill.name}/SKILL.md"
                    )
        return

    # Export skills
    exporter = SkillExporter(all_skills)
    results = exporter.export_all(output_dir, platforms, overwrite)

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


@skills.command("validate")
@click.argument("skill_name", required=False)
@click.option("--all", "validate_all", is_flag=True, help="Validate all skills")
def validate_skill(skill_name: str | None, validate_all: bool) -> None:
    """Validate skill definitions.

    Checks that skills follow the Agent Skills specification
    and have valid SKILL.md files.

    Examples:
        paracle agents skills validate --all
        paracle agents skills validate code-review
    """
    from paracle_skills import SkillLoader

    skills_dir = get_skills_dir()
    loader = SkillLoader(skills_dir)

    if validate_all:
        skill_names = loader.get_skill_names()
    elif skill_name:
        skill_names = [skill_name]
    else:
        console.print("[yellow]Specify a skill name or use --all[/yellow]")
        return

    if not skill_names:
        console.print("[yellow]No skills found to validate.[/yellow]")
        return

    console.print(f"\n[bold]Validating {len(skill_names)} skill(s)...[/bold]\n")

    valid_count = 0
    invalid_count = 0

    for name in skill_names:
        skill_path = skills_dir / name / "SKILL.md"

        if not skill_path.exists():
            console.print(f"[red]MISSING[/red] {name}: SKILL.md not found")
            invalid_count += 1
            continue

        try:
            skill = loader.load_skill(skill_path)
            console.print(f"[green]VALID[/green] {name}")

            # Show warnings
            if len(skill.description) < 20:
                console.print("  [yellow]Warning:[/yellow] Description is very short")
            if not skill.instructions:
                console.print(
                    "  [yellow]Warning:[/yellow] No instructions in SKILL.md body"
                )

            valid_count += 1

        except Exception as e:
            console.print(f"[red]INVALID[/red] {name}: {e}")
            invalid_count += 1

    console.print(
        f"\n[bold]Summary:[/bold] {valid_count} valid, {invalid_count} invalid"
    )


@skills.command("create")
@click.argument("skill_name")
@click.option(
    "--category",
    "-c",
    type=click.Choice(
        [
            "creation",
            "analysis",
            "automation",
            "integration",
            "quality",
            "devops",
            "security",
        ]
    ),
    default="automation",
    help="Skill category",
)
@click.option(
    "--level",
    "-l",
    type=click.Choice(["basic", "intermediate", "advanced", "expert"]),
    default="intermediate",
    help="Skill complexity level",
)
@click.option("--with-scripts", is_flag=True, help="Include scripts/ directory")
@click.option("--with-references", is_flag=True, help="Include references/ directory")
@click.option("--with-assets", is_flag=True, help="Include assets/ directory")
@click.option(
    "--ai-enhance",
    is_flag=True,
    help="Use AI to enhance the skill specification",
)
@click.option(
    "--ai-provider",
    type=click.Choice(["auto", "meta", "openai", "anthropic", "azure"]),
    default="auto",
    help="AI provider to use (requires --ai-enhance)",
)
@click.option(
    "--description",
    "-d",
    help="Description of what the skill does (used with --ai-enhance)",
)
def create_skill(
    skill_name: str,
    category: str,
    level: str,
    with_scripts: bool,
    with_references: bool,
    with_assets: bool,
    ai_enhance: bool,
    ai_provider: str,
    description: str | None,
) -> None:
    """Create a new skill from template, optionally AI-enhanced.

    Creates a new skill with SKILL.md and optional directories.
    With --ai-enhance, uses AI to generate detailed instructions,
    examples, and best practices based on the description.

    Examples:
        # Basic template
        paracle agents skills create code-review

        # AI-enhanced skill (requires AI provider)
        paracle agents skills create api-testing \
            --ai-enhance --description "REST API testing automation"

        # With specific AI provider
        paracle agents skills create security-scan \
            --ai-enhance --ai-provider anthropic \
            --description "Automated security vulnerability scanning"

    Creates a new skill directory with SKILL.md and optional
    scripts/, references/, and assets/ directories.

    Examples:
        paracle agents skills create code-review
        paracle agents skills create my-skill -c quality -l advanced
        paracle agents skills create deploy-automation --with-scripts
    """
    import re

    # Validate skill name
    if not re.match(r"^[a-z][a-z0-9-]*[a-z0-9]$|^[a-z]$", skill_name):
        console.print(
            "[red]Error:[/red] Skill name must be lowercase with hyphens only"
        )
        console.print("Example: code-review, my-skill, automation-tool")
        raise SystemExit(1)

    skills_dir = get_skills_dir()
    skill_dir = skills_dir / skill_name

    if skill_dir.exists():
        console.print(f"[red]Error:[/red] Skill '{skill_name}' already exists")
        raise SystemExit(1)

    # AI enhancement if requested
    ai_generated_content = None
    if ai_enhance:
        if not description:
            console.print("[red]Error:[/red] --description required with --ai-enhance")
            raise SystemExit(1)

        import asyncio

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
            console.print(f"[dim]Generating enhanced skill: {description}[/dim]\n")

            with console.status("[bold cyan]Generating skill spec..."):
                result = asyncio.run(
                    ai.generate_skill(
                        f"Skill Name: {skill_name}\n"
                        f"Category: {category}\nLevel: {level}\n"
                        f"Description: {description}"
                    )
                )

            ai_generated_content = result.get("markdown", "")
            console.print("[green]✓[/green] AI-enhanced skill spec generated")

    # Create skill directory
    skill_dir.mkdir(parents=True)

    # Create optional directories
    if with_scripts:
        (skill_dir / "scripts").mkdir()
        (skill_dir / "scripts" / ".gitkeep").write_text("")

    if with_references:
        (skill_dir / "references").mkdir()
        (skill_dir / "references" / ".gitkeep").write_text("")

    if with_assets:
        (skill_dir / "assets").mkdir()
        (skill_dir / "assets" / ".gitkeep").write_text("")

    # Generate SKILL.md content
    # Use AI-generated content if available, otherwise use template
    if ai_generated_content:
        skill_md_content = ai_generated_content
    else:
        display_name = skill_name.replace("-", " ").title()

        skill_md_content = f"""---
name: {skill_name}
description: {display_name} skill. Use when [describe when to use this skill].
license: Apache-2.0
compatibility: Python 3.10+
metadata:
  author: your-name
  version: "1.0.0"
  category: {category}
  level: {level}
  display_name: "{display_name}"
  tags:
    - {skill_name.split("-")[0]}
  capabilities:
    - capability_1
    - capability_2
---

# {display_name}

## When to use this skill

Use this skill when:
- [Condition 1]
- [Condition 2]
- [Condition 3]

## Quick start

[Provide a quick example or command]

## Instructions

### Step 1: [First step]

[Detailed instructions]

### Step 2: [Second step]

[Detailed instructions]

## Best practices

1. [Best practice 1]
2. [Best practice 2]
3. [Best practice 3]

## Related skills

- [related-skill-1](../related-skill-1/)
- [related-skill-2](../related-skill-2/)
"""

    (skill_dir / "SKILL.md").write_text(skill_md_content, encoding="utf-8")

    console.print(f"\n[green]OK[/green] Created skill: {skill_name}")
    console.print(f"\n[bold]Location:[/bold] {skill_dir}")
    console.print("\n[bold]Files created:[/bold]")
    console.print("  + SKILL.md")
    if with_scripts:
        console.print("  + scripts/")
    if with_references:
        console.print("  + references/")
    if with_assets:
        console.print("  + assets/")

    console.print("\n[bold]Next steps:[/bold]")
    console.print(f"  1. Edit {skill_dir / 'SKILL.md'}")
    console.print(f"  2. paracle agents skills validate {skill_name}")
    console.print(f"  3. paracle agents skills export -p copilot -s {skill_name}")


@skills.command("show")
@click.argument("skill_name")
@click.option("--raw", is_flag=True, help="Show raw SKILL.md content")
def show_skill(skill_name: str, raw: bool) -> None:
    """Show details for a project skill.

    For system skills, use 'paracle meta skills show'.

    Examples:
        paracle agents skills show code-review
        paracle agents skills show my-skill --raw
    """
    from paracle_skills import SkillLoader

    skills_dir = get_skills_dir()
    skill_path = skills_dir / skill_name / "SKILL.md"

    if not skill_path.exists():
        console.print(f"[red]Error:[/red] Skill '{skill_name}' not found")
        console.print(f"\nSearched: {skills_dir / skill_name}")
        console.print("\nFor system skills: paracle meta skills show <name>")
        raise SystemExit(1)

    if raw:
        console.print(skill_path.read_text(encoding="utf-8"))
        return

    loader = SkillLoader(skills_dir)

    try:
        skill = loader.load_skill(skill_path)
    except Exception as e:
        console.print(f"[red]Error loading skill:[/red] {e}")
        raise SystemExit(1)

    # Display skill info
    console.print(
        Panel(
            f"[bold cyan]{skill.metadata.display_name or skill.name}[/bold cyan]",
            title="Project Skill",
        )
    )

    console.print(f"\n[bold]Name:[/bold] {skill.name}")
    console.print(f"[bold]Description:[/bold] {skill.description}")
    console.print(f"[bold]Category:[/bold] {skill.metadata.category.value}")
    console.print(f"[bold]Level:[/bold] {skill.metadata.level.value}")

    if skill.metadata.tags:
        console.print(f"[bold]Tags:[/bold] {', '.join(skill.metadata.tags)}")

    if skill.metadata.capabilities:
        console.print("\n[bold]Capabilities:[/bold]")
        for cap in skill.metadata.capabilities:
            console.print(f"  - {cap}")

    if skill.tools:
        console.print(f"\n[bold]Tools ({len(skill.tools)}):[/bold]")
        for tool in skill.tools:
            tool_desc = tool.description
            if len(tool_desc) > 50:
                tool_desc = tool_desc[:50] + "..."
            console.print(f"  - {tool.name}: {tool_desc}")

    if skill.allowed_tools:
        console.print(f"\n[bold]Allowed Tools:[/bold] {skill.allowed_tools}")

    console.print(f"\n[bold]Path:[/bold] {skill.source_path}")
