"""Agent specification schema - SOURCE OF TRUTH.

This module defines the Pydantic models that represent the required structure
for agent specification files in .parac/agents/specs/.

All .parac/ paths that agents should know about are defined in ParacPaths.
"""

from typing import Optional

from pydantic import BaseModel, Field


class ParacPaths:
    """All .parac/ paths that agents should know about.

    This is the canonical list of paths that agents may need to read or write.
    Used by templates, validators, and documentation generators.
    """

    # ==========================================================================
    # GOVERNANCE (Always read before any task)
    # ==========================================================================
    GOVERNANCE = ".parac/GOVERNANCE.md"
    STRUCTURE = ".parac/STRUCTURE.md"

    # ==========================================================================
    # CONTEXT (Current project state)
    # ==========================================================================
    CURRENT_STATE = ".parac/memory/context/current_state.yaml"
    OPEN_QUESTIONS = ".parac/memory/context/open_questions.md"
    TECH_DEBT = ".parac/memory/context/tech_debt.md"

    # ==========================================================================
    # ROADMAP (Priorities and decisions)
    # ==========================================================================
    ROADMAP = ".parac/roadmap/roadmap.yaml"
    DECISIONS = ".parac/roadmap/decisions.md"

    # ==========================================================================
    # LOGS (Action tracking)
    # ==========================================================================
    ACTION_LOG = ".parac/memory/logs/agent_actions.log"
    DECISIONS_LOG = ".parac/memory/logs/decisions.log"

    # ==========================================================================
    # POLICIES (Guidelines to follow)
    # ==========================================================================
    CODE_STYLE = ".parac/policies/CODE_STYLE.md"
    TESTING = ".parac/policies/TESTING.md"
    SECURITY = ".parac/policies/SECURITY.md"
    POLICY_PACK = ".parac/policies/policy-pack.yaml"

    # ==========================================================================
    # KNOWLEDGE (Learned information)
    # ==========================================================================
    KNOWLEDGE_DIR = ".parac/memory/knowledge/"
    ARCHITECTURE = ".parac/memory/knowledge/architecture.md"
    GLOSSARY = ".parac/memory/knowledge/glossary.md"

    # ==========================================================================
    # AGENTS (Agent definitions)
    # ==========================================================================
    AGENTS_MANIFEST = ".parac/agents/manifest.yaml"
    AGENTS_SPECS_DIR = ".parac/agents/specs/"
    SKILL_ASSIGNMENTS = ".parac/agents/SKILL_ASSIGNMENTS.md"

    # ==========================================================================
    # SKILLS (Available skills)
    # ==========================================================================
    SKILLS_DIR = ".parac/skills/"

    # ==========================================================================
    # WORKFLOWS (Automation)
    # ==========================================================================
    WORKFLOWS_DIR = ".parac/workflows/"

    @classmethod
    def all_paths(cls) -> dict[str, str]:
        """Get all paths as a dictionary."""
        return {
            name: value
            for name, value in vars(cls).items()
            if not name.startswith("_") and isinstance(value, str)
        }

    @classmethod
    def required_pre_task(cls) -> list[str]:
        """Paths agents MUST read before starting any task."""
        return [
            cls.CURRENT_STATE,
            cls.ROADMAP,
        ]

    @classmethod
    def required_post_task(cls) -> list[str]:
        """Paths agents MUST update after completing work."""
        return [
            cls.ACTION_LOG,
        ]

    @classmethod
    def contextual_reads(cls) -> dict[str, str]:
        """Paths agents should read in specific contexts."""
        return {
            "blocked": cls.OPEN_QUESTIONS,
            "making_decision": cls.DECISIONS,
            "writing_code": cls.CODE_STYLE,
            "writing_tests": cls.TESTING,
            "security_sensitive": cls.SECURITY,
            "learning": cls.KNOWLEDGE_DIR,
            "checking_capabilities": cls.SKILL_ASSIGNMENTS,
        }


class GovernanceSection(BaseModel):
    """Required governance integration section for agent specs.

    Every agent MUST have this section to ensure they know how to
    interact with .parac/ governance structure.
    """

    pre_task_reads: list[str] = Field(
        default_factory=lambda: [
            ParacPaths.CURRENT_STATE,
            ParacPaths.ROADMAP,
        ],
        description="Files agent MUST read before starting any task",
    )

    optional_reads: list[str] = Field(
        default_factory=lambda: [
            ParacPaths.OPEN_QUESTIONS,
            ParacPaths.DECISIONS,
        ],
        description="Files agent SHOULD read when relevant",
    )

    post_task_logs: list[str] = Field(
        default_factory=lambda: [
            ParacPaths.ACTION_LOG,
        ],
        description="Files agent MUST update after completing work",
    )

    decision_recording: str = Field(
        default=ParacPaths.DECISIONS,
        description="Where to record architectural decisions",
    )

    policies_to_follow: list[str] = Field(
        default_factory=list,
        description="Policies this agent must follow (e.g., CODE_STYLE, TESTING)",
    )


class ResponsibilityCategory(BaseModel):
    """A category of responsibilities with items."""

    name: str = Field(..., description="Category name (e.g., 'Code Implementation')")
    items: list[str] = Field(..., min_length=1, description="Responsibility items")


class AgentSpecSchema(BaseModel):
    """Schema for agent specification files.

    This defines the required and optional sections that every agent spec
    in .parac/agents/specs/*.md must have.
    """

    # ==========================================================================
    # REQUIRED SECTIONS
    # ==========================================================================

    id: str = Field(
        ...,
        description="Agent identifier (derived from filename, e.g., 'coder')",
        pattern=r"^[a-z][a-z0-9-]*$",
    )

    name: str = Field(
        ..., description="Human-readable agent name (e.g., 'Coder Agent')"
    )

    role: str = Field(
        ..., description="One-paragraph description of agent's primary function"
    )

    governance: GovernanceSection = Field(
        default_factory=GovernanceSection,
        description=".parac/ integration requirements - ALWAYS REQUIRED",
    )

    skills: list[str] = Field(
        ...,
        min_length=1,
        description="List of skills from .parac/skills/ this agent uses",
    )

    responsibilities: list[ResponsibilityCategory] = Field(
        ..., min_length=1, description="Categorized list of agent responsibilities"
    )

    # ==========================================================================
    # OPTIONAL SECTIONS
    # ==========================================================================

    tools: Optional[list[str]] = Field(
        default=None, description="Tools and capabilities available to this agent"
    )

    expertise: Optional[list[str]] = Field(
        default=None, description="Technical expertise areas"
    )

    coding_standards: Optional[list[str]] = Field(
        default=None, description="Specific coding standards this agent follows"
    )

    examples: Optional[dict[str, str]] = Field(
        default=None, description="Example scenarios showing how agent handles tasks"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "id": "coder",
                "name": "Coder Agent",
                "role": "Implementation of features, writing production-quality code.",
                "governance": {
                    "pre_task_reads": [
                        ".parac/memory/context/current_state.yaml",
                        ".parac/roadmap/roadmap.yaml",
                    ],
                    "post_task_logs": [
                        ".parac/memory/logs/agent_actions.log",
                    ],
                    "policies_to_follow": ["CODE_STYLE", "TESTING"],
                },
                "skills": ["paracle-development", "api-development"],
                "responsibilities": [
                    {
                        "name": "Code Implementation",
                        "items": [
                            "Write clean, maintainable Python code",
                            "Implement features according to specifications",
                        ],
                    }
                ],
            }
        }
