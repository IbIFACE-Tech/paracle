"""Main skill exporter orchestrating multi-platform exports.

Provides a unified interface for exporting skills to all supported
platforms in a single operation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from paracle_skills.exporters.agent_skills import AgentSkillsExporter
from paracle_skills.exporters.base import ExportResult
from paracle_skills.exporters.mcp import MCPExporter
from paracle_skills.exporters.rovodev import RovoDevExporter

if TYPE_CHECKING:
    from paracle_skills.models import SkillSpec


# All supported platforms
ALL_PLATFORMS = ["copilot", "cursor", "claude", "codex", "mcp", "rovodev"]

# Agent Skills platforms (same format)
AGENT_SKILLS_PLATFORMS = ["copilot", "cursor", "claude", "codex"]


@dataclass
class MultiExportResult:
    """Result of exporting to multiple platforms.

    Attributes:
        skill_name: Name of the exported skill
        results: Export results per platform
        success_count: Number of successful exports
        error_count: Number of failed exports
    """

    skill_name: str
    results: dict[str, ExportResult] = field(default_factory=dict)

    @property
    def success_count(self) -> int:
        """Count of successful exports."""
        return sum(1 for r in self.results.values() if r.success)

    @property
    def error_count(self) -> int:
        """Count of failed exports."""
        return sum(1 for r in self.results.values() if not r.success)

    @property
    def all_success(self) -> bool:
        """True if all exports succeeded."""
        return self.error_count == 0 and self.success_count > 0


class SkillExporter:
    """Unified exporter for multiple platforms.

    Orchestrates exporting skills to all supported platforms:
    - GitHub Copilot (.github/skills/)
    - Cursor (.cursor/skills/)
    - Claude Code (.claude/skills/)
    - OpenAI Codex (.codex/skills/)
    - MCP (.parac/tools/mcp/)

    Example:
        >>> from paracle_skills import SkillLoader, SkillExporter
        >>>
        >>> # Load skills
        >>> loader = SkillLoader(".parac/agents/skills")
        >>> skills = loader.load_all()
        >>>
        >>> # Export to all platforms
        >>> exporter = SkillExporter(skills)
        >>> results = exporter.export_all(Path("."))
        >>>
        >>> for result in results:
        ...     print(f"{result.skill_name}: {result.success_count} platforms")
    """

    def __init__(self, skills: list[SkillSpec]):
        """Initialize with skills to export.

        Args:
            skills: List of skill specifications
        """
        self.skills = skills

    def export_all(
        self,
        output_dir: Path,
        platforms: list[str] | None = None,
        overwrite: bool = False,
    ) -> list[MultiExportResult]:
        """Export all skills to specified platforms.

        Args:
            output_dir: Root directory for exports
            platforms: Target platforms (default: all)
            overwrite: Whether to overwrite existing files

        Returns:
            List of MultiExportResult for each skill
        """
        if platforms is None:
            platforms = ALL_PLATFORMS

        results = []
        for skill in self.skills:
            result = self.export_skill(skill, output_dir, platforms, overwrite)
            results.append(result)

        return results

    def export_skill(
        self,
        skill: SkillSpec,
        output_dir: Path,
        platforms: list[str] | None = None,
        overwrite: bool = False,
    ) -> MultiExportResult:
        """Export a single skill to specified platforms.

        Args:
            skill: Skill specification to export
            output_dir: Root directory for exports
            platforms: Target platforms (default: all)
            overwrite: Whether to overwrite existing files

        Returns:
            MultiExportResult with results for each platform
        """
        if platforms is None:
            platforms = ALL_PLATFORMS

        result = MultiExportResult(skill_name=skill.name)

        for platform in platforms:
            platform = platform.lower()

            if platform in AGENT_SKILLS_PLATFORMS:
                exporter = AgentSkillsExporter(platform)
                export_result = exporter.export_skill(skill, output_dir, overwrite)
                result.results[platform] = export_result

            elif platform == "mcp":
                exporter = MCPExporter()
                export_result = exporter.export_skill(skill, output_dir, overwrite)
                result.results[platform] = export_result

            elif platform == "rovodev":
                exporter = RovoDevExporter()
                export_result = exporter.export_skill(skill, output_dir, overwrite)
                result.results[platform] = export_result

        return result

    def export_to_platform(
        self,
        platform: str,
        output_dir: Path,
        overwrite: bool = False,
    ) -> list[ExportResult]:
        """Export all skills to a single platform.

        Args:
            platform: Target platform name
            output_dir: Root directory for exports
            overwrite: Whether to overwrite existing files

        Returns:
            List of ExportResult for each skill
        """
        platform = platform.lower()
        results = []

        if platform in AGENT_SKILLS_PLATFORMS:
            exporter = AgentSkillsExporter(platform)
            for skill in self.skills:
                result = exporter.export_skill(skill, output_dir, overwrite)
                results.append(result)

        elif platform == "mcp":
            exporter = MCPExporter()
            for skill in self.skills:
                result = exporter.export_skill(skill, output_dir, overwrite)
                results.append(result)

        elif platform == "rovodev":
            exporter = RovoDevExporter()
            for skill in self.skills:
                result = exporter.export_skill(skill, output_dir, overwrite)
                results.append(result)

        return results


def export_skills_to_platforms(
    skills_dir: Path,
    output_dir: Path,
    platforms: list[str] | None = None,
    overwrite: bool = False,
) -> list[MultiExportResult]:
    """Convenience function to load and export skills.

    Args:
        skills_dir: Directory containing skill definitions
        output_dir: Root directory for exports
        platforms: Target platforms (default: all)
        overwrite: Whether to overwrite existing files

    Returns:
        List of MultiExportResult for each skill
    """
    from paracle_skills.loader import SkillLoader

    loader = SkillLoader(skills_dir)
    skills = loader.load_all()

    exporter = SkillExporter(skills)
    return exporter.export_all(output_dir, platforms, overwrite)
