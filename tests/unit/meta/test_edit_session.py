"""Unit tests for paracle_meta.sessions.edit module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from paracle_meta.sessions.edit import (
    EditBatch,
    EditConfig,
    EditOperation,
    EditSession,
    EditStatus,
    EditType,
)


class TestEditType:
    """Tests for EditType enum."""

    def test_type_values(self):
        """Test edit type enum values."""
        assert EditType.MODIFY.value == "modify"
        assert EditType.INSERT.value == "insert"
        assert EditType.DELETE.value == "delete"
        assert EditType.REPLACE.value == "replace"
        assert EditType.REFACTOR.value == "refactor"
        assert EditType.FORMAT.value == "format"


class TestEditStatus:
    """Tests for EditStatus enum."""

    def test_status_values(self):
        """Test edit status enum values."""
        assert EditStatus.PENDING.value == "pending"
        assert EditStatus.PREVIEWED.value == "previewed"
        assert EditStatus.APPLIED.value == "applied"
        assert EditStatus.REVERTED.value == "reverted"
        assert EditStatus.FAILED.value == "failed"
        assert EditStatus.SKIPPED.value == "skipped"


class TestEditOperation:
    """Tests for EditOperation dataclass."""

    def test_create_operation(self):
        """Test creating an edit operation."""
        op = EditOperation(
            file_path="test.py",
            edit_type=EditType.MODIFY,
            instructions="Add type hints",
        )

        assert op.file_path == "test.py"
        assert op.edit_type == EditType.MODIFY
        assert op.instructions == "Add type hints"
        assert op.status == EditStatus.PENDING
        assert op.id.startswith("edit_")

    def test_has_changes_false_when_same(self):
        """Test has_changes returns False when content is same."""
        op = EditOperation(
            file_path="test.py",
            edit_type=EditType.MODIFY,
            original_content="def foo(): pass",
            new_content="def foo(): pass",
        )

        assert op.has_changes is False

    def test_has_changes_true_when_different(self):
        """Test has_changes returns True when content differs."""
        op = EditOperation(
            file_path="test.py",
            edit_type=EditType.MODIFY,
            original_content="def foo(): pass",
            new_content="def foo() -> None: pass",
        )

        assert op.has_changes is True

    def test_lines_added(self):
        """Test lines added calculation."""
        op = EditOperation(
            file_path="test.py",
            edit_type=EditType.INSERT,
            original_content="line1\nline2",
            new_content="line1\nline2\nline3\nline4",
        )

        assert op.lines_added == 2
        assert op.lines_removed == 0

    def test_lines_removed(self):
        """Test lines removed calculation."""
        op = EditOperation(
            file_path="test.py",
            edit_type=EditType.DELETE,
            original_content="line1\nline2\nline3\nline4",
            new_content="line1\nline2",
        )

        assert op.lines_added == 0
        assert op.lines_removed == 2

    def test_lines_no_changes(self):
        """Test lines calculation with no changes."""
        op = EditOperation(
            file_path="test.py",
            edit_type=EditType.MODIFY,
            original_content="line1\nline2",
            new_content="line1\nline2",
        )

        assert op.lines_added == 0
        assert op.lines_removed == 0

    def test_generate_diff(self):
        """Test diff generation."""
        op = EditOperation(
            file_path="test.py",
            edit_type=EditType.MODIFY,
            original_content="def foo():\n    pass\n",
            new_content="def foo() -> None:\n    pass\n",
        )

        diff = op.generate_diff()

        assert "--- a/test.py" in diff
        assert "+++ b/test.py" in diff
        assert "-def foo():" in diff
        assert "+def foo() -> None:" in diff
        assert op.diff == diff

    def test_to_dict(self):
        """Test conversion to dictionary."""
        op = EditOperation(
            file_path="test.py",
            edit_type=EditType.MODIFY,
            instructions="Add type hints",
            original_content="old",
            new_content="new",
        )
        op.generate_diff()

        result = op.to_dict()

        assert result["file_path"] == "test.py"
        assert result["edit_type"] == "modify"
        assert result["instructions"] == "Add type hints"
        assert result["has_changes"] is True
        assert result["status"] == "pending"
        assert "diff" in result
        assert "created_at" in result


class TestEditBatch:
    """Tests for EditBatch dataclass."""

    def test_create_batch(self):
        """Test creating an edit batch."""
        batch = EditBatch(description="Refactor imports")

        assert batch.description == "Refactor imports"
        assert batch.id.startswith("batch_")
        assert batch.operations == []
        assert batch.status == EditStatus.PENDING

    def test_file_count(self):
        """Test file count calculation."""
        ops = [
            EditOperation(file_path="a.py", edit_type=EditType.MODIFY),
            EditOperation(file_path="b.py", edit_type=EditType.MODIFY),
            EditOperation(file_path="a.py", edit_type=EditType.MODIFY),  # Duplicate
        ]

        batch = EditBatch(description="Test", operations=ops)

        assert batch.file_count == 2

    def test_total_lines(self):
        """Test total lines calculations."""
        ops = [
            EditOperation(
                file_path="a.py",
                edit_type=EditType.INSERT,
                original_content="line1",
                new_content="line1\nline2\nline3",
            ),
            EditOperation(
                file_path="b.py",
                edit_type=EditType.DELETE,
                original_content="line1\nline2\nline3",
                new_content="line1",
            ),
        ]

        batch = EditBatch(description="Test", operations=ops)

        assert batch.total_lines_added == 2
        assert batch.total_lines_removed == 2

    def test_is_complete(self):
        """Test completion status check."""
        ops = [
            EditOperation(file_path="a.py", edit_type=EditType.MODIFY),
            EditOperation(file_path="b.py", edit_type=EditType.MODIFY),
        ]
        ops[0].status = EditStatus.APPLIED
        ops[1].status = EditStatus.SKIPPED

        batch = EditBatch(description="Test", operations=ops)

        assert batch.is_complete is True

    def test_is_not_complete(self):
        """Test incomplete batch."""
        ops = [
            EditOperation(file_path="a.py", edit_type=EditType.MODIFY),
            EditOperation(file_path="b.py", edit_type=EditType.MODIFY),
        ]
        ops[0].status = EditStatus.APPLIED
        ops[1].status = EditStatus.PENDING

        batch = EditBatch(description="Test", operations=ops)

        assert batch.is_complete is False

    def test_to_dict(self):
        """Test conversion to dictionary."""
        op = EditOperation(
            file_path="test.py",
            edit_type=EditType.MODIFY,
            original_content="old",
            new_content="new",
        )

        batch = EditBatch(description="Test batch", operations=[op])

        result = batch.to_dict()

        assert result["description"] == "Test batch"
        assert result["file_count"] == 1
        assert result["operation_count"] == 1
        assert len(result["operations"]) == 1


class TestEditConfig:
    """Tests for EditConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = EditConfig()

        assert config.auto_apply is False
        assert config.create_backups is True
        assert config.backup_suffix == ".bak"
        assert config.preview_context_lines == 3
        assert config.max_file_size_kb == 1024
        assert config.allowed_extensions is None
        assert config.confirm_destructive is True

    def test_custom_values(self):
        """Test custom configuration values."""
        config = EditConfig(
            auto_apply=True,
            create_backups=False,
            preview_context_lines=5,
        )

        assert config.auto_apply is True
        assert config.create_backups is False
        assert config.preview_context_lines == 5

    def test_sets_default_system_prompt(self):
        """Test default system prompt is set."""
        config = EditConfig()

        assert config.system_prompt is not None
        assert "code editor" in config.system_prompt.lower()


class TestEditSession:
    """Tests for EditSession."""

    @pytest.fixture
    def mock_provider(self):
        """Create mock provider."""
        provider = MagicMock()
        provider.name = "mock"
        provider.is_available = True

        async def mock_complete(request):
            response = MagicMock()
            response.content = "def foo() -> None:\n    pass"
            return response

        provider.complete = AsyncMock(side_effect=mock_complete)
        return provider

    @pytest.fixture
    def mock_registry(self):
        """Create mock registry."""
        registry = MagicMock()

        # Mock filesystem capability
        filesystem = MagicMock()

        async def mock_read(path):
            result = MagicMock()
            result.success = True
            result.output = {"content": "def foo():\n    pass\n"}
            return result

        async def mock_write(path, content):
            result = MagicMock()
            result.success = True
            return result

        async def mock_glob(pattern):
            result = MagicMock()
            result.success = True
            result.output = {
                "matches": [
                    {"path": "test.py"},
                    {"path": "main.py"},
                ]
            }
            return result

        async def mock_execute(**kwargs):
            result = MagicMock()
            result.success = True
            return result

        filesystem.read_file = AsyncMock(side_effect=mock_read)
        filesystem.write_file = AsyncMock(side_effect=mock_write)
        filesystem.glob_files = AsyncMock(side_effect=mock_glob)
        filesystem.execute = AsyncMock(side_effect=mock_execute)

        async def mock_get(name):
            if name == "filesystem":
                return filesystem
            return None

        registry.get = AsyncMock(side_effect=mock_get)
        registry.is_initialized = True

        return registry

    @pytest.fixture
    def session(self, mock_provider, mock_registry):
        """Create edit session."""
        return EditSession(mock_provider, mock_registry)

    @pytest.mark.asyncio
    async def test_initialize(self, session):
        """Test session initialization."""
        await session.initialize()

        assert session._filesystem is not None

    @pytest.mark.asyncio
    async def test_edit_file(self, session):
        """Test editing a single file."""
        await session.initialize()

        edit = await session.edit_file("test.py", "Add type hints")

        assert edit.file_path == "test.py"
        assert edit.edit_type == EditType.MODIFY
        assert edit.status == EditStatus.PREVIEWED
        assert edit.has_changes is True
        assert edit in session.pending_edits

    @pytest.mark.asyncio
    async def test_edit_file_with_line_range(self, session):
        """Test editing specific lines."""
        await session.initialize()

        edit = await session.edit_file(
            "test.py",
            "Add type hints",
            line_start=1,
            line_end=2,
        )

        assert edit.line_start == 1
        assert edit.line_end == 2

    @pytest.mark.asyncio
    async def test_insert_code(self, session):
        """Test inserting code."""
        await session.initialize()

        edit = await session.insert_code(
            "test.py",
            "# New comment\n",
            after_line=1,
        )

        assert edit.edit_type == EditType.INSERT
        assert edit.status == EditStatus.PREVIEWED

    @pytest.mark.asyncio
    async def test_delete_lines(self, session):
        """Test deleting lines."""
        await session.initialize()

        edit = await session.delete_lines("test.py", start_line=1, end_line=2)

        assert edit.edit_type == EditType.DELETE
        assert edit.line_start == 1
        assert edit.line_end == 2

    @pytest.mark.asyncio
    async def test_search_replace_single_file(self, session):
        """Test search and replace in single file."""
        await session.initialize()

        edits = await session.search_replace(
            search="foo",
            replace="bar",
            file_path="test.py",
        )

        assert len(edits) == 1
        assert edits[0].edit_type == EditType.REPLACE

    @pytest.mark.asyncio
    async def test_search_replace_pattern(self, session):
        """Test search and replace with glob pattern."""
        await session.initialize()

        edits = await session.search_replace(
            search="foo",
            replace="bar",
            pattern="**/*.py",
        )

        # Should find in both test.py and main.py
        assert len(edits) == 2

    @pytest.mark.asyncio
    async def test_apply_edit(self, session):
        """Test applying an edit."""
        await session.initialize()

        edit = await session.edit_file("test.py", "Add type hints")

        success = await session.apply(edit)

        assert success is True
        assert edit.status == EditStatus.APPLIED
        assert edit.applied_at is not None
        assert edit in session.applied_edits
        assert edit not in session.pending_edits

    @pytest.mark.asyncio
    async def test_apply_already_applied(self, session):
        """Test applying already applied edit."""
        await session.initialize()

        edit = await session.edit_file("test.py", "Add type hints")
        await session.apply(edit)

        # Apply again
        success = await session.apply(edit)

        assert success is True  # Returns True, no-op

    @pytest.mark.asyncio
    async def test_apply_no_changes(self, session, mock_provider):
        """Test applying edit with no changes."""
        await session.initialize()

        # Mock no changes
        async def mock_complete(request):
            response = MagicMock()
            response.content = "def foo():\n    pass"  # Same as original
            return response

        mock_provider.complete = AsyncMock(side_effect=mock_complete)

        edit = await session.edit_file("test.py", "No changes")

        # Manually force no changes for this test
        edit.new_content = edit.original_content

        success = await session.apply(edit)

        assert success is True
        assert edit.status == EditStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_apply_all_pending(self, session):
        """Test applying all pending edits."""
        await session.initialize()

        # Create multiple edits
        await session.edit_file("test.py", "Edit 1")
        await session.edit_file("main.py", "Edit 2")

        assert len(session.pending_edits) == 2

        stats = await session.apply_all()

        assert stats["applied"] == 2
        assert len(session.applied_edits) == 2
        assert len(session.pending_edits) == 0

    @pytest.mark.asyncio
    async def test_apply_batch(self, session):
        """Test applying a batch."""
        await session.initialize()

        batch = await session.refactor("Rename foo to bar")

        stats = await session.apply_all(batch)

        assert stats["applied"] >= 0

    @pytest.mark.asyncio
    async def test_revert_edit(self, session):
        """Test reverting an applied edit."""
        await session.initialize()

        edit = await session.edit_file("test.py", "Add type hints")
        await session.apply(edit)

        success = await session.revert(edit)

        assert success is True
        assert edit.status == EditStatus.REVERTED

    @pytest.mark.asyncio
    async def test_revert_not_applied(self, session):
        """Test reverting non-applied edit fails."""
        await session.initialize()

        edit = await session.edit_file("test.py", "Add type hints")

        success = await session.revert(edit)

        assert success is False

    @pytest.mark.asyncio
    async def test_skip_edit(self, session):
        """Test skipping an edit."""
        await session.initialize()

        edit = await session.edit_file("test.py", "Add type hints")

        await session.skip(edit)

        assert edit.status == EditStatus.SKIPPED
        assert edit not in session.pending_edits

    def test_get_diff_single(self, session):
        """Test getting diff for single edit."""
        edit = EditOperation(
            file_path="test.py",
            edit_type=EditType.MODIFY,
            original_content="old",
            new_content="new",
        )
        edit.generate_diff()
        session.pending_edits.append(edit)

        diff = session.get_diff(edit)

        assert "old" in diff or "-old" in diff

    def test_get_diff_all(self, session):
        """Test getting combined diff."""
        edit1 = EditOperation(
            file_path="a.py",
            edit_type=EditType.MODIFY,
            original_content="old1",
            new_content="new1",
        )
        edit2 = EditOperation(
            file_path="b.py",
            edit_type=EditType.MODIFY,
            original_content="old2",
            new_content="new2",
        )
        edit1.generate_diff()
        edit2.generate_diff()
        session.pending_edits.extend([edit1, edit2])

        diff = session.get_diff()

        assert "a.py" in diff
        assert "b.py" in diff

    def test_get_summary(self, session):
        """Test getting session summary."""
        session.applied_edits = [
            EditOperation(
                file_path="a.py",
                edit_type=EditType.MODIFY,
                original_content="line1",
                new_content="line1\nline2",
            ),
            EditOperation(
                file_path="b.py",
                edit_type=EditType.DELETE,
                original_content="line1\nline2",
                new_content="line1",
            ),
        ]

        summary = session.get_summary()

        assert summary["applied_edits"] == 2
        assert summary["files_modified"] == 2
        assert summary["total_lines_added"] == 1
        assert summary["total_lines_removed"] == 1

    @pytest.mark.asyncio
    async def test_auto_apply(self, mock_provider, mock_registry):
        """Test auto-apply configuration."""
        config = EditConfig(auto_apply=True)
        session = EditSession(mock_provider, mock_registry, config)
        await session.initialize()

        edit = await session.edit_file("test.py", "Add type hints")

        # Should be auto-applied
        assert edit.status == EditStatus.APPLIED

    @pytest.mark.asyncio
    async def test_refactor(self, session):
        """Test refactoring across files."""
        await session.initialize()

        batch = await session.refactor(
            instructions="Rename 'foo' to 'bar'",
            pattern="**/*.py",
        )

        assert batch.description == "Rename 'foo' to 'bar'"
        assert batch.id in session.batches

    @pytest.mark.asyncio
    async def test_send_edit_request(self, session):
        """Test sending a general edit request."""
        await session.initialize()

        response = await session.send("Add type hints to main.py")

        assert response is not None
        assert response.role == "assistant"

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_provider, mock_registry):
        """Test using session as context manager."""
        async with EditSession(mock_provider, mock_registry) as session:
            assert session._filesystem is not None

    @pytest.mark.asyncio
    async def test_failed_file_read(self, session):
        """Test handling failed file read."""
        await session.initialize()

        # Mock failed read
        async def mock_read_fail(path):
            result = MagicMock()
            result.success = False
            result.error = "File not found"
            return result

        session._filesystem.read_file = AsyncMock(side_effect=mock_read_fail)

        edit = await session.edit_file("nonexistent.py", "Edit")

        assert edit.status == EditStatus.FAILED
        assert "Cannot read file" in edit.error


class TestEditSessionFormatting:
    """Tests for edit session formatting."""

    def test_format_edit_response_empty(self):
        """Test formatting empty edits."""
        session = EditSession(MagicMock(), MagicMock())

        response = session._format_edit_response([])

        assert "No edits" in response

    def test_format_edit_response_with_changes(self):
        """Test formatting edits with changes."""
        session = EditSession(MagicMock(), MagicMock())

        edit = EditOperation(
            file_path="test.py",
            edit_type=EditType.MODIFY,
            original_content="old",
            new_content="new",
        )
        edit.generate_diff()
        edit.status = EditStatus.PREVIEWED

        response = session._format_edit_response([edit])

        assert "test.py" in response
        assert "modify" in response
        assert "+1" in response or "lines" in response.lower()
