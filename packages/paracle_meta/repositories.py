"""Repository pattern implementation for paracle_meta.

Provides typed repositories for all meta engine data:
- GenerationRepository: Generation records and history
- FeedbackRepository: User feedback
- TemplateRepository: Reusable templates with vector search
- BestPracticesRepository: Knowledge base
- CostRepository: Cost tracking and reporting
- MemoryRepository: Persistent context memory

Follows patterns from paracle_store/repository.py.

Usage:
    from paracle_meta.repositories import (
        GenerationRepository,
        TemplateRepository,
    )
    from paracle_meta.database import get_meta_database

    db = get_meta_database()

    # Sync usage
    gen_repo = GenerationRepository(db)
    template_repo = TemplateRepository(db)

    gen = gen_repo.add(generation_record)
    templates = template_repo.find_by_type("agent")

    # Async usage
    gen = await gen_repo.add_async(generation_record)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from paracle_core.logging import get_logger
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from paracle_meta.database import (
    BestPracticeRecord,
    ContextHistory,
    CostRecord,
    FeedbackRecord,
    GenerationRecord,
    MemoryItem,
    MetaDatabase,
    TemplateRecord,
)

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


class RepositoryError(Exception):
    """Base exception for repository errors."""

    pass


class NotFoundError(RepositoryError):
    """Raised when an entity is not found."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with id '{entity_id}' not found")


class DuplicateError(RepositoryError):
    """Raised when trying to create a duplicate entity."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with id '{entity_id}' already exists")


# Pydantic models for repository operations


class GenerationResult(BaseModel):
    """Generation result model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    artifact_type: str
    name: str
    content: str
    provider: str
    model: str
    quality_score: float = 0.0
    cost_usd: float = 0.0
    tokens_input: int = 0
    tokens_output: int = 0
    reasoning: str | None = None
    extra_data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Feedback(BaseModel):
    """User feedback model."""

    id: int | None = None
    generation_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None
    usage_count: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TemplateSpec(BaseModel):
    """Template specification model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    artifact_type: str
    name: str
    description: str | None = None
    content: str
    pattern: str | None = None
    quality_score: float = 0.0
    usage_count: int = 0
    source: str = "manual"  # manual, promoted
    source_generation_id: str | None = None
    extra_data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BestPractice(BaseModel):
    """Best practice model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str
    practice: str
    rationale: str | None = None
    examples: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    priority: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CostEntry(BaseModel):
    """Cost entry model."""

    id: int | None = None
    provider: str
    model: str
    operation: str
    cost_usd: float
    tokens_input: int = 0
    tokens_output: int = 0
    generation_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CostReport(BaseModel):
    """Cost report model."""

    period: str
    total_cost: float
    by_provider: dict[str, float]
    by_model: dict[str, float]
    by_operation: dict[str, float]
    total_tokens_input: int
    total_tokens_output: int
    generation_count: int


class MemoryEntry(BaseModel):
    """Memory entry model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key: str
    value: Any
    ttl_seconds: int | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None


# Repository implementations


class GenerationRepository:
    """Repository for generation records."""

    def __init__(self, db: MetaDatabase) -> None:
        self.db = db

    def add(self, result: GenerationResult) -> GenerationResult:
        """Add a new generation record."""
        with self.db.session() as session:
            record = GenerationRecord(
                id=result.id,
                artifact_type=result.artifact_type,
                name=result.name,
                content=result.content,
                provider=result.provider,
                model=result.model,
                quality_score=result.quality_score,
                cost_usd=result.cost_usd,
                tokens_input=result.tokens_input,
                tokens_output=result.tokens_output,
                reasoning=result.reasoning,
                extra_data=result.extra_data,
                created_at=result.created_at,
            )
            session.add(record)
            logger.debug(f"Added generation: {result.id}")
        return result

    async def add_async(self, result: GenerationResult) -> GenerationResult:
        """Add a new generation record (async)."""
        async with self.db.async_session() as session:
            record = GenerationRecord(
                id=result.id,
                artifact_type=result.artifact_type,
                name=result.name,
                content=result.content,
                provider=result.provider,
                model=result.model,
                quality_score=result.quality_score,
                cost_usd=result.cost_usd,
                tokens_input=result.tokens_input,
                tokens_output=result.tokens_output,
                reasoning=result.reasoning,
                extra_data=result.extra_data,
                created_at=result.created_at,
            )
            session.add(record)
            logger.debug(f"Added generation: {result.id}")
        return result

    def get(self, id: str) -> GenerationResult | None:
        """Get generation by ID."""
        with self.db.session() as session:
            record = session.get(GenerationRecord, id)
            if record is None:
                return None
            return self._to_model(record)

    async def get_async(self, id: str) -> GenerationResult | None:
        """Get generation by ID (async)."""
        async with self.db.async_session() as session:
            record = await session.get(GenerationRecord, id)
            if record is None:
                return None
            return self._to_model(record)

    def list_recent(self, limit: int = 100) -> list[GenerationResult]:
        """List recent generations."""
        with self.db.session() as session:
            stmt = (
                select(GenerationRecord)
                .order_by(GenerationRecord.created_at.desc())
                .limit(limit)
            )
            records = session.execute(stmt).scalars().all()
            return [self._to_model(r) for r in records]

    def get_by_type(
        self, artifact_type: str, limit: int = 50
    ) -> list[GenerationResult]:
        """Get generations by artifact type."""
        with self.db.session() as session:
            stmt = (
                select(GenerationRecord)
                .where(GenerationRecord.artifact_type == artifact_type)
                .order_by(GenerationRecord.created_at.desc())
                .limit(limit)
            )
            records = session.execute(stmt).scalars().all()
            return [self._to_model(r) for r in records]

    def get_statistics(self) -> dict[str, Any]:
        """Get generation statistics."""
        with self.db.session() as session:
            # Total count
            total = (
                session.execute(select(func.count(GenerationRecord.id))).scalar() or 0
            )

            # Average quality
            avg_quality = (
                session.execute(
                    select(func.avg(GenerationRecord.quality_score))
                ).scalar()
                or 0
            )

            # Success rate (quality >= 7.0)
            success_count = (
                session.execute(
                    select(func.count(GenerationRecord.id)).where(
                        GenerationRecord.quality_score >= 7.0
                    )
                ).scalar()
                or 0
            )

            success_rate = (success_count / total * 100) if total > 0 else 0

            return {
                "total_generations": total,
                "avg_quality": round(float(avg_quality), 2),
                "success_rate": round(success_rate, 1),
            }

    def _to_model(self, record: GenerationRecord) -> GenerationResult:
        """Convert database record to model."""
        return GenerationResult(
            id=record.id,
            artifact_type=record.artifact_type,
            name=record.name,
            content=record.content,
            provider=record.provider,
            model=record.model,
            quality_score=record.quality_score,
            cost_usd=record.cost_usd,
            tokens_input=record.tokens_input,
            tokens_output=record.tokens_output,
            reasoning=record.reasoning,
            extra_data=record.extra_data or {},
            created_at=record.created_at,
        )


class FeedbackRepository:
    """Repository for user feedback."""

    def __init__(self, db: MetaDatabase) -> None:
        self.db = db

    def add(self, feedback: Feedback) -> Feedback:
        """Add feedback for a generation."""
        with self.db.session() as session:
            record = FeedbackRecord(
                generation_id=feedback.generation_id,
                rating=feedback.rating,
                comment=feedback.comment,
                usage_count=feedback.usage_count,
                created_at=feedback.created_at,
            )
            session.add(record)
            session.flush()
            feedback.id = record.id
            logger.debug(f"Added feedback for generation: {feedback.generation_id}")
        return feedback

    async def add_async(self, feedback: Feedback) -> Feedback:
        """Add feedback for a generation (async)."""
        async with self.db.async_session() as session:
            record = FeedbackRecord(
                generation_id=feedback.generation_id,
                rating=feedback.rating,
                comment=feedback.comment,
                usage_count=feedback.usage_count,
                created_at=feedback.created_at,
            )
            session.add(record)
            await session.flush()
            feedback.id = record.id
            logger.debug(f"Added feedback for generation: {feedback.generation_id}")
        return feedback

    def get_for_generation(self, generation_id: str) -> list[Feedback]:
        """Get all feedback for a generation."""
        with self.db.session() as session:
            stmt = select(FeedbackRecord).where(
                FeedbackRecord.generation_id == generation_id
            )
            records = session.execute(stmt).scalars().all()
            return [self._to_model(r) for r in records]

    def get_average_rating(self, generation_id: str) -> float | None:
        """Get average rating for a generation."""
        with self.db.session() as session:
            result = session.execute(
                select(func.avg(FeedbackRecord.rating)).where(
                    FeedbackRecord.generation_id == generation_id
                )
            ).scalar()
            return float(result) if result else None

    def get_feedback_count(self, generation_id: str) -> int:
        """Get feedback count for a generation."""
        with self.db.session() as session:
            return (
                session.execute(
                    select(func.count(FeedbackRecord.id)).where(
                        FeedbackRecord.generation_id == generation_id
                    )
                ).scalar()
                or 0
            )

    def _to_model(self, record: FeedbackRecord) -> Feedback:
        """Convert database record to model."""
        return Feedback(
            id=record.id,
            generation_id=record.generation_id,
            rating=record.rating,
            comment=record.comment,
            usage_count=record.usage_count,
            created_at=record.created_at,
        )


class TemplateRepository:
    """Repository for reusable templates.

    Supports vector search for finding similar templates.
    """

    def __init__(self, db: MetaDatabase) -> None:
        self.db = db

    def add(self, template: TemplateSpec) -> TemplateSpec:
        """Add a new template."""
        with self.db.session() as session:
            record = TemplateRecord(
                id=template.id,
                artifact_type=template.artifact_type,
                name=template.name,
                description=template.description,
                content=template.content,
                pattern=template.pattern,
                quality_score=template.quality_score,
                usage_count=template.usage_count,
                source=template.source,
                source_generation_id=template.source_generation_id,
                extra_data=template.extra_data,
                created_at=template.created_at,
                updated_at=template.updated_at,
            )
            session.add(record)
            logger.info(f"Added template: {template.name}")
        return template

    async def add_async(self, template: TemplateSpec) -> TemplateSpec:
        """Add a new template (async)."""
        async with self.db.async_session() as session:
            record = TemplateRecord(
                id=template.id,
                artifact_type=template.artifact_type,
                name=template.name,
                description=template.description,
                content=template.content,
                pattern=template.pattern,
                quality_score=template.quality_score,
                usage_count=template.usage_count,
                source=template.source,
                source_generation_id=template.source_generation_id,
                extra_data=template.extra_data,
                created_at=template.created_at,
                updated_at=template.updated_at,
            )
            session.add(record)
            logger.info(f"Added template: {template.name}")
        return template

    def get(self, id: str) -> TemplateSpec | None:
        """Get template by ID."""
        with self.db.session() as session:
            record = session.get(TemplateRecord, id)
            if record is None:
                return None
            return self._to_model(record)

    def get_by_name(self, name: str) -> TemplateSpec | None:
        """Get template by name."""
        with self.db.session() as session:
            stmt = select(TemplateRecord).where(TemplateRecord.name == name)
            record = session.execute(stmt).scalar_one_or_none()
            if record is None:
                return None
            return self._to_model(record)

    def find_by_type(self, artifact_type: str, limit: int = 20) -> list[TemplateSpec]:
        """Find templates by artifact type."""
        with self.db.session() as session:
            stmt = (
                select(TemplateRecord)
                .where(TemplateRecord.artifact_type == artifact_type)
                .order_by(TemplateRecord.quality_score.desc())
                .limit(limit)
            )
            records = session.execute(stmt).scalars().all()
            return [self._to_model(r) for r in records]

    def find_top_rated(self, limit: int = 10) -> list[TemplateSpec]:
        """Find top-rated templates."""
        with self.db.session() as session:
            stmt = (
                select(TemplateRecord)
                .order_by(TemplateRecord.quality_score.desc())
                .limit(limit)
            )
            records = session.execute(stmt).scalars().all()
            return [self._to_model(r) for r in records]

    def increment_usage(self, id: str) -> None:
        """Increment template usage count."""
        with self.db.session() as session:
            record = session.get(TemplateRecord, id)
            if record:
                record.usage_count += 1
                record.updated_at = datetime.utcnow()

    def update(self, template: TemplateSpec) -> TemplateSpec:
        """Update a template."""
        with self.db.session() as session:
            record = session.get(TemplateRecord, template.id)
            if record is None:
                raise NotFoundError("Template", template.id)

            record.name = template.name
            record.description = template.description
            record.content = template.content
            record.pattern = template.pattern
            record.quality_score = template.quality_score
            record.extra_data = template.extra_data
            record.updated_at = datetime.utcnow()

            template.updated_at = record.updated_at
        return template

    def delete(self, id: str) -> bool:
        """Delete a template."""
        with self.db.session() as session:
            record = session.get(TemplateRecord, id)
            if record is None:
                return False
            session.delete(record)
            return True

    def promote_from_generation(
        self,
        generation: GenerationResult,
        avg_rating: float,
    ) -> TemplateSpec:
        """Promote a high-quality generation to a template.

        Args:
            generation: Generation to promote.
            avg_rating: Average user rating.

        Returns:
            Created template.
        """
        template = TemplateSpec(
            artifact_type=generation.artifact_type,
            name=f"{generation.name}_template",
            description=f"Promoted from generation {generation.id}",
            content=generation.content,
            quality_score=avg_rating,
            source="promoted",
            source_generation_id=generation.id,
            metadata={
                "original_provider": generation.provider,
                "original_model": generation.model,
                "promotion_date": datetime.utcnow().isoformat(),
            },
        )
        return self.add(template)

    def _to_model(self, record: TemplateRecord) -> TemplateSpec:
        """Convert database record to model."""
        return TemplateSpec(
            id=record.id,
            artifact_type=record.artifact_type,
            name=record.name,
            description=record.description,
            content=record.content,
            pattern=record.pattern,
            quality_score=record.quality_score,
            usage_count=record.usage_count,
            source=record.source,
            source_generation_id=record.source_generation_id,
            extra_data=record.extra_data or {},
            created_at=record.created_at,
            updated_at=record.updated_at,
        )


class BestPracticesRepository:
    """Repository for best practices knowledge base."""

    def __init__(self, db: MetaDatabase) -> None:
        self.db = db

    def add(self, practice: BestPractice) -> BestPractice:
        """Add a best practice."""
        with self.db.session() as session:
            record = BestPracticeRecord(
                id=practice.id,
                category=practice.category,
                practice=practice.practice,
                rationale=practice.rationale,
                examples=practice.examples,
                tags=practice.tags,
                priority=practice.priority,
                created_at=practice.created_at,
            )
            session.add(record)
            logger.debug(f"Added best practice: {practice.category}")
        return practice

    def get(self, id: str) -> BestPractice | None:
        """Get best practice by ID."""
        with self.db.session() as session:
            record = session.get(BestPracticeRecord, id)
            if record is None:
                return None
            return self._to_model(record)

    def get_by_category(self, category: str) -> list[BestPractice]:
        """Get practices by category."""
        with self.db.session() as session:
            stmt = (
                select(BestPracticeRecord)
                .where(BestPracticeRecord.category == category)
                .order_by(BestPracticeRecord.priority.desc())
            )
            records = session.execute(stmt).scalars().all()
            return [self._to_model(r) for r in records]

    def search_by_tags(self, tags: list[str]) -> list[BestPractice]:
        """Search practices by tags.

        Note: This is a simple implementation. For PostgreSQL with JSONB,
        more efficient queries can be used.
        """
        with self.db.session() as session:
            stmt = select(BestPracticeRecord)
            records = session.execute(stmt).scalars().all()

            # Filter by tags (simple in-memory filter)
            matching = []
            for record in records:
                record_tags = record.tags or []
                if any(tag in record_tags for tag in tags):
                    matching.append(self._to_model(record))

            return sorted(matching, key=lambda p: p.priority, reverse=True)

    def get_for_context(
        self,
        artifact_type: str,
        context: dict[str, Any] | None = None,
    ) -> list[BestPractice]:
        """Get relevant practices for a generation context.

        Args:
            artifact_type: Type of artifact being generated.
            context: Additional context (domain, complexity, etc.).

        Returns:
            Relevant best practices ordered by priority.
        """
        practices = self.get_by_category(artifact_type)

        # If context provided, filter by tags
        if context:
            tags = context.get("tags", [])
            if tags:
                tag_practices = self.search_by_tags(tags)
                # Combine and deduplicate
                seen = {p.id for p in practices}
                for p in tag_practices:
                    if p.id not in seen:
                        practices.append(p)

        return practices

    def _to_model(self, record: BestPracticeRecord) -> BestPractice:
        """Convert database record to model."""
        return BestPractice(
            id=record.id,
            category=record.category,
            practice=record.practice,
            rationale=record.rationale,
            examples=record.examples or [],
            tags=record.tags or [],
            priority=record.priority,
            created_at=record.created_at,
        )


class CostRepository:
    """Repository for cost tracking."""

    def __init__(self, db: MetaDatabase) -> None:
        self.db = db

    def add(self, entry: CostEntry) -> CostEntry:
        """Add a cost entry."""
        with self.db.session() as session:
            record = CostRecord(
                provider=entry.provider,
                model=entry.model,
                operation=entry.operation,
                cost_usd=entry.cost_usd,
                tokens_input=entry.tokens_input,
                tokens_output=entry.tokens_output,
                generation_id=entry.generation_id,
                created_at=entry.created_at,
            )
            session.add(record)
            session.flush()
            entry.id = record.id
        return entry

    def get_period_cost(self, period: str = "30d") -> float:
        """Get total cost for a period.

        Args:
            period: Period string (e.g., "7d", "30d", "1y").

        Returns:
            Total cost in USD.
        """
        since = self._parse_period(period)
        with self.db.session() as session:
            result = session.execute(
                select(func.sum(CostRecord.cost_usd)).where(
                    CostRecord.created_at >= since
                )
            ).scalar()
            return float(result) if result else 0.0

    def get_report(self, period: str = "30d") -> CostReport:
        """Get detailed cost report.

        Args:
            period: Period string (e.g., "7d", "30d").

        Returns:
            Detailed cost report.
        """
        since = self._parse_period(period)

        with self.db.session() as session:
            # Total cost
            total_cost = (
                session.execute(
                    select(func.sum(CostRecord.cost_usd)).where(
                        CostRecord.created_at >= since
                    )
                ).scalar()
                or 0.0
            )

            # Cost by provider
            by_provider_rows = session.execute(
                select(CostRecord.provider, func.sum(CostRecord.cost_usd))
                .where(CostRecord.created_at >= since)
                .group_by(CostRecord.provider)
            ).all()
            by_provider = {row[0]: float(row[1]) for row in by_provider_rows}

            # Cost by model
            by_model_rows = session.execute(
                select(CostRecord.model, func.sum(CostRecord.cost_usd))
                .where(CostRecord.created_at >= since)
                .group_by(CostRecord.model)
            ).all()
            by_model = {row[0]: float(row[1]) for row in by_model_rows}

            # Cost by operation
            by_op_rows = session.execute(
                select(CostRecord.operation, func.sum(CostRecord.cost_usd))
                .where(CostRecord.created_at >= since)
                .group_by(CostRecord.operation)
            ).all()
            by_operation = {row[0]: float(row[1]) for row in by_op_rows}

            # Token totals
            tokens_input = (
                session.execute(
                    select(func.sum(CostRecord.tokens_input)).where(
                        CostRecord.created_at >= since
                    )
                ).scalar()
                or 0
            )

            tokens_output = (
                session.execute(
                    select(func.sum(CostRecord.tokens_output)).where(
                        CostRecord.created_at >= since
                    )
                ).scalar()
                or 0
            )

            # Generation count
            gen_count = (
                session.execute(
                    select(func.count(CostRecord.generation_id.distinct()))
                    .where(CostRecord.created_at >= since)
                    .where(CostRecord.generation_id.isnot(None))
                ).scalar()
                or 0
            )

            return CostReport(
                period=period,
                total_cost=float(total_cost),
                by_provider=by_provider,
                by_model=by_model,
                by_operation=by_operation,
                total_tokens_input=int(tokens_input),
                total_tokens_output=int(tokens_output),
                generation_count=int(gen_count),
            )

    def get_daily_cost(self, days: int = 30) -> list[tuple[str, float]]:
        """Get daily cost breakdown.

        Args:
            days: Number of days.

        Returns:
            List of (date, cost) tuples.
        """
        since = datetime.utcnow() - timedelta(days=days)

        with self.db.session() as session:
            # SQLite vs PostgreSQL date formatting
            if self.db.is_postgres:
                date_expr = func.date(CostRecord.created_at)
            else:
                date_expr = func.strftime("%Y-%m-%d", CostRecord.created_at)

            rows = session.execute(
                select(date_expr, func.sum(CostRecord.cost_usd))
                .where(CostRecord.created_at >= since)
                .group_by(date_expr)
                .order_by(date_expr)
            ).all()

            return [(str(row[0]), float(row[1])) for row in rows]

    def _parse_period(self, period: str) -> datetime:
        """Parse period string to datetime."""
        now = datetime.utcnow()
        if period.endswith("d"):
            days = int(period[:-1])
            return now - timedelta(days=days)
        elif period.endswith("w"):
            weeks = int(period[:-1])
            return now - timedelta(weeks=weeks)
        elif period.endswith("m"):
            months = int(period[:-1])
            return now - timedelta(days=months * 30)
        elif period.endswith("y"):
            years = int(period[:-1])
            return now - timedelta(days=years * 365)
        else:
            return now - timedelta(days=30)


class MemoryRepository:
    """Repository for persistent context memory."""

    def __init__(self, db: MetaDatabase) -> None:
        self.db = db

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> MemoryEntry:
        """Set a memory entry.

        Args:
            key: Unique key.
            value: Value to store (must be JSON-serializable).
            ttl_seconds: Time-to-live in seconds (None = no expiry).

        Returns:
            Created memory entry.
        """
        expires_at = None
        if ttl_seconds:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

        entry = MemoryEntry(
            key=key,
            value=value,
            ttl_seconds=ttl_seconds,
            expires_at=expires_at,
        )

        with self.db.session() as session:
            # Upsert: delete existing then insert
            existing = session.execute(
                select(MemoryItem).where(MemoryItem.key == key)
            ).scalar_one_or_none()

            if existing:
                session.delete(existing)

            record = MemoryItem(
                id=entry.id,
                key=entry.key,
                value=entry.value,
                ttl_seconds=entry.ttl_seconds,
                created_at=entry.created_at,
                expires_at=entry.expires_at,
            )
            session.add(record)

        return entry

    def get(self, key: str) -> Any | None:
        """Get a memory value by key.

        Returns None if not found or expired.
        """
        with self.db.session() as session:
            record = session.execute(
                select(MemoryItem).where(MemoryItem.key == key)
            ).scalar_one_or_none()

            if record is None:
                return None

            # Check expiry
            if record.expires_at and record.expires_at < datetime.utcnow():
                session.delete(record)
                return None

            return record.value

    def delete(self, key: str) -> bool:
        """Delete a memory entry."""
        with self.db.session() as session:
            record = session.execute(
                select(MemoryItem).where(MemoryItem.key == key)
            ).scalar_one_or_none()

            if record is None:
                return False

            session.delete(record)
            return True

    def list_keys(self, prefix: str | None = None) -> list[str]:
        """List all keys, optionally filtered by prefix."""
        with self.db.session() as session:
            stmt = select(MemoryItem.key)

            if prefix:
                stmt = stmt.where(MemoryItem.key.like(f"{prefix}%"))

            rows = session.execute(stmt).all()
            return [row[0] for row in rows]

    def clear_expired(self) -> int:
        """Clear all expired entries.

        Returns:
            Number of entries cleared.
        """
        with self.db.session() as session:
            now = datetime.utcnow()
            expired = (
                session.execute(
                    select(MemoryItem)
                    .where(MemoryItem.expires_at.isnot(None))
                    .where(MemoryItem.expires_at < now)
                )
                .scalars()
                .all()
            )

            count = len(expired)
            for record in expired:
                session.delete(record)

            return count


class ContextRepository:
    """Repository for conversation context history."""

    def __init__(self, db: MetaDatabase) -> None:
        self.db = db

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a message to context history."""
        with self.db.session() as session:
            record = ContextHistory(
                session_id=session_id,
                role=role,
                content=content,
                metadata=metadata or {},
            )
            session.add(record)

    def get_history(
        self,
        session_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get conversation history for a session."""
        with self.db.session() as session:
            stmt = (
                select(ContextHistory)
                .where(ContextHistory.session_id == session_id)
                .order_by(ContextHistory.created_at.asc())
                .limit(limit)
            )
            records = session.execute(stmt).scalars().all()

            return [
                {
                    "role": r.role,
                    "content": r.content,
                    "extra_data": r.extra_data,
                    "created_at": r.created_at.isoformat(),
                }
                for r in records
            ]

    def clear_session(self, session_id: str) -> int:
        """Clear all messages for a session."""
        with self.db.session() as session:
            records = (
                session.execute(
                    select(ContextHistory).where(
                        ContextHistory.session_id == session_id
                    )
                )
                .scalars()
                .all()
            )

            count = len(records)
            for record in records:
                session.delete(record)

            return count
