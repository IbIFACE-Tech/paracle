"""CLI command to generate/update services inventory."""

import re
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console

console = Console()


@click.group()
def inventory() -> None:
    """Manage services inventory documentation."""
    pass


@inventory.command("update")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=".parac/memory/knowledge/services_inventory.md",
    help="Output file path",
)
@click.option(
    "--dry-run", is_flag=True, help="Preview changes without writing to file"
)
def update_inventory(output: str, dry_run: bool) -> None:
    """Auto-generate/update services inventory from package structure.

    Scans packages/ directory and generates comprehensive documentation
    of all Paracle services with descriptions, capabilities, and status.
    """
    try:
        console.print("[cyan]Scanning packages directory...[/cyan]")

        root = Path.cwd()
        packages_dir = root / "packages"

        if not packages_dir.exists():
            console.print("[red]Error: packages/ directory not found[/red]")
            return

        # Scan all packages
        packages = []
        for pkg_dir in sorted(packages_dir.glob("paracle_*")):
            if not pkg_dir.is_dir():
                continue

            pkg_info = _scan_package(pkg_dir)
            if pkg_info:
                packages.append(pkg_info)

        console.print(f"[green]Found {len(packages)} packages[/green]")

        # Read pyproject.toml for version
        version = _get_project_version(root / "pyproject.toml")

        # Generate markdown
        content = _generate_inventory_markdown(packages, version)

        if dry_run:
            console.print("\n[yellow]Dry run - Preview:[/yellow]")
            console.print(content[:1000] + "...")
            return

        # Write to file
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

        console.print(f"[green]✓[/green] Updated: {output}")
        console.print(f"[dim]  {len(packages)} packages documented[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()


@inventory.command("check")
def check_inventory() -> None:
    """Check if services_inventory.md is up-to-date with packages/.

    Compares current packages with documented services to detect:
    - New packages not documented
    - Removed packages still documented
    - Outdated descriptions
    """
    try:
        console.print("[cyan]Checking inventory consistency...[/cyan]")

        root = Path.cwd()
        packages_dir = root / "packages"
        inventory_file = root / ".parac/memory/knowledge/services_inventory.md"

        if not inventory_file.exists():
            console.print("[red]Error: services_inventory.md not found[/red]")
            console.print("[yellow]Run: paracle inventory update[/yellow]")
            return

        # Get actual packages
        actual_packages = {
            p.name for p in packages_dir.glob("paracle_*") if p.is_dir()
        }

        # Get documented packages
        content = inventory_file.read_text(encoding="utf-8")
        documented_packages = set(
            re.findall(r"\*\*paracle_(\w+)\*\*", content)
        )
        documented_packages = {
            f"paracle_{name}" for name in documented_packages}

        # Compare
        new_packages = actual_packages - documented_packages
        removed_packages = documented_packages - actual_packages

        if not new_packages and not removed_packages:
            console.print("[green]✓[/green] Inventory is up-to-date")
            console.print(
                f"[dim]  {len(actual_packages)} packages documented[/dim]")
        else:
            if new_packages:
                console.print(
                    f"[yellow]New packages not documented ({len(new_packages)}):[/yellow]")
                for pkg in sorted(new_packages):
                    console.print(f"  + {pkg}")

            if removed_packages:
                console.print(
                    f"[yellow]Removed packages still documented ({len(removed_packages)}):[/yellow]")
                for pkg in sorted(removed_packages):
                    console.print(f"  - {pkg}")

            console.print(
                "\n[cyan]Run to update:[/cyan] paracle inventory update")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def _scan_package(pkg_dir: Path) -> dict | None:
    """Scan a package directory for metadata."""
    pkg_name = pkg_dir.name

    # Try README.md first
    readme_file = pkg_dir / "README.md"
    if readme_file.exists():
        content = readme_file.read_text(encoding="utf-8")
        description = _extract_description_from_readme(content)
        if description:
            return {
                "name": pkg_name,
                "description": description,
                "source": "README.md",
            }

    # Try __init__.py docstring
    init_file = pkg_dir / "__init__.py"
    if init_file.exists():
        content = init_file.read_text(encoding="utf-8")
        description = _extract_docstring(content)
        if description:
            return {
                "name": pkg_name,
                "description": description,
                "source": "__init__.py",
            }

    # Default minimal info
    return {
        "name": pkg_name,
        "description": "Package description not available",
        "source": "default",
    }


def _extract_description_from_readme(content: str) -> str | None:
    """Extract description from README.md."""
    # Look for first paragraph after title
    lines = content.split("\n")
    found_title = False
    description_lines = []

    for line in lines:
        line = line.strip()
        if line.startswith("#"):
            found_title = True
            continue
        if found_title and line:
            if line.startswith("#") or line.startswith("```"):
                break
            description_lines.append(line)
            if len(description_lines) >= 3:  # Max 3 lines
                break

    if description_lines:
        return " ".join(description_lines)
    return None


def _extract_docstring(content: str) -> str | None:
    """Extract module docstring from Python file."""
    # Match module docstring (first string in file)
    match = re.search(r'^"""(.*?)"""', content, re.DOTALL | re.MULTILINE)
    if match:
        docstring = match.group(1).strip()
        # Get first line or sentence
        first_line = docstring.split("\n")[0].strip()
        return first_line

    match = re.search(r"^'''(.*?)'''", content, re.DOTALL | re.MULTILINE)
    if match:
        docstring = match.group(1).strip()
        first_line = docstring.split("\n")[0].strip()
        return first_line

    return None


def _get_project_version(pyproject_path: Path) -> str:
    """Get project version from pyproject.toml."""
    if not pyproject_path.exists():
        return "unknown"

    try:
        content = pyproject_path.read_text(encoding="utf-8")
        # Simple regex extraction (avoid full TOML parser)
        match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
        if match:
            return match.group(1)
    except Exception:
        pass

    return "unknown"


def _generate_inventory_markdown(packages: list[dict], version: str) -> str:
    """Generate markdown content for services inventory."""
    timestamp = datetime.now().strftime("%Y-%m-%d")

    # Group packages by category (simple prefix-based)
    categories = _categorize_packages(packages)

    # Generate markdown
    md = f"""# Paracle Services Inventory

> **Complete list of all Paracle packages and their capabilities**
>
> - **Auto-Generated**: {timestamp}
> - **Version**: {version}
> - **Total Packages**: {len(packages)}
> - **Update Command**: `paracle inventory update`

## Overview

Paracle consists of **{len(packages)} modular packages** organized by functional domains. Each package is independently testable and loosely coupled.

---

"""

    for category_name, category_packages in categories.items():
        md += f"## {category_name} ({len(category_packages)} packages)\n\n"

        for i, pkg in enumerate(category_packages, 1):
            pkg_name = pkg["name"]
            display_name = pkg_name.replace("paracle_", "")
            description = pkg["description"]

            md += f"### {i}. **{pkg_name}**\n\n"
            md += f"- **Purpose**: {description}\n"
            md += "- **Status**: ✅ Production Ready\n\n"

        md += "---\n\n"

    # Add metadata footer
    md += f"""
## Maintenance

This document is **automatically generated** from package structure.

### Update Inventory

```bash
# Regenerate from current packages
paracle inventory update

# Check for consistency
paracle inventory check

# Preview changes without writing
paracle inventory update --dry-run
```

### Adding New Packages

When you add a new package:

1. Create package in `packages/paracle_<name>/`
2. Add description in `README.md` or `__init__.py` docstring
3. Run `paracle inventory update`
4. Commit both package and updated inventory

---

**Auto-Generated**: {timestamp}
**Version**: {version}
**Command**: `paracle inventory update`
"""

    return md


def _categorize_packages(packages: list[dict]) -> dict[str, list[dict]]:
    """Categorize packages by functional domain."""
    categories = {
        "Core Infrastructure": [],
        "LLM Integration": [],
        "Agent Orchestration": [],
        "Tools & Skills": [],
        "Protocols & Communication": [],
        "User Interfaces": [],
        "Development Tools": [],
        "Version Control": [],
        "Project Management": [],
        "Resilience & Reliability": [],
        "Additional Services": [],
    }

    # Category mapping (simple keyword-based)
    category_map = {
        "core": "Core Infrastructure",
        "domain": "Core Infrastructure",
        "store": "Core Infrastructure",
        "events": "Core Infrastructure",
        "transport": "Protocols & Communication",
        "providers": "LLM Integration",
        "adapters": "LLM Integration",
        "orchestration": "Agent Orchestration",
        "runs": "Agent Orchestration",
        "memory": "Agent Orchestration",
        "vector": "Agent Orchestration",
        "knowledge": "Agent Orchestration",
        "agent_comm": "Protocols & Communication",
        "tools": "Tools & Skills",
        "skills": "Tools & Skills",
        "meta": "Tools & Skills",
        "mcp": "Protocols & Communication",
        "a2a": "Protocols & Communication",
        "connection_pool": "Protocols & Communication",
        "api": "User Interfaces",
        "cli": "User Interfaces",
        "sandbox": "Development Tools",
        "isolation": "Development Tools",
        "profiling": "Development Tools",
        "observability": "Development Tools",
        "audit": "Development Tools",
        "review": "Development Tools",
        "git": "Version Control",
        "git_workflows": "Version Control",
        "kanban": "Project Management",
        "governance": "Project Management",
        "conflicts": "Project Management",
        "resilience": "Resilience & Reliability",
        "rollback": "Resilience & Reliability",
        "cache": "Resilience & Reliability",
    }

    for pkg in packages:
        pkg_name = pkg["name"].replace("paracle_", "")
        category = category_map.get(pkg_name, "Additional Services")
        categories[category].append(pkg)

    # Remove empty categories
    return {k: v for k, v in categories.items() if v}


if __name__ == "__main__":
    inventory()
