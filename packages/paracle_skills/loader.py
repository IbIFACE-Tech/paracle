"""Skill loader for parsing SKILL.md files.

Loads skills from multiple sources following the Agent Skills specification:
1. Project skills: .parac/agents/skills/ (user's workspace, highest priority)
2. System skills: Platform-specific system directory (framework-provided)
   - Linux: ~/.local/share/paracle/skills/
   - macOS: ~/Library/Application Support/Paracle/skills/
   - Windows: %LOCALAPPDATA%\\Paracle\\skills\\

Skills in project override system skills with the same name.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

import yaml

from paracle_skills.models import (
    SkillCategory,
    SkillLevel,
    SkillMetadata,
    SkillSpec,
    SkillTool,
)

# Constants
SKILL_FILENAME = "SKILL.md"

SkillSource = Literal["project", "system"]


class SkillLoadError(Exception):
    """Raised when a skill cannot be loaded."""

    def __init__(self, skill_path: Path, message: str):
        self.skill_path = skill_path
        self.message = message
        super().__init__(f"Failed to load skill from {skill_path}: {message}")


class SkillLoader:
    """Load skills from SKILL.md files.

    Parses SKILL.md files following the Agent Skills specification,
    extracting YAML frontmatter and markdown instructions.

    Supports multiple skill sources:
    - Project skills: .parac/agents/skills/ (highest priority)
    - System skills: Platform-specific system directory

    Example:
        >>> # Load from single directory
        >>> loader = SkillLoader(Path(".parac/agents/skills"))
        >>> skills = loader.load_all()
        >>> for skill in skills:
        ...     print(f"{skill.name}: {skill.description}")

        >>> # Load from multiple sources (project + system)
        >>> loader = SkillLoader.with_system_skills(Path(".parac/agents/skills"))
        >>> skills = loader.load_all()  # Project skills override system skills
    """

    def __init__(
        self,
        skills_dir: Path | str,
        system_skills_dir: Path | str | None = None,
    ):
        """Initialize the loader.

        Args:
            skills_dir: Path to project skills directory
            system_skills_dir: Optional path to system skills directory.
                If None, only project skills are loaded.
        """
        self.skills_dir = Path(skills_dir)
        self.system_skills_dir = Path(system_skills_dir) if system_skills_dir else None

    @classmethod
    def with_system_skills(
        cls,
        project_skills_dir: Path | str,
    ) -> SkillLoader:
        """Create a loader that includes system-wide skills.

        System skills are loaded from platform-specific directories:
        - Linux: ~/.local/share/paracle/skills/
        - macOS: ~/Library/Application Support/Paracle/skills/
        - Windows: %LOCALAPPDATA%\\Paracle\\skills\\

        Args:
            project_skills_dir: Path to project skills directory

        Returns:
            SkillLoader configured with both project and system skills
        """
        from paracle_core.paths import get_system_skills_dir

        return cls(
            skills_dir=project_skills_dir,
            system_skills_dir=get_system_skills_dir(),
        )

    @classmethod
    def system_only(cls) -> SkillLoader:
        """Create a loader for system skills only (no project skills).

        Useful for listing/managing framework-provided skills.

        Returns:
            SkillLoader configured for system skills only
        """
        from paracle_core.paths import get_system_skills_dir

        system_dir = get_system_skills_dir()
        return cls(skills_dir=system_dir, system_skills_dir=None)

    def load_all(
        self,
        include_system: bool = True,
    ) -> list[SkillSpec]:
        """Load all skills from configured directories.

        Project skills take priority over system skills with the same name.

        Args:
            include_system: Whether to include system skills (default: True)

        Returns:
            List of loaded SkillSpec objects

        Raises:
            SkillLoadError: If a skill cannot be loaded
        """
        skills_by_name: dict[str, SkillSpec] = {}

        # Load system skills first (lower priority)
        if include_system and self.system_skills_dir:
            system_skills = self._load_from_directory(
                self.system_skills_dir,
                source="system",
            )
            for skill in system_skills:
                skills_by_name[skill.name] = skill

        # Load project skills (higher priority, overwrites system)
        project_skills = self._load_from_directory(
            self.skills_dir,
            source="project",
        )
        for skill in project_skills:
            skills_by_name[skill.name] = skill

        return list(skills_by_name.values())

    def load_project_skills(self) -> list[SkillSpec]:
        """Load only project skills (from .parac/agents/skills/).

        Returns:
            List of project SkillSpec objects
        """
        return self._load_from_directory(self.skills_dir, source="project")

    def load_system_skills(self) -> list[SkillSpec]:
        """Load only system skills (from platform-specific directory).

        Returns:
            List of system SkillSpec objects, or empty if not configured
        """
        if not self.system_skills_dir:
            return []
        return self._load_from_directory(self.system_skills_dir, source="system")

    def _load_from_directory(
        self,
        directory: Path,
        source: SkillSource,
    ) -> list[SkillSpec]:
        """Load skills from a specific directory.

        Args:
            directory: Skills directory path
            source: Source identifier ("project" or "system")

        Returns:
            List of loaded SkillSpec objects
        """
        skills = []

        if not directory.exists():
            return skills

        for skill_dir in directory.iterdir():
            if not skill_dir.is_dir() or skill_dir.name.startswith("."):
                continue

            skill_md = skill_dir / SKILL_FILENAME
            if not skill_md.exists():
                continue

            try:
                skill = self.load_skill(skill_md, source=source)
                skills.append(skill)
            except SkillLoadError:
                raise
            except Exception as e:
                raise SkillLoadError(skill_md, str(e)) from e

        return skills

    def load_skill(
        self,
        skill_md_path: Path,
        source: SkillSource = "project",
    ) -> SkillSpec:
        """Load a single skill from a SKILL.md file.

        Args:
            skill_md_path: Path to SKILL.md file
            source: Source identifier ("project" or "system")

        Returns:
            Parsed SkillSpec object

        Raises:
            SkillLoadError: If the skill cannot be parsed
        """
        if not skill_md_path.exists():
            raise SkillLoadError(skill_md_path, f"{SKILL_FILENAME} file not found")

        content = skill_md_path.read_text(encoding="utf-8")
        frontmatter, instructions = self._parse_skill_md(content)

        if not frontmatter:
            raise SkillLoadError(skill_md_path, "Missing YAML frontmatter")

        # Parse metadata
        metadata = self._parse_metadata(frontmatter.get("metadata", {}))

        # Parse tools if present
        tools = self._parse_tools(frontmatter.get("tools", []))

        # Build SkillSpec
        try:
            skill = SkillSpec(
                name=frontmatter.get("name", ""),
                description=frontmatter.get("description", ""),
                license=frontmatter.get("license"),
                compatibility=frontmatter.get("compatibility"),
                metadata=metadata,
                allowed_tools=frontmatter.get("allowed-tools"),
                tools=tools,
                assigned_agents=frontmatter.get("assigned-agents", []),
                instructions=instructions,
                source_path=skill_md_path,
                source=source,
            )
        except Exception as e:
            raise SkillLoadError(skill_md_path, str(e)) from e

        return skill

    def _parse_skill_md(self, content: str) -> tuple[dict[str, Any], str]:
        """Parse SKILL.md content into frontmatter and instructions.

        Args:
            content: Raw SKILL.md file content

        Returns:
            Tuple of (frontmatter dict, instructions markdown)
        """
        # Match YAML frontmatter between --- markers
        pattern = r"^---\s*\n(.*?)\n---\s*\n?(.*)"
        match = re.match(pattern, content, re.DOTALL)

        if not match:
            # No frontmatter found
            return {}, content

        frontmatter_yaml = match.group(1)
        instructions = match.group(2).strip()

        try:
            frontmatter = yaml.safe_load(frontmatter_yaml) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML frontmatter: {e}") from e

        return frontmatter, instructions

    def _parse_metadata(self, metadata_dict: dict[str, Any]) -> SkillMetadata:
        """Parse metadata section into SkillMetadata.

        Args:
            metadata_dict: Raw metadata from frontmatter

        Returns:
            Parsed SkillMetadata object
        """
        category = metadata_dict.get("category", "automation")
        if isinstance(category, str):
            try:
                category = SkillCategory(category.lower())
            except ValueError:
                category = SkillCategory.AUTOMATION

        level = metadata_dict.get("level", "intermediate")
        if isinstance(level, str):
            try:
                level = SkillLevel(level.lower())
            except ValueError:
                level = SkillLevel.INTERMEDIATE

        return SkillMetadata(
            author=metadata_dict.get("author"),
            version=str(metadata_dict.get("version", "1.0.0")),
            category=category,
            level=level,
            display_name=metadata_dict.get("display_name"),
            tags=metadata_dict.get("tags", []),
            capabilities=metadata_dict.get("capabilities", []),
            requirements=metadata_dict.get("requirements", []),
        )

    def _parse_tools(self, tools_list: list[dict[str, Any]]) -> list[SkillTool]:
        """Parse tools section into SkillTool objects.

        Args:
            tools_list: List of tool definitions from frontmatter

        Returns:
            List of parsed SkillTool objects
        """
        tools = []
        for tool_dict in tools_list:
            input_schema = tool_dict.get(
                "input_schema",
                tool_dict.get("inputSchema", {}),
            )
            output_schema = tool_dict.get(
                "output_schema",
                tool_dict.get("outputSchema"),
            )
            tool = SkillTool(
                name=tool_dict.get("name", ""),
                description=tool_dict.get("description", ""),
                input_schema=input_schema,
                output_schema=output_schema,
                implementation=tool_dict.get("implementation"),
                annotations=tool_dict.get("annotations", {}),
            )
            tools.append(tool)
        return tools

    def get_skill_names(
        self,
        include_system: bool = True,
    ) -> list[str]:
        """Get list of available skill names.

        Args:
            include_system: Whether to include system skills

        Returns:
            List of skill directory names (sorted, deduplicated)
        """
        names: set[str] = set()

        # Collect from project directory
        names.update(self._get_names_from_directory(self.skills_dir))

        # Collect from system directory
        if include_system and self.system_skills_dir:
            names.update(self._get_names_from_directory(self.system_skills_dir))

        return sorted(names)

    def _get_names_from_directory(self, directory: Path) -> set[str]:
        """Get skill names from a specific directory.

        Args:
            directory: Skills directory path

        Returns:
            Set of skill names
        """
        names: set[str] = set()

        if not directory.exists():
            return names

        for skill_dir in directory.iterdir():
            if not skill_dir.is_dir() or skill_dir.name.startswith("."):
                continue
            if (skill_dir / SKILL_FILENAME).exists():
                names.add(skill_dir.name)

        return names

    def skill_exists(
        self,
        name: str,
        check_system: bool = True,
    ) -> bool:
        """Check if a skill exists.

        Args:
            name: Skill name to check
            check_system: Whether to check system skills too

        Returns:
            True if skill exists in project or system directory
        """
        # Check project first
        project_skill = self.skills_dir / name
        if project_skill.exists() and (project_skill / SKILL_FILENAME).exists():
            return True

        # Check system if enabled
        if check_system and self.system_skills_dir:
            system_skill = self.system_skills_dir / name
            if system_skill.exists() and (system_skill / SKILL_FILENAME).exists():
                return True

        return False

    def get_skill_source(self, name: str) -> SkillSource | None:
        """Determine which source a skill comes from.

        Args:
            name: Skill name to check

        Returns:
            "project", "system", or None if not found
        """
        # Check project first (higher priority)
        project_skill = self.skills_dir / name
        if project_skill.exists() and (project_skill / SKILL_FILENAME).exists():
            return "project"

        # Check system
        if self.system_skills_dir:
            system_skill = self.system_skills_dir / name
            if system_skill.exists() and (system_skill / SKILL_FILENAME).exists():
                return "system"

        return None
