"""Tests for document chunkers."""

from paracle_knowledge.base import DocumentType
from paracle_knowledge.chunkers import (
    ChunkerConfig,
    CodeChunker,
    MarkdownChunker,
    TextChunker,
    get_chunker,
)


class TestTextChunker:
    """Tests for TextChunker."""

    def test_chunk_simple_text(self) -> None:
        """Test chunking simple text."""
        config = ChunkerConfig(chunk_size=100, chunk_overlap=20, min_chunk_size=10)
        chunker = TextChunker(config)

        content = "This is a simple test. " * 10
        chunks = chunker.chunk(content, "doc1")

        assert len(chunks) >= 1
        assert all(c.content for c in chunks)
        assert all(c.metadata.document_id == "doc1" for c in chunks)

    def test_chunk_with_paragraphs(self) -> None:
        """Test chunking text with paragraphs."""
        config = ChunkerConfig(chunk_size=200, min_chunk_size=10)
        chunker = TextChunker(config)

        content = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        chunks = chunker.chunk(content, "doc1")

        assert len(chunks) >= 1

    def test_chunk_preserves_content(self) -> None:
        """Test that chunking preserves all content."""
        config = ChunkerConfig(chunk_size=50, chunk_overlap=0, min_chunk_size=5)
        chunker = TextChunker(config)

        content = "Hello world. This is a test."
        chunks = chunker.chunk(content, "doc1")

        # All content should be in chunks
        combined = " ".join(c.content for c in chunks)
        assert "Hello" in combined
        assert "test" in combined

    def test_empty_content(self) -> None:
        """Test chunking empty content."""
        chunker = TextChunker()
        chunks = chunker.chunk("", "doc1")
        assert chunks == []

    def test_small_content(self) -> None:
        """Test chunking content smaller than min_chunk_size."""
        config = ChunkerConfig(min_chunk_size=100)
        chunker = TextChunker(config)

        content = "Small"
        chunks = chunker.chunk(content, "doc1")
        # Content smaller than min_chunk_size should be empty
        assert len(chunks) == 0


class TestMarkdownChunker:
    """Tests for MarkdownChunker."""

    def test_chunk_by_headings(self) -> None:
        """Test chunking markdown by headings."""
        chunker = MarkdownChunker()

        content = """# Introduction

This is the introduction.

## Section One

Content of section one.

## Section Two

Content of section two.
"""
        chunks = chunker.chunk(content, "doc1")

        assert len(chunks) >= 2
        # Check sections are captured
        sections = [c.metadata.section for c in chunks]
        assert any("Introduction" in (s or "") for s in sections)

    def test_chunk_preserves_code_blocks(self) -> None:
        """Test that code blocks are preserved."""
        chunker = MarkdownChunker()

        content = """# Code Example

```python
def hello():
    print("Hello")
```

More text here.
"""
        chunks = chunker.chunk(content, "doc1")

        # Code block should be in one of the chunks
        all_content = "\n".join(c.content for c in chunks)
        assert "def hello" in all_content
        assert 'print("Hello")' in all_content

    def test_no_headings(self) -> None:
        """Test chunking markdown without headings."""
        chunker = MarkdownChunker()

        content = "Just some plain text without any headings."
        chunks = chunker.chunk(content, "doc1")

        assert len(chunks) >= 1


class TestCodeChunker:
    """Tests for CodeChunker."""

    def test_chunk_python_functions(self) -> None:
        """Test chunking Python code by functions."""
        chunker = CodeChunker()

        content = '''
def hello():
    """Say hello."""
    print("Hello")

def goodbye():
    """Say goodbye."""
    print("Goodbye")

class MyClass:
    def method(self):
        pass
'''
        chunks = chunker.chunk(content, "doc1", language="python")

        assert len(chunks) >= 2
        # Check functions are captured
        contents = [c.content for c in chunks]
        assert any("def hello" in c for c in contents)
        assert any("def goodbye" in c for c in contents)

    def test_chunk_with_decorators(self) -> None:
        """Test that decorators are included with functions."""
        chunker = CodeChunker()

        content = """
@decorator
def decorated_function():
    pass
"""
        chunks = chunker.chunk(content, "doc1", language="python")

        assert len(chunks) >= 1
        # Decorator should be included
        assert "@decorator" in chunks[0].content

    def test_chunk_python_class(self) -> None:
        """Test chunking Python class."""
        chunker = CodeChunker()

        content = '''
class MyClass:
    """A test class."""

    def __init__(self):
        self.value = 0

    def method(self):
        return self.value
'''
        chunks = chunker.chunk(content, "doc1", language="python")

        # Class should be captured
        all_content = "\n".join(c.content for c in chunks)
        assert "class MyClass" in all_content

    def test_chunk_invalid_python(self) -> None:
        """Test chunking invalid Python (falls back to generic)."""
        config = ChunkerConfig(min_chunk_size=5)
        chunker = CodeChunker(config)

        content = "def broken( invalid syntax here"
        chunks = chunker.chunk(content, "doc1", language="python")

        # Should not raise, falls back to generic chunking
        assert isinstance(chunks, list)

    def test_chunk_javascript(self) -> None:
        """Test chunking JavaScript code."""
        config = ChunkerConfig(min_chunk_size=10)
        chunker = CodeChunker(config)

        content = """
function hello() {
    console.log("Hello");
}

const goodbye = () => {
    console.log("Goodbye");
}
"""
        chunks = chunker.chunk(content, "doc1", language="javascript")

        # Should find functions
        assert len(chunks) >= 1


class TestGetChunker:
    """Tests for get_chunker factory."""

    def test_get_markdown_chunker(self) -> None:
        """Test getting markdown chunker."""
        chunker = get_chunker(DocumentType.MARKDOWN)
        assert isinstance(chunker, MarkdownChunker)

    def test_get_code_chunker(self) -> None:
        """Test getting code chunker."""
        chunker = get_chunker(DocumentType.CODE)
        assert isinstance(chunker, CodeChunker)

    def test_get_text_chunker(self) -> None:
        """Test getting text chunker for unknown type."""
        chunker = get_chunker(DocumentType.TEXT)
        assert isinstance(chunker, TextChunker)

    def test_get_chunker_with_config(self) -> None:
        """Test getting chunker with custom config."""
        config = ChunkerConfig(chunk_size=500)
        chunker = get_chunker(DocumentType.TEXT, config)

        assert chunker.config.chunk_size == 500
