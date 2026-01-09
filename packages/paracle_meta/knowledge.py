"""Best Practices Knowledge Base for Paracle Meta-Agent.

Contains built-in knowledge about Paracle patterns, conventions,
and best practices for artifact generation.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from paracle_core.logging import get_logger
from pydantic import BaseModel, Field

logger = get_logger(__name__)


class BestPractice(BaseModel):
    """A best practice recommendation."""

    id: str = Field(..., description="Unique practice ID")
    category: str = Field(
        ..., description="Category: agent, workflow, skill, policy, general"
    )
    pattern: str = Field(..., description="Pattern this practice applies to")
    title: str = Field(..., description="Short title")
    recommendation: str = Field(..., description="The recommendation")
    rationale: str = Field(default="", description="Why this is recommended")
    examples: list[str] = Field(
        default_factory=list, description="Example implementations"
    )
    confidence: float = Field(default=0.8, description="Confidence score 0-1")
    source: str = Field(default="built-in", description="Source of this practice")
    usage_count: int = Field(default=0, description="Times this was used")
    success_rate: float = Field(default=0.0, description="Success rate when applied")
    created_at: datetime = Field(default_factory=datetime.now)


class BestPracticesDatabase:
    """Database of best practices for artifact generation.

    Contains:
    - Built-in Paracle conventions
    - Learned patterns from successful generations
    - User-contributed practices

    Example:
        >>> db = BestPracticesDatabase()
        >>>
        >>> # Get practices for agent generation
        >>> practices = await db.get_for("agent")
        >>> for p in practices:
        ...     print(f"- {p.title}: {p.recommendation}")
        >>>
        >>> # Add new practice from learning
        >>> await db.add(practice)
    """

    # Built-in best practices
    BUILTIN_PRACTICES: list[dict[str, Any]] = [
        # Agent best practices
        {
            "id": "agent_clear_role",
            "category": "agent",
            "pattern": "all",
            "title": "Clear Role Definition",
            "recommendation": "Define a specific, focused role for each agent. "
            "Avoid generic roles like 'helper' or 'assistant'.",
            "rationale": "Specific roles lead to better task execution and clearer boundaries.",
            "examples": [
                "Role: Security code auditor specialized in Python vulnerabilities",
                "Role: Technical documentation writer for API references",
            ],
            "confidence": 0.95,
        },
        {
            "id": "agent_system_prompt",
            "category": "agent",
            "pattern": "all",
            "title": "Effective System Prompt",
            "recommendation": "Include: role context, capabilities, constraints, "
            "output format expectations in system prompt.",
            "rationale": "Comprehensive system prompts improve output quality and consistency.",
            "examples": [
                "You are a code reviewer. Review code for: bugs, security issues, "
                "performance problems. Output: markdown with issues and fixes.",
            ],
            "confidence": 0.9,
        },
        {
            "id": "agent_tools_minimal",
            "category": "agent",
            "pattern": "all",
            "title": "Minimal Tools",
            "recommendation": "Assign only the tools an agent needs for its role. "
            "Too many tools can confuse the model.",
            "rationale": "Focused tool sets lead to better tool usage decisions.",
            "examples": [
                "CodeReviewer: read_file, grep, static_analysis",
                "DocumentWriter: read_file, write_file, markdown_lint",
            ],
            "confidence": 0.85,
        },
        {
            "id": "agent_temperature",
            "category": "agent",
            "pattern": "all",
            "title": "Appropriate Temperature",
            "recommendation": "Use low temperature (0.0-0.3) for deterministic tasks, "
            "higher (0.5-0.8) for creative tasks.",
            "rationale": "Temperature affects output consistency and creativity.",
            "examples": [
                "Code review: temperature=0.1",
                "Story generation: temperature=0.7",
                "Security audit: temperature=0.0",
            ],
            "confidence": 0.9,
        },
        # Workflow best practices
        {
            "id": "workflow_dag_structure",
            "category": "workflow",
            "pattern": "all",
            "title": "DAG Structure",
            "recommendation": "Structure workflows as DAGs with clear dependencies. "
            "Use depends_on to define execution order.",
            "rationale": "DAG structure enables parallel execution and clear dependencies.",
            "examples": [
                "steps:\n  - id: analyze\n  - id: review\n    depends_on: [analyze]",
            ],
            "confidence": 0.95,
        },
        {
            "id": "workflow_error_handling",
            "category": "workflow",
            "pattern": "all",
            "title": "Error Handling",
            "recommendation": "Include error handling steps or rollback mechanisms "
            "for critical workflows.",
            "rationale": "Graceful failure handling prevents data corruption.",
            "examples": [
                "on_failure: rollback_step",
                "retry: { max_attempts: 3, backoff: exponential }",
            ],
            "confidence": 0.85,
        },
        {
            "id": "workflow_approval_gates",
            "category": "workflow",
            "pattern": "production deployment",
            "title": "Approval Gates",
            "recommendation": "Add human approval gates before critical operations "
            "like production deployments.",
            "rationale": "Human oversight prevents costly mistakes.",
            "examples": [
                "- id: approve\n  type: approval\n  required_approvers: ['lead']",
            ],
            "confidence": 0.9,
        },
        # Skill best practices
        {
            "id": "skill_single_responsibility",
            "category": "skill",
            "pattern": "all",
            "title": "Single Responsibility",
            "recommendation": "Each skill should do one thing well. "
            "Combine skills for complex behaviors.",
            "rationale": "Single-purpose skills are more reusable and testable.",
            "examples": [
                "skill: security-scanning (not: security-and-testing)",
                "skill: api-documentation (not: documentation-everything)",
            ],
            "confidence": 0.9,
        },
        {
            "id": "skill_examples_required",
            "category": "skill",
            "pattern": "all",
            "title": "Include Examples",
            "recommendation": "Every skill should include 2-3 concrete examples "
            "showing how to use it.",
            "rationale": "Examples help agents understand how to apply skills.",
            "examples": [
                "examples:\n  - input: 'Scan auth.py'\n    output: '[3 issues found]'",
            ],
            "confidence": 0.85,
        },
        # Policy best practices
        {
            "id": "policy_measurable_rules",
            "category": "policy",
            "pattern": "all",
            "title": "Measurable Rules",
            "recommendation": "Define rules that can be automatically verified. "
            "Avoid subjective criteria.",
            "rationale": "Measurable rules enable automated enforcement.",
            "examples": [
                "rule: code_coverage >= 80%",
                "rule: no secrets in code (detected by scanner)",
            ],
            "confidence": 0.9,
        },
        {
            "id": "policy_enforcement_levels",
            "category": "policy",
            "pattern": "all",
            "title": "Enforcement Levels",
            "recommendation": "Specify enforcement level: 'warn', 'block', or 'audit'. "
            "Not all violations need blocking.",
            "rationale": "Flexible enforcement reduces friction while maintaining safety.",
            "examples": [
                "security_violation: block",
                "style_violation: warn",
                "coverage_low: audit",
            ],
            "confidence": 0.85,
        },
        # General best practices
        {
            "id": "general_yaml_formatting",
            "category": "general",
            "pattern": "all",
            "title": "YAML Formatting",
            "recommendation": "Use consistent YAML formatting: 2-space indent, "
            "no trailing spaces, blank line between sections.",
            "rationale": "Consistent formatting improves readability and reduces errors.",
            "examples": [
                "agent:\n  name: reviewer\n  model: gpt-4\n\n  tools:\n    - read_file",
            ],
            "confidence": 0.8,
        },
        {
            "id": "general_naming_conventions",
            "category": "general",
            "pattern": "all",
            "title": "Naming Conventions",
            "recommendation": "Use snake_case for IDs, PascalCase for agent names, "
            "kebab-case for skills.",
            "rationale": "Consistent naming improves discoverability and prevents conflicts.",
            "examples": [
                "agent: SecurityAuditor",
                "workflow_id: security_review",
                "skill: security-hardening",
            ],
            "confidence": 0.85,
        },
    ]

    def __init__(self, db_path: Path | None = None):
        """Initialize best practices database.

        Args:
            db_path: Path to database file
        """
        self.db_path = db_path or self._default_db_path()
        self._init_database()
        self._load_builtins()
        logger.debug(
            "BestPracticesDatabase initialized", extra={"db": str(self.db_path)}
        )

    async def get_for(
        self,
        category: str,
        pattern: str | None = None,
        limit: int = 20,
    ) -> list[BestPractice]:
        """Get best practices for a category.

        Args:
            category: Category to get practices for
            pattern: Optional pattern to filter by
            limit: Maximum number of practices

        Returns:
            List of best practices
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if pattern:
            cursor.execute(
                """
                SELECT id, category, pattern, title, recommendation, rationale,
                       examples, confidence, source, usage_count, success_rate, created_at
                FROM best_practices
                WHERE category = ? AND (pattern = ? OR pattern = 'all')
                ORDER BY confidence DESC, usage_count DESC
                LIMIT ?
            """,
                (category, pattern, limit),
            )
        else:
            cursor.execute(
                """
                SELECT id, category, pattern, title, recommendation, rationale,
                       examples, confidence, source, usage_count, success_rate, created_at
                FROM best_practices
                WHERE category = ? OR category = 'general'
                ORDER BY confidence DESC, usage_count DESC
                LIMIT ?
            """,
                (category, limit),
            )

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_practice(row) for row in rows]

    async def add(self, practice: BestPractice) -> str:
        """Add a best practice.

        Args:
            practice: Best practice to add

        Returns:
            Practice ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO best_practices (
                id, category, pattern, title, recommendation, rationale,
                examples, confidence, source, usage_count, success_rate, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                practice.id,
                practice.category,
                practice.pattern,
                practice.title,
                practice.recommendation,
                practice.rationale,
                "|".join(practice.examples),
                practice.confidence,
                practice.source,
                practice.usage_count,
                practice.success_rate,
                practice.created_at.isoformat(),
            ),
        )

        conn.commit()
        conn.close()

        logger.info(f"Added best practice: {practice.id}")
        return practice.id

    async def update_usage(self, practice_id: str, success: bool = True) -> None:
        """Update usage statistics for a practice.

        Args:
            practice_id: Practice ID
            success: Whether usage was successful
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get current stats
        cursor.execute(
            "SELECT usage_count, success_rate FROM best_practices WHERE id = ?",
            (practice_id,),
        )
        row = cursor.fetchone()

        if row:
            usage_count, success_rate = row
            new_usage = usage_count + 1
            # Update success rate as moving average
            new_success_rate = (
                success_rate * usage_count + (1 if success else 0)
            ) / new_usage

            cursor.execute(
                """
                UPDATE best_practices
                SET usage_count = ?, success_rate = ?
                WHERE id = ?
            """,
                (new_usage, new_success_rate, practice_id),
            )

        conn.commit()
        conn.close()

    async def count(self) -> int:
        """Count total best practices.

        Returns:
            Number of practices
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM best_practices")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    async def get_prompt_context(self, category: str) -> str:
        """Get best practices as prompt context.

        Args:
            category: Category to get practices for

        Returns:
            Formatted string for inclusion in LLM prompt
        """
        practices = await self.get_for(category, limit=10)

        if not practices:
            return ""

        lines = ["## Best Practices", ""]
        for p in practices:
            lines.append(f"### {p.title}")
            lines.append(p.recommendation)
            if p.examples:
                lines.append("")
                lines.append("Example:")
                lines.append(f"```\n{p.examples[0]}\n```")
            lines.append("")

        return "\n".join(lines)

    def _row_to_practice(self, row: tuple) -> BestPractice:
        """Convert database row to BestPractice."""
        return BestPractice(
            id=row[0],
            category=row[1],
            pattern=row[2],
            title=row[3],
            recommendation=row[4],
            rationale=row[5],
            examples=row[6].split("|") if row[6] else [],
            confidence=row[7],
            source=row[8],
            usage_count=row[9],
            success_rate=row[10],
            created_at=datetime.fromisoformat(row[11]),
        )

    def _init_database(self) -> None:
        """Initialize database schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS best_practices (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                pattern TEXT NOT NULL,
                title TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                rationale TEXT,
                examples TEXT,
                confidence REAL DEFAULT 0.8,
                source TEXT DEFAULT 'built-in',
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                created_at TEXT NOT NULL
            )
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_practices_category
            ON best_practices(category)
        """
        )

        conn.commit()
        conn.close()

    def _load_builtins(self) -> None:
        """Load built-in best practices."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for practice_data in self.BUILTIN_PRACTICES:
            practice = BestPractice(**practice_data)

            cursor.execute(
                """
                INSERT OR IGNORE INTO best_practices (
                    id, category, pattern, title, recommendation, rationale,
                    examples, confidence, source, usage_count, success_rate, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    practice.id,
                    practice.category,
                    practice.pattern,
                    practice.title,
                    practice.recommendation,
                    practice.rationale,
                    "|".join(practice.examples),
                    practice.confidence,
                    practice.source,
                    practice.usage_count,
                    practice.success_rate,
                    practice.created_at.isoformat(),
                ),
            )

        conn.commit()
        conn.close()

        logger.debug(f"Loaded {len(self.BUILTIN_PRACTICES)} built-in best practices")

    def _default_db_path(self) -> Path:
        """Get default database path."""
        return Path.cwd() / ".parac" / "memory" / "data" / "best_practices.db"


__all__ = [
    "BestPractice",
    "BestPracticesDatabase",
]
