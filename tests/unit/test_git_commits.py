"""Unit tests for paracle_git package - AutoCommitManager and ConventionalCommit."""

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from paracle_git import (
    AutoCommitManager,
    CommitConfig,
    CommitType,
    ConventionalCommit,
    GitChange,
)


@pytest.fixture
def temp_repo():
    """Create temporary git repository."""
    temp_dir = tempfile.mkdtemp()
    repo_path = Path(temp_dir)

    # Initialize git repo
    subprocess.run(
        ["git", "init"],
        cwd=repo_path,
        capture_output=True,
        check=True,
    )

    # Configure git
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        capture_output=True,
        check=True,
    )

    yield repo_path
    shutil.rmtree(temp_dir)


@pytest.fixture
def auto_commit_manager(temp_repo):
    """Create AutoCommitManager with temporary repo."""
    return AutoCommitManager(str(temp_repo))


@pytest.fixture
def commit_config():
    """Create commit configuration."""
    return CommitConfig(
        enabled=True,
        require_approval=False,
        conventional_commits=True,
        prefix_agent_name=True,
        include_metadata=True,
    )


class TestConventionalCommit:
    """Test ConventionalCommit formatting."""

    def test_basic_commit(self):
        """Test basic conventional commit format."""
        commit = ConventionalCommit(
            type=CommitType.FEAT,
            description="Add user authentication",
        )

        formatted = commit.format()

        assert formatted.startswith("feat: Add user authentication")
        assert "BREAKING CHANGE" not in formatted

    def test_commit_with_scope(self):
        """Test commit with scope."""
        commit = ConventionalCommit(
            type=CommitType.FIX,
            scope="api",
            description="Fix validation error",
        )

        formatted = commit.format()

        assert formatted.startswith("fix(api): Fix validation error")

    def test_commit_with_body(self):
        """Test commit with body."""
        commit = ConventionalCommit(
            type=CommitType.DOCS,
            description="Update README",
            body="Added installation instructions and examples",
        )

        formatted = commit.format()

        assert "docs: Update README" in formatted
        assert "Added installation instructions" in formatted

    def test_breaking_change(self):
        """Test commit with breaking change."""
        commit = ConventionalCommit(
            type=CommitType.FEAT,
            description="New API version",
            breaking=True,
            body="Complete API redesign",
        )

        formatted = commit.format()

        assert "feat!: New API version" in formatted
        assert "BREAKING CHANGE" in formatted

    def test_commit_with_footer(self):
        """Test commit with footer."""
        commit = ConventionalCommit(
            type=CommitType.FIX,
            description="Fix bug #123",
            footer="Closes #123",
        )

        formatted = commit.format()

        assert "Closes #123" in formatted

    def test_all_commit_types(self):
        """Test all conventional commit types."""
        types = [
            CommitType.FEAT,
            CommitType.FIX,
            CommitType.DOCS,
            CommitType.STYLE,
            CommitType.REFACTOR,
            CommitType.PERF,
            CommitType.TEST,
            CommitType.BUILD,
            CommitType.CI,
            CommitType.CHORE,
            CommitType.REVERT,
        ]

        for commit_type in types:
            commit = ConventionalCommit(
                type=commit_type,
                description="Test description",
            )
            formatted = commit.format()
            assert formatted.startswith(commit_type.value)

    def test_parse_conventional_commit(self):
        """Test parsing conventional commit message."""
        message = "feat(api): Add new endpoint\n\nDetailed description"

        commit = ConventionalCommit.from_string(message)

        assert commit.type == CommitType.FEAT
        assert commit.scope == "api"
        assert commit.description == "Add new endpoint"
        assert commit.body == "Detailed description"


class TestAutoCommitManager:
    """Test AutoCommitManager functionality."""

    def test_initialization(self, auto_commit_manager, temp_repo):
        """Test AutoCommitManager initialization."""
        assert auto_commit_manager is not None
        assert auto_commit_manager.repo_path == Path(temp_repo)
        assert auto_commit_manager.is_git_repo() is True

    def test_is_git_repo(self, temp_repo):
        """Test git repository detection."""
        manager = AutoCommitManager(str(temp_repo))
        assert manager.is_git_repo() is True

        # Test non-git directory
        non_git_dir = tempfile.mkdtemp()
        manager_non_git = AutoCommitManager(non_git_dir)
        assert manager_non_git.is_git_repo() is False
        shutil.rmtree(non_git_dir)

    def test_get_changed_files_empty(self, auto_commit_manager):
        """Test getting changed files in clean repo."""
        changes = auto_commit_manager.get_changed_files()

        assert isinstance(changes, list)
        assert len(changes) == 0

    def test_get_changed_files_with_changes(self, auto_commit_manager, temp_repo):
        """Test detecting changed files."""
        # Create new file
        test_file = temp_repo / "test.txt"
        test_file.write_text("test content")

        changes = auto_commit_manager.get_changed_files()

        assert len(changes) > 0
        assert any(c.file_path == "test.txt" for c in changes)

    def test_stage_files(self, auto_commit_manager, temp_repo):
        """Test staging files."""
        # Create test file
        test_file = temp_repo / "stage_test.txt"
        test_file.write_text("content")

        # Stage file
        auto_commit_manager.stage_files(["stage_test.txt"])

        # Verify staged
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=temp_repo,
            capture_output=True,
            text=True,
        )

        assert "stage_test.txt" in result.stdout

    def test_create_commit_basic(self, auto_commit_manager, temp_repo):
        """Test creating basic commit."""
        # Create and stage file
        test_file = temp_repo / "commit_test.txt"
        test_file.write_text("content")
        auto_commit_manager.stage_files(["commit_test.txt"])

        # Create commit
        auto_commit_manager.create_commit(
            message="Test commit",
            agent_name="test_agent",
        )

        # Verify commit exists
        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=temp_repo,
            capture_output=True,
            text=True,
        )

        assert "Test commit" in result.stdout or "[test_agent]" in result.stdout

    def test_commit_agent_changes(self, auto_commit_manager, temp_repo, commit_config):
        """Test committing agent changes with conventional format."""
        # Create manager with config
        manager = AutoCommitManager(str(temp_repo), config=commit_config)

        # Create file
        test_file = temp_repo / "agent_change.txt"
        test_file.write_text("agent content")

        # Get changes
        changes = manager.get_changed_files()

        # Commit with agent tracking
        manager.commit_agent_changes(
            agent_name="coder_agent",
            changes=changes,
            commit_type=CommitType.FEAT,
            description="Implement new feature",
            scope="api",
            body="Added authentication endpoint",
        )

        # Verify commit
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%s"],
            cwd=temp_repo,
            capture_output=True,
            text=True,
        )

        assert "feat(api)" in result.stdout or "coder_agent" in result.stdout

    def test_get_commit_history(self, auto_commit_manager, temp_repo):
        """Test retrieving commit history."""
        # Create commits
        for i in range(3):
            test_file = temp_repo / f"file{i}.txt"
            test_file.write_text(f"content {i}")
            auto_commit_manager.stage_files([f"file{i}.txt"])
            auto_commit_manager.create_commit(f"Commit {i}")

        history = auto_commit_manager.get_commit_history(limit=5)

        assert len(history) >= 3

    def test_agent_name_prefix(self, temp_repo):
        """Test agent name prefixing."""
        config = CommitConfig(prefix_agent_name=True)
        manager = AutoCommitManager(str(temp_repo), config=config)

        # Create file and commit
        test_file = temp_repo / "prefix_test.txt"
        test_file.write_text("content")
        manager.stage_files(["prefix_test.txt"])

        manager.create_commit(
            message="Test message",
            agent_name="test_agent",
        )

        # Verify prefix
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%s"],
            cwd=temp_repo,
            capture_output=True,
            text=True,
        )

        assert "[test_agent]" in result.stdout or "test_agent" in result.stdout

    def test_metadata_enrichment(self, temp_repo):
        """Test metadata enrichment in commit message."""
        config = CommitConfig(include_metadata=True)
        manager = AutoCommitManager(str(temp_repo), config=config)

        # Create file
        test_file = temp_repo / "metadata_test.txt"
        test_file.write_text("content")

        changes = [GitChange(
            file_path="metadata_test.txt",
            change_type="added",
        )]

        manager.commit_agent_changes(
            agent_name="test_agent",
            changes=changes,
            commit_type=CommitType.FEAT,
            description="Test metadata",
        )

        # Verify metadata in commit body
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%b"],
            cwd=temp_repo,
            capture_output=True,
            text=True,
        )

        # Should have agent info or file count
        assert "Agent:" in result.stdout or "Files:" in result.stdout or "test_agent" in result.stdout


class TestGitChange:
    """Test GitChange model."""

    def test_git_change_creation(self):
        """Test creating GitChange."""
        change = GitChange(
            file_path="src/api.py",
            change_type="modified",
            diff_summary="Updated authentication logic",
        )

        assert change.file_path == "src/api.py"
        assert change.change_type == "modified"
        assert change.diff_summary == "Updated authentication logic"

    def test_change_types(self):
        """Test different change types."""
        types = ["added", "modified", "deleted"]

        for change_type in types:
            change = GitChange(
                file_path=f"file_{change_type}.txt",
                change_type=change_type,
            )
            assert change.change_type == change_type


class TestCommitConfig:
    """Test CommitConfig settings."""

    def test_default_config(self):
        """Test default configuration."""
        config = CommitConfig()

        assert config.enabled is True
        assert config.require_approval is False
        assert config.conventional_commits is True
        assert config.sign_commits is False
        assert config.prefix_agent_name is True
        assert config.include_metadata is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = CommitConfig(
            enabled=False,
            require_approval=True,
            conventional_commits=False,
            sign_commits=True,
            prefix_agent_name=False,
            include_metadata=False,
        )

        assert config.enabled is False
        assert config.require_approval is True
        assert config.conventional_commits is False
        assert config.sign_commits is True
        assert config.prefix_agent_name is False
        assert config.include_metadata is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
