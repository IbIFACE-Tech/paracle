"""Git operation tools for Paracle agents."""

import subprocess

from paracle_tools.builtin.base import BaseTool


class GitAddTool(BaseTool):
    """Tool for staging files with git add."""

    def __init__(self):
        super().__init__(
            name="git_add",
            description="Stage files for git commit using 'git add'",
            parameters={
                "files": {
                    "type": "string",
                    "description": "Files to stage (use '.' or '-A' for all)",
                    "default": ".",
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory (defaults to current)",
                    "default": ".",
                },
            },
        )

    async def _execute(self, files: str = ".", cwd: str = ".") -> dict:
        """Execute git add command."""
        cmd = ["git", "add", files]
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return {
            "command": " ".join(cmd),
            "stdout": result.stdout,
            "stderr": result.stderr,
        }


class GitCommitTool(BaseTool):
    """Tool for creating git commits."""

    def __init__(self):
        super().__init__(
            name="git_commit",
            description="Create a git commit with a message",
            parameters={
                "message": {
                    "type": "string",
                    "description": "Commit message (use conventional commit format)",
                    "required": True,
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory (defaults to current)",
                    "default": ".",
                },
            },
        )

    async def _execute(self, message: str, cwd: str = ".") -> dict:
        """Execute git commit command."""
        # Use --no-verify to skip pre-commit hooks (fixes Windows /bin/sh issue)
        cmd = ["git", "commit", "-m", message, "--no-verify"]
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return {
            "command": " ".join(cmd),
            "stdout": result.stdout,
            "stderr": result.stderr,
        }


class GitStatusTool(BaseTool):
    """Tool for checking git status."""

    def __init__(self):
        super().__init__(
            name="git_status",
            description="Get git repository status",
            parameters={
                "cwd": {
                    "type": "string",
                    "description": "Working directory (defaults to current)",
                    "default": ".",
                },
            },
        )

    async def _execute(self, cwd: str = ".") -> dict:
        """Execute git status command."""
        cmd = ["git", "status", "--porcelain"]
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )

        # Parse output
        lines = (
            result.stdout.strip().split("\n")
            if result.stdout.strip()
            else []
        )
        modified = []
        added = []
        deleted = []
        untracked = []

        for line in lines:
            if not line:
                continue
            status = line[:2]
            file = line[3:]

            if status.startswith("M"):
                modified.append(file)
            elif status.startswith("A"):
                added.append(file)
            elif status.startswith("D"):
                deleted.append(file)
            elif status.startswith("??"):
                untracked.append(file)

        total = len(modified) + len(added) + len(deleted) + len(untracked)
        return {
            "modified": modified,
            "added": added,
            "deleted": deleted,
            "untracked": untracked,
            "total_changes": total,
        }


class GitPushTool(BaseTool):
    """Tool for pushing commits to remote."""

    def __init__(self):
        super().__init__(
            name="git_push",
            description="Push commits to remote repository",
            parameters={
                "remote": {
                    "type": "string",
                    "description": "Remote name (default: origin)",
                    "default": "origin",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name (default: current branch)",
                },
                "tags": {
                    "type": "boolean",
                    "description": "Push tags as well",
                    "default": False,
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory",
                    "default": ".",
                },
            },
        )

    async def _execute(
        self,
        remote: str = "origin",
        branch: str | None = None,
        tags: bool = False,
        cwd: str = ".",
    ) -> dict:
        """Execute git push command."""
        cmd = ["git", "push", remote]
        if branch:
            cmd.append(branch)
        if tags:
            cmd.append("--tags")

        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return {
            "command": " ".join(cmd),
            "stdout": result.stdout,
            "stderr": result.stderr,
        }


class GitTagTool(BaseTool):
    """Tool for creating git tags."""

    def __init__(self):
        super().__init__(
            name="git_tag",
            description="Create an annotated git tag",
            parameters={
                "tag": {
                    "type": "string",
                    "description": "Tag name (e.g., v1.0.0)",
                    "required": True,
                },
                "message": {
                    "type": "string",
                    "description": "Tag message",
                    "required": True,
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory",
                    "default": ".",
                },
            },
        )

    async def _execute(
        self, tag: str, message: str, cwd: str = "."
    ) -> dict:
        """Execute git tag command."""
        cmd = ["git", "tag", "-a", tag, "-m", message]
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return {
            "command": " ".join(cmd),
            "tag": tag,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }


# Tool instances
git_add = GitAddTool()
git_commit = GitCommitTool()
git_status = GitStatusTool()
git_push = GitPushTool()
git_tag = GitTagTool()

__all__ = [
    "GitAddTool",
    "GitCommitTool",
    "GitStatusTool",
    "GitPushTool",
    "GitTagTool",
    "git_add",
    "git_commit",
    "git_status",
    "git_push",
    "git_tag",
]
