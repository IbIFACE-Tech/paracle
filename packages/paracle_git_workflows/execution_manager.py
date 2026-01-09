"""Execution manager for git-backed workflow execution."""

import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from paracle_git_workflows.branch_manager import BranchInfo, BranchManager

logger = logging.getLogger(__name__)


class ExecutionConfig(BaseModel):
    """Configuration for git-backed execution."""

    enable_branching: bool = Field(
        default=True, description="Create branch per execution"
    )
    auto_commit: bool = Field(
        default=True, description="Auto-commit changes during execution"
    )
    auto_merge: bool = Field(
        default=False, description="Auto-merge after successful execution"
    )
    auto_cleanup: bool = Field(default=True, description="Auto-cleanup merged branches")
    base_branch: str = Field(default="main", description="Base branch for executions")


class ExecutionManager:
    """
    Manages git-backed workflow executions.

    Provides:
    - Branch-per-execution isolation
    - Automatic committing of changes
    - Merge on success
    - Cleanup of completed branches

    Example:
        >>> manager = ExecutionManager(
        ...     repo_path=Path("."),
        ...     config=ExecutionConfig(
        ...         enable_branching=True,
        ...         auto_commit=True,
        ...         auto_merge=True
        ...     )
        ... )
        >>>
        >>> # Start execution
        >>> context = manager.start_execution("exec_abc123")
        >>>
        >>> # Execution happens...
        >>> # Changes are auto-committed
        >>>
        >>> # Complete execution
        >>> manager.complete_execution("exec_abc123", success=True)
        >>> # Branch is auto-merged and cleaned up
    """

    def __init__(self, repo_path: Path, config: ExecutionConfig | None = None):
        """
        Initialize execution manager.

        Args:
            repo_path: Path to git repository
            config: Execution configuration
        """
        self.repo_path = repo_path
        self.config = config or ExecutionConfig()
        self.branch_manager = BranchManager(repo_path)
        self._active_executions: dict[str, BranchInfo] = {}

    def start_execution(self, execution_id: str) -> dict[str, Any]:
        """
        Start a new git-backed execution.

        Args:
            execution_id: Unique execution identifier

        Returns:
            Execution context with branch info
        """
        if not self.config.enable_branching:
            return {"execution_id": execution_id, "branching_enabled": False}

        # Create execution branch
        branch_info = self.branch_manager.create_execution_branch(
            execution_id=execution_id, base_branch=self.config.base_branch
        )

        # Track active execution
        self._active_executions[execution_id] = branch_info

        logger.info(
            f"Started execution '{execution_id}' " f"on branch '{branch_info.name}'"
        )

        return {
            "execution_id": execution_id,
            "branch_name": branch_info.name,
            "base_branch": branch_info.base_branch,
            "branching_enabled": True,
        }

    def commit_changes(
        self, execution_id: str, message: str, files: list | None = None
    ) -> bool:
        """
        Commit changes during execution.

        Args:
            execution_id: Execution identifier
            message: Commit message
            files: Specific files to commit (None = all changes)

        Returns:
            True if committed successfully
        """
        if not self.config.auto_commit:
            return False

        branch_info = self._active_executions.get(execution_id)
        if not branch_info:
            logger.warning(f"No active execution found for '{execution_id}'")
            return False

        try:
            # Stage files
            if files:
                for file in files:
                    self.branch_manager._run_git("add", str(file))
            else:
                self.branch_manager._run_git("add", "-A")

            # Check if there are changes to commit
            status = self.branch_manager._run_git("status", "--porcelain", check=False)
            if not status.stdout.strip():
                logger.debug("No changes to commit")
                return True

            # Commit
            self.branch_manager._run_git("commit", "-m", f"[{execution_id}] {message}")

            logger.info(f"Committed changes for execution '{execution_id}'")
            return True
        except Exception as e:
            logger.error(f"Failed to commit changes for '{execution_id}': {e}")
            return False

    def complete_execution(self, execution_id: str, success: bool) -> bool:
        """
        Complete an execution and handle branch lifecycle.

        Args:
            execution_id: Execution identifier
            success: Whether execution was successful

        Returns:
            True if completed successfully
        """
        branch_info = self._active_executions.get(execution_id)
        if not branch_info:
            logger.warning(f"No active execution found for '{execution_id}'")
            return False

        try:
            if success and self.config.auto_merge:
                # Merge back to base branch
                self.branch_manager.merge_execution_branch(
                    branch_name=branch_info.name, target_branch=branch_info.base_branch
                )

                # Delete merged branch if auto-cleanup enabled
                if self.config.auto_cleanup:
                    self.branch_manager.delete_execution_branch(
                        branch_name=branch_info.name
                    )
            else:
                # Keep branch for manual review
                logger.info(
                    f"Execution branch '{branch_info.name}' kept " f"for manual review"
                )

            # Remove from active executions
            del self._active_executions[execution_id]

            logger.info(f"Completed execution '{execution_id}' " f"(success={success})")
            return True
        except Exception as e:
            logger.error(f"Error completing execution '{execution_id}': {e}")
            return False

    def list_active_executions(self) -> dict[str, BranchInfo]:
        """
        List all active executions.

        Returns:
            Dictionary mapping execution IDs to branch info
        """
        return self._active_executions.copy()

    def cleanup_old_branches(self, days: int = 7) -> int:
        """
        Cleanup old execution branches (merged and older than N days).

        Args:
            days: Age threshold in days

        Returns:
            Number of branches cleaned up
        """
        # For now, just cleanup merged branches
        # TODO: Add age-based filtering
        return self.branch_manager.cleanup_merged_branches(
            target_branch=self.config.base_branch
        )
