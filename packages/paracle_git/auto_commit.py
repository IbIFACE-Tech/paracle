"""Automatic commit management for agent changes.

This module provides functionality to automatically create Git commits
when agents make changes to the codebase, using conventional commit format.
"""

import subprocess
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from paracle_git.conventional import CommitType, create_commit_message


class CommitConfig(BaseModel):
    """Configuration for automatic commits.

    Attributes:
        enabled: Whether auto-commit is enabled
        require_approval: Require human approval before committing
        conventional_commits: Use conventional commit format
        sign_commits: Sign commits with GPG
        prefix_agent_name: Prefix commit with agent name
        include_metadata: Include agent metadata in commit body
    """

    enabled: bool = True
    require_approval: bool = True
    conventional_commits: bool = True
    sign_commits: bool = False
    prefix_agent_name: bool = True
    include_metadata: bool = True


class GitChange(BaseModel):
    """Represents a file change for git commit.

    Attributes:
        file_path: Path to changed file
        change_type: Type of change (added, modified, deleted)
        diff_summary: Optional summary of changes
    """

    file_path: str
    change_type: str = Field(default="modified")  # added, modified, deleted
    diff_summary: str | None = None


class AutoCommitManager:
    """Manages automatic Git commits for agent changes.

    This class handles creating conventional commits for changes
    made by agents during workflow execution.
    """

    def __init__(
        self,
        repo_path: Path | str,
        config: CommitConfig | None = None,
    ):
        """Initialize auto-commit manager.

        Args:
            repo_path: Path to Git repository
            config: Commit configuration
        """
        self.repo_path = Path(repo_path)
        self.config = config or CommitConfig()

    def is_git_repo(self) -> bool:
        """Check if path is a Git repository.

        Returns:
            True if valid Git repo
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_changed_files(self) -> list[GitChange]:
        """Get list of changed files in working directory.

        Returns:
            List of GitChange objects
        """
        if not self.is_git_repo():
            return []

        try:
            # Get status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            changes = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                status = line[:2]
                file_path = line[3:]

                if status.strip() == "M":
                    change_type = "modified"
                elif status.strip() in ("A", "??"):
                    change_type = "added"
                elif status.strip() == "D":
                    change_type = "deleted"
                else:
                    change_type = "modified"

                changes.append(
                    GitChange(
                        file_path=file_path,
                        change_type=change_type,
                    )
                )

            return changes

        except Exception as e:
            print(f"Error getting changed files: {e}")
            return []

    def stage_files(self, file_paths: list[str]) -> bool:
        """Stage files for commit.

        Args:
            file_paths: List of file paths to stage

        Returns:
            True if successful
        """
        if not file_paths:
            return True

        try:
            subprocess.run(
                ["git", "add"] + file_paths,
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )
            return True
        except Exception as e:
            print(f"Error staging files: {e}")
            return False

    def create_commit(
        self,
        message: str,
        agent_name: str | None = None,
        file_paths: list[str] | None = None,
    ) -> bool:
        """Create a Git commit.

        Args:
            message: Commit message
            agent_name: Name of agent making changes
            file_paths: Optional list of specific files to commit

        Returns:
            True if commit successful
        """
        if not self.config.enabled:
            return False

        if not self.is_git_repo():
            print("Not a git repository")
            return False

        # Stage files
        if file_paths:
            if not self.stage_files(file_paths):
                return False
        else:
            # Stage all changes
            if not self.stage_files(["-A"]):
                return False

        # Add agent prefix if configured
        if self.config.prefix_agent_name and agent_name:
            message = f"[{agent_name}] {message}"

        # Build commit command
        cmd = ["git", "commit", "-m", message]
        if self.config.sign_commits:
            cmd.append("-S")

        try:
            subprocess.run(
                cmd,
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error creating commit: {e.stderr.decode()}")
            return False

    def commit_agent_changes(
        self,
        agent_name: str,
        changes: list[GitChange],
        commit_type: CommitType,
        description: str,
        scope: str | None = None,
        body: str | None = None,
    ) -> bool:
        """Create a commit for agent changes using conventional format.

        Args:
            agent_name: Name of agent making changes
            changes: List of changes to commit
            commit_type: Type of commit (feat, fix, etc)
            description: Short description
            scope: Optional scope
            body: Optional body

        Returns:
            True if commit successful
        """
        if not self.config.enabled:
            return False

        # Build commit message
        if self.config.conventional_commits:
            # Add metadata to body if configured
            if self.config.include_metadata:
                metadata = [
                    f"Agent: {agent_name}",
                    f"Timestamp: {datetime.utcnow().isoformat()}",
                    f"Files changed: {len(changes)}",
                ]
                if body:
                    body = f"{body}\n\n" + "\n".join(metadata)
                else:
                    body = "\n".join(metadata)

            message = create_commit_message(
                type=commit_type,
                description=description,
                scope=scope,
                body=body,
            )
        else:
            # Simple format
            message = f"{description}\n\n{body}" if body else description

        # Get file paths
        file_paths = [change.file_path for change in changes]

        # Create commit
        return self.create_commit(
            message=message,
            agent_name=agent_name if not self.config.conventional_commits else None,
            file_paths=file_paths,
        )

    def get_commit_history(self, limit: int = 10) -> list[str]:
        """Get recent commit history.

        Args:
            limit: Number of commits to retrieve

        Returns:
            List of commit messages
        """
        if not self.is_git_repo():
            return []

        try:
            result = subprocess.run(
                ["git", "log", f"-{limit}", "--oneline"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip().split("\n")
        except Exception:
            return []
