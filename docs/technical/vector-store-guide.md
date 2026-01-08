# Vector Store Guide

This guide covers the `paracle_vector` package for embeddings and semantic search.

## Overview

The vector store system provides:

- **ChromaDB integration** - Local/persistent vector storage
- **pgvector support** - PostgreSQL with vector extensions
- **Embedding service** - Multi-provider embedding generation
- **Semantic search** - Similarity-based document retrieval

## Quick Start

### Using ChromaDB (Local Development)

```python
from paracle_vector import ChromaStore, EmbeddingService, Document

# Initialize services
store = ChromaStore(persist_dir=".paracle/vectors")
embeddings = EmbeddingService()  # Uses mock by default

# Create a collection
await store.create_collection("knowledge", dimension=1536)

# Create documents with embeddings
texts = ["Python is a programming language", "JavaScript runs in browsers"]
vectors = await embeddings.embed(texts)

docs = [
    Document(id="doc1", content=texts[0], embedding=vectors[0]),
    Document(id="doc2", content=texts[1], embedding=vectors[1]),
]

# Add to collection
await store.add_documents("knowledge", docs)

# Search
query_embedding = await embeddings.embed_single("What is Python?")
results = await store.search("knowledge", query_embedding, top_k=5)

for result in results:
    print(f"{result.document.content} (score: {result.score:.4f})")
```

### Using pgvector (Production)

```python
from paracle_vector import PgVectorStore, EmbeddingService

# Initialize with PostgreSQL connection
store = PgVectorStore("postgresql://user:pass@localhost/db")

# Create collection with dimension
await store.create_collection("embeddings", dimension=1536)

# Add documents
await store.add_documents("embeddings", documents)

# Search with metadata filter
results = await store.search(
    "embeddings",
    query_embedding,
    top_k=10,
    filter_metadata={"category": "python"}
)
```

## Embedding Providers

### Mock Provider (Testing)

```python
from paracle_vector import EmbeddingService, EmbeddingProvider

service = EmbeddingService(provider=EmbeddingProvider.MOCK)
embedding = await service.embed_single("test")
```

Deterministic embeddings based on text hash - perfect for testing.

### OpenAI Provider

```python
from paracle_vector import EmbeddingService, EmbeddingProvider, EmbeddingConfig

config = EmbeddingConfig(
    provider=EmbeddingProvider.OPENAI,
    model="text-embedding-3-small",
    dimension=1536,
    api_key="sk-..."  # Or use OPENAI_API_KEY env var
)
service = EmbeddingService(config=config)

embedding = await service.embed_single("Hello world")
```

### Local Provider (sentence-transformers)

```python
from paracle_vector import EmbeddingService, EmbeddingProvider, EmbeddingConfig

config = EmbeddingConfig(
    provider=EmbeddingProvider.LOCAL,
    model="all-MiniLM-L6-v2",
)
service = EmbeddingService(config=config)

# Runs locally without API calls
embedding = await service.embed_single("Local embedding")
```

Requires: `pip install sentence-transformers`

## Vector Store Operations

### Collections

```python
# Create collection
await store.create_collection("my-collection", dimension=1536)

# Check existence
exists = await store.collection_exists("my-collection")

# List all collections
collections = await store.list_collections()

# Delete collection
await store.delete_collection("my-collection")
```

### Documents

```python
# Add documents
doc = Document(
    id="doc1",
    content="Document content",
    embedding=[0.1, 0.2, ...],  # 1536 dimensions
    metadata={"source": "wiki", "page": 1}
)
await store.add_documents("collection", [doc])

# Get by ID
doc = await store.get_document("collection", "doc1")

# Delete
deleted = await store.delete_document("collection", "doc1")

# Count
count = await store.count_documents("collection")
```

### Searching

```python
# Basic search
results = await store.search(
    collection="knowledge",
    query_embedding=query_vector,
    top_k=10
)

# With metadata filter
results = await store.search(
    collection="knowledge",
    query_embedding=query_vector,
    top_k=10,
    filter_metadata={"category": "python", "year": 2024}
)

# Process results
for result in results:
    print(f"ID: {result.document.id}")
    print(f"Content: {result.document.content}")
    print(f"Score: {result.score:.4f}")
    print(f"Distance: {result.distance}")
```

## ChromaDB Configuration

### In-Memory (Testing)

```python
store = ChromaStore()  # No persistence
```

### Persistent Storage

```python
store = ChromaStore(persist_dir=".paracle/vectors")
```

### Multi-Tenant

```python
store = ChromaStore(
    persist_dir=".paracle/vectors",
    tenant="my_tenant",
    database="my_database"
)
```

## pgvector Configuration

### Connection URL

```python
store = PgVectorStore("postgresql://user:pass@localhost:5432/mydb")
```

### With Pool Settings

```python
store = PgVectorStore(
    "postgresql://user:pass@localhost/db",
    pool_size=10,
    schema="vectors"  # Custom schema
)
```

### Prerequisites

1. Install pgvector extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. Install Python packages:
   ```bash
   pip install paracle[pgvector]
   ```

## Best Practices

### 1. Batch Embeddings

```python
# Good - batch multiple texts
embeddings = await service.embed(["text1", "text2", "text3"])

# Avoid - individual calls
for text in texts:
    emb = await service.embed_single(text)
```

### 2. Pre-generate Embeddings

```python
# Generate embeddings once
embeddings = await service.embed(texts)
docs = [
    Document(id=f"doc{i}", content=text, embedding=emb)
    for i, (text, emb) in enumerate(zip(texts, embeddings))
]

# Store with embeddings
await store.add_documents("collection", docs)
```

### 3. Use Appropriate Dimensions

| Provider | Model | Dimension |
|----------|-------|-----------|
| OpenAI | text-embedding-3-small | 1536 |
| OpenAI | text-embedding-3-large | 3072 |
| Local | all-MiniLM-L6-v2 | 384 |
| Local | all-mpnet-base-v2 | 768 |

### 4. Handle Errors

```python
from paracle_vector import VectorStoreError, CollectionNotFoundError

try:
    results = await store.search("unknown", query_embedding)
except CollectionNotFoundError as e:
    print(f"Collection not found: {e.collection}")
except VectorStoreError as e:
    print(f"Vector store error: {e}")
```

## Installation

```bash
# ChromaDB support
pip install paracle[vector]

# pgvector support
pip install paracle[pgvector]

# OpenAI embeddings
pip install paracle[providers]

# Local embeddings
pip install sentence-transformers
```

## API Reference

### Document

| Field | Type | Description |
|-------|------|-------------|
| id | str | Unique identifier |
| content | str | Text content |
| embedding | list[float] | Optional | Vector embedding |
| metadata | dict | Additional metadata |
| created_at | datetime | Creation timestamp |

### SearchResult

| Field | Type | Description |
|-------|------|-------------|
| document | Document | Matched document |
| score | float | Similarity score (0-1) |
| distance | float | Optional | Distance metric |

### EmbeddingConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| provider | EmbeddingProvider | MOCK | Provider to use |
| model | str | text-embedding-3-small | Model name |
| dimension | int | 1536 | Vector dimension |
| batch_size | int | 100 | Max batch size |
| api_key | str | None | Optional API key |
