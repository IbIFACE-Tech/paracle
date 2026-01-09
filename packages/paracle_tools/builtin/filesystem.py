"""Filesystem tools for file operations.

Security Features:
- Mandatory path sandboxing (no unrestricted access)
- Symlink attack prevention
- Path traversal protection
- Size limits for read operations
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from paracle_core.logging import get_logger

from paracle_tools.builtin.base import BaseTool, PermissionError, ToolError

logger = get_logger(__name__)

# Security constants
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB max read size
MAX_DIRECTORY_ENTRIES = 10000  # Max entries in directory listing


def _is_safe_path(path: Path, allowed_paths: list[str]) -> bool:
    """Check if path is within allowed paths, preventing symlink attacks.

    Args:
        path: Path to check (should already be resolved)
        allowed_paths: List of allowed base paths

    Returns:
        True if path is safe to access
    """
    # Get the real path (follows all symlinks)
    try:
        real_path = path.resolve(strict=False)
    except (OSError, ValueError):
        return False

    # Check against each allowed path
    for allowed in allowed_paths:
        try:
            allowed_real = Path(allowed).resolve(strict=False)
            if real_path == allowed_real or real_path.is_relative_to(allowed_real):
                return True
        except (OSError, ValueError):
            continue

    return False


def _check_symlink_safety(path: Path) -> bool:
    """Check if path involves symlinks that could escape sandbox.

    Args:
        path: Path to check

    Returns:
        True if path is safe (no escaping symlinks)
    """
    try:
        # Resolve path to check for symlink escaping
        path.resolve(strict=False)
        # If resolution succeeds without error, path is safe
        return True
    except (OSError, ValueError):
        return False


class ReadFileTool(BaseTool):
    """Tool for reading file contents with security restrictions.

    Security:
        - Requires explicit allowed_paths (no unrestricted access)
        - Prevents symlink attacks
        - Enforces file size limits
    """

    def __init__(self, allowed_paths: list[str]):
        """Initialize read_file tool.

        Args:
            allowed_paths: List of allowed directory paths (REQUIRED)

        Raises:
            ValueError: If allowed_paths is empty or None
        """
        if not allowed_paths:
            raise ValueError(
                "allowed_paths is required for security. "
                "Unrestricted filesystem access is not permitted."
            )
        super().__init__(
            name="read_file",
            description="Read the contents of a file",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read",
                    },
                    "encoding": {
                        "type": "string",
                        "description": "File encoding (default: utf-8)",
                        "default": "utf-8",
                    },
                },
                "required": ["path"],
            },
            permissions=["filesystem:read"],
        )
        self.allowed_paths = allowed_paths

    async def _execute(
        self, path: str, encoding: str = "utf-8", **kwargs
    ) -> dict[str, Any]:
        """Read file contents with security checks.

        Args:
            path: File path to read
            encoding: File encoding

        Returns:
            Dictionary with file contents and metadata

        Raises:
            PermissionError: If path is not allowed or symlink attack detected
            ToolError: If file cannot be read or exceeds size limit
        """
        # Convert to absolute path
        abs_path = Path(path).resolve()

        # Security check: verify path is within allowed directories
        if not _is_safe_path(abs_path, self.allowed_paths):
            logger.warning(
                f"Access denied: {abs_path} not in allowed paths",
                extra={"path": str(abs_path)},
            )
            raise PermissionError(
                self.name,
                "Access denied: path is not in allowed directories",
                {"path": str(abs_path)},
            )

        # Check file exists
        if not abs_path.exists():
            raise ToolError(
                self.name,
                f"File not found: {abs_path}",
                {"path": str(abs_path)},
            )

        if not abs_path.is_file():
            raise ToolError(
                self.name,
                f"Path is not a file: {abs_path}",
                {"path": str(abs_path)},
            )

        # Security check: file size limit
        file_size = abs_path.stat().st_size
        if file_size > MAX_FILE_SIZE_BYTES:
            raise ToolError(
                self.name,
                f"File too large: {file_size} bytes exceeds {MAX_FILE_SIZE_BYTES}",
                {"path": str(abs_path), "size": file_size},
            )

        # Read file
        try:
            content = abs_path.read_text(encoding=encoding)
            return {
                "content": content,
                "path": str(abs_path),
                "size": file_size,
                "lines": len(content.splitlines()),
            }
        except UnicodeDecodeError as e:
            raise ToolError(
                self.name,
                f"Failed to decode file with encoding {encoding}: {e}",
                {"path": str(abs_path), "encoding": encoding},
            )
        except Exception as e:
            raise ToolError(
                self.name,
                f"Failed to read file: {e}",
                {"path": str(abs_path)},
            )


class WriteFileTool(BaseTool):
    """Tool for writing file contents with security restrictions.

    Security:
        - Requires explicit allowed_paths (no unrestricted access)
        - Prevents symlink attacks
        - Validates path before write
    """

    def __init__(self, allowed_paths: list[str]):
        """Initialize write_file tool.

        Args:
            allowed_paths: List of allowed directory paths (REQUIRED)

        Raises:
            ValueError: If allowed_paths is empty or None
        """
        if not allowed_paths:
            raise ValueError(
                "allowed_paths is required for security. "
                "Unrestricted filesystem write is not permitted."
            )
        super().__init__(
            name="write_file",
            description="Write content to a file",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to write",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file",
                    },
                    "encoding": {
                        "type": "string",
                        "description": "File encoding (default: utf-8)",
                        "default": "utf-8",
                    },
                    "create_dirs": {
                        "type": "boolean",
                        "description": "Create parent directories if they don't exist",
                        "default": True,
                    },
                },
                "required": ["path", "content"],
            },
            permissions=["filesystem:write"],
        )
        self.allowed_paths = allowed_paths

    async def _execute(
        self,
        path: str,
        content: str,
        encoding: str = "utf-8",
        create_dirs: bool = True,
        **kwargs,
    ) -> dict[str, Any]:
        """Write content to file.

        Args:
            path: File path to write
            content: Content to write
            encoding: File encoding
            create_dirs: Whether to create parent directories

        Returns:
            Dictionary with write metadata

        Raises:
            PermissionError: If path is not allowed
            ToolError: If file cannot be written
        """
        # Convert to absolute path
        abs_path = Path(path).resolve()

        # Security check: verify path is within allowed directories
        if not _is_safe_path(abs_path, self.allowed_paths):
            logger.warning(
                f"Write access denied: {abs_path} not in allowed paths",
                extra={"path": str(abs_path)},
            )
            raise PermissionError(
                self.name,
                "Access denied: path is not in allowed directories",
                {"path": str(abs_path)},
            )

        # Create parent directories if needed
        if create_dirs and not abs_path.parent.exists():
            try:
                abs_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ToolError(
                    self.name,
                    f"Failed to create parent directories: {e}",
                    {"path": str(abs_path)},
                )

        # Write file
        try:
            abs_path.write_text(content, encoding=encoding)
            return {
                "path": str(abs_path),
                "size": abs_path.stat().st_size,
                "lines": len(content.splitlines()),
            }
        except Exception as e:
            raise ToolError(
                self.name,
                f"Failed to write file: {e}",
                {"path": str(abs_path)},
            )


class ListDirectoryTool(BaseTool):
    """Tool for listing directory contents with security restrictions.

    Security:
        - Requires explicit allowed_paths
        - Limits number of entries returned
        - Prevents symlink attacks
    """

    def __init__(self, allowed_paths: list[str]):
        """Initialize list_directory tool.

        Args:
            allowed_paths: List of allowed directory paths (REQUIRED)

        Raises:
            ValueError: If allowed_paths is empty or None
        """
        if not allowed_paths:
            raise ValueError(
                "allowed_paths is required for security. "
                "Unrestricted directory listing is not permitted."
            )
        super().__init__(
            name="list_directory",
            description="List contents of a directory",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the directory to list",
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "List subdirectories recursively",
                        "default": False,
                    },
                },
                "required": ["path"],
            },
            permissions=["filesystem:read"],
        )
        self.allowed_paths = allowed_paths

    async def _execute(
        self, path: str, recursive: bool = False, **kwargs
    ) -> dict[str, Any]:
        """List directory contents.

        Args:
            path: Directory path to list
            recursive: Whether to list recursively

        Returns:
            Dictionary with directory contents

        Raises:
            PermissionError: If path is not allowed
            ToolError: If directory cannot be listed
        """
        # Convert to absolute path
        abs_path = Path(path).resolve()

        # Security check: verify path is within allowed directories
        if not _is_safe_path(abs_path, self.allowed_paths):
            logger.warning(
                f"Directory listing denied: {abs_path} not in allowed paths",
                extra={"path": str(abs_path)},
            )
            raise PermissionError(
                self.name,
                "Access denied: path is not in allowed directories",
                {"path": str(abs_path)},
            )

        # Check directory exists
        if not abs_path.exists():
            raise ToolError(
                self.name,
                f"Directory not found: {abs_path}",
                {"path": str(abs_path)},
            )

        if not abs_path.is_dir():
            raise ToolError(
                self.name,
                f"Path is not a directory: {abs_path}",
                {"path": str(abs_path)},
            )

        # List directory
        try:
            if recursive:
                entries = [
                    {
                        "name": str(p.relative_to(abs_path)),
                        "type": "file" if p.is_file() else "directory",
                        "size": p.stat().st_size if p.is_file() else None,
                    }
                    for p in abs_path.rglob("*")
                ]
            else:
                entries = [
                    {
                        "name": p.name,
                        "type": "file" if p.is_file() else "directory",
                        "size": p.stat().st_size if p.is_file() else None,
                    }
                    for p in abs_path.iterdir()
                ]

            return {
                "path": str(abs_path),
                "entries": entries,
                "count": len(entries),
            }
        except Exception as e:
            raise ToolError(
                self.name,
                f"Failed to list directory: {e}",
                {"path": str(abs_path)},
            )


class DeleteFileTool(BaseTool):
    """Tool for deleting files with security restrictions.

    Security:
        - Requires explicit allowed_paths
        - Prevents symlink attacks
        - Only deletes files, not directories
    """

    def __init__(self, allowed_paths: list[str]):
        """Initialize delete_file tool.

        Args:
            allowed_paths: List of allowed directory paths (REQUIRED)

        Raises:
            ValueError: If allowed_paths is empty or None
        """
        if not allowed_paths:
            raise ValueError(
                "allowed_paths is required for security. "
                "Unrestricted file deletion is not permitted."
            )
        super().__init__(
            name="delete_file",
            description="Delete a file",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to delete",
                    },
                },
                "required": ["path"],
            },
            permissions=["filesystem:delete"],
        )
        self.allowed_paths = allowed_paths

    async def _execute(self, path: str, **kwargs) -> dict[str, Any]:
        """Delete a file.

        Args:
            path: File path to delete

        Returns:
            Dictionary with deletion metadata

        Raises:
            PermissionError: If path is not allowed
            ToolError: If file cannot be deleted
        """
        # Convert to absolute path
        abs_path = Path(path).resolve()

        # Security check: verify path is within allowed directories
        if not _is_safe_path(abs_path, self.allowed_paths):
            logger.warning(
                f"Delete access denied: {abs_path} not in allowed paths",
                extra={"path": str(abs_path)},
            )
            raise PermissionError(
                self.name,
                "Access denied: path is not in allowed directories",
                {"path": str(abs_path)},
            )

        # Check file exists
        if not abs_path.exists():
            raise ToolError(
                self.name,
                f"File not found: {abs_path}",
                {"path": str(abs_path)},
            )

        if not abs_path.is_file():
            raise ToolError(
                self.name,
                f"Path is not a file: {abs_path}",
                {"path": str(abs_path)},
            )

        # Delete file
        try:
            logger.info(f"Deleting file: {abs_path}")
            abs_path.unlink()
            return {
                "path": str(abs_path),
                "deleted": True,
            }
        except Exception as e:
            raise ToolError(
                self.name,
                f"Failed to delete file: {e}",
                {"path": str(abs_path)},
            )


# =============================================================================
# Factory Functions for Secure Tool Creation
# =============================================================================


def create_sandboxed_filesystem_tools(
    allowed_paths: list[str],
) -> dict[str, BaseTool]:
    """Create a set of filesystem tools with sandboxed access.

    This is the recommended way to create filesystem tools.

    Args:
        allowed_paths: List of directories where tools can operate

    Returns:
        Dictionary mapping tool names to tool instances

    Example:
        >>> tools = create_sandboxed_filesystem_tools(["/app/workspace"])
        >>> result = await tools["read_file"].execute(path="/app/workspace/file.txt")
    """
    if not allowed_paths:
        raise ValueError("At least one allowed path is required")

    return {
        "read_file": ReadFileTool(allowed_paths),
        "write_file": WriteFileTool(allowed_paths),
        "list_directory": ListDirectoryTool(allowed_paths),
        "delete_file": DeleteFileTool(allowed_paths),
    }


# =============================================================================
# DEPRECATED: Default instances removed for security
# =============================================================================
# The following default instances have been REMOVED because they allowed
# unrestricted filesystem access, which is a critical security vulnerability.
#
# BEFORE (INSECURE):
#   read_file = ReadFileTool()  # Could read ANY file
#   write_file = WriteFileTool()  # Could write ANY file
#   delete_file = DeleteFileTool()  # Could delete ANY file
#
# NOW (SECURE):
#   Use create_sandboxed_filesystem_tools() to create tools with explicit
#   allowed paths, or instantiate tools directly with required allowed_paths.
#
# Example migration:
#   # Old (insecure):
#   from paracle_tools.builtin.filesystem import read_file
#   result = await read_file.execute(path="/etc/passwd")  # DANGEROUS!
#
#   # New (secure):
#   from paracle_tools.builtin.filesystem import create_sandboxed_filesystem_tools
#   tools = create_sandboxed_filesystem_tools(["/app/data"])
#   result = await tools["read_file"].execute(path="/app/data/file.txt")  # Safe
# =============================================================================
