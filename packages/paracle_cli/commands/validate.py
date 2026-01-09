"""Governance validation commands for Paracle.

This module provides commands to validate:
- AI instruction files (.cursorrules, copilot-instructions.md, etc.)
- .parac/ structure and consistency
- Roadmap alignment
- ADR numbering
"""

import re
import sys
from pathlib import Path

import click
import yaml


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


class GovernanceValidator:
    """Validator for Paracle governance structures."""

    def __init__(self, root: Path = None):
        self.root = root or Path.cwd()
        self.parac = self.root / ".parac"
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str):
        """Add an error message."""
        self.errors.append(f"[ERR] {message}")

    def warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(f"[!] {message}")

    def success(self, message: str):
        """Print success message."""
        click.echo(f"[OK] {message}")

    def validate_ai_instructions(self) -> bool:
        """Validate AI instruction files have pre-flight checklist."""
        click.echo("Validating AI instruction files...")

        ide_files = [
            self.root / ".cursorrules",
            self.parac / "integrations/ide/.clinerules",
            self.parac / "integrations/ide/.windsurfrules",
            self.parac / "integrations/ide/CLAUDE.md",
            self.root / ".github/copilot-instructions.md",
        ]

        # Required sections - some have alternatives (tuple means any one must be present)
        required_sections = [
            ("MANDATORY: Pre-Flight Checklist", "MANDATORY PRE-FLIGHT CHECKLIST"),
            "PRE_FLIGHT_CHECKLIST.md",
            "VALIDATE",
            "If Task NOT in Roadmap",
        ]

        for file_path in ide_files:
            if not file_path.exists():
                self.warning(f"File not found: {file_path.relative_to(self.root)}")
                continue

            content = file_path.read_text(encoding="utf-8")
            missing = []

            for section in required_sections:
                if isinstance(section, tuple):
                    # Any one of the alternatives must be present
                    if not any(alt in content for alt in section):
                        missing.append(section[0])  # Report first alternative
                elif section not in content:
                    missing.append(section)

            if missing:
                self.error(
                    f"{file_path.relative_to(self.root)} missing sections: {', '.join(missing)}"
                )
            else:
                self.success(f"{file_path.name} has all required sections")

        return len(self.errors) == 0

    def validate_governance_structure(self) -> bool:
        """Validate .parac/ directory structure."""
        click.echo("\nValidating .parac/ structure...")

        required_files = [
            "GOVERNANCE.md",
            "PRE_FLIGHT_CHECKLIST.md",
            "manifest.yaml",
            "project.yaml",
            "roadmap/roadmap.yaml",
            "roadmap/decisions.md",
            "memory/context/current_state.yaml",
            "memory/context/open_questions.md",
            "memory/logs/agent_actions.log",
            "agents/manifest.yaml",
        ]

        required_dirs = [
            "agents/specs",
            "memory/context",
            "memory/knowledge",
            "memory/logs",
            "roadmap",
            "policies",
            "integrations/ide",
        ]

        # Check files
        for file_rel in required_files:
            file_path = self.parac / file_rel
            if not file_path.exists():
                self.error(f"Missing required file: .parac/{file_rel}")
            else:
                self.success(f"Found: {file_rel}")

        # Check directories
        for dir_rel in required_dirs:
            dir_path = self.parac / dir_rel
            if not dir_path.exists():
                self.error(f"Missing required directory: .parac/{dir_rel}")
            else:
                self.success(f"Found directory: {dir_rel}")

        return len(self.errors) == 0

    def validate_roadmap_consistency(self) -> bool:
        """Validate roadmap and current_state are consistent."""
        click.echo("\nValidating roadmap consistency...")

        roadmap_path = self.parac / "roadmap/roadmap.yaml"
        state_path = self.parac / "memory/context/current_state.yaml"

        if not roadmap_path.exists():
            self.error("roadmap.yaml not found")
            return False

        if not state_path.exists():
            self.error("current_state.yaml not found")
            return False

        try:
            roadmap = yaml.safe_load(roadmap_path.read_text(encoding="utf-8"))
            state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            self.error(f"YAML parsing error: {e}")
            return False

        # Check phase alignment
        roadmap_phase = roadmap.get("current_phase")
        state_phase = state.get("current_phase", {}).get("id")

        if roadmap_phase != state_phase:
            self.error(
                f"Phase mismatch: roadmap has '{roadmap_phase}' but "
                f"current_state has '{state_phase}'"
            )
        else:
            self.success(f"Phase aligned: {state_phase}")

        # Check progress is reasonable
        progress_str = state.get("current_phase", {}).get("progress", "0")
        try:
            # Remove % if present and convert to int
            progress = int(str(progress_str).rstrip("%"))
            if not (0 <= progress <= 100):
                self.error(f"Invalid progress: {progress}% (must be 0-100)")
            else:
                self.success(f"Progress valid: {progress}%")
        except ValueError:
            self.error(f"Invalid progress format: {progress_str}")

        return len(self.errors) == 0

    def validate_yaml_syntax(self) -> bool:
        """Validate all YAML files in .parac/ have valid syntax."""
        click.echo("\nValidating YAML syntax...")

        yaml_files = list(self.parac.rglob("*.yaml")) + list(self.parac.rglob("*.yml"))

        for yaml_path in yaml_files:
            # Skip snapshots, logs, templates (Jinja2), assets, and IDE rules (markdown content)
            if (
                "snapshots" in yaml_path.parts
                or "logs" in yaml_path.parts
                or "assets" in yaml_path.parts
                or "template" in yaml_path.name.lower()
                or yaml_path.name in ("ai-rules.yaml", "rules.yaml")
            ):
                continue

            try:
                yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
                self.success(f"Valid YAML: {yaml_path.relative_to(self.parac)}")
            except yaml.YAMLError as e:
                self.error(f"Invalid YAML in {yaml_path.relative_to(self.parac)}: {e}")

        return len(self.errors) == 0

    def validate_adr_numbering(self) -> bool:
        """Validate ADR numbers are sequential."""
        click.echo("\nValidating ADR numbering...")

        decisions_path = self.parac / "roadmap/decisions.md"
        if not decisions_path.exists():
            self.error("decisions.md not found")
            return False

        content = decisions_path.read_text(encoding="utf-8")
        adr_numbers = re.findall(r"## ADR-(\d+):", content)
        adr_numbers = sorted([int(n) for n in adr_numbers])

        if not adr_numbers:
            self.warning("No ADRs found in decisions.md")
            return True

        # Check sequential - warn if gaps exist but don't fail
        expected = list(range(1, max(adr_numbers) + 1))
        missing = set(expected) - set(adr_numbers)
        if missing:
            self.warning(f"ADR numbering has gaps. Missing: {sorted(missing)}")
        self.success(f"ADR numbering: {len(adr_numbers)} ADRs found")

        return len(self.errors) == 0

    def report(self) -> bool:
        """Print validation report and return success status."""
        click.echo("\n" + "=" * 60)

        if self.warnings:
            click.echo("\nWarnings:")
            for warning in self.warnings:
                click.echo(f"  {warning}")

        if self.errors:
            click.echo("\nErrors:")
            for error in self.errors:
                click.echo(f"  {error}")
            click.echo(f"\n[FAIL] Validation failed with {len(self.errors)} error(s)")
            return False
        else:
            click.echo("\n[PASS] All validations passed!")
            return True


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--all", "run_all", is_flag=True, help="Run all validation checks")
def validate(ctx, run_all):
    """Validate governance compliance and structure."""
    if run_all:
        validator = GovernanceValidator()
        validator.validate_ai_instructions()
        validator.validate_governance_structure()
        validator.validate_roadmap_consistency()
        validator.validate_yaml_syntax()
        validator.validate_adr_numbering()
        success = validator.report()
        sys.exit(0 if success else 1)
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@validate.command("ai-instructions")
def validate_ai_instructions():
    """Validate AI instruction files have pre-flight checklist.

    Checks:
    - .cursorrules
    - .parac/integrations/ide/.clinerules
    - .parac/integrations/ide/.windsurfrules
    - .parac/integrations/ide/CLAUDE.md
    - .github/copilot-instructions.md

    Ensures each file contains:
    - MANDATORY PRE-FLIGHT CHECKLIST section
    - Reference to PRE_FLIGHT_CHECKLIST.md
    - VALIDATE section
    - "If Task NOT in Roadmap" section
    """
    validator = GovernanceValidator()
    validator.validate_ai_instructions()

    success = validator.report()
    sys.exit(0 if success else 1)


@validate.command("governance")
def validate_governance():
    """Validate .parac/ directory structure and files.

    Checks:
    - Required files exist (GOVERNANCE.md, manifest.yaml, etc.)
    - Required directories exist (agents/, memory/, roadmap/, etc.)
    - YAML files have valid syntax
    """
    validator = GovernanceValidator()
    validator.validate_governance_structure()
    validator.validate_yaml_syntax()

    success = validator.report()
    sys.exit(0 if success else 1)


@validate.command("roadmap")
def validate_roadmap():
    """Validate roadmap consistency.

    Checks:
    - current_state.yaml phase matches roadmap.yaml
    - Progress percentage is valid (0-100)
    - ADR numbering is sequential
    """
    validator = GovernanceValidator()
    validator.validate_roadmap_consistency()
    validator.validate_adr_numbering()

    success = validator.report()
    sys.exit(0 if success else 1)
