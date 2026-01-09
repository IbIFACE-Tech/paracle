"""Paracle Skills Package.

Provides a unified skill system following the Agent Skills specification.
Skills are loaded from multiple sources and can be exported to
multiple platforms: GitHub Copilot, Cursor, Claude Code, OpenAI Codex, and MCP.

Skill Sources (priority order):
1. Project skills: .parac/agents/skills/ (user's workspace, highest priority)
2. System skills: Platform-specific system directory (framework-provided)
   - Linux: ~/.local/share/paracle/skills/
   - macOS: ~/Library/Application Support/Paracle/skills/
   - Windows: %LOCALAPPDATA%\\Paracle\\skills\\

Example:
    >>> from paracle_skills import SkillLoader, SkillExporter
    >>>
    >>> # Load skills from project directory only
    >>> loader = SkillLoader(".parac/agents/skills")
    >>> skills = loader.load_all()
    >>>
    >>> # Load from both project and system directories
    >>> loader = SkillLoader.with_system_skills(".parac/agents/skills")
    >>> skills = loader.load_all()  # Project skills override system skills
    >>>
    >>> # Export to multiple platforms
    >>> exporter = SkillExporter(skills)
    >>> exporter.export_all(output_dir=".", platforms=["copilot", "cursor", "claude"])
"""

from paracle_skills.exporter import SkillExporter
from paracle_skills.loader import SkillLoader, SkillLoadError, SkillSource
from paracle_skills.models import (
    SkillCategory,
    SkillLevel,
    SkillMetadata,
    SkillSourceType,
    SkillSpec,
    SkillTool,
)

__all__ = [
    # Models
    "SkillSpec",
    "SkillMetadata",
    "SkillTool",
    "SkillCategory",
    "SkillLevel",
    "SkillSourceType",
    # Loader
    "SkillLoader",
    "SkillLoadError",
    "SkillSource",
    # Exporter
    "SkillExporter",
]
