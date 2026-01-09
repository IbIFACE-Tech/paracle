"""Paracle Core - Shared Utilities and Infrastructure.

This package provides core utilities and cross-cutting concerns:

Subpackages:
- logging: Enterprise-grade structured logging with audit trail
- governance: Automatic .parac/ logging and tracking
- parac: .parac/ workspace management and synchronization

Modules:
- storage: Multi-layer storage configuration
- ids: ULID and unique identifier generation

The subpackages are intentionally not re-exported at this level to:
1. Encourage explicit imports from subpackages
2. Avoid circular dependencies
3. Keep the top-level namespace clean

Usage:
    from paracle_core.logging import get_logger, configure_logging
    from paracle_core.governance import log_action, log_decision
    from paracle_core.parac import ParacState, ParacValidator
    from paracle_core.storage import StorageConfig, get_storage_config
    from paracle_core.ids import generate_ulid
"""

# Exceptions
from paracle_core.exceptions import (
    ConfigurationError,
    DependencyError,
    InitializationError,
    ParacleError,
    PermissionError,
    ResourceError,
    StateError,
    ValidationError,
    WorkspaceError,
)

# ID generation utilities
from paracle_core.ids import (
    generate_correlation_id,
    generate_session_id,
    generate_short_id,
    generate_ulid,
)

# System paths (cross-platform)
from paracle_core.paths import (
    Platform,
    SystemPaths,
    detect_platform,
    ensure_system_directories,
    get_system_info,
    get_system_paths,
    get_system_skills_dir,
)

# Storage configuration is safe to export at top level
from paracle_core.storage import (
    StorageConfig,
    StorageSettings,
    get_storage_config,
    reset_storage_config,
    set_storage_config,
)

__version__ = "1.0.1"

__all__ = [
    # Exceptions
    "ParacleError",
    "ConfigurationError",
    "InitializationError",
    "ValidationError",
    "WorkspaceError",
    "DependencyError",
    "ResourceError",
    "StateError",
    "PermissionError",
    # ID generation
    "generate_ulid",
    "generate_short_id",
    "generate_correlation_id",
    "generate_session_id",
    # Storage configuration
    "StorageConfig",
    "StorageSettings",
    "get_storage_config",
    "set_storage_config",
    "reset_storage_config",
    # System paths (cross-platform)
    "Platform",
    "SystemPaths",
    "detect_platform",
    "get_system_paths",
    "get_system_skills_dir",
    "ensure_system_directories",
    "get_system_info",
]

# Note: Other subpackages are not re-exported to avoid circular imports.
# Use explicit imports from the appropriate subpackage:
#   from paracle_core.logging import get_logger
#   from paracle_core.governance import log_action
#   from paracle_core.parac import ParacState
