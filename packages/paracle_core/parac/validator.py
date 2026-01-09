"""Validation for .parac/ workspace.

Validates consistency and syntax of .parac/ files.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class ValidationLevel(Enum):
    """Validation result severity."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A single validation issue."""

    level: ValidationLevel
    file: str
    message: str
    line: int | None = None

    def __str__(self) -> str:
        """Format issue as string."""
        location = f"{self.file}"
        if self.line:
            location += f":{self.line}"
        return f"[{self.level.value.upper()}] {location}: {self.message}"


@dataclass
class ValidationResult:
    """Result of validation."""

    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    files_checked: int = 0

    @property
    def errors(self) -> list[ValidationIssue]:
        """Get only error-level issues."""
        return [i for i in self.issues if i.level == ValidationLevel.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """Get only warning-level issues."""
        return [i for i in self.issues if i.level == ValidationLevel.WARNING]

    def add_error(self, file: str, message: str, line: int | None = None) -> None:
        """Add an error issue."""
        self.issues.append(
            ValidationIssue(
                level=ValidationLevel.ERROR, file=file, message=message, line=line
            )
        )
        self.valid = False

    def add_warning(self, file: str, message: str, line: int | None = None) -> None:
        """Add a warning issue."""
        self.issues.append(
            ValidationIssue(
                level=ValidationLevel.WARNING, file=file, message=message, line=line
            )
        )

    def add_info(self, file: str, message: str, line: int | None = None) -> None:
        """Add an info issue."""
        self.issues.append(
            ValidationIssue(
                level=ValidationLevel.INFO, file=file, message=message, line=line
            )
        )


class ParacValidator:
    """Validates .parac/ workspace structure and content."""

    REQUIRED_DIRS = [
        "roadmap",
        "memory/context",
        "policies",
        "agents",
    ]

    REQUIRED_FILES = [
        "roadmap/roadmap.yaml",
        "memory/context/current_state.yaml",
        "policies/policy-pack.yaml",
    ]

    YAML_FILES = [
        "roadmap/roadmap.yaml",
        "memory/context/current_state.yaml",
        "policies/policy-pack.yaml",
        "policies/security.yaml",
        "agents/manifest.yaml",
        "memory/index.yaml",
    ]

    def __init__(self, parac_root: Path) -> None:
        """Initialize validator.

        Args:
            parac_root: Path to .parac/ directory.
        """
        self.parac_root = parac_root

    def validate(self) -> ValidationResult:
        """Run full validation.

        Returns:
            ValidationResult with all issues found.
        """
        result = ValidationResult(valid=True)

        # Check .parac/ exists
        if not self.parac_root.exists():
            result.add_error(".parac/", "Directory does not exist")
            return result

        # Check required directories
        self._validate_directories(result)

        # Check required files
        self._validate_required_files(result)

        # Validate YAML syntax
        self._validate_yaml_files(result)

        # Validate content consistency
        self._validate_consistency(result)

        return result

    def _validate_directories(self, result: ValidationResult) -> None:
        """Check required directories exist."""
        for dir_path in self.REQUIRED_DIRS:
            full_path = self.parac_root / dir_path
            if not full_path.is_dir():
                result.add_warning(dir_path, "Required directory missing")

    def _validate_required_files(self, result: ValidationResult) -> None:
        """Check required files exist."""
        for file_path in self.REQUIRED_FILES:
            full_path = self.parac_root / file_path
            if not full_path.exists():
                result.add_error(file_path, "Required file missing")
            else:
                result.files_checked += 1

    def _validate_yaml_files(self, result: ValidationResult) -> None:
        """Validate YAML syntax of all YAML files."""
        for file_path in self.YAML_FILES:
            full_path = self.parac_root / file_path
            if full_path.exists():
                result.files_checked += 1
                try:
                    with open(full_path, encoding="utf-8") as f:
                        yaml.safe_load(f)
                except yaml.YAMLError as e:
                    line = getattr(e, "problem_mark", None)
                    line_num = line.line + 1 if line else None
                    result.add_error(file_path, f"Invalid YAML: {e}", line_num)

    def _validate_consistency(self, result: ValidationResult) -> None:
        """Validate consistency between files."""
        state = self._load_yaml("memory/context/current_state.yaml")
        roadmap = self._load_yaml("roadmap/roadmap.yaml")

        if state and roadmap:
            # Check phase alignment
            state_phase = state.get("current_phase", {}).get("id")
            roadmap_phase = roadmap.get("current_phase")

            if state_phase and roadmap_phase and state_phase != roadmap_phase:
                result.add_warning(
                    "memory/context/current_state.yaml",
                    f"Phase mismatch: state={state_phase}, roadmap={roadmap_phase}",
                )

            # Check version alignment
            state_version = state.get("project", {}).get("version")
            roadmap_version = roadmap.get("version")

            if state_version and roadmap_version and state_version != roadmap_version:
                result.add_warning(
                    "memory/context/current_state.yaml",
                    f"Version mismatch: state={state_version}, "
                    f"roadmap={roadmap_version}",
                )

    def _load_yaml(self, file_path: str) -> dict[str, Any] | None:
        """Load a YAML file safely."""
        full_path = self.parac_root / file_path
        if not full_path.exists():
            return None
        try:
            with open(full_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else None
        except yaml.YAMLError:
            return None

    def validate_yaml_file(self, file_path: str) -> ValidationResult:
        """Validate a single YAML file.

        Args:
            file_path: Relative path from .parac/ root.

        Returns:
            ValidationResult for this file.
        """
        result = ValidationResult(valid=True)
        full_path = self.parac_root / file_path

        if not full_path.exists():
            result.add_error(file_path, "File does not exist")
            return result

        result.files_checked = 1
        try:
            with open(full_path, encoding="utf-8") as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            line = getattr(e, "problem_mark", None)
            line_num = line.line + 1 if line else None
            result.add_error(file_path, f"Invalid YAML: {e}", line_num)

        return result
