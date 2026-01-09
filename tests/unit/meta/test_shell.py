"""Unit tests for paracle_meta.capabilities.shell module."""

import platform

import pytest
from paracle_meta.capabilities.shell import ProcessInfo, ShellCapability, ShellConfig


class TestShellConfig:
    """Tests for ShellConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ShellConfig()
        assert config.working_directory is None
        assert config.shell is None
        assert config.inherit_env is True
        assert config.max_output_size == 1024 * 1024
        assert config.enable_background is True
        assert config.default_timeout == 60.0
        assert "rm -rf /" in config.blocked_commands

    def test_custom_values(self):
        """Test custom configuration values."""
        config = ShellConfig(
            working_directory="/tmp",
            inherit_env=False,
            default_timeout=30.0,
            allowed_commands=["echo", "ls"],
        )
        assert config.working_directory == "/tmp"
        assert config.inherit_env is False
        assert config.default_timeout == 30.0
        assert "echo" in config.allowed_commands


class TestProcessInfo:
    """Tests for ProcessInfo."""

    def test_create_process_info(self):
        """Test creating ProcessInfo."""
        from datetime import datetime, timezone

        info = ProcessInfo(
            pid=12345,
            command="echo hello",
            started_at=datetime.now(timezone.utc),
        )

        assert info.pid == 12345
        assert info.command == "echo hello"
        assert info.process is None
        assert info.output_buffer == []
        assert info.error_buffer == []

    def test_to_dict(self):
        """Test ProcessInfo conversion to dict."""
        from datetime import datetime, timezone

        info = ProcessInfo(
            pid=12345,
            command="test",
            started_at=datetime.now(timezone.utc),
        )

        data = info.to_dict()
        assert data["pid"] == 12345
        assert data["command"] == "test"
        assert "started_at" in data
        assert data["running"] is False


class TestShellCapability:
    """Tests for ShellCapability."""

    @pytest.fixture
    def shell_capability(self, tmp_path):
        """Create shell capability instance."""
        config = ShellConfig(
            working_directory=str(tmp_path),
            default_timeout=10.0,
        )
        return ShellCapability(config=config)

    def test_initialization(self, shell_capability):
        """Test capability initialization."""
        assert shell_capability.name == "shell"
        assert "shell" in shell_capability.description.lower()

    @pytest.mark.asyncio
    async def test_initialize_and_shutdown(self, shell_capability):
        """Test initialize and shutdown lifecycle."""
        await shell_capability.initialize()
        assert shell_capability.is_initialized is True
        assert shell_capability._working_dir is not None

        await shell_capability.shutdown()
        assert shell_capability.is_initialized is False

    @pytest.mark.asyncio
    async def test_run_simple_command(self, shell_capability):
        """Test running a simple command."""
        await shell_capability.initialize()

        if platform.system() == "Windows":
            result = await shell_capability.run("echo hello")
        else:
            result = await shell_capability.run("echo hello")

        assert result.success is True
        assert "hello" in result.output["stdout"].lower()
        assert result.output["return_code"] == 0

        await shell_capability.shutdown()

    @pytest.mark.asyncio
    async def test_run_command_with_error(self, shell_capability):
        """Test running a command that fails."""
        await shell_capability.initialize()

        # Run a command that doesn't exist
        result = await shell_capability.run("nonexistent_command_xyz")

        assert result.success is True  # Capability executed
        # But the command itself failed
        assert result.output["success"] is False or result.output["return_code"] != 0

        await shell_capability.shutdown()

    @pytest.mark.asyncio
    async def test_run_python_code(self, shell_capability):
        """Test running Python code via shell."""
        await shell_capability.initialize()

        result = await shell_capability.run(
            'python -c "print(1 + 1)"',
            timeout=10.0,
        )

        assert result.success is True
        assert "2" in result.output["stdout"]

        await shell_capability.shutdown()

    @pytest.mark.asyncio
    async def test_which_command(self, shell_capability):
        """Test finding command path."""
        await shell_capability.initialize()

        result = await shell_capability.which("python")

        assert result.success is True
        assert result.output["found"] is True
        assert result.output["path"] is not None

        await shell_capability.shutdown()

    @pytest.mark.asyncio
    async def test_which_nonexistent(self, shell_capability):
        """Test which for nonexistent command."""
        await shell_capability.initialize()

        result = await shell_capability.which("nonexistent_cmd_xyz")

        assert result.success is True
        assert result.output["found"] is False
        assert result.output["path"] is None

        await shell_capability.shutdown()

    @pytest.mark.asyncio
    async def test_system_info(self, shell_capability):
        """Test getting system info."""
        await shell_capability.initialize()

        result = await shell_capability.system_info()

        assert result.success is True
        assert "platform" in result.output
        assert "python_version" in result.output
        assert "architecture" in result.output

        await shell_capability.shutdown()

    @pytest.mark.asyncio
    async def test_get_cwd(self, shell_capability, tmp_path):
        """Test getting current working directory."""
        await shell_capability.initialize()

        result = await shell_capability.execute(action="cwd")

        assert result.success is True
        assert str(tmp_path) in result.output["cwd"]

        await shell_capability.shutdown()

    @pytest.mark.asyncio
    async def test_change_cwd(self, shell_capability, tmp_path):
        """Test changing working directory."""
        # Create a subdirectory
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        await shell_capability.initialize()

        result = await shell_capability.execute(action="cwd", path="subdir")

        assert result.success is True
        assert "subdir" in result.output["cwd"]

        await shell_capability.shutdown()

    @pytest.mark.asyncio
    async def test_env_operations(self, shell_capability):
        """Test environment variable operations."""
        await shell_capability.initialize()

        # Set env
        result = await shell_capability.execute(
            action="env",
            set=True,
            name="TEST_VAR",
            value="test_value",
        )
        assert result.success is True

        # Get env
        result = await shell_capability.execute(
            action="env",
            name="TEST_VAR",
        )
        assert result.success is True
        assert result.output["value"] == "test_value"

        # Unset env
        result = await shell_capability.execute(
            action="env",
            unset=True,
            name="TEST_VAR",
        )
        assert result.success is True
        assert result.output["unset"] is True

        await shell_capability.shutdown()

    @pytest.mark.asyncio
    async def test_list_processes_empty(self, shell_capability):
        """Test listing processes when none running."""
        await shell_capability.initialize()

        result = await shell_capability.execute(action="list_processes")

        assert result.success is True
        assert result.output["count"] == 0
        assert result.output["processes"] == []

        await shell_capability.shutdown()

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self, shell_capability):
        """Test execute with unknown action."""
        await shell_capability.initialize()

        result = await shell_capability.execute(action="unknown_action")

        assert result.success is False
        assert "Unknown action" in result.error

        await shell_capability.shutdown()


class TestShellSecurity:
    """Security-focused tests for ShellCapability."""

    @pytest.fixture
    def secure_capability(self, tmp_path):
        """Create capability with secure settings."""
        config = ShellConfig(
            working_directory=str(tmp_path),
            blocked_commands=["rm -rf", "mkfs", "dd if="],
            allowed_commands=["echo", "python", "ls", "dir"],
            default_timeout=5.0,
        )
        return ShellCapability(config=config)

    @pytest.mark.asyncio
    async def test_blocked_command(self, secure_capability):
        """Test that blocked commands are rejected."""
        await secure_capability.initialize()

        result = await secure_capability.run("rm -rf /")

        assert result.success is False
        assert "blocked" in result.error.lower()

        await secure_capability.shutdown()

    @pytest.mark.asyncio
    async def test_allowed_command_only(self, secure_capability):
        """Test that only allowed commands work."""
        await secure_capability.initialize()

        # Allowed command
        result = await secure_capability.run("echo test")
        assert result.success is True

        # Non-allowed command
        result = await secure_capability.run("whoami")
        assert result.success is False
        assert (
            "not in allowed" in result.error.lower()
            or "allowed" in result.error.lower()
        )

        await secure_capability.shutdown()

    @pytest.mark.asyncio
    async def test_timeout_enforcement(self, tmp_path):
        """Test command timeout."""
        config = ShellConfig(
            working_directory=str(tmp_path),
            default_timeout=2.0,
        )
        capability = ShellCapability(config=config)

        await capability.initialize()

        # Run a command that would hang
        if platform.system() == "Windows":
            result = await capability.run("ping -n 10 127.0.0.1", timeout=1.0)
        else:
            result = await capability.run("sleep 10", timeout=1.0)

        assert result.success is True
        assert result.output.get("timeout") is True or result.output["success"] is False

        await capability.shutdown()


class TestShellBackground:
    """Background process tests for ShellCapability."""

    @pytest.fixture
    def bg_capability(self, tmp_path):
        """Create capability with background enabled."""
        config = ShellConfig(
            working_directory=str(tmp_path),
            enable_background=True,
            default_timeout=10.0,
        )
        return ShellCapability(config=config)

    @pytest.mark.asyncio
    async def test_background_disabled(self, tmp_path):
        """Test background when disabled."""
        config = ShellConfig(
            working_directory=str(tmp_path),
            enable_background=False,
        )
        capability = ShellCapability(config=config)

        await capability.initialize()

        result = await capability.run_background("echo test")

        assert result.success is False
        assert "disabled" in result.error.lower()

        await capability.shutdown()

    @pytest.mark.asyncio
    async def test_run_script_file(self, bg_capability, tmp_path):
        """Test running a script file."""
        # Create a test script
        script_file = tmp_path / "test_script.py"
        script_file.write_text("print('Hello from script')")

        await bg_capability.initialize()

        result = await bg_capability.run_python_script(
            str(script_file),
            timeout=10.0,
        )

        assert result.success is True
        assert "Hello from script" in result.output["stdout"]

        await bg_capability.shutdown()

    @pytest.mark.asyncio
    async def test_run_script_not_found(self, bg_capability, tmp_path):
        """Test running nonexistent script."""
        await bg_capability.initialize()

        result = await bg_capability.run_python_script(
            "nonexistent_script.py",
            timeout=10.0,
        )

        assert result.success is False
        assert "not found" in result.error.lower()

        await bg_capability.shutdown()
