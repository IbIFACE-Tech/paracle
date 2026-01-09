"""Agent specification validator.

Validates agent specs against the schema defined in schema.py.
This is the enforcement mechanism for the agent spec structure.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from paracle_core.agents.schema import ParacPaths


class ValidationSeverity(Enum):
    """Severity level for validation issues."""

    ERROR = "error"  # Must fix - spec is invalid
    WARNING = "warning"  # Should fix - spec may not work correctly
    INFO = "info"  # Suggestion for improvement


@dataclass
class ValidationError:
    """A single validation error or warning."""

    message: str
    severity: ValidationSeverity
    section: Optional[str] = None
    line: Optional[int] = None
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        prefix = f"[{self.severity.value.upper()}]"
        location = f" in '{self.section}'" if self.section else ""
        line_info = f" (line {self.line})" if self.line else ""
        suggestion = f"\n  Suggestion: {self.suggestion}" if self.suggestion else ""
        return f"{prefix}{location}{line_info}: {self.message}{suggestion}"


@dataclass
class ValidationResult:
    """Result of validating an agent spec."""

    valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    agent_id: Optional[str] = None
    spec_path: Optional[str] = None

    @property
    def error_count(self) -> int:
        """Count of errors (not warnings or info)."""
        return sum(1 for e in self.errors if e.severity == ValidationSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        """Count of warnings."""
        return sum(1 for e in self.errors if e.severity == ValidationSeverity.WARNING)

    def __str__(self) -> str:
        if self.valid:
            status = "VALID"
        else:
            status = "INVALID"

        header = f"Validation {status}"
        if self.agent_id:
            header += f" for '{self.agent_id}'"

        lines = [header]
        lines.append(f"  Errors: {self.error_count}, Warnings: {self.warning_count}")

        for error in self.errors:
            lines.append(f"  {error}")

        return "\n".join(lines)


class AgentSpecValidator:
    """Validates agent specification markdown files.

    Uses the schema from schema.py to check that specs have:
    - All required sections
    - Governance integration with .parac/ paths
    - Valid structure
    """

    # Required sections (must exist)
    REQUIRED_SECTIONS = [
        "Role",
        "Governance Integration",
        "Skills",
        "Responsibilities",
    ]

    # Optional sections (checked if present)
    OPTIONAL_SECTIONS = [
        "Tools & Capabilities",
        "Expertise Areas",
        "Examples",
        "Coding Standards",
    ]

    # Required .parac/ paths that must be referenced
    REQUIRED_PARAC_REFS = [
        ParacPaths.CURRENT_STATE,
        ParacPaths.ROADMAP,
        ParacPaths.ACTION_LOG,
    ]

    def __init__(self, strict: bool = False):
        """Initialize validator.

        Args:
            strict: If True, warnings become errors
        """
        self.strict = strict

    def validate_file(self, spec_path: Path) -> ValidationResult:
        """Validate an agent spec file.

        Args:
            spec_path: Path to the markdown spec file

        Returns:
            ValidationResult with errors/warnings
        """
        if not spec_path.exists():
            return ValidationResult(
                valid=False,
                errors=[
                    ValidationError(
                        message=f"File not found: {spec_path}",
                        severity=ValidationSeverity.ERROR,
                    )
                ],
                spec_path=str(spec_path),
            )

        content = spec_path.read_text(encoding="utf-8")
        agent_id = spec_path.stem

        # Skip generated files
        if agent_id.upper() in ("SCHEMA", "TEMPLATE"):
            return ValidationResult(
                valid=True,
                agent_id=agent_id,
                spec_path=str(spec_path),
            )

        return self.validate_content(content, agent_id, str(spec_path))

    def validate_content(
        self,
        content: str,
        agent_id: Optional[str] = None,
        spec_path: Optional[str] = None,
    ) -> ValidationResult:
        """Validate agent spec content.

        Args:
            content: Markdown content of the spec
            agent_id: Agent identifier (for error messages)
            spec_path: Path to spec file (for error messages)

        Returns:
            ValidationResult with errors/warnings
        """
        errors: list[ValidationError] = []

        # Parse sections
        sections = self._parse_sections(content)

        # Check title (H1)
        errors.extend(self._check_title(content, agent_id))

        # Check required sections
        errors.extend(self._check_required_sections(sections))

        # Check governance section specifically
        errors.extend(self._check_governance_section(sections, content))

        # Check skills section
        errors.extend(self._check_skills_section(sections))

        # Check responsibilities section
        errors.extend(self._check_responsibilities_section(sections))

        # Check .parac/ references
        errors.extend(self._check_parac_references(content))

        # Determine validity
        has_errors = any(e.severity == ValidationSeverity.ERROR for e in errors)
        if self.strict:
            has_errors = has_errors or any(
                e.severity == ValidationSeverity.WARNING for e in errors
            )

        return ValidationResult(
            valid=not has_errors,
            errors=errors,
            agent_id=agent_id,
            spec_path=spec_path,
        )

    def _parse_sections(self, content: str) -> dict[str, str]:
        """Parse markdown into sections by H2 headings.

        Args:
            content: Markdown content

        Returns:
            Dictionary mapping section names to content
        """
        sections: dict[str, str] = {}
        current_section: Optional[str] = None
        current_content: list[str] = []

        for line in content.split("\n"):
            if line.startswith("## "):
                # Save previous section
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()

                # Start new section
                current_section = line[3:].strip()
                # Remove optional markers like "(required)"
                current_section = re.sub(
                    r"\s*\((?:required|optional)\)\s*$", "", current_section
                )
                current_content = []
            elif current_section:
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def _check_title(
        self,
        content: str,
        agent_id: Optional[str],
    ) -> list[ValidationError]:
        """Check that spec has a valid H1 title."""
        errors = []

        # Find H1
        h1_match = re.search(r"^# (.+)$", content, re.MULTILINE)
        if not h1_match:
            errors.append(
                ValidationError(
                    message="Missing H1 title (e.g., '# Coder Agent')",
                    severity=ValidationSeverity.ERROR,
                    section="title",
                    suggestion="Add a title at the top: # Your Agent Name",
                )
            )
        elif agent_id:
            title = h1_match.group(1).strip()
            # Check title relates to agent_id
            normalized_title = title.lower().replace(" ", "-").replace("-agent", "")
            normalized_id = agent_id.lower()
            if (
                normalized_id not in normalized_title
                and normalized_title not in normalized_id
            ):
                errors.append(
                    ValidationError(
                        message=f"Title '{title}' doesn't match agent ID '{agent_id}'",
                        severity=ValidationSeverity.WARNING,
                        section="title",
                        suggestion=f"Consider renaming to '{agent_id.replace('-', ' ').title()} Agent'",
                    )
                )

        return errors

    def _check_required_sections(
        self,
        sections: dict[str, str],
    ) -> list[ValidationError]:
        """Check that all required sections exist."""
        errors = []

        for section_name in self.REQUIRED_SECTIONS:
            if section_name not in sections:
                errors.append(
                    ValidationError(
                        message=f"Missing required section: '{section_name}'",
                        severity=ValidationSeverity.ERROR,
                        section=section_name,
                        suggestion=f"Add a '## {section_name}' section",
                    )
                )
            elif not sections[section_name].strip():
                errors.append(
                    ValidationError(
                        message=f"Section '{section_name}' is empty",
                        severity=ValidationSeverity.ERROR,
                        section=section_name,
                        suggestion=f"Add content to the '{section_name}' section",
                    )
                )

        return errors

    def _check_governance_section(
        self,
        sections: dict[str, str],
        full_content: str,
    ) -> list[ValidationError]:
        """Check governance section has required subsections."""
        errors = []

        governance = sections.get("Governance Integration", "")
        if not governance:
            return errors  # Already reported as missing

        # Check for required subsections
        required_subsections = [
            ("Before Starting Any Task", "pre-task"),
            ("After Completing Work", "post-task"),
        ]

        for subsection, purpose in required_subsections:
            if subsection.lower() not in governance.lower():
                errors.append(
                    ValidationError(
                        message=f"Governance section missing '{subsection}' subsection",
                        severity=ValidationSeverity.ERROR,
                        section="Governance Integration",
                        suggestion=f"Add '### {subsection}' with {purpose} instructions",
                    )
                )

        return errors

    def _check_skills_section(
        self,
        sections: dict[str, str],
    ) -> list[ValidationError]:
        """Check skills section has at least one skill."""
        errors = []

        skills = sections.get("Skills", "")
        if not skills:
            return errors  # Already reported as missing

        # Count bullet points
        bullet_count = len(re.findall(r"^[\s]*[-*]\s+\S", skills, re.MULTILINE))
        if bullet_count == 0:
            errors.append(
                ValidationError(
                    message="Skills section has no skill items",
                    severity=ValidationSeverity.ERROR,
                    section="Skills",
                    suggestion="Add skills as bullet points (e.g., '- paracle-development')",
                )
            )

        return errors

    def _check_responsibilities_section(
        self,
        sections: dict[str, str],
    ) -> list[ValidationError]:
        """Check responsibilities section has categories and items."""
        errors = []

        responsibilities = sections.get("Responsibilities", "")
        if not responsibilities:
            return errors  # Already reported as missing

        # Check for H3 categories
        categories = re.findall(r"^### (.+)$", responsibilities, re.MULTILINE)
        if not categories:
            errors.append(
                ValidationError(
                    message="Responsibilities section has no categories",
                    severity=ValidationSeverity.WARNING,
                    section="Responsibilities",
                    suggestion="Add categories with '### Category Name' headings",
                )
            )

        # Check for bullet items
        bullet_count = len(
            re.findall(r"^[\s]*[-*]\s+\S", responsibilities, re.MULTILINE)
        )
        if bullet_count == 0:
            errors.append(
                ValidationError(
                    message="Responsibilities section has no items",
                    severity=ValidationSeverity.ERROR,
                    section="Responsibilities",
                    suggestion="Add responsibility items as bullet points",
                )
            )

        return errors

    def _check_parac_references(
        self,
        content: str,
    ) -> list[ValidationError]:
        """Check that required .parac/ paths are referenced."""
        errors = []

        for path in self.REQUIRED_PARAC_REFS:
            if path not in content:
                errors.append(
                    ValidationError(
                        message=f"Missing reference to '{path}'",
                        severity=ValidationSeverity.WARNING,
                        section="Governance Integration",
                        suggestion=f"Add reference to {path} in the Governance Integration section",
                    )
                )

        # Check at least one .parac/ reference exists
        if ".parac/" not in content:
            errors.append(
                ValidationError(
                    message="No .parac/ paths referenced in spec",
                    severity=ValidationSeverity.ERROR,
                    suggestion="Add .parac/ governance references to the spec",
                )
            )

        return errors

    def validate_directory(self, specs_dir: Path) -> dict[str, ValidationResult]:
        """Validate all specs in a directory.

        Args:
            specs_dir: Path to .parac/agents/specs/

        Returns:
            Dictionary mapping agent IDs to validation results
        """
        results = {}

        if not specs_dir.exists():
            return results

        for spec_file in specs_dir.glob("*.md"):
            # Skip generated files
            if spec_file.stem.upper() in ("SCHEMA", "TEMPLATE"):
                continue

            # Skip files starting with underscore
            if spec_file.stem.startswith("_"):
                continue

            result = self.validate_file(spec_file)
            results[spec_file.stem] = result

        return results
