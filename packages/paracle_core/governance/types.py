"""Governance types - Action and Agent type definitions.

These types define what actions can be logged and what agent types
exist in the governance system. They are used by all AI assistants
consistently.
"""

from enum import Enum


class GovernanceActionType(str, Enum):
    """Types of actions that can be logged to .parac/memory/logs/.

    These map to the governance log format:
    [TIMESTAMP] [AGENT] [ACTION] Description
    """

    # Development actions
    IMPLEMENTATION = "IMPLEMENTATION"  # New code implementation
    TEST = "TEST"  # Test creation or modification
    REVIEW = "REVIEW"  # Code review
    DOCUMENTATION = "DOCUMENTATION"  # Documentation writing
    REFACTORING = "REFACTORING"  # Code refactoring
    BUGFIX = "BUGFIX"  # Bug fix

    # Planning actions
    DECISION = "DECISION"  # Architectural decision
    PLANNING = "PLANNING"  # Task planning

    # System actions
    UPDATE = "UPDATE"  # .parac/ file updates
    SESSION = "SESSION"  # Session start/end
    SYNC = "SYNC"  # Synchronization actions
    VALIDATION = "VALIDATION"  # Validation checks
    INIT = "INIT"  # Initialization
    ERROR = "ERROR"  # Error logging and recovery
    START = "START"  # Operation start
    COMPLETION = "COMPLETION"  # Operation completion


class GovernanceAgentType(str, Enum):
    """Types of agents in the governance system.

    These agents are defined in .parac/agents/specs/ and can be
    adopted by any AI assistant. The governance system tracks
    which agent performed each action.
    """

    PM = "PMAgent"  # Project Manager
    ARCHITECT = "ArchitectAgent"  # System Architect
    CODER = "CoderAgent"  # Developer
    TESTER = "TesterAgent"  # QA Engineer
    REVIEWER = "ReviewerAgent"  # Code Reviewer
    DOCUMENTER = "DocumenterAgent"  # Tech Writer
    SYSTEM = "SystemAgent"  # System/Automation

    @classmethod
    def from_string(cls, value: str) -> "GovernanceAgentType":
        """Parse agent type from string, with fallback to SYSTEM.

        Args:
            value: Agent name (e.g., "CoderAgent", "coder", "CODER")

        Returns:
            Matching GovernanceAgentType
        """
        normalized = value.lower().replace("agent", "").strip()

        mapping = {
            "pm": cls.PM,
            "architect": cls.ARCHITECT,
            "coder": cls.CODER,
            "tester": cls.TESTER,
            "reviewer": cls.REVIEWER,
            "documenter": cls.DOCUMENTER,
            "system": cls.SYSTEM,
        }

        return mapping.get(normalized, cls.SYSTEM)
