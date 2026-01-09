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
                "type": "object",
                "properties": {
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
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Commit message (use conventional commit format)",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory (defaults to current)",
                        "default": ".",
                    },
                },
                "required": ["message"],
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
                "type": "object",
                "properties": {
                    "cwd": {
                        "type": "string",
                        "description": "Working directory (defaults to current)",
                        "default": ".",
                    },
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
        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
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
                "type": "object",
                "properties": {
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
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "description": "Tag name (e.g., v1.0.0)",
                    },
                    "message": {
                        "type": "string",
                        "description": "Tag message",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory",
                        "default": ".",
                    },
                },
                "required": ["tag", "message"],
            },
        )

    async def _execute(self, tag: str, message: str, cwd: str = ".") -> dict:
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


class GitBranchTool(BaseTool):
    """Tool for managing git branches."""

    def __init__(self):
        super().__init__(
            name="git_branch",
            description="List, create, or delete git branches",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform",
                        "enum": ["list", "create", "delete", "current"],
                        "default": "list",
                    },
                    "name": {
                        "type": "string",
                        "description": "Branch name (for create/delete)",
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Force delete branch",
                        "default": False,
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory",
                        "default": ".",
                    },
                },
            },
        )

    async def _execute(
        self,
        action: str = "list",
        name: str = None,
        force: bool = False,
        cwd: str = ".",
    ) -> dict:
        """Execute git branch command."""
        if action == "list":
            cmd = ["git", "branch", "-a"]
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True, check=True
            )
            branches = [
                b.strip().lstrip("* ") for b in result.stdout.strip().split("\n") if b
            ]
            current = next(
                (
                    b.strip()[2:]
                    for b in result.stdout.strip().split("\n")
                    if b.startswith("*")
                ),
                None,
            )
            return {"branches": branches, "current": current}

        elif action == "current":
            cmd = ["git", "branch", "--show-current"]
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True, check=True
            )
            return {"current": result.stdout.strip()}

        elif action == "create":
            if not name:
                return {"error": "Branch name required for create action"}
            cmd = ["git", "branch", name]
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True, check=True
            )
            return {"action": "create", "branch": name, "success": True}

        elif action == "delete":
            if not name:
                return {"error": "Branch name required for delete action"}
            cmd = ["git", "branch", "-D" if force else "-d", name]
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True, check=True
            )
            return {"action": "delete", "branch": name, "success": True}

        return {"error": f"Unknown action: {action}"}


class GitCheckoutTool(BaseTool):
    """Tool for switching branches or restoring files."""

    def __init__(self):
        super().__init__(
            name="git_checkout",
            description="Switch branches or restore working tree files",
            parameters={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Branch name, commit hash, or file path",
                    },
                    "create": {
                        "type": "boolean",
                        "description": "Create new branch (-b flag)",
                        "default": False,
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory",
                        "default": ".",
                    },
                },
                "required": ["target"],
            },
        )

    async def _execute(self, target: str, create: bool = False, cwd: str = ".") -> dict:
        """Execute git checkout command."""
        cmd = ["git", "checkout"]
        if create:
            cmd.append("-b")
        cmd.append(target)

        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=True
        )
        return {
            "command": " ".join(cmd),
            "target": target,
            "created": create,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }


class GitMergeTool(BaseTool):
    """Tool for merging branches."""

    def __init__(self):
        super().__init__(
            name="git_merge",
            description="Merge a branch into current branch",
            parameters={
                "type": "object",
                "properties": {
                    "branch": {
                        "type": "string",
                        "description": "Branch to merge",
                    },
                    "no_ff": {
                        "type": "boolean",
                        "description": "Create merge commit even for fast-forward",
                        "default": False,
                    },
                    "message": {
                        "type": "string",
                        "description": "Merge commit message",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory",
                        "default": ".",
                    },
                },
                "required": ["branch"],
            },
        )

    async def _execute(
        self,
        branch: str,
        no_ff: bool = False,
        message: str = None,
        cwd: str = ".",
    ) -> dict:
        """Execute git merge command."""
        cmd = ["git", "merge", branch]
        if no_ff:
            cmd.append("--no-ff")
        if message:
            cmd.extend(["-m", message])

        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=True
        )
        return {
            "command": " ".join(cmd),
            "branch": branch,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }


class GitPullTool(BaseTool):
    """Tool for pulling changes from remote."""

    def __init__(self):
        super().__init__(
            name="git_pull",
            description="Fetch and merge changes from remote repository",
            parameters={
                "type": "object",
                "properties": {
                    "remote": {
                        "type": "string",
                        "description": "Remote name",
                        "default": "origin",
                    },
                    "branch": {
                        "type": "string",
                        "description": "Branch to pull",
                    },
                    "rebase": {
                        "type": "boolean",
                        "description": "Rebase instead of merge",
                        "default": False,
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory",
                        "default": ".",
                    },
                },
            },
        )

    async def _execute(
        self,
        remote: str = "origin",
        branch: str = None,
        rebase: bool = False,
        cwd: str = ".",
    ) -> dict:
        """Execute git pull command."""
        cmd = ["git", "pull"]
        if rebase:
            cmd.append("--rebase")
        cmd.append(remote)
        if branch:
            cmd.append(branch)

        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=True
        )
        return {
            "command": " ".join(cmd),
            "stdout": result.stdout,
            "stderr": result.stderr,
        }


class GitLogTool(BaseTool):
    """Tool for viewing git history."""

    def __init__(self):
        super().__init__(
            name="git_log",
            description="View git commit history",
            parameters={
                "type": "object",
                "properties": {
                    "count": {
                        "type": "integer",
                        "description": "Number of commits to show",
                        "default": 10,
                    },
                    "oneline": {
                        "type": "boolean",
                        "description": "Show abbreviated output",
                        "default": True,
                    },
                    "branch": {
                        "type": "string",
                        "description": "Branch to show history for",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory",
                        "default": ".",
                    },
                },
            },
        )

    async def _execute(
        self,
        count: int = 10,
        oneline: bool = True,
        branch: str = None,
        cwd: str = ".",
    ) -> dict:
        """Execute git log command."""
        cmd = ["git", "log", f"-{count}"]
        if oneline:
            cmd.append("--oneline")
        else:
            cmd.append("--pretty=format:%H|%an|%ad|%s")
        if branch:
            cmd.append(branch)

        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=True
        )

        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            if oneline:
                parts = line.split(" ", 1)
                commits.append(
                    {"hash": parts[0], "message": parts[1] if len(parts) > 1 else ""}
                )
            else:
                parts = line.split("|")
                if len(parts) >= 4:
                    commits.append(
                        {
                            "hash": parts[0],
                            "author": parts[1],
                            "date": parts[2],
                            "message": parts[3],
                        }
                    )

        return {"commits": commits, "count": len(commits)}


class GitDiffTool(BaseTool):
    """Tool for viewing changes."""

    def __init__(self):
        super().__init__(
            name="git_diff",
            description="Show changes between commits, branches, or working tree",
            parameters={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Target to diff against (commit, branch, or file)",
                    },
                    "staged": {
                        "type": "boolean",
                        "description": "Show staged changes",
                        "default": False,
                    },
                    "stat": {
                        "type": "boolean",
                        "description": "Show diffstat only",
                        "default": False,
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory",
                        "default": ".",
                    },
                },
            },
        )

    async def _execute(
        self,
        target: str = None,
        staged: bool = False,
        stat: bool = False,
        cwd: str = ".",
    ) -> dict:
        """Execute git diff command."""
        cmd = ["git", "diff"]
        if staged:
            cmd.append("--staged")
        if stat:
            cmd.append("--stat")
        if target:
            cmd.append(target)

        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=True
        )
        return {
            "command": " ".join(cmd),
            "diff": result.stdout,
            "has_changes": bool(result.stdout.strip()),
        }


class GitStashTool(BaseTool):
    """Tool for stashing changes."""

    def __init__(self):
        super().__init__(
            name="git_stash",
            description="Stash changes in working directory",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Stash action",
                        "enum": ["push", "pop", "list", "drop", "apply"],
                        "default": "push",
                    },
                    "message": {
                        "type": "string",
                        "description": "Stash message (for push)",
                    },
                    "index": {
                        "type": "integer",
                        "description": "Stash index (for pop/drop/apply)",
                        "default": 0,
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory",
                        "default": ".",
                    },
                },
            },
        )

    async def _execute(
        self,
        action: str = "push",
        message: str = None,
        index: int = 0,
        cwd: str = ".",
    ) -> dict:
        """Execute git stash command."""
        if action == "push":
            cmd = ["git", "stash", "push"]
            if message:
                cmd.extend(["-m", message])
        elif action == "pop":
            cmd = ["git", "stash", "pop", f"stash@{{{index}}}"]
        elif action == "apply":
            cmd = ["git", "stash", "apply", f"stash@{{{index}}}"]
        elif action == "drop":
            cmd = ["git", "stash", "drop", f"stash@{{{index}}}"]
        elif action == "list":
            cmd = ["git", "stash", "list"]
        else:
            return {"error": f"Unknown action: {action}"}

        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=True
        )

        if action == "list":
            stashes = [
                line.strip()
                for line in result.stdout.strip().split("\n")
                if line.strip()
            ]
            return {"stashes": stashes, "count": len(stashes)}

        return {
            "action": action,
            "command": " ".join(cmd),
            "stdout": result.stdout,
            "stderr": result.stderr,
        }


class GitResetTool(BaseTool):
    """Tool for resetting changes."""

    def __init__(self):
        super().__init__(
            name="git_reset",
            description="Reset current HEAD to specified state",
            parameters={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Target commit or HEAD~n",
                        "default": "HEAD",
                    },
                    "mode": {
                        "type": "string",
                        "description": "Reset mode",
                        "enum": ["soft", "mixed", "hard"],
                        "default": "mixed",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory",
                        "default": ".",
                    },
                },
            },
        )

    async def _execute(
        self, target: str = "HEAD", mode: str = "mixed", cwd: str = "."
    ) -> dict:
        """Execute git reset command."""
        cmd = ["git", "reset", f"--{mode}", target]
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=True
        )
        return {
            "command": " ".join(cmd),
            "target": target,
            "mode": mode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }


class GitFetchTool(BaseTool):
    """Tool for fetching from remote."""

    def __init__(self):
        super().__init__(
            name="git_fetch",
            description="Fetch branches and tags from remote repository",
            parameters={
                "type": "object",
                "properties": {
                    "remote": {
                        "type": "string",
                        "description": "Remote name",
                        "default": "origin",
                    },
                    "all": {
                        "type": "boolean",
                        "description": "Fetch all remotes",
                        "default": False,
                    },
                    "prune": {
                        "type": "boolean",
                        "description": "Prune deleted remote branches",
                        "default": False,
                    },
                    "tags": {
                        "type": "boolean",
                        "description": "Fetch all tags",
                        "default": False,
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory",
                        "default": ".",
                    },
                },
            },
        )

    async def _execute(
        self,
        remote: str = "origin",
        all: bool = False,
        prune: bool = False,
        tags: bool = False,
        cwd: str = ".",
    ) -> dict:
        """Execute git fetch command."""
        cmd = ["git", "fetch"]
        if all:
            cmd.append("--all")
        else:
            cmd.append(remote)
        if prune:
            cmd.append("--prune")
        if tags:
            cmd.append("--tags")

        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=True
        )
        return {
            "command": " ".join(cmd),
            "stdout": result.stdout,
            "stderr": result.stderr,
        }


class GitRemoteTool(BaseTool):
    """Tool for managing remotes."""

    def __init__(self):
        super().__init__(
            name="git_remote",
            description="Manage remote repositories",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform",
                        "enum": ["list", "add", "remove", "get-url"],
                        "default": "list",
                    },
                    "name": {
                        "type": "string",
                        "description": "Remote name",
                    },
                    "url": {
                        "type": "string",
                        "description": "Remote URL (for add)",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory",
                        "default": ".",
                    },
                },
            },
        )

    async def _execute(
        self,
        action: str = "list",
        name: str = None,
        url: str = None,
        cwd: str = ".",
    ) -> dict:
        """Execute git remote command."""
        if action == "list":
            cmd = ["git", "remote", "-v"]
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True, check=True
            )
            remotes = {}
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        remotes[parts[0]] = parts[1]
            return {"remotes": remotes}

        elif action == "add":
            if not name or not url:
                return {"error": "Name and URL required for add action"}
            cmd = ["git", "remote", "add", name, url]
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True, check=True
            )
            return {"action": "add", "name": name, "url": url, "success": True}

        elif action == "remove":
            if not name:
                return {"error": "Name required for remove action"}
            cmd = ["git", "remote", "remove", name]
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True, check=True
            )
            return {"action": "remove", "name": name, "success": True}

        elif action == "get-url":
            if not name:
                return {"error": "Name required for get-url action"}
            cmd = ["git", "remote", "get-url", name]
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True, check=True
            )
            return {"name": name, "url": result.stdout.strip()}

        return {"error": f"Unknown action: {action}"}


# Tool instances
git_add = GitAddTool()
git_commit = GitCommitTool()
git_status = GitStatusTool()
git_push = GitPushTool()
git_tag = GitTagTool()
git_branch = GitBranchTool()
git_checkout = GitCheckoutTool()
git_merge = GitMergeTool()
git_pull = GitPullTool()
git_log = GitLogTool()
git_diff = GitDiffTool()
git_stash = GitStashTool()
git_reset = GitResetTool()
git_fetch = GitFetchTool()
git_remote = GitRemoteTool()

__all__ = [
    "GitAddTool",
    "GitCommitTool",
    "GitStatusTool",
    "GitPushTool",
    "GitTagTool",
    "GitBranchTool",
    "GitCheckoutTool",
    "GitMergeTool",
    "GitPullTool",
    "GitLogTool",
    "GitDiffTool",
    "GitStashTool",
    "GitResetTool",
    "GitFetchTool",
    "GitRemoteTool",
    "git_add",
    "git_commit",
    "git_status",
    "git_push",
    "git_tag",
    "git_branch",
    "git_checkout",
    "git_merge",
    "git_pull",
    "git_log",
    "git_diff",
    "git_stash",
    "git_reset",
    "git_fetch",
    "git_remote",
]
