"""Configuration management commands.

Commands for managing Paracle project configuration.
"""

from pathlib import Path
from typing import Any

import click
import yaml
from paracle_core.parac.file_config import FileManagementConfig
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

console = Console()


@click.group()
def config() -> None:
    """Manage project configuration.

    Commands for viewing, validating, and managing split configuration files.

    Examples:
        paracle config show              - Show effective configuration
        paracle config validate          - Validate configuration
        paracle config show --format json - Show config as JSON
    """
    pass


@config.command()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["yaml", "json", "table"]),
    default="yaml",
    help="Output format",
)
@click.option(
    "--section",
    "-s",
    type=click.Choice(["all", "logs", "adr", "roadmap"]),
    default="all",
    help="Show specific section only",
)
@click.option(
    "--parac-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Path to .parac/ directory (default: current directory)",
)
def show(format: str, section: str, parac_root: Path | None) -> None:
    """Show effective configuration after merging includes.

    This shows the final configuration after processing all include
    directives and merging optional config files.

    Examples:
        paracle config show
        paracle config show --format json
        paracle config show --section logs
        paracle config show --parac-root /path/to/.parac
    """
    try:
        # Find .parac/ directory
        if parac_root is None:
            parac_root = Path.cwd() / ".parac"
            if not parac_root.exists():
                console.print("[red]Error: .parac/ directory not found[/red]")
                console.print(
                    "Run this command from a Paracle project root, "
                    "or use --parac-root"
                )
                raise click.Abort()

        # Load configuration
        try:
            config = FileManagementConfig.from_project_yaml(parac_root)
        except Exception as e:
            console.print(f"[red]Error loading configuration: {e}[/red]")
            raise click.Abort()

        # Build configuration dict
        config_dict: dict[str, Any] = {}

        if section in ["all", "logs"]:
            config_dict["logs"] = {
                "base_path": config.logs.base_path,
                "global": {
                    "max_line_length": config.logs.global_config.max_line_length,
                    "max_file_size_mb": config.logs.global_config.max_file_size_mb,
                    "async_logging": config.logs.global_config.async_logging,
                },
                "predefined": {
                    "actions": {
                        "enabled": config.logs.predefined.actions.enabled,
                        "path": config.logs.predefined.actions.path,
                    },
                    "decisions": {
                        "enabled": config.logs.predefined.decisions.enabled,
                        "path": config.logs.predefined.decisions.path,
                    },
                },
            }

        if section in ["all", "adr"]:
            config_dict["adr"] = {
                "enabled": config.adr.enabled,
                "base_path": config.adr.base_path,
                "limits": {
                    "max_title_length": config.adr.limits.max_title_length,
                    "max_total_length": config.adr.limits.max_total_length,
                },
            }

        if section in ["all", "roadmap"]:
            config_dict["roadmap"] = {
                "base_path": config.roadmap.base_path,
                "primary": config.roadmap.primary,
                "limits": {
                    "max_phase_name_length": (
                        config.roadmap.limits.max_phase_name_length
                    ),
                    "max_phases": config.roadmap.limits.max_phases,
                },
            }

        # Display configuration
        if format == "yaml":
            yaml_str = yaml.dump(config_dict, default_flow_style=False, sort_keys=False)
            syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=False)
            console.print(
                Panel(syntax, title="Effective Configuration", border_style="cyan")
            )

        elif format == "json":
            import json

            json_str = json.dumps(config_dict, indent=2)
            syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
            console.print(
                Panel(syntax, title="Effective Configuration", border_style="cyan")
            )

        elif format == "table":
            table = Table(title="Effective Configuration", show_header=True)
            table.add_column("Section", style="cyan")
            table.add_column("Key", style="yellow")
            table.add_column("Value", style="green")

            def add_rows(d: dict, prefix: str = "") -> None:
                for key, value in d.items():
                    full_key = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, dict):
                        add_rows(value, full_key)
                    else:
                        parts = full_key.split(".", 1)
                        section_name = parts[0]
                        key_name = parts[1] if len(parts) > 1 else ""
                        table.add_row(section_name, key_name, str(value))

            add_rows(config_dict)
            console.print(table)

        # Show include information
        project_yaml = parac_root / "project.yaml"
        if project_yaml.exists():
            with open(project_yaml, encoding="utf-8") as f:
                project_data = yaml.safe_load(f) or {}

            includes = project_data.get("include", [])
            if includes:
                console.print("\n[dim]Includes:[/dim]")
                for include in includes:
                    include_file = parac_root / include
                    status = "✓" if include_file.exists() else "✗"
                    console.print(f"  {status} {include}")

    except click.Abort:
        raise
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise click.Abort()


@config.command()
@click.option(
    "--parac-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Path to .parac/ directory",
)
def validate(parac_root: Path | None) -> None:
    """Validate project configuration files.

    Checks:
    - project.yaml exists and is valid YAML
    - Include files exist and are valid
    - Configuration values are within allowed ranges
    - Required fields are present

    Examples:
        paracle config validate
        paracle config validate --parac-root /path/to/.parac
    """
    try:
        # Find .parac/ directory
        if parac_root is None:
            parac_root = Path.cwd() / ".parac"
            if not parac_root.exists():
                console.print("[red]Error: .parac/ directory not found[/red]")
                raise click.Abort()

        errors = []
        warnings = []

        # Check project.yaml exists
        project_yaml = parac_root / "project.yaml"
        if not project_yaml.exists():
            errors.append("project.yaml not found")
            console.print("[red]✗ Validation failed[/red]")
            console.print("\n[red]Errors:[/red]")
            console.print(f"  • {errors[0]}")
            raise click.Abort()

        # Validate YAML syntax
        try:
            with open(project_yaml, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            errors.append(f"Invalid YAML syntax: {e}")

        if not errors:
            # Check includes
            includes = data.get("include", [])
            for include in includes:
                include_file = parac_root / include
                if not include_file.exists():
                    warnings.append(f"Include file not found: {include}")
                else:
                    # Validate include file syntax
                    try:
                        with open(include_file, encoding="utf-8") as f:
                            yaml.safe_load(f)
                    except yaml.YAMLError as e:
                        errors.append(f"Invalid YAML in {include}: {e}")

            # Try to load configuration
            try:
                config = FileManagementConfig.from_project_yaml(parac_root)

                # Validate ranges
                if config.logs.global_config.max_line_length > 10000:
                    warnings.append("logs.global.max_line_length > 10000 (very large)")

                if config.logs.global_config.max_file_size_mb > 1000:
                    warnings.append(
                        "logs.global.max_file_size_mb > 1000 MB (very large)"
                    )

                if config.adr.limits.max_total_length > 50000:
                    warnings.append("adr.limits.max_total_length > 50000 (very large)")

            except Exception as e:
                errors.append(f"Failed to load configuration: {e}")

        # Display results
        if errors:
            console.print("[red]✗ Validation failed[/red]")
            console.print(f"\n[red]Errors ({len(errors)}):[/red]")
            for error in errors:
                console.print(f"  • {error}")
        else:
            console.print("[green]✓ Configuration is valid[/green]")

        if warnings:
            console.print(f"\n[yellow]Warnings ({len(warnings)}):[/yellow]")
            for warning in warnings:
                console.print(f"  • {warning}")

        if not errors:
            console.print("\n[dim]Configuration loaded successfully[/dim]")
            if includes:
                console.print(f"[dim]Includes: {len(includes)} file(s)[/dim]")

    except click.Abort:
        raise
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise click.Abort()


@config.command()
@click.option(
    "--parac-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Path to .parac/ directory",
)
def files(parac_root: Path | None) -> None:
    """List configuration files and their status.

    Shows:
    - Base configuration file (project.yaml)
    - Included configuration files
    - File sizes and modification times
    - Include status (loaded/skipped)

    Examples:
        paracle config files
        paracle config files --parac-root /path/to/.parac
    """
    try:
        # Find .parac/ directory
        if parac_root is None:
            parac_root = Path.cwd() / ".parac"
            if not parac_root.exists():
                console.print("[red]Error: .parac/ directory not found[/red]")
                raise click.Abort()

        # Create table
        table = Table(title="Configuration Files", show_header=True)
        table.add_column("File", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Size", style="yellow")
        table.add_column("Type", style="blue")

        # Main project.yaml
        project_yaml = parac_root / "project.yaml"
        if project_yaml.exists():
            size = project_yaml.stat().st_size
            size_str = f"{size:,} bytes"
            table.add_row("project.yaml", "✓ Loaded", size_str, "Base")
        else:
            table.add_row("project.yaml", "✗ Missing", "-", "Base")

        # Check for includes
        if project_yaml.exists():
            with open(project_yaml, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            includes = data.get("include", [])
            if includes:
                for include in includes:
                    include_file = parac_root / include
                    if include_file.exists():
                        size = include_file.stat().st_size
                        size_str = f"{size:,} bytes"
                        table.add_row(include, "✓ Loaded", size_str, "Include")
                    else:
                        table.add_row(include, "✗ Missing", "-", "Include")

        console.print(table)

        # Summary
        total_files = len(table.rows)
        loaded = sum(1 for row in table.rows if row._cells[1] == "✓ Loaded")
        console.print(f"\n[dim]Total: {total_files} files, {loaded} loaded[/dim]")

    except click.Abort:
        raise
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise click.Abort()


if __name__ == "__main__":
    config()
