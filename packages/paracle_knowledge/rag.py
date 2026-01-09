"""RAG (Retrieval Augmented Generation) Engine.

This module provides the core RAG engine for context-aware queries:
- Query processing and expansion
- Multi-step retrieval
- Context building
- Source attribution
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from paracle_core.compat import UTC, datetime
from pydantic import BaseModel, Field

from paracle_knowledge.base import Chunk, KnowledgeBase, Source

if TYPE_CHECKING:
    from paracle_knowledge.reranker import Reranker

logger = logging.getLogger(__name__)


class RAGConfig(BaseModel):
    """Configuration for RAG engine.

    Attributes:
        retrieval_top_k: Number of chunks to retrieve initially
        final_top_k: Number of chunks after reranking
        min_relevance_score: Minimum relevance score to include
        max_context_length: Maximum context length in characters
        include_sources: Whether to include source citations
        enable_query_expansion: Enable query expansion
        enable_reranking: Enable reranking step
    """

    retrieval_top_k: int = 20
    final_top_k: int = 5
    min_relevance_score: float = 0.3
    max_context_length: int = 8000
    include_sources: bool = True
    enable_query_expansion: bool = False
    enable_reranking: bool = True


class RAGContext(BaseModel):
    """Context for a RAG query.

    Attributes:
        filters: Optional metadata filters
        namespace: Optional namespace to search in
        retrieval_top_k: Override retrieval count
        final_top_k: Override final count
        custom: Custom context data
    """

    filters: dict[str, Any] | None = None
    namespace: str | None = None
    retrieval_top_k: int | None = None
    final_top_k: int | None = None
    custom: dict[str, Any] = Field(default_factory=dict)


class RAGResponse(BaseModel):
    """Response from RAG query.

    Attributes:
        context: Retrieved context text
        sources: Source references
        chunks: Retrieved chunks
        query: Original query
        expanded_query: Expanded query (if enabled)
        confidence: Confidence score
        retrieval_time_ms: Time taken for retrieval
    """

    context: str
    sources: list[Source] = Field(default_factory=list)
    chunks: list[Chunk] = Field(default_factory=list)
    query: str
    expanded_query: str | None = None
    confidence: float = 0.0
    retrieval_time_ms: float = 0.0

    def format_context_with_sources(self) -> str:
        """Format context with inline source citations."""
        if not self.sources:
            return self.context

        lines = []
        for i, source in enumerate(self.sources, 1):
            lines.append(f"[{i}] {source.content}")
            lines.append(f"    Source: {source.to_citation()}")
            lines.append("")

        return "\n".join(lines)


class RAGEngine:
    """RAG (Retrieval Augmented Generation) Engine.

    Provides context-aware retrieval for LLM queries.

    Usage:
        rag = RAGEngine(
            knowledge_base=kb,
            config=RAGConfig(final_top_k=5)
        )

        response = await rag.query(
            question="How does authentication work?",
            context=RAGContext(filters={"language": "python"})
        )

        print(response.context)
        for source in response.sources:
            print(f"  - {source.to_citation()}")
    """

    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        config: RAGConfig | None = None,
        reranker: Reranker | None = None,
    ):
        """Initialize RAG engine.

        Args:
            knowledge_base: Knowledge base to query
            config: RAG configuration
            reranker: Optional reranker for improved relevance
        """
        self._kb = knowledge_base
        self._config = config or RAGConfig()
        self._reranker = reranker

    async def query(
        self,
        question: str,
        context: RAGContext | None = None,
    ) -> RAGResponse:
        """Execute a RAG query.

        Args:
            question: Question to answer
            context: Optional query context

        Returns:
            RAG response with context and sources
        """
        start_time = datetime.now(UTC)
        context = context or RAGContext()

        # Determine parameters
        retrieval_top_k = context.retrieval_top_k or self._config.retrieval_top_k
        final_top_k = context.final_top_k or self._config.final_top_k

        # Query expansion (if enabled)
        expanded_query = None
        if self._config.enable_query_expansion:
            expanded_query = await self._expand_query(question)
            search_query = expanded_query
        else:
            search_query = question

        # Retrieve chunks
        chunks_with_scores = await self._kb.search(
            search_query,
            top_k=retrieval_top_k,
            filter_metadata=context.filters,
            min_score=self._config.min_relevance_score,
        )

        # Rerank (if enabled and reranker available)
        if self._config.enable_reranking and self._reranker and chunks_with_scores:
            rerank_results = await self._reranker.rerank(
                question, chunks_with_scores, top_k=final_top_k
            )
            chunks_with_scores = [(r.chunk, r.combined_score) for r in rerank_results]
        else:
            chunks_with_scores = chunks_with_scores[:final_top_k]

        # Build context
        context_text, sources = self._build_context(chunks_with_scores)

        # Calculate confidence
        confidence = self._calculate_confidence(chunks_with_scores)

        # Calculate time
        retrieval_time = (datetime.now(UTC) - start_time).total_seconds() * 1000

        return RAGResponse(
            context=context_text,
            sources=sources,
            chunks=[chunk for chunk, _ in chunks_with_scores],
            query=question,
            expanded_query=expanded_query,
            confidence=confidence,
            retrieval_time_ms=retrieval_time,
        )

    async def query_with_history(
        self,
        question: str,
        history: list[tuple[str, str]],
        context: RAGContext | None = None,
    ) -> RAGResponse:
        """Execute a RAG query with conversation history.

        Args:
            question: Current question
            history: List of (question, answer) tuples
            context: Optional query context

        Returns:
            RAG response
        """
        # Combine history with current question for better retrieval
        history_context = "\n".join(
            f"Q: {q}\nA: {a}" for q, a in history[-3:]  # Last 3 turns
        )
        enhanced_query = f"{history_context}\n\nCurrent question: {question}"

        return await self.query(enhanced_query, context)

    async def multi_query(
        self,
        questions: list[str],
        context: RAGContext | None = None,
    ) -> list[RAGResponse]:
        """Execute multiple RAG queries.

        Args:
            questions: List of questions
            context: Shared query context

        Returns:
            List of RAG responses
        """
        responses = []
        for question in questions:
            response = await self.query(question, context)
            responses.append(response)
        return responses

    async def _expand_query(self, query: str) -> str:
        """Expand query for better retrieval.

        This is a simple implementation. A full implementation
        would use an LLM to generate query variations.
        """
        # Simple expansion: add common variations
        words = query.lower().split()

        # Add synonyms for common programming terms
        expansions = {
            "function": ["method", "def", "func"],
            "class": ["type", "struct", "object"],
            "error": ["exception", "bug", "issue"],
            "install": ["setup", "configure", "pip"],
            "import": ["include", "require", "use"],
        }

        expanded_words = list(words)
        for word in words:
            if word in expansions:
                expanded_words.extend(expansions[word][:2])

        return " ".join(expanded_words)

    def _build_context(
        self,
        chunks_with_scores: list[tuple[Chunk, float]],
    ) -> tuple[str, list[Source]]:
        """Build context text from retrieved chunks.

        Args:
            chunks_with_scores: List of (chunk, score) tuples

        Returns:
            Tuple of (context_text, sources)
        """
        context_parts = []
        sources = []
        total_length = 0

        for chunk, score in chunks_with_scores:
            # Check context length limit
            if total_length + len(chunk.content) > self._config.max_context_length:
                break

            context_parts.append(chunk.content)
            total_length += len(chunk.content)

            # Create source reference
            if self._config.include_sources:
                source = Source(
                    document_id=chunk.metadata.document_id,
                    document_name=chunk.metadata.custom.get("document_name", ""),
                    file_path=chunk.metadata.custom.get("file_path"),
                    chunk_id=chunk.id,
                    content=(
                        chunk.content[:200] + "..."
                        if len(chunk.content) > 200
                        else chunk.content
                    ),
                    line_start=chunk.metadata.start_line,
                    line_end=chunk.metadata.end_line,
                    score=score,
                )
                sources.append(source)

        context_text = "\n\n---\n\n".join(context_parts)
        return context_text, sources

    def _calculate_confidence(
        self,
        chunks_with_scores: list[tuple[Chunk, float]],
    ) -> float:
        """Calculate confidence score for the response.

        Based on:
        - Number of relevant chunks found
        - Average relevance score
        - Score distribution
        """
        if not chunks_with_scores:
            return 0.0

        scores = [score for _, score in chunks_with_scores]

        # Factors
        avg_score = sum(scores) / len(scores)
        top_score = max(scores)
        coverage = min(len(scores) / self._config.final_top_k, 1.0)

        # Weighted combination
        confidence = 0.4 * top_score + 0.3 * avg_score + 0.3 * coverage

        return min(max(confidence, 0.0), 1.0)


class RAGChain:
    """Chain multiple RAG queries for complex questions.

    Supports:
    - Query decomposition
    - Multi-step retrieval
    - Answer synthesis
    """

    def __init__(
        self,
        rag_engine: RAGEngine,
        *,
        max_steps: int = 3,
    ):
        """Initialize RAG chain.

        Args:
            rag_engine: RAG engine to use
            max_steps: Maximum number of retrieval steps
        """
        self._rag = rag_engine
        self._max_steps = max_steps

    async def query(
        self,
        question: str,
        context: RAGContext | None = None,
    ) -> RAGResponse:
        """Execute a chained RAG query.

        For complex questions, decomposes into sub-questions
        and retrieves context for each.
        """
        # Decompose question
        sub_questions = self._decompose_question(question)

        if len(sub_questions) <= 1:
            # Simple question, use direct retrieval
            return await self._rag.query(question, context)

        # Multi-step retrieval
        all_chunks = []
        all_sources = []

        for sub_q in sub_questions[: self._max_steps]:
            response = await self._rag.query(sub_q, context)
            all_chunks.extend(response.chunks)
            all_sources.extend(response.sources)

        # Deduplicate chunks
        seen_ids = set()
        unique_chunks = []
        for chunk in all_chunks:
            if chunk.id not in seen_ids:
                seen_ids.add(chunk.id)
                unique_chunks.append(chunk)

        # Build combined context
        context_text = "\n\n---\n\n".join(c.content for c in unique_chunks)

        return RAGResponse(
            context=context_text,
            sources=all_sources,
            chunks=unique_chunks,
            query=question,
            confidence=self._calculate_chain_confidence(all_sources),
        )

    def _decompose_question(self, question: str) -> list[str]:
        """Decompose complex question into sub-questions.

        Simple rule-based decomposition. A full implementation
        would use an LLM for better decomposition.
        """
        # Check for compound questions
        connectors = [" and ", " also ", " additionally "]
        for connector in connectors:
            if connector in question.lower():
                parts = question.lower().split(connector)
                return [p.strip() for p in parts if p.strip()]

        # Check for multi-part questions
        if "?" in question[:-1]:  # Multiple question marks
            parts = question.split("?")
            return [p.strip() + "?" for p in parts if p.strip()]

        return [question]

    def _calculate_chain_confidence(self, sources: list[Source]) -> float:
        """Calculate confidence for chained query."""
        if not sources:
            return 0.0

        scores = [s.score for s in sources]
        return sum(scores) / len(scores)
