"""MCP Tools for IDE integration via native CLI commands.

Provides tools to interact with IDEs (VS Code, Cursor, Windsurf, Codium)
using their native CLI commands. This allows agents to:
- Open files at specific lines
- Show diffs between files
- Manage windows and workspaces
- Install/manage extensions
"""

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class IDENotFoundError(Exception):
    """No supported IDE CLI found."""

    pass


class IDECommandError(Exception):
    """IDE command execution failed."""

    pass


# Supported IDEs and their CLI commands
SUPPORTED_IDES: dict[str, dict[str, Any]] = {
    "vscode": {
        "command": "code",
        "display_name": "Visual Studio Code",
        "supports_wait": True,
        "supports_diff": True,
        "supports_merge": True,
    },
    "cursor": {
        "command": "cursor",
        "display_name": "Cursor",
        "supports_wait": True,
        "supports_diff": True,
        "supports_merge": False,
    },
    "windsurf": {
        "command": "windsurf",
        "display_name": "Windsurf",
        "supports_wait": True,
        "supports_diff": True,
        "supports_merge": False,
    },
    "codium": {
        "command": "codium",
        "display_name": "VSCodium",
        "supports_wait": True,
        "supports_diff": True,
        "supports_merge": True,
    },
}


def detect_ide() -> str | None:
    """Detect which IDE CLI is available.

    Checks for IDE CLIs in order of preference:
    1. Cursor (AI-first IDE, likely Paracle target audience)
    2. VS Code (most popular)
    3. Windsurf (AI-focused)
    4. VSCodium (open source alternative)

    Returns:
        IDE identifier or None if no IDE found.
    """
    # Check in order of preference for Paracle users
    preference_order = ["cursor", "vscode", "windsurf", "codium"]

    for ide_id in preference_order:
        cmd = SUPPORTED_IDES[ide_id]["command"]
        if shutil.which(cmd):
            logger.info(f"Detected IDE: {SUPPORTED_IDES[ide_id]['display_name']}")
            return ide_id

    logger.warning("No supported IDE CLI found")
    return None


def get_ide_command(ide: str | None = None) -> str:
    """Get the CLI command for the specified or detected IDE.

    Args:
        ide: IDE identifier (vscode, cursor, windsurf, codium).
             If None, auto-detects.

    Returns:
        CLI command string.

    Raises:
        IDENotFoundError: If no IDE is available.
    """
    if ide is None:
        ide = detect_ide()

    if ide is None:
        raise IDENotFoundError(
            "No supported IDE found. Install one of: "
            "VS Code (code), Cursor (cursor), Windsurf (windsurf), VSCodium (codium)"
        )

    if ide not in SUPPORTED_IDES:
        raise IDENotFoundError(f"Unknown IDE: {ide}. Supported: {list(SUPPORTED_IDES.keys())}")

    return SUPPORTED_IDES[ide]["command"]


def _run_ide_command(args: list[str], ide: str | None = None) -> dict[str, Any]:
    """Execute an IDE CLI command.

    Args:
        args: Command arguments (without the IDE command itself).
        ide: IDE identifier or None for auto-detect.

    Returns:
        Result dict with success status and details.

    Raises:
        IDECommandError: If command execution fails.
    """
    cmd = get_ide_command(ide)
    full_args = [cmd] + args

    logger.debug(f"Executing IDE command: {' '.join(full_args)}")

    try:
        result = subprocess.run(
            full_args,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or f"Command failed with code {result.returncode}"
            raise IDECommandError(error_msg)

        return {
            "success": True,
            "ide": ide or detect_ide(),
            "command": " ".join(full_args),
            "stdout": result.stdout.strip() if result.stdout else None,
        }

    except subprocess.TimeoutExpired:
        raise IDECommandError(f"Command timed out: {' '.join(full_args)}")
    except FileNotFoundError:
        raise IDENotFoundError(f"IDE command not found: {cmd}")


# =============================================================================
# MCP Tool Functions
# =============================================================================


def ide_info() -> dict[str, Any]:
    """Get information about available IDEs.

    Returns:
        Dict with detected IDE and all supported IDEs.
    """
    detected = detect_ide()
    available = {}

    for ide_id, info in SUPPORTED_IDES.items():
        cmd = info["command"]
        is_available = shutil.which(cmd) is not None
        available[ide_id] = {
            "display_name": info["display_name"],
            "command": cmd,
            "available": is_available,
            "supports_diff": info["supports_diff"],
            "supports_merge": info["supports_merge"],
        }

    return {
        "detected_ide": detected,
        "detected_display_name": SUPPORTED_IDES[detected]["display_name"] if detected else None,
        "supported_ides": available,
    }


def ide_open_file(
    path: str,
    line: int | None = None,
    column: int | None = None,
    reuse_window: bool = True,
    ide: str | None = None,
) -> dict[str, Any]:
    """Open a file in the IDE.

    Args:
        path: File path to open.
        line: Optional line number to go to.
        column: Optional column number.
        reuse_window: Reuse existing window (default True).
        ide: IDE identifier or None for auto-detect.

    Returns:
        Result dict with success status.
    """
    # Resolve path
    file_path = Path(path).resolve()
    if not file_path.exists():
        return {"success": False, "error": f"File not found: {path}"}

    args = []

    # Reuse window option
    if reuse_window:
        args.append("-r")

    # Build file path with line/column
    location = str(file_path)
    if line is not None:
        location = f"{file_path}:{line}"
        if column is not None:
            location = f"{file_path}:{line}:{column}"
        args.extend(["-g", location])
    else:
        args.append(location)

    result = _run_ide_command(args, ide)
    result["file"] = str(file_path)
    result["line"] = line
    result["column"] = column
    return result


def ide_open_folder(
    path: str,
    new_window: bool = False,
    add_to_workspace: bool = False,
    ide: str | None = None,
) -> dict[str, Any]:
    """Open a folder in the IDE.

    Args:
        path: Folder path to open.
        new_window: Open in new window.
        add_to_workspace: Add to current workspace instead of opening.
        ide: IDE identifier or None for auto-detect.

    Returns:
        Result dict with success status.
    """
    folder_path = Path(path).resolve()
    if not folder_path.is_dir():
        return {"success": False, "error": f"Folder not found: {path}"}

    args = []

    if new_window:
        args.append("-n")
    elif add_to_workspace:
        args.append("--add")

    args.append(str(folder_path))

    result = _run_ide_command(args, ide)
    result["folder"] = str(folder_path)
    return result


def ide_diff(
    file1: str,
    file2: str,
    wait: bool = False,
    ide: str | None = None,
) -> dict[str, Any]:
    """Show diff between two files in the IDE.

    Args:
        file1: First file path.
        file2: Second file path.
        wait: Wait for diff window to close.
        ide: IDE identifier or None for auto-detect.

    Returns:
        Result dict with success status.
    """
    path1 = Path(file1).resolve()
    path2 = Path(file2).resolve()

    if not path1.exists():
        return {"success": False, "error": f"File not found: {file1}"}
    if not path2.exists():
        return {"success": False, "error": f"File not found: {file2}"}

    args = ["--diff", str(path1), str(path2)]

    if wait:
        args.insert(0, "--wait")

    result = _run_ide_command(args, ide)
    result["file1"] = str(path1)
    result["file2"] = str(path2)
    return result


def ide_merge(
    base: str,
    local: str,
    remote: str,
    result_path: str,
    wait: bool = True,
    ide: str | None = None,
) -> dict[str, Any]:
    """Open 3-way merge editor (VS Code/Codium only).

    Args:
        base: Base file path.
        local: Local file path.
        remote: Remote file path.
        result_path: Output file path.
        wait: Wait for merge to complete.
        ide: IDE identifier or None for auto-detect.

    Returns:
        Result dict with success status.
    """
    # Check IDE supports merge
    detected = ide or detect_ide()
    if detected and not SUPPORTED_IDES.get(detected, {}).get("supports_merge", False):
        return {
            "success": False,
            "error": f"IDE '{detected}' does not support 3-way merge",
        }

    for name, path_str in [("base", base), ("local", local), ("remote", remote)]:
        p = Path(path_str)
        if not p.exists():
            return {"success": False, "error": f"{name} file not found: {path_str}"}

    args = ["--merge", base, local, remote, result_path]

    if wait:
        args.insert(0, "--wait")

    return _run_ide_command(args, ide)


def ide_new_window(
    path: str | None = None,
    ide: str | None = None,
) -> dict[str, Any]:
    """Open a new IDE window.

    Args:
        path: Optional folder to open in new window.
        ide: IDE identifier or None for auto-detect.

    Returns:
        Result dict with success status.
    """
    args = ["-n"]

    if path:
        folder_path = Path(path).resolve()
        if folder_path.exists():
            args.append(str(folder_path))

    return _run_ide_command(args, ide)


def ide_list_extensions(ide: str | None = None) -> dict[str, Any]:
    """List installed IDE extensions.

    Args:
        ide: IDE identifier or None for auto-detect.

    Returns:
        Result dict with list of extensions.
    """
    result = _run_ide_command(["--list-extensions"], ide)

    if result.get("stdout"):
        extensions = [ext.strip() for ext in result["stdout"].split("\n") if ext.strip()]
        result["extensions"] = extensions
        result["count"] = len(extensions)

    return result


def ide_install_extension(
    extension_id: str,
    ide: str | None = None,
) -> dict[str, Any]:
    """Install an IDE extension.

    Args:
        extension_id: Extension identifier (e.g., 'ms-python.python').
        ide: IDE identifier or None for auto-detect.

    Returns:
        Result dict with success status.
    """
    result = _run_ide_command(["--install-extension", extension_id], ide)
    result["extension"] = extension_id
    return result


def ide_uninstall_extension(
    extension_id: str,
    ide: str | None = None,
) -> dict[str, Any]:
    """Uninstall an IDE extension.

    Args:
        extension_id: Extension identifier.
        ide: IDE identifier or None for auto-detect.

    Returns:
        Result dict with success status.
    """
    result = _run_ide_command(["--uninstall-extension", extension_id], ide)
    result["extension"] = extension_id
    return result


def ide_version(ide: str | None = None) -> dict[str, Any]:
    """Get IDE version information.

    Args:
        ide: IDE identifier or None for auto-detect.

    Returns:
        Result dict with version info.
    """
    result = _run_ide_command(["--version"], ide)

    if result.get("stdout"):
        lines = result["stdout"].split("\n")
        result["version_info"] = lines

    return result


# =============================================================================
# MCP Tool Registration
# =============================================================================

IDE_TOOLS = [
    {
        "name": "ide_info",
        "description": "Get information about available IDEs (VS Code, Cursor, Windsurf, Codium)",
        "function": ide_info,
        "parameters": {},
    },
    {
        "name": "ide_open_file",
        "description": "Open a file in the IDE, optionally at a specific line and column",
        "function": ide_open_file,
        "parameters": {
            "path": {"type": "string", "description": "File path to open", "required": True},
            "line": {"type": "integer", "description": "Line number to go to"},
            "column": {"type": "integer", "description": "Column number"},
            "reuse_window": {"type": "boolean", "description": "Reuse existing window (default: true)"},
            "ide": {"type": "string", "description": "IDE to use (vscode, cursor, windsurf, codium)"},
        },
    },
    {
        "name": "ide_open_folder",
        "description": "Open a folder in the IDE",
        "function": ide_open_folder,
        "parameters": {
            "path": {"type": "string", "description": "Folder path to open", "required": True},
            "new_window": {"type": "boolean", "description": "Open in new window"},
            "add_to_workspace": {"type": "boolean", "description": "Add to current workspace"},
            "ide": {"type": "string", "description": "IDE to use"},
        },
    },
    {
        "name": "ide_diff",
        "description": "Show diff between two files in the IDE",
        "function": ide_diff,
        "parameters": {
            "file1": {"type": "string", "description": "First file path", "required": True},
            "file2": {"type": "string", "description": "Second file path", "required": True},
            "wait": {"type": "boolean", "description": "Wait for diff window to close"},
            "ide": {"type": "string", "description": "IDE to use"},
        },
    },
    {
        "name": "ide_merge",
        "description": "Open 3-way merge editor (VS Code/Codium only)",
        "function": ide_merge,
        "parameters": {
            "base": {"type": "string", "description": "Base file path", "required": True},
            "local": {"type": "string", "description": "Local file path", "required": True},
            "remote": {"type": "string", "description": "Remote file path", "required": True},
            "result_path": {"type": "string", "description": "Output file path", "required": True},
            "wait": {"type": "boolean", "description": "Wait for merge to complete"},
            "ide": {"type": "string", "description": "IDE to use"},
        },
    },
    {
        "name": "ide_new_window",
        "description": "Open a new IDE window",
        "function": ide_new_window,
        "parameters": {
            "path": {"type": "string", "description": "Optional folder to open"},
            "ide": {"type": "string", "description": "IDE to use"},
        },
    },
    {
        "name": "ide_list_extensions",
        "description": "List installed IDE extensions",
        "function": ide_list_extensions,
        "parameters": {
            "ide": {"type": "string", "description": "IDE to use"},
        },
    },
    {
        "name": "ide_install_extension",
        "description": "Install an IDE extension",
        "function": ide_install_extension,
        "parameters": {
            "extension_id": {"type": "string", "description": "Extension ID (e.g., 'ms-python.python')", "required": True},
            "ide": {"type": "string", "description": "IDE to use"},
        },
    },
    {
        "name": "ide_uninstall_extension",
        "description": "Uninstall an IDE extension",
        "function": ide_uninstall_extension,
        "parameters": {
            "extension_id": {"type": "string", "description": "Extension ID", "required": True},
            "ide": {"type": "string", "description": "IDE to use"},
        },
    },
    {
        "name": "ide_version",
        "description": "Get IDE version information",
        "function": ide_version,
        "parameters": {
            "ide": {"type": "string", "description": "IDE to use"},
        },
    },
]
