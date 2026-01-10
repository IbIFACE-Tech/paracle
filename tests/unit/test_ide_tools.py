"""Tests for IDE tools module.

Tests cover:
- IDE detection
- File/folder opening
- Diff functionality
- Extension management
- Error handling
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from paracle_tools.ide_tools import (
    IDE_TOOLS,
    IDECommandError,
    IDENotFoundError,
    SUPPORTED_IDES,
    detect_ide,
    get_ide_command,
    ide_diff,
    ide_info,
    ide_install_extension,
    ide_list_extensions,
    ide_new_window,
    ide_open_file,
    ide_open_folder,
    ide_uninstall_extension,
    ide_version,
)


class TestIDEDetection:
    """Tests for IDE detection functionality."""

    def test_supported_ides_structure(self):
        """Test that SUPPORTED_IDES has correct structure."""
        assert "vscode" in SUPPORTED_IDES
        assert "cursor" in SUPPORTED_IDES
        assert "windsurf" in SUPPORTED_IDES
        assert "codium" in SUPPORTED_IDES

        for ide_id, info in SUPPORTED_IDES.items():
            assert "command" in info
            assert "display_name" in info
            assert "supports_diff" in info

    @patch("shutil.which")
    def test_detect_ide_cursor(self, mock_which):
        """Test detection prefers Cursor."""
        mock_which.side_effect = lambda cmd: cmd == "cursor"

        result = detect_ide()
        assert result == "cursor"

    @patch("shutil.which")
    def test_detect_ide_vscode(self, mock_which):
        """Test detection finds VS Code."""
        mock_which.side_effect = lambda cmd: cmd == "code"

        result = detect_ide()
        assert result == "vscode"

    @patch("shutil.which")
    def test_detect_ide_none(self, mock_which):
        """Test detection returns None when no IDE found."""
        mock_which.return_value = None

        result = detect_ide()
        assert result is None

    @patch("shutil.which")
    def test_get_ide_command_auto(self, mock_which):
        """Test get_ide_command with auto-detection."""
        mock_which.side_effect = lambda cmd: cmd == "code"

        cmd = get_ide_command()
        assert cmd == "code"

    @patch("shutil.which")
    def test_get_ide_command_explicit(self, mock_which):
        """Test get_ide_command with explicit IDE."""
        mock_which.return_value = "/usr/bin/cursor"

        cmd = get_ide_command("cursor")
        assert cmd == "cursor"

    @patch("shutil.which")
    def test_get_ide_command_not_found(self, mock_which):
        """Test get_ide_command raises when no IDE."""
        mock_which.return_value = None

        with pytest.raises(IDENotFoundError):
            get_ide_command()

    def test_get_ide_command_unknown(self):
        """Test get_ide_command raises for unknown IDE."""
        with pytest.raises(IDENotFoundError, match="Unknown IDE"):
            get_ide_command("notepad")


class TestIDEInfo:
    """Tests for ide_info function."""

    @patch("paracle_tools.ide_tools.detect_ide")
    @patch("shutil.which")
    def test_ide_info(self, mock_which, mock_detect):
        """Test ide_info returns correct structure."""
        mock_detect.return_value = "vscode"
        mock_which.side_effect = lambda cmd: cmd == "code"

        result = ide_info()

        assert "detected_ide" in result
        assert "supported_ides" in result
        assert result["detected_ide"] == "vscode"
        assert "vscode" in result["supported_ides"]
        assert result["supported_ides"]["vscode"]["available"] is True


class TestIDEOpenFile:
    """Tests for ide_open_file function."""

    @patch("paracle_tools.ide_tools._run_ide_command")
    def test_open_file_basic(self, mock_run, tmp_path):
        """Test opening a file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")

        mock_run.return_value = {"success": True, "ide": "vscode"}

        result = ide_open_file(str(test_file))

        assert result["success"] is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "-r" in args  # Reuse window by default

    @patch("paracle_tools.ide_tools._run_ide_command")
    def test_open_file_with_line(self, mock_run, tmp_path):
        """Test opening a file at specific line."""
        test_file = tmp_path / "test.py"
        test_file.write_text("line1\nline2\nline3")

        mock_run.return_value = {"success": True, "ide": "vscode"}

        result = ide_open_file(str(test_file), line=42)

        assert result["success"] is True
        assert result["line"] == 42
        args = mock_run.call_args[0][0]
        assert "-g" in args

    @patch("paracle_tools.ide_tools._run_ide_command")
    def test_open_file_with_line_and_column(self, mock_run, tmp_path):
        """Test opening a file at specific line and column."""
        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        mock_run.return_value = {"success": True, "ide": "vscode"}

        result = ide_open_file(str(test_file), line=10, column=5)

        assert result["success"] is True
        assert result["line"] == 10
        assert result["column"] == 5

    def test_open_file_not_found(self):
        """Test opening non-existent file."""
        result = ide_open_file("/nonexistent/file.py")

        assert result["success"] is False
        assert "not found" in result["error"]


class TestIDEOpenFolder:
    """Tests for ide_open_folder function."""

    @patch("paracle_tools.ide_tools._run_ide_command")
    def test_open_folder_basic(self, mock_run, tmp_path):
        """Test opening a folder."""
        mock_run.return_value = {"success": True, "ide": "vscode"}

        result = ide_open_folder(str(tmp_path))

        assert result["success"] is True
        assert "folder" in result

    @patch("paracle_tools.ide_tools._run_ide_command")
    def test_open_folder_new_window(self, mock_run, tmp_path):
        """Test opening folder in new window."""
        mock_run.return_value = {"success": True, "ide": "vscode"}

        result = ide_open_folder(str(tmp_path), new_window=True)

        assert result["success"] is True
        args = mock_run.call_args[0][0]
        assert "-n" in args

    @patch("paracle_tools.ide_tools._run_ide_command")
    def test_open_folder_add_to_workspace(self, mock_run, tmp_path):
        """Test adding folder to workspace."""
        mock_run.return_value = {"success": True, "ide": "vscode"}

        result = ide_open_folder(str(tmp_path), add_to_workspace=True)

        assert result["success"] is True
        args = mock_run.call_args[0][0]
        assert "--add" in args

    def test_open_folder_not_found(self):
        """Test opening non-existent folder."""
        result = ide_open_folder("/nonexistent/folder")

        assert result["success"] is False
        assert "not found" in result["error"]


class TestIDEDiff:
    """Tests for ide_diff function."""

    @patch("paracle_tools.ide_tools._run_ide_command")
    def test_diff_basic(self, mock_run, tmp_path):
        """Test basic diff."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")

        mock_run.return_value = {"success": True, "ide": "vscode"}

        result = ide_diff(str(file1), str(file2))

        assert result["success"] is True
        args = mock_run.call_args[0][0]
        assert "--diff" in args

    @patch("paracle_tools.ide_tools._run_ide_command")
    def test_diff_with_wait(self, mock_run, tmp_path):
        """Test diff with wait option."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")

        mock_run.return_value = {"success": True, "ide": "vscode"}

        result = ide_diff(str(file1), str(file2), wait=True)

        assert result["success"] is True
        args = mock_run.call_args[0][0]
        assert "--wait" in args

    def test_diff_file_not_found(self, tmp_path):
        """Test diff with missing file."""
        file1 = tmp_path / "exists.txt"
        file1.write_text("content")

        result = ide_diff(str(file1), "/nonexistent.txt")

        assert result["success"] is False
        assert "not found" in result["error"]


class TestIDENewWindow:
    """Tests for ide_new_window function."""

    @patch("paracle_tools.ide_tools._run_ide_command")
    def test_new_window_empty(self, mock_run):
        """Test opening new empty window."""
        mock_run.return_value = {"success": True, "ide": "vscode"}

        result = ide_new_window()

        assert result["success"] is True
        args = mock_run.call_args[0][0]
        assert "-n" in args

    @patch("paracle_tools.ide_tools._run_ide_command")
    def test_new_window_with_folder(self, mock_run, tmp_path):
        """Test opening new window with folder."""
        mock_run.return_value = {"success": True, "ide": "vscode"}

        result = ide_new_window(str(tmp_path))

        assert result["success"] is True
        args = mock_run.call_args[0][0]
        assert "-n" in args
        assert str(tmp_path) in args[-1]


class TestIDEExtensions:
    """Tests for extension management functions."""

    @patch("paracle_tools.ide_tools._run_ide_command")
    def test_list_extensions(self, mock_run):
        """Test listing extensions."""
        mock_run.return_value = {
            "success": True,
            "ide": "vscode",
            "stdout": "ms-python.python\nms-vscode.go\n",
        }

        result = ide_list_extensions()

        assert result["success"] is True
        assert "extensions" in result
        assert len(result["extensions"]) == 2
        assert "ms-python.python" in result["extensions"]

    @patch("paracle_tools.ide_tools._run_ide_command")
    def test_install_extension(self, mock_run):
        """Test installing extension."""
        mock_run.return_value = {"success": True, "ide": "vscode"}

        result = ide_install_extension("ms-python.python")

        assert result["success"] is True
        assert result["extension"] == "ms-python.python"
        args = mock_run.call_args[0][0]
        assert "--install-extension" in args

    @patch("paracle_tools.ide_tools._run_ide_command")
    def test_uninstall_extension(self, mock_run):
        """Test uninstalling extension."""
        mock_run.return_value = {"success": True, "ide": "vscode"}

        result = ide_uninstall_extension("ms-python.python")

        assert result["success"] is True
        args = mock_run.call_args[0][0]
        assert "--uninstall-extension" in args


class TestIDEVersion:
    """Tests for ide_version function."""

    @patch("paracle_tools.ide_tools._run_ide_command")
    def test_version(self, mock_run):
        """Test getting version."""
        mock_run.return_value = {
            "success": True,
            "ide": "vscode",
            "stdout": "1.85.0\ncommit abc123\ndate 2024-01-01",
        }

        result = ide_version()

        assert result["success"] is True
        assert "version_info" in result
        assert len(result["version_info"]) == 3


class TestIDEToolsRegistry:
    """Tests for MCP tools registry."""

    def test_tools_registry_structure(self):
        """Test IDE_TOOLS has correct structure."""
        assert len(IDE_TOOLS) > 0

        for tool in IDE_TOOLS:
            assert "name" in tool
            assert "description" in tool
            assert "function" in tool
            assert "parameters" in tool
            assert callable(tool["function"])

    def test_tools_registry_names(self):
        """Test all expected tools are registered."""
        tool_names = [t["name"] for t in IDE_TOOLS]

        assert "ide_info" in tool_names
        assert "ide_open_file" in tool_names
        assert "ide_open_folder" in tool_names
        assert "ide_diff" in tool_names
        assert "ide_new_window" in tool_names
        assert "ide_list_extensions" in tool_names
        assert "ide_install_extension" in tool_names


class TestErrorHandling:
    """Tests for error handling."""

    @patch("subprocess.run")
    @patch("paracle_tools.ide_tools.get_ide_command")
    def test_command_timeout(self, mock_get_cmd, mock_run):
        """Test command timeout handling."""
        mock_get_cmd.return_value = "code"
        mock_run.side_effect = subprocess.TimeoutExpired("code", 30)

        with pytest.raises(IDECommandError, match="timed out"):
            ide_version()

    @patch("subprocess.run")
    @patch("paracle_tools.ide_tools.get_ide_command")
    def test_command_not_found(self, mock_get_cmd, mock_run):
        """Test command not found handling."""
        mock_get_cmd.return_value = "nonexistent"
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(IDENotFoundError):
            ide_version()

    @patch("subprocess.run")
    @patch("paracle_tools.ide_tools.get_ide_command")
    def test_command_failure(self, mock_get_cmd, mock_run):
        """Test command failure handling."""
        mock_get_cmd.return_value = "code"
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Some error"
        mock_run.return_value = mock_result

        with pytest.raises(IDECommandError, match="Some error"):
            ide_version()
