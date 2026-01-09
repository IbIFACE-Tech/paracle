"""Tests for built-in filesystem tools."""

import pytest
from pathlib import Path

from paracle_tools.builtin.filesystem import (
    ReadFileTool,
    WriteFileTool,
    ListDirectoryTool,
    DeleteFileTool,
)
from paracle_tools.builtin.base import PermissionError, ToolError


class TestReadFileTool:
    """Test read_file tool."""

    @pytest.mark.asyncio
    async def test_read_existing_file(self, tmp_path):
        # Arrange
        file_path = tmp_path / "test.txt"
        content = "Hello, World!\nLine 2"
        file_path.write_text(content)

        tool = ReadFileTool(allowed_paths=[str(tmp_path)])

        # Act
        result = await tool.execute(path=str(file_path))

        # Assert
        assert result.success is True
        assert result.output["content"] == content
        assert result.output["lines"] == 2
        assert result.output["size"] > 0

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, tmp_path):
        # Arrange
        file_path = tmp_path / "nonexistent.txt"
        tool = ReadFileTool(allowed_paths=[str(tmp_path)])

        # Act
        result = await tool.execute(path=str(file_path))

        # Assert
        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_read_directory_fails(self, tmp_path):
        # Arrange
        tool = ReadFileTool(allowed_paths=[str(tmp_path)])

        # Act
        result = await tool.execute(path=str(tmp_path))

        # Assert
        assert result.success is False
        assert "not a file" in result.error.lower()

    @pytest.mark.asyncio
    async def test_read_with_path_restriction(self, tmp_path):
        # Arrange
        allowed_dir = tmp_path / "allowed"
        forbidden_dir = tmp_path / "forbidden"
        allowed_dir.mkdir()
        forbidden_dir.mkdir()

        allowed_file = allowed_dir / "test.txt"
        allowed_file.write_text("allowed content")

        forbidden_file = forbidden_dir / "test.txt"
        forbidden_file.write_text("forbidden content")

        tool = ReadFileTool(allowed_paths=[str(allowed_dir)])

        # Act - allowed file
        result_allowed = await tool.execute(path=str(allowed_file))

        # Assert - allowed file works
        assert result_allowed.success is True
        assert result_allowed.output["content"] == "allowed content"

        # Act - forbidden file
        result_forbidden = await tool.execute(path=str(forbidden_file))

        # Assert - forbidden file fails
        assert result_forbidden.success is False
        assert "access denied" in result_forbidden.error.lower()


class TestWriteFileTool:
    """Test write_file tool."""

    @pytest.mark.asyncio
    async def test_write_new_file(self, tmp_path):
        # Arrange
        file_path = tmp_path / "new_file.txt"
        content = "New content"
        tool = WriteFileTool(allowed_paths=[str(tmp_path)])

        # Act
        result = await tool.execute(path=str(file_path), content=content)

        # Assert
        assert result.success is True
        assert file_path.exists()
        assert file_path.read_text() == content

    @pytest.mark.asyncio
    async def test_write_creates_parent_dirs(self, tmp_path):
        # Arrange
        file_path = tmp_path / "subdir1" / "subdir2" / "file.txt"
        content = "Nested content"
        tool = WriteFileTool(allowed_paths=[str(tmp_path)])

        # Act
        result = await tool.execute(
            path=str(file_path), content=content, create_dirs=True
        )

        # Assert
        assert result.success is True
        assert file_path.exists()
        assert file_path.read_text() == content

    @pytest.mark.asyncio
    async def test_write_overwrites_existing(self, tmp_path):
        # Arrange
        file_path = tmp_path / "existing.txt"
        file_path.write_text("old content")

        tool = WriteFileTool(allowed_paths=[str(tmp_path)])
        new_content = "new content"

        # Act
        result = await tool.execute(path=str(file_path), content=new_content)

        # Assert
        assert result.success is True
        assert file_path.read_text() == new_content

    @pytest.mark.asyncio
    async def test_write_with_path_restriction(self, tmp_path):
        # Arrange
        allowed_dir = tmp_path / "allowed"
        forbidden_dir = tmp_path / "forbidden"
        allowed_dir.mkdir()
        forbidden_dir.mkdir()

        tool = WriteFileTool(allowed_paths=[str(allowed_dir)])

        # Act - allowed path
        result_allowed = await tool.execute(
            path=str(allowed_dir / "test.txt"), content="allowed"
        )

        # Assert - allowed works
        assert result_allowed.success is True

        # Act - forbidden path
        result_forbidden = await tool.execute(
            path=str(forbidden_dir / "test.txt"), content="forbidden"
        )

        # Assert - forbidden fails
        assert result_forbidden.success is False
        assert "access denied" in result_forbidden.error.lower()


class TestListDirectoryTool:
    """Test list_directory tool."""

    @pytest.mark.asyncio
    async def test_list_directory(self, tmp_path):
        # Arrange
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        (tmp_path / "subdir").mkdir()

        tool = ListDirectoryTool(allowed_paths=[str(tmp_path)])

        # Act
        result = await tool.execute(path=str(tmp_path))

        # Assert
        assert result.success is True
        assert result.output["count"] == 3

        names = [entry["name"] for entry in result.output["entries"]]
        assert "file1.txt" in names
        assert "file2.txt" in names
        assert "subdir" in names

    @pytest.mark.asyncio
    async def test_list_directory_recursive(self, tmp_path):
        # Arrange
        (tmp_path / "file1.txt").write_text("content")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file2.txt").write_text("content")

        tool = ListDirectoryTool(allowed_paths=[str(tmp_path)])

        # Act
        result = await tool.execute(path=str(tmp_path), recursive=True)

        # Assert
        assert result.success is True
        assert result.output["count"] >= 2  # At least file1.txt and subdir

        names = [entry["name"] for entry in result.output["entries"]]
        assert any("file1.txt" in name for name in names)

    @pytest.mark.asyncio
    async def test_list_nonexistent_directory(self, tmp_path):
        # Arrange
        dir_path = tmp_path / "nonexistent"
        tool = ListDirectoryTool(allowed_paths=[str(tmp_path)])

        # Act
        result = await tool.execute(path=str(dir_path))

        # Assert
        assert result.success is False
        assert "not found" in result.error.lower()


class TestDeleteFileTool:
    """Test delete_file tool."""

    @pytest.mark.asyncio
    async def test_delete_existing_file(self, tmp_path):
        # Arrange
        file_path = tmp_path / "to_delete.txt"
        file_path.write_text("content")

        tool = DeleteFileTool(allowed_paths=[str(tmp_path)])

        # Act
        result = await tool.execute(path=str(file_path))

        # Assert
        assert result.success is True
        assert not file_path.exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self, tmp_path):
        # Arrange
        file_path = tmp_path / "nonexistent.txt"
        tool = DeleteFileTool(allowed_paths=[str(tmp_path)])

        # Act
        result = await tool.execute(path=str(file_path))

        # Assert
        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_delete_directory_fails(self, tmp_path):
        # Arrange
        dir_path = tmp_path / "subdir"
        dir_path.mkdir()

        tool = DeleteFileTool(allowed_paths=[str(tmp_path)])

        # Act
        result = await tool.execute(path=str(dir_path))

        # Assert
        assert result.success is False
        assert "not a file" in result.error.lower()

    @pytest.mark.asyncio
    async def test_delete_with_path_restriction(self, tmp_path):
        # Arrange
        allowed_dir = tmp_path / "allowed"
        forbidden_dir = tmp_path / "forbidden"
        allowed_dir.mkdir()
        forbidden_dir.mkdir()

        allowed_file = allowed_dir / "test.txt"
        allowed_file.write_text("content")

        forbidden_file = forbidden_dir / "test.txt"
        forbidden_file.write_text("content")

        tool = DeleteFileTool(allowed_paths=[str(allowed_dir)])

        # Act - forbidden file
        result_forbidden = await tool.execute(path=str(forbidden_file))

        # Assert - forbidden fails
        assert result_forbidden.success is False
        assert "access denied" in result_forbidden.error.lower()

        # Act - allowed file
        result_allowed = await tool.execute(path=str(allowed_file))

        # Assert - allowed works
        assert result_allowed.success is True
        assert not allowed_file.exists()
