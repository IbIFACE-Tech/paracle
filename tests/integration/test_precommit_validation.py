"""Integration tests for Layer 4 - Pre-commit Validation.

Tests the git pre-commit hook that validates .parac/ structure
before allowing commits.
"""

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary git repository with .parac/ structure."""
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=tmp_path,
                   check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        check=True,
        capture_output=True
    )

    # Create .parac/ structure
    parac_dir = tmp_path / ".parac"
    parac_dir.mkdir()

    # Create required directories
    (parac_dir / "memory" / "data").mkdir(parents=True)
    (parac_dir / "memory" / "logs").mkdir(parents=True)
    (parac_dir / "memory" / "knowledge").mkdir(parents=True)
    (parac_dir / "roadmap").mkdir(parents=True)
    (parac_dir / "tools" / "hooks").mkdir(parents=True)

    # Copy the pre-commit hook
    hook_source = Path(__file__).parent.parent.parent.parent / \
        ".parac" / "tools" / "hooks" / "validate-structure.py"
    if hook_source.exists():
        hook_target = parac_dir / "tools" / "hooks" / "validate-structure.py"
        shutil.copy2(hook_source, hook_target)

        # Install hook to .git/hooks/
        git_hook = tmp_path / ".git" / "hooks" / "pre-commit"
        shutil.copy2(hook_source, git_hook)

        # Make executable
        if hasattr(os, 'chmod'):
            current_perms = stat.S_IMODE(os.lstat(git_hook).st_mode)
            os.chmod(git_hook, current_perms | stat.S_IXUSR |
                     stat.S_IXGRP | stat.S_IXOTH)

    return tmp_path


@pytest.fixture
def hook_script(git_repo):
    """Get path to the pre-commit hook script."""
    return git_repo / ".git" / "hooks" / "pre-commit"


class TestPreCommitHook:
    """Test suite for git pre-commit hook."""

    def test_hook_exists(self, git_repo, hook_script):
        """Test that the pre-commit hook is installed."""
        assert hook_script.exists(), "Pre-commit hook should be installed"

        # Check if executable (Unix/Mac)
        if hasattr(os, 'stat'):
            mode = os.stat(hook_script).st_mode
            assert mode & stat.S_IXUSR, "Hook should be executable"

    def test_commit_allowed_with_valid_files(self, git_repo):
        """Test that commits with valid .parac/ files are allowed."""
        # Create a valid file in correct location
        valid_file = git_repo / ".parac" / "memory" / "data" / "metrics.db"
        valid_file.write_text("test data")

        # Stage the file
        subprocess.run(
            ["git", "add", str(valid_file.relative_to(git_repo))],
            cwd=git_repo,
            check=True,
            capture_output=True
        )

        # Try to commit
        result = subprocess.run(
            ["git", "commit", "-m", "Test commit with valid file"],
            cwd=git_repo,
            capture_output=True,
            text=True
        )

        # Commit should succeed
        assert result.returncode == 0, f"Commit should succeed. Output: {result.stdout}\n{result.stderr}"
        assert "validated successfully" in result.stdout.lower() or result.returncode == 0

    def test_commit_blocked_with_invalid_files(self, git_repo):
        """Test that commits with invalid .parac/ files are blocked."""
        # Create a file in wrong location
        invalid_file = git_repo / ".parac" / "costs.db"  # Should be in memory/data/
        invalid_file.write_text("test data")

        # Stage the file
        subprocess.run(
            ["git", "add", str(invalid_file.relative_to(git_repo))],
            cwd=git_repo,
            check=True,
            capture_output=True
        )

        # Try to commit
        result = subprocess.run(
            ["git", "commit", "-m", "Test commit with invalid file"],
            cwd=git_repo,
            capture_output=True,
            text=True
        )

        # Commit should be blocked
        assert result.returncode != 0, "Commit should be blocked"
        assert "COMMIT BLOCKED" in result.stdout or "violation" in result.stdout.lower()

    def test_violation_message_shows_suggested_path(self, git_repo):
        """Test that violation messages include suggested fix."""
        # Create invalid file
        invalid_file = git_repo / ".parac" / "debug.log"  # Should be in memory/logs/
        invalid_file.write_text("log data")

        # Stage the file
        subprocess.run(
            ["git", "add", str(invalid_file.relative_to(git_repo))],
            cwd=git_repo,
            check=True,
            capture_output=True
        )

        # Try to commit
        result = subprocess.run(
            ["git", "commit", "-m", "Test commit"],
            cwd=git_repo,
            capture_output=True,
            text=True
        )

        # Check for suggested path
        output = result.stdout + result.stderr
        assert "memory/logs" in output, "Should suggest correct location"

    def test_bypass_with_no_verify(self, git_repo):
        """Test that --no-verify bypasses the hook."""
        # Create invalid file
        invalid_file = git_repo / ".parac" / "invalid.db"
        invalid_file.write_text("test data")

        # Stage the file
        subprocess.run(
            ["git", "add", str(invalid_file.relative_to(git_repo))],
            cwd=git_repo,
            check=True,
            capture_output=True
        )

        # Commit with --no-verify
        result = subprocess.run(
            ["git", "commit", "-m", "Test commit", "--no-verify"],
            cwd=git_repo,
            capture_output=True,
            text=True
        )

        # Commit should succeed (bypassed)
        assert result.returncode == 0, "Commit with --no-verify should succeed"

    def test_no_parac_files_allows_commit(self, git_repo):
        """Test that commits without .parac/ files are allowed."""
        # Create file outside .parac/
        regular_file = git_repo / "README.md"
        regular_file.write_text("# Test Project")

        # Stage the file
        subprocess.run(
            ["git", "add", "README.md"],
            cwd=git_repo,
            check=True,
            capture_output=True
        )

        # Try to commit
        result = subprocess.run(
            ["git", "commit", "-m", "Add README"],
            cwd=git_repo,
            capture_output=True,
            text=True
        )

        # Commit should succeed
        assert result.returncode == 0, "Commit without .parac/ files should succeed"

    def test_multiple_files_with_violations(self, git_repo):
        """Test validation with multiple files, some invalid."""
        # Create valid file
        valid_file = git_repo / ".parac" / "memory" / "data" / "costs.db"
        valid_file.write_text("valid data")

        # Create invalid file
        invalid_file = git_repo / ".parac" / "metrics.json"
        invalid_file.write_text("invalid data")

        # Stage both files
        subprocess.run(
            ["git", "add", ".parac/"],
            cwd=git_repo,
            check=True,
            capture_output=True
        )

        # Try to commit
        result = subprocess.run(
            ["git", "commit", "-m", "Test multiple files"],
            cwd=git_repo,
            capture_output=True,
            text=True
        )

        # Commit should be blocked due to invalid file
        assert result.returncode != 0, "Commit should be blocked"
        output = result.stdout + result.stderr
        assert "metrics.json" in output or "violation" in output.lower()


class TestHookInstallation:
    """Test hook installation via paracle init."""

    def test_hook_installed_on_init(self, tmp_path):
        """Test that pre-commit hook is installed during paracle init."""
        # Initialize git repo first
        subprocess.run(["git", "init"], cwd=tmp_path,
                       check=True, capture_output=True)

        # Run paracle init
        result = subprocess.run(
            ["paracle", "init", "--template", "lite"],
            cwd=tmp_path,
            capture_output=True,
            text=True
        )

        # Check that init succeeded
        assert result.returncode == 0, f"paracle init failed: {result.stderr}"

        # Check that hook was installed
        hook_path = tmp_path / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists(), "Pre-commit hook should be installed"

        # Check hook content
        hook_content = hook_path.read_text()
        assert "validate" in hook_content.lower() or "parac" in hook_content.lower()

    def test_hook_not_installed_without_git(self, tmp_path):
        """Test that hook installation is skipped if no git repo."""
        # Run paracle init without git repo
        result = subprocess.run(
            ["paracle", "init", "--template", "lite"],
            cwd=tmp_path,
            capture_output=True,
            text=True
        )

        # Init should succeed
        assert result.returncode == 0

        # Hook should not be installed (no .git directory)
        assert not (tmp_path / ".git" / "hooks" / "pre-commit").exists()


class TestHookPerformance:
    """Test hook performance and overhead."""

    def test_hook_runs_quickly(self, git_repo):
        """Test that the hook executes quickly."""
        import time

        # Create valid file
        valid_file = git_repo / ".parac" / "memory" / "logs" / "test.log"
        valid_file.write_text("test log")

        # Stage the file
        subprocess.run(
            ["git", "add", str(valid_file.relative_to(git_repo))],
            cwd=git_repo,
            check=True,
            capture_output=True
        )

        # Time the commit
        start_time = time.time()
        result = subprocess.run(
            ["git", "commit", "-m", "Performance test"],
            cwd=git_repo,
            capture_output=True,
            text=True
        )
        elapsed = time.time() - start_time

        # Hook should run in under 2 seconds
        assert elapsed < 2.0, f"Hook took {elapsed:.2f}s (should be < 2s)"
        assert result.returncode == 0


@pytest.mark.skipif(not shutil.which("git"), reason="git not available")
class TestRealWorldScenarios:
    """Test real-world commit scenarios."""

    def test_developer_workflow(self, git_repo):
        """Test typical developer workflow with mixed files."""
        # Developer creates multiple files
        files = [
            (git_repo / "src" / "main.py", "# Application code"),
            (git_repo / ".parac" / "memory" / "data" / "cache.db", "cache data"),
            (git_repo / "README.md", "# Project"),
        ]

        for file_path, content in files:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)

        # Stage all files
        subprocess.run(
            ["git", "add", "."],
            cwd=git_repo,
            check=True,
            capture_output=True
        )

        # Commit should succeed (all .parac/ files in correct locations)
        result = subprocess.run(
            ["git", "commit", "-m", "Feature implementation"],
            cwd=git_repo,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, "Valid commit should succeed"

    def test_ai_assistant_correction_workflow(self, git_repo):
        """Test workflow where AI assistant initially creates wrong file, then corrects."""
        # AI creates file in wrong location
        wrong_file = git_repo / ".parac" / "data.db"
        wrong_file.write_text("data")

        # Stage wrong file
        subprocess.run(
            ["git", "add", ".parac/data.db"],
            cwd=git_repo,
            check=True,
            capture_output=True
        )

        # Try to commit - should fail
        result1 = subprocess.run(
            ["git", "commit", "-m", "Add database"],
            cwd=git_repo,
            capture_output=True,
            text=True
        )
        assert result1.returncode != 0, "Commit with wrong file should fail"

        # AI moves file to correct location
        correct_file = git_repo / ".parac" / "memory" / "data" / "data.db"
        correct_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(wrong_file), str(correct_file))

        # Stage corrected file
        subprocess.run(
            ["git", "add", ".parac/"],
            cwd=git_repo,
            check=True,
            capture_output=True
        )

        # Commit should now succeed
        result2 = subprocess.run(
            ["git", "commit", "-m", "Add database (corrected)"],
            cwd=git_repo,
            capture_output=True,
            text=True
        )
        assert result2.returncode == 0, "Commit with corrected file should succeed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
