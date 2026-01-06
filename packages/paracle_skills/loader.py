"""Skill loader for parsing SKILL.md files.

Loads skills from .parac/agents/skills/ directory following
the Agent Skills specification.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from paracle_skills.models import (
    SkillCategory,
    SkillLevel,
    SkillMetadata,
    SkillSpec,
    SkillTool,
)


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

    Example:
        >>> loader = SkillLoader(Path(".parac/agents/skills"))
        >>> skills = loader.load_all()
        >>> for skill in skills:
        ...     print(f"{skill.name}: {skill.description}")
    """

    def __init__(self, skills_dir: Path | str):
        """Initialize the loader.

        Args:
            skills_dir: Path to skills directory (e.g., .parac/agents/skills)
        """
        self.skills_dir = Path(skills_dir)

    def load_all(self) -> list[SkillSpec]:
        """Load all skills from the skills directory.

        Returns:
            List of loaded SkillSpec objects

        Raises:
            SkillLoadError: If a skill cannot be loaded
        """
        skills = []

        if not self.skills_dir.exists():
            return skills

        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith("."):
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    try:
                        skill = self.load_skill(skill_md)
                        skills.append(skill)
                    except SkillLoadError:
                        raise
                    except Exception as e:
                        raise SkillLoadError(skill_md, str(e)) from e

        return skills

    def load_skill(self, skill_md_path: Path) -> SkillSpec:
        """Load a single skill from a SKILL.md file.

        Args:
            skill_md_path: Path to SKILL.md file

        Returns:
            Parsed SkillSpec object

        Raises:
            SkillLoadError: If the skill cannot be parsed
        """
        if not skill_md_path.exists():
            raise SkillLoadError(skill_md_path, "SKILL.md file not found")

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
            tool = SkillTool(
                name=tool_dict.get("name", ""),
                description=tool_dict.get("description", ""),
                input_schema=tool_dict.get("input_schema", tool_dict.get("inputSchema", {})),
                output_schema=tool_dict.get("output_schema", tool_dict.get("outputSchema")),
                implementation=tool_dict.get("implementation"),
                annotations=tool_dict.get("annotations", {}),
            )
            tools.append(tool)
        return tools

    def get_skill_names(self) -> list[str]:
        """Get list of available skill names.

        Returns:
            List of skill directory names
        """
        names = []
        if not self.skills_dir.exists():
            return names

        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith("."):
                if (skill_dir / "SKILL.md").exists():
                    names.append(skill_dir.name)

        return sorted(names)

    def skill_exists(self, name: str) -> bool:
        """Check if a skill exists.

        Args:
            name: Skill name to check

        Returns:
            True if skill exists
        """
        skill_dir = self.skills_dir / name
        return skill_dir.exists() and (skill_dir / "SKILL.md").exists()
