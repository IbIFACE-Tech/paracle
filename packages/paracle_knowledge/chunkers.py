"""Document chunking strategies.

This module provides various chunking strategies for different document types:
- TextChunker: Simple text splitting
- MarkdownChunker: Markdown-aware splitting
- CodeChunker: AST-aware code splitting
- SemanticChunker: Semantic boundary detection
"""

from __future__ import annotations

import ast
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from paracle_knowledge.base import Chunk, ChunkMetadata, DocumentType

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class ChunkerConfig:
    """Configuration for chunkers.

    Attributes:
        chunk_size: Target chunk size in characters
        chunk_overlap: Overlap between chunks in characters
        min_chunk_size: Minimum chunk size
        max_chunk_size: Maximum chunk size
        separators: Text separators for splitting
    """

    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    max_chunk_size: int = 3000
    separators: list[str] | None = None


class BaseChunker(ABC):
    """Abstract base class for document chunkers."""

    def __init__(self, config: ChunkerConfig | None = None):
        """Initialize chunker.

        Args:
            config: Chunker configuration
        """
        self.config = config or ChunkerConfig()

    @abstractmethod
    def chunk(
        self,
        content: str,
        document_id: str,
        **kwargs: Any,
    ) -> list[Chunk]:
        """Split content into chunks.

        Args:
            content: Text content to chunk
            document_id: ID of the source document
            **kwargs: Additional arguments

        Returns:
            List of chunks
        """
        pass

    def _create_chunk(
        self,
        content: str,
        document_id: str,
        chunk_index: int,
        start_line: int | None = None,
        end_line: int | None = None,
        start_char: int | None = None,
        end_char: int | None = None,
        **metadata_kwargs: Any,
    ) -> Chunk:
        """Create a chunk with metadata.

        Args:
            content: Chunk content
            document_id: Source document ID
            chunk_index: Index of this chunk
            start_line: Starting line number
            end_line: Ending line number
            start_char: Starting character offset
            end_char: Ending character offset
            **metadata_kwargs: Additional metadata

        Returns:
            Chunk instance
        """
        metadata = ChunkMetadata(
            document_id=document_id,
            chunk_index=chunk_index,
            start_line=start_line,
            end_line=end_line,
            start_char=start_char,
            end_char=end_char,
            **metadata_kwargs,
        )
        return Chunk(content=content, metadata=metadata)


class TextChunker(BaseChunker):
    """Simple text chunker using separators.

    Splits text at natural boundaries (paragraphs, sentences)
    while respecting chunk size limits.
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def chunk(
        self,
        content: str,
        document_id: str,
        **kwargs: Any,
    ) -> list[Chunk]:
        """Split text into chunks."""
        separators = self.config.separators or self.DEFAULT_SEPARATORS
        chunks = self._split_text(content, separators)

        result = []
        char_offset = 0
        line_offset = 1

        for i, chunk_text in enumerate(chunks):
            # Calculate line numbers
            start_line = line_offset
            end_line = start_line + chunk_text.count("\n")
            line_offset = end_line

            # Calculate character offsets
            start_char = char_offset
            end_char = start_char + len(chunk_text)
            char_offset = end_char - self.config.chunk_overlap

            chunk = self._create_chunk(
                content=chunk_text.strip(),
                document_id=document_id,
                chunk_index=i,
                start_line=start_line,
                end_line=end_line,
                start_char=start_char,
                end_char=end_char,
            )
            result.append(chunk)

        return result

    def _split_text(
        self,
        text: str,
        separators: list[str],
    ) -> list[str]:
        """Recursively split text using separators."""
        if not text:
            return []

        # If text is small enough, return as single chunk
        if len(text) <= self.config.chunk_size:
            if len(text) >= self.config.min_chunk_size:
                return [text]
            return []

        # Try each separator
        for separator in separators:
            if separator == "":
                # Last resort: split by character
                return self._split_by_size(text)

            if separator in text:
                splits = text.split(separator)
                chunks = self._merge_splits(splits, separator)
                return chunks

        return [text]

    def _merge_splits(
        self,
        splits: list[str],
        separator: str,
    ) -> list[str]:
        """Merge small splits into chunks of appropriate size."""
        chunks = []
        current_chunk = ""

        for split in splits:
            if not split.strip():
                continue

            test_chunk = current_chunk + separator + split if current_chunk else split

            if len(test_chunk) > self.config.max_chunk_size and current_chunk:
                # Current chunk is full, start new one
                chunks.append(current_chunk)
                current_chunk = split
            elif len(test_chunk) > self.config.chunk_size and current_chunk:
                # Add overlap from previous chunk
                chunks.append(current_chunk)
                # Start new chunk with overlap
                overlap_text = current_chunk[-self.config.chunk_overlap :]
                current_chunk = overlap_text + separator + split
            else:
                current_chunk = test_chunk

        if current_chunk and len(current_chunk) >= self.config.min_chunk_size:
            chunks.append(current_chunk)

        return chunks

    def _split_by_size(self, text: str) -> list[str]:
        """Split text by size when no separators work."""
        chunks = []
        for i in range(
            0, len(text), self.config.chunk_size - self.config.chunk_overlap
        ):
            chunk = text[i : i + self.config.chunk_size]
            if len(chunk) >= self.config.min_chunk_size:
                chunks.append(chunk)
        return chunks


class MarkdownChunker(BaseChunker):
    """Markdown-aware chunker.

    Preserves markdown structure by splitting at headings
    and keeping code blocks intact.
    """

    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```", re.MULTILINE)

    def chunk(
        self,
        content: str,
        document_id: str,
        **kwargs: Any,
    ) -> list[Chunk]:
        """Split markdown into chunks by sections."""
        sections = self._split_by_headings(content)

        result = []
        for i, (section_title, section_content) in enumerate(sections):
            # If section is too large, split further
            if len(section_content) > self.config.max_chunk_size:
                sub_chunks = self._split_large_section(section_content, document_id, i)
                for j, sub_chunk in enumerate(sub_chunks):
                    sub_chunk.metadata.section = section_title
                    sub_chunk.metadata.chunk_index = i * 100 + j
                result.extend(sub_chunks)
            else:
                chunk = self._create_chunk(
                    content=section_content,
                    document_id=document_id,
                    chunk_index=i,
                    section=section_title,
                )
                result.append(chunk)

        return result

    def _split_by_headings(self, content: str) -> list[tuple[str, str]]:
        """Split content by markdown headings."""
        sections = []
        current_title = ""
        current_content = ""

        lines = content.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]
            heading_match = self.HEADING_PATTERN.match(line)

            if heading_match:
                len(heading_match.group(1))
                title = heading_match.group(2)

                # Save previous section
                if current_content.strip():
                    sections.append((current_title, current_content.strip()))

                current_title = title
                current_content = line + "\n"
            else:
                current_content += line + "\n"

            i += 1

        # Save last section
        if current_content.strip():
            sections.append((current_title, current_content.strip()))

        return sections

    def _split_large_section(
        self,
        content: str,
        document_id: str,
        base_index: int,
    ) -> list[Chunk]:
        """Split a large section using text chunker."""
        text_chunker = TextChunker(self.config)
        return text_chunker.chunk(content, document_id)


class CodeChunker(BaseChunker):
    """AST-aware code chunker.

    Splits code at function/class boundaries while preserving
    complete definitions.
    """

    # Supported languages and their patterns
    FUNCTION_PATTERNS = {
        "python": re.compile(
            r"^(async\s+)?def\s+\w+\s*\([^)]*\)\s*(?:->.*?)?:", re.MULTILINE
        ),
        "javascript": re.compile(
            r"^(?:async\s+)?(?:function\s+\w+|(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))",
            re.MULTILINE,
        ),
        "typescript": re.compile(
            r"^(?:async\s+)?(?:function\s+\w+|(?:const|let|var)\s+\w+\s*:\s*.*?=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))",
            re.MULTILINE,
        ),
    }

    CLASS_PATTERNS = {
        "python": re.compile(r"^class\s+\w+(?:\([^)]*\))?:", re.MULTILINE),
        "javascript": re.compile(r"^class\s+\w+(?:\s+extends\s+\w+)?", re.MULTILINE),
        "typescript": re.compile(
            r"^(?:export\s+)?(?:abstract\s+)?class\s+\w+", re.MULTILINE
        ),
    }

    def chunk(
        self,
        content: str,
        document_id: str,
        *,
        language: str = "python",
        **kwargs: Any,
    ) -> list[Chunk]:
        """Split code into chunks by functions/classes."""
        if language == "python":
            return self._chunk_python(content, document_id)
        else:
            return self._chunk_generic(content, document_id, language)

    def _chunk_python(self, content: str, document_id: str) -> list[Chunk]:
        """Chunk Python code using AST parsing."""
        try:
            tree = ast.parse(content)
            return self._extract_python_nodes(tree, content, document_id)
        except SyntaxError:
            logger.warning(
                "Failed to parse Python code, falling back to generic chunker"
            )
            return self._chunk_generic(content, document_id, "python")

    def _extract_python_nodes(
        self,
        tree: ast.AST,
        content: str,
        document_id: str,
    ) -> list[Chunk]:
        """Extract chunks from Python AST."""
        lines = content.split("\n")
        chunks = []
        chunk_index = 0

        # Collect top-level nodes
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                start_line = node.lineno
                end_line = node.end_lineno or start_line

                # Include decorators
                if node.decorator_list:
                    start_line = min(d.lineno for d in node.decorator_list)

                # Extract source
                node_content = "\n".join(lines[start_line - 1 : end_line])

                chunk = self._create_chunk(
                    content=node_content,
                    document_id=document_id,
                    chunk_index=chunk_index,
                    start_line=start_line,
                    end_line=end_line,
                    language="python",
                    custom={"node_type": type(node).__name__, "name": node.name},
                )
                chunks.append(chunk)
                chunk_index += 1

        # If no functions/classes found, use text chunker
        if not chunks:
            text_chunker = TextChunker(self.config)
            chunks = text_chunker.chunk(content, document_id)
            for chunk in chunks:
                chunk.metadata.language = "python"

        return chunks

    def _chunk_generic(
        self,
        content: str,
        document_id: str,
        language: str,
    ) -> list[Chunk]:
        """Generic chunking using regex patterns."""
        func_pattern = self.FUNCTION_PATTERNS.get(language)
        class_pattern = self.CLASS_PATTERNS.get(language)

        if not func_pattern and not class_pattern:
            # Fallback to text chunker
            text_chunker = TextChunker(self.config)
            chunks = text_chunker.chunk(content, document_id)
            for chunk in chunks:
                chunk.metadata.language = language
            return chunks

        # Find all function/class starts
        boundaries = []

        if func_pattern:
            for match in func_pattern.finditer(content):
                boundaries.append(("function", match.start()))

        if class_pattern:
            for match in class_pattern.finditer(content):
                boundaries.append(("class", match.start()))

        # Sort by position
        boundaries.sort(key=lambda x: x[1])

        if not boundaries:
            text_chunker = TextChunker(self.config)
            chunks = text_chunker.chunk(content, document_id)
            for chunk in chunks:
                chunk.metadata.language = language
            return chunks

        # Extract chunks between boundaries
        chunks = []
        for i, (node_type, start) in enumerate(boundaries):
            end = boundaries[i + 1][1] if i + 1 < len(boundaries) else len(content)
            chunk_content = content[start:end].strip()

            if len(chunk_content) >= self.config.min_chunk_size:
                # Calculate line numbers
                start_line = content[:start].count("\n") + 1
                end_line = start_line + chunk_content.count("\n")

                chunk = self._create_chunk(
                    content=chunk_content,
                    document_id=document_id,
                    chunk_index=i,
                    start_line=start_line,
                    end_line=end_line,
                    language=language,
                    custom={"node_type": node_type},
                )
                chunks.append(chunk)

        return chunks


class SemanticChunker(BaseChunker):
    """Semantic chunker using embedding similarity.

    Splits text at semantic boundaries by detecting
    significant changes in embedding similarity.
    """

    def __init__(
        self,
        config: ChunkerConfig | None = None,
        embedding_service: Any = None,
        similarity_threshold: float = 0.5,
    ):
        """Initialize semantic chunker.

        Args:
            config: Chunker configuration
            embedding_service: Service for generating embeddings
            similarity_threshold: Threshold for detecting boundaries
        """
        super().__init__(config)
        self._embedding_service = embedding_service
        self._similarity_threshold = similarity_threshold

    async def chunk_async(
        self,
        content: str,
        document_id: str,
        **kwargs: Any,
    ) -> list[Chunk]:
        """Split text at semantic boundaries (async).

        This method requires embeddings, so it's async.
        """
        if self._embedding_service is None:
            # Fallback to text chunker
            text_chunker = TextChunker(self.config)
            return text_chunker.chunk(content, document_id)

        # Split into sentences
        sentences = self._split_sentences(content)
        if len(sentences) <= 1:
            return [self._create_chunk(content, document_id, 0)]

        # Generate embeddings for sentences
        embeddings = await self._embedding_service.embed(sentences)

        # Find semantic boundaries
        boundaries = self._find_boundaries(embeddings)

        # Create chunks at boundaries
        chunks = []
        start_idx = 0

        for i, end_idx in enumerate(boundaries):
            chunk_text = " ".join(sentences[start_idx : end_idx + 1])

            if len(chunk_text) >= self.config.min_chunk_size:
                chunk = self._create_chunk(
                    content=chunk_text,
                    document_id=document_id,
                    chunk_index=i,
                )
                chunks.append(chunk)

            start_idx = end_idx + 1

        # Add remaining sentences
        if start_idx < len(sentences):
            chunk_text = " ".join(sentences[start_idx:])
            if len(chunk_text) >= self.config.min_chunk_size:
                chunk = self._create_chunk(
                    content=chunk_text,
                    document_id=document_id,
                    chunk_index=len(chunks),
                )
                chunks.append(chunk)

        return chunks

    def chunk(
        self,
        content: str,
        document_id: str,
        **kwargs: Any,
    ) -> list[Chunk]:
        """Sync wrapper - falls back to text chunking."""
        text_chunker = TextChunker(self.config)
        return text_chunker.chunk(content, document_id)

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        pattern = r"(?<=[.!?])\s+"
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]

    def _find_boundaries(self, embeddings: list[list[float]]) -> list[int]:
        """Find semantic boundaries using embedding similarity."""
        boundaries = []

        for i in range(1, len(embeddings)):
            similarity = self._cosine_similarity(embeddings[i - 1], embeddings[i])

            if similarity < self._similarity_threshold:
                boundaries.append(i - 1)

        return boundaries

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)


def get_chunker(
    doc_type: DocumentType,
    config: ChunkerConfig | None = None,
    **kwargs: Any,
) -> BaseChunker:
    """Get appropriate chunker for document type.

    Args:
        doc_type: Type of document
        config: Chunker configuration
        **kwargs: Additional arguments for chunker

    Returns:
        Appropriate chunker instance
    """
    if doc_type == DocumentType.MARKDOWN:
        return MarkdownChunker(config)
    elif doc_type == DocumentType.CODE:
        return CodeChunker(config)
    else:
        return TextChunker(config)
