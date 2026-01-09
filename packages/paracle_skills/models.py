"""Skill models following the Agent Skills specification.

This module defines the canonical Paracle skill format that can be exported
to multiple platforms (GitHub Copilot, Cursor, Claude Code, OpenAI Codex, MCP).

See: https://agentskills.io/specification
See: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
"""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

# Skill source type
SkillSourceType = Literal["project", "system"]


class SkillCategory(str, Enum):
    """Skill categories for organization and discovery."""

    CREATION = "creation"
    ANALYSIS = "analysis"
    AUTOMATION = "automation"
    INTEGRATION = "integration"
    COMMUNICATION = "communication"
    QUALITY = "quality"
    DEVOPS = "devops"
    SECURITY = "security"
    VERSION_CONTROL = "version-control"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    INFRASTRUCTURE = "infrastructure"


class SkillLevel(str, Enum):
    """Skill complexity levels."""

    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class SkillTool(BaseModel):
    """Tool definition bundled with a skill (for MCP export).

    Attributes:
        name: Tool identifier (lowercase, hyphens allowed)
        description: Human-readable description for LLM understanding
        input_schema: JSON Schema for tool parameters
        output_schema: Optional JSON Schema for tool output
        implementation: Path to implementation (e.g., "scripts/tool.py:ToolClass")
        annotations: MCP tool annotations (readOnlyHint, destructiveHint, etc.)
    """

    name: str = Field(..., min_length=1, max_length=64)
    description: str = Field(..., min_length=1, max_length=1024)
    input_schema: dict[str, Any] = Field(
        default_factory=lambda: {"type": "object", "properties": {}}
    )
    output_schema: dict[str, Any] | None = None
    implementation: str | None = None
    annotations: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate tool name format."""
        if not re.match(r"^[a-z][a-z0-9_-]*$", v):
            raise ValueError(
                "Tool name must be lowercase, start with letter, "
                "and contain only letters, numbers, hyphens, underscores"
            )
        return v


class SkillMetadata(BaseModel):
    """Extended metadata for skill organization and discovery.

    Attributes:
        author: Skill author or team
        version: Semantic version string
        category: Skill category for organization
        level: Skill complexity level
        display_name: Human-friendly name for UI display
        tags: Keywords for discovery
        capabilities: List of capabilities this skill provides
        requirements: Dependencies on other skills
    """

    author: str | None = None
    version: str = "1.0.0"
    category: SkillCategory = SkillCategory.AUTOMATION
    level: SkillLevel = SkillLevel.INTERMEDIATE
    display_name: str | None = None
    tags: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    requirements: list[dict[str, Any]] = Field(default_factory=list)


class SkillSpec(BaseModel):
    """Canonical Paracle skill specification.

    This model represents a skill that can be exported to multiple platforms.
    It follows the Agent Skills specification with Paracle-specific extensions.

    Required fields (per Agent Skills spec):
        - name: 1-64 chars, lowercase alphanumeric and hyphens
        - description: 1-1024 chars explaining what/when to use

    Optional fields (per Agent Skills spec):
        - license: License name or reference
        - compatibility: Environment requirements
        - metadata: Arbitrary key-value pairs
        - allowed_tools: Pre-approved tools list

    Paracle extensions:
        - tools: Tool definitions for MCP export
        - assigned_agents: Which Paracle agents can use this skill
        - instructions: Full instruction content from SKILL.md body
        - source: Where the skill was loaded from ("project" or "system")

    Attributes:
        name: Unique skill identifier (lowercase, hyphens)
        description: Brief description of what skill does and when to use
        license: License name (e.g., "Apache-2.0")
        compatibility: Environment requirements description
        metadata: Extended metadata for organization
        allowed_tools: Space-delimited list of pre-approved tools
        tools: Tool definitions bundled with this skill
        assigned_agents: List of agent IDs that can use this skill
        instructions: Full instruction content (SKILL.md body)
        source_path: Path to source SKILL.md file
        source: Skill source - "project" (.parac/) or "system" (framework)
    """

    # Required fields (Agent Skills spec)
    name: str = Field(..., min_length=1, max_length=64)
    description: str = Field(..., min_length=1, max_length=1024)

    # Optional fields (Agent Skills spec)
    license: str | None = None
    compatibility: str | None = Field(None, max_length=500)
    metadata: SkillMetadata = Field(default_factory=SkillMetadata)
    allowed_tools: str | None = None

    # Paracle extensions
    tools: list[SkillTool] = Field(default_factory=list)
    assigned_agents: list[str] = Field(default_factory=list)
    instructions: str = ""
    source_path: Path | None = None
    source: SkillSourceType = "project"  # "project" or "system"

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate skill name per Agent Skills spec.

        Rules:
        - 1-64 characters
        - Lowercase alphanumeric and hyphens only
        - Cannot start/end with hyphen
        - Cannot contain consecutive hyphens
        - Cannot contain "anthropic" or "claude" (reserved)
        """
        if not v:
            raise ValueError("Skill name cannot be empty")

        if not re.match(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$|^[a-z0-9]$", v):
            raise ValueError(
                "Skill name must be lowercase alphanumeric with hyphens, "
                "cannot start/end with hyphen"
            )

        if "--" in v:
            raise ValueError("Skill name cannot contain consecutive hyphens")

        reserved = ["anthropic", "claude"]
        for word in reserved:
            if word in v.lower():
                raise ValueError(f"Skill name cannot contain reserved word: {word}")

        return v.lower()

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate description per Agent Skills spec."""
        if not v or not v.strip():
            raise ValueError("Description cannot be empty")

        # Check for XML tags (not allowed)
        if re.search(r"<[^>]+>", v):
            raise ValueError("Description cannot contain XML tags")

        return v.strip()

    @model_validator(mode="after")
    def set_display_name(self) -> SkillSpec:
        """Set display_name from name if not provided."""
        if self.metadata.display_name is None:
            # Convert kebab-case to Title Case
            self.metadata.display_name = self.name.replace("-", " ").title()
        return self

    def to_skill_md(self) -> str:
        """Generate SKILL.md content following Agent Skills spec.

        Returns:
            Complete SKILL.md content with YAML frontmatter and instructions
        """
        lines = ["---"]

        # Required fields
        lines.append(f"name: {self.name}")
        lines.append(f"description: {self.description}")

        # Optional fields
        if self.license:
            lines.append(f"license: {self.license}")

        if self.compatibility:
            lines.append(f"compatibility: {self.compatibility}")

        # Metadata section
        if self.metadata:
            lines.append("metadata:")
            if self.metadata.author:
                lines.append(f"  author: {self.metadata.author}")
            lines.append(f'  version: "{self.metadata.version}"')
            lines.append(f"  category: {self.metadata.category.value}")
            lines.append(f"  level: {self.metadata.level.value}")
            if self.metadata.display_name:
                lines.append(f'  display_name: "{self.metadata.display_name}"')
            if self.metadata.tags:
                lines.append("  tags:")
                for tag in self.metadata.tags:
                    lines.append(f"    - {tag}")
            if self.metadata.capabilities:
                lines.append("  capabilities:")
                for cap in self.metadata.capabilities:
                    lines.append(f"    - {cap}")

        # Allowed tools
        if self.allowed_tools:
            lines.append(f"allowed-tools: {self.allowed_tools}")

        lines.append("---")
        lines.append("")

        # Instructions body
        if self.instructions:
            lines.append(self.instructions)

        return "\n".join(lines)

    def to_mcp_tools(self) -> list[dict[str, Any]]:
        """Export tools as MCP tool definitions.

        Returns:
            List of MCP-compatible tool definitions
        """
        mcp_tools = []
        for tool in self.tools:
            mcp_tool = {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
            }
            if tool.output_schema:
                mcp_tool["outputSchema"] = tool.output_schema
            if tool.annotations:
                mcp_tool["annotations"] = tool.annotations
            mcp_tools.append(mcp_tool)
        return mcp_tools

    def get_directory_structure(self) -> dict[str, list[str]]:
        """Get the expected directory structure for this skill.

        Returns:
            Dictionary mapping directory names to expected files
        """
        structure = {
            "root": ["SKILL.md"],
            "scripts": [],
            "references": [],
            "assets": [],
        }

        # Add tool implementation scripts
        for tool in self.tools:
            if tool.implementation:
                script_path = tool.implementation.split(":")[0]
                if script_path.startswith("scripts/"):
                    script_name = script_path.replace("scripts/", "")
                    structure["scripts"].append(script_name)

        return structure
