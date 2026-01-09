"""Platform-specific paths for Paracle framework logging.

Provides cross-platform support for Paracle's own logs (not user logs):
- Windows: %LOCALAPPDATA%\\Paracle\\logs\\
- Linux: ~/.local/share/paracle/logs/
- macOS: ~/Library/Application Support/Paracle/logs/
- Docker: /var/log/paracle/ (with fallback to /tmp/paracle/logs/)

User logs go to .parac/memory/logs/ (workspace-specific).
Framework logs go to platform-specific system locations.
"""

import os
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

LogType = Literal["main", "cli", "agent", "errors", "audit"]


class PlatformPaths(BaseModel):
    """Platform-specific directory paths."""

    log_dir: Path = Field(description="Main log directory")
    cache_dir: Path = Field(description="Cache directory")
    data_dir: Path = Field(description="Data directory")
    config_dir: Path = Field(description="Configuration directory")


def detect_platform() -> Literal["windows", "linux", "macos", "docker"]:
    """Detect the current platform.

    Returns:
        Platform identifier: 'windows', 'linux', 'macos', or 'docker'
    """
    # Check if running in Docker
    if os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv"):
        return "docker"

    # Check if k8s environment
    if os.getenv("KUBERNETES_SERVICE_HOST"):
        return "docker"

    # Standard platform detection
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "darwin":
        return "macos"
    else:
        return "linux"


def get_windows_paths() -> PlatformPaths:
    """Get Windows-specific paths using AppData.

    Returns:
        Platform-specific paths for Windows
    """
    local_appdata = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    base_dir = local_appdata / "Paracle"

    return PlatformPaths(
        log_dir=base_dir / "logs",
        cache_dir=base_dir / "cache",
        data_dir=base_dir / "data",
        config_dir=base_dir / "config",
    )


def get_linux_paths() -> PlatformPaths:
    """Get Linux-specific paths using XDG Base Directory Specification.

    Returns:
        Platform-specific paths for Linux
    """
    # XDG Base Directory Specification
    xdg_data_home = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    xdg_cache_home = Path(os.getenv("XDG_CACHE_HOME", Path.home() / ".cache"))
    xdg_config_home = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))

    base_data_dir = xdg_data_home / "paracle"

    return PlatformPaths(
        log_dir=base_data_dir / "logs",
        cache_dir=xdg_cache_home / "paracle",
        data_dir=base_data_dir,
        config_dir=xdg_config_home / "paracle",
    )


def get_macos_paths() -> PlatformPaths:
    """Get macOS-specific paths using Application Support.

    Returns:
        Platform-specific paths for macOS
    """
    home = Path.home()
    app_support = home / "Library" / "Application Support" / "Paracle"

    return PlatformPaths(
        log_dir=app_support / "logs",
        cache_dir=home / "Library" / "Caches" / "Paracle",
        data_dir=app_support,
        config_dir=app_support / "config",
    )


def get_docker_paths() -> PlatformPaths:
    """Get Docker/container-specific paths.

    Uses /var/log/paracle/ if writable, otherwise /tmp/paracle/logs/.

    Returns:
        Platform-specific paths for Docker/containers
    """
    # Try standard container log directory first
    var_log = Path("/var/log/paracle")
    if var_log.exists() or _is_writable_parent(var_log):
        base_dir = var_log
    else:
        # Fallback to /tmp (always writable)
        base_dir = Path("/tmp/paracle")

    return PlatformPaths(
        log_dir=base_dir / "logs",
        cache_dir=base_dir / "cache",
        data_dir=base_dir / "data",
        config_dir=base_dir / "config",
    )


def _is_writable_parent(path: Path) -> bool:
    """Check if parent directory is writable.

    Args:
        path: Path to check

    Returns:
        True if parent is writable
    """
    parent = path.parent
    return parent.exists() and os.access(parent, os.W_OK)


def get_platform_paths() -> PlatformPaths:
    """Get platform-specific paths for current system.

    Automatically detects platform and returns appropriate paths.

    Returns:
        Platform-specific paths

    Example:
        >>> paths = get_platform_paths()
        >>> print(paths.log_dir)
        # Windows: C:\\Users\\username\\AppData\\Local\\Paracle\\logs
        # Linux: /home/username/.local/share/paracle/logs
        # macOS: /Users/username/Library/Application Support/Paracle/logs
        # Docker: /var/log/paracle/logs or /tmp/paracle/logs
    """
    platform = detect_platform()

    if platform == "windows":
        return get_windows_paths()
    elif platform == "linux":
        return get_linux_paths()
    elif platform == "macos":
        return get_macos_paths()
    else:  # docker
        return get_docker_paths()


def get_log_path(log_type: LogType = "main") -> Path:
    """Get path for a specific log type.

    Args:
        log_type: Type of log file
            - 'main': paracle.log (main framework log)
            - 'cli': paracle-cli.log (CLI operations)
            - 'agent': paracle-agent.log (agent execution framework)
            - 'errors': paracle-errors.log (framework errors only)
            - 'audit': paracle-audit.log (security audit, ISO 42001)

    Returns:
        Full path to log file

    Example:
        >>> log_path = get_log_path("main")
        >>> print(log_path)
        # Windows: C:\\Users\\username\\AppData\\Local\\Paracle\\logs\\paracle.log
        # Linux: /home/username/.local/share/paracle/logs/paracle.log
    """
    paths = get_platform_paths()

    # Ensure log directory exists
    paths.log_dir.mkdir(parents=True, exist_ok=True)

    # Map log types to filenames
    log_files = {
        "main": "paracle.log",
        "cli": "paracle-cli.log",
        "agent": "paracle-agent.log",
        "errors": "paracle-errors.log",
        "audit": "paracle-audit.log",
    }

    return paths.log_dir / log_files[log_type]


def ensure_directories() -> PlatformPaths:
    """Ensure all platform-specific directories exist.

    Creates log_dir, cache_dir, data_dir, config_dir if they don't exist.

    Returns:
        Platform paths with all directories created

    Example:
        >>> paths = ensure_directories()
        >>> assert paths.log_dir.exists()
        >>> assert paths.cache_dir.exists()
    """
    paths = get_platform_paths()

    # Create all directories
    paths.log_dir.mkdir(parents=True, exist_ok=True)
    paths.cache_dir.mkdir(parents=True, exist_ok=True)
    paths.data_dir.mkdir(parents=True, exist_ok=True)
    paths.config_dir.mkdir(parents=True, exist_ok=True)

    return paths


def get_info() -> dict[str, str]:
    """Get platform and path information for debugging.

    Returns:
        Dictionary with platform and all paths

    Example:
        >>> info = get_info()
        >>> print(info['platform'])
        'linux'
        >>> print(info['log_dir'])
        '/home/username/.local/share/paracle/logs'
    """
    platform = detect_platform()
    paths = get_platform_paths()

    return {
        "platform": platform,
        "log_dir": str(paths.log_dir),
        "cache_dir": str(paths.cache_dir),
        "data_dir": str(paths.data_dir),
        "config_dir": str(paths.config_dir),
        "main_log": str(get_log_path("main")),
        "cli_log": str(get_log_path("cli")),
        "agent_log": str(get_log_path("agent")),
        "errors_log": str(get_log_path("errors")),
        "audit_log": str(get_log_path("audit")),
    }
