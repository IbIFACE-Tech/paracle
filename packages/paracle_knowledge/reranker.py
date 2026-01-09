"""Reranking for improved search relevance.

This module provides reranking capabilities to improve
the relevance of search results from vector similarity.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from paracle_knowledge.base import Chunk

logger = logging.getLogger(__name__)


@dataclass
class RerankResult:
    """Result from reranking.

    Attributes:
        chunk: The reranked chunk
        original_score: Original similarity score
        rerank_score: New score from reranker
        combined_score: Combined/final score
    """

    chunk: Chunk
    original_score: float
    rerank_score: float
    combined_score: float


class Reranker(ABC):
    """Abstract base class for rerankers."""

    @abstractmethod
    async def rerank(
        self,
        query: str,
        chunks: list[tuple[Chunk, float]],
        top_k: int = 10,
    ) -> list[RerankResult]:
        """Rerank chunks based on query.

        Args:
            query: Search query
            chunks: List of (chunk, score) tuples from initial search
            top_k: Number of results to return

        Returns:
            Reranked results
        """
        pass


class CrossEncoderReranker(Reranker):
    """Cross-encoder based reranker.

    Uses a cross-encoder model to compute query-document
    relevance scores for better ranking.

    Requires: sentence-transformers package
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        *,
        batch_size: int = 32,
        score_weight: float = 0.7,
    ):
        """Initialize cross-encoder reranker.

        Args:
            model_name: Name of cross-encoder model
            batch_size: Batch size for inference
            score_weight: Weight of rerank score in combined score
        """
        self._model_name = model_name
        self._batch_size = batch_size
        self._score_weight = score_weight
        self._model: Any = None

    def _get_model(self) -> Any:
        """Lazy initialization of cross-encoder model."""
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
            except ImportError as e:
                raise ImportError(
                    "sentence-transformers package not installed. "
                    "Install with: pip install sentence-transformers"
                ) from e

            self._model = CrossEncoder(self._model_name)
            logger.info("Loaded cross-encoder model: %s", self._model_name)

        return self._model

    async def rerank(
        self,
        query: str,
        chunks: list[tuple[Chunk, float]],
        top_k: int = 10,
    ) -> list[RerankResult]:
        """Rerank chunks using cross-encoder."""
        if not chunks:
            return []

        model = self._get_model()

        # Prepare query-document pairs
        pairs = [(query, chunk.content) for chunk, _ in chunks]

        # Get cross-encoder scores
        scores = model.predict(pairs, batch_size=self._batch_size)

        # Combine with original scores
        results = []
        for i, (chunk, original_score) in enumerate(chunks):
            rerank_score = float(scores[i])

            # Normalize rerank score to [0, 1]
            rerank_score_normalized = (
                rerank_score + 10
            ) / 20  # Approximate normalization

            # Combine scores
            combined_score = (
                self._score_weight * rerank_score_normalized
                + (1 - self._score_weight) * original_score
            )

            results.append(
                RerankResult(
                    chunk=chunk,
                    original_score=original_score,
                    rerank_score=rerank_score,
                    combined_score=combined_score,
                )
            )

        # Sort by combined score
        results.sort(key=lambda x: x.combined_score, reverse=True)

        return results[:top_k]


class LLMReranker(Reranker):
    """LLM-based reranker using relevance scoring.

    Uses an LLM to score query-document relevance.
    More expensive but can be more accurate.
    """

    def __init__(
        self,
        *,
        score_weight: float = 0.7,
    ):
        """Initialize LLM reranker.

        Args:
            score_weight: Weight of rerank score in combined score
        """
        self._score_weight = score_weight

    async def rerank(
        self,
        query: str,
        chunks: list[tuple[Chunk, float]],
        top_k: int = 10,
    ) -> list[RerankResult]:
        """Rerank chunks using LLM scoring.

        Note: This is a placeholder implementation.
        Full implementation would use an LLM to score relevance.
        """
        # For now, use a simple keyword-based scoring
        results = []

        query_words = set(query.lower().split())

        for chunk, original_score in chunks:
            # Simple keyword overlap score
            chunk_words = set(chunk.content.lower().split())
            overlap = len(query_words & chunk_words)
            rerank_score = overlap / max(len(query_words), 1)

            combined_score = (
                self._score_weight * rerank_score
                + (1 - self._score_weight) * original_score
            )

            results.append(
                RerankResult(
                    chunk=chunk,
                    original_score=original_score,
                    rerank_score=rerank_score,
                    combined_score=combined_score,
                )
            )

        results.sort(key=lambda x: x.combined_score, reverse=True)
        return results[:top_k]


class RecencyReranker(Reranker):
    """Reranker that boosts recent documents.

    Useful for knowledge bases where freshness matters.
    """

    def __init__(
        self,
        *,
        recency_weight: float = 0.2,
        decay_days: int = 30,
    ):
        """Initialize recency reranker.

        Args:
            recency_weight: Weight of recency in final score
            decay_days: Days after which recency boost decays to zero
        """
        self._recency_weight = recency_weight
        self._decay_days = decay_days

    async def rerank(
        self,
        query: str,
        chunks: list[tuple[Chunk, float]],
        top_k: int = 10,
    ) -> list[RerankResult]:
        """Rerank with recency boost."""
        from paracle_core.compat import UTC, datetime

        now = datetime.now(UTC)
        results = []

        for chunk, original_score in chunks:
            # Calculate recency score
            age_days = (now - chunk.created_at).days
            recency_score = max(0, 1 - (age_days / self._decay_days))

            combined_score = (
                1 - self._recency_weight
            ) * original_score + self._recency_weight * recency_score

            results.append(
                RerankResult(
                    chunk=chunk,
                    original_score=original_score,
                    rerank_score=recency_score,
                    combined_score=combined_score,
                )
            )

        results.sort(key=lambda x: x.combined_score, reverse=True)
        return results[:top_k]


class EnsembleReranker(Reranker):
    """Ensemble of multiple rerankers.

    Combines scores from multiple rerankers for better results.
    """

    def __init__(
        self,
        rerankers: list[tuple[Reranker, float]],
    ):
        """Initialize ensemble reranker.

        Args:
            rerankers: List of (reranker, weight) tuples
        """
        self._rerankers = rerankers

        # Normalize weights
        total_weight = sum(w for _, w in rerankers)
        self._rerankers = [(r, w / total_weight) for r, w in rerankers]

    async def rerank(
        self,
        query: str,
        chunks: list[tuple[Chunk, float]],
        top_k: int = 10,
    ) -> list[RerankResult]:
        """Rerank using ensemble of rerankers."""
        if not chunks:
            return []

        # Collect scores from each reranker
        all_results: dict[str, list[tuple[float, float]]] = {
            chunk.id: [] for chunk, _ in chunks
        }

        for reranker, weight in self._rerankers:
            results = await reranker.rerank(query, chunks, top_k=len(chunks))
            for result in results:
                all_results[result.chunk.id].append((result.combined_score, weight))

        # Combine scores
        final_results = []
        chunk_map = {chunk.id: (chunk, score) for chunk, score in chunks}

        for chunk_id, scores in all_results.items():
            chunk, original_score = chunk_map[chunk_id]

            # Weighted average of scores
            combined_score = sum(score * weight for score, weight in scores)

            final_results.append(
                RerankResult(
                    chunk=chunk,
                    original_score=original_score,
                    rerank_score=combined_score,
                    combined_score=combined_score,
                )
            )

        final_results.sort(key=lambda x: x.combined_score, reverse=True)
        return final_results[:top_k]
