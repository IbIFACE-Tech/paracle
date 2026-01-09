"""Platform-specific paths for Paracle framework.

Provides cross-platform support for system-wide Paracle resources:
- Windows: %LOCALAPPDATA%\\Paracle\\
- Linux: ~/.local/share/paracle/ (XDG Base Directory Specification)
- macOS: ~/Library/Application Support/Paracle/
- Docker: /var/lib/paracle/ (with fallback to /tmp/paracle/)

This module handles SYSTEM resources (framework-level), not user workspace.
User workspace is always .parac/ in the project directory.

System resources include:
- skills/: Framework-provided skills (paracle_meta skills)
- content/templates/: System templates
- cache/: Framework cache
- logs/: Framework logs (see logging.platform for log-specific paths)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

Platform = Literal["windows", "linux", "macos", "docker"]


class SystemPaths(BaseModel):
    """Platform-specific system directory paths.

    These are framework-level paths, separate from user's .parac/ workspace.
    """

    base_dir: Path = Field(description="Base Paracle system directory")
    skills_dir: Path = Field(description="System-wide skills directory")
    templates_dir: Path = Field(description="System templates directory")
    cache_dir: Path = Field(description="Cache directory")
    config_dir: Path = Field(description="System configuration directory")
    data_dir: Path = Field(description="Data directory")
    logs_dir: Path = Field(description="Logs directory")


def detect_platform() -> Platform:
    """Detect the current platform.

    Returns:
        Platform identifier: 'windows', 'linux', 'macos', or 'docker'
    """
    # Check if running in Docker/container
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


def get_windows_paths() -> SystemPaths:
    """Get Windows-specific system paths.

    Uses %LOCALAPPDATA%\\Paracle\\ as base directory.

    Returns:
        Platform-specific system paths for Windows
    """
    local_appdata = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    base_dir = local_appdata / "Paracle"

    return SystemPaths(
        base_dir=base_dir,
        skills_dir=base_dir / "skills",
        templates_dir=base_dir / "templates",
        cache_dir=base_dir / "cache",
        config_dir=base_dir / "config",
        data_dir=base_dir / "data",
        logs_dir=base_dir / "logs",
    )


def get_linux_paths() -> SystemPaths:
    """Get Linux-specific system paths.

    Uses XDG Base Directory Specification:
    - Data: ~/.local/share/paracle/
    - Cache: ~/.cache/paracle/
    - Config: ~/.config/paracle/

    Returns:
        Platform-specific system paths for Linux
    """
    # XDG Base Directory Specification
    xdg_data_home = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    xdg_cache_home = Path(os.getenv("XDG_CACHE_HOME", Path.home() / ".cache"))
    xdg_config_home = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))

    base_dir = xdg_data_home / "paracle"

    return SystemPaths(
        base_dir=base_dir,
        skills_dir=base_dir / "skills",
        templates_dir=base_dir / "templates",
        cache_dir=xdg_cache_home / "paracle",
        config_dir=xdg_config_home / "paracle",
        data_dir=base_dir / "data",
        logs_dir=base_dir / "logs",
    )


def get_macos_paths() -> SystemPaths:
    """Get macOS-specific system paths.

    Uses ~/Library/Application Support/Paracle/ as base directory.

    Returns:
        Platform-specific system paths for macOS
    """
    home = Path.home()
    app_support = home / "Library" / "Application Support" / "Paracle"

    return SystemPaths(
        base_dir=app_support,
        skills_dir=app_support / "skills",
        templates_dir=app_support / "templates",
        cache_dir=home / "Library" / "Caches" / "Paracle",
        config_dir=app_support / "config",
        data_dir=app_support / "data",
        logs_dir=app_support / "logs",
    )


def get_docker_paths() -> SystemPaths:
    """Get Docker/container-specific system paths.

    Uses /var/lib/paracle/ if writable, otherwise /tmp/paracle/.

    Returns:
        Platform-specific system paths for Docker/containers
    """
    # Try standard container data directory first
    var_lib = Path("/var/lib/paracle")
    if var_lib.exists() or _is_writable_parent(var_lib):
        base_dir = var_lib
    else:
        # Fallback to /tmp (always writable)
        base_dir = Path("/tmp/paracle")

    return SystemPaths(
        base_dir=base_dir,
        skills_dir=base_dir / "skills",
        templates_dir=base_dir / "templates",
        cache_dir=base_dir / "cache",
        config_dir=base_dir / "config",
        data_dir=base_dir / "data",
        logs_dir=base_dir / "logs",
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


def get_system_paths() -> SystemPaths:
    """Get platform-specific system paths for current system.

    Automatically detects platform and returns appropriate paths.

    Returns:
        Platform-specific system paths

    Example:
        >>> paths = get_system_paths()
        >>> print(paths.skills_dir)
        # Windows: C:\\Users\\username\\AppData\\Local\\Paracle\\skills
        # Linux: /home/username/.local/share/paracle/skills
        # macOS: /Users/username/Library/Application Support/Paracle/skills
        # Docker: /var/lib/paracle/skills or /tmp/paracle/skills
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


def get_system_skills_dir() -> Path:
    """Get the system-wide skills directory.

    This is where paracle_meta and framework-provided skills are stored.
    Separate from user's .parac/agents/skills/ workspace.

    Returns:
        Path to system skills directory

    Example:
        >>> skills_dir = get_system_skills_dir()
        >>> print(skills_dir)
        # Linux: /home/user/.local/share/paracle/skills
    """
    return get_system_paths().skills_dir


def ensure_system_directories() -> SystemPaths:
    """Ensure all system directories exist.

    Creates skills_dir, templates_dir, cache_dir, config_dir, data_dir, logs_dir
    if they don't exist.

    Returns:
        System paths with all directories created

    Example:
        >>> paths = ensure_system_directories()
        >>> assert paths.skills_dir.exists()
    """
    paths = get_system_paths()

    # Create all directories
    paths.skills_dir.mkdir(parents=True, exist_ok=True)
    paths.templates_dir.mkdir(parents=True, exist_ok=True)
    paths.cache_dir.mkdir(parents=True, exist_ok=True)
    paths.config_dir.mkdir(parents=True, exist_ok=True)
    paths.data_dir.mkdir(parents=True, exist_ok=True)
    paths.logs_dir.mkdir(parents=True, exist_ok=True)

    return paths


def get_system_info() -> dict[str, str]:
    """Get platform and path information for debugging.

    Returns:
        Dictionary with platform and all system paths

    Example:
        >>> info = get_system_info()
        >>> print(info['platform'])
        'linux'
        >>> print(info['skills_dir'])
        '/home/username/.local/share/paracle/skills'
    """
    platform = detect_platform()
    paths = get_system_paths()

    return {
        "platform": platform,
        "base_dir": str(paths.base_dir),
        "skills_dir": str(paths.skills_dir),
        "templates_dir": str(paths.templates_dir),
        "cache_dir": str(paths.cache_dir),
        "config_dir": str(paths.config_dir),
        "data_dir": str(paths.data_dir),
        "logs_dir": str(paths.logs_dir),
    }
