"""Learning Engine for Paracle Meta-Agent.

Implements continuous learning and improvement through:
- Feedback collection (user ratings, usage metrics)
- Quality scoring and tracking
- Pattern recognition
- Template evolution
- Performance optimization over time

Now supports PostgreSQL + pgvector via the repository pattern.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from paracle_core.logging import get_logger
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from paracle_meta.database import MetaDatabase
    from paracle_meta.repositories import (
        FeedbackRepository,
        GenerationRepository,
        TemplateRepository,
    )

logger = get_logger(__name__)


class Feedback(BaseModel):
    """User feedback for a generation."""

    generation_id: str
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5 stars")
    comment: str | None = None
    usage_count: int = Field(default=1, description="How many times used")
    created_at: datetime = Field(default_factory=datetime.now)


class LearningMetrics(BaseModel):
    """Learning progress metrics."""

    total_generations: int
    success_rate: float  # Percentage
    avg_quality: float  # 0-10 scale

    # Learning progress
    quality_improvement: float  # Percentage improvement
    first_n_avg: float  # Avg quality of first N generations
    last_n_avg: float  # Avg quality of last N generations

    # Top patterns
    top_patterns: list[dict[str, Any]]


class LearningEngine:
    """Continuous learning engine for meta-agent.

    Learns from:
    1. User feedback (ratings, comments)
    2. Usage patterns (what gets used often)
    3. Success metrics (quality scores, no errors)
    4. Provider performance (which works best for what)

    Produces:
    - Evolved templates (successful patterns → reusable templates)
    - Improved prompts (A/B testing, optimization)
    - Provider routing rules (task type → best provider)
    - Quality predictions (estimate before generating)

    Example:
        >>> engine = LearningEngine()
        >>>
        >>> # Track generation
        >>> await engine.track_generation(result)
        >>>
        >>> # Record feedback
        >>> await engine.record_feedback(
        ...     generation_id=result.id,
        ...     rating=5,
        ...     comment="Perfect!"
        ... )
        >>>
        >>> # Get learning progress
        >>> metrics = await engine.get_statistics()
        >>> print(f"Quality improved by {metrics.quality_improvement}%")

    New repository-based usage:
        >>> from paracle_meta.database import get_meta_database
        >>> db = get_meta_database()
        >>> engine = LearningEngine.with_repositories(db)
    """

    def __init__(
        self,
        enabled: bool = True,
        db_path: Path | None = None,
        min_samples_for_template: int = 5,
        min_rating_for_template: float = 4.0,
        *,
        # New repository-based parameters
        generation_repo: GenerationRepository | None = None,
        feedback_repo: FeedbackRepository | None = None,
        template_repo: TemplateRepository | None = None,
    ):
        """Initialize learning engine.

        Args:
            enabled: Enable/disable learning
            db_path: Path to learning database (legacy SQLite mode)
            min_samples_for_template: Min samples before creating template
            min_rating_for_template: Min avg rating for template
            generation_repo: Generation repository (new mode)
            feedback_repo: Feedback repository (new mode)
            template_repo: Template repository (new mode)
        """
        self.enabled = enabled
        self.db_path = db_path or self._default_db_path()
        self.min_samples = min_samples_for_template
        self.min_rating = min_rating_for_template

        # Repository-based storage (new mode)
        self._generation_repo = generation_repo
        self._feedback_repo = feedback_repo
        self._template_repo = template_repo
        self._use_repositories = all([generation_repo, feedback_repo, template_repo])

        if enabled:
            if self._use_repositories:
                logger.info("LearningEngine initialized with repositories")
            else:
                self._init_database()
                logger.info(
                    "LearningEngine initialized", extra={"db": str(self.db_path)}
                )
        else:
            logger.info("LearningEngine disabled")

    @classmethod
    def with_repositories(
        cls,
        db: MetaDatabase,
        enabled: bool = True,
        min_samples_for_template: int = 5,
        min_rating_for_template: float = 4.0,
    ) -> LearningEngine:
        """Create LearningEngine with repository-based storage.

        This is the preferred way to create a LearningEngine for production use
        with PostgreSQL + pgvector support.

        Args:
            db: MetaDatabase instance
            enabled: Enable/disable learning
            min_samples_for_template: Min samples before creating template
            min_rating_for_template: Min avg rating for template

        Returns:
            Configured LearningEngine instance
        """
        from paracle_meta.repositories import (
            FeedbackRepository,
            GenerationRepository,
            TemplateRepository,
        )

        return cls(
            enabled=enabled,
            min_samples_for_template=min_samples_for_template,
            min_rating_for_template=min_rating_for_template,
            generation_repo=GenerationRepository(db),
            feedback_repo=FeedbackRepository(db),
            template_repo=TemplateRepository(db),
        )

    async def track_generation(self, result: Any) -> None:
        """Track a generation for learning.

        Stores:
        - Generation metadata
        - Quality score
        - Provider/model used
        - Cost
        - Tokens
        """
        if not self.enabled:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO generations (
                id, artifact_type, name, content, provider, model,
                quality_score, cost_usd, tokens_input, tokens_output,
                reasoning, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                result.id,
                result.artifact_type,
                result.name,
                result.content,
                result.provider,
                result.model,
                result.quality_score,
                result.cost_usd,
                result.tokens_input,
                result.tokens_output,
                result.reasoning,
                result.created_at.isoformat(),
            ),
        )

        conn.commit()
        conn.close()

        logger.debug(f"Tracked generation: {result.id}")

    async def record_feedback(
        self,
        generation_id: str,
        rating: int,
        comment: str | None = None,
        usage_count: int = 1,
    ) -> None:
        """Record user feedback.

        Args:
            generation_id: ID of generation
            rating: 1-5 star rating
            comment: Optional comment
            usage_count: How many times artifact was used
        """
        if not self.enabled:
            return

        feedback = Feedback(
            generation_id=generation_id,
            rating=rating,
            comment=comment,
            usage_count=usage_count,
        )

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO feedback (
                generation_id, rating, comment, usage_count, created_at
            ) VALUES (?, ?, ?, ?, ?)
        """,
            (
                feedback.generation_id,
                feedback.rating,
                feedback.comment,
                feedback.usage_count,
                feedback.created_at.isoformat(),
            ),
        )

        conn.commit()
        conn.close()

        logger.info(
            f"Feedback recorded: {generation_id}",
            extra={"rating": rating, "usage": usage_count},
        )

        # Check if this pattern should become a template
        await self._check_template_promotion(generation_id)

    async def get_statistics(self) -> dict[str, Any]:
        """Get learning statistics and progress.

        Returns:
            Dictionary with:
            - total_generations: Total count
            - success_rate: Percentage of successful generations
            - avg_quality: Average quality score
            - quality_improvement: % improvement over time
            - top_patterns: Most successful patterns
        """
        if not self.enabled:
            return {"enabled": False}

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total generations
        cursor.execute("SELECT COUNT(*) FROM generations")
        total = cursor.fetchone()[0]

        # Average quality
        cursor.execute("SELECT AVG(quality_score) FROM generations")
        avg_quality = cursor.fetchone()[0] or 0

        # Success rate (quality >= 7.0)
        cursor.execute(
            """
            SELECT COUNT(*) * 100.0 / ?
            FROM generations
            WHERE quality_score >= 7.0
        """,
            (total,),
        )
        success_rate = cursor.fetchone()[0] or 0

        # Learning progress (first 50 vs last 50)
        cursor.execute(
            """
            SELECT AVG(quality_score)
            FROM (
                SELECT quality_score FROM generations
                ORDER BY created_at ASC
                LIMIT 50
            )
        """
        )
        first_50_avg = cursor.fetchone()[0] or 0

        cursor.execute(
            """
            SELECT AVG(quality_score)
            FROM (
                SELECT quality_score FROM generations
                ORDER BY created_at DESC
                LIMIT 50
            )
        """
        )
        last_50_avg = cursor.fetchone()[0] or 0

        improvement = 0
        if first_50_avg > 0:
            improvement = ((last_50_avg - first_50_avg) / first_50_avg) * 100

        # Top patterns (by avg rating + usage)
        cursor.execute(
            """
            SELECT
                g.artifact_type,
                g.name,
                COUNT(*) as generation_count,
                AVG(f.rating) as avg_rating,
                SUM(f.usage_count) as total_usage,
                AVG(g.quality_score) as avg_quality
            FROM generations g
            LEFT JOIN feedback f ON g.id = f.generation_id
            GROUP BY g.artifact_type, g.name
            HAVING COUNT(*) >= 3 AND AVG(f.rating) >= 4.0
            ORDER BY AVG(f.rating) DESC, total_usage DESC
            LIMIT 10
        """
        )

        top_patterns = []
        for row in cursor.fetchall():
            top_patterns.append(
                {
                    "type": row[0],
                    "name": row[1],
                    "count": row[2],
                    "avg_rating": round(row[3] or 0, 2),
                    "usage": row[4] or 0,
                    "quality": round(row[5] or 0, 1),
                }
            )

        conn.close()

        return {
            "total_generations": total,
            "success_rate": round(success_rate, 1),
            "avg_quality": round(avg_quality, 1),
            "quality_improvement": round(improvement, 1),
            "first_50_avg": round(first_50_avg, 1),
            "last_50_avg": round(last_50_avg, 1),
            "top_patterns": top_patterns,
        }

    async def _check_template_promotion(self, generation_id: str) -> None:
        """Check if generation should be promoted to template.

        Criteria:
        - Used multiple times (>= min_samples)
        - High rating (>= min_rating)
        - High quality score (>= 8.0)
        """
        # Use repository mode if available
        if self._use_repositories:
            await self._check_template_promotion_repo(generation_id)
            return

        # Legacy SQLite mode
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get generation with feedback
        cursor.execute(
            """
            SELECT
                g.id,
                g.artifact_type,
                g.name,
                g.content,
                g.quality_score,
                COUNT(f.id) as feedback_count,
                AVG(f.rating) as avg_rating,
                SUM(f.usage_count) as total_usage
            FROM generations g
            LEFT JOIN feedback f ON g.id = f.generation_id
            WHERE g.id = ?
            GROUP BY g.id
        """,
            (generation_id,),
        )

        row = cursor.fetchone()
        if not row:
            conn.close()
            return

        (
            gen_id,
            artifact_type,
            name,
            content,
            quality,
            feedback_count,
            avg_rating,
            usage,
        ) = row

        # Check criteria
        if (
            feedback_count >= self.min_samples
            and avg_rating >= self.min_rating
            and quality >= 8.0
        ):

            # Promote to template!
            logger.info(
                f"Promoting to template: {name}",
                extra={
                    "type": artifact_type,
                    "rating": avg_rating,
                    "quality": quality,
                    "usage": usage,
                },
            )

            # Legacy mode: log only (no template repository available)
            logger.warning(
                "Template promotion skipped in legacy mode. "
                "Use LearningEngine.with_repositories() for full functionality."
            )

        conn.close()

    async def _check_template_promotion_repo(self, generation_id: str) -> None:
        """Check template promotion using repository pattern.

        This is the new implementation that actually saves to the template library.
        """
        if (
            not self._generation_repo
            or not self._feedback_repo
            or not self._template_repo
        ):
            return

        # Get generation
        generation = self._generation_repo.get(generation_id)
        if not generation:
            return

        # Get feedback statistics
        feedback_count = self._feedback_repo.get_feedback_count(generation_id)
        avg_rating = self._feedback_repo.get_average_rating(generation_id)

        if avg_rating is None:
            return

        # Check promotion criteria
        if (
            feedback_count >= self.min_samples
            and avg_rating >= self.min_rating
            and generation.quality_score >= 8.0
        ):

            # Check if template already exists for this generation
            existing = self._template_repo.get_by_name(f"{generation.name}_template")
            if existing:
                logger.debug(f"Template already exists for {generation.name}")
                return

            # Promote to template!
            logger.info(
                f"Promoting generation to template: {generation.name}",
                extra={
                    "type": generation.artifact_type,
                    "rating": avg_rating,
                    "quality": generation.quality_score,
                    "feedback_count": feedback_count,
                },
            )

            # Create template from generation
            template = self._template_repo.promote_from_generation(
                generation=generation,
                avg_rating=avg_rating,
            )

            logger.info(
                f"Template created: {template.name}", extra={"template_id": template.id}
            )

    def _init_database(self) -> None:
        """Initialize learning database."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Generations table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS generations (
                id TEXT PRIMARY KEY,
                artifact_type TEXT NOT NULL,
                name TEXT NOT NULL,
                content TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                quality_score REAL NOT NULL,
                cost_usd REAL NOT NULL,
                tokens_input INTEGER NOT NULL,
                tokens_output INTEGER NOT NULL,
                reasoning TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """
        )

        # Feedback table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                generation_id TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                comment TEXT,
                usage_count INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (generation_id) REFERENCES generations(id)
            )
        """
        )

        # Indexes
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_generations_created
            ON generations(created_at)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_feedback_generation
            ON feedback(generation_id)
        """
        )

        conn.commit()
        conn.close()

        logger.debug("Learning database initialized")

    def _default_db_path(self) -> Path:
        """Get default database path."""
        return Path.cwd() / ".parac" / "memory" / "data" / "meta_learning.db"


class FeedbackCollector:
    """Helper for collecting user feedback."""

    @staticmethod
    async def prompt_for_feedback(generation_id: str) -> Feedback | None:
        """Prompt user for feedback (CLI).

        Args:
            generation_id: ID of generation

        Returns:
            Feedback if provided, None if skipped
        """
        try:
            import click

            rating = click.prompt(
                "Rate this generation (1-5 stars)",
                type=click.IntRange(1, 5),
                default=None,
                show_default=False,
            )

            if rating is None:
                return None

            comment = click.prompt("Comment (optional)", default="", show_default=False)

            return Feedback(
                generation_id=generation_id, rating=rating, comment=comment or None
            )

        except Exception as e:
            logger.warning(f"Failed to collect feedback: {e}")
            return None
