"""Agent Skills exporter for GitHub Copilot, Cursor, Claude Code, OpenAI Codex.

These platforms share the same Agent Skills specification:
- SKILL.md file with YAML frontmatter
- Optional scripts/, references/, assets/ directories

See: https://agentskills.io/specification
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from paracle_skills.exporters.base import BaseExporter, ExportResult

if TYPE_CHECKING:
    from paracle_skills.models import SkillSpec


class AgentSkillsExporter(BaseExporter):
    """Export skills to Agent Skills format.

    Supports multiple platforms that use the same specification:
    - GitHub Copilot: .github/skills/
    - Cursor: .cursor/skills/
    - Claude Code: .claude/skills/
    - OpenAI Codex: .codex/skills/

    Example:
        >>> exporter = AgentSkillsExporter("copilot")
        >>> result = exporter.export_skill(skill, Path("."))
        >>> print(result.output_path)  # .github/skills/my-skill/
    """

    # Platform output directories
    PLATFORM_DIRS = {
        "copilot": ".github/skills",
        "cursor": ".cursor/skills",
        "claude": ".claude/skills",
        "codex": ".codex/skills",
    }

    def __init__(self, platform: str):
        """Initialize exporter for a specific platform.

        Args:
            platform: Target platform ("copilot", "cursor", "claude", "codex")

        Raises:
            ValueError: If platform is not supported
        """
        platform = platform.lower()
        if platform not in self.PLATFORM_DIRS:
            raise ValueError(
                f"Unknown platform: {platform}. "
                f"Supported: {list(self.PLATFORM_DIRS.keys())}"
            )
        self._platform = platform

    @property
    def platform_name(self) -> str:
        """Return the platform identifier."""
        return self._platform

    @property
    def output_directory(self) -> str:
        """Return the platform-specific output directory."""
        return self.PLATFORM_DIRS[self._platform]

    def export_skill(
        self,
        skill: SkillSpec,
        output_dir: Path,
        overwrite: bool = False,
    ) -> ExportResult:
        """Export a skill to Agent Skills format.

        Creates:
            <output_dir>/<platform_dir>/<skill-name>/
            ├── SKILL.md
            ├── scripts/ (if present in source)
            ├── references/ (if present in source)
            └── assets/ (if present in source)

        Args:
            skill: Skill specification to export
            output_dir: Root directory (typically project root)
            overwrite: Whether to overwrite existing SKILL.md

        Returns:
            ExportResult with status and created files
        """
        files_created = []
        errors = []

        # Calculate target directory
        skill_dir = output_dir / self.output_directory / skill.name

        try:
            self._ensure_directory(skill_dir)

            # Generate and write SKILL.md
            skill_md_path = skill_dir / "SKILL.md"

            if skill_md_path.exists() and not overwrite:
                errors.append(f"SKILL.md already exists: {skill_md_path}")
                return ExportResult(
                    success=False,
                    platform=self._platform,
                    skill_name=skill.name,
                    output_path=skill_dir,
                    errors=errors,
                )

            skill_md_content = skill.to_skill_md()
            skill_md_path.write_text(skill_md_content, encoding="utf-8")
            files_created.append(str(skill_md_path))

            # Copy resources (scripts, references, assets)
            copied_files = self._copy_resources(skill, skill_dir)
            files_created.extend(copied_files)

            return ExportResult(
                success=True,
                platform=self._platform,
                skill_name=skill.name,
                output_path=skill_dir,
                files_created=files_created,
            )

        except Exception as e:
            errors.append(str(e))
            return ExportResult(
                success=False,
                platform=self._platform,
                skill_name=skill.name,
                output_path=skill_dir,
                files_created=files_created,
                errors=errors,
            )


def create_exporters_for_platforms(
    platforms: list[str] | None = None,
) -> list[AgentSkillsExporter]:
    """Create exporters for multiple platforms.

    Args:
        platforms: List of platform names. If None, creates for all.

    Returns:
        List of configured AgentSkillsExporter instances
    """
    if platforms is None:
        platforms = list(AgentSkillsExporter.PLATFORM_DIRS.keys())

    exporters = []
    for platform in platforms:
        try:
            exporter = AgentSkillsExporter(platform)
            exporters.append(exporter)
        except ValueError:
            pass  # Skip unknown platforms

    return exporters
