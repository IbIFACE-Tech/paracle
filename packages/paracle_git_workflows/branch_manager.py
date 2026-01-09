"""Branch manager for git-backed workflow execution."""

import logging
import subprocess
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class BranchInfo(BaseModel):
    """Information about an execution branch."""

    name: str = Field(..., description="Branch name")
    execution_id: str = Field(..., description="Execution ID")
    created_at: str = Field(..., description="Creation timestamp")
    base_branch: str = Field(default="main", description="Base branch")
    status: str = Field(
        default="active", description="Branch status (active/merged/deleted)"
    )
    commit_count: int = Field(default=0, description="Number of commits")


class BranchManager:
    """
    Manages git branches for workflow executions.

    Provides:
    - Branch creation per execution
    - Execution isolation via branches
    - Branch lifecycle management
    - Automatic cleanup of merged branches

    Branch naming convention: exec/{execution_id}/{timestamp}

    Example:
        >>> manager = BranchManager(repo_path=Path("."))
        >>> branch = manager.create_execution_branch(
        ...     execution_id="exec_abc123",
        ...     base_branch="main"
        ... )
        >>> # Work happens on branch
        >>> manager.merge_execution_branch(branch.name)
        >>> manager.cleanup_merged_branches()
    """

    def __init__(self, repo_path: Path):
        """
        Initialize branch manager.

        Args:
            repo_path: Path to git repository

        Raises:
            ValueError: If path is not a git repository
        """
        self.repo_path = repo_path.resolve()
        if not (self.repo_path / ".git").exists():
            raise ValueError(f"{repo_path} is not a git repository")

    def _run_git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        """Run git command in repository."""
        cmd = ["git", "-C", str(self.repo_path)] + list(args)
        return subprocess.run(cmd, capture_output=True, text=True, check=check)

    def create_execution_branch(
        self, execution_id: str, base_branch: str = "main"
    ) -> BranchInfo:
        """
        Create a new branch for workflow execution.

        Args:
            execution_id: Unique execution identifier
            base_branch: Base branch to branch from

        Returns:
            Branch information

        Raises:
            RuntimeError: If branch creation fails
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        branch_name = f"exec/{execution_id}/{timestamp}"

        try:
            # Ensure we're on base branch and up to date
            self._run_git("checkout", base_branch)
            self._run_git("pull", "--ff-only")

            # Create and checkout new branch
            self._run_git("checkout", "-b", branch_name)

            logger.info(
                f"Created execution branch '{branch_name}' " f"from '{base_branch}'"
            )

            return BranchInfo(
                name=branch_name,
                execution_id=execution_id,
                created_at=timestamp,
                base_branch=base_branch,
                status="active",
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create branch '{branch_name}': {e.stderr}")

    def merge_execution_branch(
        self, branch_name: str, target_branch: str = "main"
    ) -> bool:
        """
        Merge execution branch back to target branch.

        Args:
            branch_name: Execution branch to merge
            target_branch: Target branch (usually main)

        Returns:
            True if merged successfully

        Raises:
            RuntimeError: If merge fails
        """
        try:
            # Checkout target branch
            self._run_git("checkout", target_branch)

            # Pull latest
            self._run_git("pull", "--ff-only")

            # Merge execution branch
            self._run_git(
                "merge",
                "--no-ff",
                branch_name,
                "-m",
                f"Merge execution branch {branch_name}",
            )

            logger.info(f"Merged branch '{branch_name}' into '{target_branch}'")

            return True
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to merge branch '{branch_name}': {e.stderr}")

    def delete_execution_branch(self, branch_name: str, force: bool = False) -> bool:
        """
        Delete an execution branch.

        Args:
            branch_name: Branch to delete
            force: Force delete even if not merged

        Returns:
            True if deleted successfully
        """
        try:
            flag = "-D" if force else "-d"
            self._run_git("branch", flag, branch_name)

            logger.info(f"Deleted branch '{branch_name}'")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to delete branch '{branch_name}': {e.stderr}")
            return False

    def list_execution_branches(self) -> list[BranchInfo]:
        """
        List all execution branches.

        Returns:
            List of execution branch information
        """
        try:
            result = self._run_git("branch", "--list", "exec/*")
            branch_names = [
                line.strip().lstrip("* ")
                for line in result.stdout.strip().split("\n")
                if line.strip()
            ]

            branches = []
            for name in branch_names:
                # Parse branch name: exec/{execution_id}/{timestamp}
                parts = name.split("/")
                if len(parts) >= 3:
                    execution_id = parts[1]
                    timestamp = parts[2]

                    # Get commit count
                    try:
                        count_result = self._run_git("rev-list", "--count", name)
                        commit_count = int(count_result.stdout.strip())
                    except (subprocess.CalledProcessError, ValueError):
                        commit_count = 0

                    branches.append(
                        BranchInfo(
                            name=name,
                            execution_id=execution_id,
                            created_at=timestamp,
                            commit_count=commit_count,
                        )
                    )

            return branches
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list branches: {e.stderr}")
            return []

    def cleanup_merged_branches(self, target_branch: str = "main") -> int:
        """
        Cleanup execution branches that have been merged.

        Args:
            target_branch: Target branch to check against

        Returns:
            Number of branches cleaned up
        """
        try:
            # Get merged branches
            result = self._run_git(
                "branch", "--merged", target_branch, "--list", "exec/*"
            )

            branch_names = [
                line.strip().lstrip("* ")
                for line in result.stdout.strip().split("\n")
                if line.strip()
            ]

            count = 0
            for branch_name in branch_names:
                if self.delete_execution_branch(branch_name):
                    count += 1

            logger.info(f"Cleaned up {count} merged execution branches")
            return count
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to cleanup branches: {e.stderr}")
            return 0

    def get_current_branch(self) -> str:
        """
        Get current branch name.

        Returns:
            Current branch name
        """
        try:
            result = self._run_git("branch", "--show-current")
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return ""

    def switch_branch(self, branch_name: str) -> bool:
        """
        Switch to a different branch.

        Args:
            branch_name: Branch to switch to

        Returns:
            True if switched successfully
        """
        try:
            self._run_git("checkout", branch_name)
            logger.info(f"Switched to branch '{branch_name}'")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to switch branch: {e.stderr}")
            return False
