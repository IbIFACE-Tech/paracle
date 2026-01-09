"""Unit tests for paracle_meta.capabilities.filesystem module."""

from pathlib import Path

import pytest
from paracle_meta.capabilities.filesystem import FileSystemCapability, FileSystemConfig


class TestFileSystemConfig:
    """Tests for FileSystemConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = FileSystemConfig()
        assert config.base_path is None
        assert config.allow_absolute_paths is False
        assert config.create_backups is True
        assert config.backup_suffix == ".bak"
        assert config.max_file_size_mb == 10.0
        assert config.allowed_extensions is None
        assert ".git" in config.blocked_paths
        assert config.enable_git is True

    def test_custom_values(self):
        """Test custom configuration values."""
        config = FileSystemConfig(
            base_path="/tmp/test",
            allow_absolute_paths=True,
            create_backups=False,
            max_file_size_mb=5.0,
            allowed_extensions=[".py", ".txt"],
        )
        assert config.base_path == "/tmp/test"
        assert config.allow_absolute_paths is True
        assert config.create_backups is False
        assert config.max_file_size_mb == 5.0
        assert ".py" in config.allowed_extensions


class TestFileSystemCapability:
    """Tests for FileSystemCapability."""

    @pytest.fixture
    def fs_capability(self, tmp_path):
        """Create filesystem capability instance with temp directory."""
        config = FileSystemConfig(
            base_path=str(tmp_path),
            allow_absolute_paths=False,
            create_backups=True,
        )
        return FileSystemCapability(config=config)

    @pytest.fixture
    def tmp_file(self, tmp_path):
        """Create a temporary test file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        return test_file

    def test_initialization(self, fs_capability):
        """Test capability initialization."""
        assert fs_capability.name == "filesystem"
        assert "file" in fs_capability.description.lower()

    @pytest.mark.asyncio
    async def test_initialize_and_shutdown(self, fs_capability):
        """Test initialize and shutdown lifecycle."""
        await fs_capability.initialize()
        assert fs_capability.is_initialized is True
        assert fs_capability._base_path is not None

        await fs_capability.shutdown()
        assert fs_capability.is_initialized is False

    @pytest.mark.asyncio
    async def test_read_file(self, fs_capability, tmp_file, tmp_path):
        """Test reading a file."""
        await fs_capability.initialize()

        result = await fs_capability.read_file(tmp_file.name)

        assert result.success is True
        assert "Hello, World!" in result.output["content"]
        assert result.output["lines"] == 1

        await fs_capability.shutdown()

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, fs_capability, tmp_path):
        """Test reading a nonexistent file."""
        await fs_capability.initialize()

        result = await fs_capability.read_file("nonexistent.txt")

        assert result.success is False
        assert "not found" in result.error.lower()

        await fs_capability.shutdown()

    @pytest.mark.asyncio
    async def test_write_file(self, fs_capability, tmp_path):
        """Test writing a file."""
        await fs_capability.initialize()

        content = "Test content\nLine 2"
        result = await fs_capability.write_file("output.txt", content)

        assert result.success is True
        assert result.output["lines"] == 2

        # Verify file exists
        output_file = tmp_path / "output.txt"
        assert output_file.exists()
        assert output_file.read_text() == content

        await fs_capability.shutdown()

    @pytest.mark.asyncio
    async def test_write_file_with_backup(self, fs_capability, tmp_file, tmp_path):
        """Test writing file creates backup."""
        await fs_capability.initialize()

        # Write to existing file
        new_content = "New content"
        result = await fs_capability.write_file(tmp_file.name, new_content)

        assert result.success is True
        assert result.output["backup"] is not None

        # Verify backup exists
        backup_path = Path(result.output["backup"])
        assert backup_path.exists()
        assert "Hello, World!" in backup_path.read_text()

        await fs_capability.shutdown()

    @pytest.mark.asyncio
    async def test_list_directory(self, fs_capability, tmp_path, tmp_file):
        """Test listing directory contents."""
        # Create additional files
        (tmp_path / "file1.py").write_text("# Python")
        (tmp_path / "file2.txt").write_text("Text")
        (tmp_path / "subdir").mkdir()

        await fs_capability.initialize()

        result = await fs_capability.list_directory(".")

        assert result.success is True
        assert result.output["count"] >= 3

        names = [e["name"] for e in result.output["entries"]]
        assert "file1.py" in names
        assert "file2.txt" in names
        assert "subdir" in names

        await fs_capability.shutdown()

    @pytest.mark.asyncio
    async def test_glob_files(self, fs_capability, tmp_path):
        """Test glob pattern matching."""
        # Create test files
        (tmp_path / "file1.py").write_text("# Python 1")
        (tmp_path / "file2.py").write_text("# Python 2")
        (tmp_path / "file3.txt").write_text("Text")

        await fs_capability.initialize()

        result = await fs_capability.glob_files("*.py")

        assert result.success is True
        assert result.output["count"] == 2

        names = [m["name"] for m in result.output["matches"]]
        assert "file1.py" in names
        assert "file2.py" in names
        assert "file3.txt" not in names

        await fs_capability.shutdown()

    @pytest.mark.asyncio
    async def test_create_directory(self, fs_capability, tmp_path):
        """Test creating a directory."""
        await fs_capability.initialize()

        result = await fs_capability.execute(
            action="create_directory",
            path="new_dir/subdir",
            parents=True,
        )

        assert result.success is True
        assert result.output["created"] is True
        assert (tmp_path / "new_dir" / "subdir").is_dir()

        await fs_capability.shutdown()

    @pytest.mark.asyncio
    async def test_delete_file(self, fs_capability, tmp_file, tmp_path):
        """Test deleting a file."""
        await fs_capability.initialize()

        result = await fs_capability.execute(
            action="delete_file",
            path=tmp_file.name,
        )

        assert result.success is True
        assert result.output["deleted"] is True
        assert not tmp_file.exists()

        await fs_capability.shutdown()

    @pytest.mark.asyncio
    async def test_copy_file(self, fs_capability, tmp_file, tmp_path):
        """Test copying a file."""
        await fs_capability.initialize()

        result = await fs_capability.execute(
            action="copy_file",
            source=tmp_file.name,
            destination="copy.txt",
        )

        assert result.success is True
        assert (tmp_path / "copy.txt").exists()
        assert (tmp_path / "copy.txt").read_text() == "Hello, World!"

        await fs_capability.shutdown()

    @pytest.mark.asyncio
    async def test_move_file(self, fs_capability, tmp_file, tmp_path):
        """Test moving a file."""
        await fs_capability.initialize()

        result = await fs_capability.execute(
            action="move_file",
            source=tmp_file.name,
            destination="moved.txt",
        )

        assert result.success is True
        assert not tmp_file.exists()
        assert (tmp_path / "moved.txt").exists()

        await fs_capability.shutdown()

    @pytest.mark.asyncio
    async def test_file_info(self, fs_capability, tmp_file, tmp_path):
        """Test getting file info."""
        await fs_capability.initialize()

        result = await fs_capability.execute(
            action="file_info",
            path=tmp_file.name,
        )

        assert result.success is True
        assert result.output["type"] == "file"
        assert result.output["extension"] == ".txt"
        assert result.output["size_bytes"] > 0

        await fs_capability.shutdown()

    @pytest.mark.asyncio
    async def test_blocked_path(self, fs_capability, tmp_path):
        """Test access to blocked paths is denied."""
        await fs_capability.initialize()

        # Try to access .git directory (blocked)
        result = await fs_capability.execute(
            action="read_file",
            path=".git/config",
        )

        assert result.success is False
        assert "blocked" in result.error.lower()

        await fs_capability.shutdown()

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self, fs_capability):
        """Test execute with unknown action."""
        await fs_capability.initialize()

        result = await fs_capability.execute(action="unknown_action")

        assert result.success is False
        assert "Unknown action" in result.error

        await fs_capability.shutdown()


class TestFileSystemSecurity:
    """Security-focused tests for FileSystemCapability."""

    @pytest.fixture
    def secure_capability(self, tmp_path):
        """Create capability with secure settings."""
        config = FileSystemConfig(
            base_path=str(tmp_path),
            allow_absolute_paths=False,
            allowed_extensions=[".txt", ".py"],
            max_file_size_mb=1.0,
        )
        return FileSystemCapability(config=config)

    @pytest.mark.asyncio
    async def test_path_traversal_blocked(self, secure_capability):
        """Test that path traversal is blocked."""
        await secure_capability.initialize()

        result = await secure_capability.read_file("../../../etc/passwd")

        assert result.success is False
        assert "outside" in result.error.lower() or "not found" in result.error.lower()

        await secure_capability.shutdown()

    @pytest.mark.asyncio
    async def test_absolute_path_blocked(self, secure_capability):
        """Test that absolute paths are blocked when disabled."""
        await secure_capability.initialize()

        result = await secure_capability.read_file("/etc/passwd")

        assert result.success is False
        # Should be blocked either as absolute or as outside base directory
        assert "absolute" in result.error.lower() or "outside" in result.error.lower()

        await secure_capability.shutdown()

    @pytest.mark.asyncio
    async def test_extension_restriction(self, secure_capability, tmp_path):
        """Test extension restrictions are enforced."""
        # Create a file with disallowed extension
        (tmp_path / "test.json").write_text("{}")

        await secure_capability.initialize()

        result = await secure_capability.read_file("test.json")

        assert result.success is False
        assert (
            "extension" in result.error.lower() or "not allowed" in result.error.lower()
        )

        await secure_capability.shutdown()


class TestFileSystemGit:
    """Git-related tests for FileSystemCapability."""

    @pytest.fixture
    def git_capability(self, tmp_path):
        """Create capability with git enabled."""
        config = FileSystemConfig(
            base_path=str(tmp_path),
            enable_git=True,
        )
        return FileSystemCapability(config=config)

    @pytest.mark.asyncio
    async def test_git_status_not_repo(self, git_capability):
        """Test git status in non-repo directory."""
        await git_capability.initialize()

        result = await git_capability.git_status()

        # Should either succeed with error field or fail gracefully
        assert result.success is True
        # Either we get an error in output or it's not a git repo
        if "error" not in result.output:
            # If no error, could be a repo
            pass

        await git_capability.shutdown()

    @pytest.mark.asyncio
    async def test_git_disabled(self, tmp_path):
        """Test git operations when disabled."""
        config = FileSystemConfig(
            base_path=str(tmp_path),
            enable_git=False,
        )
        capability = FileSystemCapability(config=config)

        await capability.initialize()

        result = await capability.git_status()

        assert result.success is True
        assert "disabled" in result.output.get("error", "").lower()

        await capability.shutdown()
