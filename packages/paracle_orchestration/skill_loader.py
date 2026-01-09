"""Skill loader for agent execution enhancement.

This module loads skills from .parac/agents/skills/ and makes them
available during agent execution.

Skills can be assigned to agents in two ways (in order of priority):
1. manifest.yaml - agents.[].skills field (preferred, structured)
2. SKILL_ASSIGNMENTS.md - markdown format (fallback, legacy)
"""

import logging
from pathlib import Path
from typing import Any

import yaml
from paracle_profiling import cached, profile

logger = logging.getLogger(__name__)


class Skill:
    """Represents a loaded skill."""

    def __init__(
        self,
        skill_id: str,
        name: str,
        description: str,
        content: str,
        assets: dict[str, str] | None = None,
        scripts: dict[str, str] | None = None,
        references: dict[str, str] | None = None,
    ):
        """Initialize skill.

        Args:
            skill_id: Unique skill identifier
            name: Skill name
            description: Skill description
            content: Main skill content (from SKILL.md)
            assets: Optional assets (templates, examples)
            scripts: Optional executable scripts
            references: Optional reference documentation
        """
        self.skill_id = skill_id
        self.name = name
        self.description = description
        self.content = content
        self.assets = assets or {}
        self.scripts = scripts or {}
        self.references = references or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "content": self.content,
            "has_assets": bool(self.assets),
            "has_scripts": bool(self.scripts),
            "has_references": bool(self.references),
        }


class SkillLoader:
    """Loads skills from .parac/agents/skills/ directory.

    Skill assignments are read from manifest.yaml (preferred) or
    SKILL_ASSIGNMENTS.md (fallback for backward compatibility).
    """

    def __init__(self, parac_dir: Path | None = None):
        """Initialize skill loader.

        Args:
            parac_dir: Path to .parac directory (defaults to ./.parac)
        """
        self.parac_dir = parac_dir or Path.cwd() / ".parac"
        self.skills_dir = self.parac_dir / "agents" / "skills"
        self.manifest_file = self.parac_dir / "agents" / "manifest.yaml"
        self.assignments_file = self.parac_dir / "agents" / "SKILL_ASSIGNMENTS.md"
        self._skill_cache: dict[str, Skill] = {}
        self._assignments_cache: dict[str, list[str]] = {}
        self._manifest_cache: dict[str, Any] | None = None

    def discover_skills(self) -> list[str]:
        """Discover all available skills.

        Returns:
            List of skill IDs
        """
        if not self.skills_dir.exists():
            logger.warning(f"Skills directory not found: {self.skills_dir}")
            return []

        skills = []
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                skills.append(skill_dir.name)

        logger.info(f"Discovered {len(skills)} skills: {skills}")
        return skills

    @cached(ttl=300)  # Cache skills for 5 minutes
    @profile(track_memory=True)
    def load_skill(self, skill_id: str) -> Skill | None:
        """Load a specific skill.

        Args:
            skill_id: Skill identifier (directory name)

        Returns:
            Skill object or None if not found
        """
        # Check cache
        if skill_id in self._skill_cache:
            return self._skill_cache[skill_id]

        skill_path = self.skills_dir / skill_id
        if not skill_path.exists():
            logger.warning(f"Skill not found: {skill_id}")
            return None

        skill_file = skill_path / "SKILL.md"
        if not skill_file.exists():
            logger.warning(f"SKILL.md not found for: {skill_id}")
            return None

        # Load main content
        raw_content = skill_file.read_text(encoding="utf-8")

        # Parse YAML frontmatter and extract name/description
        name, description, content = self._parse_skill_md(raw_content, skill_id)

        # Load assets
        assets = self._load_directory_files(skill_path / "assets")

        # Load scripts
        scripts = self._load_directory_files(skill_path / "scripts")

        # Load references
        references = self._load_directory_files(skill_path / "references")

        skill = Skill(
            skill_id=skill_id,
            name=name,
            description=description,
            content=content,
            assets=assets,
            scripts=scripts,
            references=references,
        )

        # Cache it
        self._skill_cache[skill_id] = skill
        logger.debug(f"Loaded skill: {skill_id}")

        return skill

    def load_agent_skills(self, agent_name: str) -> list[Skill]:
        """Load all skills assigned to an agent.

        Args:
            agent_name: Agent name (e.g., "coder", "architect")

        Returns:
            List of Skill objects
        """
        skill_ids = self.get_agent_skill_ids(agent_name)
        skills = []

        for skill_id in skill_ids:
            skill = self.load_skill(skill_id)
            if skill:
                skills.append(skill)
            else:
                logger.warning(
                    f"Could not load skill {skill_id} for agent {agent_name}"
                )

        logger.info(f"Loaded {len(skills)} skills for agent: {agent_name}")
        return skills

    def get_agent_skill_ids(self, agent_name: str) -> list[str]:
        """Get skill IDs assigned to an agent.

        Reads from manifest.yaml first (preferred), falls back to
        SKILL_ASSIGNMENTS.md for backward compatibility.

        Args:
            agent_name: Agent name (e.g., "coder", "architect")

        Returns:
            List of skill IDs
        """
        # Check cache
        if agent_name in self._assignments_cache:
            return self._assignments_cache[agent_name]

        # Try manifest.yaml first (preferred source)
        skills = self._get_skills_from_manifest(agent_name)

        # Fallback to SKILL_ASSIGNMENTS.md if not found in manifest
        if not skills:
            skills = self._get_skills_from_assignments_md(agent_name)

        # Cache it
        self._assignments_cache[agent_name] = skills
        return skills

    def _get_skills_from_manifest(self, agent_name: str) -> list[str]:
        """Read skills from manifest.yaml.

        Args:
            agent_name: Agent name (id field in manifest)

        Returns:
            List of skill IDs or empty list if not found
        """
        if not self.manifest_file.exists():
            logger.debug(f"Manifest file not found: {self.manifest_file}")
            return []

        # Load and cache manifest
        if self._manifest_cache is None:
            try:
                content = self.manifest_file.read_text(encoding="utf-8")
                self._manifest_cache = yaml.safe_load(content) or {}
                logger.debug("Loaded manifest.yaml")
            except Exception as e:
                logger.warning(f"Failed to load manifest.yaml: {e}")
                self._manifest_cache = {}
                return []

        # Find agent by id
        agents = self._manifest_cache.get("agents", [])
        for agent in agents:
            if agent.get("id") == agent_name:
                skills = agent.get("skills", [])
                if skills:
                    # Strip comments from skill IDs (e.g., "skill-name # comment")
                    clean_skills = []
                    for skill in skills:
                        skill_id = skill.split("#")[0].strip()
                        if skill_id:
                            clean_skills.append(skill_id)
                    logger.debug(
                        f"Found {len(clean_skills)} skills for {agent_name} "
                        f"in manifest.yaml"
                    )
                    return clean_skills

        logger.debug(f"No skills found for {agent_name} in manifest.yaml")
        return []

    def _get_skills_from_assignments_md(self, agent_name: str) -> list[str]:
        """Read skills from SKILL_ASSIGNMENTS.md (legacy fallback).

        Args:
            agent_name: Agent name

        Returns:
            List of skill IDs
        """
        if not self.assignments_file.exists():
            logger.debug(f"Assignments file not found: {self.assignments_file}")
            return []

        # Parse SKILL_ASSIGNMENTS.md
        content = self.assignments_file.read_text(encoding="utf-8")
        skills = self._parse_assignments(content, agent_name)

        if skills:
            logger.debug(
                f"Found {len(skills)} skills for {agent_name} "
                f"in SKILL_ASSIGNMENTS.md (legacy)"
            )
        return skills

    def _parse_assignments(self, content: str, agent_name: str) -> list[str]:
        """Parse SKILL_ASSIGNMENTS.md to extract skills for an agent.

        Args:
            content: File content
            agent_name: Agent name to find

        Returns:
            List of skill IDs
        """
        skills = []
        in_agent_section = False
        agent_header = f"### {agent_name.title()} Agent"
        agent_header_alt = f"### 💻 {agent_name.title()} Agent"
        agent_header_alt2 = f"### 🔧 {agent_name.title()} Agent"

        lines = content.split("\n")
        for line in lines:
            # Check if we're entering the agent's section
            if (
                agent_header.lower() in line.lower()
                or agent_header_alt.lower() in line.lower()
                or agent_header_alt2.lower() in line.lower()
            ):
                in_agent_section = True
                continue

            # Check if we're leaving the section (next agent)
            if in_agent_section and line.startswith("### "):
                break

            # Extract skill IDs (lines starting with -)
            if in_agent_section and line.strip().startswith("- `"):
                # Extract skill-id from: - `skill-id` - Description
                skill_id = line.split("`")[1] if "`" in line else None
                if skill_id:
                    skills.append(skill_id)

        return skills

    def _parse_skill_md(self, raw_content: str, skill_id: str) -> tuple[str, str, str]:
        """Parse SKILL.md file extracting YAML frontmatter.

        Args:
            raw_content: Raw file content
            skill_id: Skill identifier (folder name)

        Returns:
            Tuple of (name, description, content)
        """
        import re

        # Default values
        name = skill_id.replace("-", " ").title()
        description = f"Skill: {name}"
        content = raw_content

        # Check for YAML frontmatter (content between --- markers)
        frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(frontmatter_pattern, raw_content, re.DOTALL)

        if match:
            try:
                import yaml

                frontmatter_text = match.group(1)
                content = match.group(2)

                frontmatter = yaml.safe_load(frontmatter_text)
                if frontmatter:
                    # Extract name and description from frontmatter
                    name = frontmatter.get("name", skill_id)
                    description = frontmatter.get("description", f"Skill: {name}")

                    # Also try metadata.display_name if available
                    metadata = frontmatter.get("metadata", {})
                    if metadata and metadata.get("display_name"):
                        name = metadata["display_name"]

                logger.debug(
                    f"Parsed frontmatter for {skill_id}: "
                    f"name={name}, desc={description[:50]}..."
                )
            except Exception as e:
                logger.warning(f"Failed to parse frontmatter for {skill_id}: {e}")

        return name, description, content

    def _load_directory_files(self, directory: Path) -> dict[str, str]:
        """Load all files from a directory.

        Args:
            directory: Directory path

        Returns:
            Dictionary mapping filename to content
        """
        files = {}
        if not directory.exists():
            return files

        for file_path in directory.iterdir():
            if file_path.is_file():
                try:
                    content = file_path.read_text(encoding="utf-8")
                    files[file_path.name] = content
                except Exception as e:
                    logger.warning(f"Could not read {file_path}: {e}")

        return files

    def validate_agent_skills(self, agent_name: str) -> list[str]:
        """Validate that all assigned skills exist.

        Args:
            agent_name: Agent name to validate

        Returns:
            List of missing skill IDs (empty if all valid)
        """
        skill_ids = self.get_agent_skill_ids(agent_name)
        available_skills = set(self.discover_skills())
        missing = [sid for sid in skill_ids if sid not in available_skills]

        if missing:
            logger.warning(f"Agent {agent_name} has missing skills: {missing}")

        return missing

    def validate_all_agents(self) -> dict[str, list[str]]:
        """Validate skills for all agents in manifest.

        Returns:
            Dictionary mapping agent names to their missing skill IDs
        """
        if not self.manifest_file.exists():
            return {}

        # Load manifest if not cached
        if self._manifest_cache is None:
            try:
                content = self.manifest_file.read_text(encoding="utf-8")
                self._manifest_cache = yaml.safe_load(content) or {}
            except Exception as e:
                logger.warning(f"Failed to load manifest.yaml: {e}")
                return {}

        agents = self._manifest_cache.get("agents", [])
        validation_results = {}

        for agent in agents:
            agent_id = agent.get("id")
            if agent_id:
                missing = self.validate_agent_skills(agent_id)
                if missing:
                    validation_results[agent_id] = missing

        return validation_results

    def clear_cache(self) -> None:
        """Clear all caches."""
        self._skill_cache.clear()
        self._assignments_cache.clear()
        self._manifest_cache = None
