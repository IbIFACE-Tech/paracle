"""Synchronization for .parac/ workspace.

Synchronizes .parac/ state with project reality (git, tests, etc.).
"""

import subprocess
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from paracle_core.parac.state import ParacState, load_state, save_state


@dataclass
class SyncResult:
    """Result of synchronization."""

    success: bool
    changes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def add_change(self, description: str) -> None:
        """Record a change made."""
        self.changes.append(description)

    def add_error(self, description: str) -> None:
        """Record an error."""
        self.errors.append(description)
        self.success = False


@dataclass
class GitInfo:
    """Git repository information."""

    branch: str = "unknown"
    last_commit: str = "unknown"
    has_uncommitted_changes: bool = False
    ahead: int = 0
    behind: int = 0


class ParacSynchronizer:
    """Synchronizes .parac/ state with project reality."""

    def __init__(self, parac_root: Path, project_root: Path | None = None) -> None:
        """Initialize synchronizer.

        Args:
            parac_root: Path to .parac/ directory.
            project_root: Path to project root. Defaults to parac_root parent.
        """
        self.parac_root = parac_root
        self.project_root = project_root or parac_root.parent

    def sync(
        self,
        update_git: bool = True,
        update_metrics: bool = True,
        update_agent_docs: bool = True,
    ) -> SyncResult:
        """Synchronize state with project reality.

        Args:
            update_git: Whether to update git information.
            update_metrics: Whether to update file metrics.
            update_agent_docs: Whether to ensure agent docs exist.

        Returns:
            SyncResult with changes made.
        """
        result = SyncResult(success=True)

        state = load_state(self.parac_root)
        if state is None:
            result.add_error("Failed to load current state")
            return result

        original_snapshot = state.snapshot_date

        if update_git:
            self._sync_git_info(state, result)

        if update_metrics:
            self._sync_metrics(state, result)

        if update_agent_docs:
            self._sync_agent_docs(result)

        # Update snapshot date
        state.snapshot_date = str(date.today())
        if state.snapshot_date != original_snapshot:
            result.add_change(f"Updated snapshot_date to {state.snapshot_date}")

        # Save if changes were made
        if result.changes:
            if save_state(state, self.parac_root):
                result.add_change("Saved updated state")
            else:
                result.add_error("Failed to save state")

        return result

    def get_git_info(self) -> GitInfo:
        """Get current git repository information.

        Returns:
            GitInfo with current git state.
        """
        info = GitInfo()

        # Current branch
        success, output = self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
        if success:
            info.branch = output.strip()

        # Last commit
        success, output = self._run_git_command(["log", "-1", "--format=%h %s"])
        if success:
            info.last_commit = output.strip()

        # Uncommitted changes
        success, output = self._run_git_command(["status", "--porcelain"])
        if success:
            info.has_uncommitted_changes = bool(output.strip())

        return info

    def _sync_git_info(self, state: ParacState, result: SyncResult) -> None:
        """Update git information in state."""
        git_info = self.get_git_info()

        if "repository" not in state.raw_data:
            state.raw_data["repository"] = {}

        repo = state.raw_data["repository"]
        changes = []

        if repo.get("branch") != git_info.branch:
            changes.append(f"branch: {repo.get('branch')} → {git_info.branch}")
            repo["branch"] = git_info.branch

        if repo.get("last_commit") != git_info.last_commit:
            changes.append("last_commit updated")
            repo["last_commit"] = git_info.last_commit

        repo["has_uncommitted_changes"] = git_info.has_uncommitted_changes

        if changes:
            result.add_change(f"Git info updated: {', '.join(changes)}")

    def _sync_metrics(self, state: ParacState, result: SyncResult) -> None:
        """Update file metrics in state."""
        packages_dir = self.project_root / "packages"
        tests_dir = self.project_root / "tests"

        if "metrics" not in state.raw_data:
            state.raw_data["metrics"] = {}

        metrics = state.raw_data["metrics"]
        changes = []

        if packages_dir.exists():
            py_count = len(list(packages_dir.rglob("*.py")))
            if metrics.get("python_files") != py_count:
                changes.append(
                    f"python_files: {metrics.get('python_files')} → {py_count}"
                )
                metrics["python_files"] = py_count

        if tests_dir.exists():
            test_count = len(list(tests_dir.rglob("test_*.py")))
            if metrics.get("test_files") != test_count:
                changes.append(
                    f"test_files: {metrics.get('test_files')} → {test_count}"
                )
                metrics["test_files"] = test_count

        if changes:
            result.add_change(f"Metrics updated: {', '.join(changes)}")

    def _sync_agent_docs(self, result: SyncResult) -> None:
        """Ensure agent documentation files exist.

        Generates SCHEMA.md and TEMPLATE.md in .parac/agents/specs/
        if they don't exist or are outdated.
        """
        specs_dir = self.parac_root / "agents" / "specs"

        if not specs_dir.exists():
            # No specs directory, nothing to do
            return

        try:
            from paracle_core.agents.doc_generator import AgentDocsGenerator

            generator = AgentDocsGenerator(specs_dir)
            if generator.ensure_docs_exist(specs_dir):
                result.add_change("Generated agent docs (SCHEMA.md, TEMPLATE.md)")
        except ImportError:
            # Agent module not available, skip
            pass
        except Exception as e:
            result.add_error(f"Failed to generate agent docs: {e}")

    def _run_git_command(self, args: list[str]) -> tuple[bool, str]:
        """Run a git command.

        Args:
            args: Git command arguments (without 'git').

        Returns:
            Tuple of (success, output).
        """
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0, result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False, ""

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of current project state.

        Returns:
            Dictionary with summary information.
        """
        state = load_state(self.parac_root)
        git_info = self.get_git_info()

        summary: dict[str, Any] = {
            "parac_root": str(self.parac_root),
            "project_root": str(self.project_root),
            "git": {
                "branch": git_info.branch,
                "last_commit": git_info.last_commit,
                "has_changes": git_info.has_uncommitted_changes,
            },
        }

        if state:
            summary["phase"] = {
                "id": state.current_phase.id,
                "name": state.current_phase.name,
                "status": state.current_phase.status,
                "progress": state.current_phase.progress,
            }
            summary["snapshot_date"] = state.snapshot_date
            summary["blockers"] = len(state.blockers)
            summary["next_actions"] = len(state.next_actions)

        return summary
