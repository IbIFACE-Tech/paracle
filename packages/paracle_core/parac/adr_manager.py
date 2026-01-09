"""ADR (Architecture Decision Records) Manager.

Manages multi-file ADRs in Markdown format with automatic indexing.
Supports migration from legacy single-file decisions.md format.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

from pydantic import BaseModel

from paracle_core.parac.file_config import ADRConfig, FileManagementConfig


class ADRMetadata(BaseModel):
    """Metadata for an ADR."""

    id: str
    title: str
    date: date
    status: str = "Proposed"
    deciders: str = ""
    file_path: Path | None = None


class ADR(BaseModel):
    """Full ADR content."""

    id: str
    title: str
    date: date
    status: str = "Proposed"
    deciders: str = ""
    context: str = ""
    decision: str = ""
    consequences: str = ""
    implementation: str = ""
    related: str = ""
    file_path: Path | None = None


class ADRManager:
    """Manage Architecture Decision Records.

    Supports:
    - Multi-file ADRs (each ADR as separate .md file)
    - Auto-numbering (ADR-001, ADR-002, etc.)
    - Index file generation (index.md with summary)
    - Migration from legacy single-file format
    - Status management (Proposed -> Accepted -> Deprecated)

    Example:
        >>> manager = ADRManager(parac_root)
        >>> adr_id = manager.create(
        ...     title="Use Python as Primary Language",
        ...     context="Need to choose a language...",
        ...     decision="Use Python 3.10+",
        ...     consequences="Rich ecosystem but performance limits"
        ... )
        >>> print(adr_id)
        'ADR-001'
    """

    def __init__(
        self,
        parac_root: Path,
        config: ADRConfig | None = None,
    ):
        """Initialize ADR manager.

        Args:
            parac_root: Path to .parac/ directory.
            config: Optional ADRConfig. If None, loads from project.yaml.
        """
        self.parac_root = parac_root

        if config is None:
            file_config = FileManagementConfig.from_project_yaml(parac_root)
            config = file_config.adr

        self.config = config
        self.adr_dir = parac_root / config.base_path
        self.index_file = self.adr_dir / config.index_file
        self.legacy_file = (
            parac_root / config.legacy_file if config.legacy_file else None
        )

    def _ensure_dir(self) -> None:
        """Ensure ADR directory exists."""
        self.adr_dir.mkdir(parents=True, exist_ok=True)

    def _get_next_number(self) -> int:
        """Get next ADR number."""
        existing = list(self.adr_dir.glob("ADR-*.md"))
        if not existing:
            return 1

        numbers = []
        for path in existing:
            match = re.match(r"ADR-(\d+)", path.stem)
            if match:
                numbers.append(int(match.group(1)))

        return max(numbers) + 1 if numbers else 1

    def _format_id(self, number: int) -> str:
        """Format ADR ID from number."""
        return self.config.number_format.format(number)

    def create(
        self,
        title: str,
        context: str,
        decision: str,
        consequences: str,
        status: str = "Proposed",
        deciders: str = "Core Team",
        implementation: str = "",
        related: str = "",
    ) -> str:
        """Create a new ADR.

        Args:
            title: Title of the decision.
            context: Why this decision was needed.
            decision: What was decided.
            consequences: Impact of the decision.
            status: Status (Proposed, Accepted, Deprecated, Superseded).
            deciders: Who made the decision.
            implementation: Implementation details.
            related: Related decisions.

        Returns:
            The ADR ID (e.g., 'ADR-001').
        """
        self._ensure_dir()

        number = self._get_next_number()
        adr_id = self._format_id(number)
        today = date.today()

        # Render template
        content = self.config.template.format(
            id=adr_id,
            title=title,
            date=today.isoformat(),
            status=status,
            deciders=deciders,
            context=context,
            decision=decision,
            consequences=consequences,
            implementation=implementation or "TBD",
            related=related or "None",
        )

        # Write ADR file
        filename = f"{adr_id}.md"
        file_path = self.adr_dir / filename
        file_path.write_text(content, encoding="utf-8")

        # Update index
        self._update_index()

        return adr_id

    def get(self, adr_id: str) -> ADR | None:
        """Get ADR by ID.

        Args:
            adr_id: The ADR ID (e.g., 'ADR-001').

        Returns:
            ADR object or None if not found.
        """
        file_path = self.adr_dir / f"{adr_id}.md"
        if not file_path.exists():
            return None

        content = file_path.read_text(encoding="utf-8")
        return self._parse_adr(content, file_path)

    def list(
        self,
        status: str | None = None,
        since: date | None = None,
    ) -> list[ADRMetadata]:
        """List all ADRs with optional filters.

        Args:
            status: Filter by status (Proposed, Accepted, Deprecated).
            since: Filter ADRs created after this date.

        Returns:
            List of ADR metadata objects.
        """
        if not self.adr_dir.exists():
            return []

        adrs: list[ADRMetadata] = []
        for path in sorted(self.adr_dir.glob("ADR-*.md")):
            content = path.read_text(encoding="utf-8")
            metadata = self._parse_metadata(content, path)
            if metadata:
                # Apply filters
                if status and metadata.status != status:
                    continue
                if since and metadata.date < since:
                    continue
                adrs.append(metadata)

        return adrs

    def update_status(self, adr_id: str, new_status: str) -> bool:
        """Update ADR status.

        Args:
            adr_id: The ADR ID (e.g., 'ADR-001').
            new_status: New status (Proposed, Accepted, Deprecated, Superseded).

        Returns:
            True if updated, False if not found.
        """
        file_path = self.adr_dir / f"{adr_id}.md"
        if not file_path.exists():
            return False

        content = file_path.read_text(encoding="utf-8")

        # Replace status line
        new_content = re.sub(
            r"\*\*Status\*\*:\s*\w+",
            f"**Status**: {new_status}",
            content,
        )

        file_path.write_text(new_content, encoding="utf-8")
        self._update_index()
        return True

    def migrate_legacy(self) -> int:
        """Migrate from legacy single-file decisions.md format.

        Parses the legacy file and creates individual ADR files.

        Returns:
            Number of ADRs migrated.
        """
        if self.legacy_file is None or not self.legacy_file.exists():
            return 0

        self._ensure_dir()
        content = self.legacy_file.read_text(encoding="utf-8")

        # Parse legacy ADRs (format: ## ADR-XXX: Title)
        pattern = r"## (ADR-\d+):\s*(.+?)(?=\n## ADR-|\Z)"
        matches = re.findall(pattern, content, re.DOTALL)

        migrated = 0
        for adr_id, adr_content in matches:
            file_path = self.adr_dir / f"{adr_id}.md"
            if file_path.exists():
                continue  # Skip existing

            # Parse sections from content
            adr = self._parse_legacy_adr(adr_id, adr_content)
            if adr:
                self._write_adr(adr)
                migrated += 1

        if migrated > 0:
            self._update_index()

        return migrated

    def _parse_legacy_adr(self, adr_id: str, content: str) -> ADR | None:
        """Parse a legacy ADR section."""
        # Extract title from first line or ID
        title_match = re.search(r"^(.+?)$", content.strip(), re.MULTILINE)
        title = title_match.group(1).strip() if title_match else adr_id

        # Extract date
        date_match = re.search(r"\*\*Date\*\*:\s*(\d{4}-\d{2}-\d{2})", content)
        adr_date = (
            date.fromisoformat(date_match.group(1)) if date_match else date.today()
        )

        # Extract status
        status_match = re.search(r"\*\*Status\*\*:\s*(\w+)", content)
        status = status_match.group(1) if status_match else "Accepted"

        # Extract deciders
        deciders_match = re.search(
            r"\*\*Deciders?\*\*:\s*(.+?)$", content, re.MULTILINE
        )
        deciders = deciders_match.group(1).strip() if deciders_match else "Core Team"

        # Extract sections
        def extract_section(name: str) -> str:
            pattern = rf"###\s*{name}\s*\n(.*?)(?=###|\Z)"
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            return match.group(1).strip() if match else ""

        return ADR(
            id=adr_id,
            title=title,
            date=adr_date,
            status=status,
            deciders=deciders,
            context=extract_section("Context"),
            decision=extract_section("Decision"),
            consequences=extract_section("Consequences"),
            implementation=extract_section("Implementation"),
            related=extract_section("Related"),
        )

    def _write_adr(self, adr: ADR) -> None:
        """Write ADR to file."""
        content = self.config.template.format(
            id=adr.id,
            title=adr.title,
            date=adr.date.isoformat(),
            status=adr.status,
            deciders=adr.deciders,
            context=adr.context or "TBD",
            decision=adr.decision or "TBD",
            consequences=adr.consequences or "TBD",
            implementation=adr.implementation or "TBD",
            related=adr.related or "None",
        )

        file_path = self.adr_dir / f"{adr.id}.md"
        file_path.write_text(content, encoding="utf-8")

    def _parse_adr(self, content: str, file_path: Path) -> ADR:
        """Parse ADR from file content."""
        # Extract ID from filename
        adr_id = file_path.stem

        # Extract title
        title_match = re.search(
            r"#\s*" + re.escape(adr_id) + r":\s*(.+?)$", content, re.MULTILINE
        )
        title = title_match.group(1).strip() if title_match else ""

        # Extract metadata
        date_match = re.search(r"\*\*Date\*\*:\s*(\d{4}-\d{2}-\d{2})", content)
        adr_date = (
            date.fromisoformat(date_match.group(1)) if date_match else date.today()
        )

        status_match = re.search(r"\*\*Status\*\*:\s*(\w+)", content)
        status = status_match.group(1) if status_match else "Proposed"

        deciders_match = re.search(
            r"\*\*Deciders?\*\*:\s*(.+?)$", content, re.MULTILINE
        )
        deciders = deciders_match.group(1).strip() if deciders_match else ""

        # Extract sections
        def extract_section(name: str) -> str:
            pattern = rf"##\s*{name}\s*\n(.*?)(?=##|\Z)"
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            return match.group(1).strip() if match else ""

        return ADR(
            id=adr_id,
            title=title,
            date=adr_date,
            status=status,
            deciders=deciders,
            context=extract_section("Context"),
            decision=extract_section("Decision"),
            consequences=extract_section("Consequences"),
            implementation=extract_section("Implementation"),
            related=extract_section("Related"),
            file_path=file_path,
        )

    def _parse_metadata(self, content: str, file_path: Path) -> ADRMetadata | None:
        """Parse ADR metadata from file content."""
        adr_id = file_path.stem

        # Extract title
        title_match = re.search(
            r"#\s*" + re.escape(adr_id) + r":\s*(.+?)$", content, re.MULTILINE
        )
        title = title_match.group(1).strip() if title_match else ""

        # Extract date
        date_match = re.search(r"\*\*Date\*\*:\s*(\d{4}-\d{2}-\d{2})", content)
        if not date_match:
            return None
        adr_date = date.fromisoformat(date_match.group(1))

        # Extract status
        status_match = re.search(r"\*\*Status\*\*:\s*(\w+)", content)
        status = status_match.group(1) if status_match else "Proposed"

        # Extract deciders
        deciders_match = re.search(
            r"\*\*Deciders?\*\*:\s*(.+?)$", content, re.MULTILINE
        )
        deciders = deciders_match.group(1).strip() if deciders_match else ""

        return ADRMetadata(
            id=adr_id,
            title=title,
            date=adr_date,
            status=status,
            deciders=deciders,
            file_path=file_path,
        )

    def _update_index(self) -> None:
        """Update the index.md file with list of all ADRs."""
        adrs = self.list()

        lines = [
            "# Architecture Decision Records",
            "",
            "This directory contains Architecture Decision Records (ADRs) for the project.",
            "",
            "## ADR Index",
            "",
            "| ID | Title | Status | Date |",
            "|---|---|---|---|",
        ]

        for adr in sorted(adrs, key=lambda a: a.id, reverse=True):
            lines.append(
                f"| [{adr.id}]({adr.id}.md) | {adr.title} | {adr.status} | {adr.date} |"
            )

        lines.extend(
            [
                "",
                "## Statuses",
                "",
                "- **Proposed**: Under discussion",
                "- **Accepted**: Approved and implemented",
                "- **Deprecated**: No longer valid",
                "- **Superseded**: Replaced by another ADR",
                "",
                f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
            ]
        )

        self._ensure_dir()
        self.index_file.write_text("\n".join(lines), encoding="utf-8")

    def search(self, query: str) -> list[ADRMetadata]:
        """Search ADRs by keyword.

        Args:
            query: Search term (case-insensitive).

        Returns:
            List of matching ADR metadata.
        """
        query_lower = query.lower()
        results: list[ADRMetadata] = []

        for path in self.adr_dir.glob("ADR-*.md"):
            content = path.read_text(encoding="utf-8").lower()
            if query_lower in content:
                metadata = self._parse_metadata(path.read_text(encoding="utf-8"), path)
                if metadata:
                    results.append(metadata)

        return results

    def get_by_status(self, status: str) -> list[ADRMetadata]:
        """Get all ADRs with a specific status.

        Args:
            status: Status to filter by.

        Returns:
            List of ADR metadata with that status.
        """
        return self.list(status=status)

    def count_by_status(self) -> dict[str, int]:
        """Count ADRs by status.

        Returns:
            Dictionary mapping status to count.
        """
        adrs = self.list()
        counts: dict[str, int] = {}
        for adr in adrs:
            counts[adr.status] = counts.get(adr.status, 0) + 1
        return counts
