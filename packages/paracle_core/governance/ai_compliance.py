"""AI Compliance Engine - Force AI assistants to respect .parac/ structure.

This module provides real-time validation and enforcement for AI assistants
like GitHub Copilot, Claude Code, Cursor, etc. It ensures that AI-generated
code and files respect the .parac/ governance structure.

The compliance engine works by:
1. Monitoring file operations (create, modify, move)
2. Validating against .parac/STRUCTURE.md rules
3. Blocking violations before they happen
4. Suggesting correct locations for misplaced files

Integration points:
- VS Code extension (via language server)
- MCP server (for Claude, Cursor)
- File system watcher (for any AI assistant)
- Pre-save hooks (IDE integration)

Usage:
    # In VS Code extension or MCP server
    from paracle_core.governance import AIComplianceEngine

    engine = AIComplianceEngine()

    # Validate file placement before creation
    validation = engine.validate_file_path(".parac/costs.db")
    if not validation.is_valid:
        print(f"Error: {validation.error}")
        print(f"Suggestion: {validation.suggested_path}")
"""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class FileCategory(Enum):
    """Categories of files in .parac/ structure."""

    OPERATIONAL_DATA = "operational_data"  # *.db, metrics, cache
    LOGS = "logs"  # *.log files
    KNOWLEDGE = "knowledge"  # *.md knowledge base
    DECISIONS = "decisions"  # ADRs
    AGENT_SPECS = "agent_specs"  # Agent definitions
    WORKFLOWS = "workflows"  # Workflow definitions
    TOOLS = "tools"  # Tool definitions
    POLICIES = "policies"  # Policy files
    CONFIG = "config"  # Configuration files
    SUMMARIES = "summaries"  # Weekly/phase summaries
    CONTEXT = "context"  # current_state, open_questions
    EXECUTION_ARTIFACTS = "execution_artifacts"  # Run outputs (gitignored)
    USER_DOCS = "user_docs"  # User-facing documentation (NOT in .parac)
    SOURCE_CODE = "source_code"  # Python/code files (NOT in .parac)


@dataclass
class ValidationResult:
    """Result of file path validation."""

    is_valid: bool
    path: Path
    category: FileCategory | None = None
    error: str | None = None
    suggested_path: Path | None = None
    rule_violated: str | None = None
    auto_fix_available: bool = False


class AIComplianceEngine:
    """Enforce .parac/ structure compliance for AI assistants.

    This engine validates file paths against .parac/STRUCTURE.md rules
    and provides suggestions for correct placement.

    Example:
        >>> engine = AIComplianceEngine()
        >>> result = engine.validate_file_path(".parac/costs.db")
        >>> if not result.is_valid:
        ...     print(f"Error: {result.error}")
        ...     print(f"Use instead: {result.suggested_path}")
    """

    def __init__(self, parac_root: Path | None = None):
        """Initialize compliance engine.

        Args:
            parac_root: Path to .parac/ directory (auto-discovered if None)
        """
        self.parac_root = parac_root or self._find_parac_root()
        self._load_structure_rules()

    def _find_parac_root(self) -> Path:
        """Find .parac/ directory."""
        current = Path.cwd()
        for parent in [current, *current.parents]:
            parac_dir = parent / ".parac"
            if parac_dir.is_dir():
                return parac_dir
        raise FileNotFoundError(".parac/ directory not found")

    def _load_structure_rules(self) -> None:
        """Load structure rules from STRUCTURE.md."""
        # Define structure rules based on .parac/STRUCTURE.md
        # NOTE: Order matters! More specific rules first
        self.rules = {
            # Operational data MUST be in memory/data/
            r"\.parac/.*\.(db|sqlite|sqlite3)$": {
                "category": FileCategory.OPERATIONAL_DATA,
                "required_location": ".parac/memory/data/",
                "rule": "All databases must be in .parac/memory/data/",
            },
            r"\.parac/.*metrics\.(json|yaml|txt)$": {
                "category": FileCategory.OPERATIONAL_DATA,
                "required_location": ".parac/memory/data/",
                "rule": "All metrics files must be in .parac/memory/data/",
            },
            # Logs MUST be in memory/logs/
            r"\.parac/.*\.log$": {
                "category": FileCategory.LOGS,
                "required_location": ".parac/memory/logs/",
                "rule": "All log files must be in .parac/memory/logs/",
            },
            # Decisions MUST be in roadmap/ (specific file)
            r"\.parac/(roadmap/)?decisions\.md$": {
                "category": FileCategory.DECISIONS,
                "required_location": ".parac/roadmap/decisions.md",
                "rule": "ADRs must be in .parac/roadmap/decisions.md",
            },
            # Agent specs MUST be in agents/specs/
            r"\.parac/agents/specs/.*\.md$": {
                "category": FileCategory.AGENT_SPECS,
                "required_location": ".parac/agents/specs/",
                "rule": "Agent specs must be in .parac/agents/specs/",
            },
            # Context files MUST be in memory/context/
            r"\.parac/(memory/context/)?(current_state|open_questions)\..*$": {
                "category": FileCategory.CONTEXT,
                "required_location": ".parac/memory/context/",
                "rule": "Context files must be in .parac/memory/context/",
            },
            # User docs should NOT be in .parac/
            r"\.parac/docs/.*": {
                "category": FileCategory.USER_DOCS,
                "required_location": "docs/",
                "rule": "User documentation should be in docs/, not .parac/",
            },
            # Python code should NOT be in .parac/
            r"\.parac/.*\.py$": {
                "category": FileCategory.SOURCE_CODE,
                "required_location": "packages/",
                "rule": "Python code should be in packages/, not .parac/",
            },
            # Knowledge files in correct location (this validates correct placement)
            r"\.parac/memory/knowledge/.*\.md$": {
                "category": FileCategory.KNOWLEDGE,
                "required_location": ".parac/memory/knowledge/",
                "rule": "Knowledge base files must be in .parac/memory/knowledge/",
            },
            # Knowledge files NOT in correct location (catch remaining .md files)
            r"\.parac/(?!memory/knowledge/|roadmap/decisions\.md|agents/specs/|docs/).*\.md$": {
                "category": FileCategory.KNOWLEDGE,
                "required_location": ".parac/memory/knowledge/",
                "rule": "Knowledge base files must be in .parac/memory/knowledge/",
            },
        }

    def validate_file_path(self, file_path: str | Path) -> ValidationResult:
        """Validate a file path against .parac/ structure rules.

        Args:
            file_path: Path to validate (relative or absolute)

        Returns:
            ValidationResult with validity status and suggestions
        """
        path = Path(file_path)

        # Normalize path to relative
        try:
            if path.is_absolute():
                path = path.relative_to(Path.cwd())
        except ValueError:
            pass

        path_str = str(path).replace("\\", "/")

        # Check against each rule
        for pattern, rule_info in self.rules.items():
            if re.match(pattern, path_str):
                category = rule_info["category"]
                required_location = rule_info["required_location"]

                # Check if file is in correct location
                if not path_str.startswith(required_location):
                    # Violation detected
                    suggested_path = self._suggest_correct_path(
                        path, category, required_location
                    )

                    return ValidationResult(
                        is_valid=False,
                        path=path,
                        category=category,
                        error=f"File placement violation: {rule_info['rule']}",
                        suggested_path=suggested_path,
                        rule_violated=rule_info["rule"],
                        auto_fix_available=True,
                    )

                # Valid placement
                return ValidationResult(is_valid=True, path=path, category=category)

        # No rule matched - allow by default (unknown file type)
        return ValidationResult(is_valid=True, path=path)

    def _suggest_correct_path(
        self, path: Path, category: FileCategory, required_location: str
    ) -> Path:
        """Suggest correct path for a misplaced file.

        Args:
            path: Original (incorrect) path
            category: File category
            required_location: Required location prefix

        Returns:
            Suggested correct path
        """
        filename = path.name

        # Build suggested path
        if category == FileCategory.DECISIONS:
            # decisions.md has fixed location
            return Path(".parac/roadmap/decisions.md")

        elif category in (
            FileCategory.CONTEXT,
            FileCategory.OPERATIONAL_DATA,
            FileCategory.LOGS,
            FileCategory.KNOWLEDGE,
        ):
            # Append filename to required location
            return Path(required_location) / filename

        elif category == FileCategory.USER_DOCS:
            # Move to content/docs/ (outside .parac)
            return Path("docs") / filename

        elif category == FileCategory.SOURCE_CODE:
            # Move to packages/ (outside .parac)
            # Try to infer package name from path
            if "paracle" in str(path):
                parts = path.parts
                for i, part in enumerate(parts):
                    if part.startswith("paracle_"):
                        return Path("packages") / "/".join(parts[i:])
            return Path("packages") / filename

        else:
            # Default: use required location + filename
            return Path(required_location) / filename

    def validate_batch(self, file_paths: list[str | Path]) -> list[ValidationResult]:
        """Validate multiple file paths.

        Args:
            file_paths: List of paths to validate

        Returns:
            List of ValidationResult objects
        """
        return [self.validate_file_path(path) for path in file_paths]

    def get_violations(self, file_paths: list[str | Path]) -> list[ValidationResult]:
        """Get only violations from a list of paths.

        Args:
            file_paths: List of paths to validate

        Returns:
            List of ValidationResult objects for violations only
        """
        results = self.validate_batch(file_paths)
        return [r for r in results if not r.is_valid]

    def auto_fix_path(self, file_path: str | Path) -> Path | None:
        """Get auto-fix suggestion for a file path.

        Args:
            file_path: Path to fix

        Returns:
            Suggested correct path, or None if no fix available
        """
        result = self.validate_file_path(file_path)
        if not result.is_valid and result.auto_fix_available:
            return result.suggested_path
        return None

    def generate_pre_save_validation(self, file_path: str | Path) -> dict[str, Any]:
        """Generate validation response for IDE pre-save hooks.

        Args:
            file_path: Path being saved

        Returns:
            Dictionary with validation result and actions
        """
        result = self.validate_file_path(file_path)

        if result.is_valid:
            return {
                "allow_save": True,
                "message": "File placement valid",
            }
        else:
            return {
                "allow_save": False,
                "error": result.error,
                "suggested_path": str(result.suggested_path),
                "auto_fix_available": result.auto_fix_available,
                "quick_fix": {
                    "title": f"Move to {result.suggested_path}",
                    "action": "move_file",
                    "target": str(result.suggested_path),
                },
            }

    def get_structure_documentation(self, category: FileCategory) -> str:
        """Get documentation for a file category.

        Args:
            category: File category

        Returns:
            Documentation string explaining correct placement
        """
        docs = {
            FileCategory.OPERATIONAL_DATA: """
            Operational Data Files (.db, metrics, cache)
            Location: .parac/memory/data/

            Examples:
            - .parac/memory/data/costs.db
            - .parac/memory/data/metrics.json
            - .parac/memory/data/cache/responses.json

            Rule: All databases and operational data files MUST be in
            .parac/memory/data/, never in .parac root or code directories.
            """,
            FileCategory.LOGS: """
            Log Files (*.log)
            Location: .parac/memory/logs/

            Examples:
            - .parac/memory/logs/agent_actions.log
            - .parac/memory/logs/decisions.log
            - .parac/memory/logs/errors.log

            Rule: All log files MUST be in .parac/memory/logs/, never in
            code directories or .parac root.
            """,
            FileCategory.KNOWLEDGE: """
            Knowledge Base Files (*.md)
            Location: .parac/memory/knowledge/

            Examples:
            - .parac/memory/knowledge/architecture.md
            - .parac/memory/knowledge/glossary.md
            - .parac/memory/knowledge/api_patterns.md

            Rule: Technical knowledge files MUST be in .parac/memory/knowledge/.
            """,
            FileCategory.DECISIONS: """
            Architecture Decision Records (ADRs)
            Location: .parac/roadmap/decisions.md

            Rule: All ADRs MUST be in .parac/roadmap/decisions.md (single file).
            Never create separate decisions.md in .parac root.
            """,
            FileCategory.USER_DOCS: """
            User-Facing Documentation
            Location: docs/ (NOT in .parac/)

            Examples:
            - docs/getting-started.md
            - docs/api-reference.md
            - docs/tutorials/

            Rule: User documentation should be in docs/, never in .parac/.
            .parac/ is for governance, not user docs.
            """,
            FileCategory.SOURCE_CODE: """
            Python Source Code
            Location: packages/ (NOT in .parac/)

            Examples:
            - packages/paracle_core/
            - packages/paracle_agents/

            Rule: Python code should be in packages/, never in .parac/.
            .parac/ is for governance files, not source code.
            """,
        }

        return docs.get(
            category, "No documentation available for this category"
        ).strip()


class AIAssistantMonitor:
    """Monitor AI assistant file operations and enforce compliance.

    This class provides hooks for IDE extensions and MCP servers to
    validate file operations in real-time.

    Example:
        >>> monitor = AIAssistantMonitor()
        >>>
        >>> # In VS Code extension or MCP server
        >>> result = monitor.on_file_create(".parac/costs.db")
        >>> if not result["allowed"]:
        ...     show_error(result["error"])
        ...     suggest_alternative(result["suggested_path"])
    """

    def __init__(self, parac_root: Path | None = None):
        """Initialize monitor.

        Args:
            parac_root: Path to .parac/ directory
        """
        self.engine = AIComplianceEngine(parac_root)
        self.violations_log: list[ValidationResult] = []

    def on_file_create(self, file_path: str | Path) -> dict[str, Any]:
        """Handle file creation event from AI assistant.

        Args:
            file_path: Path of file being created

        Returns:
            Dictionary with allowed status and suggestions
        """
        result = self.engine.validate_file_path(file_path)

        if not result.is_valid:
            # Log violation
            self.violations_log.append(result)

            return {
                "allowed": False,
                "error": result.error,
                "suggested_path": str(result.suggested_path),
                "documentation": self.engine.get_structure_documentation(
                    result.category
                ),
                "auto_fix_available": result.auto_fix_available,
            }

        return {"allowed": True}

    def on_file_move(
        self, old_path: str | Path, new_path: str | Path
    ) -> dict[str, Any]:
        """Handle file move event from AI assistant.

        Args:
            old_path: Original path
            new_path: Target path

        Returns:
            Dictionary with allowed status and suggestions
        """
        # Validate new path
        return self.on_file_create(new_path)

    def get_violations_report(self) -> str:
        """Generate report of all violations.

        Returns:
            Formatted report string
        """
        if not self.violations_log:
            return "No violations detected."

        lines = ["# .parac/ Structure Violations\n"]
        for i, violation in enumerate(self.violations_log, 1):
            lines.append(f"\n## Violation {i}")
            lines.append(f"**File**: {violation.path}")
            lines.append(f"**Error**: {violation.error}")
            lines.append(f"**Suggested Fix**: {violation.suggested_path}")
            lines.append(f"**Rule**: {violation.rule_violated}")

        return "\n".join(lines)

    def clear_violations_log(self) -> None:
        """Clear violations log."""
        self.violations_log.clear()


# Singleton instance for global access
_compliance_engine: AIComplianceEngine | None = None
_assistant_monitor: AIAssistantMonitor | None = None


def get_compliance_engine(
    parac_root: Path | None = None,
) -> AIComplianceEngine:
    """Get singleton compliance engine instance.

    Args:
        parac_root: Path to .parac/ directory (only used on first call)

    Returns:
        AIComplianceEngine instance
    """
    global _compliance_engine
    if _compliance_engine is None:
        _compliance_engine = AIComplianceEngine(parac_root)
    return _compliance_engine


def get_assistant_monitor(
    parac_root: Path | None = None,
) -> AIAssistantMonitor:
    """Get singleton assistant monitor instance.

    Args:
        parac_root: Path to .parac/ directory (only used on first call)

    Returns:
        AIAssistantMonitor instance
    """
    global _assistant_monitor
    if _assistant_monitor is None:
        _assistant_monitor = AIAssistantMonitor(parac_root)
    return _assistant_monitor
