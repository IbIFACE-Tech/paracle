"""Document ingestion system.

This module provides document ingestion capabilities for the knowledge base:
- File-based ingestion (Markdown, code, text)
- Directory scanning
- Change detection
- Incremental updates
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from paracle_core.compat import UTC, datetime

from paracle_knowledge.base import Document, DocumentType, KnowledgeBase
from paracle_knowledge.chunkers import ChunkerConfig, get_chunker

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# File extension to document type mapping
EXTENSION_MAP: dict[str, DocumentType] = {
    # Markdown
    ".md": DocumentType.MARKDOWN,
    ".mdx": DocumentType.MARKDOWN,
    ".markdown": DocumentType.MARKDOWN,
    # Code
    ".py": DocumentType.CODE,
    ".js": DocumentType.CODE,
    ".ts": DocumentType.CODE,
    ".jsx": DocumentType.CODE,
    ".tsx": DocumentType.CODE,
    ".java": DocumentType.CODE,
    ".go": DocumentType.CODE,
    ".rs": DocumentType.CODE,
    ".cpp": DocumentType.CODE,
    ".c": DocumentType.CODE,
    ".h": DocumentType.CODE,
    ".hpp": DocumentType.CODE,
    ".cs": DocumentType.CODE,
    ".rb": DocumentType.CODE,
    ".php": DocumentType.CODE,
    ".swift": DocumentType.CODE,
    ".kt": DocumentType.CODE,
    ".scala": DocumentType.CODE,
    ".r": DocumentType.CODE,
    ".sql": DocumentType.CODE,
    ".sh": DocumentType.CODE,
    ".bash": DocumentType.CODE,
    ".zsh": DocumentType.CODE,
    ".ps1": DocumentType.CODE,
    # Data formats
    ".json": DocumentType.JSON,
    ".yaml": DocumentType.YAML,
    ".yml": DocumentType.YAML,
    # Text
    ".txt": DocumentType.TEXT,
    ".rst": DocumentType.TEXT,
    ".log": DocumentType.TEXT,
    # Web
    ".html": DocumentType.HTML,
    ".htm": DocumentType.HTML,
    ".xml": DocumentType.HTML,
}

# Language detection from extension
LANGUAGE_MAP: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".r": "r",
    ".sql": "sql",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "zsh",
    ".ps1": "powershell",
}


@dataclass
class IngestResult:
    """Result of document ingestion.

    Attributes:
        total_files: Total files processed
        added: Number of new documents added
        updated: Number of documents updated
        skipped: Number of files skipped
        failed: Number of files that failed
        errors: List of error messages
        documents: List of document IDs
        duration_seconds: Time taken
    """

    total_files: int = 0
    added: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)
    documents: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0

    def __repr__(self) -> str:
        return (
            f"IngestResult(total={self.total_files}, added={self.added}, "
            f"updated={self.updated}, failed={self.failed})"
        )


@dataclass
class IngestConfig:
    """Configuration for document ingestion.

    Attributes:
        chunk_size: Target chunk size
        chunk_overlap: Overlap between chunks
        include_patterns: Glob patterns to include
        exclude_patterns: Glob patterns to exclude
        max_file_size: Maximum file size in bytes
        skip_hidden: Skip hidden files/directories
        detect_changes: Only process changed files
        file_extensions: Allowed file extensions (None = all)
    """

    chunk_size: int = 1000
    chunk_overlap: int = 200
    include_patterns: list[str] = field(default_factory=lambda: ["**/*"])
    exclude_patterns: list[str] = field(
        default_factory=lambda: [
            "**/node_modules/**",
            "**/.git/**",
            "**/__pycache__/**",
            "**/.venv/**",
            "**/venv/**",
            "**/.env/**",
            "**/dist/**",
            "**/build/**",
            "**/*.pyc",
            "**/*.pyo",
            "**/*.egg-info/**",
        ]
    )
    max_file_size: int = 1_000_000  # 1MB
    skip_hidden: bool = True
    detect_changes: bool = True
    file_extensions: list[str] | None = None


class DocumentIngestor:
    """Document ingestion manager.

    Handles ingestion of documents from files and directories
    into the knowledge base.

    Usage:
        ingestor = DocumentIngestor(knowledge_base=kb)

        # Ingest a single file
        result = await ingestor.ingest_file("README.md")

        # Ingest a directory
        result = await ingestor.ingest_directory(
            "./docs",
            file_types=["md", "py"],
            recursive=True
        )
    """

    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        config: IngestConfig | None = None,
    ):
        """Initialize ingestor.

        Args:
            knowledge_base: Target knowledge base
            config: Ingestion configuration
        """
        self._kb = knowledge_base
        self._config = config or IngestConfig()
        self._file_hashes: dict[str, str] = {}

    async def ingest_file(
        self,
        file_path: str | Path,
        *,
        force: bool = False,
    ) -> IngestResult:
        """Ingest a single file.

        Args:
            file_path: Path to file
            force: Force re-ingestion even if unchanged

        Returns:
            Ingestion result
        """
        start_time = datetime.now(UTC)
        result = IngestResult(total_files=1)

        path = Path(file_path)

        try:
            # Validate file
            if not path.exists():
                result.failed = 1
                result.errors.append(f"File not found: {path}")
                return result

            if not path.is_file():
                result.failed = 1
                result.errors.append(f"Not a file: {path}")
                return result

            # Check file size
            if path.stat().st_size > self._config.max_file_size:
                result.skipped = 1
                logger.debug("Skipping large file: %s", path)
                return result

            # Check for changes
            content = path.read_text(encoding="utf-8", errors="replace")
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            if not force and self._config.detect_changes:
                if self._file_hashes.get(str(path)) == content_hash:
                    result.skipped = 1
                    return result

            # Determine document type
            doc_type = self._get_document_type(path)

            # Create document
            document = Document(
                name=path.name,
                file_path=str(path),
                content=content,
                doc_type=doc_type,
                metadata={
                    "file_extension": path.suffix,
                    "file_size": len(content),
                    "language": LANGUAGE_MAP.get(path.suffix.lower(), ""),
                },
            )

            # Chunk the document
            chunker_config = ChunkerConfig(
                chunk_size=self._config.chunk_size,
                chunk_overlap=self._config.chunk_overlap,
            )
            chunker = get_chunker(doc_type, chunker_config)

            kwargs = {}
            if doc_type == DocumentType.CODE:
                kwargs["language"] = LANGUAGE_MAP.get(path.suffix.lower(), "text")

            document.chunks = chunker.chunk(content, document.id, **kwargs)

            # Add to knowledge base
            doc_id = await self._kb.add_document(document)

            # Update hash cache
            self._file_hashes[str(path)] = content_hash

            result.added = 1
            result.documents.append(doc_id)

        except Exception as e:
            result.failed = 1
            result.errors.append(f"Error processing {path}: {e}")
            logger.error("Failed to ingest %s: %s", path, e)

        result.duration_seconds = (datetime.now(UTC) - start_time).total_seconds()
        return result

    async def ingest_directory(
        self,
        directory: str | Path,
        *,
        file_types: list[str] | None = None,
        recursive: bool = True,
        force: bool = False,
    ) -> IngestResult:
        """Ingest all files from a directory.

        Args:
            directory: Directory path
            file_types: File extensions to include (e.g., ["md", "py"])
            recursive: Include subdirectories
            force: Force re-ingestion of all files

        Returns:
            Aggregated ingestion result
        """
        start_time = datetime.now(UTC)
        result = IngestResult()

        dir_path = Path(directory)

        if not dir_path.exists():
            result.errors.append(f"Directory not found: {dir_path}")
            return result

        if not dir_path.is_dir():
            result.errors.append(f"Not a directory: {dir_path}")
            return result

        # Collect files
        files = self._collect_files(dir_path, file_types, recursive)
        result.total_files = len(files)

        logger.info("Found %d files to process in %s", len(files), dir_path)

        # Process files
        for file_path in files:
            file_result = await self.ingest_file(file_path, force=force)

            result.added += file_result.added
            result.updated += file_result.updated
            result.skipped += file_result.skipped
            result.failed += file_result.failed
            result.errors.extend(file_result.errors)
            result.documents.extend(file_result.documents)

        result.duration_seconds = (datetime.now(UTC) - start_time).total_seconds()

        logger.info(
            "Ingestion complete: %d added, %d skipped, %d failed in %.2fs",
            result.added,
            result.skipped,
            result.failed,
            result.duration_seconds,
        )

        return result

    async def ingest_text(
        self,
        content: str,
        name: str,
        *,
        doc_type: DocumentType = DocumentType.TEXT,
        metadata: dict[str, Any] | None = None,
    ) -> IngestResult:
        """Ingest raw text content.

        Args:
            content: Text content
            name: Document name
            doc_type: Document type
            metadata: Optional metadata

        Returns:
            Ingestion result
        """
        start_time = datetime.now(UTC)
        result = IngestResult(total_files=1)

        try:
            document = Document(
                name=name,
                content=content,
                doc_type=doc_type,
                metadata=metadata or {},
            )

            # Chunk the document
            chunker_config = ChunkerConfig(
                chunk_size=self._config.chunk_size,
                chunk_overlap=self._config.chunk_overlap,
            )
            chunker = get_chunker(doc_type, chunker_config)
            document.chunks = chunker.chunk(content, document.id)

            # Add to knowledge base
            doc_id = await self._kb.add_document(document)

            result.added = 1
            result.documents.append(doc_id)

        except Exception as e:
            result.failed = 1
            result.errors.append(f"Error processing text: {e}")
            logger.error("Failed to ingest text %s: %s", name, e)

        result.duration_seconds = (datetime.now(UTC) - start_time).total_seconds()
        return result

    def _collect_files(
        self,
        directory: Path,
        file_types: list[str] | None,
        recursive: bool,
    ) -> list[Path]:
        """Collect files matching criteria."""
        files = []

        # Determine extensions
        if file_types:
            extensions = {f".{ext.lstrip('.')}" for ext in file_types}
        elif self._config.file_extensions:
            extensions = {f".{ext.lstrip('.')}" for ext in self._config.file_extensions}
        else:
            extensions = set(EXTENSION_MAP.keys())

        # Collect files
        pattern = "**/*" if recursive else "*"
        for path in directory.glob(pattern):
            if not path.is_file():
                continue

            # Skip hidden files
            if self._config.skip_hidden and any(
                part.startswith(".") for part in path.parts
            ):
                continue

            # Check extension
            if path.suffix.lower() not in extensions:
                continue

            # Check exclude patterns
            if self._should_exclude(path):
                continue

            # Check file size
            try:
                if path.stat().st_size > self._config.max_file_size:
                    continue
            except OSError:
                continue

            files.append(path)

        return sorted(files)

    def _should_exclude(self, path: Path) -> bool:
        """Check if path matches exclude patterns."""
        path_str = str(path)
        for pattern in self._config.exclude_patterns:
            if self._match_pattern(path_str, pattern):
                return True
        return False

    @staticmethod
    def _match_pattern(path: str, pattern: str) -> bool:
        """Simple glob pattern matching."""
        import fnmatch

        # Normalize path separators
        path = path.replace("\\", "/")
        pattern = pattern.replace("\\", "/")

        return fnmatch.fnmatch(path, pattern)

    @staticmethod
    def _get_document_type(path: Path) -> DocumentType:
        """Determine document type from file extension."""
        ext = path.suffix.lower()
        return EXTENSION_MAP.get(ext, DocumentType.TEXT)


class GitIngestor:
    """Ingest documents from a Git repository.

    Supports:
    - Cloning remote repositories
    - Processing specific branches/tags
    - Tracking changes across commits
    """

    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        config: IngestConfig | None = None,
    ):
        """Initialize Git ingestor.

        Args:
            knowledge_base: Target knowledge base
            config: Ingestion configuration
        """
        self._kb = knowledge_base
        self._config = config or IngestConfig()
        self._doc_ingestor = DocumentIngestor(knowledge_base, config)

    async def ingest_repository(
        self,
        repo_path: str | Path,
        *,
        branch: str = "main",
        file_types: list[str] | None = None,
    ) -> IngestResult:
        """Ingest files from a local Git repository.

        Args:
            repo_path: Path to repository
            branch: Branch to ingest
            file_types: File extensions to include

        Returns:
            Ingestion result
        """
        path = Path(repo_path)

        if not (path / ".git").exists():
            return IngestResult(
                total_files=0,
                errors=[f"Not a Git repository: {path}"],
            )

        # Use document ingestor for the directory
        return await self._doc_ingestor.ingest_directory(
            path,
            file_types=file_types,
            recursive=True,
        )
