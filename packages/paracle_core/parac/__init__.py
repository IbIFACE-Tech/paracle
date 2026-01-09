"""Paracle Core - .parac/ Workspace Governance.

This module provides core functionality for managing .parac/ workspaces:
- State synchronization
- Validation
- Session management
- Action logging
- File management (logs, ADRs, roadmaps)
"""

from paracle_core.parac.adr_manager import ADR, ADRManager, ADRMetadata
from paracle_core.parac.file_config import (  # ADR configuration; Main configuration; Log configuration; Roadmap configuration
    ADRConfig,
    ADRDefaultsConfig,
    ADRLimitsConfig,
    ADRStatusConfig,
    ADRValidationConfig,
    CustomLogConfig,
    DeliverablesConfig,
    FileManagementConfig,
    LogFileConfig,
    LogGlobalConfig,
    LogsConfig,
    PhaseProgressConfig,
    PhasesConfig,
    PhaseStatusConfig,
    PredefinedLogsConfig,
    RoadmapConfig,
    RoadmapExportConfig,
    RoadmapFileConfig,
    RoadmapLimitsConfig,
    RoadmapSyncConfig,
    RoadmapValidationConfig,
)
from paracle_core.parac.logger import (
    ActionType,
    AgentLogger,
    AgentType,
    get_logger,
    log_action,
    log_to_custom,
)
from paracle_core.parac.roadmap_manager import (
    Roadmap,
    RoadmapManager,
    RoadmapMetadata,
    RoadmapPhase,
    SyncResult,
)
from paracle_core.parac.roadmap_manager import (
    ValidationResult as RoadmapValidationResult,
)
from paracle_core.parac.state import (
    ParacState,
    PhaseState,
    StateConflictError,
    StateLockError,
    find_parac_root,
    load_state,
    save_state,
)
from paracle_core.parac.sync import ParacSynchronizer
from paracle_core.parac.validator import ParacValidator, ValidationResult

__all__ = [
    # State management
    "ParacState",
    "load_state",
    "ParacState",
    "PhaseState",
    "StateConflictError",
    "StateLockError",
    "find_parac_root",
    "load_state",
    "save_state",
    # Validation
    "ParacValidator",
    "ValidationResult",
    # Synchronization
    "ParacSynchronizer",
    # Logging
    "ActionType",
    "AgentLogger",
    "AgentType",
    "get_logger",
    "log_action",
    "log_to_custom",
    # File configuration - Logs
    "LogGlobalConfig",
    "LogFileConfig",
    "PredefinedLogsConfig",
    "CustomLogConfig",
    "LogsConfig",
    # File configuration - ADR
    "ADRLimitsConfig",
    "ADRStatusConfig",
    "ADRDefaultsConfig",
    "ADRValidationConfig",
    "ADRConfig",
    # File configuration - Roadmap
    "RoadmapLimitsConfig",
    "PhaseStatusConfig",
    "PhaseProgressConfig",
    "PhasesConfig",
    "DeliverablesConfig",
    "RoadmapFileConfig",
    "RoadmapSyncConfig",
    "RoadmapValidationConfig",
    "RoadmapExportConfig",
    "RoadmapConfig",
    # File configuration - Main
    "FileManagementConfig",
    # ADR management
    "ADR",
    "ADRMetadata",
    "ADRManager",
    # Roadmap management
    "Roadmap",
    "RoadmapMetadata",
    "RoadmapPhase",
    "RoadmapManager",
    "RoadmapValidationResult",
    "SyncResult",
]
