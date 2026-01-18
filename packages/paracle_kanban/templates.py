"""Task templates for reusable task patterns.

This module provides task template functionality for creating
standardized tasks from predefined patterns.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from paracle_domain.models import generate_id
from pydantic import BaseModel, Field

from paracle_kanban.task import Task, TaskPriority, TaskType


class TaskTemplate(BaseModel):
    """Task template model.

    Attributes:
        id: Unique template identifier
        name: Template name
        description: Template description
        title_template: Template for task title (supports variables)
        description_template: Template for task description
        task_type: Default task type
        priority: Default priority
        estimated_hours: Default estimated hours
        tags: Default tags
        labels: Default labels
        custom_fields: Default custom fields
        checklist: Checklist items
        subtasks: Subtask templates
        created_at: When template was created
        updated_at: When template was last updated
        category: Template category
        variables: Template variables with descriptions
    """

    id: str = Field(default_factory=lambda: generate_id("template"))
    name: str
    description: str = ""
    title_template: str
    description_template: str = ""
    task_type: TaskType = TaskType.FEATURE
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_hours: float | None = None
    tags: list[str] = Field(default_factory=list)
    labels: list[dict[str, str]] = Field(default_factory=list)
    custom_fields: dict[str, Any] = Field(default_factory=dict)
    checklist: list[str] = Field(default_factory=list)
    subtasks: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    category: str = "general"
    variables: dict[str, str] = Field(
        default_factory=dict
    )  # {"var_name": "description"}

    class Config:
        """Pydantic configuration."""

        use_enum_values = True

    def create_task(
        self, board_id: str, variables: dict[str, str] | None = None
    ) -> Task:
        """Create a task from this template.

        Args:
            board_id: Board to create task in
            variables: Variable values to substitute

        Returns:
            Created task
        """
        variables = variables or {}

        # Substitute variables in title and description
        title = self.title_template
        description = self.description_template

        for var_name, var_value in variables.items():
            title = title.replace(f"{{{var_name}}}", var_value)
            description = description.replace(f"{{{var_name}}}", var_value)

        # Create task
        task = Task(
            board_id=board_id,
            title=title,
            description=description,
            task_type=self.task_type,
            priority=self.priority,
            estimated_hours=self.estimated_hours,
            tags=self.tags.copy(),
            labels=[label.copy() for label in self.labels],
            custom_fields=self.custom_fields.copy(),
            template_id=self.id,
        )

        # Add checklist to metadata
        if self.checklist:
            task.metadata["checklist"] = [
                {"item": item, "completed": False} for item in self.checklist
            ]

        return task


# Predefined templates
BUILTIN_TEMPLATES = [
    TaskTemplate(
        name="Bug Report",
        title_template="[BUG] {summary}",
        description_template=(
            "## Bug Description\n{description}\n\n"
            "## Steps to Reproduce\n{steps}\n\n"
            "## Expected Behavior\n{expected}\n\n"
            "## Actual Behavior\n{actual}\n\n"
            "## Environment\n{environment}"
        ),
        task_type=TaskType.BUG,
        priority=TaskPriority.HIGH,
        tags=["bug"],
        labels=[{"name": "bug", "color": "#d73a4a"}],
        category="development",
        variables={
            "summary": "Brief bug summary",
            "description": "Detailed description",
            "steps": "Steps to reproduce",
            "expected": "Expected behavior",
            "actual": "Actual behavior",
            "environment": "OS, version, etc.",
        },
    ),
    TaskTemplate(
        name="Feature Request",
        title_template="[FEATURE] {title}",
        description_template=(
            "## User Story\nAs a {user_type}, I want to {action}"
            " so that {benefit}.\n\n"
            "## Acceptance Criteria\n{criteria}\n\n"
            "## Additional Context\n{context}"
        ),
        task_type=TaskType.FEATURE,
        priority=TaskPriority.MEDIUM,
        tags=["feature"],
        labels=[{"name": "enhancement", "color": "#a2eeef"}],
        category="development",
        variables={
            "title": "Feature title",
            "user_type": "User type",
            "action": "Desired action",
            "benefit": "Expected benefit",
            "criteria": "Acceptance criteria",
            "context": "Additional context",
        },
    ),
    TaskTemplate(
        name="Code Review",
        title_template="Review: {pr_title}",
        description_template=(
            "## PR Information\n"
            "PR: {pr_link}\n"
            "Author: {author}\n\n"
            "## Review Checklist\n"
            "- Code quality\n"
            "- Test coverage\n"
            "- Documentation\n"
            "- Security considerations\n"
            "- Performance impact"
        ),
        task_type=TaskType.CHORE,
        priority=TaskPriority.HIGH,
        estimated_hours=2.0,
        tags=["review", "code-quality"],
        labels=[{"name": "review", "color": "#fbca04"}],
        category="quality",
        checklist=[
            "Check code quality",
            "Verify test coverage",
            "Review documentation",
            "Check security",
            "Assess performance",
        ],
        variables={
            "pr_title": "Pull request title",
            "pr_link": "Pull request URL",
            "author": "PR author",
        },
    ),
    TaskTemplate(
        name="Documentation Update",
        title_template="Docs: {topic}",
        description_template=(
            "## Documentation Task\n{description}\n\n"
            "## Files to Update\n{files}\n\n"
            "## Sections\n{sections}"
        ),
        task_type=TaskType.DOCS,
        priority=TaskPriority.LOW,
        estimated_hours=1.0,
        tags=["documentation"],
        labels=[{"name": "docs", "color": "#0075ca"}],
        category="documentation",
        variables={
            "topic": "Documentation topic",
            "description": "What needs to be documented",
            "files": "Files to update",
            "sections": "Sections to add/modify",
        },
    ),
    TaskTemplate(
        name="Test Implementation",
        title_template="Tests: {component}",
        description_template=(
            "## Component\n{component}\n\n"
            "## Test Types\n{test_types}\n\n"
            "## Coverage Target\n{coverage}%"
        ),
        task_type=TaskType.TEST,
        priority=TaskPriority.MEDIUM,
        estimated_hours=3.0,
        tags=["testing", "quality"],
        labels=[{"name": "tests", "color": "#1d76db"}],
        category="quality",
        checklist=[
            "Unit tests",
            "Integration tests",
            "Edge cases",
            "Error handling",
        ],
        variables={
            "component": "Component to test",
            "test_types": "Types of tests needed",
            "coverage": "Coverage target percentage",
        },
    ),
]


class TemplateManager:
    """Manages task templates."""

    def __init__(self) -> None:
        """Initialize template manager."""
        self.templates: dict[str, TaskTemplate] = {}

        # Load built-in templates
        for template in BUILTIN_TEMPLATES:
            self.templates[template.id] = template

    def add_template(self, template: TaskTemplate) -> None:
        """Add a custom template.

        Args:
            template: Template to add
        """
        self.templates[template.id] = template

    def get_template(self, template_id: str) -> TaskTemplate | None:
        """Get template by ID.

        Args:
            template_id: Template ID

        Returns:
            Template if found, None otherwise
        """
        return self.templates.get(template_id)

    def list_templates(self, category: str | None = None) -> list[TaskTemplate]:
        """List templates.

        Args:
            category: Filter by category

        Returns:
            List of templates
        """
        templates = list(self.templates.values())
        if category:
            templates = [t for t in templates if t.category == category]
        return templates

    def remove_template(self, template_id: str) -> None:
        """Remove a template.

        Args:
            template_id: Template ID to remove
        """
        if template_id in self.templates:
            del self.templates[template_id]
