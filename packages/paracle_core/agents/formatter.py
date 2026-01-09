"""Agent specification formatter and auto-fixer.

Automatically fixes common issues in agent specs:
- Adds missing governance section
- Adds missing .parac/ references
- Normalizes section structure
"""

import re
from pathlib import Path
from typing import Optional

from paracle_core.agents.schema import ParacPaths
from paracle_core.agents.template import AgentTemplate
from paracle_core.agents.validator import AgentSpecValidator, ValidationResult


class AgentSpecFormatter:
    """Formats and fixes agent specification files.

    Can automatically add missing sections and normalize structure
    while preserving user-written content.
    """

    def __init__(self, validator: Optional[AgentSpecValidator] = None):
        """Initialize formatter.

        Args:
            validator: Validator to use for checking (creates default if None)
        """
        self.validator = validator or AgentSpecValidator()
        self.template = AgentTemplate()

    def format_file(
        self,
        spec_path: Path,
        fix: bool = True,
        dry_run: bool = False,
    ) -> tuple[str, ValidationResult, bool]:
        """Format an agent spec file.

        Args:
            spec_path: Path to the spec file
            fix: Whether to apply fixes
            dry_run: If True, don't write changes

        Returns:
            Tuple of (formatted_content, validation_result, was_modified)
        """
        if not spec_path.exists():
            result = self.validator.validate_file(spec_path)
            return "", result, False

        content = spec_path.read_text(encoding="utf-8")
        agent_id = spec_path.stem

        # Skip generated files
        if agent_id.upper() in ("SCHEMA", "TEMPLATE"):
            result = ValidationResult(valid=True, agent_id=agent_id)
            return content, result, False

        formatted, was_modified = self.format_content(content, agent_id, fix)

        if was_modified and not dry_run:
            spec_path.write_text(formatted, encoding="utf-8")

        result = self.validator.validate_content(formatted, agent_id)

        return formatted, result, was_modified

    def format_content(
        self,
        content: str,
        agent_id: Optional[str] = None,
        fix: bool = True,
    ) -> tuple[str, bool]:
        """Format agent spec content.

        Args:
            content: Markdown content
            agent_id: Agent identifier
            fix: Whether to apply fixes

        Returns:
            Tuple of (formatted_content, was_modified)
        """
        if not fix:
            return content, False

        original = content
        modified = content

        # Fix missing title
        modified = self._fix_missing_title(modified, agent_id)

        # Fix missing governance section
        modified = self._fix_missing_governance(modified)

        # Fix missing skills section
        modified = self._fix_missing_skills(modified)

        # Fix missing responsibilities section
        modified = self._fix_missing_responsibilities(modified)

        # Add missing .parac/ references in governance
        modified = self._fix_missing_parac_refs(modified)

        # Normalize whitespace
        modified = self._normalize_whitespace(modified)

        return modified, modified != original

    def _fix_missing_title(
        self,
        content: str,
        agent_id: Optional[str],
    ) -> str:
        """Add missing H1 title."""
        if re.search(r"^# .+$", content, re.MULTILINE):
            return content

        if agent_id:
            title = agent_id.replace("-", " ").title() + " Agent"
        else:
            title = "New Agent"

        return f"# {title}\n\n{content}"

    def _fix_missing_governance(self, content: str) -> str:
        """Add missing governance section."""
        if "## Governance Integration" in content:
            return content

        # Find where to insert (after Role, before Skills)
        governance_content = self._get_governance_template()

        # Try to insert after Role section
        role_match = re.search(
            r"(## Role\n.*?)(?=\n## |\Z)",
            content,
            re.DOTALL,
        )

        if role_match:
            insert_pos = role_match.end()
            return (
                content[:insert_pos]
                + "\n\n"
                + governance_content
                + content[insert_pos:]
            )

        # Insert at the end if no Role section
        return content + "\n\n" + governance_content

    def _fix_missing_skills(self, content: str) -> str:
        """Add missing skills section."""
        if "## Skills" in content:
            return content

        skills_content = """## Skills

- [skill-1]
- [skill-2]

> See `.parac/agents/SKILL_ASSIGNMENTS.md` for available skills.
"""
        # Insert after Governance Integration or at end
        governance_match = re.search(
            r"(## Governance Integration\n.*?)(?=\n## |\Z)",
            content,
            re.DOTALL,
        )

        if governance_match:
            insert_pos = governance_match.end()
            return content[:insert_pos] + "\n\n" + skills_content + content[insert_pos:]

        return content + "\n\n" + skills_content

    def _fix_missing_responsibilities(self, content: str) -> str:
        """Add missing responsibilities section."""
        if "## Responsibilities" in content:
            return content

        responsibilities_content = """## Responsibilities

### Primary

- [First responsibility]
- [Second responsibility]
"""
        # Insert after Skills or at end
        skills_match = re.search(
            r"(## Skills\n.*?)(?=\n## |\Z)",
            content,
            re.DOTALL,
        )

        if skills_match:
            insert_pos = skills_match.end()
            return (
                content[:insert_pos]
                + "\n\n"
                + responsibilities_content
                + content[insert_pos:]
            )

        return content + "\n\n" + responsibilities_content

    def _fix_missing_parac_refs(self, content: str) -> str:
        """Add missing .parac/ references to governance section."""
        # Only fix if governance section exists
        if "## Governance Integration" not in content:
            return content

        # Check required refs
        missing_refs = []
        for path in AgentSpecValidator.REQUIRED_PARAC_REFS:
            if path not in content:
                missing_refs.append(path)

        if not missing_refs:
            return content

        # Find governance section and add missing refs
        governance_match = re.search(
            r"(## Governance Integration\n)(.*?)(?=\n## |\Z)",
            content,
            re.DOTALL,
        )

        if not governance_match:
            return content

        governance_content = governance_match.group(2)

        # Add missing refs to appropriate subsections
        for path in missing_refs:
            if path == ParacPaths.ACTION_LOG:
                # Add to "After Completing Work" if exists
                if "### After Completing Work" in governance_content:
                    governance_content = governance_content.replace(
                        "### After Completing Work",
                        f"### After Completing Work\n\nLog to `{path}`:",
                    )
                else:
                    governance_content += (
                        f"\n\n### After Completing Work\n\nLog to `{path}`"
                    )
            else:
                # Add to "Before Starting Any Task" if exists
                if "### Before Starting Any Task" in governance_content:
                    if path not in governance_content:
                        # Find the list and add to it
                        governance_content = re.sub(
                            r"(### Before Starting Any Task\n)",
                            f"\\1\n- Read `{path}`",
                            governance_content,
                        )
                else:
                    governance_content = (
                        f"### Before Starting Any Task\n\n- Read `{path}`\n"
                        + governance_content
                    )

        # Reconstruct content
        return (
            content[: governance_match.start()]
            + "## Governance Integration\n"
            + governance_content
            + content[governance_match.end() :]
        )

    def _get_governance_template(self) -> str:
        """Get the governance section template."""
        return f"""## Governance Integration

### Before Starting Any Task

1. Read `{ParacPaths.CURRENT_STATE}` - Current phase & status
2. Check `{ParacPaths.ROADMAP}` - Priorities for current phase
3. Review `{ParacPaths.OPEN_QUESTIONS}` - Check for blockers

### After Completing Work

Log action to `{ParacPaths.ACTION_LOG}`:

```
[TIMESTAMP] [AGENT_ID] [ACTION_TYPE] Description
```

### Decision Recording

Document architectural decisions in `{ParacPaths.DECISIONS}`.
"""

    def _normalize_whitespace(self, content: str) -> str:
        """Normalize whitespace in content."""
        # Remove trailing whitespace from lines
        lines = [line.rstrip() for line in content.split("\n")]

        # Ensure single blank line between sections
        result = []
        prev_blank = False
        for line in lines:
            is_blank = not line
            is_heading = line.startswith("#")

            if is_heading and result and not prev_blank:
                result.append("")

            if not (is_blank and prev_blank):
                result.append(line)

            prev_blank = is_blank

        # Ensure ends with newline
        content = "\n".join(result)
        if not content.endswith("\n"):
            content += "\n"

        return content

    def format_directory(
        self,
        specs_dir: Path,
        fix: bool = True,
        dry_run: bool = False,
    ) -> dict[str, tuple[ValidationResult, bool]]:
        """Format all specs in a directory.

        Args:
            specs_dir: Path to .parac/agents/specs/
            fix: Whether to apply fixes
            dry_run: If True, don't write changes

        Returns:
            Dictionary mapping agent IDs to (validation_result, was_modified)
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

            _, result, modified = self.format_file(spec_file, fix, dry_run)
            results[spec_file.stem] = (result, modified)

        return results
