"""Paracle Skills Package.

Provides a unified skill system following the Agent Skills specification.
Skills are defined once in .parac/agents/skills/ and can be exported to
multiple platforms: GitHub Copilot, Cursor, Claude Code, OpenAI Codex, and MCP.

Example:
    >>> from paracle_skills import SkillLoader, SkillExporter
    >>>
    >>> # Load skills from directory
    >>> loader = SkillLoader(".parac/agents/skills")
    >>> skills = loader.load_all()
    >>>
    >>> # Export to multiple platforms
    >>> exporter = SkillExporter(skills)
    >>> exporter.export_all(output_dir=".", platforms=["copilot", "cursor", "claude"])
"""

from paracle_skills.models import (
    SkillSpec,
    SkillMetadata,
    SkillTool,
    SkillCategory,
    SkillLevel,
)
from paracle_skills.loader import SkillLoader
from paracle_skills.exporter import SkillExporter

__all__ = [
    "SkillSpec",
    "SkillMetadata",
    "SkillTool",
    "SkillCategory",
    "SkillLevel",
    "SkillLoader",
    "SkillExporter",
]
