"""Conventional Commits implementation.

Implements the Conventional Commits specification for
standardized commit message formatting.

Reference: https://www.conventionalcommits.org/
"""

from enum import Enum

from pydantic import BaseModel, Field


class CommitType(str, Enum):
    """Conventional commit types."""

    FEAT = "feat"  # New feature
    FIX = "fix"  # Bug fix
    DOCS = "docs"  # Documentation changes
    STYLE = "style"  # Code style changes (formatting, etc)
    REFACTOR = "refactor"  # Code refactoring
    PERF = "perf"  # Performance improvements
    TEST = "test"  # Test additions or changes
    BUILD = "build"  # Build system changes
    CI = "ci"  # CI/CD changes
    CHORE = "chore"  # Maintenance tasks
    REVERT = "revert"  # Revert previous commit


class ConventionalCommit(BaseModel):
    """Conventional commit message.

    Format: <type>[optional scope]: <description>

    [optional body]

    [optional footer(s)]

    Attributes:
        type: Commit type (feat, fix, etc)
        scope: Optional scope (component/module affected)
        description: Short description (subject line)
        body: Optional longer description
        breaking: Whether this is a breaking change
        footer: Optional footer (e.g., issue references)
    """

    type: CommitType
    scope: str | None = None
    description: str = Field(min_length=1, max_length=72)
    body: str | None = None
    breaking: bool = False
    footer: str | None = None

    def format(self) -> str:
        """Format as conventional commit message.

        Returns:
            Formatted commit message
        """
        # Header line
        header = f"{self.type.value}"
        if self.scope:
            header += f"({self.scope})"
        if self.breaking:
            header += "!"
        header += f": {self.description}"

        # Full message
        parts = [header]

        if self.body:
            parts.append("")  # Blank line
            parts.append(self.body)

        if self.breaking and "BREAKING CHANGE:" not in (self.body or ""):
            parts.append("")  # Blank line
            parts.append("BREAKING CHANGE: This commit contains breaking changes")

        if self.footer:
            parts.append("")  # Blank line
            parts.append(self.footer)

        return "\n".join(parts)

    @classmethod
    def from_string(cls, message: str) -> "ConventionalCommit":
        """Parse conventional commit from string.

        Args:
            message: Commit message string

        Returns:
            ConventionalCommit instance

        Raises:
            ValueError: If message doesn't match conventional format
        """
        lines = message.strip().split("\n")
        if not lines:
            raise ValueError("Empty commit message")

        # Parse header
        header = lines[0]
        breaking = "!" in header

        # Extract type and scope
        if "(" in header:
            type_part, rest = header.split("(", 1)
            scope, rest = rest.split(")", 1)
        else:
            if ":" not in header:
                raise ValueError(f"Invalid commit format: {header}")
            type_part, rest = header.split(":", 1)
            scope = None

        # Remove ! from type if present
        type_part = type_part.replace("!", "")

        # Extract description
        description = rest.lstrip(": ").strip()

        # Parse body and footer
        body_lines = []
        footer_lines = []
        in_footer = False

        for line in lines[1:]:
            if not line.strip():
                continue
            if (
                line.startswith("BREAKING CHANGE:")
                or line.startswith("Refs:")
                or line.startswith("Closes:")
            ):
                in_footer = True
            if in_footer:
                footer_lines.append(line)
            else:
                body_lines.append(line)

        body = "\n".join(body_lines) if body_lines else None
        footer = "\n".join(footer_lines) if footer_lines else None

        # Check for breaking change
        if "BREAKING CHANGE:" in message:
            breaking = True

        return cls(
            type=CommitType(type_part),
            scope=scope,
            description=description,
            body=body,
            breaking=breaking,
            footer=footer,
        )


def create_commit_message(
    type: CommitType,
    description: str,
    scope: str | None = None,
    body: str | None = None,
    breaking: bool = False,
    footer: str | None = None,
) -> str:
    """Create a conventional commit message.

    Args:
        type: Commit type
        description: Short description
        scope: Optional scope
        body: Optional body
        breaking: Whether breaking change
        footer: Optional footer

    Returns:
        Formatted commit message
    """
    commit = ConventionalCommit(
        type=type,
        scope=scope,
        description=description,
        body=body,
        breaking=breaking,
        footer=footer,
    )
    return commit.format()
