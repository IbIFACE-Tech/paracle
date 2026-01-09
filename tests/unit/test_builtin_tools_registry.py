"""Tests for built-in tool registry."""

import pytest

from paracle_tools.builtin.registry import BuiltinToolRegistry


@pytest.fixture
def registry(tmp_path):
    """Create a registry with required security config."""
    allowed_dir = tmp_path / "workspace"
    allowed_dir.mkdir()
    return BuiltinToolRegistry(
        filesystem_paths=[str(allowed_dir)],
        allowed_commands=["echo", "ls", "python"],
    )


@pytest.fixture
def workspace_dir(tmp_path):
    """Create a workspace directory."""
    allowed_dir = tmp_path / "workspace"
    allowed_dir.mkdir()
    return allowed_dir


class TestBuiltinToolRegistry:
    """Test BuiltinToolRegistry."""

    def test_registry_initialization(self, registry):
        # Assert
        assert registry is not None
        # 4 filesystem + 4 HTTP + 1 shell = 9
        assert len(registry.list_tool_names()) == 9

    def test_registry_requires_filesystem_paths(self):
        # Act & Assert
        with pytest.raises(ValueError, match="filesystem_paths is required"):
            BuiltinToolRegistry(
                filesystem_paths=None,
                allowed_commands=["echo"],
            )

        with pytest.raises(ValueError, match="filesystem_paths is required"):
            BuiltinToolRegistry(
                filesystem_paths=[],
                allowed_commands=["echo"],
            )

    def test_registry_requires_allowed_commands(self, tmp_path):
        # Arrange
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Act & Assert
        with pytest.raises(ValueError, match="allowed_commands is required"):
            BuiltinToolRegistry(
                filesystem_paths=[str(workspace)],
                allowed_commands=None,
            )

        with pytest.raises(ValueError, match="allowed_commands is required"):
            BuiltinToolRegistry(
                filesystem_paths=[str(workspace)],
                allowed_commands=[],
            )

    def test_list_all_tools(self, registry):
        # Act
        tools = registry.list_tools()

        # Assert
        assert len(tools) == 9
        assert all("name" in tool for tool in tools)
        assert all("description" in tool for tool in tools)
        assert all("parameters" in tool for tool in tools)

    def test_list_tool_names(self, registry):
        # Act
        names = registry.list_tool_names()

        # Assert
        assert "read_file" in names
        assert "write_file" in names
        assert "list_directory" in names
        assert "delete_file" in names
        assert "http_get" in names
        assert "http_post" in names
        assert "http_put" in names
        assert "http_delete" in names
        assert "run_command" in names

    def test_get_tool(self, registry):
        # Act
        tool = registry.get_tool("read_file")

        # Assert
        assert tool is not None
        assert tool.name == "read_file"
        assert "read" in tool.description.lower()

    def test_get_nonexistent_tool(self, registry):
        # Act
        tool = registry.get_tool("nonexistent_tool")

        # Assert
        assert tool is None

    def test_has_tool(self, registry):
        # Act & Assert
        assert registry.has_tool("read_file") is True
        assert registry.has_tool("http_get") is True
        assert registry.has_tool("nonexistent") is False

    @pytest.mark.asyncio
    async def test_execute_tool(self, tmp_path):
        # Arrange
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        file_path = workspace / "test.txt"
        content = "test content"
        file_path.write_text(content)

        registry = BuiltinToolRegistry(
            filesystem_paths=[str(workspace)],
            allowed_commands=["echo"],
        )

        # Act
        result = await registry.execute_tool("read_file", path=str(file_path))

        # Assert
        assert result.success is True
        assert result.output["content"] == content

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self, registry):
        # Act
        result = await registry.execute_tool("nonexistent_tool")

        # Assert
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_get_tools_by_category(self, registry):
        # Act
        categories = registry.get_tools_by_category()

        # Assert
        assert "filesystem" in categories
        assert "http" in categories
        assert "shell" in categories

        assert "read_file" in categories["filesystem"]
        assert "write_file" in categories["filesystem"]
        assert "list_directory" in categories["filesystem"]
        assert "delete_file" in categories["filesystem"]

        assert "http_get" in categories["http"]
        assert "http_post" in categories["http"]
        assert "http_put" in categories["http"]
        assert "http_delete" in categories["http"]

        assert "run_command" in categories["shell"]

    def test_get_tool_permissions(self, registry):
        # Act
        read_perms = registry.get_tool_permissions("read_file")
        write_perms = registry.get_tool_permissions("write_file")
        http_perms = registry.get_tool_permissions("http_get")
        shell_perms = registry.get_tool_permissions("run_command")

        # Assert
        assert "filesystem:read" in read_perms
        assert "filesystem:write" in write_perms
        assert "http:request" in http_perms
        assert "shell:execute" in shell_perms

    def test_configure_filesystem_paths(self, tmp_path):
        # Arrange
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        new_workspace = tmp_path / "new_workspace"
        new_workspace.mkdir()

        registry = BuiltinToolRegistry(
            filesystem_paths=[str(workspace)],
            allowed_commands=["echo"],
        )

        # Act
        registry.configure_filesystem_paths([str(new_workspace)])

        # Assert - tool should be reconfigured
        tool = registry.get_tool("read_file")
        assert tool.allowed_paths == [str(new_workspace)]

    def test_configure_allowed_commands(self, tmp_path):
        # Arrange
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        registry = BuiltinToolRegistry(
            filesystem_paths=[str(workspace)],
            allowed_commands=["echo", "ls"],
        )
        new_commands = ["python", "pip"]

        # Act
        registry.configure_allowed_commands(new_commands)

        # Assert - tool should be reconfigured
        tool = registry.get_tool("run_command")
        assert tool.allowed_commands == set(new_commands)

    def test_registry_with_custom_config(self, tmp_path):
        # Arrange
        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()

        # Act
        registry = BuiltinToolRegistry(
            filesystem_paths=[str(allowed_dir)],
            allowed_commands=["echo"],
            http_timeout=10.0,
            command_timeout=5.0,
        )

        # Assert
        read_tool = registry.get_tool("read_file")
        assert read_tool.allowed_paths == [str(allowed_dir)]

        shell_tool = registry.get_tool("run_command")
        assert shell_tool.allowed_commands == {"echo"}
        assert shell_tool.timeout == 5.0

        http_tool = registry.get_tool("http_get")
        assert http_tool.timeout == 10.0
