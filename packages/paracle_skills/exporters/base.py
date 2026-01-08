"""Base exporter class for skill platform exports."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from paracle_skills.models import SkillSpec


@dataclass
class ExportResult:
    """Result of a skill export operation.

    Attributes:
        success: Whether the export succeeded
        platform: Target platform name
        skill_name: Name of the exported skill
        output_path: Path where skill was exported
        files_created: List of files created
        errors: List of error messages if any
    """

    success: bool
    platform: str
    skill_name: str
    output_path: Path | None = None
    files_created: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class BaseExporter(ABC):
    """Abstract base class for skill exporters.

    Subclasses must implement:
        - platform_name: Return platform identifier
        - export_skill: Export a single skill
    """

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the platform identifier.

        Returns:
            Platform name (e.g., "copilot", "cursor", "claude", "codex", "mcp")
        """
        pass

    @property
    @abstractmethod
    def output_directory(self) -> str:
        """Return the default output directory relative to project root.

        Returns:
            Directory path (e.g., ".github/skills", ".claude/skills")
        """
        pass

    @abstractmethod
    def export_skill(
        self,
        skill: SkillSpec,
        output_dir: Path,
        overwrite: bool = False,
    ) -> ExportResult:
        """Export a single skill to the platform format.

        Args:
            skill: Skill specification to export
            output_dir: Root directory for output
            overwrite: Whether to overwrite existing files

        Returns:
            ExportResult with status and created files
        """
        pass

    def export_all(
        self,
        skills: list[SkillSpec],
        output_dir: Path,
        overwrite: bool = False,
    ) -> list[ExportResult]:
        """Export multiple skills.

        Args:
            skills: List of skills to export
            output_dir: Root directory for output
            overwrite: Whether to overwrite existing files

        Returns:
            List of ExportResult for each skill
        """
        results = []
        for skill in skills:
            result = self.export_skill(skill, output_dir, overwrite)
            results.append(result)
        return results

    def _ensure_directory(self, path: Path) -> None:
        """Ensure a directory exists.

        Args:
            path: Directory path to create
        """
        path.mkdir(parents=True, exist_ok=True)

    def _copy_resources(
        self,
        skill: SkillSpec,
        target_dir: Path,
    ) -> list[str]:
        """Copy skill resources (scripts, references, assets) to target.

        Args:
            skill: Skill with source_path set
            target_dir: Target skill directory

        Returns:
            List of copied file paths
        """
        copied = []

        if not skill.source_path:
            return copied

        source_dir = skill.source_path.parent

        # Copy scripts/
        scripts_src = source_dir / "scripts"
        if scripts_src.exists():
            scripts_dst = target_dir / "scripts"
            copied.extend(self._copy_directory(scripts_src, scripts_dst))

        # Copy references/
        refs_src = source_dir / "references"
        if refs_src.exists():
            refs_dst = target_dir / "references"
            copied.extend(self._copy_directory(refs_src, refs_dst))

        # Copy assets/
        assets_src = source_dir / "assets"
        if assets_src.exists():
            assets_dst = target_dir / "assets"
            copied.extend(self._copy_directory(assets_src, assets_dst))

        return copied

    def _copy_directory(self, src: Path, dst: Path) -> list[str]:
        """Recursively copy a directory.

        Args:
            src: Source directory
            dst: Destination directory

        Returns:
            List of copied file paths
        """
        import shutil

        copied = []

        if not src.exists():
            return copied

        self._ensure_directory(dst)

        for item in src.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(src)
                target = dst / rel_path
                self._ensure_directory(target.parent)
                shutil.copy2(item, target)
                copied.append(str(target))

        return copied
