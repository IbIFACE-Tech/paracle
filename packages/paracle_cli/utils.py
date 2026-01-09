"""Common utilities for CLI commands.

This module provides shared helper functions used across multiple CLI commands,
consolidating duplicate code and ensuring consistent behavior.
"""

from pathlib import Path
from typing import Optional

from paracle_core.parac.state import find_parac_root
from rich.console import Console

console = Console()


def get_parac_root_or_exit() -> Path:
    """Get .parac root directory or exit with error message.

    Returns:
        Path to .parac directory

    Raises:
        SystemExit: If not in a Paracle project

    Example:
        >>> parac_root = get_parac_root_or_exit()
        >>> agents_dir = parac_root / "agents"
    """
    parac_root = find_parac_root()
    if parac_root is None:
        console.print("[red]Error:[/red] Not in a Paracle project")
        console.print("Run 'paracle init' to initialize")
        raise SystemExit(1)
    return parac_root


def get_api_client() -> Optional["APIClient"]:
    """Get API client if server is running.

    Returns:
        APIClient instance if server is reachable, None otherwise

    Example:
        >>> client = get_api_client()
        >>> if client:
        ...     response = client.get("/agents")

    Note:
        This function does not raise an exception if the server is not
        reachable. It simply returns None, allowing commands to gracefully
        handle the absence of a running API server.
    """
    try:
        from paracle_api.client import APIClient

        client = APIClient()
        # Verify server is reachable with a health check
        client.get("/health")
        return client
    except Exception:
        return None


def get_skills_dir() -> Path:
    """Get project skills directory.

    Returns:
        Path to .parac/agents/skills/

    Raises:
        SystemExit: If not in a Paracle project

    Example:
        >>> skills_dir = get_skills_dir()
        >>> skill_path = skills_dir / "my-skill" / "SKILL.md"
    """
    parac_root = get_parac_root_or_exit()
    return parac_root / "agents" / "skills"


def get_system_skills_dir() -> Path:
    """Get system-wide skills directory.

    Returns:
        Path to ~/.paracle/skills/

    Example:
        >>> system_skills = get_system_skills_dir()
        >>> bundled_skills = system_skills / "bundled"

    Note:
        This directory is used for system-wide skills installed via
        `paracle meta skills install-bundled`.
    """
    return Path.home() / ".paracle" / "skills"
