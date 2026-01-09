"""Template Library and Evolution for Paracle Meta-Agent.

Manages reusable templates learned from successful generations.
Templates evolve based on user feedback and usage patterns.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from paracle_core.logging import get_logger
from pydantic import BaseModel, Field

from paracle_meta.exceptions import TemplateNotFoundError

logger = get_logger(__name__)


class Template(BaseModel):
    """A reusable generation template."""

    id: str = Field(..., description="Unique template ID")
    artifact_type: str = Field(..., description="Type: agent, workflow, skill, policy")
    pattern: str = Field(..., description="Pattern/category this template matches")
    name: str = Field(..., description="Template name")
    content: str = Field(..., description="Template content")
    quality_score: float = Field(default=0.0, description="Quality score 0-10")
    usage_count: int = Field(default=0, description="Number of times used")
    avg_rating: float = Field(default=0.0, description="Average user rating")
    success_rate: float = Field(default=0.0, description="Success rate 0-1")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    source: str = Field(default="generated", description="How template was created")
    version: int = Field(default=1, description="Template version")
    metadata: dict[str, Any] = Field(default_factory=dict)

    def customize(
        self,
        name: str,
        description: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Customize template for a specific request.

        Args:
            name: Artifact name
            description: Artifact description
            context: Additional context

        Returns:
            Customized content
        """
        content = self.content

        # Replace placeholders
        content = content.replace("{{name}}", name)
        content = content.replace("{{NAME}}", name.upper())
        content = content.replace("{{description}}", description)

        # Replace context placeholders
        if context:
            for key, value in context.items():
                content = content.replace(f"{{{{{key}}}}}", str(value))

        return content


class TemplateMatch(BaseModel):
    """Result of template matching."""

    template: Template
    similarity_score: float = Field(..., description="Similarity score 0-1")
    match_reason: str = Field(..., description="Why this template matched")


class TemplateLibrary:
    """Library of reusable templates.

    Manages templates for:
    - Agent specifications
    - Workflow definitions
    - Skill definitions
    - Policy definitions

    Example:
        >>> library = TemplateLibrary()
        >>>
        >>> # Find similar template
        >>> match = await library.find_similar(
        ...     artifact_type="agent",
        ...     description="security auditor"
        ... )
        >>> if match and match.quality_score > 9.0:
        ...     content = match.customize(name="MySecurityAgent", ...)
        >>>
        >>> # Save new template
        >>> await library.save(template)
    """

    def __init__(self, db_path: Path | None = None):
        """Initialize template library.

        Args:
            db_path: Path to template database
        """
        self.db_path = db_path or self._default_db_path()
        self._init_database()
        logger.debug("TemplateLibrary initialized", extra={"db": str(self.db_path)})

    async def find_similar(
        self,
        artifact_type: str,
        description: str,
        min_quality: float = 7.0,
    ) -> Template | None:
        """Find a similar template for a description.

        Args:
            artifact_type: Type of artifact
            description: Description to match against
            min_quality: Minimum quality score required

        Returns:
            Best matching template or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get templates of matching type with good quality
        cursor.execute(
            """
            SELECT id, artifact_type, pattern, name, content, quality_score,
                   usage_count, avg_rating, success_rate, created_at, updated_at,
                   source, version, metadata
            FROM templates
            WHERE artifact_type = ? AND quality_score >= ?
            ORDER BY quality_score DESC, usage_count DESC
            LIMIT 20
        """,
            (artifact_type, min_quality),
        )

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return None

        # Simple keyword matching
        description_words = set(description.lower().split())

        best_match = None
        best_score = 0.0

        for row in rows:
            template = self._row_to_template(row)

            # Calculate similarity based on pattern matching
            pattern_words = set(template.pattern.lower().split())
            overlap = len(description_words & pattern_words)
            total = len(description_words | pattern_words)
            similarity = overlap / total if total > 0 else 0

            # Weight by quality and usage
            weighted_score = (
                similarity * 0.6
                + template.quality_score / 10 * 0.3
                + min(template.usage_count / 100, 1) * 0.1
            )

            if weighted_score > best_score:
                best_score = weighted_score
                best_match = template

        return best_match

    async def save(self, template: Template) -> str:
        """Save a template to the library.

        Args:
            template: Template to save

        Returns:
            Template ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO templates (
                id, artifact_type, pattern, name, content, quality_score,
                usage_count, avg_rating, success_rate, created_at, updated_at,
                source, version, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                template.id,
                template.artifact_type,
                template.pattern,
                template.name,
                template.content,
                template.quality_score,
                template.usage_count,
                template.avg_rating,
                template.success_rate,
                template.created_at.isoformat(),
                datetime.now().isoformat(),
                template.source,
                template.version,
                str(template.metadata),
            ),
        )

        conn.commit()
        conn.close()

        logger.info(
            f"Saved template: {template.id}", extra={"type": template.artifact_type}
        )
        return template.id

    async def get(self, template_id: str) -> Template:
        """Get a template by ID.

        Args:
            template_id: Template ID

        Returns:
            Template

        Raises:
            TemplateNotFoundError: If template not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, artifact_type, pattern, name, content, quality_score,
                   usage_count, avg_rating, success_rate, created_at, updated_at,
                   source, version, metadata
            FROM templates WHERE id = ?
        """,
            (template_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise TemplateNotFoundError(template_id)

        return self._row_to_template(row)

    async def list_templates(
        self,
        artifact_type: str | None = None,
        min_quality: float = 0.0,
        limit: int = 50,
    ) -> list[Template]:
        """List templates.

        Args:
            artifact_type: Filter by artifact type
            min_quality: Minimum quality score
            limit: Maximum number of templates

        Returns:
            List of templates
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if artifact_type:
            cursor.execute(
                """
                SELECT id, artifact_type, pattern, name, content, quality_score,
                       usage_count, avg_rating, success_rate, created_at, updated_at,
                       source, version, metadata
                FROM templates
                WHERE artifact_type = ? AND quality_score >= ?
                ORDER BY quality_score DESC, usage_count DESC
                LIMIT ?
            """,
                (artifact_type, min_quality, limit),
            )
        else:
            cursor.execute(
                """
                SELECT id, artifact_type, pattern, name, content, quality_score,
                       usage_count, avg_rating, success_rate, created_at, updated_at,
                       source, version, metadata
                FROM templates
                WHERE quality_score >= ?
                ORDER BY quality_score DESC, usage_count DESC
                LIMIT ?
            """,
                (min_quality, limit),
            )

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_template(row) for row in rows]

    async def update_usage(self, template_id: str) -> None:
        """Update usage count for a template.

        Args:
            template_id: Template ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE templates
            SET usage_count = usage_count + 1, updated_at = ?
            WHERE id = ?
        """,
            (datetime.now().isoformat(), template_id),
        )

        conn.commit()
        conn.close()

    async def update_rating(self, template_id: str, rating: float) -> None:
        """Update average rating for a template.

        Args:
            template_id: Template ID
            rating: New rating to incorporate
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get current stats
        cursor.execute(
            "SELECT usage_count, avg_rating FROM templates WHERE id = ?",
            (template_id,),
        )
        row = cursor.fetchone()
        if row:
            usage, avg = row
            # Calculate new average
            new_avg = (avg * usage + rating) / (usage + 1) if usage > 0 else rating

            cursor.execute(
                """
                UPDATE templates
                SET avg_rating = ?, updated_at = ?
                WHERE id = ?
            """,
                (new_avg, datetime.now().isoformat(), template_id),
            )

        conn.commit()
        conn.close()

    async def count(self) -> int:
        """Count total templates.

        Returns:
            Number of templates
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM templates")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def _row_to_template(self, row: tuple) -> Template:
        """Convert database row to Template."""
        return Template(
            id=row[0],
            artifact_type=row[1],
            pattern=row[2],
            name=row[3],
            content=row[4],
            quality_score=row[5],
            usage_count=row[6],
            avg_rating=row[7],
            success_rate=row[8],
            created_at=datetime.fromisoformat(row[9]),
            updated_at=datetime.fromisoformat(row[10]),
            source=row[11],
            version=row[12],
            metadata=eval(row[13]) if row[13] else {},
        )

    def _init_database(self) -> None:
        """Initialize template database."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS templates (
                id TEXT PRIMARY KEY,
                artifact_type TEXT NOT NULL,
                pattern TEXT NOT NULL,
                name TEXT NOT NULL,
                content TEXT NOT NULL,
                quality_score REAL DEFAULT 0,
                usage_count INTEGER DEFAULT 0,
                avg_rating REAL DEFAULT 0,
                success_rate REAL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                source TEXT DEFAULT 'generated',
                version INTEGER DEFAULT 1,
                metadata TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_templates_type
            ON templates(artifact_type)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_templates_quality
            ON templates(quality_score)
        """
        )

        conn.commit()
        conn.close()

    def _default_db_path(self) -> Path:
        """Get default database path."""
        return Path.cwd() / ".parac" / "memory" / "data" / "meta_templates.db"


class TemplateEvolution:
    """Evolves templates based on feedback and usage.

    Implements:
    - Template promotion (successful patterns → templates)
    - Template versioning
    - Quality improvement over time
    """

    def __init__(
        self,
        library: TemplateLibrary,
        min_samples: int = 5,
        min_rating: float = 4.0,
        min_quality: float = 8.0,
    ):
        """Initialize template evolution.

        Args:
            library: TemplateLibrary instance
            min_samples: Minimum samples before promotion
            min_rating: Minimum average rating for promotion
            min_quality: Minimum quality score for promotion
        """
        self.library = library
        self.min_samples = min_samples
        self.min_rating = min_rating
        self.min_quality = min_quality
        logger.debug("TemplateEvolution initialized")

    async def check_for_promotion(
        self,
        generation_id: str,
        artifact_type: str,
        name: str,
        content: str,
        quality_score: float,
        feedback_count: int,
        avg_rating: float,
    ) -> Template | None:
        """Check if a generation should be promoted to template.

        Args:
            generation_id: ID of the generation
            artifact_type: Type of artifact
            name: Artifact name
            content: Generated content
            quality_score: Quality score
            feedback_count: Number of feedback entries
            avg_rating: Average user rating

        Returns:
            Created template if promoted, None otherwise
        """
        # Check promotion criteria
        if feedback_count < self.min_samples:
            logger.debug(
                f"Not enough samples for promotion: {feedback_count} < {self.min_samples}"
            )
            return None

        if avg_rating < self.min_rating:
            logger.debug(
                f"Rating too low for promotion: {avg_rating} < {self.min_rating}"
            )
            return None

        if quality_score < self.min_quality:
            logger.debug(
                f"Quality too low for promotion: {quality_score} < {self.min_quality}"
            )
            return None

        # Create template
        template = Template(
            id=f"tmpl_{artifact_type}_{name}_{datetime.now().strftime('%Y%m%d')}",
            artifact_type=artifact_type,
            pattern=self._extract_pattern(name, content),
            name=name,
            content=self._templatize(content),
            quality_score=quality_score,
            usage_count=1,
            avg_rating=avg_rating,
            success_rate=1.0,
            source="promotion",
            metadata={
                "promoted_from": generation_id,
                "feedback_count": feedback_count,
            },
        )

        await self.library.save(template)

        logger.info(
            f"Promoted to template: {template.id}",
            extra={
                "artifact_type": artifact_type,
                "quality": quality_score,
                "rating": avg_rating,
            },
        )

        return template

    async def evolve_template(
        self,
        template_id: str,
        improved_content: str,
        new_quality: float,
    ) -> Template:
        """Create an evolved version of a template.

        Args:
            template_id: ID of template to evolve
            improved_content: Improved content
            new_quality: New quality score

        Returns:
            New template version
        """
        original = await self.library.get(template_id)

        # Create new version
        new_template = Template(
            id=f"{original.id}_v{original.version + 1}",
            artifact_type=original.artifact_type,
            pattern=original.pattern,
            name=original.name,
            content=improved_content,
            quality_score=new_quality,
            usage_count=0,
            avg_rating=0.0,
            success_rate=0.0,
            source="evolution",
            version=original.version + 1,
            metadata={
                "evolved_from": original.id,
                "previous_quality": original.quality_score,
            },
        )

        await self.library.save(new_template)

        logger.info(
            f"Evolved template: {template_id} → {new_template.id}",
            extra={
                "quality_change": f"{original.quality_score} → {new_quality}",
                "version": new_template.version,
            },
        )

        return new_template

    def _extract_pattern(self, name: str, content: str) -> str:
        """Extract pattern description from content."""
        # Simple pattern extraction based on name and keywords
        patterns = []

        name_lower = name.lower()
        content_lower = content.lower()

        # Detect common patterns
        if "security" in name_lower or "security" in content_lower:
            patterns.append("security")
        if "test" in name_lower or "test" in content_lower:
            patterns.append("testing")
        if "deploy" in name_lower or "deploy" in content_lower:
            patterns.append("deployment")
        if "code" in name_lower or "code" in content_lower:
            patterns.append("code")
        if "review" in name_lower or "review" in content_lower:
            patterns.append("review")
        if "audit" in name_lower or "audit" in content_lower:
            patterns.append("audit")

        return " ".join(patterns) if patterns else name_lower

    def _templatize(self, content: str) -> str:
        """Convert content to template with placeholders."""
        # This is a simple implementation
        # In production, you'd use more sophisticated templating
        return content


__all__ = [
    "Template",
    "TemplateMatch",
    "TemplateLibrary",
    "TemplateEvolution",
]
