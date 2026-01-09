"""Git integration for Paracle.

This module provides Git operations for automatic commits,
conventional commit formatting, and change tracking.
"""

from paracle_git.auto_commit import AutoCommitManager, CommitConfig, GitChange
from paracle_git.conventional import CommitType, ConventionalCommit

__all__ = [
    "AutoCommitManager",
    "CommitConfig",
    "GitChange",
    "ConventionalCommit",
    "CommitType",
]

__version__ = "1.0.1"
