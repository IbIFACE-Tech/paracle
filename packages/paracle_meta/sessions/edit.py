"""Edit session for structured code editing and refactoring.

This module provides an edit session that enables targeted code modifications
with diff previews, multi-file operations, and undo support.

Example:
    >>> from paracle_meta.sessions import EditSession, EditConfig
    >>> from paracle_meta.capabilities.providers import AnthropicProvider
    >>> from paracle_meta.registry import CapabilityRegistry
    >>>
    >>> provider = AnthropicProvider()
    >>> registry = CapabilityRegistry()
    >>> await registry.initialize()
    >>>
    >>> config = EditConfig(
    ...     auto_apply=False,  # Preview before applying
    ...     create_backups=True,
    ... )
    >>>
    >>> async with EditSession(provider, registry, config) as editor:
    ...     # Single file edit
    ...     edit = await editor.edit_file(
    ...         "src/main.py",
    ...         instructions="Add type hints to all functions"
    ...     )
    ...     print(edit.diff)  # Preview changes
    ...     await editor.apply(edit)  # Apply if satisfied
    ...
    ...     # Multi-file refactoring
    ...     edits = await editor.refactor(
    ...         pattern="**/*.py",
    ...         instructions="Rename 'get_user' to 'fetch_user' everywhere"
    ...     )
    ...     await editor.apply_all(edits)
    ...
    ...     # Search and replace
    ...     edits = await editor.search_replace(
    ...         search="TODO:",
    ...         replace="FIXME:",
    ...         pattern="**/*.py"
    ...     )
"""

from __future__ import annotations

import difflib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

from paracle_meta.capabilities.provider_protocol import LLMMessage, LLMRequest
from paracle_meta.sessions.base import (
    Session,
    SessionConfig,
    SessionMessage,
    SessionStatus,
)

if TYPE_CHECKING:
    from paracle_meta.capabilities.provider_protocol import CapabilityProvider
    from paracle_meta.registry import CapabilityRegistry


# Edit mode system prompt
EDIT_SYSTEM_PROMPT = """You are a precise code editor. Your role is to make targeted, accurate code modifications.

When editing code:
1. Understand the EXACT change requested
2. Preserve existing formatting and style
3. Make minimal changes - only what's necessary
4. Maintain code correctness and functionality
5. Keep imports organized
6. Preserve comments unless specifically asked to modify them

Output format for edits:
- Return ONLY the modified code
- Do not include explanations unless asked
- Do not add extra features beyond what's requested
- Match the existing code style exactly

For refactoring:
- Ensure all references are updated
- Maintain backward compatibility when possible
- Update related tests if requested"""


class EditType(Enum):
    """Type of edit operation."""

    MODIFY = "modify"  # Modify existing content
    INSERT = "insert"  # Insert new content
    DELETE = "delete"  # Delete content
    REPLACE = "replace"  # Search and replace
    REFACTOR = "refactor"  # Multi-file refactoring
    FORMAT = "format"  # Code formatting


class EditStatus(Enum):
    """Status of an edit operation."""

    PENDING = "pending"  # Not yet applied
    PREVIEWED = "previewed"  # Diff generated, awaiting approval
    APPLIED = "applied"  # Successfully applied
    REVERTED = "reverted"  # Applied then undone
    FAILED = "failed"  # Failed to apply
    SKIPPED = "skipped"  # Skipped by user


@dataclass
class EditOperation:
    """A single edit operation.

    Attributes:
        id: Unique operation ID.
        file_path: Path to the file being edited.
        edit_type: Type of edit.
        instructions: Human instructions for the edit.
        original_content: Original file content.
        new_content: New content after edit.
        diff: Unified diff of changes.
        status: Current status.
        line_start: Starting line (for partial edits).
        line_end: Ending line (for partial edits).
        search_pattern: Search pattern (for replace operations).
        replace_pattern: Replace pattern (for replace operations).
        backup_path: Path to backup file.
        error: Error message if failed.
        created_at: When the operation was created.
        applied_at: When the operation was applied.
    """

    file_path: str
    edit_type: EditType
    instructions: str = ""
    original_content: str = ""
    new_content: str = ""
    diff: str = ""
    status: EditStatus = EditStatus.PENDING
    id: str = field(default_factory=lambda: f"edit_{uuid.uuid4().hex[:12]}")
    line_start: int | None = None
    line_end: int | None = None
    search_pattern: str | None = None
    replace_pattern: str | None = None
    backup_path: str | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    applied_at: datetime | None = None

    @property
    def has_changes(self) -> bool:
        """Whether the edit has actual changes."""
        return self.original_content != self.new_content

    @property
    def lines_added(self) -> int:
        """Number of lines added."""
        if not self.has_changes:
            return 0
        orig_lines = len(self.original_content.splitlines())
        new_lines = len(self.new_content.splitlines())
        return max(0, new_lines - orig_lines)

    @property
    def lines_removed(self) -> int:
        """Number of lines removed."""
        if not self.has_changes:
            return 0
        orig_lines = len(self.original_content.splitlines())
        new_lines = len(self.new_content.splitlines())
        return max(0, orig_lines - new_lines)

    def generate_diff(self, context_lines: int = 3) -> str:
        """Generate unified diff.

        Args:
            context_lines: Number of context lines around changes.

        Returns:
            Unified diff string.
        """
        original_lines = self.original_content.splitlines(keepends=True)
        new_lines = self.new_content.splitlines(keepends=True)

        diff = difflib.unified_diff(
            original_lines,
            new_lines,
            fromfile=f"a/{self.file_path}",
            tofile=f"b/{self.file_path}",
            n=context_lines,
        )

        self.diff = "".join(diff)
        return self.diff

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "file_path": self.file_path,
            "edit_type": self.edit_type.value,
            "instructions": self.instructions,
            "status": self.status.value,
            "has_changes": self.has_changes,
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
            "diff": self.diff,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
        }


@dataclass
class EditBatch:
    """A batch of related edit operations.

    Attributes:
        id: Batch ID.
        description: Description of the batch.
        operations: List of edit operations.
        status: Overall batch status.
    """

    description: str
    operations: list[EditOperation] = field(default_factory=list)
    id: str = field(default_factory=lambda: f"batch_{uuid.uuid4().hex[:12]}")
    status: EditStatus = EditStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def file_count(self) -> int:
        """Number of files affected."""
        return len(set(op.file_path for op in self.operations))

    @property
    def total_lines_added(self) -> int:
        """Total lines added across all operations."""
        return sum(op.lines_added for op in self.operations)

    @property
    def total_lines_removed(self) -> int:
        """Total lines removed across all operations."""
        return sum(op.lines_removed for op in self.operations)

    @property
    def is_complete(self) -> bool:
        """Whether all operations are complete."""
        return all(
            op.status in (EditStatus.APPLIED, EditStatus.SKIPPED, EditStatus.REVERTED)
            for op in self.operations
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "description": self.description,
            "file_count": self.file_count,
            "operation_count": len(self.operations),
            "total_lines_added": self.total_lines_added,
            "total_lines_removed": self.total_lines_removed,
            "status": self.status.value,
            "operations": [op.to_dict() for op in self.operations],
        }


@dataclass
class EditConfig(SessionConfig):
    """Configuration for edit sessions.

    Attributes:
        auto_apply: Whether to apply edits automatically.
        create_backups: Whether to create backup files.
        backup_suffix: Suffix for backup files.
        preview_context_lines: Lines of context in diff preview.
        max_file_size_kb: Maximum file size to edit (KB).
        allowed_extensions: Allowed file extensions (None = all).
        confirm_destructive: Require confirmation for destructive edits.
    """

    auto_apply: bool = False
    create_backups: bool = True
    backup_suffix: str = ".bak"
    preview_context_lines: int = 3
    max_file_size_kb: int = 1024  # 1MB
    allowed_extensions: list[str] | None = None
    confirm_destructive: bool = True

    def __post_init__(self) -> None:
        """Set default system prompt."""
        if self.system_prompt is None:
            self.system_prompt = EDIT_SYSTEM_PROMPT


class EditSession(Session):
    """Edit session for structured code editing.

    Provides a workflow for making targeted code changes with
    diff previews, multi-file support, and undo capabilities.

    Attributes:
        config: Edit configuration.
        pending_edits: Edits awaiting application.
        applied_edits: Successfully applied edits.
        batches: Edit batches for multi-file operations.
    """

    def __init__(
        self,
        provider: CapabilityProvider,
        registry: CapabilityRegistry,
        config: EditConfig | None = None,
    ):
        """Initialize edit session.

        Args:
            provider: LLM provider.
            registry: Capability registry.
            config: Edit configuration.
        """
        super().__init__(provider, registry, config or EditConfig())
        self.config: EditConfig = self.config  # type: ignore
        self.pending_edits: list[EditOperation] = []
        self.applied_edits: list[EditOperation] = []
        self.batches: dict[str, EditBatch] = {}
        self._filesystem: Any = None

    async def initialize(self) -> None:
        """Initialize the edit session."""
        # Get filesystem capability for file operations
        self._filesystem = await self.registry.get("filesystem")
        self.status = SessionStatus.ACTIVE

    async def send(self, message: str) -> SessionMessage:
        """Send an edit request.

        Args:
            message: Edit instructions.

        Returns:
            Response with edit summary.
        """
        # Parse the message to determine edit type
        if "refactor" in message.lower():
            edits = await self._handle_refactor_request(message)
        elif "replace" in message.lower() or "rename" in message.lower():
            edits = await self._handle_replace_request(message)
        else:
            edits = await self._handle_edit_request(message)

        # Format response
        response = self._format_edit_response(edits)
        return await self.add_message("assistant", response)

    async def edit_file(
        self,
        file_path: str,
        instructions: str,
        line_start: int | None = None,
        line_end: int | None = None,
    ) -> EditOperation:
        """Edit a single file.

        Args:
            file_path: Path to the file.
            instructions: Edit instructions.
            line_start: Start line for partial edit.
            line_end: End line for partial edit.

        Returns:
            The edit operation with diff preview.
        """
        # Read original content
        result = await self._filesystem.read_file(file_path)
        if not result.success:
            return self._create_failed_edit(
                file_path, instructions, f"Cannot read file: {result.error}"
            )

        original_content = result.output.get("content", "")

        # Extract section if line range specified
        if line_start is not None:
            lines = original_content.splitlines(keepends=True)
            end = line_end or len(lines)
            section = "".join(lines[line_start - 1 : end])
        else:
            section = original_content

        # Generate edited content using LLM
        new_section = await self._generate_edit(section, instructions, file_path)

        # Reconstruct full content if partial edit
        if line_start is not None:
            lines = original_content.splitlines(keepends=True)
            end = line_end or len(lines)
            new_lines = new_section.splitlines(keepends=True)
            lines[line_start - 1 : end] = new_lines
            new_content = "".join(lines)
        else:
            new_content = new_section

        # Create edit operation
        edit = EditOperation(
            file_path=file_path,
            edit_type=EditType.MODIFY,
            instructions=instructions,
            original_content=original_content,
            new_content=new_content,
            line_start=line_start,
            line_end=line_end,
        )

        # Generate diff
        edit.generate_diff(self.config.preview_context_lines)
        edit.status = EditStatus.PREVIEWED

        self.pending_edits.append(edit)

        # Auto-apply if configured
        if self.config.auto_apply and edit.has_changes:
            await self.apply(edit)

        return edit

    async def insert_code(
        self,
        file_path: str,
        content: str,
        after_line: int | None = None,
        before_line: int | None = None,
    ) -> EditOperation:
        """Insert code into a file.

        Args:
            file_path: Path to the file.
            content: Content to insert.
            after_line: Insert after this line.
            before_line: Insert before this line.

        Returns:
            The edit operation.
        """
        result = await self._filesystem.read_file(file_path)
        if not result.success:
            return self._create_failed_edit(
                file_path, "Insert code", f"Cannot read file: {result.error}"
            )

        original_content = result.output.get("content", "")
        lines = original_content.splitlines(keepends=True)

        # Determine insertion point
        if after_line is not None:
            insert_at = after_line
        elif before_line is not None:
            insert_at = before_line - 1
        else:
            insert_at = len(lines)  # End of file

        # Ensure content ends with newline
        if not content.endswith("\n"):
            content += "\n"

        # Insert content
        content_lines = content.splitlines(keepends=True)
        lines[insert_at:insert_at] = content_lines
        new_content = "".join(lines)

        edit = EditOperation(
            file_path=file_path,
            edit_type=EditType.INSERT,
            instructions=f"Insert code at line {insert_at + 1}",
            original_content=original_content,
            new_content=new_content,
            line_start=insert_at + 1,
        )

        edit.generate_diff(self.config.preview_context_lines)
        edit.status = EditStatus.PREVIEWED
        self.pending_edits.append(edit)

        if self.config.auto_apply:
            await self.apply(edit)

        return edit

    async def delete_lines(
        self,
        file_path: str,
        start_line: int,
        end_line: int | None = None,
    ) -> EditOperation:
        """Delete lines from a file.

        Args:
            file_path: Path to the file.
            start_line: First line to delete.
            end_line: Last line to delete (inclusive).

        Returns:
            The edit operation.
        """
        result = await self._filesystem.read_file(file_path)
        if not result.success:
            return self._create_failed_edit(
                file_path, "Delete lines", f"Cannot read file: {result.error}"
            )

        original_content = result.output.get("content", "")
        lines = original_content.splitlines(keepends=True)

        end = end_line or start_line
        del lines[start_line - 1 : end]
        new_content = "".join(lines)

        edit = EditOperation(
            file_path=file_path,
            edit_type=EditType.DELETE,
            instructions=f"Delete lines {start_line}-{end}",
            original_content=original_content,
            new_content=new_content,
            line_start=start_line,
            line_end=end,
        )

        edit.generate_diff(self.config.preview_context_lines)
        edit.status = EditStatus.PREVIEWED
        self.pending_edits.append(edit)

        if self.config.auto_apply:
            await self.apply(edit)

        return edit

    async def search_replace(
        self,
        search: str,
        replace: str,
        file_path: str | None = None,
        pattern: str | None = None,
        regex: bool = False,
    ) -> list[EditOperation]:
        """Search and replace across files.

        Args:
            search: Search string or pattern.
            replace: Replacement string.
            file_path: Specific file (if None, uses pattern).
            pattern: Glob pattern for files.
            regex: Whether search is a regex.

        Returns:
            List of edit operations.
        """
        import re

        edits: list[EditOperation] = []

        # Get files to process
        if file_path:
            files = [file_path]
        elif pattern:
            result = await self._filesystem.glob_files(pattern)
            if result.success:
                files = [m["path"] for m in result.output.get("matches", [])]
            else:
                return edits
        else:
            return edits

        for fp in files:
            result = await self._filesystem.read_file(fp)
            if not result.success:
                continue

            original = result.output.get("content", "")

            # Perform replacement
            if regex:
                new_content = re.sub(search, replace, original)
            else:
                new_content = original.replace(search, replace)

            if original != new_content:
                edit = EditOperation(
                    file_path=fp,
                    edit_type=EditType.REPLACE,
                    instructions=f"Replace '{search}' with '{replace}'",
                    original_content=original,
                    new_content=new_content,
                    search_pattern=search,
                    replace_pattern=replace,
                )
                edit.generate_diff(self.config.preview_context_lines)
                edit.status = EditStatus.PREVIEWED
                edits.append(edit)
                self.pending_edits.append(edit)

        return edits

    async def refactor(
        self,
        instructions: str,
        pattern: str = "**/*.py",
    ) -> EditBatch:
        """Perform multi-file refactoring.

        Args:
            instructions: Refactoring instructions.
            pattern: Glob pattern for files.

        Returns:
            Batch of edit operations.
        """
        batch = EditBatch(description=instructions)

        # Get files matching pattern
        result = await self._filesystem.glob_files(pattern)
        if not result.success:
            batch.status = EditStatus.FAILED
            return batch

        files = [m["path"] for m in result.output.get("matches", [])]

        # Analyze what needs to change
        analysis = await self._analyze_refactor(instructions, files)

        # Create edits for each affected file
        for file_path in analysis.get("affected_files", files[:10]):
            edit = await self.edit_file(file_path, instructions)
            if edit.has_changes:
                batch.operations.append(edit)

        batch.status = EditStatus.PREVIEWED
        self.batches[batch.id] = batch

        return batch

    async def apply(self, edit: EditOperation) -> bool:
        """Apply a single edit.

        Args:
            edit: The edit operation to apply.

        Returns:
            True if successful.
        """
        if edit.status == EditStatus.APPLIED:
            return True

        if not edit.has_changes:
            edit.status = EditStatus.SKIPPED
            return True

        try:
            # Create backup if configured
            if self.config.create_backups:
                backup_path = edit.file_path + self.config.backup_suffix
                result = await self._filesystem.execute(
                    action="copy_file",
                    source=edit.file_path,
                    destination=backup_path,
                )
                if result.success:
                    edit.backup_path = backup_path

            # Write new content
            result = await self._filesystem.write_file(
                edit.file_path,
                edit.new_content,
            )

            if result.success:
                edit.status = EditStatus.APPLIED
                edit.applied_at = datetime.now(timezone.utc)

                # Move from pending to applied
                if edit in self.pending_edits:
                    self.pending_edits.remove(edit)
                self.applied_edits.append(edit)

                return True
            else:
                edit.status = EditStatus.FAILED
                edit.error = result.error
                return False

        except Exception as e:
            edit.status = EditStatus.FAILED
            edit.error = str(e)
            return False

    async def apply_all(
        self,
        edits: list[EditOperation] | EditBatch | None = None,
    ) -> dict[str, int]:
        """Apply multiple edits.

        Args:
            edits: Edits to apply (or all pending if None).

        Returns:
            Statistics about applied edits.
        """
        if isinstance(edits, EditBatch):
            ops = edits.operations
        elif edits:
            ops = edits
        else:
            ops = self.pending_edits.copy()

        stats = {"applied": 0, "failed": 0, "skipped": 0}

        for edit in ops:
            if edit.status in (EditStatus.APPLIED, EditStatus.SKIPPED):
                stats["skipped"] += 1
                continue

            success = await self.apply(edit)
            if success:
                stats["applied"] += 1
            else:
                stats["failed"] += 1

        return stats

    async def revert(self, edit: EditOperation) -> bool:
        """Revert an applied edit.

        Args:
            edit: The edit to revert.

        Returns:
            True if successful.
        """
        if edit.status != EditStatus.APPLIED:
            return False

        try:
            # Restore from backup if available
            if edit.backup_path:
                result = await self._filesystem.execute(
                    action="copy_file",
                    source=edit.backup_path,
                    destination=edit.file_path,
                )
            else:
                # Write original content
                result = await self._filesystem.write_file(
                    edit.file_path,
                    edit.original_content,
                )

            if result.success:
                edit.status = EditStatus.REVERTED
                return True
            return False

        except Exception:
            return False

    async def skip(self, edit: EditOperation) -> None:
        """Skip an edit operation.

        Args:
            edit: The edit to skip.
        """
        edit.status = EditStatus.SKIPPED
        if edit in self.pending_edits:
            self.pending_edits.remove(edit)

    def get_diff(self, edit: EditOperation | None = None) -> str:
        """Get diff for edit(s).

        Args:
            edit: Specific edit (or all pending if None).

        Returns:
            Combined diff string.
        """
        if edit:
            return edit.diff

        diffs = []
        for e in self.pending_edits:
            if e.diff:
                diffs.append(e.diff)

        return "\n".join(diffs)

    def get_summary(self) -> dict[str, Any]:
        """Get session summary.

        Returns:
            Summary statistics.
        """
        return {
            "pending_edits": len(self.pending_edits),
            "applied_edits": len(self.applied_edits),
            "batches": len(self.batches),
            "total_lines_added": sum(e.lines_added for e in self.applied_edits),
            "total_lines_removed": sum(e.lines_removed for e in self.applied_edits),
            "files_modified": len(set(e.file_path for e in self.applied_edits)),
        }

    async def _generate_edit(
        self,
        content: str,
        instructions: str,
        file_path: str,
    ) -> str:
        """Generate edited content using LLM.

        Args:
            content: Original content.
            instructions: Edit instructions.
            file_path: Path for context.

        Returns:
            Edited content.
        """
        prompt = f"""Edit the following code according to these instructions:

Instructions: {instructions}

File: {file_path}

Original code:
```
{content}
```

Return ONLY the modified code, nothing else."""

        request = LLMRequest(
            messages=[LLMMessage(role="user", content=prompt)],
            system_prompt=self.config.system_prompt,
            temperature=0.3,  # Lower temperature for precise edits
            max_tokens=self.config.max_tokens,
        )

        response = await self.provider.complete(request)

        # Extract code from response (handle markdown code blocks)
        result = response.content.strip()
        if result.startswith("```"):
            lines = result.split("\n")
            # Remove first and last lines (code block markers)
            if len(lines) > 2:
                result = "\n".join(lines[1:-1])

        return result

    async def _analyze_refactor(
        self,
        instructions: str,
        files: list[str],
    ) -> dict[str, Any]:
        """Analyze refactoring scope.

        Args:
            instructions: Refactoring instructions.
            files: Available files.

        Returns:
            Analysis results.
        """
        prompt = f"""Analyze this refactoring request and identify which files need changes:

Instructions: {instructions}

Available files:
{chr(10).join(files[:50])}

Return a JSON object with:
- "affected_files": list of files that need changes
- "change_summary": brief description of changes per file
"""

        request = LLMRequest(
            messages=[LLMMessage(role="user", content=prompt)],
            system_prompt="You are a code analysis assistant. Return valid JSON.",
            temperature=0.3,
            max_tokens=2048,
        )

        response = await self.provider.complete(request)

        # Parse JSON response
        import json

        try:
            content = response.content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
        except json.JSONDecodeError:
            pass

        # Fallback: return first few files
        return {"affected_files": files[:5]}

    async def _handle_edit_request(self, message: str) -> list[EditOperation]:
        """Handle a general edit request."""
        # Ask LLM to parse the request
        prompt = f"""Parse this edit request and extract:
1. File path to edit
2. Edit instructions

Request: {message}

If no file is specified, ask for clarification.
Return the file path and instructions."""

        request = LLMRequest(
            messages=[LLMMessage(role="user", content=prompt)],
            system_prompt="Extract file path and edit instructions from requests.",
            temperature=0.3,
            max_tokens=512,
        )

        response = await self.provider.complete(request)
        await self.add_message("user", message)

        # For now, return empty - would need file path from context
        return []

    async def _handle_replace_request(self, message: str) -> list[EditOperation]:
        """Handle a replace/rename request."""
        # Parse search/replace from message
        return []

    async def _handle_refactor_request(self, message: str) -> list[EditOperation]:
        """Handle a refactor request."""
        batch = await self.refactor(message)
        return batch.operations

    def _create_failed_edit(
        self,
        file_path: str,
        instructions: str,
        error: str,
    ) -> EditOperation:
        """Create a failed edit operation."""
        edit = EditOperation(
            file_path=file_path,
            edit_type=EditType.MODIFY,
            instructions=instructions,
            status=EditStatus.FAILED,
            error=error,
        )
        return edit

    def _format_edit_response(self, edits: list[EditOperation]) -> str:
        """Format edit operations as response."""
        if not edits:
            return "No edits to apply."

        lines = [f"## Edit Preview ({len(edits)} file(s))"]

        for edit in edits:
            status_icon = {
                EditStatus.PENDING: "○",
                EditStatus.PREVIEWED: "◐",
                EditStatus.APPLIED: "●",
                EditStatus.FAILED: "✗",
                EditStatus.SKIPPED: "○",
            }.get(edit.status, "○")

            lines.append(f"\n### {status_icon} {edit.file_path}")
            lines.append(f"Type: {edit.edit_type.value}")

            if edit.has_changes:
                lines.append(
                    f"Changes: +{edit.lines_added} -{edit.lines_removed} lines"
                )
                if edit.diff:
                    lines.append("\n```diff")
                    lines.append(edit.diff[:2000])  # Truncate long diffs
                    lines.append("```")
            else:
                lines.append("No changes needed.")

            if edit.error:
                lines.append(f"Error: {edit.error}")

        return "\n".join(lines)
