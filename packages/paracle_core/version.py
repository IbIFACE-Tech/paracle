"""Paracle version information - Single source of truth.

This module provides the canonical version number for Paracle.
All other modules should import from here to ensure consistency.

Version Format: Semantic Versioning (SemVer)
    MAJOR.MINOR.PATCH

    - MAJOR: Breaking changes
    - MINOR: New features (backward compatible)
    - PATCH: Bug fixes (backward compatible)

Usage:
    from paracle_core.version import __version__
    print(f"Paracle v{__version__}")
"""

__version__ = "1.0.3"
__version_info__ = tuple(int(x) for x in __version__.split("."))

# Version metadata
VERSION_MAJOR = __version_info__[0]
VERSION_MINOR = __version_info__[1]
VERSION_PATCH = __version_info__[2]

# Release information
RELEASE_DATE = "2026-01-10"
RELEASE_NAME = "Production Ready"
RELEASE_CODENAME = "Phoenix"  # v1.0 series

# Feature flags based on version
FEATURES = {
    "mcp_full_coverage": True,  # v1.0.0+
    "docker_optional": True,  # v1.0.2+
    "watch_mode": True,  # v1.0.3+
    "health_check": True,  # v1.0.3+
    "migration_guide": True,  # v1.0.3+
    "dx_metrics": True,  # v1.0.3+
}


def get_version() -> str:
    """Get the current version string.

    Returns:
        Version string in format "MAJOR.MINOR.PATCH"
    """
    return __version__


def get_version_info() -> tuple[int, int, int]:
    """Get version as tuple.

    Returns:
        Tuple of (major, minor, patch)
    """
    return __version_info__


def is_feature_available(feature: str) -> bool:
    """Check if a feature is available in this version.

    Args:
        feature: Feature name (e.g., 'mcp_full_coverage')

    Returns:
        True if feature is available, False otherwise
    """
    return FEATURES.get(feature, False)


def format_version(include_date: bool = False) -> str:
    """Format version string with optional metadata.

    Args:
        include_date: Include release date

    Returns:
        Formatted version string

    Examples:
        >>> format_version()
        'Paracle v1.0.3'
        >>> format_version(include_date=True)
        'Paracle v1.0.3 (2026-01-10)'
    """
    if include_date:
        return f"Paracle v{__version__} ({RELEASE_DATE})"
    return f"Paracle v{__version__}"


# For backward compatibility
VERSION = __version__
