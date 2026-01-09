"""
Git Workflow Manager for Paracle

Branch-per-execution management and git-backed workflow execution.
Provides isolation via git branches and automatic branch lifecycle management.
"""

__version__ = "1.0.1"

from paracle_git_workflows.branch_manager import BranchManager
from paracle_git_workflows.execution_manager import ExecutionManager

__all__ = ["BranchManager", "ExecutionManager"]
