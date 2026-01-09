"""FileSystem Capability for MetaAgent.

Provides file and directory operations:
- Read/write/modify files
- Directory operations (create, list, delete)
- File search with glob patterns
- Git integration for version control
- Safe file operations with backup

Example:
    >>> cap = FileSystemCapability()
    >>> await cap.initialize()
    >>>
    >>> # Read file
    >>> result = await cap.read_file("src/main.py")
    >>>
    >>> # Write file
    >>> result = await cap.write_file("output.txt", "Hello, World!")
    >>>
    >>> # Search files
    >>> result = await cap.glob_files("**/*.py")
    >>>
    >>> # Git operations
    >>> result = await cap.git_status()
"""

import asyncio
import fnmatch
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import Field

from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)


class FileSystemConfig(CapabilityConfig):
    """Configuration for FileSystem capability."""

    base_path: str | None = Field(
        default=None, description="Base path for all operations (defaults to cwd)"
    )
    allow_absolute_paths: bool = Field(
        default=False,
        description="Allow operations on absolute paths outside base_path",
    )
    create_backups: bool = Field(
        default=True, description="Create backup before modifying files"
    )
    backup_suffix: str = Field(default=".bak", description="Suffix for backup files")
    max_file_size_mb: float = Field(
        default=10.0, ge=0.1, le=100.0, description="Maximum file size to read in MB"
    )
    allowed_extensions: list[str] | None = Field(
        default=None, description="Allowed file extensions (None = all)"
    )
    blocked_paths: list[str] = Field(
        default_factory=lambda: [".git", "__pycache__", "node_modules", ".env"],
        description="Blocked path patterns",
    )
    enable_git: bool = Field(default=True, description="Enable git operations")


class FileSystemCapability(BaseCapability):
    """FileSystem capability for file and directory operations.

    Provides safe file operations with:
    - Path validation and sandboxing
    - Automatic backups
    - Git integration
    - Glob pattern searching

    Example:
        >>> cap = FileSystemCapability()
        >>> await cap.initialize()
        >>> result = await cap.read_file("README.md")
        >>> print(result.output["content"])
    """

    name = "filesystem"
    description = "File and directory operations with safety features"

    def __init__(self, config: FileSystemConfig | None = None):
        """Initialize FileSystem capability."""
        super().__init__(config or FileSystemConfig())
        self.config: FileSystemConfig = self.config
        self._base_path: Path | None = None

    async def initialize(self) -> None:
        """Initialize capability."""
        await super().initialize()

        # Set base path
        if self.config.base_path:
            self._base_path = Path(self.config.base_path).resolve()
        else:
            self._base_path = Path.cwd()

    async def shutdown(self) -> None:
        """Cleanup capability."""
        await super().shutdown()

    def _resolve_path(self, path: str) -> Path:
        """Resolve and validate a path.

        Args:
            path: Path to resolve

        Returns:
            Resolved Path object

        Raises:
            ValueError: If path is invalid or outside allowed area
        """
        target = Path(path)

        # Handle absolute vs relative paths
        if target.is_absolute():
            if not self.config.allow_absolute_paths:
                raise ValueError(f"Absolute paths not allowed: {path}")
            resolved = target.resolve()
        else:
            resolved = (self._base_path / target).resolve()

        # Check if path is within base_path (sandboxing)
        if not self.config.allow_absolute_paths:
            try:
                resolved.relative_to(self._base_path)
            except ValueError:
                raise ValueError(f"Path outside base directory: {path}")

        # Check blocked paths
        path_str = str(resolved)
        for blocked in self.config.blocked_paths:
            if blocked in path_str:
                raise ValueError(f"Access to blocked path: {blocked}")

        return resolved

    def _check_extension(self, path: Path) -> None:
        """Check if file extension is allowed."""
        if self.config.allowed_extensions:
            ext = path.suffix.lower()
            if ext not in self.config.allowed_extensions:
                raise ValueError(f"File extension not allowed: {ext}")

    def _create_backup(self, path: Path) -> Path | None:
        """Create a backup of a file.

        Returns:
            Path to backup file or None if no backup created
        """
        if not self.config.create_backups or not path.exists():
            return None

        backup_path = path.with_suffix(path.suffix + self.config.backup_suffix)
        shutil.copy2(path, backup_path)
        return backup_path

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute filesystem operation.

        Actions:
            - read_file: Read file content
            - write_file: Write content to file
            - append_file: Append content to file
            - delete_file: Delete a file
            - create_directory: Create directory
            - delete_directory: Delete directory
            - list_directory: List directory contents
            - glob_files: Search files with glob pattern
            - file_info: Get file metadata
            - copy_file: Copy a file
            - move_file: Move/rename a file
            - git_status: Get git status
            - git_diff: Get git diff
        """
        action = kwargs.get("action", "read_file")
        start_time = time.time()

        try:
            if action == "read_file":
                result = await self._read_file(kwargs.get("path", ""))
            elif action == "write_file":
                result = await self._write_file(
                    kwargs.get("path", ""),
                    kwargs.get("content", ""),
                    kwargs.get("create_dirs", True),
                )
            elif action == "append_file":
                result = await self._append_file(
                    kwargs.get("path", ""),
                    kwargs.get("content", ""),
                )
            elif action == "delete_file":
                result = await self._delete_file(kwargs.get("path", ""))
            elif action == "create_directory":
                result = await self._create_directory(
                    kwargs.get("path", ""),
                    kwargs.get("parents", True),
                )
            elif action == "delete_directory":
                result = await self._delete_directory(
                    kwargs.get("path", ""),
                    kwargs.get("recursive", False),
                )
            elif action == "list_directory":
                result = await self._list_directory(
                    kwargs.get("path", "."),
                    kwargs.get("recursive", False),
                    kwargs.get("pattern"),
                )
            elif action == "glob_files":
                result = await self._glob_files(
                    kwargs.get("pattern", "**/*"),
                    kwargs.get("path", "."),
                )
            elif action == "file_info":
                result = await self._file_info(kwargs.get("path", ""))
            elif action == "copy_file":
                result = await self._copy_file(
                    kwargs.get("source", ""),
                    kwargs.get("destination", ""),
                )
            elif action == "move_file":
                result = await self._move_file(
                    kwargs.get("source", ""),
                    kwargs.get("destination", ""),
                )
            elif action == "git_status":
                result = await self._git_status()
            elif action == "git_diff":
                result = await self._git_diff(kwargs.get("path"))
            elif action == "search_content":
                result = await self._search_content(
                    kwargs.get("pattern", ""),
                    kwargs.get("path", "."),
                    kwargs.get("file_pattern", "**/*"),
                )
            else:
                return CapabilityResult.error_result(
                    capability=self.name,
                    error=f"Unknown action: {action}",
                )

            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.success_result(
                capability=self.name,
                output=result,
                duration_ms=duration_ms,
                action=action,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.error_result(
                capability=self.name,
                error=str(e),
                duration_ms=duration_ms,
                action=action,
            )

    async def _read_file(self, path: str) -> dict[str, Any]:
        """Read file content."""
        resolved = self._resolve_path(path)
        self._check_extension(resolved)

        if not resolved.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if not resolved.is_file():
            raise ValueError(f"Not a file: {path}")

        # Check file size
        size_mb = resolved.stat().st_size / (1024 * 1024)
        if size_mb > self.config.max_file_size_mb:
            raise ValueError(
                f"File too large: {size_mb:.2f} MB (max: {self.config.max_file_size_mb} MB)"
            )

        # Read content
        content = resolved.read_text(encoding="utf-8")

        return {
            "path": str(resolved),
            "content": content,
            "size_bytes": len(content.encode("utf-8")),
            "lines": content.count("\n") + 1,
            "encoding": "utf-8",
        }

    async def _write_file(
        self,
        path: str,
        content: str,
        create_dirs: bool = True,
    ) -> dict[str, Any]:
        """Write content to file."""
        resolved = self._resolve_path(path)
        self._check_extension(resolved)

        # Create parent directories if needed
        if create_dirs:
            resolved.parent.mkdir(parents=True, exist_ok=True)

        # Create backup if file exists
        backup_path = self._create_backup(resolved)

        # Write content
        resolved.write_text(content, encoding="utf-8")

        return {
            "path": str(resolved),
            "size_bytes": len(content.encode("utf-8")),
            "lines": content.count("\n") + 1,
            "backup": str(backup_path) if backup_path else None,
            "created": not resolved.exists(),
        }

    async def _append_file(self, path: str, content: str) -> dict[str, Any]:
        """Append content to file."""
        resolved = self._resolve_path(path)
        self._check_extension(resolved)

        # Create backup
        backup_path = self._create_backup(resolved)

        # Append content
        with open(resolved, "a", encoding="utf-8") as f:
            f.write(content)

        return {
            "path": str(resolved),
            "appended_bytes": len(content.encode("utf-8")),
            "backup": str(backup_path) if backup_path else None,
        }

    async def _delete_file(self, path: str) -> dict[str, Any]:
        """Delete a file."""
        resolved = self._resolve_path(path)

        if not resolved.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Create backup before deletion
        backup_path = self._create_backup(resolved)

        resolved.unlink()

        return {
            "path": str(resolved),
            "deleted": True,
            "backup": str(backup_path) if backup_path else None,
        }

    async def _create_directory(
        self,
        path: str,
        parents: bool = True,
    ) -> dict[str, Any]:
        """Create a directory."""
        resolved = self._resolve_path(path)

        existed = resolved.exists()
        resolved.mkdir(parents=parents, exist_ok=True)

        return {
            "path": str(resolved),
            "created": not existed,
            "already_existed": existed,
        }

    async def _delete_directory(
        self,
        path: str,
        recursive: bool = False,
    ) -> dict[str, Any]:
        """Delete a directory."""
        resolved = self._resolve_path(path)

        if not resolved.exists():
            raise FileNotFoundError(f"Directory not found: {path}")

        if not resolved.is_dir():
            raise ValueError(f"Not a directory: {path}")

        if recursive:
            shutil.rmtree(resolved)
        else:
            resolved.rmdir()

        return {
            "path": str(resolved),
            "deleted": True,
            "recursive": recursive,
        }

    async def _list_directory(
        self,
        path: str = ".",
        recursive: bool = False,
        pattern: str | None = None,
    ) -> dict[str, Any]:
        """List directory contents."""
        resolved = self._resolve_path(path)

        if not resolved.exists():
            raise FileNotFoundError(f"Directory not found: {path}")

        entries = []

        if recursive:
            for item in resolved.rglob("*"):
                if pattern and not fnmatch.fnmatch(item.name, pattern):
                    continue
                entries.append(self._file_entry(item))
        else:
            for item in resolved.iterdir():
                if pattern and not fnmatch.fnmatch(item.name, pattern):
                    continue
                entries.append(self._file_entry(item))

        return {
            "path": str(resolved),
            "entries": entries,
            "count": len(entries),
            "recursive": recursive,
        }

    def _file_entry(self, path: Path) -> dict[str, Any]:
        """Create a file entry dict."""
        stat = path.stat()
        return {
            "name": path.name,
            "path": str(path),
            "type": "directory" if path.is_dir() else "file",
            "size_bytes": stat.st_size if path.is_file() else 0,
            "modified": datetime.fromtimestamp(
                stat.st_mtime, tz=timezone.utc
            ).isoformat(),
        }

    async def _glob_files(
        self,
        pattern: str,
        path: str = ".",
    ) -> dict[str, Any]:
        """Search files with glob pattern."""
        resolved = self._resolve_path(path)

        matches = []
        for match in resolved.glob(pattern):
            if match.is_file():
                matches.append(
                    {
                        "path": str(match),
                        "name": match.name,
                        "relative": str(match.relative_to(resolved)),
                        "size_bytes": match.stat().st_size,
                    }
                )

        return {
            "pattern": pattern,
            "base_path": str(resolved),
            "matches": matches,
            "count": len(matches),
        }

    async def _file_info(self, path: str) -> dict[str, Any]:
        """Get file metadata."""
        resolved = self._resolve_path(path)

        if not resolved.exists():
            raise FileNotFoundError(f"Path not found: {path}")

        stat = resolved.stat()

        return {
            "path": str(resolved),
            "name": resolved.name,
            "type": "directory" if resolved.is_dir() else "file",
            "size_bytes": stat.st_size,
            "extension": resolved.suffix,
            "created": datetime.fromtimestamp(
                stat.st_ctime, tz=timezone.utc
            ).isoformat(),
            "modified": datetime.fromtimestamp(
                stat.st_mtime, tz=timezone.utc
            ).isoformat(),
            "accessed": datetime.fromtimestamp(
                stat.st_atime, tz=timezone.utc
            ).isoformat(),
            "permissions": oct(stat.st_mode)[-3:],
        }

    async def _copy_file(
        self,
        source: str,
        destination: str,
    ) -> dict[str, Any]:
        """Copy a file."""
        src = self._resolve_path(source)
        dst = self._resolve_path(destination)

        if not src.exists():
            raise FileNotFoundError(f"Source not found: {source}")

        # Create destination directory if needed
        dst.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(src, dst)

        return {
            "source": str(src),
            "destination": str(dst),
            "size_bytes": dst.stat().st_size,
        }

    async def _move_file(
        self,
        source: str,
        destination: str,
    ) -> dict[str, Any]:
        """Move/rename a file."""
        src = self._resolve_path(source)
        dst = self._resolve_path(destination)

        if not src.exists():
            raise FileNotFoundError(f"Source not found: {source}")

        # Create destination directory if needed
        dst.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(str(src), str(dst))

        return {
            "source": str(src),
            "destination": str(dst),
        }

    async def _search_content(
        self,
        pattern: str,
        path: str = ".",
        file_pattern: str = "**/*",
    ) -> dict[str, Any]:
        """Search for pattern in file contents."""
        import re

        resolved = self._resolve_path(path)
        regex = re.compile(pattern, re.IGNORECASE)

        matches = []

        for file_path in resolved.glob(file_pattern):
            if not file_path.is_file():
                continue

            # Skip blocked paths
            skip = False
            for blocked in self.config.blocked_paths:
                if blocked in str(file_path):
                    skip = True
                    break
            if skip:
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                for i, line in enumerate(content.split("\n"), 1):
                    if regex.search(line):
                        matches.append(
                            {
                                "file": str(file_path),
                                "line_number": i,
                                "line": line.strip()[:200],
                            }
                        )
            except (UnicodeDecodeError, PermissionError):
                continue

        return {
            "pattern": pattern,
            "file_pattern": file_pattern,
            "base_path": str(resolved),
            "matches": matches[:100],  # Limit results
            "count": len(matches),
            "truncated": len(matches) > 100,
        }

    async def _git_status(self) -> dict[str, Any]:
        """Get git status."""
        if not self.config.enable_git:
            return {"error": "Git operations disabled"}

        try:
            proc = await asyncio.create_subprocess_exec(
                "git",
                "status",
                "--porcelain",
                cwd=str(self._base_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                return {"error": stderr.decode()}

            # Parse status
            modified = []
            added = []
            deleted = []
            untracked = []

            for line in stdout.decode().strip().split("\n"):
                if not line:
                    continue
                status = line[:2]
                filename = line[3:]

                if "M" in status:
                    modified.append(filename)
                elif "A" in status:
                    added.append(filename)
                elif "D" in status:
                    deleted.append(filename)
                elif "?" in status:
                    untracked.append(filename)

            # Get branch
            branch_proc = await asyncio.create_subprocess_exec(
                "git",
                "branch",
                "--show-current",
                cwd=str(self._base_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            branch_stdout, _ = await branch_proc.communicate()
            branch = branch_stdout.decode().strip()

            return {
                "branch": branch,
                "modified": modified,
                "added": added,
                "deleted": deleted,
                "untracked": untracked,
                "clean": not (modified or added or deleted or untracked),
            }

        except FileNotFoundError:
            return {"error": "Git not found"}

    async def _git_diff(self, path: str | None = None) -> dict[str, Any]:
        """Get git diff."""
        if not self.config.enable_git:
            return {"error": "Git operations disabled"}

        try:
            cmd = ["git", "diff"]
            if path:
                resolved = self._resolve_path(path)
                cmd.append(str(resolved))

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self._base_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                return {"error": stderr.decode()}

            return {
                "diff": stdout.decode(),
                "path": path,
                "has_changes": bool(stdout),
            }

        except FileNotFoundError:
            return {"error": "Git not found"}

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    async def read_file(self, path: str) -> CapabilityResult:
        """Read file content."""
        return await self.execute(action="read_file", path=path)

    async def write_file(
        self,
        path: str,
        content: str,
        create_dirs: bool = True,
    ) -> CapabilityResult:
        """Write content to file."""
        return await self.execute(
            action="write_file",
            path=path,
            content=content,
            create_dirs=create_dirs,
        )

    async def glob_files(
        self,
        pattern: str,
        path: str = ".",
    ) -> CapabilityResult:
        """Search files with glob pattern."""
        return await self.execute(
            action="glob_files",
            pattern=pattern,
            path=path,
        )

    async def list_directory(
        self,
        path: str = ".",
        recursive: bool = False,
    ) -> CapabilityResult:
        """List directory contents."""
        return await self.execute(
            action="list_directory",
            path=path,
            recursive=recursive,
        )

    async def git_status(self) -> CapabilityResult:
        """Get git status."""
        return await self.execute(action="git_status")

    async def search_content(
        self,
        pattern: str,
        path: str = ".",
        file_pattern: str = "**/*.py",
    ) -> CapabilityResult:
        """Search for pattern in file contents."""
        return await self.execute(
            action="search_content",
            pattern=pattern,
            path=path,
            file_pattern=file_pattern,
        )
