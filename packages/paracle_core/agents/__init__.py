"""Agent specification system for Paracle.

This module provides:
- Schema definitions for agent specs (Pydantic models)
- Template for new agent creation
- Validation of agent specs
- Auto-formatting/fixing of specs
- Documentation generation for .parac/agents/specs/

The code in this module is the SOURCE OF TRUTH.
SCHEMA.md and TEMPLATE.md in .parac/agents/specs/ are GENERATED from here.
"""

from paracle_core.agents.doc_generator import AgentDocsGenerator
from paracle_core.agents.formatter import AgentSpecFormatter
from paracle_core.agents.schema import (
    AgentSpecSchema,
    GovernanceSection,
    ParacPaths,
    ResponsibilityCategory,
)
from paracle_core.agents.template import AgentTemplate
from paracle_core.agents.validator import (
    AgentSpecValidator,
    ValidationError,
    ValidationResult,
)

__all__ = [
    # Schema
    "AgentSpecSchema",
    "GovernanceSection",
    "ParacPaths",
    "ResponsibilityCategory",
    # Validation
    "AgentSpecValidator",
    "ValidationError",
    "ValidationResult",
    # Formatting
    "AgentSpecFormatter",
    # Template
    "AgentTemplate",
    # Docs
    "AgentDocsGenerator",
]
