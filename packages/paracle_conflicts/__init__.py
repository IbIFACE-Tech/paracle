"""Conflict resolution for concurrent agent execution.

This module provides mechanisms to detect and resolve conflicts
when multiple agents modify the same files concurrently.
"""

from paracle_conflicts.detector import ConflictDetector, FileConflict
from paracle_conflicts.lock import FileLock, LockManager
from paracle_conflicts.resolver import (
    ConflictResolver,
    ResolutionResult,
    ResolutionStrategy,
)

__all__ = [
    "ConflictDetector",
    "FileConflict",
    "ConflictResolver",
    "ResolutionResult",
    "ResolutionStrategy",
    "FileLock",
    "LockManager",
]

__version__ = "1.0.1"
