"""Paracle Governance - Automatic .parac/ logging and tracking.

This module provides automatic governance logging that works regardless
of which AI assistant or IDE is being used. It integrates with the
framework to ensure all actions are logged to .parac/memory/logs/.

The key principle: "Declare once in .parac/, use everywhere."

Usage:
    from paracle_core.governance import governance_logger, log_action

    # Automatic logging for any action
    log_action("IMPLEMENTATION", "Added new feature X")

    # With specific agent context
    with governance_logger.agent_context("CoderAgent"):
        log_action("REFACTORING", "Improved error handling")

    # Automatic session tracking
    with governance_logger.session():
        # All actions within this session are logged
        ...

    # Layer 5: Continuous monitoring
    from paracle_core.governance import get_monitor

    monitor = get_monitor(auto_repair=True)
    monitor.start()
"""

from paracle_core.governance.ai_compliance import (
    AIAssistantMonitor,
    AIComplianceEngine,
    FileCategory,
    ValidationResult,
    get_assistant_monitor,
    get_compliance_engine,
)
from paracle_core.governance.auto_logger import (
    agent_operation,
    async_agent_operation,
    log_agent_action,
    sanitize_args,
)
from paracle_core.governance.context import (
    AgentContext,
    SessionContext,
    agent_context,
    session_context,
)
from paracle_core.governance.logger import (
    GovernanceLogger,
    get_governance_logger,
    log_action,
    log_decision,
    reset_governance_logger,
)
from paracle_core.governance.monitor import (
    GovernanceHealth,
    GovernanceMonitor,
    RepairAction,
    Violation,
    ViolationSeverity,
    get_monitor,
)
from paracle_core.governance.state_manager import (
    AutomaticStateManager,
    get_state_manager,
    reset_state_manager,
)
from paracle_core.governance.types import GovernanceActionType, GovernanceAgentType

__all__ = [
    # AI Compliance (Layer 3)
    "AIComplianceEngine",
    "AIAssistantMonitor",
    "ValidationResult",
    "FileCategory",
    "get_compliance_engine",
    "get_assistant_monitor",
    # Automatic logging
    "log_agent_action",
    "agent_operation",
    "async_agent_operation",
    "sanitize_args",
    # State management
    "AutomaticStateManager",
    "get_state_manager",
    "reset_state_manager",
    # Logger
    "GovernanceLogger",
    "get_governance_logger",
    "reset_governance_logger",
    "log_action",
    "log_decision",
    # Context
    "AgentContext",
    "SessionContext",
    "agent_context",
    "session_context",
    # Types
    "GovernanceActionType",
    "GovernanceAgentType",
]
