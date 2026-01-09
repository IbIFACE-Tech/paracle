"""Rovo Dev exporter for Atlassian Rovo Dev CLI subagents.

Exports Paracle skills to Rovo Dev subagent format:
- Markdown files with YAML frontmatter
- Stored in .rovodev/subagents/ directory

See: https://support.atlassian.com/rovo/docs/use-subagents-in-rovo-dev-cli/
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from paracle_skills.exporters.base import BaseExporter, ExportResult

if TYPE_CHECKING:
    from paracle_skills.models import SkillSpec


# Mapping from Paracle tool names to Rovo Dev tool names
PARACLE_TO_ROVODEV_TOOLS = {
    # File operations
    "read_file": "open_files",
    "write_file": "write_file",
    "list_files": "list_files",
    "search_files": "grep",
    # Code operations
    "grep": "grep",
    "find": "grep",
    "analyze_code": "expand_code_chunks",
    # Shell operations
    "bash": "bash",
    "execute": "bash",
    "run_command": "bash",
    # Git operations
    "git": "bash",
    # Web operations
    "web_search": "web_search",
    "fetch_url": "fetch_url",
}

# Default tools available in Rovo Dev
DEFAULT_ROVODEV_TOOLS = [
    "open_files",
    "expand_code_chunks",
    "grep",
    "bash",
]


class RovoDevExporter(BaseExporter):
    """Export skills to Rovo Dev subagent format.

    Rovo Dev subagents are markdown files with YAML frontmatter containing:
    - name: Subagent identifier
    - description: One-line description
    - tools: List of available tools

    The markdown body contains the system prompt/instructions.

    Example output:
        .rovodev/subagents/security-hardening.md

        ```yaml
        ---
        name: security-hardening
        description: Security auditing and vulnerability detection
        tools:
          - open_files
          - grep
          - bash
        ---
        You are a security expert...
        ```
    """

    @property
    def platform_name(self) -> str:
        """Return the platform identifier."""
        return "rovodev"

    @property
    def output_directory(self) -> str:
        """Return the default output directory."""
        return ".rovodev/subagents"

    def export_skill(
        self,
        skill: SkillSpec,
        output_dir: Path,
        overwrite: bool = False,
    ) -> ExportResult:
        """Export a skill to Rovo Dev subagent format.

        Creates:
            <output_dir>/.rovodev/subagents/<skill-name>.md

        Args:
            skill: Skill specification to export
            output_dir: Root directory (typically project root)
            overwrite: Whether to overwrite existing file

        Returns:
            ExportResult with status and created files
        """
        files_created = []
        errors = []

        # Calculate target directory
        subagents_dir = output_dir / self.output_directory

        try:
            self._ensure_directory(subagents_dir)

            # Generate subagent file
            subagent_path = subagents_dir / f"{skill.name}.md"

            if subagent_path.exists() and not overwrite:
                errors.append(f"Subagent already exists: {subagent_path}")
                return ExportResult(
                    success=False,
                    platform=self.platform_name,
                    skill_name=skill.name,
                    output_path=subagent_path,
                    errors=errors,
                )

            # Generate content
            content = self._generate_subagent_content(skill)
            subagent_path.write_text(content, encoding="utf-8")
            files_created.append(str(subagent_path))

            return ExportResult(
                success=True,
                platform=self.platform_name,
                skill_name=skill.name,
                output_path=subagent_path,
                files_created=files_created,
            )

        except Exception as e:
            errors.append(str(e))
            return ExportResult(
                success=False,
                platform=self.platform_name,
                skill_name=skill.name,
                output_path=subagents_dir / f"{skill.name}.md",
                files_created=files_created,
                errors=errors,
            )

    def _generate_subagent_content(self, skill: SkillSpec) -> str:
        """Generate Rovo Dev subagent markdown content.

        Args:
            skill: Skill specification

        Returns:
            Complete subagent markdown with YAML frontmatter
        """
        lines = ["---"]

        # Required fields
        lines.append(f"name: {skill.name}")

        # Description (truncate to one line if needed)
        description = skill.description.split("\n")[0][:200]
        lines.append(f"description: {description}")

        # Tools
        tools = self._map_tools(skill)
        lines.append("tools:")
        for tool in tools:
            lines.append(f"  - {tool}")

        lines.append("---")
        lines.append("")

        # System prompt (instructions)
        lines.append(self._generate_system_prompt(skill))

        return "\n".join(lines)

    def _map_tools(self, skill: SkillSpec) -> list[str]:
        """Map Paracle skill tools to Rovo Dev tools.

        Args:
            skill: Skill specification

        Returns:
            List of Rovo Dev tool names
        """
        rovodev_tools = set()

        # Map from allowed_tools if present
        if skill.allowed_tools:
            for tool in skill.allowed_tools.split():
                mapped = PARACLE_TO_ROVODEV_TOOLS.get(tool.lower(), tool.lower())
                rovodev_tools.add(mapped)

        # Map from skill.tools if present
        for tool in skill.tools:
            mapped = PARACLE_TO_ROVODEV_TOOLS.get(tool.name.lower(), tool.name.lower())
            rovodev_tools.add(mapped)

        # Use defaults if no tools specified
        if not rovodev_tools:
            rovodev_tools = set(DEFAULT_ROVODEV_TOOLS)

        # Ensure we have at least open_files for reading
        rovodev_tools.add("open_files")

        return sorted(rovodev_tools)

    def _generate_system_prompt(self, skill: SkillSpec) -> str:
        """Generate the system prompt for the subagent.

        Args:
            skill: Skill specification

        Returns:
            System prompt content
        """
        parts = []

        # Role/expertise header
        display_name = (
            skill.metadata.display_name or skill.name.replace("-", " ").title()
        )
        parts.append(f"You are an expert {display_name} assistant.")
        parts.append("")

        # Description
        parts.append("## Purpose")
        parts.append("")
        parts.append(skill.description)
        parts.append("")

        # Main instructions from SKILL.md body
        if skill.instructions:
            parts.append("## Instructions")
            parts.append("")
            parts.append(skill.instructions)
            parts.append("")

        # Capabilities from metadata
        if skill.metadata.capabilities:
            parts.append("## Capabilities")
            parts.append("")
            for cap in skill.metadata.capabilities:
                parts.append(f"- {cap}")
            parts.append("")

        # Guidelines for Rovo Dev
        parts.append("## Guidelines")
        parts.append("")
        parts.append("When working on tasks:")
        parts.append("1. Analyze the request thoroughly before taking action")
        parts.append("2. Use available tools to gather context")
        parts.append("3. Provide specific, actionable feedback")
        parts.append("4. Explain your reasoning when making recommendations")
        parts.append("")

        # Paracle integration note
        parts.append("## Paracle Integration")
        parts.append("")
        parts.append("This subagent follows Paracle governance rules.")
        parts.append(
            "After completing tasks, log actions to `.parac/memory/logs/agent_actions.log`."
        )

        return "\n".join(parts)
