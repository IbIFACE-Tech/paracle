# Knowledge Engine Guide

This guide covers the `paracle_knowledge` package for RAG (Retrieval Augmented Generation) capabilities.

## Overview

The Knowledge Engine provides:

- **Document Ingestion** - Import files, directories, and git repositories
- **Smart Chunking** - Text, Markdown, Code (AST-aware), and Semantic chunking
- **Vector Search** - Similarity-based retrieval with filtering
- **Reranking** - Cross-encoder, LLM, and ensemble reranking
- **RAG Engine** - Query interface with source attribution

## Quick Start

```python
from paracle_knowledge import (
    KnowledgeBase,
    RAGEngine,
    RAGConfig,
    DocumentIngestor,
)
from paracle_vector import ChromaStore, EmbeddingService

# Initialize components
store = ChromaStore(persist_dir=".paracle/vectors")
embeddings = EmbeddingService()
kb = KnowledgeBase(store, embeddings)

# Ingest documents
ingestor = DocumentIngestor(kb)
result = await ingestor.ingest_directory("./docs")
print(f"Ingested {result.documents_processed} documents")

# Create RAG engine
rag = RAGEngine(kb)

# Query
response = await rag.query("How do I create an agent?")
print(response.context)

for source in response.sources:
    print(f"- {source.document_name}:{source.line_start}")
```

## Document Chunking

### Text Chunker

Best for plain text with paragraph or sentence boundaries.

```python
from paracle_knowledge import TextChunker

chunker = TextChunker(
    chunk_size=500,      # Target characters per chunk
    chunk_overlap=50,    # Overlap between chunks
    separators=["\n\n", "\n", ". ", " "]  # Split priority
)

chunks = chunker.chunk(content, document_id="doc-1")
```

### Markdown Chunker

Splits at headings while preserving structure.

```python
from paracle_knowledge import MarkdownChunker

chunker = MarkdownChunker(
    chunk_size=1000,
    min_heading_level=2,  # Split at ## and below
    preserve_code_blocks=True
)

chunks = chunker.chunk(markdown_content, document_id="readme")
```

### Code Chunker (AST-Aware)

Intelligently splits code at function/class boundaries.

```python
from paracle_knowledge import CodeChunker

chunker = CodeChunker(language="python")

# Extracts functions and classes as separate chunks
chunks = chunker.chunk(python_code, document_id="main.py")

for chunk in chunks:
    print(f"{chunk.metadata.chunk_type}: {chunk.metadata.start_line}-{chunk.metadata.end_line}")
    # Output: function: 1-15
    # Output: class: 17-45
```

Supported languages:
- **Python** - Full AST parsing (functions, classes, methods)
- **JavaScript/TypeScript** - Regex-based (functions, classes, arrow functions)
- **Other** - Falls back to text chunking

### Semantic Chunker

Uses embeddings to detect semantic boundaries.

```python
from paracle_knowledge import SemanticChunker

chunker = SemanticChunker(
    embedding_service=embeddings,
    similarity_threshold=0.5,  # Split when similarity drops
    min_chunk_size=100,
    max_chunk_size=1000
)

# Groups semantically related sentences
chunks = await chunker.chunk_async(content, document_id="article")
```

### Automatic Chunker Selection

```python
from paracle_knowledge.chunkers import get_chunker
from paracle_knowledge import DocumentType

# Automatically selects appropriate chunker
chunker = get_chunker(DocumentType.CODE, language="python")
chunker = get_chunker(DocumentType.MARKDOWN)
chunker = get_chunker(DocumentType.TEXT)
```

## Document Ingestion

### Single File

```python
from paracle_knowledge import DocumentIngestor, IngestConfig

ingestor = DocumentIngestor(knowledge_base)

config = IngestConfig(
    chunk_size=500,
    chunk_overlap=50,
    include_patterns=["*.py", "*.md"],
    exclude_patterns=["*_test.py", "*.pyc"]
)

result = await ingestor.ingest_file("src/main.py", config=config)
print(f"Created {result.chunks_created} chunks")
```

### Directory

```python
result = await ingestor.ingest_directory(
    "src/",
    recursive=True,
    config=config
)

print(f"Documents: {result.documents_processed}")
print(f"Chunks: {result.chunks_created}")
print(f"Errors: {len(result.errors)}")
```

### Git Repository

```python
from paracle_knowledge import GitIngestor

git_ingestor = GitIngestor(knowledge_base)

result = await git_ingestor.ingest_repository(
    "https://github.com/user/repo",
    branch="main",
    include_patterns=["*.py", "*.md"]
)
```

### Supported File Types

| Extension | Type | Chunker |
|-----------|------|---------|
| `.py` | Code | CodeChunker (AST) |
| `.js`, `.ts`, `.tsx` | Code | CodeChunker (regex) |
| `.java`, `.go`, `.rs` | Code | CodeChunker (regex) |
| `.md`, `.markdown` | Markdown | MarkdownChunker |
| `.txt`, `.log` | Text | TextChunker |
| `.json`, `.yaml`, `.toml` | Config | TextChunker |

## RAG Engine

### Basic Query

```python
from paracle_knowledge import RAGEngine, RAGConfig

config = RAGConfig(
    retrieval_top_k=20,       # Initial retrieval count
    final_top_k=5,            # After reranking
    min_relevance_score=0.3,  # Filter threshold
    include_sources=True,     # Include source attribution
    enable_reranking=True     # Use reranker
)

rag = RAGEngine(knowledge_base, config=config)

response = await rag.query("How do agents work?")

print(f"Context: {response.context}")
print(f"Confidence: {response.confidence:.2f}")
print(f"Sources: {len(response.sources)}")
```

### With Context Filters

```python
from paracle_knowledge import RAGContext

context = RAGContext(
    filters={"language": "python", "type": "function"},
    namespace="codebase",
    retrieval_top_k=10  # Override config
)

response = await rag.query(
    "How to handle authentication?",
    context=context
)
```

### Multi-Query

```python
questions = [
    "What is an agent?",
    "How do workflows work?",
    "What tools are available?"
]

responses = await rag.multi_query(questions)

for q, r in zip(questions, responses):
    print(f"Q: {q}")
    print(f"A: {r.context[:200]}...")
```

### RAG Response

```python
response = await rag.query("...")

# Response fields
response.context      # str - Combined context from chunks
response.query        # str - Original query
response.chunks       # list[Chunk] - Retrieved chunks
response.sources      # list[Source] - Source attribution
response.confidence   # float - Confidence score (0-1)
response.retrieval_time_ms  # int - Retrieval duration

# Format with sources
formatted = response.format_context_with_sources()
# Output:
# [1] From agents.py (lines 10-25):
# def create_agent(name: str) -> Agent:
#     ...
#
# [2] From workflows.md:
# ## Agent Creation
# ...
```

## Reranking

### Cross-Encoder Reranker

Uses sentence-transformers for accurate reranking.

```python
from paracle_knowledge import CrossEncoderReranker

reranker = CrossEncoderReranker(
    model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"
)

# Rerank chunks based on query relevance
reranked = await reranker.rerank(query, chunks, top_k=5)
```

### Ensemble Reranker

Combines multiple reranking strategies.

```python
from paracle_knowledge.reranker import (
    EnsembleReranker,
    CrossEncoderReranker,
    RecencyReranker
)

reranker = EnsembleReranker(
    rerankers=[
        (CrossEncoderReranker(), 0.7),   # 70% weight
        (RecencyReranker(), 0.3)          # 30% weight
    ]
)

reranked = await reranker.rerank(query, chunks, top_k=5)
```

### Custom Reranker

```python
from paracle_knowledge import Reranker, Chunk

class MyReranker(Reranker):
    async def rerank(
        self,
        query: str,
        chunks: list[Chunk],
        top_k: int = 5
    ) -> list[Chunk]:
        # Custom scoring logic
        scored = [(chunk, self._score(query, chunk)) for chunk in chunks]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [chunk for chunk, _ in scored[:top_k]]
```

## Knowledge Base

### Adding Documents

```python
from paracle_knowledge import Document, KnowledgeBase

kb = KnowledgeBase(store, embeddings)

# Add document
doc = Document(
    id="doc-1",
    name="readme.md",
    content="# My Project\n...",
    doc_type=DocumentType.MARKDOWN,
    metadata={"project": "paracle"}
)

await kb.add_document(doc)
```

### Searching

```python
# Basic search
results = await kb.search("authentication", top_k=10)

# With filters
results = await kb.search(
    "authentication",
    top_k=10,
    filters={"language": "python"}
)

for chunk, score in results:
    print(f"{score:.3f}: {chunk.content[:100]}")
```

### Statistics

```python
stats = await kb.get_stats()
print(f"Documents: {stats['document_count']}")
print(f"Chunks: {stats['chunk_count']}")
print(f"Collections: {stats['collections']}")
```

## RAG Chain (Multi-Step)

For complex queries requiring multiple retrieval steps.

```python
from paracle_knowledge.rag import RAGChain

chain = RAGChain(knowledge_base)

# Step 1: Find relevant concepts
chain.add_step("concepts", query="What concepts relate to {question}?")

# Step 2: Find implementation details
chain.add_step(
    "implementation",
    query="How is {concepts.answer} implemented?",
    depends_on=["concepts"]
)

# Execute chain
result = await chain.execute(question="How do agents communicate?")
print(result["implementation"].context)
```

## Configuration

### RAGConfig Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `retrieval_top_k` | int | 20 | Initial retrieval count |
| `final_top_k` | int | 5 | Final results after reranking |
| `min_relevance_score` | float | 0.3 | Minimum similarity score |
| `include_sources` | bool | True | Include source attribution |
| `enable_reranking` | bool | True | Use reranker |
| `enable_query_expansion` | bool | False | Expand query with synonyms |

### IngestConfig Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `chunk_size` | int | 500 | Target chunk size |
| `chunk_overlap` | int | 50 | Overlap between chunks |
| `include_patterns` | list | ["*"] | File patterns to include |
| `exclude_patterns` | list | [] | File patterns to exclude |
| `detect_changes` | bool | True | Skip unchanged files |

## Best Practices

### 1. Choose Appropriate Chunk Size

```python
# Code: Smaller chunks (individual functions)
code_config = IngestConfig(chunk_size=300)

# Documentation: Larger chunks (sections)
doc_config = IngestConfig(chunk_size=1000)
```

### 2. Use Metadata for Filtering

```python
# Add metadata during ingestion
doc = Document(
    ...,
    metadata={
        "project": "paracle",
        "module": "agents",
        "version": "1.0"
    }
)

# Filter during search
results = await kb.search(
    query,
    filters={"module": "agents"}
)
```

### 3. Tune Reranking

```python
# For code search: Higher retrieval, aggressive reranking
config = RAGConfig(
    retrieval_top_k=50,   # Cast wide net
    final_top_k=3,        # Narrow to best
    enable_reranking=True
)

# For documentation: More context
config = RAGConfig(
    retrieval_top_k=20,
    final_top_k=10,       # More results
    enable_reranking=True
)
```

### 4. Handle Sources

```python
response = await rag.query("...")

# Always show sources for transparency
for source in response.sources:
    print(f"Source: {source.document_name}")
    if source.line_start:
        print(f"Lines: {source.line_start}-{source.line_end}")
    print(f"Relevance: {source.score:.2f}")
```

## Installation

```bash
# Basic knowledge engine
pip install paracle

# With vector storage (ChromaDB)
pip install paracle[vector]

# With reranking (sentence-transformers)
pip install sentence-transformers

# Full installation
pip install paracle[all]
```

## API Reference

### Document

| Field | Type | Description |
|-------|------|-------------|
| id | str | Unique identifier |
| name | str | Document name |
| content | str | Full content |
| doc_type | DocumentType | TEXT, MARKDOWN, CODE, etc. |
| metadata | dict | Custom metadata |
| file_path | str | Optional | Source file path |
| language | str | Optional | Programming language |

### Chunk

| Field | Type | Description |
|-------|------|-------------|
| id | str | Unique identifier |
| document_id | str | Parent document ID |
| content | str | Chunk content |
| metadata | ChunkMetadata | Chunk metadata |
| embedding | list[float] | Optional | Vector embedding |

### ChunkMetadata

| Field | Type | Description |
|-------|------|-------------|
| start_line | int | Start line in document |
| end_line | int | End line in document |
| chunk_type | str | function, class, section, etc. |
| language | str | Programming language |
| heading | str | Section heading (markdown) |

### Source

| Field | Type | Description |
|-------|------|-------------|
| document_id | str | Document ID |
| document_name | str | Document name |
| file_path | str | File path |
| content | str | Source content |
| line_start | int | Start line |
| line_end | int | End line |
| score | float | Relevance score |

### RAGResponse

| Field | Type | Description |
|-------|------|-------------|
| context | str | Combined context |
| query | str | Original query |
| chunks | list[Chunk] | Retrieved chunks |
| sources | list[Source] | Source attribution |
| confidence | float | Confidence (0-1) |
| retrieval_time_ms | int | Retrieval duration |
